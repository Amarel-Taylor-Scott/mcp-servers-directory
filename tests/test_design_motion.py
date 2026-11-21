"""Cross-check design and motion discovery against the bundled catalog."""
import csv
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def search(scope, query, mode="lexical"):
    command = [sys.executable, str(ROOT / "main.py"), "search", "--scope", scope,
               "--mode", mode, "--format", "json", "--limit", "1", query]
    return json.loads(subprocess.check_output(command, text=True))


def test_design_and_motion_scopes_preserve_distinct_ids_and_provenance():
    resource = ROOT / "resources" / "design-motion.csv"
    with resource.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    commit = resource.with_suffix(".commit").read_text(encoding="ascii").strip()
    for slug, scope, source in [("scenario-storyboards", "design", "design-skill"), ("coldtype", "motion", "motion-tool")]:
        sample = next(r for r in rows if r["id"] == slug)
        identifier = f"{scope}:{sample['id']}"
        result, = search(scope, identifier)
        assert result == search("all", identifier, mode="bm25")[0]
        assert result["id"] == identifier and result["source"] == source
        assert result["url"] == sample["repo_url"] and result["evidence_url"] == sample["evidence_url"]
        assert re.search(r"/(?:blob|tree)/[0-9a-f]{40}(?:/|$)", result["evidence_url"])
        assert result["catalog_url"].endswith(f"/blob/{commit}/resources/design-motion.csv")
        assert result["tags"] == [tag.strip() for tag in sample["tags"].split("|") if tag.strip()]
        assert search("servers", identifier) == []
