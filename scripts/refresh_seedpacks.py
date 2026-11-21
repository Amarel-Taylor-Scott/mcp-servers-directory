"""Regenerate the ta-amps resource CSV and its license from a pinned local Git repository."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

UPSTREAM = "https://github.com/ta-amps/seed-packs-library-of-nouns-and-verbs"
FIELDS = ("pack_id", "title", "version", "status", "task_objects", "tasks",
          "guide_url", "manifest_url", "nouns_sha256", "verbs_sha256", "summary")


def build_catalog(read: Callable[[str], str], revision: str) -> tuple[str, str]:
    report = json.loads(read("packs/VALIDATION.json"))
    if report["errors"]:
        raise ValueError("upstream validation report contains errors")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for pack_id, evidence in sorted(report["packs"].items()):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", pack_id):
            raise ValueError(f"unexpected pack id: {pack_id}")
        folder = f"packs/{pack_id}"
        manifest = json.loads(read(f"{folder}/manifest.json"))
        if manifest["pack_id"] != pack_id or manifest["format"] != "ta-amps.seed-pack.proposal.v1":
            raise ValueError(f"{pack_id}: unexpected identity or manifest format")
        if manifest["license"] != "MIT" or not manifest["summary"].strip():
            raise ValueError(f"{pack_id}: check license and summary")
        if (len(manifest["nouns"]), len(manifest["verbs"])) != (evidence["records"], evidence["tasks"]):
            raise ValueError(f"{pack_id}: manifest counts disagree with validation report")
        digests = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
        for name in ("nouns", "verbs"):
            if digests[f"{name}.json"] != evidence[f"{name}_sha256"]:
                raise ValueError(f"{pack_id}: {name} digest disagrees with validation report")
        url = f"{UPSTREAM}/blob/{revision}/{folder}"
        writer.writerow(dict(
            pack_id=pack_id, title=manifest["title"], version=manifest["version"],
            status=manifest["status"], task_objects=evidence["records"], tasks=evidence["tasks"],
            guide_url=f"{url}/README.md", manifest_url=f"{url}/manifest.json",
            nouns_sha256=digests["nouns.json"], verbs_sha256=digests["verbs.json"], summary=manifest["summary"],
        ))
    attribution = (
        "The pack titles and summaries in ta-amps-seedpacks.csv come from the upstream pack manifests.\n"
        f"Source: {UPSTREAM}/tree/{revision}/packs\n\n"
        + read("LICENSE")
    )
    return output.getvalue(), attribution


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="local clone of ta-amps/seed-packs-library-of-nouns-and-verbs")
    parser.add_argument("commit", help="full 40-character upstream Git commit SHA")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("supply a full lower-case Git commit SHA")

    def read(path: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(args.checkout), "show", f"{args.commit}:{path}"], encoding="utf-8",
        )

    catalog, attribution = build_catalog(read, args.commit)
    directory = Path(__file__).resolve().parents[1] / "resources"
    for filename, content in (("ta-amps-seedpacks.csv", catalog), ("ta-amps-seedpacks.LICENSE.txt", attribution)):
        (directory / filename).write_bytes(content.encode("utf-8"))


if __name__ == "__main__":
    main()
