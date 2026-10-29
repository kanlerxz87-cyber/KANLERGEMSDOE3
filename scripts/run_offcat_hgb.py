#!/usr/bin/env python3
"""Spatially blocked hide-and-recover experiment and final dot candidate.

Method (one shared evaluator, no private metric fork):
  * Positives = the mirrored catalogue (labels.tif == 1, 60,988 px). Each 8-connected
    catalogue component is one fault segment; it is assigned whole to a quadrant fold
    by its centroid (NW/NE/SW/SE). Holdout fold k withholds all segments in quadrant k.
  * Training for fold k uses only visible segments (other quadrants) and excludes every
    pixel within 10 px (1 km) of a withheld segment (buffer). Background samples avoid
    2 px of visible catalogue.
  * Features: the 35-channel stack assembled in memory from the restored owner-mirror
    inputs (19 training bands + 12 LiDAR-derived + 4 GeoDAWN radiometric). No catalogue
    derived band is used. This is NOT the unverified canonical cache; it is a fresh
    in-memory stack, reported as such.
  * Model: HistGradientBoostingClassifier (balanced class weights).
  * Dots: local maxima of the probability surface, greedily thinned to Chebyshev
    spacing 4 px, top-K under a budget of 37,654 split by region area (the recorded
    dot budget of the competition-style lattices).
  * Score: shared gems24 metric.dti_components_exact (alpha 0.2, beta 0.8, 3 px linear
    kernel), pooled over folds (sum TP/FP/FN). 95% CI: cluster bootstrap over withheld
    segments. Per-truth credit reuses the metric's KERNEL_OFFSETS; FP is held fixed
    (documented approximation). Pooled TP is checked against the shared metric.
  * Canary: univariate AUC of each channel (withheld positives vs footprint background).
  * Baseline: uniform random surface selected with the same thinning and budget.
  * Final candidate: model trained on all visible positives, dots over the full footprint.

Usage: python scripts/run_offcat_hgb.py [--out-dir data/candidates] [--final-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "vendor" / "gems24_template"))
import metric as M  # shared, unmodified DTI primitives  # noqa: E402

BUDGET = 37_654
BUFFER_PX = 10
BG_EXCL_PX = 2
SPACING = 4
SEED = 20261029
BOOT = 1000
FOLD_NAMES = ["NW", "NE", "SW", "SE"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_grid():
    with rasterio.open(DATA / "sample_submission.tif") as t:
        tmpl = t.read(1)
        meta = dict(crs=str(t.crs), transform=list(t.transform), shape=list(t.shape))
    footprint = np.isfinite(tmpl)
    with rasterio.open(DATA / "labels.tif") as s:
        lab = s.read(1)
    pos = (lab == 1) & footprint
    return footprint, pos, meta


def load_features(footprint):
    cols, names = [], []
    with rasterio.open(DATA / "training_features.tif") as s:
        for i in range(1, s.count + 1):
            a = s.read(i).astype(np.float32)
            a[a < -1e38] = np.nan
            cols.append(a[footprint]); names.append(f"train_b{i:02d}")
            del a
    with rasterio.open(DATA / "external" / "lidar_scarp_features_u8.tif") as s:
        for i in range(1, s.count + 1):
            cols.append(s.read(i).astype(np.float32)[footprint]); names.append(f"lidar_b{i:02d}")
    with rasterio.open(DATA / "external" / "geodawn_rad_u8.tif") as s:
        for i in range(1, s.count + 1):
            cols.append(s.read(i).astype(np.float32)[footprint]); names.append(f"geodawn_b{i:02d}")
    X = np.column_stack(cols)
    del cols
    nan = np.isnan(X)
    if nan.any():
        med = np.nanmedian(X[::7], axis=0)
        r, c = np.nonzero(nan)
        X[r, c] = med[c]
    return X, names


def quadrant_folds(footprint, pos):
    rows, cols = np.nonzero(footprint)
    rmid = (rows.min() + rows.max()) / 2.0
    cmid = (cols.min() + cols.max()) / 2.0
    rr, cc = np.indices(footprint.shape)
    north = rr < rmid
    west = cc < cmid
    quad = np.where(north, np.where(west, 0, 1), np.where(west, 2, 3)).astype(np.int8)  # NW,NE,SW,SE
    seg_lab, n_seg = ndimage.label(pos, structure=np.ones((3, 3)))
    seg_quad = np.zeros(n_seg + 1, np.int8)
    cen = ndimage.center_of_mass(pos, seg_lab, np.arange(1, n_seg + 1))
    for i, (r, c) in enumerate(cen, start=1):
        seg_quad[i] = (0 if r < rmid else 2) + (0 if c < cmid else 1)
    fold_of_pos = np.full(footprint.shape, -1, np.int8)
    fold_of_pos[pos] = seg_quad[seg_lab[pos]]
    return quad, seg_lab, n_seg, seg_quad, fold_of_pos


def select_dots(P, region, budget, excl=None, spacing=SPACING):
    """Local maxima (5x5) thinned greedily to Chebyshev spacing; top-budget by score."""
    cand = (P == ndimage.maximum_filter(P, size=5)) & region & (P > 0)
    if excl is not None:
        cand &= ~excl
    yy, xx = np.nonzero(cand)
    order = np.argsort(-P[yy, xx], kind="stable")
    H, W = P.shape
    blocked = np.zeros(P.shape, bool)
    dots = np.zeros(P.shape, np.float32)
    n = 0
    for j in order:
        y, x = int(yy[j]), int(xx[j])
        if blocked[y, x]:
            continue
        dots[y, x] = 1.0
        n += 1
        blocked[max(0, y - spacing + 1):min(H, y + spacing), max(0, x - spacing + 1):min(W, x + spacing)] = True
        if n >= budget:
            break
    return dots, n


def train_model(X, fp_index, pos_rows, bg_rows, rng, n_pos, n_bg):
    pr = rng.choice(pos_rows, size=min(n_pos, len(pos_rows)), replace=False)
    br = rng.choice(bg_rows, size=min(n_bg, len(bg_rows)), replace=False)
    idx = np.concatenate([pr, br])
    y = np.concatenate([np.ones(len(pr), np.int8), np.zeros(len(br), np.int8)])
    model = HistGradientBoostingClassifier(
        max_iter=150, learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=100,
        l2_regularization=1.0, class_weight="balanced", random_state=SEED,
    )
    model.fit(X[idx], y)
    return model


def predict_grid(model, X, fp_index, region, footprint):
    out = np.zeros(footprint.shape, np.float32)
    rows = fp_index[region]
    out[region] = model.predict_proba(X[rows])[:, 1].astype(np.float32)
    return out


def dilate_within(mask, r):
    return ndimage.distance_transform_edt(~mask) <= r


def pooled_dti(parts):
    tp = sum(p["TP_w"] for p in parts)
    fp = sum(p["FP_w"] for p in parts)
    fn = sum(p["FN_w"] for p in parts)
    n = sum(p["n_truth"] for p in parts)
    dti = tp / (tp + M.ALPHA * fp + M.BETA * fn + M.EPS)
    return {"TP_w": tp, "FP_w": fp, "FN_w": fn, "n_truth": int(n), "dti": float(dti)}


def per_truth_credit(D, truth_rows_yx):
    """Credit per truth pixel using the shared metric's kernel offsets (same rule as the metric)."""
    H, W = D.shape
    yy, xx = truth_rows_yx
    credit = np.zeros(len(yy), np.float64)
    flat = D.ravel()
    for dy, dx, k in M.KERNEL_OFFSETS:
        ny, nx = yy + dy, xx + dx
        ok = (ny >= 0) & (nx >= 0) & (ny < H) & (nx < W)
        credit[ok] = np.maximum(credit[ok], flat[ny[ok] * W + nx[ok]] * k)
    return credit


def run_holdout(X, names, footprint, pos, quad, seg_lab, n_seg, seg_quad, fold_of_pos, fp_index, rng, flank_px, log):
    results = {"folds": [], "pooled": {}, "canary": [], "baseline_random": None}
    D_all = np.zeros(footprint.shape, np.float32)
    P_all = np.zeros(footprint.shape, np.float32)
    part_list, comp_rows = [], []
    tot_fp_region = footprint.sum()
    per_fold_truth_credit = []
    # Random baseline surface (same thinning/budget logic)
    rand_surface = rng.random(footprint.shape).astype(np.float32) * footprint
    fold_parts_rand = []
    for k in range(4):
        region = footprint & (quad == k)
        withheld = pos & (fold_of_pos == k)
        visible = pos & (fold_of_pos != k) & (fold_of_pos >= 0)
        buf = dilate_within(withheld, BUFFER_PX)
        near_vis = dilate_within(visible, BG_EXCL_PX)
        train_pos_rows = fp_index[visible & ~buf]
        train_bg_mask = footprint & ~buf & ~near_vis
        train_bg_rows = fp_index[train_bg_mask]
        t0 = time.time()
        model = train_model(X, fp_index, train_pos_rows, train_bg_rows, rng, 30_000, 150_000)
        Pk = predict_grid(model, X, fp_index, region, footprint)
        P_all[region] = Pk[region]
        budget_k = int(round(BUDGET * region.sum() / tot_fp_region))
        excl = dilate_within(visible, flank_px) if flank_px > 0 else None
        Dk, nk = select_dots(Pk, region, budget_k, excl=excl)
        D_all += Dk
        catalogue_visible = visible
        truth = withheld
        part = M.dti_components_exact(pred=Dk, truth=truth.astype(np.uint8), valid_mask=footprint, catalogue_mask=catalogue_visible)
        part_list.append(part)
        # Rand baseline for this fold
        Rk, nr = select_dots(rand_surface, region, budget_k, excl=excl)
        fold_parts_rand.append(M.dti_components_exact(pred=Rk, truth=truth.astype(np.uint8), valid_mask=footprint, catalogue_mask=catalogue_visible))
        # Cluster bootstrap bookkeeping: per-component TP/FN
        tr_yy, tr_xx = np.nonzero(truth)
        credit = per_truth_credit(Dk, (tr_yy, tr_xx))
        seg_ids = seg_lab[tr_yy, tr_xx]
        for sid in np.unique(seg_ids):
            m = seg_ids == sid
            comp_rows.append((int(sid), k, int(m.sum()), float(credit[m].sum())))
        results["folds"].append({
            "fold": FOLD_NAMES[k], "withheld_positive_px": int(truth.sum()), "visible_positive_px": int(visible.sum()),
            "train_pos_rows": int(len(train_pos_rows)), "train_bg_rows": int(len(train_bg_rows)),
            "region_footprint_px": int(region.sum()), "budget": budget_k, "dots_placed": int(nk),
            "dti_fold": part["dti"], "TP_w": part["TP_w"], "FP_w": part["FP_w"], "FN_w": part["FN_w"],
            "fit_seconds": round(time.time() - t0, 1),
        })
        log(f"fold {FOLD_NAMES[k]}: withheld={int(truth.sum())} dots={nk} dti={part['dti']:.4f}")
        del model, Pk
    pooled = pooled_dti(part_list)
    pooled_rand = pooled_dti(fold_parts_rand)
    # Consistency check: per-component TP sums to the shared metric pooled TP.
    tp_components = sum(c[3] for c in comp_rows)
    fp_total = pooled["FP_w"]
    consistency = abs(tp_components - pooled["TP_w"])
    n_truth_total = pooled["n_truth"]
    # Cluster bootstrap over withheld segments (FP held fixed)
    comp_arr = np.array([(c[2], c[3]) for c in comp_rows], float)
    rng_b = np.random.default_rng(SEED + 1)
    boots = []
    for _ in range(BOOT):
        pick = rng_b.integers(0, len(comp_arr), len(comp_arr))
        n_b = comp_arr[pick, 0].sum()
        tp_b = comp_arr[pick, 1].sum()
        fn_b = n_b - tp_b
        boots.append(tp_b / (tp_b + M.ALPHA * fp_total + M.BETA * fn_b + M.EPS))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    results["pooled"] = {**pooled, "ci95_low": float(lo), "ci95_high": float(hi),
                         "withheld_segments": int(len(comp_arr)), "withheld_positive_px": int(n_truth_total),
                         "tp_component_consistency_abs_diff": float(consistency)}
    results["baseline_random"] = {"dti": pooled_rand["dti"], "TP_w": pooled_rand["TP_w"], "FP_w": pooled_rand["FP_w"], "FN_w": pooled_rand["FN_w"]}
    # Leakage canary: univariate AUC per channel on withheld positives vs footprint background.
    pos_fp = pos[footprint]  # per footprint-row catalogue flag
    bg_pool = np.flatnonzero(~pos_fp)
    bg_rows = rng.choice(bg_pool, size=min(200_000, len(bg_pool)), replace=False)
    pos_rows = rng.choice(fp_index[pos], size=min(20_000, int(pos.sum())), replace=False)
    yy = np.concatenate([np.ones(len(pos_rows)), np.zeros(len(bg_rows))])
    for j, nm in enumerate(names):
        s = np.concatenate([X[pos_rows, j], X[bg_rows, j]])
        auc = float(roc_auc_score(yy, s))
        results["canary"].append({"feature": nm, "auc_univariate": round(auc, 4), "flag_gt_0_90": bool(auc > 0.90), "flag_lt_0_10": bool(auc < 0.10)})
    return results, D_all, P_all


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=DATA / "candidates")
    ap.add_argument("--evidence", type=Path, default=ROOT / "evidence" / "offcat_hgb_experiment.json")
    ap.add_argument("--final-only", action="store_true")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    logs = []

    def log(msg):
        line = f"[{time.time() - t_start:7.1f}s] {msg}"
        logs.append(line)
        print(line, flush=True)

    footprint, pos, meta = load_grid()
    log(f"grid {meta['shape']} footprint={int(footprint.sum())} positives={int(pos.sum())}")
    X, names = load_features(footprint)
    log(f"features {X.shape} channels={len(names)}")
    fp_index = np.full(footprint.shape, -1, np.int64)
    fp_index[footprint] = np.arange(int(footprint.sum()))
    quad, seg_lab, n_seg, seg_quad, fold_of_pos = quadrant_folds(footprint, pos)
    log(f"catalogue segments={n_seg} per-fold segments={[int((seg_quad[1:] == k).sum()) for k in range(4)]}")
    rng = np.random.default_rng(SEED)

    experiments = {}
    if not args.final_only:
        for name, flank in [("E1_model_no_flank_exclusion", 0), ("E2_model_flank2px_exclusion", 2)]:
            log(f"== {name}")
            res, _, _ = run_holdout(X, names, footprint, pos, quad, seg_lab, n_seg, seg_quad, fold_of_pos, fp_index, rng, flank, log)
            experiments[name] = res
            log(f"{name} pooled DTI {res['pooled']['dti']:.4f} CI [{res['pooled']['ci95_low']:.4f},{res['pooled']['ci95_high']:.4f}] random {res['baseline_random']['dti']:.4f}")
        top_auc = sorted(experiments["E1_model_no_flank_exclusion"]["canary"], key=lambda r: -r["auc_univariate"])[:3]
        log(f"canary top AUC: {top_auc}")

    # Final candidate: all visible positives, no holdout.
    log("== FINAL model on all catalogue positives")
    near_pos = dilate_within(pos, BG_EXCL_PX)
    bg_rows = fp_index[footprint & ~near_pos]
    pos_rows = fp_index[pos]
    model = train_model(X, fp_index, pos_rows, bg_rows, rng, 60_000, 200_000)
    P_final = predict_grid(model, X, fp_index, footprint, footprint)
    np.save(args.out_dir / "P_final.npy", P_final)
    log(f"surface min={float(P_final[footprint].min()):.4g} max={float(P_final[footprint].max()):.4g}")
    summary = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator": "gems24-shared metric.dti_components_exact (gems-segment-pooled-v1 equivalent: alpha 0.2 beta 0.8 3px linear kernel)",
        "features": {"channels": len(names), "names": names, "source": "restored owner mirrors (data/), assembled in memory; not the canonical cache"},
        "holdout_design": "quadrant-blocked hide-and-recover of whole catalogue segments, 10 px buffer, background 2 px from visible catalogue",
        "budget": BUDGET, "spacing_px": SPACING, "seed": SEED,
        "experiments": experiments,
        "grid": meta,
        "log": logs,
    }
    if not args.final_only:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(summary, indent=1, default=float) + "\n")
        log(f"wrote {args.evidence}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
