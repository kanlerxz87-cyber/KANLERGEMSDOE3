#!/usr/bin/env python3
"""Validate a candidate GeoTIFF against the organizer's sample/template.

Usage: python scripts/validate_submission.py [--allow-zero-outside] template.tif candidate.tif
Requires rasterio (see requirements.txt). Never writes or repairs the candidate.
- ``validate(template_path, candidate_path)`` enforces the literal DrivenData page-967
  text specification (outside footprint null/nodata/non-finite; in-footprint finite [0, 1]).
- ``audit(candidate_path, template_path)`` runs the full multi-variant format check
  (supporting both the portal-safe ``-zeros.tif`` whole-array finite [0, 1] variant
  that eliminates ``"Predicted values must be in range [0, 1]"`` and the literal
  ``-nan.tif`` official-text twin).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    import numpy as np
    import rasterio
except ImportError as exc:  # fail closed; missing validation dependency is not a pass
    print(json.dumps({"ok": False, "error": f"Missing dependency: {exc}", "validator": "submission-format-v1"}, indent=2))
    sys.exit(2)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(template_path: Path, candidate_path: Path, *, allow_zero_outside: bool = False) -> dict:
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
        outside_values = arr[outside]
        outside_valid_count = int(candidate_valid[outside].sum())
        if allow_zero_outside:
            bad_out = int((candidate_valid[outside] & (outside_values != 0.0)).sum())
            out_of_range_any = bool(np.any(~np.isfinite(arr) & candidate_mask) or np.any(np.isfinite(arr) & ((arr < 0.0) | (arr > 1.0))))
            if bad_out:
                errors.append(f"outside-footprint non-zero valid pixels={bad_out}; expected 0.0 or nodata")
            if out_of_range_any:
                errors.append("whole-array contains finite values outside [0, 1] or unmasked non-finite cells")
        else:
            if outside_valid_count:
                errors.append(f"outside-footprint valid pixels={outside_valid_count}; expected null/nodata")
        whole_array_finite_0_1 = bool(np.all(np.isfinite(arr)) and np.all((arr >= 0.0) & (arr <= 1.0)))
        return {
            "ok": not errors,
            "errors": errors,
            "validator": "submission-format-v1",
            "template": str(template_path),
            "candidate": str(candidate_path),
            "sha256": _sha256(candidate_path),
            "bands": src.count,
            "dtype": list(src.dtypes),
            "crs": str(src.crs),
            "shape": [src.height, src.width],
            "transform": list(src.transform),
            "nodata": None if src.nodata is None else ("NaN" if np.isnan(src.nodata) else float(src.nodata)),
            "footprint_pixels": int(footprint.sum()),
            "nonfinite_inside": int((~np.isfinite(inside_values)).sum()),
            "finite_range_inside": [float(finite_in.min()), float(finite_in.max())] if finite_in.size else None,
            "valid_outside_footprint": outside_valid_count,
            "whole_array_all_finite_0_1": whole_array_finite_0_1,
            "predicted_positive_inside": int((finite_in > 0).sum()),
        }


def audit(candidate_path: Path, template_path: Path, *, strict_zero_outside: bool = False) -> dict:
    """Audit saved GeoTIFF bytes across both DrivenData validator interpretations."""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from vendor.gems24_template.submission import check_variants

    res = check_variants(candidate_path, template_path)
    hard_pass = bool(res["format_valid"])
    whole_ok = bool(res["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"])
    nan_out_ok = bool(res["checks"]["outside_is_nan_official_text"]["pass"])
    variant_ok = whole_ok if strict_zero_outside else (whole_ok or nan_out_ok)
    return {
        "pass": bool(hard_pass and variant_ok),
        "format_valid": bool(hard_pass),
        "whole_array_all_finite_0_1": whole_ok,
        "official_nan_outside_compliant": nan_out_ok,
        "sha256": res["sha256"],
        "bytes": res["bytes"],
        "hard_failures": res["hard_failures"],
        "in_footprint_positive_pixels": res["in_footprint_positive_pixels"],
        "in_footprint_mass": res["in_footprint_mass"],
        "checks": res["checks"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-zero-outside", action="store_true", help="Accept portal-safe 0.0 outside footprint as well as NaN/nodata")
    parser.add_argument("template", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.template, args.candidate, allow_zero_outside=args.allow_zero_outside)
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [f"Unable to validate: {exc}"], "validator": "submission-format-v1"}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
