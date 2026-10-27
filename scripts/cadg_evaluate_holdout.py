#!/usr/bin/env python3
"""Shared hide-and-recover evaluator and uniqueness screener for KANLERGEMSDOE3.

All Distance-Weighted Tversky Index (alpha=0.2, beta=0.8, 300 m triangular kernel),
10 km spatial-tile component attribution, pooled ratio computation, paired block
bootstrap confidence intervals, and two-polarity single-feature leakage canaries
delegate directly to the SHA-256-pinned ``vendor/gems24_template`` modules with
zero private numerical edits.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, label as ndi_label
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vendor.gems24_template.holdout import (  # noqa: E402,F401
    MTR_EVALUATOR_VERSION,
    SegmentHoldout,
    pooled_bootstrap,
    pooled_components,
    pooled_dti,
    spatial_bootstrap_ci,
    spatial_components,
)
from vendor.gems24_template.metric import (  # noqa: E402,F401
    ALPHA,
    BETA,
    EPS,
    RADIUS_PX,
    dti_components_exact,
    dti_score_fast,
    verify_organizer_worked_example,
)
from vendor.gems24_template.validator import sha256_file  # noqa: E402,F401


def make_diagonal_wedge_folds(footprint: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Orthogonal 45-degree rotated N/E/S/W wedges for independent confirmation."""
    footprint = np.asarray(footprint, bool)
    yy, xx = np.nonzero(footprint)
    yc, xc = float(np.median(yy)), float(np.median(xx))
    H, W = footprint.shape
    gy, gx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
    u = (gy - yc) + (gx - xc)
    v = (gy - yc) - (gx - xc)
    fold = np.full((H, W), -1, dtype=np.int8)
    fold[(u < 0) & (v < 0) & footprint] = 0
    fold[(u >= 0) & (v < 0) & footprint] = 1
    fold[(u >= 0) & (v >= 0) & footprint] = 2
    fold[(u < 0) & (v >= 0) & footprint] = 3
    return fold, ["Diag_N", "Diag_E", "Diag_S", "Diag_W"]


class DiagonalSegmentHoldout:
    """Orthogonal 45-degree rotated whole-component buffered confirmation holdout.

    Delegates 100% of metric, tile-attribution, pooling, and block-bootstrap calls
    directly to ``vendor.gems24_template.holdout`` with zero private metric fork.
    """

    def __init__(self, footprint: np.ndarray, labels: np.ndarray, *, buffer_px: int = 20):
        self.footprint = np.asarray(footprint, bool)
        self.labels = np.asarray(labels, bool)
        if (
            self.footprint.shape != self.labels.shape
            or self.footprint.ndim != 2
            or buffer_px < 3
            or np.any(self.labels & ~self.footprint)
            or not self.labels.any()
        ):
            raise ValueError("Aligned nonempty catalogue, footprint and >=3 px collar required")
        self.components, self.n_components = ndi_label(self.labels, structure=np.ones((3, 3), int))
        self.fold_grid, names = make_diagonal_wedge_folds(self.footprint)
        self.folds = []
        for f, name in enumerate(names):
            valid = self.footprint & (self.fold_grid == f)
            if not valid.any():
                raise ValueError(f"Empty diagonal fold: {name}")
            collar = distance_transform_edt(~valid) <= buffer_px
            hidden_ids = np.unique(self.components[collar & self.labels])
            hidden_ids = hidden_ids[hidden_ids > 0]
            hidden = self.labels & np.isin(self.components, hidden_ids)
            visible = self.labels & ~hidden
            truth = hidden & valid
            if not truth.any():
                raise ValueError(f"No withheld positives in diagonal fold: {name}")
            self.folds.append(
                {
                    "id": f,
                    "name": name,
                    "valid": valid,
                    "train": self.footprint & (distance_transform_edt(~(valid | hidden)) > buffer_px),
                    "visible": visible,
                    "truth": truth,
                    "hidden_component_ids": hidden_ids,
                }
            )
        self.buffer_px = buffer_px
        self.split_id = f"diagonal-wedge-buffered-{buffer_px}px-confirm-v1"

    def score_fold(self, prediction: np.ndarray, fold: dict[str, Any]):
        pred = np.asarray(prediction)
        if pred.shape != self.footprint.shape or not np.isin(pred, [0, 1]).all():
            raise ValueError("Finite aligned binary prediction required")
        blocks, reference = spatial_components(
            pred, fold["truth"], fold["valid"], fold["visible"], tile_px=100
        )
        return reference, blocks

    def summarize(self, predictions: list[np.ndarray], *, ci_draws: int = 1999) -> dict[str, Any]:
        if len(predictions) != len(self.folds):
            raise ValueError("One independent prediction per held-out fold required")
        rows, block_rows = [], []
        for pred, fold in zip(predictions, self.folds):
            result, blocks = self.score_fold(pred, fold)
            rows.append({"fold": fold["name"], **result})
            block_rows.append(blocks)
        blocks = np.sum(block_rows, axis=0)
        yy, xx = np.nonzero(self.footprint)
        nx = (self.footprint.shape[1] + 99) // 100
        active_blocks = np.unique((yy // 100) * nx + xx // 100)
        total = pooled_components(rows)
        return {
            "label": "HOLDOUT-DTI",
            "evaluator_version": MTR_EVALUATOR_VERSION,
            "split_id": self.split_id,
            **total,
            "n_withheld_positive_pixels": int(total["n_truth"]),
            "n_unique_withheld_components": self.n_components,
            "ci95": spatial_bootstrap_ci(blocks[active_blocks], draws=ci_draws),
            "folds": rows,
        }

    def compare_paired(
        self,
        candidate_predictions: list[np.ndarray],
        baseline_predictions: list[np.ndarray],
        *,
        ci_draws: int = 1999,
        seed: int = 20261026,
    ) -> dict[str, Any]:
        if len(candidate_predictions) != len(self.folds) or len(baseline_predictions) != len(self.folds):
            raise ValueError("One independent prediction per held-out fold required for both series")
        cand_rows, cand_blocks = [], []
        base_rows, base_blocks = [], []
        fold_deltas = []
        for c_pred, b_pred, fold in zip(candidate_predictions, baseline_predictions, self.folds):
            c_res, c_blk = self.score_fold(c_pred, fold)
            b_res, b_blk = self.score_fold(b_pred, fold)
            cand_rows.append({"fold": fold["name"], **c_res})
            base_rows.append({"fold": fold["name"], **b_res})
            cand_blocks.append(c_blk)
            base_blocks.append(b_blk)
            fold_deltas.append(
                {
                    "fold": fold["name"],
                    "candidate_dti": float(c_res["dti"]),
                    "baseline_dti": float(b_res["dti"]),
                    "delta_dti": float(c_res["dti"] - b_res["dti"]),
                    "candidate_wins": bool(c_res["dti"] > b_res["dti"]),
                }
            )
        c_sum = np.sum(cand_blocks, axis=0)
        b_sum = np.sum(base_blocks, axis=0)
        yy, xx = np.nonzero(self.footprint)
        nx = (self.footprint.shape[1] + 99) // 100
        active = np.unique((yy // 100) * nx + xx // 100)
        c_tot = pooled_components(cand_rows)
        b_tot = pooled_components(base_rows)
        delta_ci = pooled_bootstrap(c_sum[active], paired=b_sum[active], resamples=ci_draws, seed=seed)
        wins = int(sum(1 for d in fold_deltas if d["candidate_wins"]))
        return {
            "evaluator_version": MTR_EVALUATOR_VERSION,
            "split_id": self.split_id,
            "candidate_dti": float(c_tot["dti"]),
            "baseline_dti": float(b_tot["dti"]),
            "paired_delta_dti": float(c_tot["dti"] - b_tot["dti"]),
            "paired_delta_ci95": delta_ci,
            "ci95_strictly_positive": bool(delta_ci[0] > 0.0),
            "fold_wins": wins,
            "n_folds": len(self.folds),
            "min_fold_delta": float(min(d["delta_dti"] for d in fold_deltas)),
            "folds": fold_deltas,
        }


def audit_uniqueness_against_registry(
    surface_2d: np.ndarray,
    preview_dots_2d: np.ndarray,
    final_dots_2d: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    registry_entries: list[dict[str, Any]],
    *,
    rho_limit: float = 0.90,
    overlap_limit: float = 0.70,
    subsample_step: int = 5,
) -> dict[str, Any]:
    """Screen both pre-placement surface and final emitted raster against registry.

    Evaluates:
    - Spearman |rho| over scored off-catalogue footprint cells (subsampled every
      ``subsample_step`` cells deterministically for speed, >1.02M cells), and
    - Exact 3-pixel (300 m) Euclidean fraction of candidate dots within 3 px of
      every registry raster's positive dots.

    Genuine detector rasters (``is_calibration_probe=False``) enforce both
    ``|rho| <= 0.90`` and ``overlap_3px <= 0.70``. Synthetic grid-covering
    calibration probes (such as ``r13-lattice-s5``, a 5x5 uniform lattice with
    206,895 dots and Voronoi covering radius 2*sqrt(2)=2.828 <= 3.0 px, IR-42-UNIQ-01)
    still enforce ``|rho| <= 0.90`` and report exact 3-px proximity transparently
    under ``calibration_probes``.
    """
    active = np.asarray(footprint, bool) & ~np.asarray(catalogue, bool)
    active_idx = np.flatnonzero(active)[::subsample_step]
    s_vec = np.asarray(surface_2d, dtype=np.float32).ravel()[active_idx]
    f_vec = np.asarray(final_dots_2d, dtype=np.float32).ravel()[active_idx]
    prev_mask = np.asarray(preview_dots_2d, bool) & active
    fin_mask = np.asarray(final_dots_2d, bool) & active
    n_prev = int(prev_mask.sum())
    n_fin = int(fin_mask.sum())
    if n_prev == 0 or n_fin == 0:
        raise ValueError("Empty preview or final dot mask cannot be uniqueness-screened")

    detector_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []

    for entry in registry_entries:
        path = Path(entry["resolved_path"])
        actual_sha = sha256_file(path)
        if entry.get("sha256") and actual_sha != entry["sha256"]:
            raise ValueError(f"Registry SHA-256 mismatch for {entry['id']}: {actual_sha} != {entry['sha256']}")
        with rasterio.open(path) as src:
            ref_arr = src.read(1, masked=False)
        ref_clean = np.where(np.isfinite(ref_arr) & active, ref_arr, 0.0).astype(np.float32)
        ref_vec = ref_clean.ravel()[active_idx]
        ref_pos = (ref_clean > 0.0) & active

        s_rho = 0.0 if np.std(ref_vec) == 0.0 else float(spearmanr(s_vec, ref_vec).statistic)
        f_rho = 0.0 if np.std(ref_vec) == 0.0 else float(spearmanr(f_vec, ref_vec).statistic)
        if not np.isfinite(s_rho):
            s_rho = 0.0
        if not np.isfinite(f_rho):
            f_rho = 0.0

        if ref_pos.any():
            dt_ref = distance_transform_edt(~ref_pos)
            prev_ov3 = float((dt_ref[prev_mask] <= 3.0).mean())
            fin_ov3 = float((dt_ref[fin_mask] <= 3.0).mean())
        else:
            prev_ov3 = 0.0
            fin_ov3 = 0.0

        row = {
            "id": entry["id"],
            "site": entry.get("site", ""),
            "file": path.name,
            "sha256": actual_sha,
            "positive_pixels_off_catalogue": int(ref_pos.sum()),
            "reported_dti": entry.get("reported_dti"),
            "is_calibration_probe": bool(entry.get("is_calibration_probe", False)),
            "surface_spearman_rho": round(s_rho, 6),
            "surface_abs_spearman_rho": round(abs(s_rho), 6),
            "surface_preview_3px_overlap": round(prev_ov3, 6),
            "final_spearman_rho": round(f_rho, 6),
            "final_abs_spearman_rho": round(abs(f_rho), 6),
            "final_3px_overlap": round(fin_ov3, 6),
        }
        if row["is_calibration_probe"]:
            probe_rows.append(row)
        else:
            detector_rows.append(row)

    if not detector_rows:
        raise ValueError("Registry must contain at least one genuine detector raster")

    all_rows = detector_rows + probe_rows
    # Literal un-weakened metrics across ALL registry rasters (including uniform lattice probes)
    lit_surf_rho = max(r["surface_abs_spearman_rho"] for r in all_rows)
    lit_surf_ov3 = max(r["surface_preview_3px_overlap"] for r in all_rows)
    lit_fin_rho = max(r["final_abs_spearman_rho"] for r in all_rows)
    lit_fin_ov3 = max(r["final_3px_overlap"] for r in all_rows)
    lit_surf_pass = (lit_surf_rho <= rho_limit) and (lit_surf_ov3 <= overlap_limit)
    lit_fin_pass = (lit_fin_rho <= rho_limit) and (lit_fin_ov3 <= overlap_limit)

    # Genuine geological fault-detector metrics (excluding synthetic uniform grid calibration probes)
    det_surf_rho = max(r["surface_abs_spearman_rho"] for r in detector_rows)
    det_surf_ov3 = max(r["surface_preview_3px_overlap"] for r in detector_rows)
    det_fin_rho = max(r["final_abs_spearman_rho"] for r in detector_rows)
    det_fin_ov3 = max(r["final_3px_overlap"] for r in detector_rows)
    det_surf_pass = (det_surf_rho <= rho_limit) and (det_surf_ov3 <= overlap_limit)
    det_fin_pass = (det_fin_rho <= rho_limit) and (det_fin_ov3 <= overlap_limit)

    nearest_lit_surf = max(all_rows, key=lambda r: max(r["surface_abs_spearman_rho"] / rho_limit, r["surface_preview_3px_overlap"] / overlap_limit))
    nearest_lit_fin = max(all_rows, key=lambda r: max(r["final_abs_spearman_rho"] / rho_limit, r["final_3px_overlap"] / overlap_limit))
    nearest_det_surf = max(detector_rows, key=lambda r: max(r["surface_abs_spearman_rho"] / rho_limit, r["surface_preview_3px_overlap"] / overlap_limit))
    nearest_det_fin = max(detector_rows, key=lambda r: max(r["final_abs_spearman_rho"] / rho_limit, r["final_3px_overlap"] / overlap_limit))

    # Exact pigeonhole lower bound induced by any calibration lattice probes at candidate dot count
    pigeonhole_bounds: list[dict[str, Any]] = []
    fp_bool = np.asarray(footprint, bool)
    n_fp_total = int(fp_bool.sum())
    for pr in probe_rows:
        probe_entry = next(e for e in registry_entries if e["id"] == pr["id"])
        with rasterio.open(probe_entry["resolved_path"]) as src:
            pa = src.read(1, masked=False)
        p_dots = np.isfinite(pa) & (pa > 0.0) & fp_bool
        dt_p = distance_transform_edt(~p_dots)
        covered_fp = int((dt_p[fp_bool] <= 3.0).sum())
        uncovered_fp = n_fp_total - covered_fp
        lb = max(0.0, 1.0 - float(uncovered_fp) / float(n_fin))
        pigeonhole_bounds.append(
            {
                "id": pr["id"],
                "probe_in_footprint_dots": int(p_dots.sum()),
                "footprint_cells_total": n_fp_total,
                "footprint_cells_within_3px": covered_fp,
                "footprint_cells_uncovered": uncovered_fp,
                "footprint_3px_saturation_fraction": round(covered_fp / n_fp_total, 6),
                "candidate_budget_dots": n_fin,
                "mathematical_min_possible_3px_overlap": round(lb, 6),
            }
        )

    return {
        "passed": bool(lit_surf_pass and lit_fin_pass),
        "genuine_detectors_passed": bool(det_surf_pass and det_fin_pass),
        "thresholds": {"max_abs_spearman_rho": rho_limit, "max_3px_overlap": overlap_limit},
        "total_registry_rasters_checked": len(all_rows),
        "genuine_detector_rasters_checked": len(detector_rows),
        "calibration_probes_checked": len(probe_rows),
        "surface": {
            "passed": bool(lit_surf_pass),
            "max_abs_spearman_rho": lit_surf_rho,
            "max_preview_fraction_within_3px": lit_surf_ov3,
            "nearest_raster": nearest_lit_surf,
            "genuine_detectors_passed": bool(det_surf_pass),
            "genuine_detectors_max_abs_spearman_rho": det_surf_rho,
            "genuine_detectors_max_preview_fraction_within_3px": det_surf_ov3,
            "nearest_genuine_detector": nearest_det_surf,
        },
        "final_dots": {
            "passed": bool(lit_fin_pass),
            "max_abs_spearman_rho": lit_fin_rho,
            "max_candidate_fraction_within_3px": lit_fin_ov3,
            "nearest_raster": nearest_lit_fin,
            "genuine_detectors_passed": bool(det_fin_pass),
            "genuine_detectors_max_abs_spearman_rho": det_fin_rho,
            "genuine_detectors_max_candidate_fraction_within_3px": det_fin_ov3,
            "nearest_genuine_detector": nearest_det_fin,
        },
        "pigeonhole_lattice_bounds": pigeonhole_bounds,
        "detector_comparisons": detector_rows,
        "calibration_probes": probe_rows,
        "irregularity_note": (
            "IR-42-UNIQ-01: 13GEMSDOE calibration probe r13-lattice-s5 places 206,895 dots on a "
            "uniform spacing-5 grid covering 5,160,724 / 5,167,373 footprint cells (99.8713%) within "
            "3 px, leaving only 6,649 boundary-sliver cells uncovered and forcing forward 3-px overlap "
            ">= 1 - 6,649/37,654 = 0.823418 > 0.70 for ANY 37,654-dot in-footprint candidate. Per "
            "research/review.md ('report that conflict rather than weakening the gate'), top-level "
            "passed/surface/final_dots enforce the un-weakened literal 36-raster gate while "
            "genuine_detectors_* reports exact uniqueness across all 35 real geological fault detectors."
        ),
    }


if __name__ == "__main__":
    print(json.dumps({"evaluator_version": MTR_EVALUATOR_VERSION, "worked_example": verify_organizer_worked_example()}, indent=2))
