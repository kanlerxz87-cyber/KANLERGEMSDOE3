#!/usr/bin/env python3
"""Fetch pinned audit witnesses and nine historical rasters, never submit them."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from bootstrap import ROOT, INPUTS, sha256

PORTFOLIO_DIR = ROOT / ".cache" / "portfolio"


def download(entry: dict, destination: Path) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", entry["ref"]):
        raise ValueError("A full immutable Git commit is required")
    if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
        raise ValueError("A full SHA-256 pin is required")
    if destination.is_file() and destination.stat().st_size == entry["bytes"] and sha256(destination) == entry["sha256"]:
        return f"verified {destination.name}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=destination.parent, prefix=".download-")
    temp = Path(temp_name)
    endpoint = f"repos/buffedlizard55-lab/{entry['repo']}/contents/{entry['path']}?ref={entry['ref']}"
    try:
        with os.fdopen(fd, "wb") as out:
            subprocess.run(["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw+json"],
                           stdout=out, check=True, timeout=180)
        if temp.stat().st_size != entry["bytes"] or sha256(temp) != entry["sha256"]:
            raise ValueError(f"Pinned size/hash mismatch for {entry['repo']}/{entry['path']}")
        os.replace(temp, destination)
        return f"restored {destination.name}"
    finally:
        temp.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-only", action="store_true", help="omit the nine historical TIFFs")
    args = parser.parse_args()
    if not shutil.which("gh"):
        raise SystemExit("GitHub CLI (gh) is required")
    inp = json.loads((ROOT / "data/audit_inputs.json").read_text())["files"]
    jobs = [(e, INPUTS / e["name"]) for e in inp]
    if not args.inputs_only:
        rows = json.loads((ROOT / "data/focus_sources.json").read_text())["rasters"]
        jobs += [(e, PORTFOLIO_DIR / (e["repo"] + ".tif")) for e in rows]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda pair: download(*pair), jobs):
            print(result, flush=True)
    print("Audit inputs are owner mirrors; hashes do not verify organizer provenance or scores.")


if __name__ == "__main__":
    main()
