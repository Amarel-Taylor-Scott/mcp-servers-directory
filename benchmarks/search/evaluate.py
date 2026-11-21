"""Evaluate the public search command against fixed, source-scoped judgments."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys


def result_key(row: dict) -> str:
    source = row["source"]
    if source in ("library", "retriever"):
        return row["id"]
    identifier = row["pack_id"] if source == "pack" else row["name"]
    return f"{source}:{identifier}"


def evaluate(checkout: Path, cases: Path, mode: str | None) -> list[dict]:
    results = []
    with cases.open(encoding="utf-8", newline="") as handle:
        for case in csv.DictReader(handle, delimiter="\t"):
            command = [sys.executable, str(checkout / "main.py"), "search",
                       "--scope", case["scope"], "--format", "json", "--limit", "5"]
            if mode is not None:
                command.extend(["--mode", mode])
            command.append(case["query"])
            rows = json.loads(subprocess.check_output(command, text=True))
            returned = [result_key(row) for row in rows]
            targets = set(filter(None, case["targets"].split("|")))
            rank = next((i for i, key in enumerate(returned, 1) if key in targets), None)
            results.append(dict(case, top5=returned, rank=rank))
    return results


def summarize(results: list[dict]) -> dict:
    metrics = {}
    for group in sorted({row["group"] for row in results}):
        rows = [row for row in results if row["group"] == group]
        summary = {"queries": len(rows), "empty": sum(not r["top5"] for r in rows)}
        if any(row["targets"] for row in rows):
            for k in (1, 3, 5):
                summary[f"hit_at_{k}"] = sum(r["rank"] is not None and r["rank"] <= k for r in rows)
            summary["mrr_at_5"] = round(sum(1 / r["rank"] for r in rows if r["rank"]) / len(rows), 3)
        metrics[group] = summary
    return metrics


def main() -> None:
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=directory.parents[1],
                        help="Directory containing the revision's main.py.")
    parser.add_argument("--mode", choices=["lexical", "bm25"],
                        help="Omit to exercise the revision's default (including older CLIs).")
    parser.add_argument("--cases", type=Path, default=directory / "existing.tsv")
    parser.add_argument("--output", type=Path, help="Write per-query results and group metrics as JSON.")
    args = parser.parse_args()
    results = evaluate(args.checkout.resolve(), args.cases, args.mode)
    summary = summarize(results)
    print(json.dumps(summary, indent=2))
    if args.output:
        payload = {"mode": args.mode or "default", "groups": summary, "results": results}
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
