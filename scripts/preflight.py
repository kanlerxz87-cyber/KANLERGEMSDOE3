#!/usr/bin/env python3
"""Prove or disprove the literal registry universal-blocker preflight.

This is a pre-placement proof, not an experiment, holdout score, submission
validator or a complete registry scan. A single positive everywhere witness is
sufficient to stop every nonempty candidate under the shared support rule.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

from restore_workspace import DEFAULT_CACHE, PINS, ROOT, restore, sha256_file


def witness_certificate(footprint, witness, near_function, *, budget=37654):
    footprint = np.asarray(footprint, dtype=bool)
    a = np.asarray(witness)
    if footprint.ndim != 2 or a.shape != footprint.shape or not footprint.any():
        raise ValueError("Witness/footprint must be matching nonempty 2-D grids")
    support = np.isfinite(a) & (a > 0)
    near = np.asarray(near_function(support), dtype=bool)
    if near.shape != footprint.shape:
        raise ValueError("near function changed the grid")
    n = int(footprint.sum())
    uncovered = int((footprint & ~near).sum())
    if budget <= 0 or budget > n:
        raise ValueError("budget must be positive and fit in the footprint")
    return {"footprint_cells": n,
            "positive_inside_footprint": int((support & footprint).sum()),
            "within_3px_cells": n - uncovered,
            "uncovered_cells": uncovered,
            "fraction_within_3px": (n - uncovered) / n,
            "universal_blocker": uncovered == 0,
            "example_budget": budget,
            "overlap_lower_bound_at_example_budget": max(0.0, 1.0 - uncovered / budget)}


def run(cache: Path) -> dict:
    restore(cache, fetch=False, features=False, anchors=False)
    sys.path.insert(0, str(cache / "template/src"))
    # The pinned shared implementation defines positive finite pixels as dots.
    from gems57.uniqueness import _near, dot_overlap
    data = cache / "data"
    with rasterio.open(data / "sample_submission.tif") as sample:
        sample_array = sample.read(1)
        footprint = np.isfinite(sample_array)
        grid = (sample.shape, sample.crs, sample.transform)
    with rasterio.open(data / "existing_faults.tif") as source:
        if (source.shape, source.crs, source.transform) != grid:
            raise ValueError("Catalogue does not match mirrored sample grid")
        catalogue = source.read(1)
    witnesses = {}
    for name in ("registry_dense", "registry_lattice"):
        path = data / f"{name}.tif"
        with rasterio.open(path) as src:
            if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
                raise ValueError(f"{name} grid does not match mirrored sample")
            a = src.read(1)
        certificate = witness_certificate(footprint, a, _near)
        certificate.update(sha256=sha256_file(path),
                           positive_support_definition="finite values greater than zero")
        # Cross-check the shared routine using an allowed, nonempty historic
        # binary mask. This is diagnostic only, not a new candidate.
        certificate["shared_overlap_with_catalogue_as_example"] = dot_overlap(
            ((catalogue > 0) & footprint).astype(np.float32), a)
        witnesses[name] = certificate
    catalogue_mask = (catalogue > 0) & footprint
    sample_positive = np.isfinite(sample_array) & (sample_array > 0)
    sample_matches_labels = bool(np.array_equal(sample_positive, catalogue_mask))
    dense = witnesses["registry_dense"]
    return {"schema": "gems-workbench-preflight-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "evidence_class": "REGISTRY-MEASUREMENT, not HOLDOUT-DTI or an organizer score",
            "template_commit": json.loads(PINS.read_text())["template"]["commit"],
            "rule": "stop if any prior surface/dots overlap exceeds 0.70 within 3 pixels",
            "preplacement_verdict": "STOP" if dense["universal_blocker"] else "INCONCLUSIVE",
            "experiments_run": 0, "submission_slots_used": 0,
            "witnesses": witnesses,
            "grid": {"shape": list(grid[0]), "crs": str(grid[1]),
                     "transform": list(grid[2])[:6],
                     "sample_sha256": sha256_file(data / "sample_submission.tif"),
                     "catalogue_sha256": sha256_file(data / "existing_faults.tif"),
                     "catalogue_positive_inside": int(catalogue_mask.sum()),
                     "sample_positive_matches_catalogue": sample_matches_labels},
            "provenance_warning": "Mirrors are hash-pinned but not independently authenticated organizer files; the mirrored sample's positive labels conflict with the official description of a total-absence example.",
            "scope_warning": "Two indexed public witnesses prove a stop only; this is not a complete organizer or fleet registry scan.",
            "dense_witness_url": "https://github.com/buffedlizard55-lab/17GEMSDOE/blob/main/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
            "lattice_witness_url": "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/main/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, help="Write JSON evidence (no file on preflight error)")
    args = parser.parse_args()
    try:
        report = run(args.cache)
        text = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        # A STOP is a successful diagnostic, not submission authorization.
        return 0
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        print(f"PREFLIGHT FAILED CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
