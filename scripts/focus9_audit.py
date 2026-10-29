#!/usr/bin/env python3
"""Audit the nine focus-site historical TIFFs against the competition grid.

Reads only the hash-pinned focus files in .cache/peers/focus9 (fetched by
scripts/fetch_peer_tifs.py) and the participant-mirror labels/sample. Reports
format facts, dot counts, catalogue overlap, pairwise 3-px dot overlap, and the
vendored hide-and-recover holdout value.

The holdout value is LEAKY for these files: each historical field was generated
from the full catalogue (they remove dots using the catalogue), so the withheld
segments already influenced placement. It is printed only as a diagnostic.
Nothing here is an organizer score.
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
FOCUS = ROOT / ".cache/peers/focus9"
OUT = ROOT / "evidence/focus9-audit-20261029.json"


def load_grid():
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        grid = {"crs": str(ds.crs), "shape": list(ds.shape), "transform": list(ds.transform)[:6]}
    with rasterio.open(DATA / "labels.tif") as ds:
        labels = ds.read(1) > 0
    return foot, labels, grid


def dot_mask(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float64)
        info = {
            "crs": str(ds.crs),
            "shape": list(ds.shape),
            "transform": list(ds.transform)[:6],
            "dtype": ds.dtypes[0],
            "count": ds.count,
            "nodata": None if ds.nodata is None or np.isnan(ds.nodata) else float(ds.nodata),
            "nodata_is_nan": bool(ds.nodata is not None and np.isnan(ds.nodata)),
        }
    return a, info


def main() -> None:
    foot, labels, grid = load_grid()
    tpl_mod = shared_tools.verify_template()
    if not tpl_mod["ok"]:
        raise SystemExit("shared template lock failed: " + "; ".join(tpl_mod["failures"]))
    sys.path.insert(0, str(shared_tools.TEMPLATE / "src"))
    import gems32.holdout as H  # vendored, unmodified, lock-verified

    ctx = H.load_holdout_context(DATA)
    files = sorted(FOCUS.glob("*.tif"))
    masks, rows = {}, []
    for f in files:
        a, info = dot_mask(f)
        in_f = a[foot]
        finite_in = np.isfinite(in_f)
        dots = np.zeros(foot.shape, bool)
        dots[foot] = np.nan_to_num(in_f, nan=0.0) > 0.5
        masks[f.name] = dots
        out_f = a[~foot]
        row = {
            "file": f.name,
            "bytes": f.stat().st_size,
            "grid_match": info["crs"].endswith("32611") and tuple(info["shape"]) == (3730, 3292)
            and np.allclose(info["transform"], grid["transform"]),
            "dtype": info["dtype"],
            "bands": info["count"],
            "nodata": info["nodata"] if not info["nodata_is_nan"] else "nan",
            "in_footprint_nonfinite": int((~finite_in).sum()),
            "in_footprint_min": float(np.nanmin(in_f)),
            "in_footprint_max": float(np.nanmax(in_f)),
            "in_footprint_outside_01": int(((in_f < 0) | (in_f > 1)).sum()),
            "outside_footprint_nonzero_or_finite": int((np.isfinite(out_f) & (out_f != 0)).sum()),
            "dots_gt_0p5": int(dots.sum()),
            "dots_on_catalogue": int((dots & labels).sum()),
            "dots_within_2px_catalogue": int((dots & (distance_transform_edt(~labels) <= 2.0)).sum()),
        }
        rows.append(row)

    names = list(masks)
    dist = {n: distance_transform_edt(~masks[n]) if masks[n].any() else None for n in names}
    overlap = {}
    for a_name in names:
        for b_name in names:
            if a_name == b_name or not masks[a_name].any() or not masks[b_name].any():
                continue
            d = dist[b_name]
            near = d[masks[a_name]] <= 3.0
            overlap[f"{a_name} -> {b_name}"] = round(float(near.mean()), 6)

    # Leaky diagnostic: vendored hide-and-recover scoring of the historical binary dot sets.
    diag = {}
    for n in names:
        r = H.evaluate_hide_and_recover(masks[n], ctx, name=n, n_boot=200)
        diag[n] = {
            "evaluator_version": r["evaluator_version"],
            "pooled_dti_leaky": round(float(r["pooled_dti"]), 6),
            "ci95_cluster_bootstrap": [round(float(x), 6) for x in r["ci95_cluster_bootstrap"]],
            "n_withheld_positives": r["n_withheld_positives"],
        }

    # Off-catalogue proxy: USGS SGMC faults not on/near the catalogue (vendored evaluate_sgmc_with_ci).
    sgmc = {}
    champs = json.loads((ROOT / "registry/focus9_champions.json").read_text())["entries"]
    for n in names:
        r = H.evaluate_sgmc_with_ci(masks[n], ctx, n_boot=200, name=n)
        site = n.split("__")[0]
        owner_value = next((e["score_owner_reported"] for e in champs if e["site"] == site), None)
        sgmc[n] = {
            "site": site,
            "owner_reported_leaderboard_value_UNVERIFIED": owner_value,
            "evaluator_version": r["evaluator_version"],
            "score_label": "HOLDOUT-DTI (proxy)",
            "n_withheld_positives": r["n_withheld_positives"],
            "sgmc_raw_dti": round(float(r["sgmc_raw_pooled_dti"]), 6),
            "sgmc_raw_ci95": [round(float(x), 6) for x in r["sgmc_raw_ci95"]],
            "sgmc_prevalence_calibrated_dti": round(float(r["sgmc_prevalence_calibrated_dti"]), 6),
            "sgmc_calibrated_ci95": [round(float(x), 6) for x in r["sgmc_calibrated_ci95"]],
        }
    result = {
        "kind": "FORMAT + GEOMETRY AUDIT of historical focus TIFFs; leaky holdout diagnostic and SGMC proxy; not a score",
        "sgmc_offcatalogue_proxy": sgmc,
        "template_lock": {"ok": tpl_mod["ok"], "commit": tpl_mod["commit"], "files_checked": tpl_mod["files_checked"]},
        "grid_reference": grid,
        "rows": rows,
        "pairwise_fraction_of_dots_within_3px": overlap,
        "leaky_holdout_diagnostic": diag,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    print(json.dumps({"rows": rows}, indent=1, default=float))
    print(json.dumps({"leaky_holdout_diagnostic": diag}, indent=1, default=float))


if __name__ == "__main__":
    main()
