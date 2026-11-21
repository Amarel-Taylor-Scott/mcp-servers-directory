"""Registry integrity + CLI smoke tests (pure stdlib, no network)."""

from __future__ import annotations

import json
from pathlib import Path

import data
import report
import main as cli


def test_checked_in_readme_matches_registry():
    readme = Path(report.__file__).with_name("README.md")
    assert readme.read_text(encoding="utf-8") == report.generate() + "\n"


def test_registry_nonempty():
    assert len(data.SERVERS) >= 20


def test_unique_names():
    names = [s.name for s in data.SERVERS]
    assert len(names) == len(set(names)), "duplicate server names"


def test_every_server_has_link_and_category():
    for s in data.SERVERS:
        assert s.repo or s.homepage, f"{s.name} has no repo/homepage"
        assert isinstance(s.category, data.Category)
        assert s.description.strip()
        assert s.maintainer.strip()


def test_report_generates_markdown():
    md = report.generate()
    assert md.startswith("<!-- AUTO-GENERATED")
    assert "# 🔌 MCP Servers Directory" in md
    # every category with members should render a section
    labels = {s.category.label for s in data.SERVERS}
    for label in labels:
        assert f"### {label}" in md


def test_export_json_roundtrips():
    rows = [cli._to_dict(s) for s in data.SERVERS]
    blob = json.dumps(rows)
    back = json.loads(blob)
    assert len(back) == len(data.SERVERS)
    assert all("name" in r and "category" in r for r in back)


def test_cli_search_and_list_build():
    parser = cli.build_parser()
    ns = parser.parse_args(["search", "postgres"])
    assert ns.func is cli.cmd_search
    ns = parser.parse_args(["list", "--official"])
    assert ns.func is cli.cmd_list and ns.official is True

