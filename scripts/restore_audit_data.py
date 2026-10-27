#!/usr/bin/env python3
"""Restore small pinned historic audit inputs for learning, never as candidates.

Uses the same hash-verifying Git transport as core-data restoration, with no
REST quota and no redundant download when a pinned file is already present.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import GitHubSource


def main() -> None:
    source = GitHubSource()
    archive = json.loads((ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text())
    for row in archive["historical_winners"]:
        result = source.restore("buffedlizard55-lab/" + row["repo"], row["head"], row["file"], ROOT / "data" / (row["repo"] + ".tif"), row["sha256"])
        print(row["repo"], result["status"])
    manifest = json.loads((ROOT / "sources/GEMSDOE32/registry/data_manifest.json").read_text())
    for row in manifest["files"]:
        if row["id"] in ("sample_submission", "labels"):
            source.restore(row["repo"], row["ref"], row["path"], ROOT / "data" / row["dest"], row["sha256"])


if __name__ == "__main__":
    main()
