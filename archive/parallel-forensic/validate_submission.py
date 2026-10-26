#!/usr/bin/env python3
"""Validate a candidate GeoTIFF against the organizer's sample/template.

Usage: python scripts/validate_submission.py template.tif candidate.tif
Requires rasterio (see requirements.txt). Never writes or repairs the candidate.
The template's valid-data mask defines the footprint; candidate pixels outside it
must be nodata/masked/non-finite. In-footprint predictions must be finite [0, 1].
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
    import rasterio
except ImportError as exc:  # fail closed; missing validation dependency is not a pass
    print(json.dumps({"ok": False, "error": f"Missing dependency: {exc}", "validator": "submission-format-v1"}, indent=2))
    sys.exit(2)


def validate(template_path: Path, candidate_path: Path) -> dict:
    errors: list[str] = []
    with rasterio.open(template_path) as ref, rasterio.open(candidate_path) as src:
        if src.count != 1:
            errors.append(f"candidate bands={src.count}; expected exactly 1")
        if src.width != ref.width or src.height != ref.height:
            errors.append(f"shape candidate={(src.height, src.width)} template={(ref.height, ref.width)}")
        if src.crs != ref.crs:
            errors.append(f"CRS candidate={src.crs}; template={ref.crs}")
        if src.transform != ref.transform:
            errors.append(f"transform candidate={src.transform}; template={ref.transform}")
        if src.dtypes != ("float32",):
            errors.append(f"dtype candidate={src.dtypes}; expected float32")
        if ref.crs is None or ref.crs.to_epsg() != 32611:
            errors.append(f"template CRS must identify as EPSG:32611; found {ref.crs}")
        if src.width != ref.width or src.height != ref.height:
            return {"ok": False, "errors": errors, "template": str(template_path), "candidate": str(candidate_path), "validator": "submission-format-v1"}
        footprint = ref.dataset_mask() > 0
        arr = src.read(1, masked=False)
        candidate_mask = src.dataset_mask() > 0
        candidate_valid = candidate_mask & np.isfinite(arr)
        inside_values = arr[footprint]
        missing_inside = int((~candidate_mask[footprint]).sum())
        if missing_inside:
            errors.append(f"masked/nodata in-footprint pixels={missing_inside}")
        if not np.all(np.isfinite(inside_values)):
            errors.append(f"non-finite in-footprint pixels={int((~np.isfinite(inside_values)).sum())}")
        finite_in = inside_values[np.isfinite(inside_values)]
        if finite_in.size and (float(finite_in.min()) < 0 or float(finite_in.max()) > 1):
            errors.append(f"in-footprint range=[{float(finite_in.min())}, {float(finite_in.max())}]; expected [0,1]")
        outside = ~footprint
        outside_valid_count = int(candidate_valid[outside].sum())
        if outside_valid_count:
            errors.append(f"outside-footprint valid pixels={outside_valid_count}; expected null/nodata")
        return {
            "ok": not errors,
            "errors": errors,
            "validator": "submission-format-v1",
            "template": str(template_path),
            "candidate": str(candidate_path),
            "bands": src.count,
            "dtype": list(src.dtypes),
            "crs": str(src.crs),
            "shape": [src.height, src.width],
            "transform": list(src.transform),
            "footprint_pixels": int(footprint.sum()),
            "nonfinite_inside": int((~np.isfinite(inside_values)).sum()),
            "finite_range_inside": [float(finite_in.min()), float(finite_in.max())] if finite_in.size else None,
            "valid_outside_footprint": outside_valid_count,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.template, args.candidate)
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [f"Unable to validate: {exc}"], "validator": "submission-format-v1"}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
