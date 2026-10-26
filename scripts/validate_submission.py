#!/usr/bin/env python3
"""Conservatively check saved GeoTIFF bytes against a sample's data mask.

Usage: python scripts/validate_submission.py template.tif candidate.tif
The sample mask is a *local conservative* interpretation of outside-footprint
nulls, not proof of DrivenData portal behavior. Never clips or repairs data.
The sample's provenance must be verified separately; this checks format only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
    import rasterio
except ImportError as exc:
    print(json.dumps({"ok": False, "error": f"Missing dependency: {exc}", "validator": "submission-format-v2"}, indent=2))
    sys.exit(2)


VERSION = "submission-format-v2"


def validate(template_path: Path, candidate_path: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    with rasterio.open(template_path) as ref, rasterio.open(candidate_path) as src:
        if ref.count != 1:
            errors.append(f"template bands={ref.count}; expected exactly 1")
        if src.driver != "GTiff":
            errors.append(f"candidate driver={src.driver}; expected GTiff")
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
        # A sidecar mask is not part of a standalone single-TIFF upload.
        if any(str(p).lower().endswith(".msk") for p in src.files):
            errors.append("candidate depends on an external .msk sidecar; the TIFF must stand alone")
        if src.width != ref.width or src.height != ref.height or ref.count != 1 or src.count != 1:
            return {"ok": False, "errors": errors, "warnings": warnings,
                    "template": str(template_path), "candidate": str(candidate_path), "validator": VERSION}

        footprint = ref.dataset_mask() > 0
        ref_values = ref.read(1, masked=False)
        if not footprint.any():
            errors.append("template footprint is empty; cannot validate predictions")
        if not np.isfinite(ref_values[footprint]).all():
            errors.append("template mask includes non-finite sample pixels; footprint is ambiguous")

        arr = src.read(1, masked=False)
        candidate_mask = src.dataset_mask() > 0
        inside_values = arr[footprint]
        missing_inside = int((~candidate_mask[footprint]).sum())
        if missing_inside:
            errors.append(f"masked/nodata in-footprint pixels={missing_inside}")
        nonfinite_inside = int((~np.isfinite(inside_values)).sum())
        if nonfinite_inside:
            errors.append(f"non-finite in-footprint pixels={nonfinite_inside}")
        finite_in = inside_values[np.isfinite(inside_values)]
        if finite_in.size and (float(finite_in.min()) < 0 or float(finite_in.max()) > 1):
            errors.append(f"in-footprint range=[{float(finite_in.min())}, {float(finite_in.max())}]; expected [0,1]")

        # NaN is explicitly permitted outside the area; masked finite nodata is
        # locally treated as null. Infinity is not NaN or a valid probability.
        outside = ~footprint
        outside_valid_count = int((candidate_mask & outside & ~np.isnan(arr)).sum())
        if outside_valid_count:
            errors.append(f"outside-footprint unmasked non-null pixels={outside_valid_count}; local policy expects null/nodata")
        infinity_count = int(np.isinf(arr).sum())
        if infinity_count:
            errors.append(f"infinite pixels anywhere in TIFF={infinity_count}")

        nan_count = int(np.isnan(arr).sum())
        finite_out_of_range = int((np.isfinite(arr) & ((arr < 0) | (arr > 1))).sum())
        whole_grid_in_range = nan_count == 0 and infinity_count == 0 and finite_out_of_range == 0
        if not whole_grid_in_range:
            warnings.append("raw whole-grid values include non-finite or out-of-range cells; portal handling of nodata/masks is unverified")

        return {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings,
            "validator": VERSION,
            "policy": "conservative sample-mask check; not an organizer acceptance or submission approval",
            "template": str(template_path),
            "candidate": str(candidate_path),
            "bands": src.count,
            "dtype": list(src.dtypes),
            "crs": str(src.crs),
            "shape": [src.height, src.width],
            "transform": list(src.transform),
            "footprint_pixels": int(footprint.sum()),
            "nonfinite_inside": nonfinite_inside,
            "finite_range_inside": [float(finite_in.min()), float(finite_in.max())] if finite_in.size else None,
            "valid_outside_footprint": outside_valid_count,
            "nan_pixels_whole_grid": nan_count,
            "infinite_pixels_whole_grid": infinity_count,
            "finite_out_of_range_whole_grid": finite_out_of_range,
            "raw_whole_grid_finite_in_range": whole_grid_in_range,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.template, args.candidate)
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [f"Unable to validate: {exc}"], "validator": VERSION}, indent=2))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
