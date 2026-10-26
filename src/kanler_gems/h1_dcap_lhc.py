"""Frozen Lane KANLER-H1 (DCAP-LHC):
Dip-Coupled Asymmetric Piedmont-Scarp, Road-Vetoed 1m LiDAR Scarplet,
and Hydrothermal-Magnetic Conduit Concordance.

Strictly implements `research/preregistration_kanler_h1.md` using the shared
`vendor/gems57` template (`evaluate_holdout.py`, `spatial.py`, `metric.py`,
`submission_writer.py`). Zero catalogue-derived features are ever computed
in the static line stack.
"""
from __future__ import annotations

import gc
import hashlib
import heapq
import json
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.optimize import minimize
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout as ev
from gems57 import metric as vmetric
from gems57 import spatial, submission_writer

SHAPE = (3730, 3292)
BUDGET = 37_654
B_PX = 2.0
CONFIRM_SEED = 3103
BUFFER_PX = 80

COMPETITION_BANDS = [
    "mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope", "tc",
    "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15", "iso_grav_anom_vg",
    "det_elev", "iso_grav_anom", "tmi", "depth_to_base_surf", "ieq_n100a15",
    "cond_surf", "iso_grav_anom_hg", "det_elev_slope",
]
LIDAR_BANDS = [
    "ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max",
    "downface_max", "upface_max", "cross_max", "relief", "coh100", "strike", "valid",
]
RAD_BANDS = ["K", "Th", "U", "TC"]
EXT_BANDS = ["ThK", "UK", "UTh", "TMI_up150"]

LINE_NAMES = [
    "J_ASYM",
    "SUB_DIP",
    "LIDAR_SCARP",
    "BLIND_CONDUIT",
    "TECT_CTX",
    "CTRL",
    "SLOPE",
    "REF_H31X",
]


def log(*args) -> None:
    print("[kanler-h1]", *args, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_base_masks(root: Path):
    with rasterio.open(root / "data/official/sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(root / "data/official/labels.tif") as ds:
        cat = (ds.read(1) == 1) & foot
    with rasterio.open(root / "data/external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = (ds.read(1) == 1) & foot
    d_cat = distance_transform_edt(~cat).astype(np.float32)
    off_sgmc = sgmc & (d_cat > 3.0)
    return foot, cat, sgmc, off_sgmc, d_cat


def load_cached_band(root: Path, band_name: str) -> np.ndarray:
    idx = COMPETITION_BANDS.index(band_name) + 1
    p = root / ".cache" / "features" / f"band-{idx:02d}.npy"
    arr = np.load(p, mmap_mode="r")
    return np.asarray(arr, dtype=np.float32).copy()


def load_external_band(path: Path, band_idx_1based: int, zero_is_nodata: bool = True) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(band_idx_1based).astype(np.float32)
    if zero_is_nodata:
        arr[arr == 0] = np.nan
    arr[(~np.isfinite(arr)) | (np.abs(arr) > 1e30)] = np.nan
    return arr


def fill_nearest_and_winsorize(
    raw: np.ndarray,
    foot: np.ndarray,
    base_valid: np.ndarray | None = None,
    base_idx: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray]]:
    """Winsorize [0.1, 99.9] inside footprint and nearest-valid-neighbor extrapolate outside."""
    valid = foot & np.isfinite(raw)
    vals = raw[valid]
    lo, hi = np.percentile(vals, [0.1, 99.9])
    out = np.clip(raw, lo, hi).astype(np.float32, copy=True)
    if base_idx is not None and base_valid is not None and np.array_equal(valid, base_valid):
        idx = base_idx
    else:
        _, idx = distance_transform_edt(~valid, return_distances=True, return_indices=True)
    bad = ~valid
    if bad.any():
        out[bad] = out[idx[0][bad], idx[1][bad]]
    return out, idx


def rank01(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Label-free mid-rank / uniform percentile transform in (0, 1] inside `mask`, 0 outside."""
    out = np.zeros(arr.shape, dtype=np.float32)
    m = mask & np.isfinite(arr)
    v = arr[m]
    if v.size == 0:
        return out
    pos = v > 0 if (v >= 0).all() else np.ones(v.size, dtype=bool)
    if not pos.any():
        return out
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size, dtype=np.float32)
    ranks[order] = (np.arange(1, v.size + 1, dtype=np.float32)) / float(v.size)
    # Exact zero input stays zero so masked regions never receive spurious positive rank
    if (v == 0).any() and (v >= 0).all():
        z_frac = float((v == 0).mean())
        ranks = np.where(v > 0, (ranks - z_frac) / max(1.0 - z_frac, 1e-6), 0.0).astype(np.float32)
    out[m] = np.clip(ranks, 0.0, 1.0)
    return out


def trapezoid_window(s: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    w = np.zeros(s.shape, dtype=np.float32)
    rise = (s > a) & (s < b)
    w[rise] = (s[rise] - a) / (b - a)
    w[(s >= b) & (s <= c)] = 1.0
    fall = (s > c) & (s < d)
    w[fall] = (d - s[fall]) / (d - c)
    return w


def sample_along_vector_foot(
    field: np.ndarray,
    fy: np.ndarray,
    fx: np.ndarray,
    vy_f: np.ndarray,
    vx_f: np.ndarray,
    dist_px: float,
) -> np.ndarray:
    """Fast 1D bilinear interpolation of `field` at `(fy + dist*vy, fx + dist*vx)` on footprint pixels."""
    h, w = field.shape
    ry = np.clip(fy + dist_px * vy_f, 0.0, h - 1.001)
    rx = np.clip(fx + dist_px * vx_f, 0.0, w - 1.001)
    y0 = ry.astype(np.int32)
    x0 = rx.astype(np.int32)
    wy = (ry - y0).astype(np.float32)
    wx = (rx - x0).astype(np.float32)
    v00 = field[y0, x0]
    v01 = field[y0, x0 + 1]
    v10 = field[y0 + 1, x0]
    v11 = field[y0 + 1, x0 + 1]
    return (
        v00 * (1.0 - wy) * (1.0 - wx)
        + v01 * (1.0 - wy) * wx
        + v10 * wy * (1.0 - wx)
        + v11 * wy * wx
    ).astype(np.float32)


def soft_crest_nms(
    field: np.ndarray,
    fy_f: np.ndarray,
    fx_f: np.ndarray,
    ny_f: np.ndarray,
    nx_f: np.ndarray,
    foot: np.ndarray,
    off_crest_scale: float = 0.12,
) -> np.ndarray:
    """Soft 1-px cross-strike crest localization: preserves full-grid Spearman rank continuity
    while concentrating top-K support onto 1-px structural centerlines."""
    fy_i = fy_f.astype(np.int32)
    fx_i = fx_f.astype(np.int32)
    c0 = field[fy_i, fx_i]
    cp1 = sample_along_vector_foot(field, fy_f, fx_f, ny_f, nx_f, +1.0)
    cm1 = sample_along_vector_foot(field, fy_f, fx_f, ny_f, nx_f, -1.0)
    cp2 = sample_along_vector_foot(field, fy_f, fx_f, ny_f, nx_f, +2.0)
    cm2 = sample_along_vector_foot(field, fy_f, fx_f, ny_f, nx_f, -2.0)
    is_crest = (c0 >= cp1) & (c0 >= cm1) & (c0 > 0.5 * (cp2 + cm2))
    out = np.zeros(field.shape, dtype=np.float32)
    out[fy_i, fx_i] = np.where(is_crest, c0, off_crest_scale * c0).astype(np.float32)
    out[~foot] = 0.0
    return out


def build_lines(root: Path, force: bool = False) -> dict:
    """Compute and cache all frozen KANLER-H1 physical lines + controls in `.cache/kanler_h1/`."""
    cache_dir = root / ".cache" / "kanler_h1"
    cache_dir.mkdir(parents=True, exist_ok=True)
    lines_path = cache_dir / "lines.f32"
    meta_path = cache_dir / "lines_meta.json"
    if lines_path.is_file() and meta_path.is_file() and not force:
        log("Reusing cached physical lines:", lines_path)
        return json.loads(meta_path.read_text())

    t0 = time.time()
    foot, _, _, _, _ = load_base_masks(root)
    # Attenuate 2-px outer survey boundary sliver where derivatives touch extrapolated padding
    d_edge = distance_transform_edt(foot).astype(np.float32)
    edge_taper = np.clip((d_edge - 1.0) / 2.0, 0.0, 1.0).astype(np.float32)

    fy, fx = np.nonzero(foot)
    fy_f = fy.astype(np.float32)
    fx_f = fx.astype(np.float32)

    mm = np.memmap(lines_path, dtype=np.float32, mode="w+", shape=(len(LINE_NAMES),) + SHAPE)

    # ------------------------------------------------------------------
    # Load elevation & slope once -> compute u_down, strike t, REF_H31X, SLOPE, and Line 1 (J_ASYM)
    # ------------------------------------------------------------------
    raw_elev = load_cached_band(root, "det_elev")
    base_valid = foot & np.isfinite(raw_elev)
    z, base_idx = fill_nearest_and_winsorize(raw_elev, foot)
    del raw_elev
    raw_slope = load_cached_band(root, "det_elev_slope")
    s, _ = fill_nearest_and_winsorize(raw_slope, foot, base_valid, base_idx)
    del raw_slope

    zs = gaussian_filter(z, 1.5, mode="nearest")
    gy = gaussian_filter(zs, 1.0, order=(1, 0), mode="nearest")
    gx = gaussian_filter(zs, 1.0, order=(0, 1), mode="nearest")
    mag = np.hypot(gy, gx) + 1e-6
    uy = (-gy / mag).astype(np.float32)
    ux = (-gx / mag).astype(np.float32)
    del gy, gx, mag

    ss = gaussian_filter(s, 1.5, mode="nearest")
    sy = gaussian_filter(ss, 1.0, order=(1, 0), mode="nearest")
    sx = gaussian_filter(ss, 1.0, order=(0, 1), mode="nearest")
    d_down = (sy * uy + sx * ux).astype(np.float32)
    j_raw = np.maximum(-d_down, 0.0).astype(np.float32)
    del sy, sx, d_down

    # Exact H31-X reference reproduction (`X1_raw`: window 1-3-15-25 deg, no NMS)
    ref_h31x = (j_raw * trapezoid_window(ss, 1.0, 3.0, 15.0, 25.0)).astype(np.float32)
    ref_h31x[~foot] = 0.0
    mm[LINE_NAMES.index("REF_H31X")] = rank01(ref_h31x, foot)
    del ref_h31x

    # SLOPE control
    mm[LINE_NAMES.index("SLOPE")] = rank01(np.where(foot, s, 0.0), foot)

    # Line 1: J_ASYM — scale-normalized break + step-vs-thalweg asymmetry + 800m strike persistence
    uy_f = uy[fy, fx]
    ux_f = ux[fy, fx]
    ty_f = -ux_f
    tx_f = uy_f

    z_up = sample_along_vector_foot(zs, fy_f, fx_f, uy_f, ux_f, -3.0)
    z_dn = sample_along_vector_foot(zs, fy_f, fx_f, uy_f, ux_f, +3.0)
    s_up = sample_along_vector_foot(ss, fy_f, fx_f, uy_f, ux_f, -3.0)
    s_dn = sample_along_vector_foot(ss, fy_f, fx_f, uy_f, ux_f, +3.0)
    z0_f = zs[fy, fx]

    # Monotonic step-ramp drop (vetoes symmetric canyon thalwegs where both banks rise)
    mono_step = ((z_up > z0_f + 0.35) & (z0_f > z_dn + 0.15)).astype(np.float32)
    slope_asym = np.clip((s_up - s_dn + 0.8) / (s_up + s_dn + 2.0), 0.0, 1.0).astype(np.float32)
    step_gate_f = mono_step * (0.25 + 0.75 * slope_asym)
    del z_up, z_dn, s_up, s_dn, z0_f, slope_asym

    win_pied = trapezoid_window(ss, 0.8, 2.2, 16.0, 26.0)
    j_rel = (j_raw / (ss + 2.0)) * win_pied
    j_abs = j_raw * win_pied
    j_comb = (0.50 * rank01(j_abs, foot) + 0.50 * rank01(j_rel, foot)).astype(np.float32)
    j_comb[fy, fx] *= step_gate_f
    j_comb *= edge_taper
    del j_raw, j_rel, j_abs, win_pied

    # Along-strike persistence over k in {-3..+3} px (600 m aperture along strike t)
    acc = np.zeros(fy.size, dtype=np.float32)
    w_tot = 0.0
    for k_off in (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0):
        wk = float(np.exp(-0.5 * (k_off / 2.0) ** 2))
        acc += wk * sample_along_vector_foot(j_comb, fy_f, fx_f, ty_f, tx_f, k_off)
        w_tot += wk
    j_pers = np.zeros(SHAPE, dtype=np.float32)
    j_pers[fy, fx] = acc / w_tot
    j_crest = soft_crest_nms(j_pers, fy_f, fx_f, uy_f, ux_f, foot, off_crest_scale=0.12)
    mm[LINE_NAMES.index("J_ASYM")] = rank01(j_crest, foot)
    del j_comb, j_pers, j_crest, acc
    log("Built Line 1 (J_ASYM) + REF_H31X + SLOPE in", round(time.time() - t0, 1), "s")

    # ------------------------------------------------------------------
    # Line 2: SUB_DIP — Dip-Projected Hanging-Wall Gravity / Basement / Upward-Mag Corroboration
    # ------------------------------------------------------------------
    g_slope, _ = fill_nearest_and_winsorize(load_cached_band(root, "iso_grav_anom_slope"), foot, base_valid, base_idx)
    d_base, _ = fill_nearest_and_winsorize(load_cached_band(root, "depth_to_base_surf"), foot, base_valid, base_idx)
    db_s = gaussian_filter(d_base, 1.5, mode="nearest")
    db_grad = np.hypot(
        gaussian_filter(db_s, 1.0, order=(1, 0), mode="nearest"),
        gaussian_filter(db_s, 1.0, order=(0, 1), mode="nearest"),
    ).astype(np.float32)
    del d_base, db_s

    tmi_up_raw = load_external_band(root / "data/external/geodawn_extensions_u8.tif", 4, zero_is_nodata=True)
    tmi_up_ok = foot & np.isfinite(tmi_up_raw)
    tmi_up, _ = fill_nearest_and_winsorize(tmi_up_raw, foot)
    del tmi_up_raw
    tu_s = gaussian_filter(tmi_up, 1.5, mode="nearest")
    tu_grad = np.hypot(
        gaussian_filter(tu_s, 1.0, order=(1, 0), mode="nearest"),
        gaussian_filter(tu_s, 1.0, order=(0, 1), mode="nearest"),
    ).astype(np.float32)
    tu_grad[~tmi_up_ok] = 0.0
    del tmi_up, tu_s

    r_sub = (
        0.50 * rank01(gaussian_filter(np.abs(g_slope), 1.5, mode="nearest"), foot)
        + 0.30 * rank01(db_grad, foot)
        + 0.20 * rank01(tu_grad, foot)
    ).astype(np.float32)
    del g_slope, db_grad

    # Project down-dip along +u_down at d in {0, 5, 10, 14} px (0..1400 m basinward)
    sub_dip_f = r_sub[fy, fx].copy()
    for d_px in (5.0, 10.0, 14.0):
        shifted = sample_along_vector_foot(r_sub, fy_f, fx_f, uy_f, ux_f, d_px)
        sub_dip_f = np.maximum(sub_dip_f, shifted)
    sub_dip = np.zeros(SHAPE, dtype=np.float32)
    sub_dip[fy, fx] = sub_dip_f * edge_taper[fy, fx]
    mm[LINE_NAMES.index("SUB_DIP")] = rank01(sub_dip, foot)
    del r_sub, sub_dip_f, sub_dip
    log("Built Line 2 (SUB_DIP) in", round(time.time() - t0, 1), "s")

    # ------------------------------------------------------------------
    # Line 3: LIDAR_SCARP — Road-Vetoed Single-Facing 1 m 3DEP LiDAR Piedmont Scarplet
    # ------------------------------------------------------------------
    lidar_path = root / "data/external/lidar_scarp_features_u8.tif"
    li_valid = load_external_band(lidar_path, LIDAR_BANDS.index("valid") + 1, zero_is_nodata=False)
    lidar_ok = foot & np.isfinite(li_valid) & (li_valid > 0)
    del li_valid
    step_max = np.nan_to_num(load_external_band(lidar_path, LIDAR_BANDS.index("step_max") + 1), nan=0.0)
    upface = np.nan_to_num(load_external_band(lidar_path, LIDAR_BANDS.index("upface_max") + 1), nan=0.0)
    dnface = np.nan_to_num(load_external_band(lidar_path, LIDAR_BANDS.index("downface_max") + 1), nan=0.0)
    coh100 = np.nan_to_num(load_external_band(lidar_path, LIDAR_BANDS.index("coh100") + 1), nan=0.0)

    face_pol = np.abs(upface - dnface) / (upface + dnface + 2.0)
    del upface, dnface
    scarp_raw = step_max * face_pol * (0.25 + 0.75 * (coh100 / 255.0))
    del step_max, face_pol, coh100

    # Smooth gently at 100m, gate by gentle-to-moderate piedmont window (0.3..15 deg) & road veto
    scarp_sm = gaussian_filter(scarp_raw, 1.0, mode="nearest")
    del scarp_raw
    road_d = load_external_band(root / "data/external/tiger_road_distance_m.tif", 1, zero_is_nodata=False)
    road_d = np.where(np.isfinite(road_d), road_d, 1000.0).astype(np.float32)
    w_road = np.clip((road_d - 80.0) / 170.0, 0.08, 1.0).astype(np.float32)
    del road_d

    pied_env = trapezoid_window(ss, 0.3, 1.0, 12.0, 18.0)
    scarp_field = scarp_sm * pied_env * w_road * edge_taper
    # Also apply light monotonic 300m elevation drop check so two-bank flat washes are attenuated
    scarp_field[fy, fx] *= (0.35 + 0.65 * mono_step)
    scarp_field[~lidar_ok] = 0.0
    scarp_crest = soft_crest_nms(scarp_field, fy_f, fx_f, uy_f, ux_f, lidar_ok, off_crest_scale=0.15)
    mm[LINE_NAMES.index("LIDAR_SCARP")] = rank01(scarp_crest, lidar_ok)
    del scarp_sm, w_road, pied_env, scarp_field, scarp_crest, mono_step
    log("Built Line 3 (LIDAR_SCARP) in", round(time.time() - t0, 1), "s")

    # ------------------------------------------------------------------
    # Line 4: BLIND_CONDUIT — Upward-Continued Magnetic Tilt-Zero + Hydrothermal Alteration Conduit
    # + CTRL (generic tmi_hg rank control matching H31-U/H31-X)
    # ------------------------------------------------------------------
    hg, _ = fill_nearest_and_winsorize(load_cached_band(root, "tmi_hg"), foot, base_valid, base_idx)
    vg, _ = fill_nearest_and_winsorize(load_cached_band(root, "tmi_vg"), foot, base_valid, base_idx)
    mm[LINE_NAMES.index("CTRL")] = rank01(np.where(foot, np.abs(hg), 0.0), foot)

    hg_abs = np.abs(gaussian_filter(hg, 1.2, mode="nearest"))
    vg_sm = gaussian_filter(vg, 1.2, mode="nearest")
    eps_m = float(np.percentile(hg_abs[foot], 15.0)) + 1e-6
    tilt = np.arctan2(vg_sm, hg_abs + eps_m).astype(np.float32)
    del hg, vg, vg_sm

    # Normal to tilt contour for magnetic crest localization
    tgy = gaussian_filter(tilt, 1.2, order=(1, 0), mode="nearest")
    tgx = gaussian_filter(tilt, 1.2, order=(0, 1), mode="nearest")
    tmag = np.hypot(tgy, tgx) + 1e-6
    mny_f = (tgy / tmag)[fy, fx].astype(np.float32)
    mnx_f = (tgx / tmag)[fy, fx].astype(np.float32)
    del tgy, tgx, tmag

    tilt_zero = np.exp(-np.abs(tilt) / 0.35).astype(np.float32)
    del tilt
    mag_contact = tilt_zero * np.sqrt(
        np.maximum(rank01(hg_abs, foot) * np.where(tmi_up_ok, rank01(tu_grad, tmi_up_ok), rank01(hg_abs, foot)), 0.0)
    )
    del hg_abs, tu_grad, tilt_zero

    # Hydrothermal alteration: potassic K/Th excess + playa-debiased |grad(cond_surf)| + GDR paleo/2m corridor
    rad_path = root / "data/external/geodawn_rad_u8.tif"
    rad_k = load_external_band(rad_path, RAD_BANDS.index("K") + 1, zero_is_nodata=True)
    rad_th = load_external_band(rad_path, RAD_BANDS.index("Th") + 1, zero_is_nodata=True)
    rad_ok = foot & np.isfinite(rad_k) & np.isfinite(rad_th)
    rk = rank01(np.nan_to_num(rad_k, nan=0.0), rad_ok)
    rth = rank01(np.nan_to_num(rad_th, nan=0.0), rad_ok)
    k_excess = np.where(rad_ok, np.clip(rk - 0.65 * rth, 0.0, 1.0), 0.25).astype(np.float32)
    del rad_k, rad_th, rk, rth

    cond, _ = fill_nearest_and_winsorize(load_cached_band(root, "cond_surf"), foot, base_valid, base_idx)
    cond_s = gaussian_filter(cond, 1.5, mode="nearest")
    cond_grad = np.hypot(
        gaussian_filter(cond_s, 1.0, order=(1, 0), mode="nearest"),
        gaussian_filter(cond_s, 1.0, order=(0, 1), mode="nearest"),
    ).astype(np.float32)
    # Debias flat 0-degree evaporite playa pans
    playa_debias = np.clip(ss / 1.5, 0.25, 1.0).astype(np.float32)
    r_cond = rank01(cond_grad * playa_debias, foot)
    del cond, cond_s, cond_grad, playa_debias

    with rasterio.open(root / "data/external/derived_gdr_paleo_100m_u8.tif") as ds:
        paleo = (ds.read(1) > 0) & foot
    with rasterio.open(root / "data/external/derived_gdr_2m_probes_100m_u8.tif") as ds:
        probes = (ds.read(1) > 0) & foot
    d_hydro = distance_transform_edt(~(paleo | probes)).astype(np.float32)
    hydro_corridor = np.exp(-0.5 * (d_hydro / 25.0) ** 2).astype(np.float32)
    del paleo, probes, d_hydro

    hydro_mod = (0.45 + 0.25 * k_excess + 0.20 * r_cond + 0.10 * hydro_corridor).astype(np.float32)
    blind_raw = mag_contact * hydro_mod * edge_taper
    blind_crest = soft_crest_nms(blind_raw, fy_f, fx_f, mny_f, mnx_f, foot, off_crest_scale=0.12)
    mm[LINE_NAMES.index("BLIND_CONDUIT")] = rank01(blind_crest, foot)
    del mag_contact, hydro_mod, k_excess, r_cond, hydro_corridor, blind_raw, blind_crest, mny_f, mnx_f
    log("Built Line 4 (BLIND_CONDUIT) + CTRL in", round(time.time() - t0, 1), "s")

    # ------------------------------------------------------------------
    # Line 5: TECT_CTX — Crustal Transtensional & Microseismic Loading Context
    # ------------------------------------------------------------------
    g2, _ = fill_nearest_and_winsorize(load_cached_band(root, "geod_2ndinv"), foot, base_valid, base_idx)
    gsh, _ = fill_nearest_and_winsorize(load_cached_band(root, "geod_shearrate"), foot, base_valid, base_idx)
    deq, _ = fill_nearest_and_winsorize(load_cached_band(root, "deq_n100a15"), foot, base_valid, base_idx)
    tect = (
        0.45 * rank01(gaussian_filter(np.abs(g2), 3.0, mode="nearest"), foot)
        + 0.35 * rank01(gaussian_filter(np.abs(gsh), 3.0, mode="nearest"), foot)
        + 0.20 * rank01(gaussian_filter(np.log1p(np.maximum(deq, 0.0)), 3.0, mode="nearest"), foot)
    ).astype(np.float32)
    tect[~foot] = 0.0
    mm[LINE_NAMES.index("TECT_CTX")] = rank01(tect, foot)
    del g2, gsh, deq, tect, z, zs, s, ss, uy, ux, uy_f, ux_f, ty_f, tx_f
    mm.flush()
    gc.collect()

    stats_out = {}
    for idx, name in enumerate(LINE_NAMES):
        v = np.asarray(mm[idx])[foot]
        stats_out[name] = {
            "min": float(v.min()),
            "max": float(v.max()),
            "mean": float(v.mean()),
            "p99": float(np.percentile(v, 99.0)),
            "frac_positive": float((v > 0).mean()),
        }
    meta = {
        "lane": "KANLER-H1",
        "shape": list(SHAPE),
        "lines": LINE_NAMES,
        "elapsed_sec": round(time.time() - t0, 2),
        "stats": stats_out,
        "catalogue_inputs_used": False,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    log("All lines cached cleanly in", meta["elapsed_sec"], "s")
    return meta


def open_lines_memmap(root: Path) -> np.memmap:
    return np.memmap(
        root / ".cache" / "kanler_h1" / "lines.f32",
        dtype=np.float32,
        mode="r",
        shape=(len(LINE_NAMES),) + SHAPE,
    )


def get_line(root: Path, name: str) -> np.ndarray:
    mm = open_lines_memmap(root)
    return np.asarray(mm[LINE_NAMES.index(name)], dtype=np.float32).copy()


# ----------------------------------------------------------------------
# Unsupervised Surfaces (EXP-1)
# ----------------------------------------------------------------------
def build_unsupervised_surfaces(root: Path, foot: np.ndarray) -> dict[str, np.ndarray]:
    """Construct frozen EXP-1 candidate & control surfaces without touching labels."""
    j_asym = get_line(root, "J_ASYM")
    sub_dip = get_line(root, "SUB_DIP")
    lidar = get_line(root, "LIDAR_SCARP")
    blind = get_line(root, "BLIND_CONDUIT")
    tect = get_line(root, "TECT_CTX")

    # H1_JASYM: Asymmetric scale-normalized piedmont break + down-dip hanging-wall boost
    s_jasym = j_asym * (0.55 + 0.45 * sub_dip)
    s_jasym[~foot] = 0.0

    # H1_MULTI: Multi-regime concordance across mountain-front piedmont (J_ASYM),
    # 1m 3DEP LiDAR piedmont scarplets (LIDAR_SCARP), and blind intrabasin magnetic/hydrothermal
    # conduits (BLIND_CONDUIT), each corroborated by hanging-wall dip gravity (SUB_DIP) & strain context.
    r_geom = j_asym * (0.55 + 0.45 * sub_dip)
    r_lidar = lidar * (0.50 + 0.50 * sub_dip)
    r_blind = blind * (0.45 + 0.55 * sub_dip)

    # Soft multi-regime envelope + synergy bonus where >=2 independent physical regimes co-fire
    top1 = np.maximum(np.maximum(r_geom, 0.88 * r_lidar), 0.76 * r_blind)
    synergy = (
        0.22 * np.sqrt(np.maximum(r_geom * r_lidar, 0.0))
        + 0.18 * np.sqrt(np.maximum(r_geom * r_blind, 0.0))
        + 0.18 * np.sqrt(np.maximum(r_lidar * r_blind, 0.0))
    )
    s_multi = (top1 + synergy) * (0.85 + 0.15 * tect)
    s_multi[~foot] = 0.0

    return {
        "H1_JASYM": rank01(s_jasym, foot),
        "H1_MULTI": rank01(s_multi, foot),
        "REF_H31X": get_line(root, "REF_H31X"),
        "CTRL": get_line(root, "CTRL"),
        "SLOPE": get_line(root, "SLOPE"),
    }


# ----------------------------------------------------------------------
# Single-Feature Leakage Canary (Protocol Rule 4)
# ----------------------------------------------------------------------
def single_feature_auc(vals: np.ndarray, pos_mask: np.ndarray, foot: np.ndarray, seed: int = 20261026) -> float:
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(pos_mask & foot)
    neg_all = np.flatnonzero(foot & ~pos_mask)
    neg = rng.choice(neg_all, size=min(200_000, neg_all.size), replace=False)
    y = np.r_[np.ones(pos.size, dtype=np.int8), np.zeros(neg.size, dtype=np.int8)]
    s = np.r_[vals.ravel()[pos], vals.ravel()[neg]].astype(np.float64)
    s = np.where(np.isfinite(s), s, 0.0)
    return float(roc_auc_score(y, s))


def run_leakage_canary(root: Path) -> dict:
    foot, cat, _, off_sgmc, _ = load_base_masks(root)
    rows = []
    for name in LINE_NAMES:
        v = get_line(root, name)
        auc_cat = single_feature_auc(v, cat, foot)
        auc_sgmc = single_feature_auc(v, off_sgmc, foot)
        eff_max = max(auc_cat, 1.0 - auc_cat, auc_sgmc, 1.0 - auc_sgmc)
        rows.append({
            "feature": name,
            "kind": "physical_line",
            "auc_catalogue": round(auc_cat, 6),
            "auc_off_catalogue_sgmc": round(auc_sgmc, 6),
            "max_directional_auc": round(eff_max, 6),
            "leakage_flagged": bool(eff_max > 0.90),
        })
        log(f"Canary {name:<15} AUC_cat={auc_cat:.4f} AUC_sgmc={auc_sgmc:.4f} flag={eff_max > 0.90}")

    surfs = build_unsupervised_surfaces(root, foot)
    for name in ("H1_JASYM", "H1_MULTI"):
        v = surfs[name]
        auc_cat = single_feature_auc(v, cat, foot)
        auc_sgmc = single_feature_auc(v, off_sgmc, foot)
        eff_max = max(auc_cat, 1.0 - auc_cat, auc_sgmc, 1.0 - auc_sgmc)
        rows.append({
            "feature": name,
            "kind": "composite_surface",
            "auc_catalogue": round(auc_cat, 6),
            "auc_off_catalogue_sgmc": round(auc_sgmc, 6),
            "max_directional_auc": round(eff_max, 6),
            "leakage_flagged": bool(eff_max > 0.90),
        })
        log(f"Canary {name:<15} AUC_cat={auc_cat:.4f} AUC_sgmc={auc_sgmc:.4f} flag={eff_max > 0.90}")

    report = {
        "evidence_class": "COMPUTED",
        "protocol_rule": "Single-feature AUC > 0.90 implies catalogue leakage until proven otherwise",
        "auc_ceiling": 0.90,
        "all_pass": bool(all(not r["leakage_flagged"] for r in rows)),
        "rows": rows,
    }
    out_p = root / "evidence" / "kanler_h1" / "canary.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(report, indent=2) + "\n")
    if not report["all_pass"]:
        raise RuntimeError("LEAKAGE CANARY FAILED: at least one feature exceeded 0.90 AUC!")
    return report


# ----------------------------------------------------------------------
# Dot Emission Engines: Greedy 2.8-px Poisson Disk & Exact 300m Submodular CELF
# ----------------------------------------------------------------------
def emit_poisson_disk(
    surf: np.ndarray,
    allowed: np.ndarray,
    budget: int = BUDGET,
    min_dist_px: float = 2.8,
    max_pool: int = 380_000,
) -> np.ndarray:
    cand_mask = allowed & (surf > 0)
    flat_idx = np.flatnonzero(cand_mask)
    if flat_idx.size == 0:
        return np.zeros(surf.shape, dtype=bool)
    scores = surf.ravel()[flat_idx]
    if flat_idx.size > max_pool:
        part = np.argpartition(scores, -max_pool)[-max_pool:]
        flat_idx = flat_idx[part]
        scores = scores[part]
    order = np.argsort(-scores, kind="mergesort")
    flat_idx = flat_idx[order]

    h, w = surf.shape
    ys = (flat_idx // w).astype(np.int32)
    xs = (flat_idx % w).astype(np.int32)

    r_pad = int(np.ceil(min_dist_px)) + 1
    yy, xx = np.mgrid[-r_pad : r_pad + 1, -r_pad : r_pad + 1]
    disk_mask = (yy * yy + xx * xx) <= (min_dist_px * min_dist_px + 1e-9)
    dy_b = yy[disk_mask].astype(np.int32)
    dx_b = xx[disk_mask].astype(np.int32)

    blocked = np.zeros((h + 2 * r_pad, w + 2 * r_pad), dtype=bool)
    out = np.zeros((h, w), dtype=bool)
    accepted = 0
    for i in range(ys.size):
        py = int(ys[i]) + r_pad
        px = int(xs[i]) + r_pad
        if not blocked[py, px]:
            out[py - r_pad, px - r_pad] = True
            blocked[py + dy_b, px + dx_b] = True
            accepted += 1
            if accepted >= budget:
                break
    return out


def emit_celf_submodular_300m(
    surf: np.ndarray,
    allowed: np.ndarray,
    budget: int = BUDGET,
    min_dist_px: float = 2.4,
    gamma: float = 2.5,
    max_pool: int = 300_000,
) -> np.ndarray:
    """Exact Minoux-CELF lazy greedy maximizer of expected 300m triangular-kernel TP_w
    `F(D) = sum_g q(g) * max_{x in D} max(0, 1 - ||x - g||_2 / 3.0)` with Triangle-Inequality
    exact untouched fast-path."""
    # Sharpened positive-rank density q(g) = surf^gamma on footprint so fault crests dominate background
    q = np.where(surf > 0, np.power(np.clip(surf, 0.0, 1.0), gamma), 0.0).astype(np.float32)

    # 300 m (3.0 px) triangular kernel
    yy3, xx3 = np.mgrid[-3:4, -3:4]
    dist3 = np.hypot(yy3, xx3)
    k7 = np.maximum(0.0, 1.0 - dist3 / 3.0).astype(np.float32)
    k_mask = k7 > 0.0
    dy_k = yy3[k_mask].astype(np.int32)
    dx_k = xx3[k_mask].astype(np.int32)
    kw_k = k7[k_mask].astype(np.float32)

    # Exact initial standalone marginal gain via 2D convolution (when cov == 0 everywhere)
    init_gain_map = ndi.convolve(q, k7, mode="constant", cval=0.0)

    cand_mask = allowed & (surf > 0)
    flat_idx = np.flatnonzero(cand_mask)
    if flat_idx.size == 0:
        return np.zeros(surf.shape, dtype=bool)
    init_scores = init_gain_map.ravel()[flat_idx]
    if flat_idx.size > max_pool:
        part = np.argpartition(init_scores, -max_pool)[-max_pool:]
        flat_idx = flat_idx[part]
        init_scores = init_scores[part]

    h, w = surf.shape
    ys = (flat_idx // w).astype(np.int32)
    xs = (flat_idx % w).astype(np.int32)

    pad = 6
    q_pad = np.pad(q, pad, mode="constant", constant_values=0.0)
    cov_pad = np.zeros((h + 2 * pad, w + 2 * pad), dtype=np.float32)
    blocked_pad = np.zeros((h + 2 * pad, w + 2 * pad), dtype=bool)
    touched_pad = np.zeros((h + 2 * pad, w + 2 * pad), dtype=bool)

    r_b = int(np.ceil(min_dist_px))
    yyb, xxb = np.mgrid[-r_b : r_b + 1, -r_b : r_b + 1]
    b_mask = (yyb * yyb + xxb * xxb) <= (min_dist_px * min_dist_px + 1e-9)
    dy_b = yyb[b_mask].astype(np.int32)
    dx_b = xxb[b_mask].astype(np.int32)

    # Two 3-px kernels overlap on truth pixel g iff ||x1 - x2||_2 < 6.0 px
    yyt, xxt = np.mgrid[-5:6, -5:6]
    t_mask = (yyt * yyt + xxt * xxt) < 36
    dy_t = yyt[t_mask].astype(np.int32)
    dx_t = xxt[t_mask].astype(np.int32)

    heap = [(-float(init_scores[i]), int(i), 0) for i in range(ys.size)]
    heapq.heapify(heap)

    out = np.zeros((h, w), dtype=bool)
    accepted = 0
    step = 0
    while heap and accepted < budget:
        neg_gain, idx, computed_at = heapq.heappop(heap)
        py = int(ys[idx]) + pad
        px = int(xs[idx]) + pad
        if blocked_pad[py, px]:
            continue
        # Exact fast-path: if never touched by a <6px neighbor, initial gain is still exact!
        if computed_at == step or not touched_pad[py, px]:
            out[py - pad, px - pad] = True
            ky = py + dy_k
            kx = px + dx_k
            cov_pad[ky, kx] = np.maximum(cov_pad[ky, kx], kw_k)
            blocked_pad[py + dy_b, px + dx_b] = True
            touched_pad[py + dy_t, px + dx_t] = True
            accepted += 1
            step += 1
        else:
            ky = py + dy_k
            kx = px + dx_k
            inc = np.maximum(0.0, kw_k - cov_pad[ky, kx])
            new_gain = float(np.dot(q_pad[ky, kx], inc))
            next_top = -heap[0][0] if heap else -1.0
            if new_gain >= next_top:
                out[py - pad, px - pad] = True
                cov_pad[ky, kx] = np.maximum(cov_pad[ky, kx], kw_k)
                blocked_pad[py + dy_b, px + dx_b] = True
                touched_pad[py + dy_t, px + dx_t] = True
                accepted += 1
                step += 1
            else:
                heapq.heappush(heap, (-new_gain, idx, step))
    return out


# ----------------------------------------------------------------------
# EXP-2: Fold-Local Positive-Unlabeled (SAR-PU) Monotonic Out-of-Fold Calibrator
# ----------------------------------------------------------------------
def _pu_features_at_indices(root: Path, idx_flat: np.ndarray) -> np.ndarray:
    """7-column structural feature matrix on pixel indices (strictly non-negative ranks in [0, 1])."""
    mm = open_lines_memmap(root)
    j = np.asarray(mm[LINE_NAMES.index("J_ASYM")], dtype=np.float32).ravel()[idx_flat]
    sd = np.asarray(mm[LINE_NAMES.index("SUB_DIP")], dtype=np.float32).ravel()[idx_flat]
    li = np.asarray(mm[LINE_NAMES.index("LIDAR_SCARP")], dtype=np.float32).ravel()[idx_flat]
    bl = np.asarray(mm[LINE_NAMES.index("BLIND_CONDUIT")], dtype=np.float32).ravel()[idx_flat]
    tc = np.asarray(mm[LINE_NAMES.index("TECT_CTX")], dtype=np.float32).ravel()[idx_flat]
    return np.column_stack([
        j,
        li,
        bl,
        j * sd,
        li * sd,
        bl * sd,
        0.5 * (j + li + bl) * tc,
    ]).astype(np.float64)


def fit_nonneg_pu_weights(
    root: Path,
    train_mask: np.ndarray,
    visible_cat: np.ndarray,
    seed: int = 1026,
) -> np.ndarray:
    """Fit non-negative monotonic structural weights strictly inside `train_mask` (`buffer_px=80`),
    with SAR-PU observability propensity weighting so low-slope / blind-basin unlabeled pixels
    are not treated as confident true negatives (`IR-A8A-PU-BIAS-01`)."""
    rng = np.random.default_rng(seed)
    # Dilate visible training faults by 1 px so 1-px crest registration jitter on DEM/LiDAR is captured
    pos_zone = ndi.binary_dilation(visible_cat & train_mask, structure=np.ones((3, 3), bool)) & train_mask
    neg_zone = train_mask & (distance_transform_edt(~visible_cat) > 6.0)

    pos_idx = np.flatnonzero(pos_zone)
    neg_all = np.flatnonzero(neg_zone)
    neg_idx = rng.choice(neg_all, size=min(120_000, neg_all.size), replace=False)

    if pos_idx.size > 60_000:
        pos_idx = rng.choice(pos_idx, size=60_000, replace=False)

    X_pos = _pu_features_at_indices(root, pos_idx)
    X_neg = _pu_features_at_indices(root, neg_idx)

    # SAR-PU observability weight on unlabeled background: steep range fronts with LiDAR were heavily
    # mapped in QFFD (high observability -> unlabeled is very likely true negative, weight ~1.0),
    # whereas flat un-LiDARed basins had low pre-2023 QFFD mapping observability (weight ~0.45).
    mm = open_lines_memmap(root)
    slope_neg = np.asarray(mm[LINE_NAMES.index("SLOPE")], dtype=np.float32).ravel()[neg_idx]
    lidar_neg = np.asarray(mm[LINE_NAMES.index("LIDAR_SCARP")], dtype=np.float32).ravel()[neg_idx] > 0
    obs_propensity = 0.45 + 0.40 * slope_neg + 0.15 * lidar_neg.astype(np.float64)

    X = np.vstack([X_pos, X_neg])
    y = np.r_[np.ones(X_pos.shape[0]), np.zeros(X_neg.shape[0])]
    # Balanced class total weight with observability propensity on unlabeled negatives
    w_pos = np.full(X_pos.shape[0], 1.0 / max(X_pos.shape[0], 1), dtype=np.float64)
    w_neg = obs_propensity / max(obs_propensity.sum(), 1e-9)
    sample_w = np.r_[w_pos, w_neg]

    # Optimize L2-regularized weighted logistic loss with w >= 0.02 on primary physical channels
    # (bias parameter b = params[0] unconstrained; weights params[1:] >= 0)
    init = np.array([-1.5, 2.0, 1.2, 0.8, 1.5, 1.0, 0.8, 0.5], dtype=np.float64)
    bounds = [(None, None)] + [(0.05, 12.0)] * 3 + [(0.0, 12.0)] * 4

    def loss_and_grad(params):
        b = params[0]
        w = params[1:]
        z = b + X @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))
        # Numerically stable logistic loss + L2 penalty
        pos_part = -y * np.log(np.maximum(p, 1e-12)) - (1.0 - y) * np.log(np.maximum(1.0 - p, 1e-12))
        reg = 1e-3 * float(np.dot(w, w))
        loss = float(np.dot(sample_w, pos_part)) + reg
        diff = sample_w * (p - y)
        gb = float(diff.sum())
        gw = X.T @ diff + 2e-3 * w
        return loss, np.r_[gb, gw]

    res = minimize(loss_and_grad, init, jac=True, method="L-BFGS-B", bounds=bounds)
    return res.x


def predict_pu_surface(root: Path, params: np.ndarray, foot: np.ndarray) -> np.ndarray:
    fy_fx = np.flatnonzero(foot)
    X = _pu_features_at_indices(root, fy_fx)
    w = params[1:]
    # Linear logit rank is strictly monotonic with logistic probability and avoids exp saturation ties
    scores_f = (X @ w).astype(np.float32)
    out = np.zeros(SHAPE, dtype=np.float32)
    out[foot] = scores_f
    return rank01(out, foot)


# ----------------------------------------------------------------------
# Evaluation Helpers (Shared `gems57-pooled-hide-v2` + Random-Component Confirmation + SGMC)
# ----------------------------------------------------------------------
def evaluate_surfaces_on_folds(
    surfaces_by_arm: dict[str, np.ndarray | list[np.ndarray]],
    folds: list[dict],
    foot: np.ndarray,
    emitter: str = "poisson",
) -> dict:
    """Evaluate static or fold-specific OOF surfaces on `gems57-pooled-hide-v2`."""
    terms: dict[str, np.ndarray] = {}
    per_fold: dict[str, list[dict]] = {arm: [] for arm in surfaces_by_arm}
    emit_fn = emit_poisson_disk if emitter == "poisson" else emit_celf_submodular_300m

    for f_idx, f in enumerate(folds):
        d_vis = distance_transform_edt(~f["visible"]).astype(np.float32)
        allowed = foot & (d_vis > B_PX)
        for arm, surf_or_list in surfaces_by_arm.items():
            surf = surf_or_list[f_idx] if isinstance(surf_or_list, list) else surf_or_list
            dots = emit_fn(surf, allowed & (surf > 0), budget=BUDGET)
            pred = dots.astype(np.float32)
            res, trm = ev.evaluate(pred, f, foot)
            terms[arm] = trm if arm not in terms else terms[arm] + trm
            dti_f = float(vmetric.dti_from_components(res["tpw"], res["fpw"], res["fnw"]))
            per_fold[arm].append({
                "fold": int(f["fold"]),
                "dti": dti_f,
                "n_truth": int(res["n_truth"]),
                "emitted_in_region": int(res["n_emitted"]),
            })
            log(f"  fold={f['fold']} arm={arm:<14} emitter={emitter:<7} dti={dti_f:.4f} truth={res['n_truth']}")
    return {"terms": terms, "per_fold": per_fold}


def random_component_split(cat: np.ndarray, foot: np.ndarray, seed: int = CONFIRM_SEED) -> dict:
    comp, n = ndi.label(cat, np.ones((3, 3), bool))
    rng = np.random.default_rng(seed)
    hidden_ids = np.flatnonzero(rng.random(n + 1) < 0.5)
    hidden_ids = hidden_ids[hidden_ids > 0]
    hidden = np.isin(comp, hidden_ids) & cat
    visible = cat & ~hidden
    train_mask = foot & (distance_transform_edt(~hidden) > 30.0)
    return {
        "fold": 9,
        "region": foot.copy(),
        "train": train_mask,
        "visible": visible,
        "masked_known": visible,
        "truth": hidden,
        "receipt": {
            "split": "random-component-50pct",
            "seed": seed,
            "components": int(n),
            "hidden_components": int(hidden_ids.size),
            "truth_px": int(hidden.sum()),
            "visible_px": int(visible.sum()),
        },
    }


def score_off_catalogue_sgmc(root: Path, dots: np.ndarray, foot: np.ndarray, off_sgmc: np.ndarray) -> dict:
    raw_slope = load_cached_band(root, "det_elev_slope")
    slope = np.where(np.isfinite(raw_slope), raw_slope, 0.0).astype(np.float32)
    pied_mask = foot & (slope <= 6.0)
    mtn_mask = foot & (slope > 6.0)

    full = vmetric.dti_exact(dots.astype(np.float64), off_sgmc, valid=foot)
    pied = vmetric.dti_exact((dots & pied_mask).astype(np.float64), off_sgmc & pied_mask, valid=pied_mask)
    mtn = vmetric.dti_exact((dots & mtn_mask).astype(np.float64), off_sgmc & mtn_mask, valid=mtn_mask)
    return {
        "evidence_class": "COMPUTED off-catalogue USGS-SGMC diagnostic (not leaderboard truth)",
        "full_off_catalogue": {
            "dti": float(full["dti"]),
            "tpw": float(full["tp"]),
            "fpw": float(full["fp"]),
            "n_truth": int(off_sgmc.sum()),
            "n_dots": int(dots.sum()),
        },
        "piedmont_slope_le_6deg": {
            "dti": float(pied["dti"]),
            "n_truth": int((off_sgmc & pied_mask).sum()),
            "n_dots": int((dots & pied_mask).sum()),
            "dot_share": float((dots & pied_mask).sum() / max(int(dots.sum()), 1)),
        },
        "mountain_slope_gt_6deg": {
            "dti": float(mtn["dti"]),
            "n_truth": int((off_sgmc & mtn_mask).sum()),
            "n_dots": int((dots & mtn_mask).sum()),
            "dot_share": float((dots & mtn_mask).sum() / max(int(dots.sum()), 1)),
        },
    }
