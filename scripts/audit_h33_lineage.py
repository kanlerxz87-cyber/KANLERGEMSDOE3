#!/usr/bin/env python3
"""Reproduce a historical geometry comparison, not a model or score.

Only the three hash-pinned research references and the participant-mirror
catalogue/template are read. No reference is copied into a candidate. Output
reports pixel equivalence on this mirror grid, not actual program ancestry,
organizer authentication, a causal score improvement, or eligibility to submit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import sha256_file  # noqa: E402


def measure(footprint: np.ndarray, known: np.ndarray, p25: np.ndarray,
            p30: np.ndarray, p32: np.ndarray) -> dict:
    """Count exact binary-mask relations and distances, without a DTI score."""
    arrays = (footprint, known, p25, p30, p32)
    if any(not isinstance(x, np.ndarray) or x.dtype != np.bool_ or x.ndim != 2 for x in arrays):
        raise ValueError("five two-dimensional boolean masks required")
    if any(x.shape != footprint.shape for x in arrays) or not footprint.any() or not known.any():
        raise ValueError("identical nonempty grid and nonempty known catalogue required")
    if any((x & ~footprint).any() for x in arrays[1:]):
        raise ValueError("catalogue and prediction masks must lie in the footprint")
    if any(not x.any() for x in (p25, p30, p32)):
        raise ValueError("historical dot masks must be nonempty")
    distance = distance_transform_edt(~known)
    removed = p30 & ~p32
    added = p32 & ~p30
    within = distance <= 2.0
    return {
        "footprint_pixels": int(footprint.sum()),
        "catalogue_positive_pixels": int(known.sum()),
        "gemsdoe25_dots": int(p25.sum()),
        "gemsdoe30_dots": int(p30.sum()),
        "gemsdoe32_dots": int(p32.sum()),
        "gemsdoe25_and_30_exact_dot_mask_equal": bool(np.array_equal(p25, p30)),
        "gemsdoe32_dots_added_to_30": int(added.sum()),
        "gemsdoe30_dots_removed_to_get_32": int(removed.sum()),
        "removed_within_two_pixels_of_catalogue": int((removed & within).sum()),
        "removed_beyond_two_pixels_of_catalogue": int((removed & ~within).sum()),
        "gemsdoe32_retained_within_two_pixels": int((p32 & within).sum()),
        "gemsdoe32_equals_30_after_two_pixel_exclusion": bool(np.array_equal(p32, p30 & ~within)),
    }


def run() -> dict:
    source = json.loads((ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text())
    winners = {row["repo"]: row for row in source["historical_winners"]}
    manifest = {row["id"]: row for row in json.loads((ROOT / "data/core-manifest.json").read_text())["files"]}
    files = {site: (ROOT / "data" / f"{site}.tif", winners[site]["sha256"])
             for site in ("GEMSDOE25", "GEMSDOE30", "GEMSDOE32")}
    files.update({key: (ROOT / "data/core" / manifest[key]["dest"], manifest[key]["sha256"])
                  for key in ("labels", "sample_submission")})
    for name, (path, expected) in files.items():
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"missing or altered pinned research input: {name}")
    with rasterio.open(files["sample_submission"][0]) as ref:
        sample = ref.read(1)
        footprint = (ref.dataset_mask() > 0) & np.isfinite(sample)
        grid = (ref.shape, ref.crs, ref.transform)
        if ref.count != 1 or ref.crs is None or ref.crs.to_epsg() != 32611 or (ref.transform.a, ref.transform.e, ref.transform.b, ref.transform.d) != (100, -100, 0, 0):
            raise ValueError("mirror template is not the expected 100 m single-band grid")
    masks = {}
    for name in ("labels", "GEMSDOE25", "GEMSDOE30", "GEMSDOE32"):
        with rasterio.open(files[name][0]) as src:
            if (src.shape, src.crs, src.transform) != grid or src.count != 1:
                raise ValueError(f"unaligned research input: {name}")
            values = src.read(1)
            valid = src.dataset_mask() > 0
            if not valid[footprint].all() or not np.isfinite(values[footprint]).all() or not np.isin(values[footprint], [0, 1]).all():
                raise ValueError(f"nonbinary, masked or nonfinite footprint in {name}")
            masks[name] = footprint & (values > 0)
    counts = measure(footprint, masks["labels"], masks["GEMSDOE25"], masks["GEMSDOE30"], masks["GEMSDOE32"])
    return {
        "kind": "HISTORICAL GEOMETRIC AUDIT; not HOLDOUT-DTI or a submission receipt",
        "input_hashes": {name: digest for name, (_, digest) in files.items()},
        "source_files": {site: {"commit": winners[site]["head"], "path": winners[site]["file"]}
                         for site in ("GEMSDOE25", "GEMSDOE30", "GEMSDOE32")},
        "measurement": counts,
        "distance_rule": "Euclidean pixel-center distance <= 2 pixels (100 m pixels); no resampling",
        "provenance": "Pinned participant mirrors; organizer origin and score-to-file receipts are not authenticated.",
        "interpretation": "Equal masks and exclusion are observed geometry, not proof of implementation ancestry, causal score gain, hidden-label recovery or competition acceptance.",
        "candidate_generated": False,
        "slot_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON receipt path")
    args = parser.parse_args()
    try:
        report = run()
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "slot_authorized": False}, indent=2), file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
