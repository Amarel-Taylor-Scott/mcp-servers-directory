#!/usr/bin/env python3
"""Reproduce the bundled design and motion CSV from its tracked upstream commit."""
import argparse
import csv
import io
from pathlib import Path
import re
import subprocess
from tempfile import NamedTemporaryFile
from urllib.error import URLError
from urllib.request import urlopen


REPOSITORY = "Amarel-Taylor-Scott/ai-agent-skills-directory"
CATALOG = "resources/design-motion.csv"
ROOT = Path(__file__).resolve().parents[1]


def validate(content):
    rows = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    fields = "id kind name repo_url evidence_url license description tags".split()
    if rows.fieldnames != fields:
        raise ValueError("unexpected source CSV header")
    seen = set()
    for row in rows:
        kind, slug = row["kind"], row["id"]
        if None in row or not all(row.get(key) for key in fields):
            raise ValueError(f"invalid catalog row at line {rows.line_num}")
        if kind not in {"skill", "tool"} or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"invalid kind or ID at line {rows.line_num}")
        if not re.fullmatch(r"https://github\.com/[^/]+/[^/]+/blob/[a-f0-9]{40}/.+", row["evidence_url"]):
            raise ValueError(f"expected a commit-pinned evidence file at line {rows.line_num}")
        if (kind, slug) in seen:
            raise ValueError(f"duplicate {kind} ID: {slug}")
        seen.add((kind, slug))
    if not seen:
        raise ValueError("empty design and motion catalog")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare bytes and exit without writing")
    parser.add_argument("--repo", type=Path, help="read the pinned commit from a local Git clone")
    args = parser.parse_args()
    output = ROOT / CATALOG
    try:
        commit = output.with_suffix(".commit").read_text(encoding="ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("expected a full lowercase SHA in resources/design-motion.commit")
        if args.repo:
            content = subprocess.check_output(["git", "-C", str(args.repo), "show", f"{commit}:{CATALOG}"])
        else:
            url = f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}/{CATALOG}"
            with urlopen(url, timeout=30) as response:
                content = response.read()
        validate(content)
        if args.check:
            if output.read_bytes() != content:
                parser.exit(1, "Design and motion snapshot differs from the pinned source.\n")
        else:
            with NamedTemporaryFile(dir=output.parent, delete=False) as stream:
                stream.write(content)
            Path(stream.name).replace(output)
    except (OSError, ValueError, csv.Error, URLError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Could not refresh design and motion snapshot: {exc}\n")


if __name__ == "__main__":
    main()
