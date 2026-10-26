#!/usr/bin/env python3
"""Fail-closed preflight for an existing GeoTIFF; NEVER uploads or selects a slot.

The single-witness comparison can prove a duplicate, not a complete uniqueness
pass. Without an attached fold-local holdout and separate selector approval this
script always returns a negative overall verdict. It does not create a TIFF.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.assets import CACHE, load_template, sha256, verify, verify_core  # noqa: E402

WITNESS_SHA = "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be"


def rank_rho(a, b, footprint):
    aa, bb = np.asarray(a)[footprint], np.asarray(b)[footprint]
    if aa.size == 0 or not np.isfinite(aa).all() or not np.isfinite(bb).all():
        return None
    if np.ptp(aa) == 0 or np.ptp(bb) == 0:
        return None
    return float(spearmanr(aa, bb).statistic)


def inspect(candidate: Path, surface: Path | None = None) -> dict:
    load_template()
    from gems57 import gates, uniqueness, validate  # verified original shared tools

    verify_core()
    witness = CACHE / "registry/witness.tif"
    verify(witness, WITNESS_SHA)
    with rasterio.open(CACHE / "data/sample_submission.tif") as ref:
        fp = np.isfinite(ref.read(1)) & (ref.dataset_mask() > 0)
        expected = (ref.shape, ref.crs, ref.transform)
    with rasterio.open(CACHE / "data/existing_faults.tif") as src:
        if (src.shape, src.crs, src.transform) != expected:
            raise ValueError("catalogue grid mismatch")
        known = (src.read(1) > 0) & fp
    with rasterio.open(witness) as src:
        if (src.shape, src.crs, src.transform) != expected:
            raise ValueError("registry witness grid mismatch")
        witness_values = src.read(1)

    format_report = gates.format_report(candidate, CACHE / "data/sample_submission.tif", footprint=fp)
    # The shared validator also enforces the conservative all-finite project policy.
    validator = validate.validate(candidate, fp, known)
    surface_report = {"performed": False, "pass": False, "reason": "No pre-placement surface supplied."}
    if surface is not None:
        with rasterio.open(surface) as src:
            if src.count != 1 or (src.shape, src.crs, src.transform) != expected:
                raise ValueError("surface must be single-band and match the reference grid")
            field = src.read(1)
        if not np.isfinite(field[fp]).all() or (field[fp] < 0).any() or (field[fp] > 1).any():
            raise ValueError("surface must already be finite and in [0,1] inside the footprint")
        rho = rank_rho(field, witness_values, fp)
        surface_report = {"performed": True, "sha256": sha256(surface),
                          "spearman_vs_witness": rho,
                          "pass": False,
                          "reason": "One witness cannot establish a complete registry surface pass; undefined ranks also fail closed."}
    final = {"performed": False, "overlap_vs_witness": None, "spearman_vs_witness": None,
             "duplicate": None, "pass": False,
             "reason": "Invalid file or empty support cannot pass."}
    if format_report["ok"] and validator["all_checks_passed"]:
        with rasterio.open(candidate) as src:
            arr = src.read(1)
        support = np.isfinite(arr) & (arr > 0) & fp
        if support.any():
            overlap = uniqueness.dot_overlap(np.where(fp, arr, 0), witness_values)
            rho = rank_rho(arr, witness_values, fp)
            final = {"performed": True, "overlap_vs_witness": overlap, "spearman_vs_witness": rho,
                     "duplicate": bool(overlap > 0.70 or (rho is not None and rho > 0.90)),
                     "pass": False,
                     "reason": "A firing proves duplication; a non-firing does not clear the incomplete registry."}
    return {"schema": "submission-preflight-v1", "candidate": str(candidate),
            "candidate_sha256": sha256(candidate), "local_format_report": format_report,
            "local_validator": validator, "surface_check": surface_report,
            "final_check": final, "registry_complete": False,
            "holdout_and_feature_canaries": "not supplied or verified by this preflight",
            "selector_approval": False, "verdict": "negative", "ok_to_submit": False,
            "reason": "This preflight cannot confer scientific, full-registry, or slot-selector approval."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate", type=Path)
    p.add_argument("--surface", type=Path, help="optional pre-placement surface GeoTIFF")
    p.add_argument("--out", type=Path, help="write JSON receipt as well as stdout")
    args = p.parse_args()
    try:
        result = inspect(args.candidate, args.surface)
        text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"PREFLIGHT ERROR (NOT APPROVED): {exc}", file=sys.stderr)
        return 1
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 2 if not result["ok_to_submit"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
