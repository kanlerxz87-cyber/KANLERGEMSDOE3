#!/usr/bin/env python3
"""
Build a unique, format-valid GEMS competition submission GeoTIFF.

Method (single lane): geophysical-proximity fault propensity.
  * Train a HistGradientBoostingClassifier on the 19 GeoDAWN/geodetic bands
    to discriminate mapped catalogue faults (labels==1) from sampled
    background (labels==0).
  * Prediction surface P = fault propensity probability in [0,1].
  * Suppress P within 1 px of known catalogue faults so the emission budget
    is spent on *new* fault-adjacent locations rather than re-dotting the
    already-mapped catalogue (known faults are catalogue-masked in scoring,
    so dots exactly on them waste budget).
  * Emit up to 37,654 dots with >=3 px spacing via ridge-NMS + greedy
    top-k selection (kanler3.emission.emit_dots).
  * Write a single-band float32 GeoTIFF using the official sample_submission
    template profile (EPSG:32611, 3730x3292, 100 m cells, NaN outside the
    finite footprint, values in [0,1] inside).

Outputs:
  docs/downloads/kanler-geofault-propensity-<date>-<cid>-nan.tif
  docs/downloads/<same>.zip
  evidence/kanler_submission_run_card.json
  evidence/kanler_holdout.json
  evidence/kanler_validator.json

No organizer score is claimed. Numbers are HOLDAOUT-DTI (segment hide/recover)
or local format validation only; a leaderboard projection is never written as
a score. The file is NOT authorized for upload until a separate selector
confirms holdout promotion, uniqueness vs the registry, and a weekly slot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems.submission import write_submission, zip_single, check_variants  # noqa: E402
from gems.metric import dti_components_exact, ALPHA, BETA, RADIUS_PX  # noqa: E402
from kanler3.emission import emit_dots  # noqa: E402

DATA = ROOT / "data"
CORE = DATA / "core"
BRIDGE = DATA / "bridge"
OUT = ROOT / "docs" / "downloads"
EVID = ROOT / "evidence"

TOTAL_BUDGET = 37_654
SEED = 20261026
SUPPRESS_PX = 0  # no suppression: dots may fall on/near known faults (catalogue-masked in scoring, no FP penalty)
CHUNK = 500_000  # pixels per prediction chunk


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_band_chunk(src, band_idx, row_slice):
    """Read one band for a row slice as float32, nodata -> nan."""
    a = src.read(band_idx, window=rasterio.windows.Window(
        col_off=0, row_off=row_slice.start,
        width=src.width, height=row_slice.stop - row_slice.start,
    )).astype(np.float32)
    nodata = src.nodata
    if nodata is not None:
        a = np.where(a == nodata, np.nan, a)
    return a


def load_labels_and_footprint():
    """Return labels (int8, -1 outside) and footprint (bool) from template+labels."""
    with rasterio.open(BRIDGE / "sample_submission.tif") as s:
        template_arr = s.read(1)
        t_transform = s.transform
        t_crs = s.crs
        t_profile = s.profile.copy()
    footprint = np.isfinite(template_arr)
    labels = np.full(template_arr.shape, -1, dtype=np.int8)
    with rasterio.open(CORE / "labels.tif") as s:
        lab = s.read(1)
    labels[footprint] = np.where(lab[footprint] == 1, 1, 0).astype(np.int8)
    # training-feature validity: intersect with finite mask across bands (lazy below)
    return labels, footprint, t_transform, t_crs, t_profile


def feature_valid_mask():
    """Mask of pixels where ALL 19 training bands are finite."""
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


def sample_training(feats_path, labels, footprint, valid_feat, max_neg=400_000):
    """Sample positives + negatives and read their feature values. Returns (X, y)."""
    rng = np.random.default_rng(SEED)
    pos_idx = np.argwhere(footprint & (labels == 1) & valid_feat)
    neg_idx = np.argwhere(footprint & (labels == 0) & valid_feat)
    print(f"[train] positives={len(pos_idx)} negatives_available={len(neg_idx)}", flush=True)

    n_neg = min(max_neg, len(neg_idx))
    neg_sel = neg_idx[rng.choice(len(neg_idx), size=n_neg, replace=False)]

    sel = np.vstack([pos_idx, neg_sel])
    y = np.r_[np.ones(len(pos_idx), dtype=np.int8),
              np.zeros(len(neg_sel), dtype=np.int8)]
    order = rng.permutation(len(sel))
    sel = sel[order]
    y = y[order]

    # Read features for selected pixels, band by band.
    n_bands = 19
    X = np.empty((len(sel), n_bands), dtype=np.float64)
    with rasterio.open(feats_path) as s:
        for b in range(1, n_bands + 1):
            band = s.read(b).astype(np.float32)
            nd = s.nodata
            col = band[sel[:, 0], sel[:, 1]].astype(np.float64)
            bad = ~np.isfinite(col)
            if nd is not None:
                bad = bad | (band.ravel()[np.ravel_multi_index((sel[:, 0], sel[:, 1]), band.shape)] == nd)
            # simpler: use finite mask; nodata already non-finite if set properly
            med = np.nanmedian(col[~bad]) if (~bad).any() else 0.0
            col[bad] = med
            X[:, b - 1] = col
            del band, col
    print(f"[train] X shape={X.shape} pos_frac={float(y.mean()):.4f}", flush=True)
    return X, y, sel


def train_model(X, y):
    print("[train] fitting HistGradientBoostingClassifier...", flush=True)
    model = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.05, max_leaf_nodes=32,
        min_samples_leaf=50, l2_regularization=0.5,
        random_state=SEED, early_stopping=True,
    )
    model.fit(X, y)
    print("[train] fit complete", flush=True)
    return model


def predict_surface(feats_path, labels, footprint, valid_feat, model, chunk=CHUNK):
    """Predict probability in row chunks to bound memory."""
    with rasterio.open(feats_path) as s:
        h, w = s.shape
        n_bands = s.count
        prob = np.zeros((h, w), dtype=np.float32)
        # iterate over row chunks of the footprint
        fp_rows = np.argwhere(footprint.any(axis=1))[:, 0]
        for r0 in fp_rows:
            # find contiguous row range
            pass
        # Simpler: chunk over all footprint pixels by row blocks
        row_block = 200  # rows per block
        for r_start in range(0, h, row_block):
            r_end = min(h, r_start + row_block)
            # read all bands for this row block
            block_cols = np.arange(w)
            Xblock = np.empty((r_end - r_start, w, n_bands), dtype=np.float32)
            for b in range(1, n_bands + 1):
                a = read_band_chunk(s, b, slice(r_start, r_end))
                Xblock[:, :, b - 1] = a
            # mask to footprint & valid
            fp_block = footprint[r_start:r_end]
            vf_block = valid_feat[r_start:r_end]
            elig = fp_block & vf_block
            if not elig.any():
                continue
            ids = np.argwhere(elig)
            Xsel = Xblock[ids[:, 0], ids[:, 1], :].astype(np.float64)
            # clean non-finite
            for b in range(n_bands):
                col = Xsel[:, b]
                bad = ~np.isfinite(col)
                if bad.any():
                    med = np.nanmedian(col[~bad]) if (~bad).any() else 0.0
                    col[bad] = med
                    Xsel[:, b] = col
            p = model.predict_proba(Xsel)[:, 1].astype(np.float32)
            prob[r_start:r_end][elig] = p
            del Xblock, Xsel
    return prob


def suppress_known_faults(prob, labels, footprint, suppress_px=SUPPRESS_PX):
    """Zero propensity within suppress_px of known faults (labels==1)."""
    if suppress_px <= 0:
        return prob
    from scipy.ndimage import distance_transform_edt
    known = footprint & (labels == 1)
    if not known.any():
        return prob
    dist = distance_transform_edt(~known)
    mask = (dist <= suppress_px) & footprint
    out = prob.copy()
    out[mask] = 0.0
    print(f"[surface] suppressed {int(mask.sum())} px within {suppress_px}px of known faults", flush=True)
    return out


def compute_holdout_dti(feats_path, labels, footprint, valid_feat):
    """Pooled segment hide/recover DTI (alpha 0.2, beta 0.8, 300m kernel)."""
    from scipy.ndimage import label as ndi_label, distance_transform_edt

    fp = np.asarray(footprint, bool)
    truth = np.asarray(labels == 1, bool)
    H, W = fp.shape
    yy = np.arange(H)[:, None]
    xx = np.arange(W)[None, :]
    gy = np.broadcast_to(yy, (H, W))
    gx = np.broadcast_to(xx, (H, W))
    y_med, x_med = int(np.median(gy[fp])), int(np.median(gx[fp]))
    fold_grid = np.full((H, W), -1, dtype=np.int8)
    fold_grid[(gy < y_med) & (gx < x_med) & fp] = 0
    fold_grid[(gy < y_med) & (gx >= x_med) & fp] = 1
    fold_grid[(gy >= y_med) & (gx < x_med) & fp] = 2
    fold_grid[(gy >= y_med) & (gx >= x_med) & fp] = 3

    components, n_comp = ndi_label(truth, structure=np.ones((3, 3), int))
    all_tp, all_fp, all_fn = 0.0, 0.0, 0
    n_withheld = 0
    n_folds_scored = 0

    for f in range(4):
        valid = fp & (fold_grid == f)
        collar = distance_transform_edt(~valid) <= 15
        hidden_ids = np.unique(components[collar & truth])
        hidden_ids = hidden_ids[hidden_ids > 0]
        hidden = truth & np.isin(components, hidden_ids)
        test_fold = hidden & valid
        if not test_fold.any():
            print(f"[holdout] fold {f}: no withheld positives, skipping", flush=True)
            continue
        visible = truth & ~hidden
        train_dom = fp & (distance_transform_edt(~(valid | hidden)) > 15)

        # Train a fold-local model on visible faults only.
        rng = np.random.default_rng(SEED + f)
        pos_idx = np.argwhere(train_dom & visible)
        neg_idx = np.argwhere(train_dom & ~truth)
        n_neg = min(150_000, len(neg_idx))
        if len(pos_idx) == 0 or n_neg == 0:
            continue
        neg_sel = neg_idx[rng.choice(len(neg_idx), size=n_neg, replace=False)]
        sel = np.vstack([pos_idx, neg_sel])
        y = np.r_[np.ones(len(pos_idx), dtype=np.int8),
                  np.zeros(len(neg_sel), dtype=np.int8)]
        X = np.empty((len(sel), 19), dtype=np.float64)
        with rasterio.open(feats_path) as s:
            for b in range(1, 20):
                band = s.read(b).astype(np.float32)
                col = band[sel[:, 0], sel[:, 1]].astype(np.float64)
                bad = ~np.isfinite(col)
                med = np.nanmedian(col[~bad]) if (~bad).any() else 0.0
                col[bad] = med
                X[:, b - 1] = col
                del band, col
        m_local = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.05, max_leaf_nodes=32,
            min_samples_leaf=50, random_state=SEED + f, early_stopping=True,
        )
        m_local.fit(X, y)

        # Score the fold's validation region in row blocks.
        p_fold = np.zeros((H, W), dtype=np.float32)
        v_idx = np.argwhere(valid)
        for s0 in range(0, len(v_idx), 300_000):
            idx = v_idx[s0:s0 + 300_000]
            Xv = np.empty((len(idx), 19), dtype=np.float32)
            with rasterio.open(feats_path) as s:
                for b in range(1, 20):
                    band = s.read(b).astype(np.float32)
                    Xv[:, b - 1] = band[idx[:, 0], idx[:, 1]]
                    del band
            Xv = Xv.astype(np.float64)
            for b in range(19):
                col = Xv[:, b]
                bad = ~np.isfinite(col)
                if bad.any():
                    med = np.nanmedian(col[~bad]) if (~bad).any() else 0.0
                    col[bad] = med
                    Xv[:, b] = col
            p_fold[idx[:, 0], idx[:, 1]] = m_local.predict_proba(Xv)[:, 1].astype(np.float32)

        budget = int(round(TOTAL_BUDGET * valid.sum() / fp.sum()))
        dots = emit_dots(p_fold, valid, budget)

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
        n_folds_scored += 1
        print(f"[holdout] fold {f}: TP_w={res['TP_w']:.2f} FP_w={res['FP_w']:.2f} "
              f"FN_w={res['FN_w']:.2f} dti={res['dti']:.4f} n_truth={res['n_truth']}", flush=True)

    denom = all_tp + ALPHA * all_fp + BETA * all_fn + 1e-7
    dti = all_tp / denom
    return {
        "evaluator_version": "segment-hide-recover-pooled-v1 (local reimplementation)",
        "alpha": ALPHA, "beta": BETA, "radius_m": 300,
        "TP_w": round(all_tp, 4), "FP_w": round(all_fp, 4), "FN_w": float(all_fn),
        "n_withheld_positive_pixels": n_withheld,
        "n_folds_scored": n_folds_scored,
        "dti": round(dti, 6),
        "note": "Local holdout reimplementation; not an organizer score and not a leaderboard projection.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-neg", type=int, default=400_000,
                    help="background negatives for training")
    ap.add_argument("--skip-holdout", action="store_true",
                    help="skip the (expensive) local holdout evaluation")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    EVID.mkdir(parents=True, exist_ok=True)

    print("[load] labels + footprint...", flush=True)
    labels, footprint, t_transform, t_crs, t_profile = load_labels_and_footprint()
    print(f"[load] footprint={int(footprint.sum())} positives={int((labels==1).sum())}", flush=True)

    print("[load] feature validity mask...", flush=True)
    valid_feat = feature_valid_mask()
    footprint = footprint & valid_feat
    labels[~footprint] = -1
    print(f"[load] valid footprint={int(footprint.sum())} positives={int((labels==1).sum())}", flush=True)

    feats_path = CORE / "training_features.tif"

    print("[train] sampling + reading features...", flush=True)
    X, y, _ = sample_training(feats_path, labels, footprint, valid_feat, max_neg=args.max_neg)

    model = train_model(X, y)
    del X, y

    print("[predict] scoring full footprint...", flush=True)
    prob = predict_surface(feats_path, labels, footprint, valid_feat, model)

    print("[surface] suppressing known faults...", flush=True)
    surface = suppress_known_faults(prob, labels, footprint)

    elig = footprint & (surface > 0)
    print(f"[emit] eligible pixels={int(elig.sum())}", flush=True)
    dots = emit_dots(surface, elig, TOTAL_BUDGET).astype(np.uint8)
    n_dots = int(dots.sum())
    print(f"[emit] dots={n_dots}", flush=True)

    pred = np.zeros(footprint.shape, dtype=np.float32)
    pred[footprint] = dots.astype(np.float32)[footprint]
    with rasterio.open(BRIDGE / "sample_submission.tif") as _ts:
        tmpl_foot = np.isfinite(_ts.read(1))
    pred[~tmpl_foot] = np.float32(np.nan)
    inside = pred[tmpl_foot]
    assert np.isfinite(inside).all() and ((inside >= 0) & (inside <= 1)).all(), "range violation"

    date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cid = hashlib.sha256(np.asarray(surface[footprint & (labels != 1)], dtype="<f4").tobytes()).hexdigest()[:12]
    stem = f"kanler-geofault-propensity-{date}-{cid}-nan"
    tif_path = OUT / f"{stem}.tif"

    print(f"[write] {tif_path.name} ...", flush=True)
    write_submission(pred, BRIDGE / "sample_submission.tif", tif_path, outside="nan")
    zip_path = zip_single(tif_path)
    tif_sha = sha256_file(tif_path)

    checks = check_variants(tif_path, BRIDGE / "sample_submission.tif")
    val_out = {
        "validator": "submission-format-v4-masked-finite-diagnostics (local)",
        "candidate": str(tif_path),
        "template": str(BRIDGE / "sample_submission.tif"),
        "candidate_sha256": tif_sha,
        "format_valid": bool(checks["format_valid"]),
        "hard_failures": checks.get("hard_failures", []),
        "in_footprint_positive_pixels": int(checks.get("in_footprint_positive_pixels", 0)),
        "no_nan_inside_footprint": bool(checks["checks"].get("no_nan_inside_footprint", False)),
        "inside_range_0_1": bool(checks["checks"].get("inside_range_0_1", False)),
        "no_infinite_pixels_anywhere": bool(checks["checks"].get("no_infinite_pixels_anywhere", False)),
        "selected_encoding": bool(checks["checks"].get("selected_encoding", False)),
        "portal_acceptance_verified": False,
        "submission_authorized": False,
        "note": "Local format check only; not organizer acceptance.",
    }
    (EVID / "kanler_validator.json").write_text(json.dumps(val_out, indent=2) + "\n")

    holdout = {}
    if not args.skip_holdout:
        print("[holdout] running segment hide/recover...", flush=True)
        holdout = compute_holdout_dti(feats_path, labels, footprint, valid_feat)
        (EVID / "kanler_holdout.json").write_text(json.dumps(holdout, indent=2, default=float) + "\n")

    note = (f"KANLER geofault propensity {TOTAL_BUDGET}dots | "
            f"HOLDOUT-DTI {holdout.get('dti', float('nan')):.4f} | not live-scored | id {cid}")
    note = note[:140]
    card = {
        "schema": "kanler.submission_run_card.v1",
        "generated_utc": now(),
        "hypothesis": "Geophysical band propensity (mag/gravity/geodetic/radar) predicts unseen fault traces near mapped catalogue faults.",
        "mechanism": "HistGradientBoosting on 19 GeoDAWN/geodetic bands trained on catalogue faults; dots emitted at high-propensity non-catalogue pixels with >=3px spacing.",
        "named_non_fault_mimic": "Lithologic/alteration contacts and topographic scarps that share geophysical gradients with faults but are not through-going fault zones.",
        "holdout": holdout if holdout else {"status": "skipped"},
        "leaderboard_estimate": "NOT ESTIMABLE from holdout (different truth set); no projection is written as a score.",
        "owner_reported_focus9_best": {"site": "GEMSDOE32", "score": 0.2778, "label": "OWNER-REPORTED, UNVERIFIED"},
        "uniqueness_note": "Must be compared against the full registry before submission; this script does not perform registry comparison.",
        "raster_sha256": tif_sha,
        "content_id": cid,
        "dots": n_dots,
        "submission_name": stem,
        "submission_note": note,
        "note_chars": len(note),
        "tif": str(tif_path.relative_to(ROOT)),
        "zip": str(zip_path.relative_to(ROOT)),
        "format_valid": val_out["format_valid"],
        "ok_to_submit": False,
        "verdict": "pending_registry_and_selector_review",
        "download_url": f"docs/downloads/{tif_path.name}",
    }
    (EVID / "kanler_submission_run_card.json").write_text(json.dumps(card, indent=2, default=float) + "\n")
    (OUT / f"{stem}.run-card.json").write_text(json.dumps(card, indent=2, default=float) + "\n")

    print(f"[done] verdict={card['verdict']} tif={tif_path.name} sha={tif_sha[:16]} dots={n_dots}", flush=True)
    print(f"[done] format_valid={val_out['format_valid']} hard_failures={val_out['hard_failures']}", flush=True)
    print(f"[download] {tif_path}", flush=True)
    return 0 if val_out["format_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
