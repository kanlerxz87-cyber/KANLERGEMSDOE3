#!/usr/bin/env python3
"""E1 leakage canary (pre-registered in evidence/preregistration-20261029-kanler-s3.json).

Each feature is tested ALONE: AUC of withheld-catalogue truth vs. active background
inside every vendored hide-and-recover cell. AUC > 0.90 = leakage until disproved.
d_visible (distance to VISIBLE faults only) is included as the catalogue-derived feature.
Reads the lock-verified vendored holdout; nothing is copied from another submission.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shared_tools  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "evidence/kanler-s3-e1-canary-20261029.json"
RNG = np.random.default_rng(20261029)
SENTINEL = -1e30


def load_band(path: Path, band: int, nodata_is_sentinel: bool = True) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(band).astype(np.float64)
        nd = ds.nodata
    bad = ~np.isfinite(a)
    if nd is not None and not np.isnan(nd):
        bad |= a == nd
    if nodata_is_sentinel:
        bad |= a < SENTINEL
    a[bad] = np.nan
    return a


def ridge_response(a: np.ndarray, sigma: float) -> np.ndarray:
    """Largest-magnitude negative Hessian eigenvalue (bright ridge) after Gaussian smoothing."""
    fill = np.where(np.isfinite(a), a, np.nanmedian(a))
    s = gaussian_filter(fill, sigma)
    gyy = np.gradient(np.gradient(s, axis=0), axis=0)
    gxx = np.gradient(np.gradient(s, axis=1), axis=1)
    gxy = np.gradient(np.gradient(s, axis=0), axis=1)
    tr, det = gxx + gyy, gxx * gyy - gxy * gxy
    lam_min = tr / 2 - np.sqrt(np.maximum((tr / 2) ** 2 - det, 0))
    return -lam_min  # positive where a bright ridge is present


def auc_cells(feature: np.ndarray, cells, foot: np.ndarray) -> dict:
    per_cell = []
    for cell in cells:
        sl = cell.bbox
        f = feature[sl]
        act = cell.active_sub & np.isfinite(f) & foot[sl]
        pos = np.zeros(f.shape, bool)
        ty, tx = cell.truth_coords
        pos[ty, tx] = True
        pos &= act
        neg = act & ~pos
        n_pos, n_neg = int(pos.sum()), int(neg.sum())
        if n_pos < 50 or n_neg < 50:
            continue
        pv = f[pos]
        nv = f[neg]
        if nv.size > 300_000:
            nv = RNG.choice(nv, 300_000, replace=False)
        y = np.r_[np.ones(pv.size), np.zeros(nv.size)]
        s = np.r_[pv, nv]
        per_cell.append(float(roc_auc_score(y, s)))
    arr = np.array(per_cell)
    return {"auc_mean": round(float(arr.mean()), 4), "auc_min": round(float(arr.min()), 4),
            "auc_max": round(float(arr.max()), 4), "cells": len(per_cell)}


def main() -> None:
    tpl = shared_tools.verify_template()
    if not tpl["ok"]:
        raise SystemExit("template lock failed")
    sys.path.insert(0, str(shared_tools.TEMPLATE / "src"))
    import gems32.holdout as H

    ctx = H.load_holdout_context(DATA)
    foot = ctx.foot
    results = {}

    # Catalogue-derived feature: distance to VISIBLE faults only, per cell (leak-free by construction).
    dvis_auc = []
    for cell in ctx.cells:
        d = distance_transform_edt(~cell.visible_full)  # full grid; auc_cells slices by the cell bbox
        dvis_auc.append(auc_cells(d, [cell], foot))
    results["d_visible_catalogue_only_visible_faults"] = {
        "auc_mean": round(float(np.mean([r["auc_mean"] for r in dvis_auc])), 4),
        "auc_min": round(float(np.min([r["auc_min"] for r in dvis_auc])), 4),
        "auc_max": round(float(np.max([r["auc_max"] for r in dvis_auc])), 4),
        "cells": int(sum(r["cells"] for r in dvis_auc)),
        "verdict": "LEAKAGE" if max(r["auc_max"] for r in dvis_auc) > 0.90 else "pass (<=0.90)",
    }

    with rasterio.open(DATA / "training_features.tif") as ds:
        names = [f"band{i:02d}" for i in range(1, ds.count + 1)]
    prep = json.loads((DATA / "prepared_manifest.json").read_text())["bands"]
    names = [b["name"] for b in prep]

    feats = {}
    for i, nm in enumerate(names, start=1):
        feats[nm] = load_band(DATA / "training_features.tif", i)
    feats["ridge_rtp_s1p5"] = ridge_response(feats["rtp"], 1.5)
    feats["geod_shear_smooth_s1p5"] = gaussian_filter(np.where(np.isfinite(feats["geod_shearrate"]), feats["geod_shearrate"], 0.0), 1.5)

    for nm, arr in feats.items():
        a = arr.copy()
        a[~foot] = np.nan
        if not np.isfinite(a[foot]).all():
            a = np.where(np.isfinite(a), a, np.nanmedian(a[foot]))
        r = auc_cells(a, ctx.cells, foot)
        r["verdict"] = "LEAKAGE" if r["auc_max"] > 0.90 else ("pass (<=0.90)" if r["auc_max"] <= 0.90 else "pass")
        results[nm] = r

    for nm in ("lidar_scarp_features_u8", "geodawn_rad_u8"):
        with rasterio.open(DATA / "external" / (nm + ".tif")) as ds:
            n = ds.count
        for b in range(1, n + 1):
            a = load_band(DATA / "external" / (nm + ".tif"), b, nodata_is_sentinel=False)
            a[~foot] = np.nan
            if not np.isfinite(a[foot]).all():
                a = np.where(np.isfinite(a), a, np.nanmedian(a[foot]))
            r = auc_cells(a, ctx.cells, foot)
            r["verdict"] = "LEAKAGE" if r["auc_max"] > 0.90 else "pass (<=0.90)"
            results[f"{nm}_b{b}"] = r

    worst = max(results.items(), key=lambda kv: kv[1]["auc_max"])
    out = {
        "kind": "E1 LEAKAGE CANARY (each feature alone; holdout cells; not a score)",
        "evaluator": "vendored gems32 load_holdout_context (lock-verified)",
        "results": results,
        "max_auc_feature": {"name": worst[0], "auc_max": worst[1]["auc_max"]},
        "n_leakage_flags": int(sum(1 for v in results.values() if v["verdict"] == "LEAKAGE")),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"max_auc_feature": out["max_auc_feature"], "n_leakage_flags": out["n_leakage_flags"]}, indent=1))
    for k, v in results.items():
        print(f"{k:34s} mean={v['auc_mean']:.3f} max={v['auc_max']:.3f} cells={v['cells']} {v['verdict']}")


if __name__ == "__main__":
    main()
