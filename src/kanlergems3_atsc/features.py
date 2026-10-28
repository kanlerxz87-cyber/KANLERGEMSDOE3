"""Streaming (<450 MB RSS) feature builder for L-K3-ATSC-SUBMOD.

Reuses the cached 58-column label-free feature memmap from ``src.kanlergems3.features``
without rebuilding, appends 22 novel label-free dip-offset hanging-wall tomography &
GeoDAWN radon/seam deconfounding columns into a separate float32 memmap, and computes
8-azimuth structural corridor integrals and fold-visible tip/relay interactions.
"""
from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import (
    binary_dilation,
    convolve,
    distance_transform_edt,
    gaussian_filter,
    map_coordinates,
)
from scipy.special import logit

from src.kanlergems3.features import build_or_load_feature_cache

ATSC_EXTRA_VERSION = "kanlergems3-atsc-extra-v1"

ATSC_GROUP_D_NAMES: list[str] = [
    "dip_grav_hg_p3",
    "dip_grav_hg_p7",
    "dip_tmi_up150_hg_p5",
    "dip_coupl_scarp_grav3",
    "dip_coupl_scarp_mag5",
    "hw_fw_depth_jump_600m",
    "hw_fw_cond_asymmetry_600m",
    "hw_fw_f2m_asymmetry_700m",
    "hw_fw_grav_jump_800m",
    "geod_transtension_index",
    "strike_align_grav_topo",
    "dem10_scarp_prominence_dog",
]

ATSC_GROUP_E_NAMES: list[str] = [
    "rad_uth_dog_2_10",
    "rad_uk_dog_2_10",
    "rad_kth_dog_2_10",
    "rad_cross_fault_k_jump",
    "rad_cross_fault_th_jump",
    "geodawn_seam_prox",
    "rail_road_corridor_veto",
    "flat_playa_indicator",
    "piedmont_sweetspot_prior",
    "chi_cross_drainage_break",
]

STAGE2_CORRIDOR_NAMES: list[str] = [
    "s2_p1_raw",
    "s2_corr_max_1km",
    "s2_corr_max_2p6km",
    "s2_corr_bilateral_min_1km",
    "s2_corr_bilateral_min_2p6km",
    "s2_corr_tip_asym_2p6km",
    "s2_ortho_1km",
    "s2_anisotropy_ratio_1km",
    "s2_anisotropy_ratio_2p6km",
    "s2_crest_conc_300m",
    "s2_crest_conc_800m",
    "s2_log_odds_dog_1p2_7",
    "s2_basin_extensional_strike_align",
    "s2_strain_x_corridor",
    "s2_dip_grav_x_corridor",
    "s2_has_lidar",
    "s2_ctx_depth_base",
    "s2_ctx_det_elev_slope",
    "s2_ctx_topo10_relief",
    "s2_ctx_flat_playa",
    "s2_ctx_road_logdist",
    "s2_ctx_piedmont_sweetspot",
]

STAGE2_TIP_NAMES: list[str] = [
    "vis_tip_lobe_300_3500m",
    "vis_tip_x_s2corr_2p6km",
    "vis_relay_band_400_3000m",
    "vis_relay_x_s2corr_1km",
]

def _extract_fast_cols(
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
) -> dict[str, np.ndarray]:
    """Read frequently accessed 1D columns in one sequential pass (~180 MB RAM) to avoid strided mmap scans."""
    bmap = {n: i for i, n in enumerate(base_meta["feature_names"])}
    emap = {n: i for i, n in enumerate(extra_meta["extra_feature_names"])}
    b_keys = [
        "has_lidar",
        "depth_to_base_surf",
        "det_elev_slope",
        "topo10_relief_local",
        "tiger_road_logdist",
        "pluvial_shoreline_elev_dist_m",
        "iso_grav_anom_hg",
        "tmi_up150_grad",
    ]
    e_keys = [
        "geod_transtension_index",
        "dip_grav_hg_p3",
        "flat_playa_indicator",
        "piedmont_sweetspot_prior",
        "geodawn_seam_prox",
    ]
    n_fp = base_mm.shape[0]
    out = {k: np.empty(n_fp, dtype=np.float32) for k in b_keys + e_keys}
    b_idx = np.asarray([bmap[k] for k in b_keys], dtype=np.intp)
    e_idx = np.asarray([emap[k] for k in e_keys], dtype=np.intp)
    step = 500_000
    for s in range(0, n_fp, step):
        e = min(n_fp, s + step)
        xb = np.array(base_mm[s:e], copy=False)[:, b_idx]
        xe = np.array(extra_mm[s:e], copy=False)[:, e_idx]
        for j, k in enumerate(b_keys):
            out[k][s:e] = xb[:, j]
        for j, k in enumerate(e_keys):
            out[k][s:e] = xe[:, j]
    return out


# 8 azimuths in [0, pi): 0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5 deg
_AZIMUTHS_RAD = [k * np.pi / 8.0 for k in range(8)]


def _col_to_2d(
    mm: np.memmap,
    col_idx: int,
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    *,
    fill_outside: bool = True,
) -> np.ndarray:
    arr = np.zeros(footprint.shape, dtype=np.float32)
    vals = np.asarray(mm[:, col_idx], dtype=np.float32)
    finite = np.isfinite(vals)
    if not finite.all():
        vals = np.where(finite, vals, 0.0)
    arr.ravel()[fp_idx] = vals
    if fill_outside:
        bad = ~footprint
        if bad.any():
            nearest = distance_transform_edt(bad, return_distances=False, return_indices=True)
            arr[bad] = arr[tuple(nearest[:, bad])]
    return arr


def _sample_along_dip(
    field_2d: np.ndarray,
    ny_2d: np.ndarray,
    nx_2d: np.ndarray,
    lag_px: float,
) -> np.ndarray:
    """Bilinearly sample ``field_2d`` at `(r + lag_px * ny, c + lag_px * nx)` in row chunks."""
    H, W = field_2d.shape
    out = np.empty((H, W), dtype=np.float32)
    step = 512
    for r0 in range(0, H, step):
        r1 = min(H, r0 + step)
        rr, cc = np.mgrid[r0:r1, 0:W].astype(np.float32)
        coords_y = np.clip(rr + lag_px * ny_2d[r0:r1], 0.0, H - 1.0)
        coords_x = np.clip(cc + lag_px * nx_2d[r0:r1], 0.0, W - 1.0)
        out[r0:r1] = map_coordinates(
            field_2d, [coords_y, coords_x], order=1, mode="nearest", prefilter=False
        )
    return out


def _detect_geodawn_block_seams(data_dir: Path, footprint: np.ndarray) -> np.ndarray:
    """Detect survey-compilation block boundaries purely from label-free raster coverage & step edges."""
    ext_dir = data_dir / "external"
    seam = np.zeros(footprint.shape, dtype=bool)
    with rasterio.open(ext_dir / "geodawn_rad_u8.tif") as src:
        q_tc = src.read(4)
        valid_rad = (q_tc > 0) & footprint
    # Coverage edge inside footprint
    cov_edge = binary_dilation(~valid_rad, iterations=1) & valid_rad & footprint
    seam |= cov_edge
    # Straight N-S or E-W compilation tie seams (>6 km persistent derivative jump on TC)
    tc_f = q_tc.astype(np.float32)
    bad = ~valid_rad
    if bad.any() and valid_rad.any():
        idx = distance_transform_edt(bad, return_distances=False, return_indices=True)
        tc_f[bad] = tc_f[tuple(idx[:, bad])]
    dy = np.abs(np.diff(tc_f, axis=0, prepend=tc_f[:1, :]))
    dx = np.abs(np.diff(tc_f, axis=1, prepend=tc_f[:, :1]))
    # Smooth strictly along E-W for dy jumps, N-S for dx jumps
    ew_line = gaussian_filter(dy, sigma=(0.5, 18.0))
    ns_line = gaussian_filter(dx, sigma=(18.0, 0.5))
    thr_ew = float(np.percentile(ew_line[footprint], 99.6))
    thr_ns = float(np.percentile(ns_line[footprint], 99.6))
    seam |= ((ew_line >= thr_ew) | (ns_line >= thr_ns)) & footprint
    if not seam.any():
        return np.zeros(footprint.shape, dtype=np.float32)
    d_seam_m = distance_transform_edt(~seam).astype(np.float32) * 100.0
    return np.exp(-d_seam_m / 400.0).astype(np.float32)


def build_or_load_atsc_cache(data_dir: Path, cache_dir: Path) -> dict[str, Any]:
    """Load 58-col base memmap + build/load 22-col ATSC float32 memmap (<400 MB RSS)."""
    base = build_or_load_feature_cache(data_dir, cache_dir)
    base_mm: np.memmap = base["memmap"]
    base_meta: dict[str, Any] = base["meta"]
    footprint: np.ndarray = base["footprint"]
    fp_idx: np.ndarray = base["fp_idx"]
    n_fp = int(footprint.sum())

    extra_names = ATSC_GROUP_D_NAMES + ATSC_GROUP_E_NAMES
    n_extra = len(extra_names)
    extra_mmap_path = cache_dir / "atsc_extra_22col_f32.mmap"
    extra_meta_path = cache_dir / "atsc_extra_22col_meta.json"

    if extra_mmap_path.is_file() and extra_meta_path.is_file():
        emeta = json.loads(extra_meta_path.read_text())
        if (
            emeta.get("version") == ATSC_EXTRA_VERSION
            and emeta.get("base_digest") == base_meta["cache_digest_sha256"]
            and emeta.get("extra_feature_names") == extra_names
            and extra_mmap_path.stat().st_size == n_fp * n_extra * 4
        ):
            extra_mm = np.memmap(extra_mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_extra))
            return {
                **base,
                "extra_memmap": extra_mm,
                "extra_meta": emeta,
                "fast_cols": _extract_fast_cols(base_mm, base_meta, extra_mm, emeta),
                "all_feature_names": base_meta["feature_names"] + extra_names,
            }

    bmap = {n: i for i, n in enumerate(base_meta["feature_names"])}
    emap = {n: i for i, n in enumerate(extra_names)}
    extra_mm = np.memmap(extra_mmap_path, dtype=np.float32, mode="w+", shape=(n_fp, n_extra))
    col_hashes: dict[str, str] = {}

    def put_2d(name: str, arr2d: np.ndarray) -> None:
        vec = np.asarray(arr2d, dtype=np.float32).ravel()[fp_idx]
        vec = np.where(np.isfinite(vec), vec, 0.0).astype(np.float32)
        extra_mm[:, emap[name]] = vec
        col_hashes[name] = hashlib.sha256(vec.tobytes()).hexdigest()[:16]

    def put_1d(name: str, vec1d: np.ndarray) -> None:
        vec = np.asarray(vec1d, dtype=np.float32)
        vec = np.where(np.isfinite(vec), vec, 0.0).astype(np.float32)
        extra_mm[:, emap[name]] = vec
        col_hashes[name] = hashlib.sha256(vec.tobytes()).hexdigest()[:16]

    # 1. Basin-inward unit dip vector n_basin from smoothed depth_to_base_surf (fallback -grad(det_elev))
    depth_2d = _col_to_2d(base_mm, bmap["depth_to_base_surf"], footprint, fp_idx)
    det_elev_2d = _col_to_2d(base_mm, bmap["det_elev"], footprint, fp_idx)
    d_smooth = gaussian_filter(depth_2d, sigma=8.0)
    dy_b = gaussian_filter(d_smooth, sigma=1.0, order=(1, 0))
    dx_b = gaussian_filter(d_smooth, sigma=1.0, order=(0, 1))
    mag_b = np.hypot(dy_b, dx_b)

    z_smooth = gaussian_filter(det_elev_2d, sigma=6.0)
    dy_z = -gaussian_filter(z_smooth, sigma=1.0, order=(1, 0))
    dx_z = -gaussian_filter(z_smooth, sigma=1.0, order=(0, 1))
    mag_z = np.hypot(dy_z, dx_z)

    use_b = mag_b > 2.5
    ny = np.where(use_b, dy_b / np.maximum(mag_b, 1e-5), dy_z / np.maximum(mag_z, 1e-5)).astype(np.float32)
    nx = np.where(use_b, dx_b / np.maximum(mag_b, 1e-5), dx_z / np.maximum(mag_z, 1e-5)).astype(np.float32)
    del d_smooth, dy_b, dx_b, mag_b, z_smooth

    # Group D: Basinward dip-offset hanging-wall wedge tomography
    grav_hg_2d = _col_to_2d(base_mm, bmap["iso_grav_anom_hg"], footprint, fp_idx)
    dip_g3 = _sample_along_dip(grav_hg_2d, ny, nx, +3.0)
    dip_g7 = _sample_along_dip(grav_hg_2d, ny, nx, +7.0)
    put_2d("dip_grav_hg_p3", dip_g3)
    put_2d("dip_grav_hg_p7", dip_g7)
    del grav_hg_2d

    tmi150_g_2d = _col_to_2d(base_mm, bmap["tmi_up150_grad"], footprint, fp_idx)
    dip_m5 = _sample_along_dip(tmi150_g_2d, ny, nx, +5.0)
    put_2d("dip_tmi_up150_hg_p5", dip_m5)
    del tmi150_g_2d

    topo10_slope_2d = _col_to_2d(base_mm, bmap["topo10_slope_p90"], footprint, fp_idx)
    topo10_curv_2d = _col_to_2d(base_mm, bmap["topo10_curv_prof_absmax"], footprint, fp_idx)
    scarp_10m = np.maximum(topo10_curv_2d, 0.0)
    put_2d("dip_coupl_scarp_grav3", np.sqrt(scarp_10m * np.maximum(dip_g3, 0.0)))
    put_2d("dip_coupl_scarp_mag5", np.sqrt(scarp_10m * np.maximum(dip_m5, 0.0)))
    put_2d(
        "dem10_scarp_prominence_dog",
        topo10_slope_2d - gaussian_filter(topo10_slope_2d, sigma=6.0),
    )
    del dip_g3, dip_g7, dip_m5, scarp_10m, topo10_curv_2d

    hw_d = _sample_along_dip(depth_2d, ny, nx, +3.0)
    fw_d = _sample_along_dip(depth_2d, ny, nx, -3.0)
    put_2d("hw_fw_depth_jump_600m", hw_d - fw_d)
    del hw_d, fw_d

    cond_2d = _col_to_2d(base_mm, bmap["cond_surf"], footprint, fp_idx)
    put_2d(
        "hw_fw_cond_asymmetry_600m",
        _sample_along_dip(cond_2d, ny, nx, +4.0) - _sample_along_dip(cond_2d, ny, nx, -4.0),
    )
    del cond_2d

    f2m_2d = _col_to_2d(base_mm, bmap["probe2m_dab_s5"], footprint, fp_idx)
    put_2d(
        "hw_fw_f2m_asymmetry_700m",
        _sample_along_dip(f2m_2d, ny, nx, +5.0) - _sample_along_dip(f2m_2d, ny, nx, -5.0),
    )
    del f2m_2d

    grav_2d = _col_to_2d(base_mm, bmap["iso_grav_anom"], footprint, fp_idx)
    put_2d(
        "hw_fw_grav_jump_800m",
        _sample_along_dip(grav_2d, ny, nx, -4.0) - _sample_along_dip(grav_2d, ny, nx, +4.0),
    )
    ggy = gaussian_filter(grav_2d, sigma=2.0, order=(1, 0))
    ggx = gaussian_filter(grav_2d, sigma=2.0, order=(0, 1))
    gmag = np.hypot(ggy, ggx)
    cos_align = np.abs(dy_z * ggy + dx_z * ggx) / np.maximum(mag_z * gmag, 1e-5)
    put_2d("strike_align_grav_topo", cos_align)
    del grav_2d, ggy, ggx, gmag, cos_align, dy_z, dx_z, mag_z, det_elev_2d

    dil_fp = np.asarray(base_mm[:, bmap["geod_dilaterate"]], dtype=np.float32)
    shr_fp = np.asarray(base_mm[:, bmap["geod_shearrate"]], dtype=np.float32)
    # Shift dilaterate above its 10th percentile so extensional/transtensional zones stay positive
    dil_pos = np.maximum(dil_fp - float(np.percentile(dil_fp, 15.0)), 0.0)
    shr_pos = np.maximum(shr_fp, 0.0)
    put_1d("geod_transtension_index", np.sqrt(dil_pos * shr_pos))
    del dil_fp, shr_fp, dil_pos, shr_pos

    # Group E: GeoDAWN Radon/Potassic DoG + 4-block seam deconfounding + habitat controls
    uth_2d = _col_to_2d(base_mm, bmap["ext_UTh"], footprint, fp_idx)
    put_2d("rad_uth_dog_2_10", gaussian_filter(uth_2d, 1.5) - gaussian_filter(uth_2d, 10.0))
    del uth_2d

    uk_2d = _col_to_2d(base_mm, bmap["ext_UK"], footprint, fp_idx)
    put_2d("rad_uk_dog_2_10", gaussian_filter(uk_2d, 1.5) - gaussian_filter(uk_2d, 10.0))
    del uk_2d

    rad_k_2d = _col_to_2d(base_mm, bmap["rad_K"], footprint, fp_idx)
    rad_th_2d = _col_to_2d(base_mm, bmap["rad_Th"], footprint, fp_idx)
    kth_ratio = rad_k_2d / (rad_th_2d + 5.0)
    put_2d("rad_kth_dog_2_10", gaussian_filter(kth_ratio, 1.5) - gaussian_filter(kth_ratio, 10.0))
    put_2d(
        "rad_cross_fault_k_jump",
        np.abs(_sample_along_dip(rad_k_2d, ny, nx, +3.0) - _sample_along_dip(rad_k_2d, ny, nx, -3.0)),
    )
    put_2d(
        "rad_cross_fault_th_jump",
        np.abs(_sample_along_dip(rad_th_2d, ny, nx, +3.0) - _sample_along_dip(rad_th_2d, ny, nx, -3.0)),
    )
    del rad_k_2d, rad_th_2d, kth_ratio, ny, nx

    put_2d("geodawn_seam_prox", _detect_geodawn_block_seams(data_dir, footprint))

    road_log_fp = np.asarray(base_mm[:, bmap["tiger_road_logdist"]], dtype=np.float32)
    road_m_fp = np.expm1(np.maximum(road_log_fp, 0.0))
    asym_fp = np.asarray(base_mm[:, bmap["lidar_scarp_asymmetry"]], dtype=np.float32)
    asym_clean = np.where(np.isfinite(asym_fp), asym_fp, 0.5)
    put_1d("rail_road_corridor_veto", np.exp(-road_m_fp / 120.0) * (1.0 - asym_clean))
    del road_log_fp, road_m_fp, asym_fp, asym_clean

    slope_fp = np.asarray(base_mm[:, bmap["det_elev_slope"]], dtype=np.float32)
    depth_fp = np.asarray(base_mm[:, bmap["depth_to_base_surf"]], dtype=np.float32)
    relief_fp = np.asarray(base_mm[:, bmap["topo10_relief_local"]], dtype=np.float32)
    flat_playa = np.exp(-np.maximum(slope_fp, 0.0) / 1.5) * np.clip((depth_fp - 250.0) / 500.0, 0.0, 1.0)
    put_1d("flat_playa_indicator", flat_playa)

    sweetspot = np.exp(-(((np.maximum(depth_fp, 0.0) - 450.0) / 550.0) ** 2)) * np.exp(
        -(((relief_fp - 45.0) / 110.0) ** 2)
    )
    put_1d("piedmont_sweetspot_prior", sweetspot)
    del slope_fp, depth_fp, relief_fp, flat_playa, sweetspot

    chi_step_fp = np.maximum(np.asarray(base_mm[:, bmap["chi_step_max"]], dtype=np.float32), 0.0)
    topo_s_fp = np.maximum(topo10_slope_2d.ravel()[fp_idx], 0.0)
    put_1d("chi_cross_drainage_break", chi_step_fp / (topo_s_fp + 2.0))
    del chi_step_fp, topo_s_fp, topo10_slope_2d, depth_2d

    extra_mm.flush()
    digest = hashlib.sha256(json.dumps(col_hashes, sort_keys=True).encode()).hexdigest()
    emeta = {
        "version": ATSC_EXTRA_VERSION,
        "base_digest": base_meta["cache_digest_sha256"],
        "extra_digest_sha256": digest,
        "n_footprint": n_fp,
        "n_extra_features": n_extra,
        "extra_feature_names": extra_names,
        "groups": {
            "group_d": ATSC_GROUP_D_NAMES,
            "group_e": ATSC_GROUP_E_NAMES,
        },
        "column_hashes": col_hashes,
    }
    extra_meta_path.write_text(json.dumps(emeta, indent=2) + "\n")
    del extra_mm
    gc.collect()

    extra_ro = np.memmap(extra_mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_extra))
    return {
        **base,
        "extra_memmap": extra_ro,
        "extra_meta": emeta,
        "fast_cols": _extract_fast_cols(base_mm, base_meta, extra_ro, emeta),
        "all_feature_names": base_meta["feature_names"] + extra_names,
    }


def _shifted_add_into(dst: np.ndarray, src_pad: np.ndarray, pad: int, dy: int, dx: int) -> None:
    H, W = dst.shape
    dst += src_pad[pad + dy : pad + dy + H, pad + dx : pad + dx + W]


def compute_stage2_corridor_features(
    p1_2d: np.ndarray,
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    base_mm: np.memmap,
    base_meta: dict[str, Any],
    extra_mm: np.memmap,
    extra_meta: dict[str, Any],
    fast_cols: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """Compute 22 Stage-2 8-azimuth structural corridor & context features (<180 MB peak RAM)."""
    H, W = footprint.shape
    n_fp = len(fp_idx)
    fc = fast_cols if fast_cols is not None else _extract_fast_cols(base_mm, base_meta, extra_mm, extra_meta)

    p_raw = np.where(footprint & np.isfinite(p1_2d), np.clip(p1_2d, 0.0, 1.0), 0.0).astype(np.float32)
    p_fp_raw = p_raw.ravel()[fp_idx]
    has_lid_fp = fc["has_lidar"] > 0.5
    pos_lid = p_fp_raw[has_lid_fp & (p_fp_raw > 0.0)]
    pos_void = p_fp_raw[(~has_lid_fp) & (p_fp_raw > 0.0)]
    if len(pos_lid) > 1000 and len(pos_void) > 1000:
        q99_lid = float(np.percentile(pos_lid, 99.0))
        q99_void = float(np.percentile(pos_void, 99.0))
        void_gain = float(np.clip(q99_lid / max(q99_void, 1e-5), 0.85, 2.60))
    else:
        void_gain = 1.0

    # Harmonize 10 m-3DEP void amplitude with 1 m-LiDAR amplitude before 2.6 km corridor integration
    p_harm_fp = np.where(has_lid_fp, p_fp_raw, np.clip(p_fp_raw * void_gain, 0.0, 1.0)).astype(np.float32)
    p = np.zeros((H, W), dtype=np.float32)
    p.ravel()[fp_idx] = p_harm_fp

    pad = 14
    p_pad = np.pad(p, pad, mode="constant", constant_values=0.0)
    short_steps = [1, 2, 3, 4, 5]
    long_steps = [2, 4, 6, 8, 10, 13]

    # Process orthogonal azimuth pairs (a, a+4) together so we never store (8, n_fp) arrays!
    corr_max_1 = np.full(n_fp, -1.0, dtype=np.float32)
    bmin_1 = np.zeros(n_fp, dtype=np.float32)
    ortho_1 = np.zeros(n_fp, dtype=np.float32)

    corr_max_2 = np.full(n_fp, -1.0, dtype=np.float32)
    bmin_2 = np.zeros(n_fp, dtype=np.float32)
    tasym_2 = np.zeros(n_fp, dtype=np.float32)
    ortho_2 = np.zeros(n_fp, dtype=np.float32)
    best_a2 = np.zeros(n_fp, dtype=np.int8)

    fwd = np.empty((H, W), dtype=np.float32)
    bwd = np.empty((H, W), dtype=np.float32)

    def _eval_az(a_idx: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        theta = _AZIMUTHS_RAD[a_idx]
        uy, ux = float(np.cos(theta)), float(np.sin(theta))
        fwd.fill(0.0)
        bwd.fill(0.0)
        for s in short_steps:
            dy, dx = int(round(s * uy)), int(round(s * ux))
            _shifted_add_into(fwd, p_pad, pad, dy, dx)
            _shifted_add_into(bwd, p_pad, pad, -dy, -dx)
        inv1 = np.float32(1.0 / len(short_steps))
        f1 = fwd.ravel()[fp_idx] * inv1
        b1 = bwd.ravel()[fp_idx] * inv1
        c1 = np.float32(0.5) * (f1 + b1)
        bm1 = np.minimum(f1, b1)
        del f1, b1

        fwd.fill(0.0)
        bwd.fill(0.0)
        for s in long_steps:
            dy, dx = int(round(s * uy)), int(round(s * ux))
            _shifted_add_into(fwd, p_pad, pad, dy, dx)
            _shifted_add_into(bwd, p_pad, pad, -dy, -dx)
        inv2 = np.float32(1.0 / len(long_steps))
        f2 = fwd.ravel()[fp_idx] * inv2
        b2 = bwd.ravel()[fp_idx] * inv2
        c2 = np.float32(0.5) * (f2 + b2)
        bm2 = np.minimum(f2, b2)
        ta2 = np.abs(f2 - b2)
        return c1, bm1, c2, bm2, ta2

    for a in range(4):
        c1_a, bm1_a, c2_a, bm2_a, ta2_a = _eval_az(a)
        c1_b, bm1_b, c2_b, bm2_b, ta2_b = _eval_az(a + 4)

        for idx_cur, c1_cur, bm1_cur, c1_ort, c2_cur, bm2_cur, ta2_cur, c2_ort in (
            (a, c1_a, bm1_a, c1_b, c2_a, bm2_a, ta2_a, c2_b),
            (a + 4, c1_b, bm1_b, c1_a, c2_b, bm2_b, ta2_b, c2_a),
        ):
            m1 = c1_cur > corr_max_1
            corr_max_1[m1] = c1_cur[m1]
            bmin_1[m1] = bm1_cur[m1]
            ortho_1[m1] = c1_ort[m1]

            m2 = c2_cur > corr_max_2
            corr_max_2[m2] = c2_cur[m2]
            bmin_2[m2] = bm2_cur[m2]
            tasym_2[m2] = ta2_cur[m2]
            ortho_2[m2] = c2_ort[m2]
            best_a2[m2] = idx_cur

    del fwd, bwd, p_pad

    p_fp = p.ravel()[fp_idx]
    g3 = gaussian_filter(p, sigma=3.0).ravel()[fp_idx]
    g8 = gaussian_filter(p, sigma=8.0).ravel()[fp_idx]

    p_clip = np.clip(p, 1e-5, 1.0 - 1e-5)
    lo_2d = logit(p_clip).astype(np.float32)
    lo_dog = (gaussian_filter(lo_2d, sigma=1.2) - gaussian_filter(lo_2d, sigma=7.0)).ravel()[fp_idx]
    del lo_2d, p_clip

    # Regional Basin-and-Range N-S / NNE extensional azimuth alignment:
    # theta=0 corresponds to N-S (dy=cos(0)=1, dx=0), so |cos(theta - pi/12)| peaks on NNE (~N15E) strike!
    az_angles = np.asarray(_AZIMUTHS_RAD, dtype=np.float32)[best_a2]
    nne_align = np.abs(np.cos(az_angles - (np.pi / 12.0))).astype(np.float32)

    strain_fp = fc["geod_transtension_index"]
    dip_g3_fp = fc["dip_grav_hg_p3"]

    out = np.empty((n_fp, len(STAGE2_CORRIDOR_NAMES)), dtype=np.float32)
    out[:, 0] = p_fp
    out[:, 1] = corr_max_1
    out[:, 2] = corr_max_2
    out[:, 3] = bmin_1
    out[:, 4] = bmin_2
    out[:, 5] = tasym_2
    out[:, 6] = ortho_1
    out[:, 7] = (corr_max_1 + 1e-4) / (ortho_1 + 1e-4)
    out[:, 8] = (corr_max_2 + 1e-4) / (ortho_2 + 1e-4)
    out[:, 9] = (p_fp + 1e-4) / (g3 + 1e-4)
    out[:, 10] = (p_fp + 1e-4) / (g8 + 1e-4)
    out[:, 11] = lo_dog
    out[:, 12] = nne_align
    out[:, 13] = corr_max_2 * strain_fp
    out[:, 14] = corr_max_2 * np.maximum(dip_g3_fp, 0.0)
    out[:, 15] = fc["has_lidar"]
    out[:, 16] = fc["depth_to_base_surf"]
    out[:, 17] = fc["det_elev_slope"]
    out[:, 18] = fc["topo10_relief_local"]
    out[:, 19] = fc["flat_playa_indicator"]
    out[:, 20] = fc["tiger_road_logdist"]
    out[:, 21] = fc["piedmont_sweetspot_prior"]
    return out


def compute_visible_tip_bridge_features(
    visible_2d: np.ndarray,
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    s2_corr_1km_fp: np.ndarray,
    s2_corr_2p6km_fp: np.ndarray,
) -> np.ndarray:
    """Compute 4 strictly fold-visible-only tip-lobe & band-passed relay-bridge features."""
    vis = np.asarray(visible_2d, dtype=bool) & footprint
    n_fp = len(fp_idx)
    out = np.zeros((n_fp, 4), dtype=np.float32)
    if not vis.any():
        return out

    d_vis_px = distance_transform_edt(~vis).astype(np.float32)
    d_vis_m = d_vis_px * 100.0

    # Degree-1 endpoints of visible traces
    nb_kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int16)
    deg = convolve(vis.astype(np.int16), nb_kernel, mode="constant", cval=0)
    tips = vis & (deg == 1)

    if tips.any():
        # Smooth visible trace tangent orientation via structure tensor on blurred visible mask
        v_blur = gaussian_filter(vis.astype(np.float32), sigma=2.0)
        gy = gaussian_filter(v_blur, sigma=1.0, order=(1, 0))
        gx = gaussian_filter(v_blur, sigma=1.0, order=(0, 1))
        # Tangent is orthogonal to gradient: (-gx, gy)
        tmag = np.hypot(gx, gy)
        ty = -gx / np.maximum(tmag, 1e-5)
        tx = gy / np.maximum(tmag, 1e-5)

        d_tip_px, near_tip = distance_transform_edt(~tips, return_distances=True, return_indices=True)
        tr = near_tip[0]
        tc = near_tip[1]
        H, W = footprint.shape
        rr, cc = np.ogrid[:H, :W]
        vy = (rr - tr).astype(np.float32)
        vx = (cc - tc).astype(np.float32)
        vmag = np.maximum(d_tip_px.astype(np.float32), 1e-3)
        cos_ang = np.abs((vy * ty[tr, tc] + vx * tx[tr, tc]) / vmag)

        d_tip_m = d_tip_px.astype(np.float32) * 100.0
        in_band = (d_vis_m > 300.0) & (d_tip_m <= 4000.0)
        tip_lobe_2d = np.where(
            in_band,
            np.exp(-d_tip_m / 1800.0) * (cos_ang ** 3),
            0.0,
        ).astype(np.float32)
        tip_fp = tip_lobe_2d.ravel()[fp_idx]
    else:
        tip_fp = np.zeros(n_fp, dtype=np.float32)

    d_vis_fp = d_vis_m.ravel()[fp_idx]
    relay_band_fp = np.where(
        d_vis_fp > 300.0,
        np.exp(-(((d_vis_fp - 1200.0) / 900.0) ** 2)),
        0.0,
    ).astype(np.float32)

    out[:, 0] = tip_fp
    out[:, 1] = tip_fp * s2_corr_2p6km_fp
    out[:, 2] = relay_band_fp
    out[:, 3] = relay_band_fp * s2_corr_1km_fp
    return out
