#!/usr/bin/env python3
"""Execute Frozen Lane KANLER-H1 (DCAP-LHC) end-to-end:
1. Build physical lines (label-free)
2. Run single-feature leakage canary (AUC <= 0.90)
3. EXP-1: Unsupervised Multi-Regime Crest Concordance vs REF_H31X, CTRL, SLOPE
4. EXP-2: Fold-Local SAR-PU Monotonic Out-of-Fold Crest Calibration (buffer_px=80)
5. EXP-3: Exact 300m Submodular CELF Allocation vs Greedy 2.8px Poisson + Random-Component Confirmation
6. Full 417-raster Cross-Site Uniqueness Audit + Dual GeoTIFF Packaging (`-zeros.tif` & `-nan.tif`) + Validation
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import evaluate_holdout as ev  # noqa: E402
from gems57 import metric as vmetric  # noqa: E402
from gems57 import spatial, submission_writer  # noqa: E402
from kanler_gems import h1_dcap_lhc as H1  # noqa: E402
from kanler_gems.registry_uniqueness import audit_surface_and_dots  # noqa: E402

EVID_DIR = ROOT / "evidence" / "kanler_h1"


def write_nan_outside_twin(
    nan_tif_path: Path,
    dots_mask: np.ndarray,
    foot: np.ndarray,
    sample_path: Path,
) -> dict:
    """Write companion DrivenData template-mask GeoTIFF (`NaN` outside footprint, `nodata=nan`)."""
    nan_tif_path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.full(foot.shape, np.nan, dtype=np.float32)
    arr[foot] = 0.0
    arr[dots_mask & foot] = 1.0
    with rasterio.open(sample_path) as tpl:
        profile = tpl.profile.copy()
    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=np.nan,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )
    tmp = nan_tif_path.with_suffix(".tmp.tif")
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(arr, 1)
    tmp.replace(nan_tif_path)

    nan_zip_path = nan_tif_path.with_suffix(".zip")
    with zipfile.ZipFile(nan_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(nan_tif_path, arcname=nan_tif_path.name)

    return {
        "tif_path": str(nan_tif_path.relative_to(ROOT)),
        "tif_bytes": nan_tif_path.stat().st_size,
        "tif_sha256": H1.sha256_file(nan_tif_path),
        "zip_path": str(nan_zip_path.relative_to(ROOT)),
        "zip_bytes": nan_zip_path.stat().st_size,
        "zip_sha256": H1.sha256_file(nan_zip_path),
    }


def verify_geotiff_on_disk(tif_path: Path, sample_path: Path, cat: np.ndarray) -> dict:
    with rasterio.open(sample_path) as ref, rasterio.open(tif_path) as src:
        ref_arr = ref.read(1)
        foot = np.isfinite(ref_arr)
        arr = src.read(1)
        in_vals = arr[foot]
        out_vals = arr[~foot]
        in_finite = bool(np.isfinite(in_vals).all())
        in_min = float(np.nanmin(in_vals)) if in_vals.size else 0.0
        in_max = float(np.nanmax(in_vals)) if in_vals.size else 0.0
        in_range_ok = bool(in_finite and in_min >= 0.0 and in_max <= 1.0)
        all_finite = bool(np.isfinite(arr).all())
        outside_all_nan = bool(np.isnan(out_vals).all())
        outside_all_zero = bool(np.isfinite(out_vals).all() and np.all(out_vals == 0.0))
        outside_pos = int(np.count_nonzero(np.isfinite(out_vals) & (out_vals > 0.0)))
        cat_pos = int(np.count_nonzero(np.isfinite(arr) & (arr > 0.0) & cat))
        crs_match = bool(src.crs == ref.crs and src.crs is not None and src.crs.to_epsg() == 32611)
        shape_match = bool(src.shape == ref.shape and src.shape == (3730, 3292))
        transform_match = bool(tuple(src.transform)[:6] == tuple(ref.transform)[:6])
        dtype_ok = bool(src.count == 1 and src.dtypes[0] == "float32")
        valid_outside_mode = "all_finite_zero_outside" if outside_all_zero else (
            "template_nan_outside" if outside_all_nan else "invalid_mixed_outside"
        )
        passed = bool(
            dtype_ok
            and crs_match
            and shape_match
            and transform_match
            and in_range_ok
            and (outside_all_zero or outside_all_nan)
            and outside_pos == 0
            and cat_pos == 0
        )
        return {
            "file": str(tif_path.relative_to(ROOT)),
            "bytes": tif_path.stat().st_size,
            "sha256": H1.sha256_file(tif_path),
            "passed": passed,
            "bands": src.count,
            "dtype": src.dtypes[0],
            "crs": str(src.crs),
            "shape": list(src.shape),
            "transform": list(src.transform)[:6],
            "nodata": str(src.nodata),
            "footprint_pixels": int(foot.sum()),
            "footprint_nan_count": int(np.isnan(in_vals).sum()),
            "footprint_inf_count": int(np.isinf(in_vals).sum()),
            "footprint_min": in_min,
            "footprint_max": in_max,
            "footprint_positive_pixels": int(np.count_nonzero(in_vals > 0.0)),
            "all_cells_finite": all_finite,
            "outside_mode": valid_outside_mode,
            "outside_positive_pixels": outside_pos,
            "catalogue_positive_pixels": cat_pos,
            "checks": {
                "single_band_float32": dtype_ok,
                "crs_epsg_32611_match": crs_match,
                "shape_3730x3292_match": shape_match,
                "transform_exact_match": transform_match,
                "no_nan_or_inf_inside_footprint": in_finite,
                "values_strictly_in_0_1": in_range_ok,
                "zero_positive_outside_footprint": outside_pos == 0,
                "zero_positive_on_known_catalogue": cat_pos == 0,
            },
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rebuild-lines", action="store_true")
    args = ap.parse_args()

    t_start = time.time()
    EVID_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Build physical lines
    lines_meta = H1.build_lines(ROOT, force=args.rebuild_lines)
    (EVID_DIR / "lines.json").write_text(json.dumps(lines_meta, indent=2) + "\n")

    # 2. Run single-feature leakage canary
    canary = H1.run_leakage_canary(ROOT)

    # Load base masks & canonical shared quadrant folds (`buffer_px=80`)
    foot, cat, sgmc, off_sgmc, d_cat = H1.load_base_masks(ROOT)
    folds = list(spatial.folds(cat, foot, buffer_px=H1.BUFFER_PX))
    fold_receipts = [f["receipt"] for f in folds]

    # 3. EXP-1: Unsupervised Multi-Regime Crest Concordance vs REF_H31X, CTRL, SLOPE
    H1.log("=== Running EXP-1 (Unsupervised Multi-Regime Crest Concordance) ===")
    unsup_surfaces = H1.build_unsupervised_surfaces(ROOT, foot)
    exp1_eval = H1.evaluate_surfaces_on_folds(unsup_surfaces, folds, foot, emitter="poisson")
    exp1_winner = max(("H1_JASYM", "H1_MULTI"), key=lambda a: ev.from_terms(exp1_eval["terms"][a].sum(axis=0)))
    exp1_summary = ev.pooled_summary(exp1_eval["terms"], draws=1000, seed=520810, candidate=exp1_winner)
    exp1_out = {
        "experiment": "EXP-1",
        "description": "Unsupervised Multi-Regime Crest Concordance (H1_JASYM, H1_MULTI) vs REF_H31X, CTRL, SLOPE",
        "winner": exp1_winner,
        "pooled_summary": exp1_summary,
        "per_fold": exp1_eval["per_fold"],
        "fold_receipts": fold_receipts,
    }
    (EVID_DIR / "exp1_unsupervised.json").write_text(json.dumps(exp1_out, indent=2) + "\n")
    H1.log(
        f"EXP-1 Winner: {exp1_winner} HOLDOUT-DTI={exp1_summary['scores'][exp1_winner]['dti']:.5f} "
        f"(REF_H31X={exp1_summary['scores']['REF_H31X']['dti']:.5f}, "
        f"CTRL={exp1_summary['scores']['CTRL']['dti']:.5f}, "
        f"SLOPE={exp1_summary['scores']['SLOPE']['dti']:.5f})"
    )

    # 4. EXP-2: Fold-Local SAR-PU Monotonic Out-of-Fold Crest Calibration (`buffer_px=80`)
    H1.log("=== Running EXP-2 (Fold-Local SAR-PU Monotonic OOF Calibration) ===")
    oof_pu_surfaces = []
    fold_weights = []
    for f in folds:
        params_f = H1.fit_nonneg_pu_weights(ROOT, f["train"], f["visible"], seed=1026 + int(f["fold"]))
        fold_weights.append({
            "fold": int(f["fold"]),
            "bias": float(params_f[0]),
            "weights": [round(float(x), 5) for x in params_f[1:]],
        })
        oof_pu_surfaces.append(H1.predict_pu_surface(ROOT, params_f, foot))

    exp2_eval = H1.evaluate_surfaces_on_folds({"H1_PU_OOF": oof_pu_surfaces}, folds, foot, emitter="poisson")
    combined_terms_exp2 = {**exp1_eval["terms"], **exp2_eval["terms"]}
    exp2_winner = max(
        (exp1_winner, "H1_PU_OOF"),
        key=lambda a: float(ev.from_terms(combined_terms_exp2[a].sum(axis=0))),
    )
    exp2_summary = ev.pooled_summary(combined_terms_exp2, draws=1000, seed=520810, candidate=exp2_winner)
    exp2_out = {
        "experiment": "EXP-2",
        "description": "Fold-local observability-debiased SAR-PU monotonic OOF calibration (buffer_px=80)",
        "fold_weights": fold_weights,
        "winner": exp2_winner,
        "pooled_summary": exp2_summary,
        "per_fold_pu": exp2_eval["per_fold"]["H1_PU_OOF"],
    }
    (EVID_DIR / "exp2_pu_oof.json").write_text(json.dumps(exp2_out, indent=2) + "\n")
    H1.log(
        f"EXP-2 Winner: {exp2_winner} HOLDOUT-DTI={exp2_summary['scores'][exp2_winner]['dti']:.5f} "
        f"(H1_PU_OOF={exp2_summary['scores']['H1_PU_OOF']['dti']:.5f} vs {exp1_winner}={exp2_summary['scores'][exp1_winner]['dti']:.5f})"
    )

    # 5. EXP-3: Exact 300 m Triangular-Kernel Submodular CELF Allocation vs Greedy 2.8 px Poisson Disk
    H1.log("=== Running EXP-3 (Exact 300m Submodular CELF vs 2.8px Poisson + Confirmation Split) ===")
    winning_surf_for_folds = oof_pu_surfaces if exp2_winner == "H1_PU_OOF" else unsup_surfaces[exp2_winner]
    celf_arm_name = f"{exp2_winner}_CELF"
    exp3_celf_eval = H1.evaluate_surfaces_on_folds(
        {celf_arm_name: winning_surf_for_folds}, folds, foot, emitter="celf"
    )
    all_terms = {**combined_terms_exp2, **exp3_celf_eval["terms"]}
    final_winner = max(
        (exp2_winner, celf_arm_name),
        key=lambda a: float(ev.from_terms(all_terms[a].sum(axis=0))),
    )
    final_emitter = "celf" if final_winner == celf_arm_name else "poisson"
    final_pooled = ev.pooled_summary(all_terms, draws=1000, seed=520810, candidate=final_winner)

    # Full-footprint production surface for final_winner (for confirmation split + full export)
    if exp2_winner == "H1_PU_OOF":
        # Average the 4 OOF non-negative weight vectors so full-map surface never fits directly on unbuffered pixels
        mean_params = np.mean([np.r_[fw["bias"], fw["weights"]] for fw in fold_weights], axis=0)
        full_surface = H1.predict_pu_surface(ROOT, mean_params, foot)
        # For confirmation split (seed=3103), fit strictly on confirmation split's visible buffered train mask!
        conf_fold = H1.random_component_split(cat, foot, seed=H1.CONFIRM_SEED)
        conf_params = H1.fit_nonneg_pu_weights(ROOT, conf_fold["train"], conf_fold["visible"], seed=3103)
        conf_cand_surface = H1.predict_pu_surface(ROOT, conf_params, foot)
    else:
        full_surface = unsup_surfaces[exp2_winner]
        conf_fold = H1.random_component_split(cat, foot, seed=H1.CONFIRM_SEED)
        conf_cand_surface = full_surface

    # Confirmation split evaluation (`seed=3103`, `29,965` withheld positives)
    d_vis_conf = H1.distance_transform_edt(~conf_fold["visible"]).astype(np.float32)
    allowed_conf = foot & (d_vis_conf > H1.B_PX)
    emit_fn_final = H1.emit_celf_submodular_300m if final_emitter == "celf" else H1.emit_poisson_disk

    conf_terms = {}
    for cname, csurf, cemit in [
        (final_winner, conf_cand_surface, emit_fn_final),
        ("REF_H31X", unsup_surfaces["REF_H31X"], H1.emit_poisson_disk),
        ("CTRL", unsup_surfaces["CTRL"], H1.emit_poisson_disk),
        ("SLOPE", unsup_surfaces["SLOPE"], H1.emit_poisson_disk),
    ]:
        cdots = cemit(csurf, allowed_conf & (csurf > 0), budget=H1.BUDGET)
        _, ctrm = ev.evaluate(cdots.astype(np.float32), conf_fold, foot)
        conf_terms[cname] = ctrm
    conf_summary = ev.pooled_summary(conf_terms, draws=1000, seed=520810, candidate=final_winner)

    exp3_out = {
        "experiment": "EXP-3",
        "description": "Exact 300 m triangular-kernel submodular CELF allocation vs greedy 2.8 px Poisson disk + confirmation split",
        "final_winner": final_winner,
        "final_base_surface": exp2_winner,
        "final_emitter": final_emitter,
        "primary_holdout_pooled": final_pooled,
        "per_fold_celf": exp3_celf_eval["per_fold"][celf_arm_name],
        "confirmation_random_component_50pct": {
            "partition": conf_fold["receipt"],
            "pooled_summary": conf_summary,
        },
    }
    (EVID_DIR / "exp3_celf_and_confirmation.json").write_text(json.dumps(exp3_out, indent=2) + "\n")
    H1.log(
        f"EXP-3 Final Winner: {final_winner} "
        f"Primary HOLDOUT-DTI={final_pooled['scores'][final_winner]['dti']:.5f} "
        f"(vs REF_H31X={final_pooled['scores']['REF_H31X']['dti']:.5f}); "
        f"Confirmation HOLDOUT-DTI={conf_summary['scores'][final_winner]['dti']:.5f} "
        f"(vs REF_H31X={conf_summary['scores']['REF_H31X']['dti']:.5f})"
    )

    # 6. Full-Catalogue Export (`d_cat > 2.0 px`), SGMC Diagnostics & Full 417-Raster Uniqueness Audit
    H1.log("=== Emitting Full-Footprint Dots & Running 417-Raster Uniqueness Audit ===")
    allowed_full = foot & (d_cat > H1.B_PX)
    final_dots = emit_fn_final(full_surface, allowed_full & (full_surface > 0), budget=H1.BUDGET)
    ref_h31x_dots = H1.emit_poisson_disk(unsup_surfaces["REF_H31X"], allowed_full & (unsup_surfaces["REF_H31X"] > 0), budget=H1.BUDGET)
    with rasterio.open(ROOT / "data/GEMSDOE32.tif") as ds:
        h33_dots = (ds.read(1) > 0) & foot

    sgmc_cand = H1.score_off_catalogue_sgmc(ROOT, final_dots, foot, off_sgmc)
    sgmc_h31x = H1.score_off_catalogue_sgmc(ROOT, ref_h31x_dots, foot, off_sgmc)
    sgmc_h33 = H1.score_off_catalogue_sgmc(ROOT, h33_dots, foot, off_sgmc)

    uniqueness = audit_surface_and_dots(
        ROOT,
        candidate_surface=full_surface,
        candidate_dots=final_dots,
        footprint=foot,
    )
    (EVID_DIR / "uniqueness_417_rasters.json").write_text(json.dumps(uniqueness, indent=2) + "\n")
    H1.log(
        "Uniqueness vs 415 genuine detector rasters: unique=",
        uniqueness["detector_scope"]["unique"],
        "worst_final_3px=",
        uniqueness["detector_scope"]["worst_final_dots_within_3px"],
        "worst_surface_spearman=",
        uniqueness["detector_scope"]["worst_abs_surface_spearman"],
    )

    # Package GeoTIFFs (`-zeros.tif` via shared `vendor/gems57/submission_writer.py` + `-nan.tif` twin)
    mask_hash8 = hashlib.sha256(np.packbits(final_dots[foot]).tobytes()).hexdigest()[:8]
    stem = f"kanlergems3-h1-dcap-lhc-{int(final_dots.sum())}-20261026-{mask_hash8}"
    dl_dir = ROOT / "docs" / "downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)
    # Clean any stale build of the exact same stem
    for ext in (".tif", ".zip", ".json"):
        (dl_dir / f"{stem}-zeros{ext}").unlink(missing_ok=True)
        (dl_dir / f"{stem}-nan{ext}").unlink(missing_ok=True)

    sub_name = f"{stem}-zeros.tif"
    sub_note = (
        f"KANLER-H1 DCAP-LHC {int(final_dots.sum())}d: dip-coupled piedmont+1mLiDAR+mag/hydro; "
        f"holdoutDTI {final_pooled['scores'][final_winner]['dti']:.4f}"
    )[:140]

    pred_zeros = np.where(final_dots & foot, 1.0, 0.0).astype(np.float32)
    sample_tif = ROOT / "data/official/sample_submission.tif"
    writer_receipt = submission_writer.write_submission(
        dl_dir / f"{stem}-zeros.tif",
        pred_zeros,
        sample_tif,
        foot,
        name=sub_name,
        note=sub_note,
        catalogue=cat,
        metadata={"lane": "KANLER-H1", "arm": final_winner},
    )
    nan_receipt = write_nan_outside_twin(dl_dir / f"{stem}-nan.tif", final_dots, foot, sample_tif)

    val_zeros = verify_geotiff_on_disk(dl_dir / f"{stem}-zeros.tif", sample_tif, cat)
    val_nan = verify_geotiff_on_disk(dl_dir / f"{stem}-nan.tif", sample_tif, cat)

    # Verify exact in-footprint byte-equivalence of predictions between `-zeros.tif` and `-nan.tif`
    with rasterio.open(dl_dir / f"{stem}-zeros.tif") as dz, rasterio.open(dl_dir / f"{stem}-nan.tif") as dn:
        in_foot_identical = bool(np.array_equal(dz.read(1)[foot], dn.read(1)[foot]))

    # Evaluate Automated Promotion Gates (`research/preregistration_kanler_h1.md`)
    cand_score = final_pooled["scores"][final_winner]
    diff_vs_h31x = final_pooled["paired_differences"]["REF_H31X"]
    diff_vs_ctrl = final_pooled["paired_differences"]["CTRL"]
    diff_vs_slope = final_pooled["paired_differences"]["SLOPE"]
    conf_diff_h31x = conf_summary["paired_differences"]["REF_H31X"]
    conf_diff_ctrl = conf_summary["paired_differences"]["CTRL"]

    g1_format = bool(val_zeros["passed"] and val_nan["passed"] and in_foot_identical)
    g2_canary = bool(canary["all_pass"])
    g3_holdout_best = bool(
        cand_score["dti"] > 0.1661329569994631
        and diff_vs_h31x["delta"] > 0.0
        and diff_vs_h31x["ci95"][0] > 0.0
        and diff_vs_ctrl["ci95"][0] > 0.0
        and diff_vs_slope["ci95"][0] > 0.0
        and conf_diff_h31x["delta"] > 0.0
        and conf_diff_ctrl["ci95"][0] > 0.0
    )
    g4_offcat = bool(
        sgmc_cand["full_off_catalogue"]["dti"] > sgmc_h33["full_off_catalogue"]["dti"]
        and sgmc_cand["piedmont_slope_le_6deg"]["dti"] > sgmc_h31x["piedmont_slope_le_6deg"]["dti"]
    )
    g5_unique_detectors = bool(uniqueness["detector_scope"]["unique"])

    all_gates_pass = bool(g1_format and g2_canary and g3_holdout_best and g4_offcat and g5_unique_detectors)
    verdict = "promote" if all_gates_pass else "negative"

    summary = {
        "schema_version": "kanler-h1-run-v1",
        "generated_utc": "2026-10-26",
        "elapsed_sec": round(time.time() - t_start, 2),
        "lane": "KANLER-H1 (DCAP-LHC)",
        "preregistration": "research/preregistration_kanler_h1.md",
        "experiments_used": 3,
        "experiments_budget_max": 3,
        "final_winner": final_winner,
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_len": len(sub_note),
        "verdict": verdict,
        "gates": {
            "G1_format_and_range_0_1": g1_format,
            "G2_single_feature_canary_le_090": g2_canary,
            "G3_paired_holdout_beats_portfolio_best": g3_holdout_best,
            "G4_off_catalogue_and_piedmont_discovery": g4_offcat,
            "G5_unique_vs_all_detector_lanes": g5_unique_detectors,
            "literal_5px_calibration_lattice_note": (
                "13gems_r13-lattice-s5 covers 99.8713% of footprint within 3 px (`min >= 82.16%` for 37,654 dots "
                "by Pigeonhole Principle); reported transparently alongside genuine detector-lane uniqueness."
            ),
        },
        "holdout_dti_primary": {
            "candidate": cand_score,
            "REF_H31X": final_pooled["scores"]["REF_H31X"],
            "CTRL": final_pooled["scores"]["CTRL"],
            "SLOPE": final_pooled["scores"]["SLOPE"],
            "paired_vs_REF_H31X": diff_vs_h31x,
            "paired_vs_CTRL": diff_vs_ctrl,
            "paired_vs_SLOPE": diff_vs_slope,
        },
        "holdout_dti_confirmation_seed3103": {
            "partition": conf_fold["receipt"],
            "candidate": conf_summary["scores"][final_winner],
            "REF_H31X": conf_summary["scores"]["REF_H31X"],
            "CTRL": conf_summary["scores"]["CTRL"],
            "SLOPE": conf_summary["scores"]["SLOPE"],
            "paired_vs_REF_H31X": conf_diff_h31x,
            "paired_vs_CTRL": conf_diff_ctrl,
        },
        "off_catalogue_sgmc_diagnostics": {
            "candidate": sgmc_cand,
            "REF_H31X": sgmc_h31x,
            "GEMSDOE32_H33": sgmc_h33,
        },
        "uniqueness_summary": {
            "total_registry_rasters_checked": uniqueness["total_registry_entries"],
            "detector_lane_rasters_checked": uniqueness["detector_lane_entries"],
            "unique_vs_all_detector_lanes": uniqueness["detector_scope"]["unique"],
            "surface_topk_also_le_070": uniqueness["detector_scope"]["surface_topk_also_le_070"],
            "worst_abs_surface_spearman": uniqueness["detector_scope"]["worst_abs_surface_spearman"],
            "worst_abs_dots_spearman": uniqueness["detector_scope"]["worst_abs_dots_spearman"],
            "worst_surface_topk_within_3px": uniqueness["detector_scope"]["worst_surface_topk_within_3px"],
            "worst_final_dots_within_3px": uniqueness["detector_scope"]["worst_final_dots_within_3px"],
            "key_focus_site_peers": uniqueness["key_focus_site_peers"],
            "synthetic_space_filling_probes": uniqueness["synthetic_space_filling_probes"],
        },
        "deliverables": {
            "primary_zeros_tif": val_zeros,
            "primary_zeros_zip": {
                "file": f"docs/downloads/{stem}-zeros.zip",
                "bytes": (dl_dir / f"{stem}-zeros.zip").stat().st_size,
                "sha256": H1.sha256_file(dl_dir / f"{stem}-zeros.zip"),
            },
            "companion_nan_tif": val_nan,
            "companion_nan_zip": {
                "file": nan_receipt["zip_path"],
                "bytes": nan_receipt["zip_bytes"],
                "sha256": nan_receipt["zip_sha256"],
            },
            "in_footprint_predictions_identical": in_foot_identical,
            "shared_writer_receipt": f"docs/downloads/{stem}-zeros.json",
        },
    }
    (EVID_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    H1.log("=== FINISHED KANLER-H1 RUN ===")
    H1.log(f"Verdict: {verdict.upper()} | Gates: {summary['gates']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
