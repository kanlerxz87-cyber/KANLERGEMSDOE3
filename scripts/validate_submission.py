#!/usr/bin/env python3
"""Read-only GeoTIFF validation with two EXPLICIT local encoding profiles.

The official task requires float32, one band, matching EPSG:32611/100 m grid,
probabilities in [0,1], and null/NaN outside bounds. Whether its wording means
all template-masked padding is not authenticated by a local file check.

`template-mask`: require null/masked pixels outside the sample's valid mask.
`finite-grid`: require finite [0,1] over the entire grid and zero outside that
mask, following the participant shared writer's range-safe representation.
Neither profile guarantees portal acceptance or authorizes a submission slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

VERSION = "submission-format-v2-explicit-encoding"
PROFILES = ("template-mask", "finite-grid")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            result.update(chunk)
    return result.hexdigest()


def validate(template_path: Path, candidate_path: Path, profile: str = "template-mask") -> dict:
    if profile not in PROFILES:
        raise ValueError("Unknown encoding profile")
    errors: list[str] = []
    with rasterio.open(template_path) as ref, rasterio.open(candidate_path) as src:
        checks = {
            "template_single_band": ref.count == 1,
            "single_band": src.count == 1,
            "shape_match": src.shape == ref.shape,
            "crs_match": src.crs is not None and src.crs == ref.crs,
            "transform_match": src.transform == ref.transform,
            "dtype_float32": src.dtypes == ("float32",),
            "template_epsg_32611": ref.crs is not None and ref.crs.to_epsg() == 32611,
            "template_100m_grid": ref.transform.a == 100 and ref.transform.e == -100 and ref.transform.b == 0 and ref.transform.d == 0,
        }
        errors.extend(key for key, ok in checks.items() if not ok)
        base = {"validator": VERSION, "encoding_profile": profile, "template": str(template_path), "candidate": str(candidate_path), "template_sha256": digest(Path(template_path)), "candidate_sha256": digest(Path(candidate_path)), "organizer_acceptance": "NOT_TESTED", "slot_authorized": False, "checks": checks}
        if not checks["shape_match"]:
            return {**base, "ok": False, "errors": errors}
        footprint = (ref.dataset_mask() > 0) & np.isfinite(ref.read(1))
        if not footprint.any():
            return {**base, "ok": False, "errors": errors + ["empty_template_footprint"]}
        arr = src.read(1, masked=False)
        candidate_mask = src.dataset_mask() > 0
        finite = np.isfinite(arr)
        inside = arr[footprint]
        finite_inside = inside[np.isfinite(inside)]
        inside_ok = bool(candidate_mask[footprint].all() and np.isfinite(inside).all() and ((inside >= 0) & (inside <= 1)).all())
        outside = ~footprint
        valid_outside = candidate_mask[outside] & finite[outside]
        null_outside = bool(np.all((~candidate_mask[outside]) | np.isnan(arr[outside])))
        full_range = bool(finite.all() and ((arr >= 0) & (arr <= 1)).all())
        zeros_outside = bool(np.all(arr[outside] == 0))
        encodings = {"template-mask": inside_ok and null_outside, "finite-grid": inside_ok and full_range and zeros_outside}
        checks.update(no_nan_inside_footprint=bool(np.isfinite(inside).all()), no_masked_inside_footprint=bool(candidate_mask[footprint].all()), inside_range_0_1=bool(((inside >= 0) & (inside <= 1)).all()), selected_encoding=bool(encodings[profile]))
        errors.extend(key for key in ("no_nan_inside_footprint", "no_masked_inside_footprint", "inside_range_0_1", "selected_encoding") if not checks[key])
        return {
            **base, "ok": not errors, "errors": errors,
            "bands": src.count, "dtype": list(src.dtypes), "crs": str(src.crs),
            "shape": list(src.shape), "transform": list(src.transform),
            "footprint_pixels": int(footprint.sum()),
            "nonfinite_inside": int((~np.isfinite(inside)).sum()),
            "masked_inside": int((~candidate_mask[footprint]).sum()),
            "finite_range_inside": [float(finite_inside.min()), float(finite_inside.max())] if finite_inside.size else None,
            "valid_outside_footprint": int(valid_outside.sum()),
            "entire_grid_finite_range_0_1": full_range,
            "local_encoding_compatibility": {key: bool(value and all(checks[x] for x in ("template_single_band", "single_band", "shape_match", "crs_match", "transform_match", "dtype_float32", "template_epsg_32611", "template_100m_grid"))) for key, value in encodings.items()},
            "note": "Local contract checks only; template-mirror authenticity, scientific quality and official outside-mask interpretation require separate evidence. A finite nodata sentinel may pass template-mask but fail the portal's whole-grid range scan.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--profile", choices=PROFILES, default="template-mask")
    args = parser.parse_args()
    try:
        result = validate(args.template, args.candidate, args.profile)
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [f"Unable to validate: {exc}"], "validator": VERSION}, indent=2))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
