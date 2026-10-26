#!/usr/bin/env python3
"""Restore immutable, hash-pinned owner mirrors via GitHub's API, without committing bulk data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/input-manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo: str, ref: str, path: str, out) -> None:
    safe_path = urllib.parse.quote(path, safe="/")
    endpoint = f"repos/{repo}/contents/{safe_path}?ref={ref}"
    if shutil.which("gh"):
        subprocess.run(["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"], stdout=out, check=True)
    else:
        req = urllib.request.Request("https://api.github.com/" + endpoint, headers={"Accept": "application/vnd.github.raw", "User-Agent": "KANLERGEMSDOE3-data-restore"})
        with urllib.request.urlopen(req, timeout=180) as response:
            shutil.copyfileobj(response, out, length=1024 * 1024)


def restore(entry: dict, root: Path) -> dict:
    root = root.resolve()
    dest = (root / entry["dest"]).resolve()
    if not dest.is_relative_to(root):
        raise ValueError("destination must stay inside data directory")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size == entry["bytes"] and sha256(dest) == entry["sha256"]:
        return {"id": entry["id"], "status": "already verified", "sha256": entry["sha256"]}
    partial = dest.with_name(dest.name + ".partial")
    try:
        with partial.open("wb") as out:
            for part in entry.get("parts", [entry.get("path")]):
                if not part:
                    raise ValueError("missing source path")
                print(f"Fetching {entry['id']}: {part}", flush=True)
                fetch(entry["repo"], entry["ref"], part, out)
        digest = sha256(partial)
        if partial.stat().st_size != entry["bytes"] or digest != entry["sha256"]:
            raise ValueError(f"{entry['id']}: byte count or SHA-256 mismatch (got {digest}); file not installed")
        os.replace(partial, dest)
        return {"id": entry["id"], "status": "restored and verified", "sha256": digest}
    finally:
        partial.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--ids", nargs="*", help="restore these IDs only; default restores all")
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    entries = manifest["inputs"]
    ids = {e["id"] for e in entries}
    if args.ids is not None and (not args.ids or set(args.ids) - ids):
        ap.error(f"--ids must select known entries: {', '.join(sorted(ids))}")
    result = []
    for e in entries:
        if args.ids is None or e["id"] in args.ids:
            item = restore(e, args.target_dir)
            result.append(item)
            print(json.dumps(item), flush=True)
    print("Owner-mirror integrity checked; organizer authentication and competition eligibility not established.")

if __name__ == "__main__":
    main()
