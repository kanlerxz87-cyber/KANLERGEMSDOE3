#!/usr/bin/env python3
"""Replay literal-lattice checks on inherited research TIFFs, never create one.

Uses the existing geometry auditor. This is not a model experiment, HOLDOUT-DTI,
complete registry audit, writer, promotion or account submission. Nonzero is an
intentional negative finding. All model cards/artifacts remain unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from scripts.audit_parallel_candidate import audit
from scripts.github_source import GitHubSource, sha256_file
from scripts.validate_submission import validate


def inherited_files() -> dict[str, str]:
    gpc = json.loads((ROOT / "evidence/run_card.json").read_text())
    k3 = json.loads((ROOT / "evidence/k3h1-run-card.json").read_text())
    h1 = json.loads((ROOT / "evidence/kanler_h1/run-card.json").read_text())
    return {
        "docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif": gpc["raster_sha256"],
        "docs/downloads/" + k3["raster_file"]: k3["raster_sha256"],
        h1["deliverable_files"]["primary_zeros_tif"]: h1["raster_sha256"],
        h1["deliverable_files"]["companion_nan_tif"]: h1["companion_nan_raster_sha256"],
    }


def measure(restore: bool = False) -> dict:
    row = next(row for row in json.loads((ROOT / "research/registry-lock.json").read_text())["entries"] if row["id"] == "registry-160")
    lattice = ROOT / "data/registry-review/lattice.tif"
    if restore:
        GitHubSource().restore(row["repo"], row["ref"], row["file"], lattice, row["sha256"])
    if not lattice.is_file() or sha256_file(lattice) != row["sha256"]:
        raise ValueError("Pinned lattice missing/changed; use --restore")
    files = inherited_files()
    from scripts.build_site import check_quarantined_artifacts
    quarantine = check_quarantined_artifacts()
    actual = {str(path.relative_to(ROOT)) for path in (ROOT / "docs/downloads").glob("*.tif")}
    if actual != set(files) | set(quarantine["files"]):
        raise ValueError("Research/quarantined artifact inventory changed; do not silently omit a TIFF")
    results = []
    for name, digest in files.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to((ROOT / "docs/downloads").resolve()) or sha256_file(path) != digest:
            raise ValueError("Inherited artifact hash/path differs from its run card: " + name)
        measured = audit(path, lattice, ROOT / "data/core/sample_submission.tif", ROOT / "data/core/labels.tif")
        measured["validator"] = validate(ROOT / "data/core/sample_submission.tif", path, "template-mask" if name.endswith("-nan.tif") else "finite-grid", measured["candidate_dots"])
        results.append({"file": name, **measured})
    return {
        "kind": "GEOMETRIC_SAVED_BYTES_AUDIT_NOT_MODEL_RESULT",
        "source_main_commit": "9ebfc4bbfbedf39bb2633a524dd49e9192dd3889",
        "scope": "Four inherited TIFFs versus one required pinned binary lattice; no soft-diagnostic exclusion, no complete-registry claim.",
        "lattice": row, "rows": results,
        "status": "STOP_DUPLICATE" if any(row["duplicate_over_70_percent"] for row in results) else "BLOCKED_INCOMPLETE_REGISTRY",
        "all_inherited_files_exceed_overlap_stop": all(row["duplicate_over_70_percent"] for row in results),
        "slot_authorized": False, "new_rasters_written": 0, "geological_experiments_run": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/inherited_literal_audit.json")
    args = parser.parse_args()
    try:
        result = measure(args.restore)
        exit_code = 1  # A one-reference audit cannot authorize a scientific release.
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {"status": "BLOCKED_AUDIT_ERROR", "error": str(exc), "slot_authorized": False, "new_rasters_written": 0}
        exit_code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
