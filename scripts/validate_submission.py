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
