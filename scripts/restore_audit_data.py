#!/usr/bin/env python3
"""Restore pinned audit inputs into .cache/ with symlinks in data/ (zero REST API quota required)."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57.prepare_data import fetch_raw, sha256  # noqa: E402


def fetch(repo: str, path: str, ref: str, dest: Path, expected_sha: str) -> None:
    cache_dest = ROOT / ".cache" / "audit_inputs" / dest.relative_to(ROOT / "data")
    fetch_raw(repo, path, ref, cache_dest, expected_sha)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    dest.symlink_to(os.path.relpath(cache_dest, dest.parent))
    assert sha256(dest) == expected_sha, f"Hash mismatch after symlink: {dest}"


def main() -> int:
    archive = json.loads((ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text())
    for r in archive["historical_winners"]:
        fetch(
            "buffedlizard55-lab/" + r["repo"],
            r["file"],
            r["head"],
            ROOT / "data" / f"{r['repo']}.tif",
            r["sha256"],
        )
        print(f"[audit-restore] OK data/{r['repo']}.tif ({r['sha256'][:12]})", flush=True)
    manifest = json.loads((ROOT / "sources/GEMSDOE32/registry/data_manifest.json").read_text())
    for r in manifest["files"]:
        if r["id"] in ("sample_submission", "labels"):
            fetch(r["repo"], r["path"], r["ref"], ROOT / "data" / r["dest"], r["sha256"])
            print(f"[audit-restore] OK data/{r['dest']} ({r['sha256'][:12]})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
