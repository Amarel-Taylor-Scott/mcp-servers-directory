"""Registry integrity + CLI smoke tests (pure stdlib, no network)."""

from __future__ import annotations

import csv
import io
import json
from argparse import Namespace

import data
import report
import main as cli


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


def test_export_csv_preserves_registry_fields(capsys):
    assert cli.cmd_export(Namespace(format="csv")) == 0

    rows = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))

    assert len(rows) == len(data.SERVERS)
    assert set(rows[0]) == {
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
    }
    assert all(row["description"] and row["transports"] for row in rows)


def test_cli_search_and_list_build():
    parser = cli.build_parser()
    ns = parser.parse_args(["search", "postgres"])
    assert ns.func is cli.cmd_search
    ns = parser.parse_args(["list", "--official"])
    assert ns.func is cli.cmd_list and ns.official is True
