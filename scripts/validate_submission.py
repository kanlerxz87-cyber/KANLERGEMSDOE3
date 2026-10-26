#!/usr/bin/env python3
"""Validate a submission GeoTIFF: shared-template checks PLUS whole-array [0,1].

The portal error 'Predicted values must be in range [0, 1]' is checked on the
entire array (including outside the footprint), not only inside it: a file
with NaN outside the footprint fails this validator by design. Use the
-zeros variant (outside=0, nodata=None) for upload.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.submission import check_variants  # noqa: E402

# --- Compatibility API preserved from origin/main on merge (2026-10-26) ---
# The forensic session's scripts/audit_rasters.py imports validate(template,
# candidate) with nodata-outside semantics ("submission-format-v1"). It is kept
# verbatim for that audit; this lane's portal gate above uses whole-array [0,1]
# (-zeros) semantics instead. Do not confuse the two: they answer different
# questions, and both are labelled in their outputs.
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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("submission", type=Path)
    ap.add_argument("--template", type=Path, default=ROOT / "data" / "raw" / "sample_submission.tif")
    ap.add_argument("--expected-dots", type=int, default=None)
    args = ap.parse_args()
    checks = check_variants(args.submission, args.template)
    with rasterio.open(args.submission) as s:
        arr = s.read(1)
        whole_finite = bool(np.isfinite(arr).all())
        whole_range = bool(arr.min() >= 0.0 and arr.max() <= 1.0) if whole_finite else False
        nodata = s.nodata
        dots = int((arr == 1.0).sum())
        checks["whole_array_finite"] = whole_finite
        checks["whole_array_in_0_1"] = whole_range
        checks["nodata_is_nan"] = bool(nodata is not None and np.isnan(nodata))
        checks["positive_dots_eq1"] = dots
        checks["portal_range_ok"] = bool(whole_finite and whole_range)
        if args.expected_dots is not None:
            checks["dots_match_expected"] = bool(dots == args.expected_dots)
    ok = bool(checks.get("format_valid")) and checks["portal_range_ok"]
    if args.expected_dots is not None:
        ok = ok and checks["dots_match_expected"]
    checks["validator_verdict"] = "PASS" if ok else "FAIL"
    print(json.dumps(checks, indent=2, default=str))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
