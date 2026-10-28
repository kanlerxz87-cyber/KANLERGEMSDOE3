"""Fast (<65s/fold on 2 cores, <450 MB RSS) two-stage nested spatial-OOF corridor & dip-offset learners."""
from __future__ import annotations

import gc
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter, label as ndi_label
from scipy.special import expit
from sklearn.ensemble import HistGradientBoostingClassifier

from src.kanlergems3.submodular import celf_submodular_emit_300m
from vendor.gems24_template.metric import ridge_nms

from .features import (
    ATSC_GROUP_D_NAMES,
    ATSC_GROUP_E_NAMES,
    compute_stage2_corridor_features,
    compute_visible_tip_bridge_features,
)


@dataclass
class Stage1DualBundle:
    lidar_model: HistGradientBoostingClassifier
    void_model: HistGradientBoostingClassifier
    base_lidar_cols: list[int]
    extra_lidar_cols: list[int]
    base_void_cols: list[int]
    extra_void_cols: list[int]
    has_lidar_base_col: int
    lidar_prior_ratio: float
    void_prior_ratio: float


@dataclass
class ATSCExperimentBundle:
    exp_id: str
    stage1: Stage1DualBundle
    stage2_lidar_model: HistGradientBoostingClassifier | None
    stage2_void_model: HistGradientBoostingClassifier | None
    stage2_lidar_prior_ratio: float
    stage2_void_prior_ratio: float
    use_tip_features: bool
    report: dict[str, Any]


def _make_hgb(
    *,
    max_iter: int = 75,
    max_leaf_nodes: int = 31,
    min_samples_leaf: int = 180,
    l2_regularization: float = 2.0,
    seed: int = 42,
) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=max_iter,
        learning_rate=0.09,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf,
        l2_regularization=l2_regularization,
        max_bins=255,
        early_stopping=False,
        random_state=seed,
    )


def _prior_calibrate(prob_raw: np.ndarray, prior_ratio: float, sharpness: float = 1.15) -> np.ndarray:
    eps = 1e-6
    p = np.clip(np.asarray(prob_raw, dtype=np.float64), eps, 1.0 - eps)
    lo = (np.log(p) - np.log1p(-p)) * sharpness + np.log(max(prior_ratio, 1e-6))
    return expit(lo).astype(np.float32)


def _select_stage1_cols(
    base_meta: dict[str, Any],
    extra_meta: dict[str, Any],
    exp_id: str,
) -> tuple[list[int], list[int], list[int], list[int]]:
    bnames = base_meta["feature_names"]
    enames = extra_meta["extra_feature_names"]
    bmap = {n: i for i, n in enumerate(bnames)}
    emap = {n: i for i, n in enumerate(enames)}

    # Select strictly the 77 label-free columns in base_meta (exclude any vis_* if present)
    chosen_base = [n for n in bnames if not n.startswith("vis_")]
    if exp_id == "Exp-ATSC-1":
        chosen_extra = list(ATSC_GROUP_D_NAMES)
    elif exp_id in ("Exp-ATSC-2", "Exp-ATSC-3"):
        chosen_extra = list(ATSC_GROUP_D_NAMES) + list(ATSC_GROUP_E_NAMES)
    else:
        raise ValueError(f"Unknown ATSC experiment: {exp_id}")

    base_lidar_cols = [bmap[n] for n in chosen_base]
    extra_lidar_cols = [emap[n] for n in chosen_extra]
    base_void_cols = [
        bmap[n] for n in chosen_base if not n.startswith("lidar_") and n != "has_lidar"
    ]
    extra_void_cols = [emap[n] for n in chosen_extra if n != "rail_road_corridor_veto"]
    return base_lidar_cols, extra_lidar_cols, base_void_cols, extra_void_cols


def _assemble_rows(
    base_mm: np.memmap,
    extra_mm: np.memmap,
    rows_fp: np.ndarray,
    base_cols: list[int],
    extra_cols: list[int],
) -> np.ndarray:
    """Fast C-level row+col gather in 250k chunks to prevent cache-thrashing strided loops."""
    n = len(rows_fp)
    b_arr = np.asarray(base_cols, dtype=np.intp)
    e_arr = np.asarray(extra_cols, dtype=np.intp)
    nb, ne = len(b_arr), len(e_arr)
    X = np.empty((n, nb + ne), dtype=np.float32)
    step = 250_000
    for s in range(0, n, step):
        e = min(n, s + step)
        r_chunk = rows_fp[s:e]
        X[s:e, :nb] = np.asarray(base_mm[r_chunk], dtype=np.float32)[:, b_arr]
        if ne > 0:
            X[s:e, nb:] = np.asarray(extra_mm[r_chunk], dtype=np.float32)[:, e_arr]
    return X


def _assemble_slice(
    base_mm: np.memmap,
    extra_mm: np.memmap,
    s: int,
    e: int,
    base_cols: list[int],
    extra_cols: list[int],
) -> np.ndarray:
    """Fast sequential slice assembly using single-pass C column take."""
    b_arr = np.asarray(base_cols, dtype=np.intp)
    xb = np.array(base_mm[s:e], copy=False)[:, b_arr]
    if extra_cols:
        e_arr = np.asarray(extra_cols, dtype=np.intp)
        xe = np.array(extra_mm[s:e], copy=False)[:, e_arr]
        return np.concatenate([xb, xe], axis=1).astype(np.float32, copy=False)
    return np.asarray(xb, dtype=np.float32)


def _sample_stratified_negatives(
    base_mm: np.memmap,
    extra_mm: np.memmap,
    bmap: dict[str, int],
    emap: dict[str, int],
    domain_fp_mask: np.ndarray,
    d_vis_fp: np.ndarray,
    n_neg_target: int,
    *,
    use_seam: bool,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    pool_all = np.flatnonzero(domain_fp_mask & (d_vis_fp >= 3.5))
    n_pool = len(pool_all)
    if n_pool <= n_neg_target:
        return pool_all, np.ones(n_pool, dtype=np.float32)

    d_sub = d_vis_fp[pool_all]
    road_sub = np.asarray(base_mm[:, bmap["tiger_road_logdist"]], dtype=np.float32)[pool_all]
    shore_sub = np.asarray(base_mm[:, bmap["pluvial_shoreline_elev_dist_m"]], dtype=np.float32)[pool_all]
    if use_seam:
        seam_sub = np.asarray(extra_mm[:, emap["geodawn_seam_prox"]], dtype=np.float32)[pool_all]
        is_mimic_raw = (road_sub < np.log1p(150.0)) | (shore_sub < 22.0) | (seam_sub > 0.35)
    else:
        is_mimic_raw = (road_sub < np.log1p(150.0)) | (shore_sub < 22.0)

    s_shoulder = d_sub < 9.0
    s_mimic = (~s_shoulder) & is_mimic_raw
    s_bg = (~s_shoulder) & (~is_mimic_raw)

    strata = [pool_all[s_shoulder], pool_all[s_mimic], pool_all[s_bg]]
    target_fracs = [0.22, 0.22, 0.56]

    sel_parts: list[np.ndarray] = []
    w_parts: list[np.ndarray] = []
    rem_budget = n_neg_target

    for idx_s, t_frac in zip(strata[:-1], target_fracs[:-1]):
        true_frac = float(len(idx_s)) / float(n_pool)
        if len(idx_s) == 0 or true_frac < 1e-5:
            continue
        k = min(len(idx_s), int(round(n_neg_target * max(t_frac, true_frac))))
        chosen = rng.choice(idx_s, size=k, replace=False)
        sample_frac = float(k) / float(n_neg_target)
        w = float(np.clip(true_frac / max(sample_frac, 1e-4), 0.25, 2.0))
        sel_parts.append(chosen)
        w_parts.append(np.full(k, w, dtype=np.float32))
        rem_budget -= k

    idx_bg = strata[-1]
    if len(idx_bg) > 0 and rem_budget > 0:
        k_bg = min(len(idx_bg), rem_budget)
        chosen_bg = rng.choice(idx_bg, size=k_bg, replace=False)
        true_bg_frac = float(len(idx_bg)) / float(n_pool)
        sample_bg_frac = float(k_bg) / float(n_neg_target)
        w_bg = float(np.clip(true_bg_frac / max(sample_bg_frac, 1e-4), 0.4, 2.0))
        sel_parts.append(chosen_bg)
        w_parts.append(np.full(k_bg, w_bg, dtype=np.float32))

    sel = np.concatenate(sel_parts)
    w = np.concatenate(w_parts)
    order = np.argsort(sel)
    return sel[order], w[order]


def _fit_stage1_dual(
    exp_id: str,
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    train_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    max_iter: int = 135,
    neg_mult: int = 4,
    seed: int,
) -> Stage1DualBundle:
    bmap = {n: i for i, n in enumerate(base_meta["feature_names"])}
    emap = {n: i for i, n in enumerate(extra_meta["extra_feature_names"])}
    bl_cols, el_cols, bv_cols, ev_cols = _select_stage1_cols(base_meta, extra_meta, exp_id)
    has_lid_col = bmap["has_lidar"]
    use_seam = exp_id in ("Exp-ATSC-2", "Exp-ATSC-3")

    d_vis_fp = distance_transform_edt(~visible_2d).ravel()[fp_idx].astype(np.float32)
    train_fp = train_2d.ravel()[fp_idx]
    vis_fp = visible_2d.ravel()[fp_idx]
    has_lid_fp = np.asarray(base_mm[:, has_lid_col], dtype=np.float32) > 0.5

    pos_all = np.flatnonzero(train_fp & vis_fp)
    n_neg_all = min(int((train_fp & (d_vis_fp >= 3.5)).sum()), max(len(pos_all) * neg_mult, 30_000))
    neg_all, w_neg_all = _sample_stratified_negatives(
        base_mm, extra_mm, bmap, emap, train_fp, d_vis_fp, n_neg_all, use_seam=use_seam, seed=seed
    )
    rows_void = np.concatenate([pos_all, neg_all])
    r_ord = np.argsort(rows_void)
    rows_void = rows_void[r_ord]
    y_void = np.concatenate([np.ones(len(pos_all), dtype=np.int8), np.zeros(len(neg_all), dtype=np.int8)])[r_ord]
    w_void = np.concatenate([np.ones(len(pos_all), dtype=np.float32), w_neg_all])[r_ord]
    X_void = _assemble_rows(base_mm, extra_mm, rows_void, bv_cols, ev_cols)

    void_model = _make_hgb(max_iter=max_iter, seed=seed + 7)
    void_model.fit(X_void, y_void, sample_weight=w_void)
    true_prior_void = float(len(pos_all)) / max(int(train_fp.sum()), 1)
    eff_neg_void = float(w_neg_all.sum())
    void_prior_ratio = true_prior_void / max(
        (1.0 - true_prior_void) * (len(pos_all) / max(eff_neg_void, 1.0)), 1e-6
    )
    del X_void, y_void, w_void, rows_void

    train_lid_fp = train_fp & has_lid_fp
    pos_lid = np.flatnonzero(train_lid_fp & vis_fp)
    if len(pos_lid) < 500:
        lidar_model = void_model
        bl_cols, el_cols = bv_cols, ev_cols
        lidar_prior_ratio = void_prior_ratio
    else:
        n_neg_lid = min(int((train_lid_fp & (d_vis_fp >= 3.5)).sum()), max(len(pos_lid) * neg_mult, 25_000))
        neg_lid, w_neg_lid = _sample_stratified_negatives(
            base_mm, extra_mm, bmap, emap, train_lid_fp, d_vis_fp, n_neg_lid, use_seam=use_seam, seed=seed + 19
        )
        rows_lid = np.concatenate([pos_lid, neg_lid])
        l_ord = np.argsort(rows_lid)
        rows_lid = rows_lid[l_ord]
        y_lid = np.concatenate([np.ones(len(pos_lid), dtype=np.int8), np.zeros(len(neg_lid), dtype=np.int8)])[l_ord]
        w_lid = np.concatenate([np.ones(len(pos_lid), dtype=np.float32), w_neg_lid])[l_ord]
        X_lid = _assemble_rows(base_mm, extra_mm, rows_lid, bl_cols, el_cols)

        lidar_model = _make_hgb(max_iter=max_iter, seed=seed + 23)
        lidar_model.fit(X_lid, y_lid, sample_weight=w_lid)
        true_prior_lid = float(len(pos_lid)) / max(int(train_lid_fp.sum()), 1)
        eff_neg_lid = float(w_neg_lid.sum())
        lidar_prior_ratio = true_prior_lid / max(
            (1.0 - true_prior_lid) * (len(pos_lid) / max(eff_neg_lid, 1.0)), 1e-6
        )
        del X_lid, y_lid, w_lid, rows_lid

    return Stage1DualBundle(
        lidar_model=lidar_model,
        void_model=void_model,
        base_lidar_cols=bl_cols,
        extra_lidar_cols=el_cols,
        base_void_cols=bv_cols,
        extra_void_cols=ev_cols,
        has_lidar_base_col=has_lid_col,
        lidar_prior_ratio=lidar_prior_ratio,
        void_prior_ratio=void_prior_ratio,
    )


def _predict_routed_single_pass(
    models_by_route: list[Stage1DualBundle],
    route_id_fp: np.ndarray,
    base_mm: np.memmap,
    extra_mm: np.memmap,
) -> np.ndarray:
    """Single sequential pass over 5.17M mmap rows routing each row to models_by_route[route_id_fp[i]]."""
    n_fp = base_mm.shape[0]
    out = np.zeros(n_fp, dtype=np.float32)
    s0 = models_by_route[0]
    chunk = 500_000
    for s in range(0, n_fp, chunk):
        e = min(n_fp, s + chunk)
        r_chunk = route_id_fp[s:e]
        if (r_chunk < 0).all():
            continue
        has_lid = np.asarray(base_mm[s:e, s0.has_lidar_base_col], dtype=np.float32) > 0.5
        X_l_all = _assemble_slice(base_mm, extra_mm, s, e, s0.base_lidar_cols, s0.extra_lidar_cols)
        X_v_all = _assemble_slice(base_mm, extra_mm, s, e, s0.base_void_cols, s0.extra_void_cols)
        p_chunk = np.zeros(e - s, dtype=np.float32)
        for m_idx, mdl in enumerate(models_by_route):
            m_mask = r_chunk == m_idx
            if not m_mask.any():
                continue
            m_lid = m_mask & has_lid
            m_void = m_mask & ~has_lid
            if m_void.any():
                p_chunk[m_void] = _prior_calibrate(
                    mdl.void_model.predict_proba(X_v_all[m_void])[:, 1],
                    mdl.void_prior_ratio,
                    sharpness=1.15,
                )
            if m_lid.any():
                p_chunk[m_lid] = _prior_calibrate(
                    mdl.lidar_model.predict_proba(X_l_all[m_lid])[:, 1],
                    mdl.lidar_prior_ratio,
                    sharpness=1.15,
                )
        del X_l_all, X_v_all
        out[s:e] = p_chunk
    return out


def _predict_s2_fused_domain(
    b: ATSCExperimentBundle,
    s2_corr_fp: np.ndarray,
    tip_fp: np.ndarray | None,
    p1_fp: np.ndarray,
    dom_rows: np.ndarray,
) -> np.ndarray:
    assert b.stage2_lidar_model is not None and b.stage2_void_model is not None
    fused = np.empty(len(dom_rows), dtype=np.float32)
    chunk = 350_000
    for s in range(0, len(dom_rows), chunk):
        sl = dom_rows[s : s + chunk]
        X_sub = (
            np.hstack([s2_corr_fp[sl], tip_fp[sl]]).astype(np.float32)
            if (b.use_tip_features and tip_fp is not None)
            else s2_corr_fp[sl].astype(np.float32)
        )
        has_lid = s2_corr_fp[sl, 15] > 0.5
        p1_c = p1_fp[sl]
        f_c = np.empty(len(sl), dtype=np.float32)
        if (~has_lid).any():
            p2_v = _prior_calibrate(
                b.stage2_void_model.predict_proba(X_sub[~has_lid])[:, 1],
                b.stage2_void_prior_ratio,
                sharpness=1.16,
            )
            f_c[~has_lid] = (0.50 * p2_v + 0.50 * p1_c[~has_lid]).astype(np.float32)
        if has_lid.any():
            p2_l = _prior_calibrate(
                b.stage2_lidar_model.predict_proba(X_sub[has_lid])[:, 1],
                b.stage2_lidar_prior_ratio,
                sharpness=1.18,
            )
            f_c[has_lid] = (0.72 * p2_l + 0.28 * p1_c[has_lid]).astype(np.float32)
        fused[s : s + chunk] = f_c
    return fused


def _predict_stage1_subset(
    s1: Stage1DualBundle,
    base_mm: np.memmap,
    extra_mm: np.memmap,
    rows_fp: np.ndarray,
) -> np.ndarray:
    n = len(rows_fp)
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    out = np.empty(n, dtype=np.float32)
    chunk = 400_000
    for s in range(0, n, chunk):
        sl = rows_fp[s : s + chunk]
        has_lid = np.asarray(base_mm[sl, s1.has_lidar_base_col], dtype=np.float32) > 0.5
        p_chunk = np.empty(len(sl), dtype=np.float32)
        if (~has_lid).any():
            nl_local = np.flatnonzero(~has_lid)
            X_v = _assemble_rows(base_mm, extra_mm, sl[nl_local], s1.base_void_cols, s1.extra_void_cols)
            p_chunk[nl_local] = _prior_calibrate(
                s1.void_model.predict_proba(X_v)[:, 1], s1.void_prior_ratio, sharpness=1.15
            )
            del X_v
        if has_lid.any():
            lid_local = np.flatnonzero(has_lid)
            X_l = _assemble_rows(base_mm, extra_mm, sl[lid_local], s1.base_lidar_cols, s1.extra_lidar_cols)
            p_chunk[lid_local] = _prior_calibrate(
                s1.lidar_model.predict_proba(X_l)[:, 1], s1.lidar_prior_ratio, sharpness=1.15
            )
            del X_l
        out[s : s + chunk] = p_chunk
    return out


def _make_inner_spatial_substrips(
    train_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    n_splits: int = 2,
    buffer_px: int = 10,
) -> list[dict[str, np.ndarray]]:
    """Partition ``train_2d`` into contiguous diagonal spatial halves with whole-segment purging."""
    yy, xx = np.nonzero(train_2d)
    proj = (yy + xx).astype(np.float32)
    cuts = np.quantile(proj, np.linspace(0.0, 1.0, n_splits + 1))
    strip_id = np.full(train_2d.shape, -1, dtype=np.int8)
    for k in range(n_splits):
        lo, hi = float(cuts[k]), float(cuts[k + 1])
        mask_k = (proj >= lo) & (proj <= hi if k == n_splits - 1 else proj < hi)
        strip_id[yy[mask_k], xx[mask_k]] = k

    comp, _ = ndi_label(visible_2d, structure=np.ones((3, 3), dtype=int))
    splits: list[dict[str, np.ndarray]] = []
    for k in range(n_splits):
        val_k = train_2d & (strip_id == k)
        collar_k = distance_transform_edt(~val_k) <= buffer_px
        hid_ids = np.unique(comp[collar_k & visible_2d])
        hid_ids = hid_ids[hid_ids > 0]
        hid_k = visible_2d & np.isin(comp, hid_ids)
        vis_keep_k = visible_2d & ~hid_k
        trn_k = train_2d & (distance_transform_edt(~(val_k | hid_k)) > buffer_px)
        splits.append({"val": val_k, "trn": trn_k, "vis_keep": vis_keep_k})
    return splits


def _fit_stage2_head_from_corr(
    exp_id: str,
    s1_full: Stage1DualBundle,
    s2_corr_oof_fp: np.ndarray,
    inner_splits: list[dict[str, np.ndarray]],
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    train_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    seed: int,
) -> ATSCExperimentBundle:
    use_tip = exp_id == "Exp-ATSC-3"
    n_fp = len(fp_idx)
    tip_oof_fp = np.zeros((n_fp, 4), dtype=np.float32) if use_tip else None
    if use_tip and tip_oof_fp is not None:
        for sp in inner_splits:
            val_mask_fp = sp["val"].ravel()[fp_idx]
            if not val_mask_fp.any():
                continue
            tip_k = compute_visible_tip_bridge_features(
                sp["vis_keep"],
                footprint,
                fp_idx,
                s2_corr_oof_fp[:, 1],
                s2_corr_oof_fp[:, 2],
            )
            tip_oof_fp[val_mask_fp] = tip_k[val_mask_fp]
            del tip_k

    bmap = {n: i for i, n in enumerate(base_meta["feature_names"])}
    emap = {n: i for i, n in enumerate(extra_meta["extra_feature_names"])}
    train_fp = train_2d.ravel()[fp_idx]
    vis_fp = visible_2d.ravel()[fp_idx]
    d_vis_fp = distance_transform_edt(~visible_2d).ravel()[fp_idx].astype(np.float32)
    has_lid_fp = s2_corr_oof_fp[:, 15] > 0.5

    def _fit_s2_regime(reg_mask: np.ndarray, r_seed: int) -> tuple[HistGradientBoostingClassifier, float, int]:
        dom = train_fp & reg_mask
        pos_r = np.flatnonzero(dom & vis_fp)
        n_neg_r = min(int((dom & (d_vis_fp >= 3.2)).sum()), max(len(pos_r) * 5, 25_000))
        neg_r, w_neg_r = _sample_stratified_negatives(
            base_mm, extra_mm, bmap, emap, dom, d_vis_fp, n_neg_r, use_seam=True, seed=r_seed
        )
        rows_r = np.concatenate([pos_r, neg_r])
        if use_tip and tip_oof_fp is not None:
            X_r = np.hstack([s2_corr_oof_fp[rows_r], tip_oof_fp[rows_r]]).astype(np.float32)
        else:
            X_r = s2_corr_oof_fp[rows_r].astype(np.float32)
        y_r = np.concatenate([np.ones(len(pos_r), dtype=np.int8), np.zeros(len(neg_r), dtype=np.int8)])
        w_r = np.concatenate([np.ones(len(pos_r), dtype=np.float32), w_neg_r])
        mdl = _make_hgb(
            max_iter=95,
            max_leaf_nodes=31,
            min_samples_leaf=180,
            l2_regularization=2.5,
            seed=r_seed + 17,
        )
        mdl.fit(X_r, y_r, sample_weight=w_r)
        tp_r = float(len(pos_r)) / max(int(dom.sum()), 1)
        en_r = float(w_neg_r.sum())
        pr_r = tp_r / max((1.0 - tp_r) * (len(pos_r) / max(en_r, 1.0)), 1e-6)
        nf = int(X_r.shape[1])
        del X_r, y_r, w_r, rows_r
        return mdl, pr_r, nf

    # Void Stage-2 trained on ALL train_fp using regime-harmonized corridor features;
    # LiDAR Stage-2 trained strictly on has_lidar == 1 cells so LiDAR amplitude never starves 10 m voids!
    s2_void_model, s2_void_pr, n_s2_feats = _fit_s2_regime(np.ones(n_fp, dtype=bool), seed + 503)
    if int((train_fp & has_lid_fp & vis_fp).sum()) >= 500:
        s2_lid_model, s2_lid_pr, _ = _fit_s2_regime(has_lid_fp, seed + 607)
    else:
        s2_lid_model, s2_lid_pr = s2_void_model, s2_void_pr
    del tip_oof_fp

    return ATSCExperimentBundle(
        exp_id=exp_id,
        stage1=s1_full,
        stage2_lidar_model=s2_lid_model,
        stage2_void_model=s2_void_model,
        stage2_lidar_prior_ratio=s2_lid_pr,
        stage2_void_prior_ratio=s2_void_pr,
        use_tip_features=use_tip,
        report={
            "stage": 2,
            "n_stage2_features": n_s2_feats,
            "use_tip_features": use_tip,
            "n_pos_train": int((train_fp & vis_fp).sum()),
        },
    )


def fit_atsc_experiment(
    exp_id: str,
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    train_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    fast_cols: dict[str, np.ndarray] | None = None,
    seed: int,
) -> ATSCExperimentBundle:
    """Standalone single-experiment fitter (used during orthogonal confirmation & unit tests)."""
    s1_full = _fit_stage1_dual(
        exp_id,
        base_mm,
        base_meta,
        extra_mm,
        extra_meta,
        footprint,
        fp_idx,
        train_2d,
        visible_2d,
        max_iter=75,
        seed=seed,
    )
    if exp_id == "Exp-ATSC-1":
        return ATSCExperimentBundle(
            exp_id=exp_id,
            stage1=s1_full,
            stage2_lidar_model=None,
            stage2_void_model=None,
            stage2_lidar_prior_ratio=1.0,
            stage2_void_prior_ratio=1.0,
            use_tip_features=False,
            report={"stage": 1, "n_stage2_features": 0},
        )

    inner_splits = _make_inner_spatial_substrips(train_2d, visible_2d, n_splits=2, buffer_px=10)
    route_id = np.zeros(len(fp_idx), dtype=np.int8)
    route_id[train_2d.ravel()[fp_idx]] = -1
    models_route = [s1_full]
    for k, sp in enumerate(inner_splits):
        val_mask = sp["val"].ravel()[fp_idx]
        if not val_mask.any() or int((sp["trn"] & sp["vis_keep"]).sum()) < 500:
            route_id[val_mask] = 0
            continue
        s1_inner = _fit_stage1_dual(
            exp_id,
            base_mm,
            base_meta,
            extra_mm,
            extra_meta,
            footprint,
            fp_idx,
            sp["trn"],
            sp["vis_keep"],
            max_iter=65,
            neg_mult=4,
            seed=seed + 101 * (k + 1),
        )
        route_id[val_mask] = len(models_route)
        models_route.append(s1_inner)

    p1_oof_fp = _predict_routed_single_pass(models_route, route_id, base_mm, extra_mm)
    del models_route
    p1_oof_2d = np.zeros(footprint.shape, dtype=np.float32)
    p1_oof_2d.ravel()[fp_idx] = p1_oof_fp
    del p1_oof_fp

    s2_corr_fp = compute_stage2_corridor_features(
        p1_oof_2d, footprint, fp_idx, base_mm, base_meta, extra_mm, extra_meta, fast_cols=fast_cols
    )
    del p1_oof_2d
    out = _fit_stage2_head_from_corr(
        exp_id,
        s1_full,
        s2_corr_fp,
        inner_splits,
        base_mm,
        base_meta,
        extra_mm,
        extra_meta,
        footprint,
        fp_idx,
        train_2d,
        visible_2d,
        seed=seed,
    )
    del s2_corr_fp
    gc.collect()
    return out


def fit_and_predict_fold_trio(
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    train_2d: np.ndarray,
    valid_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    fast_cols: dict[str, np.ndarray] | None = None,
    seed: int,
) -> dict[str, tuple[np.ndarray, dict[str, Any]]]:
    """Fit & predict Exp-ATSC-1, Exp-ATSC-2, and Exp-ATSC-3 on one fold in a single sequential pass."""
    results: dict[str, tuple[np.ndarray, dict[str, Any]]] = {}
    n_fp = len(fp_idx)
    val_mask_fp = (valid_2d & footprint).ravel()[fp_idx]
    val_rows = np.flatnonzero(val_mask_fp)

    # 1. Exp-ATSC-1 (Group D only, 1-stage)
    s1_e1_bundle = _fit_stage1_dual(
        "Exp-ATSC-1",
        base_mm,
        base_meta,
        extra_mm,
        extra_meta,
        footprint,
        fp_idx,
        train_2d,
        visible_2d,
        max_iter=75,
        neg_mult=4,
        seed=seed + 1000,
    )
    route_e1 = np.where(val_mask_fp, 0, -1).astype(np.int8)
    p_e1_fp = _predict_routed_single_pass([s1_e1_bundle], route_e1, base_mm, extra_mm)
    s1_e1 = np.zeros(footprint.shape, dtype=np.float32)
    s1_e1.ravel()[fp_idx] = p_e1_fp
    results["Exp-ATSC-1"] = (s1_e1, {"stage": 1, "n_stage2_features": 0})
    del s1_e1_bundle, p_e1_fp
    gc.collect()

    # 2. Shared Stage-1 (Groups D + E) + 2-strip buffered inner-OOF in ONE sequential mmap pass!
    s1_shared = _fit_stage1_dual(
        "Exp-ATSC-2",
        base_mm,
        base_meta,
        extra_mm,
        extra_meta,
        footprint,
        fp_idx,
        train_2d,
        visible_2d,
        max_iter=75,
        neg_mult=4,
        seed=seed + 2000,
    )
    inner_splits = _make_inner_spatial_substrips(train_2d, visible_2d, n_splits=2, buffer_px=10)
    route_id = np.zeros(n_fp, dtype=np.int8)
    route_id[train_2d.ravel()[fp_idx]] = -1
    models_route = [s1_shared]
    for k, sp in enumerate(inner_splits):
        vm = sp["val"].ravel()[fp_idx]
        if not vm.any() or int((sp["trn"] & sp["vis_keep"]).sum()) < 500:
            route_id[vm] = 0
            continue
        s1_in = _fit_stage1_dual(
            "Exp-ATSC-2",
            base_mm,
            base_meta,
            extra_mm,
            extra_meta,
            footprint,
            fp_idx,
            sp["trn"],
            sp["vis_keep"],
            max_iter=65,
            neg_mult=4,
            seed=seed + 2000 + 101 * (k + 1),
        )
        route_id[vm] = len(models_route)
        models_route.append(s1_in)

    p1_comp_fp = _predict_routed_single_pass(models_route, route_id, base_mm, extra_mm)
    del models_route

    p1_comp_2d = np.zeros(footprint.shape, dtype=np.float32)
    p1_comp_2d.ravel()[fp_idx] = p1_comp_fp

    s2_corr_fp = compute_stage2_corridor_features(
        p1_comp_2d, footprint, fp_idx, base_mm, base_meta, extra_mm, extra_meta, fast_cols=fast_cols
    )
    del p1_comp_2d

    b2 = _fit_stage2_head_from_corr(
        "Exp-ATSC-2",
        s1_shared,
        s2_corr_fp,
        inner_splits,
        base_mm,
        base_meta,
        extra_mm,
        extra_meta,
        footprint,
        fp_idx,
        train_2d,
        visible_2d,
        seed=seed + 2000,
    )
    b3 = _fit_stage2_head_from_corr(
        "Exp-ATSC-3",
        s1_shared,
        s2_corr_fp,
        inner_splits,
        base_mm,
        base_meta,
        extra_mm,
        extra_meta,
        footprint,
        fp_idx,
        train_2d,
        visible_2d,
        seed=seed + 3000,
    )

    tip_eval_fp = compute_visible_tip_bridge_features(
        visible_2d, footprint, fp_idx, s2_corr_fp[:, 1], s2_corr_fp[:, 2]
    )

    for b, eid in ((b2, "Exp-ATSC-2"), (b3, "Exp-ATSC-3")):
        fused = _predict_s2_fused_domain(b, s2_corr_fp, tip_eval_fp, p1_comp_fp, val_rows)
        surf = np.zeros(footprint.shape, dtype=np.float32)
        surf.ravel()[fp_idx[val_rows]] = fused
        results[eid] = (surf, b.report)

    del s2_corr_fp, tip_eval_fp, p1_comp_fp, b2, b3, s1_shared
    gc.collect()
    return results


def predict_atsc_surface(
    bundle: ATSCExperimentBundle,
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    domain_2d: np.ndarray,
    visible_2d: np.ndarray,
    *,
    fast_cols: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    dom_mask_fp = (domain_2d & footprint).ravel()[fp_idx]
    dom_local = np.flatnonzero(dom_mask_fp)
    if len(dom_local) == 0:
        return np.zeros(footprint.shape, dtype=np.float32)

    if bundle.stage2_lidar_model is None:
        r_dom = np.where(dom_mask_fp, 0, -1).astype(np.int8)
        out = np.zeros(footprint.shape, dtype=np.float32)
        out.ravel()[fp_idx] = _predict_routed_single_pass([bundle.stage1], r_dom, base_mm, extra_mm)
        return out

    # Only need Stage-1 within 14 px of domain_2d!
    needed_2d = binary_dilation(domain_2d & footprint, iterations=14) & footprint
    r_need = np.where(needed_2d.ravel()[fp_idx], 0, -1).astype(np.int8)
    p1_fp = _predict_routed_single_pass([bundle.stage1], r_need, base_mm, extra_mm)
    p1_2d = np.zeros(footprint.shape, dtype=np.float32)
    p1_2d.ravel()[fp_idx] = p1_fp

    s2_corr_fp = compute_stage2_corridor_features(
        p1_2d, footprint, fp_idx, base_mm, base_meta, extra_mm, extra_meta, fast_cols=fast_cols
    )
    del p1_2d
    tip_fp = (
        compute_visible_tip_bridge_features(visible_2d, footprint, fp_idx, s2_corr_fp[:, 1], s2_corr_fp[:, 2])
        if bundle.use_tip_features
        else None
    )
    fused_dom = _predict_s2_fused_domain(bundle, s2_corr_fp, tip_fp, p1_fp, dom_local)
    out = np.zeros(footprint.shape, dtype=np.float32)
    out.ravel()[fp_idx[dom_local]] = fused_dom
    return out


def build_axial_submodular_mass(
    surf_2d: np.ndarray,
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    *,
    fast_cols: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    p = np.where(footprint & np.isfinite(surf_2d) & (surf_2d > 0.0), surf_2d, 0.0).astype(np.float32)
    bg_800 = gaussian_filter(p, sigma=8.0)
    crest_conc = np.clip((p + 1e-4) / (bg_800 + 1e-4), 0.30, 4.20).astype(np.float32)

    spine = ridge_nms(p, footprint, sigma=1.0) & footprint
    spine_near = binary_dilation(spine, iterations=1) & footprint & ~spine
    axial_w = np.where(spine, 1.0, np.where(spine_near, 0.52, 0.20)).astype(np.float32)

    if fast_cols is not None:
        playa_fp = fast_cols["flat_playa_indicator"]
        grav_hg_fp = fast_cols["iso_grav_anom_hg"]
        tmi_up_fp = fast_cols["tmi_up150_grad"]
    else:
        bmap = {n: i for i, n in enumerate(base_meta["feature_names"])}
        emap = {n: i for i, n in enumerate(extra_meta["extra_feature_names"])}
        playa_fp = np.asarray(extra_mm[:, emap["flat_playa_indicator"]], dtype=np.float32)
        grav_hg_fp = np.asarray(base_mm[:, bmap["iso_grav_anom_hg"]], dtype=np.float32)
        tmi_up_fp = np.asarray(base_mm[:, bmap["tmi_up150_grad"]], dtype=np.float32)
    weak_geophys = (grav_hg_fp < float(np.median(grav_hg_fp))) & (tmi_up_fp < float(np.median(tmi_up_fp)))

    hab_fp = np.where((playa_fp > 0.45) & weak_geophys, 0.35, 1.0).astype(np.float32)
    hab_2d = np.ones(footprint.shape, dtype=np.float32)
    hab_2d.ravel()[fp_idx] = hab_fp

    q_axial = (p * (crest_conc ** 0.45) * axial_w * hab_2d).astype(np.float32)
    q_axial[~footprint] = 0.0
    return q_axial


def emit_atsc_submodular(
    surf_2d: np.ndarray,
    eligible_2d: np.ndarray,
    active_mass_2d: np.ndarray,
    budget: int,
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    *,
    fast_cols: dict[str, np.ndarray] | None = None,
    min_self_spacing_px: float = 2.85,
) -> np.ndarray:
    q_axial = build_axial_submodular_mass(
        surf_2d, footprint, fp_idx, base_mm, base_meta, extra_mm, extra_meta, fast_cols=fast_cols
    )
    return celf_submodular_emit_300m(
        q_axial,
        eligible_2d,
        budget,
        active_mass_mask=active_mass_2d,
        min_self_spacing_px=min_self_spacing_px,
    )
