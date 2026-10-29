#!/usr/bin/env python3
"""
Compare candidate submission surfaces using the local holdout protocol.
Surfaces tested:
  A) ML propensity + 1px known-fault suppression (current submission)
  B) ML propensity, NO suppression (dots allowed on/near known faults)
  C) Fault proximity: inverse distance to nearest known fault, kernel-weighted
  D) ML propensity x fault proximity (hybrid)

Each surface is scored with the same 4-fold segment hide/recover DTI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems.metric import dti_components_exact, ALPHA, BETA  # noqa: E402
from kanler3.emission import emit_dots  # noqa: E402

CORE = ROOT / "data" / "core"
BRIDGE = ROOT / "data" / "bridge"
EVID = ROOT / "evidence"
TOTAL_BUDGET = 37_654
SEED = 20261026


def load_grid():
    with rasterio.open(BRIDGE / "sample_submission.tif") as s:
        tmpl = s.read(1)
    fp = np.isfinite(tmpl)
    labels = np.full(tmpl.shape, -1, dtype=np.int8)
    with rasterio.open(CORE / "labels.tif") as s:
        lab = s.read(1)
    labels[fp] = np.where(lab[fp] == 1, 1, 0).astype(np.int8)
    return labels, fp


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


def train_propensity(labels, fp, valid_feat, max_neg=300_000):
    rng = np.random.default_rng(SEED)
    pos_idx = np.argwhere(fp & (labels == 1) & valid_feat)
    neg_idx = np.argwhere(fp & (labels == 0) & valid_feat)
    n_neg = min(max_neg, len(neg_idx))
    neg_sel = neg_idx[rng.choice(len(neg_idx), size=n_neg, replace=False)]
    sel = np.vstack([pos_idx, neg_sel])
    y = np.r_[np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_sel), dtype=np.int8)]
    order = rng.permutation(len(sel)); sel = sel[order]; y = y[order]
    with rasterio.open(CORE / "training_features.tif") as s:
        X = np.empty((len(sel), 19), dtype=np.float64)
        for b in range(1, 20):
            band = s.read(b).astype(np.float32)
            col = band[sel[:, 0], sel[:, 1]].astype(np.float64)
            bad = ~np.isfinite(col)
            med = np.nanmedian(col[~bad]) if (~bad).any() else 0.0
            col[bad] = med
            X[:, b - 1] = col
            del band, col
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=32,
                                       min_samples_leaf=50, l2_regularization=0.5,
                                       random_state=SEED, early_stopping=True)
    m.fit(X, y)
    return m


def predict_propensity(m, fp, valid_feat):
    H, W = fp.shape
    prob = np.zeros((H, W), dtype=np.float32)
    with rasterio.open(CORE / "training_features.tif") as s:
        for r0 in range(0, H, 200):
            r1 = min(H, r0 + 200)
            row_fp = fp[r0:r1]
            if not row_fp.any():
                continue
            c_ids = np.argwhere(row_fp.any(axis=0))[:, 0]
            c0, c1 = c_ids[0], c_ids[-1] + 1
            block = np.empty((r1 - r0, c1 - c0, 19), dtype=np.float32)
            for b in range(1, 20):
                block[:, :, b - 1] = s.read(b, window=rasterio.windows.Window(
                    col_off=c0, row_off=r0, width=c1 - c0, height=r1 - r0)).astype(np.float32)
            sel = np.argwhere(row_fp[:, c0:c1] & valid_feat[r0:r1, c0:c1])
            if len(sel) == 0:
                continue
            Xb = block[sel[:, 0], sel[:, 1], :].astype(np.float64)
            for b in range(19):
                col = Xb[:, b]; bad = ~np.isfinite(col)
                if bad.any():
                    col[bad] = np.nanmedian(col[~bad]) if (~bad).any() else 0.0
                    Xb[:, b] = col
            p = m.predict_proba(Xb)[:, 1].astype(np.float32)
            prob[r0:r1][fp[r0:r1] & valid_feat[r0:r1]] = p
            del block, Xb
    return prob


def fault_proximity_surface(labels, fp, sigma_px=3.0):
    """Inverse-distance-to-fault kernel surface: high near faults, decays with distance."""
    known = fp & (labels == 1)
    dist = distance_transform_edt(~known)
    surf = np.maximum(1.0 - dist / sigma_px, 0.0)
    surf = np.where(fp, surf, 0.0).astype(np.float32)
    return surf


def holdout_score(surface, labels, fp, tag):
    """4-fold buffered whole-component hide/recover pooled DTI."""
    from scipy.ndimage import label as ndi_label

    H, W = fp.shape
    truth = (labels == 1)
    gy, gx = np.mgrid[0:H, 0:W]
    y_med, x_med = int(np.median(gy[fp])), int(np.median(gx[fp]))
    fold_grid = np.full((H, W), -1, dtype=np.int8)
    fold_grid[(gy < y_med) & (gx < x_med) & fp] = 0
    fold_grid[(gy < y_med) & (gx >= x_med) & fp] = 1
    fold_grid[(gy >= y_med) & (gx < x_med) & fp] = 2
    fold_grid[(gy >= y_med) & (gx >= x_med) & fp] = 3

    components, n_comp = ndi_label(truth, structure=np.ones((3, 3), int))
    from scipy.ndimage import distance_transform_edt as dte

    all_tp, all_fp, all_fn = 0.0, 0.0, 0
    n_withheld = 0
    folds = []

    for f in range(4):
        valid = fp & (fold_grid == f)
        collar = dte(~valid) <= 15
        hidden_ids = np.unique(components[collar & truth])
        hidden_ids = hidden_ids[hidden_ids > 0]
        hidden = truth & np.isin(components, hidden_ids)
        test_fold = hidden & valid
        if not test_fold.any():
            continue
        visible = truth & ~hidden
        p_fold = np.where(valid, surface, 0.0).astype(np.float32)
        budget = int(round(TOTAL_BUDGET * valid.sum() / fp.sum()))
        dots = emit_dots(p_fold, valid, budget)
        res = dti_components_exact(dots.astype(np.float64), test_fold.astype(np.float64),
                                   valid_mask=valid, catalogue_mask=visible, alpha=ALPHA, beta=BETA)
        all_tp += res["TP_w"]; all_fp += res["FP_w"]; all_fn += res["FN_w"]
        n_withheld += int(res["n_truth"])
        folds.append({"fold": f, "dti": round(res["dti"], 6), "n_truth": int(res["n_truth"]),
                      "dots": int(dots.sum())})
        print(f"  [{tag}] fold {f}: dti={res['dti']:.4f} n_truth={res['n_truth']} dots={int(dots.sum())}", flush=True)

    denom = all_tp + ALPHA * all_fp + BETA * all_fn + 1e-7
    dti = all_tp / denom
    print(f"[{tag}] POOLED HOLDAOUT-DTI = {dti:.6f} (n_withheld={n_withheld})", flush=True)
    return {"tag": tag, "dti": round(dti, 6), "n_withheld": n_withheld,
            "TP_w": round(all_tp, 2), "FP_w": round(all_fp, 2), "FN_w": round(all_fn, 2),
            "folds": folds}


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    labels, fp = load_grid()
    valid_feat = feature_valid_mask()
    fp = fp & valid_feat
    labels[~fp] = -1

    print("[train] propensity model...", flush=True)
    m = train_propensity(labels, fp, valid_feat)
    print("[predict] propensity surface...", flush=True)
    prop = predict_propensity(m, fp, valid_feat)

    print("[surface] fault proximity...", flush=True)
    prox = fault_proximity_surface(labels, fp, sigma_px=3.0)

    surfaces = {
        "A_ml_suppressed": np.where(fp & (distance_transform_edt(~(fp & (labels == 1))) > 1), prop, 0.0),
        "B_ml_nosuppress": prop,
        "C_proximity_only": prox,
        "D_ml_x_proximity": prop * prox,
    }

    results = []
    for tag, surf in surfaces.items():
        surf = np.where(fp, surf, 0.0).astype(np.float32)
        r = holdout_score(surf, labels, fp, tag)
        results.append(r)

    results.sort(key=lambda r: -r["dti"])
    print("\n=== RANKING ===")
    for r in results:
        print(f"  {r['tag']:28s} HOLDAOUT-DTI = {r['dti']:.6f}  n_withheld={r['n_withheld']}")
    best = results[0]
    print(f"\nBest: {best['tag']} with HOLDAOUT-DTI {best['dti']:.6f}")
    (EVID / "kanler_surface_comparison.json").write_text(json.dumps(results, indent=2, default=float) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
