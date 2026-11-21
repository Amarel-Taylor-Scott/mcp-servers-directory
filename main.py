"""MCP Servers Directory — CLI.

Search, filter, and export a curated registry of Model Context Protocol servers,
and regenerate the README from it.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
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


def _read_packs():
    filename = "ta-amps-seedpacks.csv"
    index = Path(__file__).with_name("resources") / filename
    if not index.is_file():
        # Wheels install the same CSV as package data under a distinct package name.
        index = files("mcp_directory_resources").joinpath(filename)

    with index.open(encoding="utf-8", newline="") as stream:
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
            yield result, [pack["title"], pack["pack_id"]], (), [pack["status"], "ta-amps"]


def cmd_search(args: argparse.Namespace) -> int:
    query = _normalize(" ".join(args.query))
    terms = query.split()
    ranked = []
    for row, names, tags, fields in _search_candidates(args.scope):
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
    matches = [row for _, row in ranked[:args.limit]]
    if args.format == "json":
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for row in matches:
            detail = row["description"] if row["source"] == "server" else row["status"]
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

    ps = sub.add_parser("search", help="Find servers or seed packs by matching all query terms")
    ps.add_argument("query", nargs="+", help="Words to find across indexed metadata")
    ps.add_argument("--scope", choices=["servers", "packs", "all"], default="servers")
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
