#!/usr/bin/env python3
"""Measure historic D2.8/B2 support identity; never infer hidden truth or score causation."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from restore_workspace import DEFAULT_CACHE, restore, sha256_file


def run(cache: Path) -> dict:
    restore(cache, fetch=False, anchors=True, features=False)
    base = cache / "data/anchors/GEMSDOE25.tif"
    child = cache / "data/anchors/GEMSDOE32.tif"
    with rasterio.open(cache / "data/sample_submission.tif") as src:
        valid = np.isfinite(src.read(1)); grid = (src.shape, src.crs, src.transform)
    def read_aligned(path):
        with rasterio.open(path) as src:
            if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
                raise ValueError(f"grid mismatch: {path}")
            return src.read(1)
    catalogue = (read_aligned(cache / "data/existing_faults.tif") > 0) & valid
    if not catalogue.any():
        raise ValueError("empty known-fault catalogue")
    b = read_aligned(base); c = read_aligned(child)
    if not np.isfinite(b[valid]).all() or not np.isfinite(c[valid]).all():
        raise ValueError("invalid on-footprint values")
    b = (b > 0) & valid; c = (c > 0) & valid
    distances = distance_transform_edt(~catalogue)
    removed = b & ~c
    counts = {}
    for name, selection in (("distance_0", distances == 0), ("distance_1", distances == 1),
                            ("distance_sqrt2", np.isclose(distances, np.sqrt(2), rtol=0, atol=1e-12)),
                            ("distance_2", distances == 2), ("distance_gt_2", distances > 2)):
        counts[name] = int((removed & selection).sum())
    return {"schema": "gems-anchor-lineage-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "evidence_class": "RASTER-MEASUREMENT; no leaderboard score or hidden-label causation",
            "base": {"site": "GEMSDOE25", "sha256": sha256_file(base), "positive_pixels": int(b.sum())},
            "child": {"site": "GEMSDOE32", "sha256": sha256_file(child), "positive_pixels": int(c.sum())},
            "pixel_size_m": 100, "catalogue_sha256": sha256_file(cache / 'data/existing_faults.tif'),
            "child_is_subset_of_base": bool(np.all(~c | b)),
            "child_exactly_base_excluding_catalogue_distance_le_2px": bool(np.array_equal(c, b & (distances > 2))),
            "removed_pixels": int(removed.sum()), "removed_distance_classes_px": counts,
            "child_at_most_2px_from_catalogue": int((c & (distances <= 2)).sum()),
            "caveat": "Distances use the third-party mirrored catalogue; its hash does not authenticate organizer origin. These observations do not prove a score or causal effect."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--output', type=Path)
    a = parser.parse_args()
    try:
        report = run(a.cache)
        text = json.dumps(report, indent=2, allow_nan=False) + '\n'
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(text, encoding='utf-8')
        print(text, end='')
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"LINEAGE AUDIT FAILED: {exc}", file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
