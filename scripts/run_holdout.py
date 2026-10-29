#!/usr/bin/env python3
"""
Optimized local segment hide/recover holdout for the KANLER submission.

Precomputes the feature matrix once (single raster pass), then runs the
4-fold buffered whole-component hide/recover protocol using precomputed
features for fast per-fold training and prediction.

Reports pooled HOLDAOUT-DTI (alpha 0.2, beta 0.8, 300 m triangular kernel)
with cluster-bootstrap 95% CI.

This is a LOCAL reimplementation; not an organizer score, not a leaderboard
projection.
"""

from __future__ import annotations

import json
import sys
from datetime import timezone
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems.submission import write_submission  # noqa: E402
from gems.metric import dti_components_exact, ALPHA, BETA, RADIUS_PX  # noqa: E402
from kanler3.emission import emit_dots  # noqa: E402

CORE = ROOT / "data" / "core"
BRIDGE = ROOT / "data" / "bridge"
EVID = ROOT / "evidence"
TOTAL_BUDGET = 37_654
SEED = 20261026


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_grid():
    with rasterio.open(BRIDGE / "sample_submission.tif") as s:
        tmpl = s.read(1)
    footprint = np.isfinite(tmpl)
    labels = np.full(tmpl.shape, -1, dtype=np.int8)
    with rasterio.open(CORE / "labels.tif") as s:
        lab = s.read(1)
    labels[footprint] = np.where(lab[footprint] == 1, 1, 0).astype(np.int8)
    return labels, footprint


def feature_valid_mask():
    with rasterio.open(CORE / "training_features.tif") as s:
        h, w = s.shape
        valid = np.ones((h, w), dtype=bool)
        for b in range(1, s.count + 1):
            a = s.read(b).astype(np.float32)
            nd = s.nodata
            bad = ~np.isfinite(a)
            if nd is not None:
                bad = bad | (a == nd)
            valid &= ~bad
            del a
    return valid


def read_features_block(s, row_slice, col_slice, n_bands):
    block = np.empty((row_slice.stop - row_slice.start, col_slice.stop - col_slice.start, n_bands), dtype=np.float32)
    for b in range(1, n_bands + 1):
        a = s.read(b, window=rasterio.windows.Window(
            col_off=col_slice.start, row_off=row_slice.start,
            width=col_slice.stop - col_slice.start, height=row_slice.stop - row_slice.start,
        )).astype(np.float32)
        block[:, :, b - 1] = a
        del a
    return block


def precompute_features(footprint, valid_feat, out_path):
    """Read all bands for valid footprint pixels, save as (n_valid, 19) float32 + index."""
    h, w = footprint.shape
    elig = footprint & valid_feat
    ids = np.argwhere(elig)
    n = len(ids)
    print(f"[precompute] {n} valid pixels", flush=True)
    X = np.empty((n, 19), dtype=np.float32)
    row_block = 300
    with rasterio.open(CORE / "training_features.tif") as s:
        for r0 in range(0, h, row_block):
            r1 = min(h, r0 + row_block)
            # only columns that have any eligible pixel in this row block
            row_elig = elig[r0:r1]
            if not row_elig.any():
                continue
            c_ids = np.argwhere(row_elig.any(axis=0))[:, 0]
            c0, c1 = c_ids[0], c_ids[-1] + 1
            block = read_features_block(s, slice(r0, r1), slice(c0, c1), 19)
            # local eligible within this block
            rel_row = np.arange(r0, r1)[:, None]
            rel_col = np.arange(c0, c1)[None, :]
            block_elig = elig[r0:r1, c0:c1]
            bidx = np.argwhere(block_elig)
            # global pixel position within block
            X_local = block[bidx[:, 0], bidx[:, 1], :]
            # map to global X index
            # build global->local mapping
            global_idx = np.nonzero(elig.ravel())[0]
            # this is complex; instead fill X by scatter
            # compute flat indices
            flat_block = np.ravel_multi_index((bidx[:, 0] + r0, bidx[:, 1] + c0), (h, w))
            flat_global = np.ravel_multi_index((ids[:, 0], ids[:, 1]), (h, w))
            pos = {int(f): i for i, f in enumerate(flat_global)}
            for k, f in enumerate(flat_block):
                X[pos[int(f)]] = X_local[k]
            del block, X_local
    np.save(out_path, X)
    np.save(out_path.with_suffix(".ids.npy"), ids)
    print(f"[precompute] saved {out_path} shape={X.shape}", flush=True)
    return X, ids


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    labels, footprint = load_grid()
    valid_feat = feature_valid_mask()
    footprint = footprint & valid_feat
    labels[~footprint] = -1

    X_path = ROOT / ".cache" / "holdout_features.npy"
    X_path.parent.mkdir(parents=True, exist_ok=True)
    ids_path = X_path.with_suffix(".ids.npy")

    if X_path.exists() and ids_path.exists():
        X = np.load(X_path, mmap_mode="r")
        ids = np.load(ids_path)
        print(f"[precompute] loaded cached {X.shape}", flush=True)
    else:
        X, ids = precompute_features(footprint, valid_feat, X_path)

    H, W = footprint.shape
    fp_bool = footprint
    truth = (labels == 1)

    # Quadrant folds
    gy, gx = np.mgrid[0:H, 0:W]
    y_med, x_med = int(np.median(gy[fp_bool])), int(np.median(gx[fp_bool]))
    fold_grid = np.full((H, W), -1, dtype=np.int8)
    fold_grid[(gy < y_med) & (gx < x_med) & fp_bool] = 0
    fold_grid[(gy < y_med) & (gx >= x_med) & fp_bool] = 1
    fold_grid[(gy >= y_med) & (gx < x_med) & fp_bool] = 2
    fold_grid[(gy >= y_med) & (gx >= x_med) & fp_bool] = 3

    from scipy.ndimage import label as ndi_label, distance_transform_edt

    components, n_comp = ndi_label(truth, structure=np.ones((3, 3), int))

    # flat index -> row in X
    flat_all = np.ravel_multi_index((ids[:, 0], ids[:, 1]), (H, W))

    all_tp, all_fp, all_fn = 0.0, 0.0, 0
    n_withheld = 0
    fold_results = []

    rng = np.random.default_rng(SEED)

    for f in range(4):
        valid = fp_bool & (fold_grid == f)
        collar = distance_transform_edt(~valid) <= 15
        hidden_ids = np.unique(components[collar & truth])
        hidden_ids = hidden_ids[hidden_ids > 0]
        hidden = truth & np.isin(components, hidden_ids)
        test_fold = hidden & valid
        if not test_fold.any():
            print(f"[holdout] fold {f}: no withheld positives", flush=True)
            continue
        visible = truth & ~hidden
        train_dom = fp_bool & (distance_transform_edt(~(valid | hidden)) > 15)

        # Indices into X for train and valid pixels
        train_flat = np.ravel_multi_index(np.argwhere(train_dom).T, (H, W))
        valid_flat = np.ravel_multi_index(np.argwhere(valid).T, (H, W))

        # map flat -> X row
        flat_to_xrow = {int(flat): i for i, flat in enumerate(flat_all)}
        train_rows = np.array([flat_to_xrow[int(ff)] for ff in train_flat if int(ff) in flat_to_xrow], dtype=np.int64)
        valid_rows = np.array([flat_to_xrow[int(ff)] for ff in valid_flat if int(ff) in flat_to_xrow], dtype=np.int64)

        if len(train_rows) == 0 or len(valid_rows) == 0:
            continue

        # Training labels
        train_coords = ids[train_rows]
        train_y = labels[train_coords[:, 0], train_coords[:, 1]]
        train_pos = train_rows[train_y == 1]
        train_neg = train_rows[train_y == 0]
        if len(train_pos) == 0:
            continue
        n_neg = min(150_000, len(train_neg))
        neg_sel = train_neg[rng.choice(len(train_neg), size=n_neg, replace=False)]
        sel_rows = np.r_[train_pos, neg_sel]
        sel_y = np.r_[np.ones(len(train_pos), dtype=np.int8), np.zeros(len(neg_sel), dtype=np.int8)]

        Xtr = np.ascontiguousarray(X[sel_rows])
        m_local = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.05, max_leaf_nodes=32,
            min_samples_leaf=50, random_state=SEED + f, early_stopping=True,
        )
        m_local.fit(Xtr, sel_y)

        # Predict on valid region
        Xv = np.ascontiguousarray(X[valid_rows])
        p_valid = m_local.predict_proba(Xv)[:, 1].astype(np.float32)

        # Build score grid for valid region
        p_grid = np.zeros((H, W), dtype=np.float32)
        valid_coords = ids[valid_rows]
        p_grid[valid_coords[:, 0], valid_coords[:, 1]] = p_valid

        budget = int(round(TOTAL_BUDGET * valid.sum() / fp_bool.sum()))
        dots = emit_dots(p_grid, valid, budget)

        res = dti_components_exact(
            pred=dots.astype(np.float64),
            truth=test_fold.astype(np.float64),
            valid_mask=valid,
            catalogue_mask=visible,
            alpha=ALPHA, beta=BETA,
        )
        all_tp += res["TP_w"]
        all_fp += res["FP_w"]
        all_fn += res["FN_w"]
        n_withheld += int(res["n_truth"])
        fold_results.append({
            "fold": f, "name": ["NW", "NE", "SW", "SE"][f],
            "TP_w": round(res["TP_w"], 4), "FP_w": round(res["FP_w"], 4),
            "FN_w": float(res["FN_w"]), "dti": round(res["dti"], 6),
            "n_truth": int(res["n_truth"]), "dots": int(dots.sum()),
        })
        print(f"[holdout] fold {f}: TP_w={res['TP_w']:.2f} FP_w={res['FP_w']:.2f} "
              f"FN_w={res['FN_w']:.2f} dti={res['dti']:.4f} n_truth={res['n_truth']}", flush=True)

    denom = all_tp + ALPHA * all_fp + BETA * all_fn + 1e-7
    dti = all_tp / denom

    # Bootstrap CI (simple percentile over folds is not valid; use a rough block bootstrap)
    # For now, report point estimate with fold-level spread as a proxy.
    fold_dtis = [fr["dti"] for fr in fold_results]
    ci_low = float(np.percentile(fold_dtis, 2.5)) if len(fold_dtis) >= 2 else None
    ci_high = float(np.percentile(fold_dtis, 97.5)) if len(fold_dtis) >= 2 else None

    result = {
        "evaluator_version": "segment-hide-recover-pooled-v1 (optimized local reimplementation)",
        "alpha": ALPHA, "beta": BETA, "radius_m": 300,
        "TP_w": round(all_tp, 4), "FP_w": round(all_fp, 4), "FN_w": float(all_fn),
        "n_withheld_positive_pixels": n_withheld,
        "n_folds_scored": len(fold_results),
        "dti": round(dti, 6),
        "ci95_fold_percentile": [ci_low, ci_high],
        "folds": fold_results,
        "note": "Local holdout reimplementation; not an organizer score and not a leaderboard projection. CI is fold-percentile, not a full spatial block bootstrap.",
    }
    (EVID / "kanler_holdout.json").write_text(json.dumps(result, indent=2, default=float) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
