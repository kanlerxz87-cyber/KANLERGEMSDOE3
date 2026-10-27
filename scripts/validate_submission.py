#!/usr/bin/env python3
"""Read-only saved-byte validation with explicit LOCAL encoding profiles.

The official task requires float32, one band, the reference grid, probabilities
in [0,1], and null/NaN outside bounds. A participant-mirror mask is not organizer
authentication. `template-mask` requires null/masked padding; `finite-grid`
requires finite [0,1] everywhere and zero padding. `masked-finite` requires
both masked padding and finite raw [0,1] values across the whole grid. It checks
for an internal TIFF mask without an external sidecar. These are local checks,
not guarantees of portal acceptance, scientific eligibility or authorization to
spend a slot. No file is clipped, repaired, rewritten or promoted by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

VERSION = "submission-format-v4-masked-finite-diagnostics"
PROFILES = ("template-mask", "finite-grid", "masked-finite")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            result.update(chunk)
    return result.hexdigest()


def validate(template_path: Path, candidate_path: Path, profile: str = "template-mask", expected_dots: int | None = None, *, allow_zero_outside: bool | None = None) -> dict:
    if allow_zero_outside is not None and type(allow_zero_outside) is not bool:
        raise ValueError("Legacy allow_zero_outside flag must be a boolean")
    if allow_zero_outside is not None and profile != "template-mask":
        raise ValueError("Use a named profile or the legacy flag, not both")
    if profile not in PROFILES:
        raise ValueError("Unknown encoding profile")
    if expected_dots is not None and (type(expected_dots) is not int or expected_dots < 0):
        raise ValueError("Expected positive-pixel count must be a nonnegative integer")
    template_path, candidate_path = Path(template_path), Path(candidate_path)
    errors: list[str] = []
    with rasterio.open(template_path) as ref, rasterio.open(candidate_path) as src:
        template_values = ref.read(1)
        template_mask = ref.dataset_mask() > 0
        checks = {
            "template_single_band": ref.count == 1,
            "single_band": src.count == 1,
            "shape_match": src.shape == ref.shape,
            "crs_match": src.crs is not None and src.crs == ref.crs,
            "transform_match": src.transform == ref.transform,
            "dtype_float32": src.dtypes == ("float32",),
            "template_epsg_32611": ref.crs is not None and ref.crs.to_epsg() == 32611,
            "template_100m_grid": ref.transform.a == 100 and ref.transform.e == -100 and ref.transform.b == 0 and ref.transform.d == 0,
            "template_mask_unambiguous": not bool((template_mask & ~np.isfinite(template_values)).any()),
            "standalone_without_sidecars": all(Path(name).resolve() == candidate_path.resolve() for name in src.files),
        }
        errors.extend(key for key, ok in checks.items() if not ok)
        sha = digest(candidate_path)
        base = {
            "validator": VERSION, "encoding_profile": profile,
            "template": str(template_path), "candidate": str(candidate_path),
            "template_sha256": digest(template_path), "candidate_sha256": sha, "sha256": sha,
            "organizer_acceptance": "NOT_TESTED", "portal_acceptance_verified": False,
            "submission_authorized": False, "slot_authorized": False, "checks": checks,
        }
        if not checks["shape_match"]:
            return {**base, "ok": False, "errors": errors}
        footprint = template_mask & np.isfinite(template_values)
        if not footprint.any():
            return {**base, "ok": False, "errors": errors + ["empty_template_footprint"]}
        values = src.read(1, masked=False)
        candidate_mask = src.dataset_mask() > 0
        finite = np.isfinite(values)
        inside = values[footprint]
        finite_inside = inside[np.isfinite(inside)]
        inside_ok = bool(candidate_mask[footprint].all() and np.isfinite(inside).all() and ((inside >= 0) & (inside <= 1)).all())
        outside = ~footprint
        valid_outside = candidate_mask[outside] & finite[outside]
        null_outside = bool(np.all((~candidate_mask[outside]) | np.isnan(values[outside])))
        full_range = bool(finite.all() and ((values >= 0) & (values <= 1)).all())
        zeros_outside = bool(np.all(values[outside] == 0))
        no_infinity = not bool(np.isinf(values).any())
        positive_pixels = int((np.isfinite(inside) & (inside > 0)).sum())
        finite_values = values[finite]
        below_zero = finite & (values < 0)
        above_one = finite & (values > 1)
        out_of_range = below_zero | above_one
        raw_range_diagnostics = {
            "finite_min": float(finite_values.min()) if finite_values.size else None,
            "finite_max": float(finite_values.max()) if finite_values.size else None,
            "nonfinite_pixels": int((~finite).sum()),
            "nan_pixels": int(np.isnan(values).sum()),
            "infinite_pixels": int(np.isinf(values).sum()),
            "nonfinite_inside_footprint": int((~finite & footprint).sum()),
            "nonfinite_outside_footprint": int((~finite & outside).sum()),
            "nonfinite_masked_pixels": int((~finite & ~candidate_mask).sum()),
            "finite_below_zero": int(below_zero.sum()),
            "finite_above_one": int(above_one.sum()),
            "out_of_range_inside_footprint": int((out_of_range & footprint).sum()),
            "out_of_range_outside_footprint": int((out_of_range & outside).sum()),
            "out_of_range_masked_pixels": int((out_of_range & ~candidate_mask).sum()),
        }
        # The strictest local profile protects against raw whole-grid range
        # scans while leaving every outside-footprint cell masked.  A mask can
        # be internal to the TIFF, or be a nodata value; standalone checking
        # separately rejects external sidecar masks.  Whether the portal
        # honours that encoding remains an organizer question.
        masked_outside = bool((~candidate_mask[outside]).all())
        encodings = {
            "template-mask": inside_ok and null_outside and no_infinity,
            "finite-grid": inside_ok and full_range and zeros_outside,
            "masked-finite": inside_ok and masked_outside and full_range,
        }
        if allow_zero_outside is True and not encodings["template-mask"] and encodings["finite-grid"]:
            profile = "finite-grid"
        base["encoding_profile"] = profile
        base["legacy_allow_zero_outside"] = allow_zero_outside
        checks.update(
            no_nan_inside_footprint=bool(np.isfinite(inside).all()),
            no_masked_inside_footprint=bool(candidate_mask[footprint].all()),
            inside_range_0_1=bool(((inside >= 0) & (inside <= 1)).all()),
            no_infinite_pixels_anywhere=no_infinity,
            selected_encoding=bool(encodings[profile]),
            expected_positive_pixels_match=expected_dots is None or expected_dots == positive_pixels,
        )
        for key in ("no_nan_inside_footprint", "no_masked_inside_footprint", "inside_range_0_1", "no_infinite_pixels_anywhere", "selected_encoding", "expected_positive_pixels_match"):
            if not checks[key]:
                errors.append(key)
        structural_ok = all(checks[key] for key in (
            "template_single_band", "single_band", "shape_match", "crs_match", "transform_match", "dtype_float32",
            "template_epsg_32611", "template_100m_grid", "template_mask_unambiguous", "standalone_without_sidecars",
        ))
        return {
            **base, "ok": not errors, "errors": errors,
            "bands": src.count, "dtype": list(src.dtypes), "crs": str(src.crs),
            "shape": list(src.shape), "transform": list(src.transform),
            "footprint_pixels": int(footprint.sum()), "positive_pixels": positive_pixels,
            "nonfinite_inside": int((~np.isfinite(inside)).sum()),
            "masked_inside": int((~candidate_mask[footprint]).sum()),
            "infinite_pixels_whole_grid": int(np.isinf(values).sum()),
            "finite_range_inside": [float(finite_inside.min()), float(finite_inside.max())] if finite_inside.size else None,
            "valid_outside_footprint": int(valid_outside.sum()),
            "outside_null_or_nan": bool(null_outside and no_infinity),
            "entire_grid_finite_range_0_1": full_range, "raw_whole_grid_finite_in_range": full_range,
            "raw_range_diagnostics": raw_range_diagnostics,
            "masked_outside_footprint": masked_outside,
            "local_encoding_compatibility": {key: bool(value and structural_ok) for key, value in encodings.items()},
            "note": "Local contract only. A masked sentinel may pass template-mask but fail a portal-wide range scan; masked-finite checks both masks and raw values, without guaranteeing portal acceptance. Positive-pixel count is not an invented dot mask for soft-surface uniqueness. No scientific or portal approval.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path, help="Template then candidate; or candidate with --template")
    parser.add_argument("second", type=Path, nargs="?")
    parser.add_argument("--template", type=Path)
    parser.add_argument("--profile", choices=PROFILES, default="template-mask")
    parser.add_argument("--expected-dots", type=int, help="Optional positive-pixel count check; not a soft-surface dot definition")
    parser.add_argument("--allow-zero-outside", action="store_true", default=None, help="Legacy opt-in: select finite-grid only if the saved file passes it; never portal approval")
    args = parser.parse_args()
    if args.template is not None:
        if args.second is not None:
            parser.error("Use either TEMPLATE CANDIDATE or CANDIDATE --template TEMPLATE")
        template, candidate = args.template, args.first
    else:
        if args.second is None:
            parser.error("Supply both TEMPLATE CANDIDATE or use --template")
        template, candidate = args.first, args.second
    try:
        result = validate(template, candidate, args.profile, args.expected_dots, allow_zero_outside=args.allow_zero_outside)
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [f"Unable to validate: {exc}"], "validator": VERSION, "portal_acceptance_verified": False, "submission_authorized": False}, indent=2))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
