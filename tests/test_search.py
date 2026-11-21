"""Search behavior through the same entry point as mcp-dir."""

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import main as cli
from data import Category, Server


CLI = Path(__file__).resolve().parents[1] / "main.py"


def search(*args):
    return json.loads(subprocess.check_output([sys.executable, str(CLI), "search", "--format", "json", *args], text=True))


def test_search_requires_all_terms_and_defaults_to_servers():
    rows = search("DuCkDb", "sQl")
    assert rows == search("duckdb sql")
    assert any(r["name"] == "MotherDuck for DuckDB" for r in rows)
    assert all(r["source"] == "server" and r["url"] == (r["repo"] or r["homepage"]) for r in rows)
    assert search("postgre")  # Partial single-term lookup remains supported.
    assert search("duckdb", "xyzzy-does-not-exist") == []


def test_combined_search_scopes_links_and_ranking():
    rows = search("--scope", "all", "video")
    assert {"server", "pack"} <= {r["source"] for r in rows}
    assert search("--scope", "all", "--limit", "2", "video") == rows[:2]
    packs = search("--scope", "packs", "video")
    assert packs == [r for r in rows if r["source"] == "pack"]
    assert all(r["url"] == r["guide_url"] for r in packs)
    exact = search("--scope", "all", "TOOL_DISCOVERY")
    assert exact[0]["pack_id"] == "tool-discovery"
    assert exact == search("--scope", "all", "tool-discovery") == search("--scope", "all", "tool", "discovery")


def test_limit_must_be_positive():
    for value in ("0", "-2"):
        proc = subprocess.run([sys.executable, str(CLI), "search", "video", "--limit", value], capture_output=True)
        assert proc.returncode == 2
        assert b"at least 1" in proc.stderr


def test_exact_name_outranks_tags_then_descriptions_with_stable_ties():
    def entry(name, tags=()):
        return Server(name, "Find echo samples", Category.search_web, "Fixture", tags=tags,
                      homepage="https://example.org/")

    records = [entry("Zulu"), entry("Tagged", ("echo",)), entry("Echo"), entry("Alpha")]
    args = cli.build_parser().parse_args(["search", "echo", "--format", "json"])
    for order in (records, list(reversed(records))):
        out = StringIO()
        with patch.object(cli, "SERVERS", order), redirect_stdout(out):
            cli.cmd_search(args)
        assert [r["name"] for r in json.loads(out.getvalue())] == ["Echo", "Tagged", "Alpha", "Zulu"]
