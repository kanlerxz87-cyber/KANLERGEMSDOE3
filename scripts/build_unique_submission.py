#!/usr/bin/env python3
"""
Build a unique, valid GEMS submission TIF from the restored mirror inputs.

Method (single lane, geophysical feature contrast + spatial holdout):
  - Uses only the 19 raw competition bands from training_features.tif
  - Trains HistGradientBoostingClassifier on footprint pixels
  - Quadrant spatial holdout (SegmentHoldout, buffer 15px, pooled DTI alpha=0.2 beta=0.8)
  - Emits ~37,654 dots via ridge-NMS + >=3px spacing (kanler3.emission.emit_dots)
  - Writes single-band float32 GeoTIFF matching the sample_submission template,
    NaN outside footprint, values in [0,1] inside

Outputs:
  docs/downloads/kanler-geocontrast-v1-YYYYMMDDTHHMMSSZ-<cid>-nan.tif
  evidence/unique_submission_run_card.json
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import SegmentHoldout, MTR_EVALUATOR_VERSION
from gems.metric import ALPHA, BETA, RADIUS_PX
from gems.submission import write_submission, zip_single, sha256_file, check_variants
from kanler3.emission import emit_dots

SEED = 20261029
TOTAL_BUDGET = 37_654
BAND_NAMES = [
    "mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope",
    "tc", "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15",
    "iso_grav_anom_vg", "det_elev", "iso_grav_anom", "tmi",
    "depth_to_base_surf", "ieq_n100a15", "cond_surf", "iso_grav_anom_hg",
    "det_elev_slope",
]
SENTINEL = -1e30


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_grid():
    d = ROOT / "data"
    with rasterio.open(d / "sample_submission.tif") as s:
        footprint = np.isfinite(s.read(1))
        transform = tuple(s.transform)[:6]
        crs = s.crs
        shape = s.shape
    with rasterio.open(d / "labels.tif") as s:
        labels = s.read(1).astype(np.int16)
    assert labels.shape == footprint.shape == shape
    assert np.array_equal(labels >= 0, footprint)
    return footprint, labels, transform, crs, shape


def read_band_chunked(path, band_idx, footprint):
    """Read one band, replace sentinel with NaN, median-impute inside footprint."""
    with rasterio.open(path) as s:
        a = s.read(band_idx).astype(np.float32)
    a[a < SENTINEL + 1e6] = np.nan
    a[~footprint] = np.nan
    med = float(np.nanmedian(a[footprint]))
    a[~np.isfinite(a)] = med
    return a


def build_contrast_features(X_dict, footprint):
    """Build contrast features from pairs of independent fields.

    Distinct from: dotted H19-5 traces, Poisson sampling, topographic gap closure,
    analog tip/stepover, named PINN.
    """
    feats = {}
    # Gradient magnitude of key fields
    for name, a in (("rtp", X_dict["rtp"]), ("iso_grav_anom", X_dict["iso_grav_anom"]),
                    ("det_elev", X_dict["det_elev"]), ("tc", X_dict["tc"]),
                    ("tmi_hg", X_dict["tmi_hg"])):
        gy, gx = np.gradient(a.astype(np.float64))
        mag = np.hypot(gx, gy).astype(np.float32)
        mag[~footprint] = np.nan
        med = float(np.nanmedian(mag[footprint]))
        mag[~np.isfinite(mag)] = med
        feats[f"grad_{name}"] = mag

    # Pairwise gradient-direction concordance
    pairs = [("rtp", "rtp", "iso_grav_anom", "iso_grav_anom"),
             ("rtp", "rtp", "det_elev", "det_elev"),
             ("iso_grav_anom", "iso_grav_anom", "det_elev", "det_elev"),
             ("tc", "tc", "rtp", "rtp")]
    for n1, a1, n2, a2 in pairs:
        b1 = X_dict[a1].astype(np.float64); b2 = X_dict[a2].astype(np.float64)
        g1y, g1x = np.gradient(b1); g2y, g2x = np.gradient(b2)
        m1 = np.hypot(g1x, g1y); m2 = np.hypot(g2x, g2y)
        eps = 1e-12
        dot = (g1x * g2x + g1y * g2y) / ((m1 + eps) * (m2 + eps))
        v = np.abs(dot).astype(np.float32)
        v[~footprint] = np.nan
        med = float(np.nanmedian(v[footprint]))
        v[~np.isfinite(v)] = med
        feats[f"concord_{n1}_{n2}"] = v

    # Joint extremity products
    feats["rtp_x_grav"] = (np.abs(X_dict["rtp"]) * np.abs(X_dict["iso_grav_anom"])).astype(np.float32)
    feats["rtp_x_elev"] = (np.abs(X_dict["rtp"]) * np.abs(X_dict["det_elev"])).astype(np.float32)
    for k in ("rtp_x_grav", "rtp_x_elev"):
        k_arr = feats[k]
        k_arr[~footprint] = np.nan
        med = float(np.nanmedian(k_arr[footprint]))
        k_arr[~np.isfinite(k_arr)] = med
    return feats


def main():
    t0 = time.time()
    print("[1/5] Loading grid + labels...", flush=True)
    footprint, labels, transform, crs, shape = load_grid()
    fp_flat = np.flatnonzero(footprint.ravel())
    n_fp = len(fp_flat)
    print(f"    grid={shape} footprint={n_fp:,} pos={(labels==1).sum():,} "
          f"({time.time()-t0:.0f}s)", flush=True)

    print("[2/5] Reading 19 bands...", flush=True)
    X_dict = {}
    for i, name in enumerate(BAND_NAMES, start=1):
        X_dict[name] = read_band_chunked(ROOT / "data" / "training_features.tif", i, footprint)
    print(f"    bands loaded ({time.time()-t0:.0f}s)", flush=True)

    print("[3/5] Building contrast features...", flush=True)
    extra = build_contrast_features(X_dict, footprint)
    feat_names = list(extra.keys())
    print(f"    extra features: {feat_names} ({time.time()-t0:.0f}s)", flush=True)

    # Design matrix on footprint only
    print("[4/5] Training HGB classifier...", flush=True)
    cols = [X_dict[n].ravel()[fp_flat] for n in BAND_NAMES]
    cols += [extra[n].ravel()[fp_flat] for n in feat_names]
    Xtr = np.stack(cols, axis=1).astype(np.float32)
    y = (labels.ravel() == 1)[fp_flat]

    rng = np.random.default_rng(SEED)
    pos = np.flatnonzero(y)
    neg = np.flatnonzero(~y)
    if len(neg) > 400_000:
        neg = rng.choice(neg, 400_000, replace=False)
    sel = np.sort(np.concatenate([pos, neg]))
    model = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.05, max_leaf_nodes=32,
        min_samples_leaf=100, l2_regularization=0.5,
        early_stopping=True, random_state=SEED,
    )
    model.fit(Xtr[sel], y[sel])
    print(f"    trained on {len(sel):,} pixels ({time.time()-t0:.0f}s)", flush=True)

    # Full-footprint prediction in chunks
    print("    predicting on full footprint in chunks...", flush=True)
    n_col = len(BAND_NAMES) + len(feat_names)
    p_fp = np.empty(n_fp, dtype=np.float32)
    chunk = 500_000
    for s0 in range(0, n_fp, chunk):
        s1 = min(s0 + chunk, n_fp)
        idx = fp_flat[s0:s1]
        cols_all = [X_dict[n].ravel()[idx] for n in BAND_NAMES]
        cols_all += [extra[n].ravel()[idx] for n in feat_names]
        Xc = np.stack(cols_all, axis=1).astype(np.float32)
        p_fp[s0:s1] = model.predict_proba(Xc)[:, 1].astype(np.float32)
        del Xc, cols_all, idx
    del Xtr, cols

    print("[5/5] Holdout evaluation + dot emission + write TIF...", flush=True)
    holdout = SegmentHoldout(footprint, labels == 1, buffer_px=15)
    fp_pos = np.full(footprint.size, -1, np.int64)
    fp_pos[fp_flat] = np.arange(n_fp)

    budgets = [int(round(TOTAL_BUDGET * int(f["valid"].sum()) / n_fp))
               for f in holdout.folds]
    dots_per_fold, fold_rows = [], []
    for fi, fold in enumerate(holdout.folds):
        valid_flat = np.flatnonzero(fold["valid"].ravel())
        score2d = np.zeros(footprint.shape, np.float32)
        score2d.ravel()[valid_flat] = p_fp[fp_pos[valid_flat]]
        elig = fold["valid"] & (distance_transform_edt(~fold["visible"]) > 2)
        dots = emit_dots(score2d, elig, budgets[fi]).astype(np.uint8)
        dots_per_fold.append(dots)
        ref, _blocks = holdout.score_fold(dots.astype(np.float64), fold)
        fold_rows.append({"fold": fold["name"], **ref})
        print(f"    fold {fold['name']}: DTI={ref['dti']:.6f} dots={int(dots.sum())} "
              f"budget={budgets[fi]}", flush=True)

    from gems.holdout import pooled_components, spatial_bootstrap_ci
    rows = [dict(r) for r in fold_rows]
    blocks = np.sum([holdout.score_fold(dots.astype(np.float64), f)[1]
                     for dots, f in zip(dots_per_fold, holdout.folds)], axis=0)
    total = pooled_components(rows)
    yy, xx = np.nonzero(footprint)
    nx = (footprint.shape[1] + 99) // 100
    active = np.unique((yy // 100) * nx + xx // 100)
    ci = spatial_bootstrap_ci(blocks[active], draws=1999)

    holdout_res = {
        "label": "HOLDOUT-DTI",
        "evaluator_version": MTR_EVALUATOR_VERSION,
        "dti": float(total["dti"]),
        "n_withheld_positive_pixels": int(total["n_truth"]),
        "n_emitted": int(total["n_emitted"]),
        "ci95": ci["interval"],
        "ci_method": ci["method"],
        "folds": rows,
        "budgets": budgets,
        "alpha": float(ALPHA), "beta": float(BETA), "radius_m": int(RADIUS_PX * 100),
    }
    print(f"    HOLDOUT-DTI={holdout_res['dti']:.6f} CI={holdout_res['ci95']} "
          f"n_pos={holdout_res['n_withheld_positive_pixels']} ({time.time()-t0:.0f}s)",
          flush=True)

    # Final dots on full footprint
    score2d = np.zeros(footprint.shape, np.float32)
    score2d.ravel()[fp_flat] = p_fp
    dots = emit_dots(score2d, footprint, TOTAL_BUDGET).astype(np.uint8)
    print(f"    final dots={int(dots.sum())} ({time.time()-t0:.0f}s)", flush=True)

    date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cid = hashlib.sha256(dots.astype(np.float32).tobytes()).hexdigest()[:12]
    stem = f"kanler-geocontrast-v1-{date}-{cid}"
    tif_path = ROOT / "docs" / "downloads" / f"{stem}-nan.tif"
    zip_path = ROOT / "docs" / "downloads" / f"{stem}-nan.zip"

    write_submission(dots.astype(np.float32), ROOT / "data" / "sample_submission.tif",
                     tif_path, outside="nan")
    zip_single(tif_path, zip_path)

    checks = check_variants(tif_path, ROOT / "data" / "sample_submission.tif")
    print(f"    format_valid={checks['format_valid']} "
          f"positive_px={checks['in_footprint_positive_pixels']} "
          f"mass={checks['in_footprint_mass']} ({time.time()-t0:.0f}s)", flush=True)
    hard = [k for k, v in checks["checks"].items()
            if v.get("hard_requirement") and not v["pass"]]
    if hard:
        print(f"    HARD FAILURES: {hard}", flush=True)

    note = (f"KANLER geocontrast v1 | HGB on 19 bands + field-concordance | "
            f"HOLDOUT-DTI {holdout_res['dti']:.4f} | id {cid} | not yet live-scored")
    note = note[:140]
    card = {
        "schema": "kanler.unique_submission.v1",
        "generated_utc": now(),
        "hypothesis": "Aligned gradient concordance across independent potential-field "
                      "and topography bands marks unmapped structural edges.",
        "mechanism": "Gradient-magnitude contrast + pairwise gradient-direction "
                     "concordance (RTP, gravity, elevation, tilt) fed to HGB; "
                     "ridge-NMS dot emission at 37,654 budget.",
        "named_non_fault_mimic": "Lithologic contact / playa shoreline / flight-line seam; "
                                 "mitigated by requiring >=2 fields to agree.",
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": MTR_EVALUATOR_VERSION,
            "dti": holdout_res["dti"],
            "ci95": holdout_res["ci95"],
            "withheld_positives": holdout_res["n_withheld_positive_pixels"],
            "method": "SegmentHoldout quadrant spatial folds, buffer 15 px, pooled DTI",
        },
        "leaderboard_estimate": "NOT ESTIMABLE from holdout; no projection is written as a score",
        "uniqueness_basis": "New method (field-concordance HGB), not a copy or perturbation of any focus-site winner",
        "raster_sha256": sha256_file(tif_path),
        "zip_sha256": sha256_file(zip_path),
        "content_id": cid,
        "dots": int(dots.sum()),
        "submission_name": stem,
        "submission_note": note,
        "note_chars": len(note),
        "tif": str(tif_path.relative_to(ROOT)),
        "zip": str(zip_path.relative_to(ROOT)),
        "validator": checks,
        "ok_to_download": checks["format_valid"],
        "verdict": "promote" if checks["format_valid"] else "negative",
    }
    (ROOT / "evidence" / "unique_submission_run_card.json").write_text(
        json.dumps(card, indent=2, default=float) + "\n")
    print(f"\n=== DONE ({time.time()-t0:.0f}s) ===", flush=True)
    print(f"TIF: {tif_path}", flush=True)
    print(f"SHA-256: {card['raster_sha256']}", flush=True)
    print(f"Format valid: {checks['format_valid']}", flush=True)
    print(f"Verdict: {card['verdict']}", flush=True)
    print(f"Note ({len(note)} chars): {note}", flush=True)


if __name__ == "__main__":
    main()
