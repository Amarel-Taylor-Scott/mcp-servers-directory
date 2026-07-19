"""MCP Servers Directory — CLI.

Search, filter, and export a curated registry of Model Context Protocol servers,
and regenerate the README from it.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from __version__ import __version__
from data import SERVERS, Category, Server


def _matches(s: Server, query: str) -> bool:
    q = query.lower()
    hay = " ".join([s.name, s.description, s.maintainer, s.category.value, " ".join(s.tags)]).lower()
    return q in hay


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


def cmd_search(args: argparse.Namespace) -> int:
    servers = [s for s in SERVERS if _matches(s, args.query)]
    _print_table(servers)
    print(f"\n{len(servers)} match(es) for {args.query!r}.")
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
        import csv

        cols = [
            "name",
            "description",
            "category",
            "maintainer",
            "official",
            "transports",
            "language",
            "install",
            "repo",
            "homepage",
            "auth_required",
            "tags",
        ]
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        for d in data:
            w.writerow([
                ";".join(value) if isinstance(value, list) else value
                for value in (d.get(column, "") for column in cols)
            ])
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

    ps = sub.add_parser("search", help="Search name/description/tags")
    ps.add_argument("query")
    ps.set_defaults(func=cmd_search)

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
