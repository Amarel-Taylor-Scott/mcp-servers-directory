"""MCP Servers Directory — CLI.

Search, filter, and export a curated registry of Model Context Protocol servers,
and regenerate the README from it.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from contextlib import closing
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path

from __version__ import __version__
from data import SERVERS, Category, Server


def _normalize(text: str) -> str:
    return " ".join(text.casefold().replace("-", " ").replace("_", " ").split())


def _to_dict(s: Server) -> dict:
    d = asdict(s)
    d["category"] = s.category.value
    d["transports"] = [t.value for t in s.transports]
    d["tags"] = list(s.tags)
    return d


def _print_table(servers: list[Server]) -> None:
    if not servers:
        print("No servers matched.")
        return
    width = max(len(s.name) for s in servers)
    for s in sorted(servers, key=lambda s: (s.category.value, s.name.lower())):
        flag = "✅" if s.official else "  "
        auth = "🔑" if s.auth_required else "  "
        print(f"{flag}{auth} {s.name.ljust(width)}  [{s.category.label}]  {s.description}")


def cmd_list(args: argparse.Namespace) -> int:
    servers = list(SERVERS)
    if args.category:
        servers = [s for s in servers if s.category.value == args.category]
    if args.official:
        servers = [s for s in servers if s.official]
    _print_table(servers)
    print(f"\n{len(servers)} server(s).")
    return 0


def _resource(filename: str):
    index = Path(__file__).with_name("resources") / filename
    if index.is_file() or Path(__file__).with_name("pyproject.toml").is_file():
        return index
    return files("mcp_directory_resources").joinpath(filename)


def _read_packs():
    with _resource("ta-amps-seedpacks.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            yield {**row, "task_objects": int(row["task_objects"]), "tasks": int(row["tasks"])}


def _search_candidates(scope: str):
    if scope in {"servers", "all"}:
        for server in SERVERS:
            result = {**_to_dict(server), "source": "server", "url": server.repo or server.homepage}
            fields = [server.description, server.maintainer, server.category.label, server.category.value, server.language]
            yield result, [server.name], server.tags, fields + result["transports"]
    if scope in {"packs", "all"}:
        for pack in _read_packs():
            result = {**pack, "name": pack["title"], "source": "pack", "url": pack["guide_url"]}
            yield result, [pack["title"], pack["pack_id"]], (), [pack["status"], "ta-amps", pack.get("summary", "")]
    if scope in {"retrievers", "libraries", "all"}:
        with _resource("retrieval-catalogs.json").open(encoding="utf-8") as stream:
            snapshot = json.load(stream)
        if snapshot["schema_version"] != 1:
            raise ValueError("Unsupported retrieval catalog schema version")
        for entry in snapshot["entries"]:
            catalog = entry["source"]
            kind = {"ann": "library", "rag": "retriever"}[catalog]
            if (scope == "libraries" and kind != "library") or (scope == "retrievers" and kind != "retriever"):
                continue
            result = {**entry, "source": kind, "catalog": catalog, "catalog_url": snapshot["sources"][catalog]["url"]}
            fields = [entry["note"], entry["org"], entry["category"], entry["license"]]
            if entry["open_source"]:
                fields.append("open source")
            yield result, [entry["name"], entry["id"]], entry["tags"], fields


def _lexical_search(candidates, query):
    terms = query.split()
    ranked = []
    for row, names, tags, fields in candidates:
        names = [_normalize(name) for name in names]
        tags = {_normalize(tag) for tag in tags}
        haystack = " ".join([*names, *tags, *map(_normalize, fields)])
        if not terms or not all(term in haystack for term in terms):
            continue
        # Prefer exact names and IDs, then exact tags and matches within names.
        key = (-(query in names), -(query in tags), -sum(term in tags for term in terms),
               -sum(any(term in name for name in names) for term in terms), names[0], row["source"])
        ranked.append((key, row))
    ranked.sort(key=lambda item: item[0])
    return [row for _, row in ranked]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", text.casefold())


def _distinct_fts_terms(db, terms, tokenizer):
    """Pick one literal query word for each distinct term produced by FTS5."""
    db.execute(f"CREATE VIRTUAL TABLE query_words USING fts5(word, tokenize='{tokenizer}')")
    db.executemany("INSERT INTO query_words(word) VALUES (?)", [(term,) for term in terms])
    db.execute("CREATE VIRTUAL TABLE stems USING fts5vocab(query_words, 'instance')")
    rows = db.execute("SELECT min(doc) FROM stems GROUP BY term ORDER BY term")
    return [f'"{terms[word_id - 1]}"' for (word_id,) in rows]


def _bm25_search(candidates, query):
    # Treat user input as words. Operators, quotes and punctuation never enter the FTS expression.
    stopwords = {"a", "an", "and", "are", "can", "do", "for", "from", "how", "i", "in", "is",
                 "my", "of", "or", "the", "to", "what", "which", "with"}
    terms = set(_tokens(query)) - stopwords
    if not terms:
        return []
    if len(terms) > 128:
        raise ValueError("BM25 search accepts at most 128 distinct query terms")
    try:
        import sqlite3
    except ImportError as exc:
        raise ValueError("BM25 needs SQLite FTS5. Use --mode lexical or install a Python build with FTS5.") from exc

    records = []
    documents = []
    for row, names, tags, fields in candidates:
        columns = [" ".join(_tokens(" ".join(group))) for group in (names, tags, fields)]
        records.append((row, query in map(_normalize, names)))
        documents.append(columns)
    try:
        with closing(sqlite3.connect(":memory:")) as db:
            tokenizer = "porter unicode61 remove_diacritics 0"
            db.execute(f"CREATE VIRTUAL TABLE docs USING fts5(names, tags, metadata, tokenize='{tokenizer}')")
            db.executemany("INSERT INTO docs VALUES (?, ?, ?)", documents)
            literals = _distinct_fts_terms(db, sorted(terms), tokenizer)
            if not literals:
                return []
            coverage = Counter()
            for literal in literals:
                coverage.update(rowid for (rowid,) in db.execute("SELECT rowid FROM docs WHERE docs MATCH ?", (literal,)))
            match_query = " OR ".join(literals)
            hits = db.execute("SELECT rowid, bm25(docs, 5, 3, 1) FROM docs WHERE docs MATCH ?", (match_query,))
            ranked = []
            for rowid, score in hits:
                row, exact = records[rowid - 1]
                key = (-exact, -coverage[rowid], score, row["name"].casefold(), row["source"], row["url"])
                ranked.append((key, row))
    except sqlite3.OperationalError as exc:
        if "no such module: fts5" in str(exc).lower():
            raise ValueError("BM25 needs SQLite FTS5. Use --mode lexical or install a Python build with FTS5.") from exc
        raise ValueError(f"SQLite search failed: {exc}") from exc
    ranked.sort(key=lambda item: item[0])
    return [row for _, row in ranked]


def cmd_search(args: argparse.Namespace) -> int:
    query = _normalize(" ".join(args.query))
    candidates = _search_candidates(args.scope)
    try:
        ranked = _bm25_search(candidates, query) if args.mode == "bm25" else _lexical_search(candidates, query)
    except (OSError, ImportError, KeyError, TypeError, ValueError) as exc:
        print(f"Search failed: {exc}", file=sys.stderr)
        return 2
    matches = ranked[:args.limit]
    if args.format == "json":
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for row in matches:
            detail = row.get("description") or row.get("note") or row.get("summary") or row.get("status", "")
            print(f"[{row['source']}] {row['name']}  {detail}\n  {row['url']}")
        print(f"{len(matches)} of {len(ranked)} match(es) for {' '.join(args.query)!r}.")
    return 0


def _positive_limit(value: str) -> int:
    limit = int(value)
    if limit < 1:
        raise argparse.ArgumentTypeError("limit must be at least 1")
    return limit


def cmd_packs(args: argparse.Namespace) -> int:
    terms = " ".join(args.query).casefold().split()
    matches = []
    for row in _read_packs():
        searchable = " ".join((row["pack_id"], row["title"], row["status"])).casefold()
        if all(term in searchable for term in terms):
            matches.append(row)

    if args.format == "json":
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for pack in matches:
            print(f"{pack['title']} [{pack['status']}]  {pack['task_objects']} task objects, {pack['tasks']} tasks")
            print(f"  {pack['guide_url']}")
        print(f"{len(matches)} seed pack(s).")
    return 0


def cmd_categories(_: argparse.Namespace) -> int:
    counts: dict[str, int] = {}
    for s in SERVERS:
        counts[s.category.label] = counts.get(s.category.label, 0) + 1
    width = max(len(k) for k in counts)
    for label in sorted(counts):
        print(f"{label.ljust(width)}  {counts[label]}")
    print(f"\n{len(counts)} categories, {len(SERVERS)} servers.")
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    official = sum(1 for s in SERVERS if s.official)
    auth = sum(1 for s in SERVERS if s.auth_required)
    print(f"servers:    {len(SERVERS)}")
    print(f"official:   {official}")
    print(f"need auth:  {auth}")
    print(f"categories: {len({s.category for s in SERVERS})}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    data = [_to_dict(s) for s in SERVERS]
    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:  # csv
        cols = ["name", "category", "maintainer", "official", "language", "auth_required", "repo", "install", "homepage"]
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        for d in data:
            w.writerow([d.get(c, "") for c in cols])
    return 0


def cmd_generate(_: argparse.Namespace) -> int:
    from report import generate
    readme = Path(__file__).parent / "README.md"
    readme.write_text(generate() + "\n", encoding="utf-8")
    print(f"Wrote {readme} ({len(SERVERS)} servers).")
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(f"mcp-servers-directory {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mcp-dir", description="MCP Servers Directory CLI")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command")

    pl = sub.add_parser("list", help="List servers")
    pl.add_argument("--category", choices=[c.value for c in Category], help="Filter by category")
    pl.add_argument("--official", action="store_true", help="Only official/first-party servers")
    pl.set_defaults(func=cmd_list)

    ps = sub.add_parser("search", help="Search the directory and its linked retrieval catalogs")
    ps.add_argument("query", nargs="+", help="Words to find across indexed metadata")
    ps.add_argument("--scope", choices=["servers", "packs", "retrievers", "libraries", "all"], default="servers")
    ps.add_argument("--mode", choices=["lexical", "bm25"], default="lexical",
                    help="Match every substring (lexical) or rank token matches by coverage and BM25 (requires SQLite FTS5)")
    ps.add_argument("--format", choices=["text", "json"], default="text")
    ps.add_argument("--limit", type=_positive_limit, help="Maximum results to display")
    ps.set_defaults(func=cmd_search)

    pp = sub.add_parser("packs", help="List or search ta-amps seed packs")
    pp.add_argument("query", nargs="*", help="Match all words against the pack ID, title or status")
    pp.add_argument("--format", choices=["text", "json"], default="text")
    pp.set_defaults(func=cmd_packs)

    sub.add_parser("categories", help="List categories + counts").set_defaults(func=cmd_categories)
    sub.add_parser("stats", help="Registry statistics").set_defaults(func=cmd_stats)

    pe = sub.add_parser("export", help="Export the registry")
    pe.add_argument("--format", choices=["json", "csv"], default="json")
    pe.set_defaults(func=cmd_export)

    sub.add_parser("generate", help="Regenerate README.md").set_defaults(func=cmd_generate)
    sub.add_parser("version", help="Print version").set_defaults(func=cmd_version)
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
