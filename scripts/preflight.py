#!/usr/bin/env python3
"""Report availability/integrity without creating a stack or running an experiment."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect(data: Path, work: Path, manifest: dict, card: dict) -> dict:
    files = []
    for entry in manifest["files"]:
        path = data / entry["dest"]
        actual = digest(path) if path.is_file() else None
        files.append({"id": entry["id"], "file": str(path), "sha256": actual,
                      "verified_against_owner_mirror": actual == entry["sha256"]})
    stack = work / "feature_stack.npy"
    stack_sha = digest(stack) if stack.is_file() else None
    declared = card.get("feature_cache", {})
    stack_ok = (isinstance(declared, dict) and declared.get("provenance_verified") is True
                and stack_sha is not None and stack_sha == declared.get("sha256"))
    lane = card.get("lane", {})
    lane_ok = (isinstance(lane, dict) and lane.get("explicitly_assigned") is True
               and isinstance(lane.get("assigned_method"), str) and bool(lane["assigned_method"].strip()))
    return {"core": files, "mirror_authentication": "not established from organizer",
            "feature_stack": {"file": str(stack), "present": stack.is_file(),
                              "sha256": stack_sha, "provenance_verified": stack_ok},
            "explicit_method_lane": lane_ok,
            "ready_for_experiment": bool(files) and all(x["verified_against_owner_mirror"] for x in files) and stack_ok and lane_ok,
            "note": "This does not evaluate canaries, holdout, uniqueness, format or slot selection."}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=Path(os.environ.get("GEMS_DATA_DIR", ROOT / ".cache/gems_data")))
    p.add_argument("--work-dir", type=Path, default=Path(os.environ.get("GEMS_WORK_DIR", ROOT / ".cache/gems_work")))
    args = p.parse_args()
    result = inspect(args.data_dir, args.work_dir, json.loads((ROOT / "data/core-manifest.json").read_text()),
                     json.loads((ROOT / "evidence/run-card.json").read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    if not result["ready_for_experiment"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
