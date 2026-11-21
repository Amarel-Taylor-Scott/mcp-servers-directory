"""Exercise seed pack discovery through the CLI entry point."""

import csv
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def packs(*args):
    return subprocess.check_output([sys.executable, str(ROOT / "main.py"), "packs", *args], text=True)


def test_json_pack_index_matches_source():
    with (ROOT / "resources" / "ta-amps-seedpacks.csv").open(encoding="utf-8", newline="") as stream:
        source = list(csv.DictReader(stream))
    records = json.loads(packs("--format", "json"))
    assert records == [{**row, "tasks": int(row["tasks"]), "task_objects": int(row["task_objects"])} for row in source]
    assert len({record["pack_id"] for record in records}) == len(records)


def test_pack_search_case_and_empty_results():
    hits = json.loads(packs("HARNESS", "onboarding", "--format", "json"))
    assert "harness-onboarding-e2e" in {row["pack_id"] for row in hits}
    assert hits[0]["guide_url"] in packs("HARNESS", "onboarding")
    assert json.loads(packs("--format", "json", "no-such-pack-in-this-index")) == []
