#!/usr/bin/env python3
"""Validate a GEMS submission GeoTIFF and diagnose the portal error "Predicted values must be in range [0, 1]".

Usage:
    python scripts/portal_check.py CANDIDATE.tif [--sample data/sample_submission.tif] [--labels data/labels.tif]

Two independent verdicts, both automated (no human step):

1. ``official_format``: what the official spec (competition page 967) requires — one float32 band, EPSG:32611,
   the sample's 3730x3292 grid/transform, every in-footprint pixel finite and in [0,1]; outside the footprint
   either null/NaN (as in the official sample) or a finite value in [0,1].  Additionally *no finite value
   anywhere* may lie outside [0,1] and there may be no +/-inf, because a scorer that range-checks the raw
   array (without applying the nodata mask) would reject such files.
2. ``submit_safe``: the stricter shared export policy (vendor/gems57/validate.py, unchanged): no NaN anywhere,
   zeros outside the footprint, no nodata tag, zero dots on mapped catalogue pixels.  Files we publish must pass
   this; it is what the 0.2778 "-zeros" champion used.

Exit code 0 only if both verdicts pass.  Zeros outside the footprint are accepted (the 0.2778 champion used them and
was scored); an earlier local validator in this repo wrongly rejected such files.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

SENTINELS = (-9999.0, -999.0, 9999.0, -3.4028234663852886e38, 3.4028234663852886e38)


def official_format(candidate: Path, sample: Path) -> dict:
    problems, causes = [], []
    with rasterio.open(sample) as ref:
        fp = np.isfinite(ref.read(1))
        ref_meta = (ref.width, ref.height, ref.crs, ref.transform)
    with rasterio.open(candidate) as src:
        meta = dict(bands=src.count, dtype=src.dtypes[0], crs=str(src.crs), shape=[src.height, src.width],
                    transform=list(src.transform)[:6], nodata=src.nodata, compress=src.profile.get("compress"))
        if src.count != 1:
            problems.append(f"{src.count} bands; exactly 1 required")
        if src.dtypes[0] != "float32":
            problems.append(f"dtype {src.dtypes[0]}; float32 required")
        if (src.width, src.height) != ref_meta[:2]:
            problems.append(f"shape {src.height}x{src.width} != sample {ref_meta[1]}x{ref_meta[0]}")
            return {"ok": False, "problems": problems, "meta": meta, "likely_range_error_causes": causes}
        if src.crs != ref_meta[2] or src.crs is None or src.crs.to_epsg() != 32611:
            problems.append(f"CRS {src.crs}; EPSG:32611 required")
        if src.transform != ref_meta[3]:
            problems.append("transform differs from the official sample")
        a = src.read(1).astype(np.float64)
    fin = np.isfinite(a)
    inside, outside = a[fp], a[~fp]
    n_nan_in = int(np.isnan(inside).sum())
    n_inf = int(np.isinf(a).sum())
    bad_lo = int((a[fin] < 0).sum())
    bad_hi = int((a[fin] > 1).sum())
    if n_nan_in:
        problems.append(f"{n_nan_in} NaN pixels INSIDE the footprint")
        causes.append("NaN inside the scored footprint: NaN fails any 0<=p<=1 comparison")
    if n_inf:
        problems.append(f"{n_inf} infinite pixels")
        causes.append("+/-inf values")
    if bad_lo or bad_hi:
        lo, hi = float(a[fin].min()), float(a[fin].max())
        problems.append(f"{bad_lo + bad_hi} finite pixels outside [0,1] (min {lo:.9g}, max {hi:.9g})")
        if np.isin(a[fin][(a[fin] < 0) | (a[fin] > 1)], SENTINELS).any():
            causes.append("nodata sentinel written as a real value (e.g. -9999 or -3.4e38) — a raw-array range check rejects it")
        if hi > 1 and hi < 1 + 1e-5:
            causes.append("float rounding just above 1.0 (e.g. 1.0000001 after rescaling) — clip/round before writing")
        if lo < 0:
            causes.append("negative values (e.g. logits/standardised scores not passed through a sigmoid)")
        if hi >= 1 + 1e-5:
            causes.append("values above 1 (e.g. counts, percent 0-100, or un-normalised scores)")
    if src_nodata_bad(meta["nodata"]):
        problems.append(f"nodata tag {meta['nodata']} outside [0,1] (readers that ignore the mask see it as data)")
        causes.append("nodata tag outside [0,1]")
    return {"ok": not problems, "problems": problems, "likely_range_error_causes": causes, "meta": meta,
            "footprint_pixels": int(fp.sum()), "nan_inside_footprint": n_nan_in,
            "nan_outside_footprint": int(np.isnan(outside).sum()), "finite_outside_footprint": int(np.isfinite(outside).sum()),
            "infinite_pixels": n_inf, "finite_below_0": bad_lo, "finite_above_1": bad_hi,
            "positive_pixels_inside": int((inside > 0).sum())}


def src_nodata_bad(nodata) -> bool:
    if nodata is None:
        return False
    return bool(np.isfinite(nodata) and not (0.0 <= nodata <= 1.0))


def submit_safe(candidate: Path, sample: Path, labels: Path | None) -> dict:
    from gems57.validate import validate  # shared, unchanged
    with rasterio.open(sample) as ref:
        fp = np.isfinite(ref.read(1))
    cat = None
    if labels is not None and Path(labels).exists():
        with rasterio.open(labels) as ds:
            cat = (ds.read(1) == 1) & fp
    r = validate(candidate, fp, cat)
    return {"ok": bool(r["all_checks_passed"]), "checks": r["checks"], "sha256": r["sha256"], "bytes": r["bytes"],
            "emitted_positive_pixels": r["emitted_positive_pixels"], "min": r["min"], "max": r["max"],
            "validator": "vendor/gems57/validate.py (shared, unchanged)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--sample", type=Path, default=ROOT / "data" / "sample_submission.tif")
    ap.add_argument("--labels", type=Path, default=ROOT / "data" / "labels.tif")
    a = ap.parse_args()
    try:
        off = official_format(a.candidate, a.sample)
        safe = submit_safe(a.candidate, a.sample, a.labels) if off["meta"].get("shape") == [3730, 3292] else {"ok": False, "checks": {}}
    except Exception as exc:  # fail closed
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=1))
        return 2
    out = {"candidate": str(a.candidate), "official_format": off, "submit_safe": safe,
           "ok_to_upload": bool(off["ok"] and safe["ok"]),
           "validator_version": "kanler3-validate-v2 (official-spec + shared gems57 export policy)"}
    print(json.dumps(out, indent=1, default=str))
    return 0 if out["ok_to_upload"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
