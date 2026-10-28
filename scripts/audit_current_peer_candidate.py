#!/usr/bin/env python3
"""Audit the saved ATSC research TIFF against the bounded 2026-10-28 peer cache.

This is a read-only final-dot forensic check. It does not recreate a pre-placement
surface, run a holdout, estimate a leaderboard score, or authorize a slot. The
peer cache is intentionally bounded (the fetcher selects at most 12 unique raster
stems per repository), so a passing bounded comparison can never override the
literal full-registry calibration-lattice stop already recorded in the ATSC card.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / "docs/atsc-submod/downloads/kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros.tif"
DEFAULT_MANIFEST = ROOT / ".cache/peer_registry_20261028/manifest.json"
DEFAULT_TEMPLATE = ROOT / ".cache/gems_data/sample_submission.tif"
DEFAULT_OUTPUT = ROOT / "evidence/atsc-current-peer-audit-20261028.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dot_rc(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    mask = np.isfinite(arr) & (arr > 0.0) & footprint
    return np.column_stack(np.nonzero(mask)).astype(np.float32, copy=False)


def audit(candidate: Path, manifest_path: Path, template: Path) -> dict:
    with rasterio.open(template) as src:
        footprint = np.isfinite(src.read(1, masked=False))
        shape = src.shape
        crs = str(src.crs)
    with rasterio.open(candidate) as src:
        if src.count != 1 or src.shape != shape or str(src.crs) != crs:
            raise ValueError("candidate grid does not match the saved template")
        candidate_arr = src.read(1, masked=False)
    candidate_dots = dot_rc(candidate_arr, footprint)
    if len(candidate_dots) == 0:
        raise ValueError("candidate has no positive in-footprint dots")

    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("bounded peer manifest is empty or malformed")
    rows = []
    seen_sha = set()
    for entry in manifest:
        local = manifest_path.parent / entry["local_file"]
        if not local.is_file():
            raise FileNotFoundError(local)
        actual = sha256_file(local)
        if actual != entry["sha256"]:
            raise ValueError(f"peer SHA-256 mismatch: {entry['local_file']}")
        if actual in seen_sha:
            continue
        seen_sha.add(actual)
        with rasterio.open(local) as src:
            if src.count != 1 or src.shape != shape or str(src.crs) != crs:
                raise ValueError(f"peer grid mismatch: {entry['local_file']}")
            ref_arr = src.read(1, masked=False)
        ref_dots = dot_rc(ref_arr, footprint)
        if len(ref_dots) == 0:
            continue
        distances, _ = cKDTree(ref_dots).query(candidate_dots, k=1)
        overlap = float((distances <= 3.0).mean())
        rows.append(
            {
                "repository": entry["repo"],
                "path": entry["repo_path"],
                "local_file": entry["local_file"],
                "sha256": actual,
                "is_calibration_probe": bool(entry["is_calibration_probe"]),
                "reference_dots": int(len(ref_dots)),
                "candidate_dots_within_3px": int((distances <= 3.0).sum()),
                "candidate_dot_overlap_3px": round(overlap, 8),
                "duplicate_over_70_percent": bool(overlap > 0.70),
            }
        )
    if not rows:
        raise ValueError("no comparable peer raster survived the audit")
    rows.sort(key=lambda r: r["candidate_dot_overlap_3px"], reverse=True)
    genuine = [r for r in rows if not r["is_calibration_probe"]]
    probes = [r for r in rows if r["is_calibration_probe"]]
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidate": {
            "path": str(candidate.relative_to(ROOT)),
            "sha256": sha256_file(candidate),
            "dots_in_footprint": int(len(candidate_dots)),
            "preplacement_surface_comparison": None,
            "validator_or_holdout": "not run by this read-only audit",
        },
        "peer_registry_scope": {
            "manifest": str(manifest_path.relative_to(ROOT)),
            "rasters_compared": len(rows),
            "genuine_detectors_compared": len(genuine),
            "calibration_or_continuous_probes_compared": len(probes),
            "complete_registry": False,
            "selection_rule": "At most 12 unique raster stems per repository; exact GitHub tree and saved-byte hashes are recorded in the companion manifest.",
        },
        "result": {
            "max_final_dot_overlap_3px_all_compared": rows[0]["candidate_dot_overlap_3px"],
            "max_final_dot_overlap_3px_genuine_detectors": max(r["candidate_dot_overlap_3px"] for r in genuine) if genuine else None,
            "max_final_dot_overlap_3px_calibration_or_continuous_probes": max(r["candidate_dot_overlap_3px"] for r in probes) if probes else None,
            "nearest_all_compared": rows[0],
            "nearest_genuine_detector": genuine[0] if genuine else None,
            "nearest_calibration_or_continuous_probe": probes[0] if probes else None,
            "literal_duplicate_stop": any(r["duplicate_over_70_percent"] for r in rows),
            "surface_gate_evaluated": False,
        },
        "interpretation": "This bounded final-dot comparison cannot authorize the candidate. The ATSC run card already records a literal full-registry r13-lattice stop; no surface comparison, HOLDOUT-DTI rerun, organizer receipt, or weekly-slot authorization is created here.",
        "comparisons": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = audit(args.candidate, args.manifest, args.template)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "candidate_sha256": result["candidate"]["sha256"],
        "rasters_compared": result["peer_registry_scope"]["rasters_compared"],
        "genuine_detectors_compared": result["peer_registry_scope"]["genuine_detectors_compared"],
        "max_final_dot_overlap_3px_all_compared": result["result"]["max_final_dot_overlap_3px_all_compared"],
        "max_final_dot_overlap_3px_genuine_detectors": result["result"]["max_final_dot_overlap_3px_genuine_detectors"],
        "literal_duplicate_stop": result["result"]["literal_duplicate_stop"],
    }, indent=2))
    return 1 if result["result"]["literal_duplicate_stop"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
