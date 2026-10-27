"""Fold-proper multi-physics, decontamination, and continuation learners for L-K3-CADG-SUBMOD."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.ndimage import distance_transform_edt, label as ndi_label
from scipy.special import expit, logit
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from .features import compute_visible_continuation


@dataclass
class DualExpertBundle:
    full_model: HistGradientBoostingClassifier
    void_model: HistGradientBoostingClassifier
    full_cols: list[int]
    void_cols: list[int]
    has_lidar_col: int
    piedmont_col: int
    prior_ratio: float
    meta_combiner: LogisticRegression | None
    report: dict[str, Any]


def _make_hgb(*, max_iter: int = 200, seed: int = 42) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=max_iter,
        learning_rate=0.06,
        max_leaf_nodes=63,
        min_samples_leaf=180,
        l2_regularization=1.5,
        max_bins=255,
        early_stopping=False,
        random_state=seed,
    )


def _prior_calibrate(prob_raw: np.ndarray, prior_ratio: float, sharpness: float = 1.28) -> np.ndarray:
    """Convert negative-subsampled tree probabilities to sharp spatial posterior scores."""
    eps = 1e-6
    p = np.clip(np.asarray(prob_raw, dtype=np.float64), eps, 1.0 - eps)
    lo = (np.log(p) - np.log1p(-p)) * sharpness + np.log(max(prior_ratio, 1e-6))
    return expit(lo).astype(np.float32)


def _sample_negatives(
    mm: np.memmap,
    col_map: dict[str, int],
    neg_pool_fp_pos: np.ndarray,
    n_neg_target: int,
    *,
    hard_decontam: bool,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample off-fault negatives (optionally oversampling road & shoreline mimics with importance weights)."""
    rng = np.random.default_rng(seed)
    n_pool = len(neg_pool_fp_pos)
    if n_pool <= n_neg_target:
        return neg_pool_fp_pos, np.ones(n_pool, dtype=np.float32)

    if not hard_decontam:
        chosen = rng.choice(neg_pool_fp_pos, size=n_neg_target, replace=False)
        return np.sort(chosen), np.ones(n_neg_target, dtype=np.float32)

    # Identify off-fault cultural roads (<150 m -> log1p < 5.02) and pluvial benches (<22 m)
    road_v = mm[neg_pool_fp_pos, col_map["tiger_road_logdist"]]
    shore_v = mm[neg_pool_fp_pos, col_map["pluvial_shoreline_elev_dist_m"]]
    is_mimic = (road_v < np.log1p(150.0)) | (shore_v < 22.0)

    mimic_pool = neg_pool_fp_pos[is_mimic]
    bg_pool = neg_pool_fp_pos[~is_mimic]
    true_mimic_frac = max(float(len(mimic_pool)) / float(n_pool), 1e-4)
    sample_mimic_frac = min(max(true_mimic_frac * 2.0, 0.22), 0.38)

    n_mim = min(len(mimic_pool), int(round(n_neg_target * sample_mimic_frac)))
    n_bg = min(len(bg_pool), n_neg_target - n_mim)
    sel_mim = rng.choice(mimic_pool, size=n_mim, replace=False) if n_mim > 0 else np.zeros(0, dtype=np.int64)
    sel_bg = rng.choice(bg_pool, size=n_bg, replace=False) if n_bg > 0 else np.zeros(0, dtype=np.int64)

    # Importance weights preserve true marginal negative distribution while increasing split resolution on mimics
    actual_mim_frac = float(len(sel_mim)) / max(len(sel_mim) + len(sel_bg), 1)
    w_mim = float(np.clip(true_mimic_frac / max(actual_mim_frac, 1e-4), 0.35, 1.5))
    w_bg = float(np.clip((1.0 - true_mimic_frac) / max(1.0 - actual_mim_frac, 1e-4), 0.5, 1.5))

    sel = np.concatenate([sel_mim, sel_bg])
    w = np.concatenate(
        [
            np.full(len(sel_mim), w_mim, dtype=np.float32),
            np.full(len(sel_bg), w_bg, dtype=np.float32),
        ]
    )
    order = np.argsort(sel)
    return sel[order], w[order]


def fit_baseline_regional_19band(
    mm: np.memmap,
    meta: dict[str, Any],
    footprint: np.ndarray,
    train_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    seed: int,
) -> tuple[HistGradientBoostingClassifier, list[int], float]:
    """Matched 19-band regional HGB baseline (zero external layers, greedy 2.8 px spacing)."""
    names = meta["feature_names"]
    cols_19 = list(range(19))
    assert names[0] == "mag_anom" and names[18] == "det_elev_slope"

    d_vis = distance_transform_edt(~visible_2d)
    train_fp = train_2d.ravel()[np.flatnonzero(footprint.ravel())]
    vis_fp = visible_2d.ravel()[np.flatnonzero(footprint.ravel())]
    d_vis_fp = d_vis.ravel()[np.flatnonzero(footprint.ravel())]

    pos_idx = np.flatnonzero(train_fp & vis_fp)
    neg_pool = np.flatnonzero(train_fp & (d_vis_fp >= 5.0))
    n_neg = min(len(neg_pool), len(pos_idx) * 6)
    rng = np.random.default_rng(seed)
    neg_idx = np.sort(rng.choice(neg_pool, size=n_neg, replace=False))

    idx_all = np.concatenate([pos_idx, neg_idx])
    X = np.asarray(mm[idx_all][:, cols_19], dtype=np.float32)
    y = np.concatenate([np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_idx), dtype=np.int8)])

    clf = _make_hgb(max_iter=180, seed=seed)
    clf.fit(X, y)
    true_prior = float(len(pos_idx)) / max(int(train_fp.sum()), 1)
    sample_ratio = float(len(pos_idx)) / max(len(neg_idx), 1)
    prior_ratio = true_prior / max((1.0 - true_prior) * sample_ratio, 1e-6)
    return clf, cols_19, prior_ratio


def predict_baseline_regional_19band(
    clf: HistGradientBoostingClassifier,
    cols_19: list[int],
    prior_ratio: float,
    mm: np.memmap,
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    domain_2d: np.ndarray,
) -> np.ndarray:
    dom_fp = np.flatnonzero(domain_2d.ravel()[fp_idx])
    out = np.zeros(footprint.shape, dtype=np.float32)
    if len(dom_fp) == 0:
        return out
    probs = np.empty(len(dom_fp), dtype=np.float32)
    chunk = 250_000
    for s in range(0, len(dom_fp), chunk):
        sl = dom_fp[s : s + chunk]
        X_sub = np.asarray(mm[sl][:, cols_19], dtype=np.float32)
        probs[s : s + chunk] = _prior_calibrate(clf.predict_proba(X_sub)[:, 1], prior_ratio, sharpness=1.20)
    out.ravel()[fp_idx[dom_fp]] = probs
    return out


def _select_columns_for_experiment(meta: dict[str, Any], exp_id: str) -> tuple[list[int], list[int]]:
    names = meta["feature_names"]
    col_map = {n: i for i, n in enumerate(names)}
    gb = meta["groups"]["group_b"]
    ga = meta["groups"]["group_a"]
    gc = meta["groups"]["group_c"]

    if exp_id == "Exp-K3-1":
        chosen_names = gb + ga
    elif exp_id in ("Exp-K3-2", "Exp-K3-3"):
        chosen_names = gb + ga + gc
    else:
        raise ValueError(f"Unknown experiment id: {exp_id}")

    full_cols = [col_map[n] for n in chosen_names]
    void_cols = [
        col_map[n]
        for n in chosen_names
        if not n.startswith("lidar_") and n != "has_lidar"
    ]
    return full_cols, void_cols


def _predict_dual_raw(
    full_model: HistGradientBoostingClassifier,
    void_model: HistGradientBoostingClassifier,
    full_cols: list[int],
    void_cols: list[int],
    has_lidar_col: int,
    prior_ratio: float,
    mm: np.memmap,
    rows_fp: np.ndarray,
) -> np.ndarray:
    """Predict fused dual-expert posterior score on selected footprint row indices."""
    out = np.empty(len(rows_fp), dtype=np.float32)
    chunk = 250_000
    for s in range(0, len(rows_fp), chunk):
        sl = rows_fp[s : s + chunk]
        X_full = np.asarray(mm[sl][:, full_cols], dtype=np.float32)
        X_void = np.asarray(mm[sl][:, void_cols], dtype=np.float32)
        has_lid = mm[sl, has_lidar_col] > 0.5
        p_full = _prior_calibrate(full_model.predict_proba(X_full)[:, 1], prior_ratio, sharpness=1.28)
        p_void = _prior_calibrate(void_model.predict_proba(X_void)[:, 1], prior_ratio, sharpness=1.28)
        out[s : s + chunk] = np.where(
            has_lid,
            0.70 * p_full + 0.30 * p_void,
            0.22 * p_full + 0.78 * p_void,
        ).astype(np.float32)
    return out


def fit_lane_experiment(
    exp_id: str,
    mm: np.memmap,
    meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    train_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    seed: int,
) -> DualExpertBundle:
    """Fit Exp-K3-1, Exp-K3-2, or Exp-K3-3 strictly on fold['train'] & fold['visible']."""
    names = meta["feature_names"]
    col_map = {n: i for i, n in enumerate(names)}
    full_cols, void_cols = _select_columns_for_experiment(meta, exp_id)
    has_lidar_col = col_map["has_lidar"]
    piedmont_col = col_map["piedmont_margin_score"]
    depth_col = col_map["depth_to_base_surf"]
    relief_col = col_map["topo10_relief_local"]

    d_vis = distance_transform_edt(~visible_2d)
    train_fp = train_2d.ravel()[fp_idx]
    vis_fp = visible_2d.ravel()[fp_idx]
    d_vis_fp = d_vis.ravel()[fp_idx]

    pos_idx = np.flatnonzero(train_fp & vis_fp)
    neg_pool = np.flatnonzero(train_fp & (d_vis_fp >= 5.0))
    n_neg = min(len(neg_pool), len(pos_idx) * 6)
    use_decontam = exp_id in ("Exp-K3-2", "Exp-K3-3")
    neg_idx, neg_w = _sample_negatives(
        mm, col_map, neg_pool, n_neg, hard_decontam=use_decontam, seed=seed
    )

    pos_w_full = np.ones(len(pos_idx), dtype=np.float32)
    pos_w_void = np.ones(len(pos_idx), dtype=np.float32)
    # Void/subsurface specialist always slightly emphasizes basin-hosted positives
    pos_depth = mm[pos_idx, depth_col]
    pos_rel = mm[pos_idx, relief_col]
    is_piedmont_pos = (pos_depth >= 200.0) | (pos_rel < 95.0)
    pos_w_void[is_piedmont_pos] = 1.35
    if exp_id == "Exp-K3-3":
        # Piedmont/basin-margin habitat calibration (63.9% of Quaternary faults are basin-hosted)
        pos_w_full[is_piedmont_pos] = 1.45
        pos_w_void[is_piedmont_pos] = 1.65

    idx_all = np.concatenate([pos_idx, neg_idx])
    y_all = np.concatenate([np.ones(len(pos_idx), dtype=np.int8), np.zeros(len(neg_idx), dtype=np.int8)])
    w_full = np.concatenate([pos_w_full, neg_w])
    w_void = np.concatenate([pos_w_void, neg_w])

    X_full = np.asarray(mm[idx_all][:, full_cols], dtype=np.float32)
    X_void = np.asarray(mm[idx_all][:, void_cols], dtype=np.float32)

    m_full = _make_hgb(max_iter=190, seed=seed + 11)
    m_void = _make_hgb(max_iter=190, seed=seed + 23)
    m_full.fit(X_full, y_all, sample_weight=w_full)
    m_void.fit(X_void, y_all, sample_weight=w_void)

    true_prior = float(len(pos_idx)) / max(int(train_fp.sum()), 1)
    sample_ratio = float(len(pos_idx)) / max(len(neg_idx), 1)
    prior_ratio = true_prior / max((1.0 - true_prior) * sample_ratio, 1e-6)

    meta_combiner: LogisticRegression | None = None
    meta_report: dict[str, Any] = {}

    if exp_id == "Exp-K3-3":
        # Leave-Component-Out internal calibration inside fold['train'] & fold['visible']
        # Withhold 25% of training fault components so Stage-2 continuation never sees d_visible==0!
        train_vis_2d = train_2d & visible_2d
        comp, n_comp = ndi_label(train_vis_2d, structure=np.ones((3, 3), dtype=int))
        rng = np.random.default_rng(seed + 99)
        comp_ids = np.arange(1, n_comp + 1)
        rng.shuffle(comp_ids)
        val_comp_ids = comp_ids[: max(1, len(comp_ids) // 4)]
        val_hidden_2d = np.isin(comp, val_comp_ids)
        vis_sub_2d = visible_2d & ~val_hidden_2d

        # Train lightweight out-of-component Stage-1 proxy on the remaining 75% training components
        sub_pos = np.flatnonzero((train_vis_2d & ~val_hidden_2d).ravel()[fp_idx])
        sub_neg_pool = np.flatnonzero((train_2d & (distance_transform_edt(~vis_sub_2d) >= 6.0) & ~val_hidden_2d).ravel()[fp_idx])
        sub_n_neg = min(len(sub_neg_pool), len(sub_pos) * 5)
        sub_neg = np.sort(rng.choice(sub_neg_pool, size=sub_n_neg, replace=False))
        sub_idx = np.concatenate([sub_pos, sub_neg])
        sub_y = np.concatenate([np.ones(len(sub_pos), dtype=np.int8), np.zeros(len(sub_neg), dtype=np.int8)])

        sub_m_full = _make_hgb(max_iter=130, seed=seed + 101)
        sub_m_void = _make_hgb(max_iter=130, seed=seed + 103)
        sub_m_full.fit(np.asarray(mm[sub_idx][:, full_cols], dtype=np.float32), sub_y)
        sub_m_void.fit(np.asarray(mm[sub_idx][:, void_cols], dtype=np.float32), sub_y)

        # Evaluate on withheld internal components (val_hidden_2d) vs clean off-fault negatives
        cal_pos_fp = np.flatnonzero(val_hidden_2d.ravel()[fp_idx])
        cal_neg_pool = np.flatnonzero(
            (train_2d & ~visible_2d & (distance_transform_edt(~visible_2d) >= 6.0)).ravel()[fp_idx]
        )
        cal_neg_fp = np.sort(
            rng.choice(cal_neg_pool, size=min(len(cal_neg_pool), len(cal_pos_fp) * 8), replace=False)
        )
        cal_rows = np.concatenate([cal_pos_fp, cal_neg_fp])
        cal_y = np.concatenate([np.ones(len(cal_pos_fp), dtype=np.int8), np.zeros(len(cal_neg_fp), dtype=np.int8)])

        p_phys_cal = _predict_dual_raw(
            sub_m_full, sub_m_void, full_cols, void_cols, has_lidar_col, prior_ratio, mm, cal_rows
        )
        cont_sub = compute_visible_continuation(vis_sub_2d, footprint)
        cal_grid_idx = fp_idx[cal_rows]
        Z_cal = np.column_stack(
            [
                logit(np.clip(p_phys_cal, 1e-6, 1.0 - 1e-6)),
                cont_sub["vis_relay_band_300_3500m"].ravel()[cal_grid_idx],
                np.log1p(cont_sub["vis_tip_propagation_lobe"].ravel()[cal_grid_idx] * 25.0),
                np.log1p(cont_sub["vis_belt_density_2p5km"].ravel()[cal_grid_idx] * 80.0),
                mm[cal_rows, piedmont_col],
            ]
        ).astype(np.float64)

        lr = LogisticRegression(C=0.5, max_iter=300, random_state=seed + 107)
        lr.fit(Z_cal, cal_y)
        # Enforce physically non-negative weight on geophysical log-odds and continuation lobes
        coef = lr.coef_.copy()
        coef[0, 0] = max(float(coef[0, 0]), 0.65)
        coef[0, 1] = np.clip(float(coef[0, 1]), 0.0, 1.2)
        coef[0, 2] = np.clip(float(coef[0, 2]), 0.0, 1.2)
        coef[0, 3] = np.clip(float(coef[0, 3]), 0.0, 1.0)
        lr.coef_ = coef
        meta_combiner = lr
        meta_report = {
            "internal_withheld_components": int(len(val_comp_ids)),
            "internal_withheld_pixels": int(len(cal_pos_fp)),
            "combiner_weights": {
                "logit_phys": round(float(coef[0, 0]), 4),
                "vis_relay_band": round(float(coef[0, 1]), 4),
                "vis_tip_lobe": round(float(coef[0, 2]), 4),
                "vis_belt_density": round(float(coef[0, 3]), 4),
                "piedmont_margin": round(float(coef[0, 4]), 4),
            },
        }

    return DualExpertBundle(
        full_model=m_full,
        void_model=m_void,
        full_cols=full_cols,
        void_cols=void_cols,
        has_lidar_col=has_lidar_col,
        piedmont_col=piedmont_col,
        prior_ratio=prior_ratio,
        meta_combiner=meta_combiner,
        report={
            "exp_id": exp_id,
            "n_pos_train": int(len(pos_idx)),
            "n_neg_train": int(len(neg_idx)),
            "n_full_features": len(full_cols),
            "n_void_features": len(void_cols),
            "prior_ratio": round(prior_ratio, 6),
            **meta_report,
        },
    )


def predict_lane_surface(
    bundle: DualExpertBundle,
    mm: np.memmap,
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    domain_2d: np.ndarray,
    visible_2d: np.ndarray,
) -> np.ndarray:
    """Predict calibrated fault surface over ``domain_2d`` using ``visible_2d`` only."""
    dom_rows = np.flatnonzero(domain_2d.ravel()[fp_idx])
    out = np.zeros(footprint.shape, dtype=np.float32)
    if len(dom_rows) == 0:
        return out

    p_phys = _predict_dual_raw(
        bundle.full_model,
        bundle.void_model,
        bundle.full_cols,
        bundle.void_cols,
        bundle.has_lidar_col,
        bundle.prior_ratio,
        mm,
        dom_rows,
    )

    if bundle.meta_combiner is not None:
        cont = compute_visible_continuation(visible_2d, footprint)
        grid_idx = fp_idx[dom_rows]
        Z = np.column_stack(
            [
                logit(np.clip(p_phys, 1e-6, 1.0 - 1e-6)),
                cont["vis_relay_band_300_3500m"].ravel()[grid_idx],
                np.log1p(cont["vis_tip_propagation_lobe"].ravel()[grid_idx] * 25.0),
                np.log1p(cont["vis_belt_density_2p5km"].ravel()[grid_idx] * 80.0),
                mm[dom_rows, bundle.piedmont_col],
            ]
        ).astype(np.float64)
        # Calibrate combined log-odds back to spatial prior scale
        comb_prob = bundle.meta_combiner.predict_proba(Z)[:, 1]
        # Shift by ratio of true prior to internal calibration 1:8 sample ratio
        cal_prior_ratio = 0.012 / (0.988 * (1.0 / 8.0))
        final_p = _prior_calibrate(comb_prob, cal_prior_ratio, sharpness=1.22)
    else:
        final_p = p_phys

    out.ravel()[fp_idx[dom_rows]] = final_p
    return out
