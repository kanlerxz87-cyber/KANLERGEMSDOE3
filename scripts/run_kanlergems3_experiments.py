#!/usr/bin/env python3
"""End-to-end deterministic experiment runner for KANLERGEMSDOE3 (L-K3-CADG-SUBMOD).

Executes the frozen 3-experiment within-lane ablation plan locked in
``evidence/preregistration_20261026.json``:
  - Step 0: Verify frozen preregistration SHA-256 & restored input pins
  - Step 1: Build/load label-free feature cache (<350 MB RSS)
  - Step 2: Run two-polarity single-feature leakage canaries across ALL cached +
            fold-visible continuation features (halt fail-closed if any AUC > 0.90)
  - Step 3: Execute <= 3 controlled within-lane experiments (Exp-K3-1, Exp-K3-2, Exp-K3-3)
            on pinned SegmentHoldout(buffer_px=15) alongside matched leak-free baselines
            & historical static benchmarks, plus orthogonal confirmation on
            DiagonalSegmentHoldout(buffer_px=20)
  - Step 4: Construct stitched 8-fold spatial out-of-fold cross-fitted deployment surface
            (0.5 * quadrant OOF + 0.5 * diagonal-wedge OOF; zero in-sample training
            memorization around catalogue collars) & run 36-raster uniqueness guard on
            BOTH pre-placement ridge surface AND final binary dots
  - Step 5: Emit validated -zeros.tif/.zip and -nan.tif/.zip via shared submission_writer.py,
            audit saved bytes via validate_submission.py, assess scripts/promotion_gate.py,
            and emit run-card.json + full evidence bundle.
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import argparse
import gc
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_holdout import (  # noqa: E402
    DiagonalSegmentHoldout,
    SegmentHoldout,
    audit_uniqueness_against_registry,
    dti_score_fast,
    sha256_file,
)
from kanlergems3.features import (  # noqa: E402
    build_or_load_feature_cache,
    compute_visible_continuation,
)
from kanlergems3.models import (  # noqa: E402
    fit_baseline_regional_19band,
    fit_lane_experiment,
    predict_baseline_regional_19band,
    predict_lane_surface,
)
from kanlergems3.submodular import (  # noqa: E402
    celf_submodular_emit_300m,
    greedy_spacing_emit,
)
import promotion_gate  # noqa: E402
from submission_writer import write_pair  # noqa: E402
from validate_submission import audit as audit_saved_tiff  # noqa: E402
from vendor.gems24_template.metric import ridge_nms, select_top_positive  # noqa: E402

PREREG_PATH = ROOT / "evidence/preregistration_20261026.json"
PREREG_SHA256 = "e49c6aae3afafdcb60306ac79ff439d48fdfde2342b4fb9c0ba611fb23f54278"
REGISTRY_MANIFEST_PATH = ROOT / "registry/uniqueness_registry_20261026.json"
EVIDENCE_OUT = ROOT / "evidence/kanlergems3_experiments_20261026.json"
CANARY_OUT = ROOT / "evidence/kanlergems3_leakage_canaries_20261026.json"
UNIQUENESS_OUT = ROOT / "evidence/kanlergems3_uniqueness_20261026.json"

FULL_DOT_BUDGET = 37_654
COLLAR_PX = 2.05
SUBMOD_SELF_SPACING_PX = 2.5


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")


def _load_raster_bool(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1, masked=False)
    return np.isfinite(a) & (a > 0.0) & footprint


def _build_unsupervised_multiphysics_surface(
    mm: np.memmap,
    meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
) -> np.ndarray:
    """100% label-free heuristic multi-physics composite (leak-free D2.8/H33-style baseline)."""
    col_map = {n: i for i, n in enumerate(meta["feature_names"])}

    def zpos(cname: str) -> np.ndarray:
        v = np.asarray(mm[:, col_map[cname]], dtype=np.float32)
        fin = np.isfinite(v)
        med = float(np.median(v[fin]))
        mad = float(np.median(np.abs(v[fin] - med))) * 1.4826 + 1e-6
        z = np.clip((v - med) / mad, 0.0, 8.0) / 8.0
        return np.where(fin, z, np.nan).astype(np.float32)

    lid = zpos("lidar_step_max")
    t10 = zpos("topo10_curv_prof_absmax")
    mag = zpos("tmi_hg")
    grv = zpos("iso_grav_anom_hg")
    bas = zpos("basement_grad")
    has_lid = mm[:, col_map["has_lidar"]] > 0.5
    scarp = np.where(has_lid & np.isfinite(lid), 0.65 * lid + 0.35 * t10, t10)
    comp_fp = 0.50 * scarp + 0.20 * mag + 0.18 * grv + 0.12 * bas
    surf = np.zeros(footprint.shape, dtype=np.float32)
    surf.ravel()[fp_idx] = comp_fp.astype(np.float32)
    return surf


def _run_batched_canaries(
    holdout: SegmentHoldout,
    mm: np.memmap,
    feature_names: list[str],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    batch_size: int = 8,
) -> tuple[list[dict[str, Any]], bool]:
    expected_total = len(feature_names) + 3
    if CANARY_OUT.is_file():
        cached = json.loads(CANARY_OUT.read_text())
        if cached.get("tested_features_count") == expected_total and len(cached.get("all_features", [])) == expected_total:
            return cached["all_features"], bool(cached["leakage_suspected"])

    rows: list[dict[str, Any]] = []
    any_suspect = False
    n_feats = len(feature_names)
    for start in range(0, n_feats, batch_size):
        batch_names = feature_names[start : start + batch_size]
        batch_dict: dict[str, np.ndarray] = {}
        for offset, fname in enumerate(batch_names):
            arr = np.zeros(footprint.shape, dtype=np.float32)
            arr.ravel()[fp_idx] = mm[:, start + offset]
            batch_dict[fname] = arr
        res = holdout.canary(batch_dict, seed=20261025)
        for fname in batch_names:
            fmeta = res["features"][fname]
            max_fold = float(max(max(d["auc"], 1.0 - d["auc"]) for d in fmeta["folds"]))
            two_pooled = float(max(fmeta["pooled_auc"], 1.0 - fmeta["pooled_auc"]))
            suspect = bool(fmeta["leakage_suspected"])
            any_suspect = any_suspect or suspect
            rows.append(
                {
                    "feature": fname,
                    "group": "label_free_cached",
                    "raw_pooled_auc": round(float(fmeta["pooled_auc"]), 6),
                    "two_sided_pooled_auc": round(two_pooled, 6),
                    "max_two_sided_fold_auc": round(max_fold, 6),
                    "max_canary_auc": round(max(two_pooled, max_fold), 6),
                    "leakage_suspected": suspect,
                }
            )
        del batch_dict
        gc.collect()

    oof_cont = {
        "vis_relay_band_300_3500m": np.zeros(footprint.shape, dtype=np.float32),
        "vis_tip_propagation_lobe": np.zeros(footprint.shape, dtype=np.float32),
        "vis_belt_density_2p5km": np.zeros(footprint.shape, dtype=np.float32),
    }
    for fold in holdout.folds:
        c_fold = compute_visible_continuation(fold["visible"], footprint)
        v_mask = fold["valid"]
        for k in oof_cont:
            oof_cont[k][v_mask] = c_fold[k][v_mask]
    res_c = holdout.canary(oof_cont, seed=20261025)
    for fname, fmeta in res_c["features"].items():
        max_fold = float(max(max(d["auc"], 1.0 - d["auc"]) for d in fmeta["folds"]))
        two_pooled = float(max(fmeta["pooled_auc"], 1.0 - fmeta["pooled_auc"]))
        suspect = bool(fmeta["leakage_suspected"])
        any_suspect = any_suspect or suspect
        rows.append(
            {
                "feature": fname,
                "group": "fold_visible_only_continuation",
                "raw_pooled_auc": round(float(fmeta["pooled_auc"]), 6),
                "two_sided_pooled_auc": round(two_pooled, 6),
                "max_two_sided_fold_auc": round(max_fold, 6),
                "max_canary_auc": round(max(two_pooled, max_fold), 6),
                "leakage_suspected": suspect,
            }
        )
    del oof_cont
    gc.collect()
    return rows, any_suspect


def _score_piedmont_blind_diagnostic(
    oof_dots_map: dict[str, np.ndarray],
    data_dir: Path,
    mm: np.memmap,
    meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    catalogue: np.ndarray,
) -> dict[str, Any]:
    with rasterio.open(data_dir / "external/derived_sgmc_faults_100m_u8.tif") as src:
        sgmc = (src.read(1) > 0) & footprint
    d_cat = distance_transform_edt(~catalogue)
    col_map = {n: i for i, n in enumerate(meta["feature_names"])}
    depth_2d = np.zeros(footprint.shape, dtype=np.float32)
    relief_2d = np.zeros(footprint.shape, dtype=np.float32)
    depth_2d.ravel()[fp_idx] = mm[:, col_map["depth_to_base_surf"]]
    relief_2d.ravel()[fp_idx] = mm[:, col_map["topo10_relief_local"]]

    piedmont_domain = footprint & ~catalogue & (d_cat > 3.0) & (depth_2d >= 200.0) & (relief_2d < 180.0)
    c_pied_truth = sgmc & piedmont_domain
    b_prime_domain = footprint & ~catalogue & (d_cat > 3.0)
    b_prime_truth = sgmc & b_prime_domain

    out: dict[str, Any] = {
        "note": (
            "DIAGNOSTIC-ONLY (non-promotional; SGMC never used in feature engineering or model training). "
            "Instrument C_pied (piedmont/basin-margin blind faults, depth>=200m & low local relief, d_cat>300m) "
            "calibrated at Spearman rho=+0.8667 across 22 live-scored owner submissions."
        ),
        "c_pied_positive_pixels": int(c_pied_truth.sum()),
        "b_prime_positive_pixels": int(b_prime_truth.sum()),
        "models": {},
    }
    for name, pred in oof_dots_map.items():
        res_c = dti_score_fast(pred, c_pied_truth, valid_mask=piedmont_domain, catalogue_mask=catalogue)
        res_b = dti_score_fast(pred, b_prime_truth, valid_mask=b_prime_domain, catalogue_mask=catalogue)
        d_on = d_cat[pred & footprint & ~catalogue]
        out["models"][name] = {
            "c_pied_dti": round(float(res_c["dti"]), 6),
            "c_pied_coverage": round(float(res_c["coverage"]), 6),
            "b_prime_dti": round(float(res_b["dti"]), 6),
            "emitted_dots": int(pred.sum()),
            "fraction_dots_d_cat_gt_10px": round(float((d_on > 10.0).mean()), 6) if d_on.size else 0.0,
        }
    return out


def _make_surface_preview_dots(surface_2d: np.ndarray, eligible_2d: np.ndarray, budget: int) -> np.ndarray:
    """Pre-submodular 1-px Hessian ridge level set on continuous surface at matched budget."""
    ridges = ridge_nms(surface_2d, eligible_2d, sigma=1.0) & eligible_2d
    out = select_top_positive(np.where(ridges, surface_2d, 0.0), eligible_2d, budget)
    cur = int(out.sum())
    if cur < budget:
        rem = eligible_2d & ~out
        out |= select_top_positive(surface_2d, rem, budget - cur)
    return out


def run_all() -> int:
    t0 = time.monotonic()
    started_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    actual_prereg_sha = sha256_file(PREREG_PATH)
    if actual_prereg_sha != PREREG_SHA256:
        raise SystemExit(
            f"Frozen preregistration modified: {actual_prereg_sha} != {PREREG_SHA256}; halting."
        )
    data_dir = Path(os.environ.get("GEMS_DATA_DIR", ROOT / ".cache/gems_data"))
    cache_dir = ROOT / ".cache/gems_work"
    if not (data_dir / "training_features.tif").is_file():
        raise SystemExit("Missing restored data in .cache/gems_data; run ./scripts/download_competition_data.sh first.")

    print("[Step 1/5] Building/loading label-free memmap cache...", flush=True)
    fcache = build_or_load_feature_cache(data_dir, cache_dir)
    mm = fcache["memmap"]
    meta = fcache["meta"]
    footprint = fcache["footprint"]
    fp_idx = fcache["fp_idx"]
    n_fp = int(footprint.sum())
    catalogue = _load_raster_bool(data_dir / "labels.tif", footprint)
    print(
        f"  Cache ready: {meta['n_features']} features x {n_fp:,} footprint cells (digest {meta['cache_digest_sha256'][:16]})",
        flush=True,
    )

    screen_holdout = SegmentHoldout(footprint, catalogue, buffer_px=15)
    confirm_holdout = DiagonalSegmentHoldout(footprint, catalogue, buffer_px=20)

    print("[Step 2/5] Verifying two-polarity single-feature leakage canaries (Rule 4)...", flush=True)
    canary_rows, leakage_suspect = _run_batched_canaries(
        screen_holdout, mm, meta["feature_names"], footprint, fp_idx, batch_size=8
    )
    max_canary_auc = float(max(r["max_canary_auc"] for r in canary_rows))
    top5_canaries = sorted(canary_rows, key=lambda r: r["max_canary_auc"], reverse=True)[:5]
    canary_summary = {
        "evaluator_version": "gems-segment-pooled-v1",
        "split_id": "quadrant-buffered-15px-v1",
        "threshold_two_sided_auc": 0.90,
        "tested_features_count": len(canary_rows),
        "max_feature_auc": max_canary_auc,
        "leakage_suspected": leakage_suspect,
        "top_5_features_by_auc": top5_canaries,
        "all_features": canary_rows,
    }
    _write_json(CANARY_OUT, canary_summary)
    print(
        f"  Tested {len(canary_rows)} features; max two-sided canary AUC = {max_canary_auc:.4f} (limit 0.90)",
        flush=True,
    )
    if leakage_suspect or max_canary_auc > 0.90:
        raise SystemExit(f"LEAKAGE CANARY TRIPPED (max AUC = {max_canary_auc:.4f} > 0.90); halting.")

    d28_static = _load_raster_bool(
        data_dir / "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", footprint
    )
    h33_static = _load_raster_bool(data_dir / "registry/GEMSDOE32.tif", footprint)
    h19_static = _load_raster_bool(
        data_dir / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
        footprint,
    )
    p8_static = _load_raster_bool(data_dir / "registry/G70-p8-oof38k.tif", footprint)
    p9_static = _load_raster_bool(data_dir / "registry/G70-p9-piedmont-submod.tif", footprint)
    g33_csht_static = _load_raster_bool(data_dir / "registry/G33-a33-r2-csht-0b78c04d5fad.tif", footprint)
    unsup_d28_surf = _build_unsupervised_multiphysics_surface(mm, meta, footprint, fp_idx)

    print("[Step 3/5] Running 3 controlled within-lane experiments on primary 4-fold holdout...", flush=True)
    series_names = [
        "matched_random",
        "static_H33_B2",
        "static_G70_P8",
        "unsupervised_D28_37654",
        "B0_regional_d28",
        "Exp-K3-1",
        "Exp-K3-2",
        "Exp-K3-3",
        "archive_unbuffered_D28_44k",
        "archive_unbuffered_H19_5_121k",
    ]
    screen_preds: dict[str, list[np.ndarray]] = {k: [] for k in series_names}
    oof_quad_surfaces: dict[str, np.ndarray] = {
        e: np.zeros(footprint.shape, dtype=np.float32) for e in ("Exp-K3-1", "Exp-K3-2", "Exp-K3-3")
    }
    fold_reports: list[dict[str, Any]] = []

    for fold in screen_holdout.folds:
        f_id = int(fold["id"])
        fname = fold["name"]
        valid = fold["valid"]
        train = fold["train"]
        visible = fold["visible"]
        truth = fold["truth"]
        if (train & valid).any() or (visible & truth).any():
            raise RuntimeError(f"Holdout leakage invariant violated in fold {fname}")

        d_vis = distance_transform_edt(~visible)
        eligible = valid & (d_vis > COLLAR_PX)
        active_mass = valid & ~visible & (d_vis > 1.5)
        budget = int(round(FULL_DOT_BUDGET * int(valid.sum()) / n_fp))
        t_fold = time.monotonic()

        rng = np.random.default_rng(20261026 + 31 * f_id)
        rnd_surf = np.zeros(footprint.shape, dtype=np.float32)
        rnd_surf[eligible] = rng.random(int(eligible.sum()), dtype=np.float32)
        screen_preds["matched_random"].append(
            greedy_spacing_emit(rnd_surf, eligible, budget, min_spacing_px=2.8).astype(np.uint8)
        )
        screen_preds["static_H33_B2"].append((h33_static & valid & ~visible).astype(np.uint8))
        screen_preds["static_G70_P8"].append((p8_static & valid & ~visible).astype(np.uint8))
        screen_preds["unsupervised_D28_37654"].append(
            greedy_spacing_emit(unsup_d28_surf, eligible, budget, min_spacing_px=2.8).astype(np.uint8)
        )
        screen_preds["archive_unbuffered_D28_44k"].append((d28_static & valid & (d_vis > 2.0)).astype(np.uint8))
        screen_preds["archive_unbuffered_H19_5_121k"].append((h19_static & valid & ~visible).astype(np.uint8))

        b0_clf, b0_cols, b0_pr = fit_baseline_regional_19band(
            mm, meta, footprint, train, visible, seed=20261026 + 100 * f_id
        )
        b0_surf = predict_baseline_regional_19band(b0_clf, b0_cols, b0_pr, mm, footprint, fp_idx, valid)
        screen_preds["B0_regional_d28"].append(
            greedy_spacing_emit(b0_surf, eligible, budget, min_spacing_px=2.8).astype(np.uint8)
        )
        del b0_clf, b0_surf

        exp_meta_fold: dict[str, Any] = {}
        for exp_idx, exp_id in enumerate(("Exp-K3-1", "Exp-K3-2", "Exp-K3-3"), start=1):
            bundle = fit_lane_experiment(
                exp_id,
                mm,
                meta,
                footprint,
                fp_idx,
                train,
                visible,
                seed=20261026 + 1000 * exp_idx + 100 * f_id,
            )
            surf = predict_lane_surface(bundle, mm, footprint, fp_idx, valid, visible)
            oof_quad_surfaces[exp_id][valid] = surf[valid]
            dots = celf_submodular_emit_300m(
                surf,
                eligible,
                budget,
                active_mass_mask=active_mass,
                min_self_spacing_px=SUBMOD_SELF_SPACING_PX,
            )
            screen_preds[exp_id].append(dots.astype(np.uint8))
            exp_meta_fold[exp_id] = {**bundle.report, "emitted_dots": int(dots.sum())}
            del bundle, surf, dots
            gc.collect()

        fold_reports.append(
            {
                "fold": fname,
                "valid_pixels": int(valid.sum()),
                "train_pixels": int(train.sum()),
                "withheld_positives": int(truth.sum()),
                "dot_budget": budget,
                "elapsed_sec": round(time.monotonic() - t_fold, 2),
                "experiments": exp_meta_fold,
            }
        )
        print(
            f"  Fold {fname} done in {fold_reports[-1]['elapsed_sec']:.1f}s (budget={budget:,}, withheld={int(truth.sum()):,})",
            flush=True,
        )

    screen_summaries: dict[str, Any] = {}
    for sname, preds in screen_preds.items():
        screen_summaries[sname] = screen_holdout.summarize(preds, ci_draws=1999)
        print(
            f"  [HOLDOUT-DTI] {sname:28s}: {screen_summaries[sname]['dti']:.6f}  95% CI={screen_summaries[sname]['ci95']['interval']}",
            flush=True,
        )

    best_exp_id = max(("Exp-K3-1", "Exp-K3-2", "Exp-K3-3"), key=lambda e: screen_summaries[e]["dti"])
    print(f"  Selected top within-lane candidate: {best_exp_id} ({screen_summaries[best_exp_id]['dti']:.6f})", flush=True)

    baseline_keys = [
        "B0_regional_d28",
        "unsupervised_D28_37654",
        "static_H33_B2",
        "static_G70_P8",
        "matched_random",
    ]
    best_baseline_key = max(baseline_keys, key=lambda b: screen_summaries[b]["dti"])
    paired_vs_all_baselines = {
        bkey: screen_holdout.compare_paired(
            screen_preds[best_exp_id], screen_preds[bkey], ci_draws=1999, seed=20261026
        )
        for bkey in baseline_keys
    }
    paired_ablation_steps = {
        "Exp-K3-2_vs_Exp-K3-1": screen_holdout.compare_paired(
            screen_preds["Exp-K3-2"], screen_preds["Exp-K3-1"], ci_draws=1999, seed=20261026
        ),
        "Exp-K3-3_vs_Exp-K3-2": screen_holdout.compare_paired(
            screen_preds["Exp-K3-3"], screen_preds["Exp-K3-2"], ci_draws=1999, seed=20261026
        ),
        "Exp-K3-3_vs_Exp-K3-1": screen_holdout.compare_paired(
            screen_preds["Exp-K3-3"], screen_preds["Exp-K3-1"], ci_draws=1999, seed=20261026
        ),
    }

    print("[Step 3b/5] Running orthogonal DiagonalSegmentHoldout(buffer_px=20) confirmation...", flush=True)
    confirm_preds: dict[str, list[np.ndarray]] = {
        "B0_regional_d28": [],
        "unsupervised_D28_37654": [],
        best_exp_id: [],
    }
    oof_diag_surface = np.zeros(footprint.shape, dtype=np.float32)
    for fold in confirm_holdout.folds:
        f_id = int(fold["id"])
        valid = fold["valid"]
        train = fold["train"]
        visible = fold["visible"]
        if (train & valid).any() or (visible & fold["truth"]).any():
            raise RuntimeError(f"Confirmation leakage invariant violated in {fold['name']}")
        d_vis = distance_transform_edt(~visible)
        eligible = valid & (d_vis > COLLAR_PX)
        active_mass = valid & ~visible & (d_vis > 1.5)
        budget = int(round(FULL_DOT_BUDGET * int(valid.sum()) / n_fp))

        confirm_preds["unsupervised_D28_37654"].append(
            greedy_spacing_emit(unsup_d28_surf, eligible, budget, min_spacing_px=2.8).astype(np.uint8)
        )

        b0_clf, b0_cols, b0_pr = fit_baseline_regional_19band(
            mm, meta, footprint, train, visible, seed=20261026 + 500 + 100 * f_id
        )
        b0_surf = predict_baseline_regional_19band(b0_clf, b0_cols, b0_pr, mm, footprint, fp_idx, valid)
        confirm_preds["B0_regional_d28"].append(
            greedy_spacing_emit(b0_surf, eligible, budget, min_spacing_px=2.8).astype(np.uint8)
        )
        del b0_clf, b0_surf

        bundle_c = fit_lane_experiment(
            best_exp_id,
            mm,
            meta,
            footprint,
            fp_idx,
            train,
            visible,
            seed=20261026 + 7000 + 100 * f_id,
        )
        surf_c = predict_lane_surface(bundle_c, mm, footprint, fp_idx, valid, visible)
        oof_diag_surface[valid] = surf_c[valid]
        dots_c = celf_submodular_emit_300m(
            surf_c,
            eligible,
            budget,
            active_mass_mask=active_mass,
            min_self_spacing_px=SUBMOD_SELF_SPACING_PX,
        )
        confirm_preds[best_exp_id].append(dots_c.astype(np.uint8))
        del bundle_c, surf_c, dots_c
        gc.collect()

    confirm_summaries = {k: confirm_holdout.summarize(v, ci_draws=1999) for k, v in confirm_preds.items()}
    best_confirm_base = max(("B0_regional_d28", "unsupervised_D28_37654"), key=lambda b: confirm_summaries[b]["dti"])
    confirm_paired = {
        b: confirm_holdout.compare_paired(confirm_preds[best_exp_id], confirm_preds[b], ci_draws=1999, seed=20261026)
        for b in ("B0_regional_d28", "unsupervised_D28_37654")
    }
    print(
        f"  [CONFIRM HOLDOUT-DTI] {best_exp_id}={confirm_summaries[best_exp_id]['dti']:.6f} vs "
        f"{best_confirm_base}={confirm_summaries[best_confirm_base]['dti']:.6f} "
        f"(paired CI={confirm_paired[best_confirm_base]['paired_delta_ci95']})",
        flush=True,
    )

    print("[Step 4/5] Building 8-fold cross-fitted OOF deployment surface & screening 36-raster uniqueness...", flush=True)
    d_full_cat = distance_transform_edt(~catalogue)
    full_eligible = footprint & (d_full_cat > COLLAR_PX)
    full_active_mass = footprint & ~catalogue & (d_full_cat > 1.5)

    # Cross-fitted 8-fold OOF surface (0.5 * 4-quadrant OOF + 0.5 * 4-diagonal-wedge OOF):
    # Every footprint pixel is predicted strictly out-of-sample across two orthogonal spatial
    # partitions, preventing in-sample catalogue leaf memorization in 2.05 < d_cat <= 8.0 px.
    full_surface = (0.5 * oof_quad_surfaces[best_exp_id] + 0.5 * oof_diag_surface).astype(np.float32)
    full_surface = np.where(footprint, full_surface, 0.0).astype(np.float32)
    np.save(cache_dir / "deployed_oof8f_surface_fp.npy", full_surface.ravel()[fp_idx])

    preview_dots = _make_surface_preview_dots(full_surface, full_eligible, FULL_DOT_BUDGET)
    final_dots = celf_submodular_emit_300m(
        full_surface,
        full_eligible,
        FULL_DOT_BUDGET,
        active_mass_mask=full_active_mass,
        min_self_spacing_px=SUBMOD_SELF_SPACING_PX,
    )
    if int(final_dots.sum()) != FULL_DOT_BUDGET:
        raise RuntimeError(f"Expected {FULL_DOT_BUDGET} dots, emitted {int(final_dots.sum())}")

    oof_maps = {
        "static_H33_B2": h33_static & ~catalogue,
        "static_G70_P8": p8_static & ~catalogue,
        "static_G70_P9": p9_static & ~catalogue,
        "static_G33_CSHT": g33_csht_static & ~catalogue,
        "unsupervised_D28_37654": np.sum(screen_preds["unsupervised_D28_37654"], axis=0) > 0,
        "B0_regional_d28": np.sum(screen_preds["B0_regional_d28"], axis=0) > 0,
        "deployed_oof8f_candidate": final_dots & ~catalogue,
    }
    piedmont_diag = _score_piedmont_blind_diagnostic(
        oof_maps, data_dir, mm, meta, footprint, fp_idx, catalogue
    )
    print(
        f"  [DIAGNOSTIC C_pied] H33={piedmont_diag['models']['static_H33_B2']['c_pied_dti']:.4f} "
        f"G70-P8={piedmont_diag['models']['static_G70_P8']['c_pied_dti']:.4f} "
        f"G33-CSHT={piedmont_diag['models']['static_G33_CSHT']['c_pied_dti']:.4f} "
        f"deployed_oof8f={piedmont_diag['models']['deployed_oof8f_candidate']['c_pied_dti']:.4f} "
        f"(d_cat>10px={piedmont_diag['models']['deployed_oof8f_candidate']['fraction_dots_d_cat_gt_10px']:.1%})",
        flush=True,
    )

    reg_manifest = json.loads(REGISTRY_MANIFEST_PATH.read_text())
    reg_entries = [
        {**e, "resolved_path": str(data_dir / e["dest"])}
        for e in reg_manifest["rasters"]
    ]
    uniq_report = audit_uniqueness_against_registry(
        full_surface, preview_dots, final_dots, footprint, catalogue, reg_entries
    )
    _write_json(UNIQUENESS_OUT, uniq_report)
    print(
        f"  Uniqueness (35 genuine detectors): passed={uniq_report['genuine_detectors_passed']} | "
        f"surface |rho|={uniq_report['surface']['genuine_detectors_max_abs_spearman_rho']:.4f}, "
        f"3px={uniq_report['surface']['genuine_detectors_max_preview_fraction_within_3px']:.4f} | "
        f"final |rho|={uniq_report['final_dots']['genuine_detectors_max_abs_spearman_rho']:.4f}, "
        f"3px={uniq_report['final_dots']['genuine_detectors_max_candidate_fraction_within_3px']:.4f}",
        flush=True,
    )
    print(
        f"  Uniqueness (literal all-36 incl. uniform 5x5 lattice probe): passed={uniq_report['passed']} | "
        f"surface 3px={uniq_report['surface']['max_preview_fraction_within_3px']:.4f}, "
        f"final 3px={uniq_report['final_dots']['max_candidate_fraction_within_3px']:.4f}",
        flush=True,
    )

    incumbent_comp = paired_vs_all_baselines[best_baseline_key]
    recorded_sibling_b1 = 0.11324405875705776
    recorded_sibling_csht = 0.13671594852245653

    # Literal un-weakened gate check (per research/review.md: report lattice conflict rather than weakening gate)
    prelim_verdict = (
        "promote"
        if (
            uniq_report["passed"]
            and screen_summaries[best_exp_id]["dti"]
            > max(screen_summaries[best_baseline_key]["dti"], recorded_sibling_b1, recorded_sibling_csht)
            and incumbent_comp["ci95_strictly_positive"]
            and confirm_paired[best_confirm_base]["ci95_strictly_positive"]
        )
        else "negative"
    )

    print("[Step 5/5] Emitting GeoTIFF bundle, auditing saved bytes & running promotion_gate...", flush=True)
    slug = f"h-k3-1-cadg-submod-{best_exp_id.lower()}-oof8f-{FULL_DOT_BUDGET}"
    note_tpl = (
        f"K3 {best_exp_id} 8f-OOF: decontam scarp+TMI150+hydro 300m CELF {FULL_DOT_BUDGET}d | "
        + ("PROMOTE" if prelim_verdict == "promote" else "HOLD-SEL")
        + " | {cid}"
    )
    receipt = write_pair(
        final_dots.astype(np.float32),
        template=data_dir / "sample_submission.tif",
        catalogue=catalogue,
        footprint=footprint,
        outdir=ROOT / "docs/downloads",
        family="kanlergemsdoe3",
        hypothesis=slug,
        date="20261026",
        note_template=note_tpl,
        scientific_verdict=prelim_verdict,
    )
    zero_path = ROOT / "docs/downloads" / receipt["primary_zero_outside"]["file"]
    nan_path = ROOT / "docs/downloads" / receipt["official_text_nan_outside_twin"]["file"]
    saved_audit = audit_saved_tiff(zero_path, data_dir / "sample_submission.tif", strict_zero_outside=True)
    saved_nan_audit = audit_saved_tiff(nan_path, data_dir / "sample_submission.tif", strict_zero_outside=False)
    if not saved_audit["pass"] or not saved_nan_audit["pass"]:
        raise RuntimeError("Independent post-write GeoTIFF audit failed!")

    cand_summary = screen_summaries[best_exp_id]
    cand_ci = [float(x) for x in cand_summary["ci95"]["interval"]]
    delta_ci = [float(x) for x in incumbent_comp["paired_delta_ci95"]]
    elapsed_sec = round(time.monotonic() - t0, 2)

    run_card = {
        "lane_id": "L-K3-CADG-SUBMOD",
        "selected_hypothesis_id": "H-K3-1",
        "selected_ablation_id": best_exp_id,
        "deployment_surface_mode": "8-fold-spatial-OOF-cross-fitted (0.5*quadrant + 0.5*diagonal)",
        "lane_recorded": True,
        "shared_template_pinned": True,
        "whole_segment_buffered_holdout": True,
        "visible_only_features": True,
        "pixel_exact_visible_mask": True,
        "all_features_canary_tested": True,
        "same_evaluator_incumbent": True,
        "registry_complete": True,
        "surface_checked_before_placement": True,
        "final_dots_checked": True,
        "saved_bytes_validated": bool(saved_audit["pass"]),
        "template_provenance_verified": False,
        "provenance_note": (
            "Shared Python evaluator/writer verified byte-for-byte against vendor/gems24_template/SOURCE.json "
            "(GEMSDOE24@fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1). Competition input rasters verified against "
            "SHA-256-pinned owner mirrors across 9 sibling repos (sample_submission.tif 2176d08e..., "
            "training_features.tif 4371c82e..., labels.tif 7ba308cc...); template_provenance_verified is set "
            "False fail-closed because DrivenData /data/ requires authenticated login."
        ),
        "hypothesis": (
            f"H-K3-1 ({best_exp_id}, lane L-K3-CADG-SUBMOD): Cultural/pluvial-decontaminated asymmetric 1 m LiDAR "
            "and seamless 10 m 3DEP piedmont scarp breaklines fused with 150 m upward-continued magnetic/gravity "
            "depth-persistence, label-free INGENIOUS hydrothermal/radiometric upflow halos, fold-safe visible tip/relay "
            "continuation, and exact 300 m submodular CELF binary dot allocation on an 8-fold spatial out-of-fold "
            "cross-fitted surface recover concealed off-catalogue Quaternary faults better than matched regional, "
            "unsupervised D2.8, and sibling holdout incumbents."
        ),
        "mechanism": (
            "Stitched 8-fold spatial out-of-fold (0.5 * 4-quadrant SegmentHoldout + 0.5 * 4-wedge DiagonalSegmentHoldout) "
            "dual HistGradientBoosting ensemble (full-stack + LiDAR-void 10 m/subsurface specialist) combining signed 1 m "
            "scarp polarity asymmetry |downface-upface|/(downface+upface+4) decontaminated by US Census TIGER/Line 2024 "
            "road distance and Lahontan/Bonneville highstand benches, 150 m upward-continued TMI depth-persistence ratio, "
            "Miller-Singh tilt edges, GeoDAWN K-metasomatism & INGENIOUS 2 m probe/spring/sinter upflow halos, and "
            "leave-component-out calibrated visible relay/tip lobes, emitted at exact N=37,654 off-catalogue binary dots "
            "via lazy-greedy 300 m DTI submodular coverage."
        ),
        "non_fault_mimic": (
            "Buried caldera/plutonic intrusive ring contacts or tilted Miocene ash-flow tuff hogbacks located far "
            "from TIGER/Line roads and outside Pleistocene Lake Lahontan (1332 m) / Bonneville (1463, 1552 m) "
            "shorelines that juxtapose contrasting magnetic susceptibilities and fossil K-alteration without Quaternary slip."
        ),
        "holdout": {
            "class": "HOLDOUT-DTI",
            "evaluator_version": cand_summary["evaluator_version"],
            "split_id": "quadrant-buffered-15px-v1",
            "withheld_positives": int(cand_summary["n_withheld_positive_pixels"]),
            "value": float(cand_summary["dti"]),
            "ci95": cand_ci,
            "alpha": 0.2,
            "beta": 0.8,
            "kernel_m": 300,
            "kernel": "triangular",
            "aggregation": "pooled",
        },
        "incumbent_comparison": {
            "strongest_same_evaluator_incumbent": best_baseline_key,
            "incumbent_holdout_dti": float(screen_summaries[best_baseline_key]["dti"]),
            "incumbent_ci95": screen_summaries[best_baseline_key]["ci95"]["interval"],
            "recorded_gemsdoe33_b1_regional_holdout_dti": recorded_sibling_b1,
            "recorded_gemsdoe33_a33_r2_csht_holdout_dti": recorded_sibling_csht,
            "recorded_gemsdoe70_p9_holdout_dti": 0.1099675770922385,
            "paired_delta_dti": float(incumbent_comp["paired_delta_dti"]),
            "paired_delta_ci95": delta_ci,
            "fold_wins": f"{incumbent_comp['fold_wins']}/{incumbent_comp['n_folds']}",
            "all_leak_free_37654_baselines_holdout_dti": {
                k: {
                    "dti": round(float(screen_summaries[k]["dti"]), 6),
                    "ci95": [round(float(v), 6) for v in screen_summaries[k]["ci95"]["interval"]],
                }
                for k in baseline_keys
            },
            "within_lane_ablations_holdout_dti": {
                k: {
                    "dti": round(float(screen_summaries[k]["dti"]), 6),
                    "ci95": [round(float(v), 6) for v in screen_summaries[k]["ci95"]["interval"]],
                }
                for k in ("Exp-K3-1", "Exp-K3-2", "Exp-K3-3")
            },
            "contaminated_or_unmatched_archive_diagnostics": {
                "note": (
                    "Archive H19-5 (121,131 dots = 3.22x budget) and D2.8 (44,090 dots = 1.17x budget) were "
                    "generated in 19GEMSDOE on legacy unbuffered Holdout (no 1.5 km component purge) and "
                    "post-masked with labels.tif==0 across all 4 quadrants (packing 6,436 dots into 1<=d_truth<=2 px). "
                    "Reported for forensic completeness; NOT valid leak-free SegmentHoldout comparators."
                ),
                "archive_unbuffered_D28_44k_dti": round(float(screen_summaries["archive_unbuffered_D28_44k"]["dti"]), 6),
                "archive_unbuffered_H19_5_121k_dti": round(float(screen_summaries["archive_unbuffered_H19_5_121k"]["dti"]), 6),
            },
        },
        "independent_confirmation": {
            "class": "HOLDOUT-DTI",
            "evaluator_version": confirm_summaries[best_exp_id]["evaluator_version"],
            "split_id": confirm_summaries[best_exp_id]["split_id"],
            "withheld_positives": int(confirm_summaries[best_exp_id]["n_withheld_positive_pixels"]),
            "candidate_dti": float(confirm_summaries[best_exp_id]["dti"]),
            "candidate_ci95": confirm_summaries[best_exp_id]["ci95"]["interval"],
            "strongest_confirm_incumbent": best_confirm_base,
            "incumbent_dti": float(confirm_summaries[best_confirm_base]["dti"]),
            "paired_delta_dti": float(confirm_paired[best_confirm_base]["paired_delta_dti"]),
            "paired_delta_ci95": confirm_paired[best_confirm_base]["paired_delta_ci95"],
            "fold_wins": f"{confirm_paired[best_confirm_base]['fold_wins']}/{confirm_paired[best_confirm_base]['n_folds']}",
        },
        "diagnostic_piedmont_proxy": piedmont_diag,
        "paired_improvement_ci95": delta_ci,
        "max_feature_auc": max_canary_auc,
        # Un-weakened literal 36-raster metrics (per research/review.md: report lattice conflict, do not weaken gate)
        "surface_max_rank_correlation": float(uniq_report["surface"]["max_abs_spearman_rho"]),
        "surface_dot_overlap_3px": float(uniq_report["surface"]["max_preview_fraction_within_3px"]),
        "final_max_rank_correlation": float(uniq_report["final_dots"]["max_abs_spearman_rho"]),
        "final_dot_overlap_3px": float(uniq_report["final_dots"]["max_candidate_fraction_within_3px"]),
        "uniqueness_registry_summary": {
            "manifest_path": "registry/uniqueness_registry_20261026.json",
            "manifest_sha256": sha256_file(REGISTRY_MANIFEST_PATH),
            "total_rasters_checked": uniq_report["total_registry_rasters_checked"],
            "genuine_detector_rasters_checked": uniq_report["genuine_detector_rasters_checked"],
            "calibration_probes_checked": uniq_report["calibration_probes_checked"],
            "genuine_35_detectors_passed": bool(uniq_report["genuine_detectors_passed"]),
            "genuine_35_surface_max_abs_spearman_rho": float(
                uniq_report["surface"]["genuine_detectors_max_abs_spearman_rho"]
            ),
            "genuine_35_surface_dot_overlap_3px": float(
                uniq_report["surface"]["genuine_detectors_max_preview_fraction_within_3px"]
            ),
            "genuine_35_final_max_abs_spearman_rho": float(
                uniq_report["final_dots"]["genuine_detectors_max_abs_spearman_rho"]
            ),
            "genuine_35_final_dot_overlap_3px": float(
                uniq_report["final_dots"]["genuine_detectors_max_candidate_fraction_within_3px"]
            ),
            "nearest_genuine_surface_detector": uniq_report["surface"]["nearest_genuine_detector"],
            "nearest_genuine_final_detector": uniq_report["final_dots"]["nearest_genuine_detector"],
            "pigeonhole_lattice_bounds": uniq_report["pigeonhole_lattice_bounds"],
            "calibration_probes": uniq_report["calibration_probes"],
        },
        "raster_sha256": receipt["primary_zero_outside"]["sha256"],
        "validator": {
            "single_band": bool(saved_audit["checks"]["single_band"]["pass"]),
            "all_finite": bool(
                saved_audit["checks"]["footprint_all_finite"]["pass"] and saved_audit["whole_array_all_finite_0_1"]
            ),
            "range_0_1": bool(
                saved_audit["checks"]["footprint_range_0_1"]["pass"] and saved_audit["whole_array_all_finite_0_1"]
            ),
            "crs_match": bool(saved_audit["checks"]["crs_epsg_32611"]["pass"]),
            "shape_match": bool(saved_audit["checks"]["shape_matches_template"]["pass"]),
            "transform_match": bool(saved_audit["checks"]["geotransform_matches_template"]["pass"]),
            "whole_array_all_finite_0_1": bool(saved_audit["whole_array_all_finite_0_1"]),
            "predicted_positive_dots": int(saved_audit["in_footprint_positive_pixels"]),
            "catalogue_overlap_dots": int((final_dots & catalogue).sum()),
        },
        "submission_name": receipt["submission_name"],
        "submission_note": receipt["note"],
        "note": receipt["note"],
        "submission_artifacts": {
            "primary_zeros_tif": f"docs/downloads/{receipt['primary_zero_outside']['file']}",
            "primary_zeros_zip": f"docs/downloads/{receipt['primary_zero_outside']['zip']}",
            "primary_zeros_sha256": receipt["primary_zero_outside"]["sha256"],
            "primary_zeros_bytes": receipt["primary_zero_outside"]["bytes"],
            "official_nan_twin_tif": f"docs/downloads/{receipt['official_text_nan_outside_twin']['file']}",
            "official_nan_twin_zip": f"docs/downloads/{receipt['official_text_nan_outside_twin']['zip']}",
            "official_nan_twin_sha256": receipt["official_text_nan_outside_twin"]["sha256"],
            "note_file": f"docs/downloads/{receipt['note_file']}",
            "receipt_file": f"docs/downloads/{receipt['receipt_file']}",
        },
        "experiments_used": 3,
        "max_experiments_budget": 3,
        "elapsed_seconds": elapsed_sec,
        "live_submission_slots_used": 0,
    }

    gate_result = promotion_gate.assess(run_card)
    run_card["verdict"] = gate_result["verdict"]
    run_card["gate_failures"] = gate_result["failures"]
    run_card["slot_authorized"] = gate_result["slot_authorized"]

    _write_json(ROOT / "run-card.json", run_card)
    _write_json(ROOT / "docs/run-card.json", run_card)
    _write_json(ROOT / "docs/data/run_card.json", run_card)

    full_evidence = {
        "schema_version": 1,
        "started_utc": started_utc,
        "completed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "preregistration_path": "evidence/preregistration_20261026.json",
        "preregistration_sha256": PREREG_SHA256,
        "feature_cache_meta": meta,
        "canary_summary": {
            "tested_features_count": len(canary_rows),
            "max_feature_auc": max_canary_auc,
            "top_5_features_by_auc": top5_canaries,
        },
        "screen_fold_reports": fold_reports,
        "screen_summaries": screen_summaries,
        "paired_vs_all_baselines": paired_vs_all_baselines,
        "paired_ablation_steps": paired_ablation_steps,
        "confirm_summaries": confirm_summaries,
        "confirm_paired": confirm_paired,
        "diagnostic_piedmont_proxy": piedmont_diag,
        "uniqueness_summary": {
            "literal_all_36_passed": uniq_report["passed"],
            "genuine_35_detectors_passed": uniq_report["genuine_detectors_passed"],
            "surface": uniq_report["surface"],
            "final_dots": uniq_report["final_dots"],
            "pigeonhole_lattice_bounds": uniq_report["pigeonhole_lattice_bounds"],
            "calibration_probes": uniq_report["calibration_probes"],
        },
        "submission_receipt": receipt,
        "promotion_gate": gate_result,
        "elapsed_seconds": elapsed_sec,
    }
    _write_json(EVIDENCE_OUT, full_evidence)

    print(
        json.dumps(
            {
                "verdict": run_card["verdict"],
                "gate_failures": run_card["gate_failures"],
                "genuine_35_detectors_passed": uniq_report["genuine_detectors_passed"],
                "genuine_35_final_3px_overlap": uniq_report["final_dots"]["genuine_detectors_max_candidate_fraction_within_3px"],
                "selected_ablation": best_exp_id,
                "HOLDOUT_DTI": run_card["holdout"]["value"],
                "HOLDOUT_CI95": run_card["holdout"]["ci95"],
                "strongest_incumbent": best_baseline_key,
                "incumbent_HOLDOUT_DTI": screen_summaries[best_baseline_key]["dti"],
                "paired_delta_CI95": delta_ci,
                "confirm_HOLDOUT_DTI": confirm_summaries[best_exp_id]["dti"],
                "confirm_paired_delta_CI95": confirm_paired[best_confirm_base]["paired_delta_ci95"],
                "deployed_c_pied_dti": piedmont_diag["models"]["deployed_oof8f_candidate"]["c_pied_dti"],
                "deployed_d_cat_gt_10px": piedmont_diag["models"]["deployed_oof8f_candidate"]["fraction_dots_d_cat_gt_10px"],
                "primary_tif": receipt["primary_zero_outside"]["file"],
                "sha256": receipt["primary_zero_outside"]["sha256"],
                "elapsed_seconds": elapsed_sec,
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Verify recorded run-card and GeoTIFF bytes")
    args = parser.parse_args()
    if args.verify_only:
        card = json.loads((ROOT / "run-card.json").read_text())
        gate = promotion_gate.assess(card)
        tif_p = ROOT / card["submission_artifacts"]["primary_zeros_tif"]
        data_dir = Path(os.environ.get("GEMS_DATA_DIR", ROOT / ".cache/gems_data"))
        aud = audit_saved_tiff(tif_p, data_dir / "sample_submission.tif", strict_zero_outside=True)
        ok = (
            gate["verdict"] == card["verdict"]
            and aud["pass"]
            and aud["sha256"] == card["raster_sha256"]
        )
        print(json.dumps({"ok": ok, "gate": gate, "saved_byte_audit_pass": aud["pass"]}, indent=2))
        return 0 if ok else 1
    return run_all()


if __name__ == "__main__":
    raise SystemExit(main())
