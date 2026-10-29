#!/usr/bin/env python3
"""Apply the same checks to any candidate raster, so candidates are compared on one basis.

Reports (all labelled; none is an organizer score):
  * format: grid, dtype, range inside/outside the footprint, NaN outside, finite grid
  * catalogue: dots on the labelled catalogue, dots within 2 px of it
  * SGMC-CAL proxy (vendored evaluate_sgmc_with_ci, n_boot=400), the same proxy used for E2/E3
    and for the H33 B2 reference (0.0641)
Usage: .venv/bin/python scripts/evaluate_candidate_proxy.py <candidate.tif> <receipt.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shared_tools  # noqa: E402

DATA = ROOT / "data"


def main(candidate: Path, receipt: Path) -> dict:
    lock = shared_tools.verify_template()
    if not lock["ok"]:
        raise SystemExit("template lock failed")
    sys.path.insert(0, str(shared_tools.TEMPLATE / "src"))
    import gems32.holdout as H

    ctx = H.load_holdout_context(DATA)
    foot = ctx.foot
    labels = np.asarray(ctx.labels) > 0
    with rasterio.open(candidate) as ds:
        raw = ds.read(1)
        fmt = {
            "crs": str(ds.crs), "shape": list(ds.shape), "dtype": ds.dtypes[0], "bands": ds.count,
            "transform": list(ds.transform)[:6], "nodata": ds.nodata,
        }
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        ref_shape, ref_tr = ds.shape, tuple(ds.transform)[:6]
    fmt["grid_matches_reference"] = bool(tuple(fmt["shape"]) == ref_shape
                                         and np.allclose(fmt["transform"], ref_tr) and "32611" in fmt["crs"])
    inside = raw[foot].astype(np.float64)
    fmt["finite_inside_footprint"] = bool(np.isfinite(inside).all())
    fmt["inside_min"] = float(np.nanmin(inside))
    fmt["inside_max"] = float(np.nanmax(inside))
    fmt["inside_in_0_1"] = bool(np.nanmin(inside) >= 0.0 and np.nanmax(inside) <= 1.0)
    outside = raw[~foot]
    fmt["outside_nan_count"] = int(np.isnan(outside).sum())
    fmt["outside_nonzero_finite"] = int(np.isfinite(outside).sum() - (outside == 0).sum())
    fmt["grid_all_finite"] = bool(np.isfinite(raw).all())

    dots = (np.nan_to_num(raw, nan=0.0) > 0.5) & foot
    dist = distance_transform_edt(~labels)
    cat = {
        "dots": int(dots.sum()),
        "on_catalogue": int((dots & labels).sum()),
        "within_2px_catalogue": int((dots & (dist <= 2)).sum()),
    }
    r = H.evaluate_sgmc_with_ci(dots, ctx, n_boot=400, name="candidate")
    proxy = {
        "label": "SGMC-CAL PROXY (vendored evaluator; NOT an organizer score)",
        "evaluator_version": str(getattr(H, "EVALUATOR_VERSION", "vendored gems32.holdout")),
        "sgmc_prevalence_calibrated_dti": round(float(r["sgmc_prevalence_calibrated_dti"]), 6),
        "sgmc_calibrated_ci95": [round(float(x), 6) for x in r["sgmc_calibrated_ci95"]],
    }
    out = {"kind": "CANDIDATE PROXY CHECK (format, catalogue, SGMC-CAL proxy; not a score)",
           "candidate": candidate.name, "template_lock_commit": lock["commit"],
           "format": fmt, "catalogue": cat, "proxy": proxy}
    receipt.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]), Path(sys.argv[2])), indent=1))
