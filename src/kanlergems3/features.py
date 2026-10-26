"""Streaming memory-safe (<350 MB RSS) multi-physics feature builder for L-K3-CADG-SUBMOD.

Strict leakage invariants:
1. All cached features in ``features_fp.f32`` are 100% label-free: neither ``labels.tif``
   nor ``existing_faults.tif`` nor finite values of ``sample_submission.tif`` are ever
   read here (``sample_submission.tif`` supplies ``np.isfinite`` footprint mask only).
2. ``gdr_wellspring_in_footprint.csv`` explicitly asserts ``dist_known_fault_px`` is ignored.
3. Fold-visible structural continuation features (``compute_visible_continuation``)
   accept ONLY ``fold["visible"]`` (or internal sub-fold ``visible_sub``) and never touch
   withheld segments.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import struct
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy.ndimage import (
    binary_erosion,
    convolve,
    distance_transform_edt,
    gaussian_filter,
    label as ndi_label,
)

SENTINEL_FLOOR = -1e30

CORE_19_BANDS = [
    (1, "mag_anom"),
    (2, "rtp"),
    (3, "tmi_hg"),
    (4, "geod_2ndinv"),
    (5, "iso_grav_anom_slope"),
    (6, "tc"),
    (7, "geod_shearrate"),
    (8, "geod_dilaterate"),
    (9, "tmi_vg"),
    (10, "deq_n100a15"),
    (11, "iso_grav_anom_vg"),
    (12, "det_elev"),
    (13, "iso_grav_anom"),
    (14, "tmi"),
    (15, "depth_to_base_surf"),
    (16, "ieq_n100a15"),
    (17, "cond_surf"),
    (18, "iso_grav_anom_hg"),
    (19, "det_elev_slope"),
]

FORBIDDEN_POINT_COLUMNS = frozenset(
    {"dist_known_fault_px", "fault_id", "qfault_dist", "label", "labels", "existing_faults"}
)


def _fill_nearest(arr: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
    bad = ~valid_mask
    if not bad.any():
        return arr.astype(np.float32, copy=False)
    _, idx = distance_transform_edt(bad, return_distances=True, return_indices=True)
    out = arr.astype(np.float32, copy=True)
    out[bad] = out[idx[0][bad], idx[1][bad]]
    return out


def _grad_mag(arr: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    sm = gaussian_filter(arr.astype(np.float32), sigma=sigma)
    gy, gx = np.gradient(sm)
    return np.hypot(gy, gx).astype(np.float32)


def _hessian_ridge(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Concave-down positive ridge eigenvalue (-lambda_min) at scale sigma."""
    sm = gaussian_filter(arr.astype(np.float32), sigma=sigma)
    gy, gx = np.gradient(sm)
    hyy, hyx = np.gradient(gy)
    hxy, hxx = np.gradient(gx)
    hxy = 0.5 * (hxy + hyx)
    rad = np.sqrt((0.5 * (hxx - hyy)) ** 2 + hxy * hxy)
    lam_min = 0.5 * (hxx + hyy) - rad
    return np.maximum(-lam_min, 0.0).astype(np.float32)


def _robust_pos_scale(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    v = arr[fp]
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med))) * 1.4826 + 1e-6
    return np.maximum((arr - med) / mad, 0.0).astype(np.float32)


def _lonlat_nad83_to_rc(
    lons: list[float],
    lats: list[float],
    affine_tr: Any,
    shape: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not lons:
        empty_i = np.zeros(0, dtype=np.int64)
        empty_b = np.zeros(0, dtype=bool)
        return empty_i, empty_i, empty_b
    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    x_arr = np.asarray(xs, dtype=np.float64)
    y_arr = np.asarray(ys, dtype=np.float64)
    cols = np.floor((x_arr - affine_tr.c) / affine_tr.a).astype(np.int64)
    rows = np.floor((y_arr - affine_tr.f) / affine_tr.e).astype(np.int64)
    ok = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    return rows[ok], cols[ok], ok


def _parse_2m_probes_dbf(zip_path: Path, affine_tr: Any, shape: tuple[int, int]) -> np.ndarray:
    """Parse INGENIOUS 2m temperature survey DBF (F2mDAB & T2m) with stdlib struct."""
    imp_dab = np.zeros(shape, dtype=np.float32)
    if not zip_path.is_file():
        return imp_dab
    with zipfile.ZipFile(zip_path) as zf:
        dbf_name = next(n for n in zf.namelist() if n.lower().endswith(".dbf"))
        buf = zf.read(dbf_name)
    numrec, lenhdr, lenrec = struct.unpack("<4xIHH20x", buf[:32])
    fields: list[tuple[str, int, int]] = []
    pos = 32
    offset = 1
    while buf[pos] != 0x0D:
        fname = buf[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        if fname.lower() in FORBIDDEN_POINT_COLUMNS:
            raise ValueError(f"Forbidden column in 2m probe DBF: {fname}")
        flen = buf[pos + 16]
        fields.append((fname, offset, flen))
        offset += flen
        pos += 32
    fmap = {name: (off, flen) for name, off, flen in fields}
    lons, lats, scores = [], [], []
    for i in range(numrec):
        rec = buf[lenhdr + i * lenrec : lenhdr + (i + 1) * lenrec]
        if not rec or rec[0:1] == b"*":
            continue
        try:
            lat = float(rec[fmap["LatDegreeN"][0] : fmap["LatDegreeN"][0] + fmap["LatDegreeN"][1]].strip())
            lon = float(rec[fmap["LongDegree"][0] : fmap["LongDegree"][0] + fmap["LongDegree"][1]].strip())
            dab_raw = rec[fmap["F2mDAB"][0] : fmap["F2mDAB"][0] + fmap["F2mDAB"][1]].strip()
            t2m_raw = rec[fmap["T2m"][0] : fmap["T2m"][0] + fmap["T2m"][1]].strip()
            dab = float(dab_raw) if dab_raw else 0.0
            t2m = float(t2m_raw) if t2m_raw else 15.0
            if not np.isfinite(dab) or dab < -50:
                dab = 0.0
            val = max(0.0, dab) + 0.35 * max(0.0, t2m - 22.0)
            if val > 0.0:
                lons.append(lon)
                lats.append(lat)
                scores.append(val)
        except (ValueError, KeyError):
            continue
    rr, cc, ok = _lonlat_nad83_to_rc(lons, lats, affine_tr, shape)
    sc_ok = np.asarray(scores, dtype=np.float32)[ok]
    for r, c, v in zip(rr, cc, sc_ok):
        if v > imp_dab[r, c]:
            imp_dab[r, c] = v
    return imp_dab


def _parse_paleo_geothermal_zip(zip_path: Path, affine_tr: Any, shape: tuple[int, int]) -> np.ndarray:
    """Parse INGENIOUS Paleo-Geothermal sinter/tufa/travertine compilation."""
    imp = np.zeros(shape, dtype=np.float32)
    if not zip_path.is_file():
        return imp
    with zipfile.ZipFile(zip_path) as zf:
        cname = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        with io.TextIOWrapper(zf.open(cname), encoding="utf-8-sig", errors="replace") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames is not None
            for col in reader.fieldnames:
                if col.lower() in FORBIDDEN_POINT_COLUMNS:
                    raise ValueError(f"Forbidden column in paleo CSV: {col}")
            lons, lats, weights = [], [], []
            for row in reader:
                try:
                    lon = float(row["Long_deg_NAD83"])
                    lat = float(row["Lat_deg_NAD83"])
                except (ValueError, KeyError):
                    continue
                dtype = (row.get("Deposit_type") or "").lower()
                w = 1.5 if ("sinter" in dtype or "silic" in dtype) else 1.0
                lons.append(lon)
                lats.append(lat)
                weights.append(w)
    rr, cc, ok = _lonlat_nad83_to_rc(lons, lats, affine_tr, shape)
    w_ok = np.asarray(weights, dtype=np.float32)[ok]
    np.add.at(imp, (rr, cc), w_ok)
    return np.log1p(imp).astype(np.float32)


def build_or_load_feature_cache(data_dir: Path, cache_dir: Path) -> dict[str, Any]:
    """Stream and SHA-256-hash the 61-column label-free feature memmap."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    meta_path = cache_dir / "feature_meta_v1.json"
    mmap_path = cache_dir / "features_fp_v1.f32"

    with rasterio.open(data_dir / "sample_submission.tif") as tpl:
        footprint = np.isfinite(tpl.read(1))
        shape = tpl.shape
        affine_tr = tpl.transform

    fp_idx = np.flatnonzero(footprint.ravel())
    n_fp = int(len(fp_idx))

    if meta_path.is_file() and mmap_path.is_file():
        meta = json.loads(meta_path.read_text())
        expected_bytes = n_fp * len(meta["feature_names"]) * 4
        if mmap_path.stat().st_size == expected_bytes:
            mm = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, len(meta["feature_names"])))
            return {
                "memmap": mm,
                "meta": meta,
                "footprint": footprint,
                "fp_idx": fp_idx,
                "shape": shape,
            }

    ext_dir = data_dir / "external"
    # Pre-declare exact ordered columns across Groups B (core+potential), A (geomorphic), C (decontam+hydro)
    group_b_names = [name for _, name in CORE_19_BANDS] + [
        "tmi_up150",
        "tmi_up150_grad",
        "mag_depth_persistence_150m",
        "mag_tilt_edge",
        "grav_tilt_edge",
        "basement_grad",
        "piedmont_margin_score",
        "cond_surf_grad",
    ]
    group_a_names = [
        "has_lidar",
        "lidar_ex_max",
        "lidar_step_max",
        "lidar_lapneg_max",
        "lidar_lappos_max",
        "lidar_downface_max",
        "lidar_upface_max",
        "lidar_relief",
        "lidar_coh100",
        "lidar_scarp_asymmetry",
        "lidar_asymmetric_step",
        "lidar_crest_toe_dipole",
        "lidar_scarp_sharpness",
        "topo10_slope_p90",
        "topo10_slope_max",
        "topo10_steep_frac",
        "topo10_slope_std",
        "topo10_relief_local",
        "topo10_curv_prof_absmax",
        "topo10_aspect_coherence",
        "topo10_hs_lineament",
        "topo10_hs_dog",
        "topo10_curv_dog",
        "chi_step_max",
        "chi_ksn_max",
        "chi_log10_area",
        "chi_zmean_m",
        "chi_tectonic_step_ratio",
        "det_elev_ridge_s1p2",
        "det_elev_ridge_s2p5",
    ]
    group_c_names = [
        "tiger_road_logdist",
        "lidar_step_road_decontam",
        "topo10_curv_road_decontam",
        "pluvial_shoreline_elev_dist_m",
        "pluvial_bench_mimic_score",
        "rad_K",
        "rad_Th",
        "rad_U",
        "rad_TC",
        "ext_ThK",
        "ext_UK",
        "ext_UTh",
        "rad_K_alteration_halo",
        "tmi_demag_trough",
        "probe2m_dab_s5",
        "probe2m_dab_s14",
        "gdr_thermal_upflow_s5",
        "gdr_thermal_upflow_s16",
        "paleo_sinter_tufa_s5",
        "paleo_sinter_tufa_s14",
    ]
    all_names = group_b_names + group_a_names + group_c_names
    col_index = {name: i for i, name in enumerate(all_names)}
    n_cols = len(all_names)

    mm = np.memmap(mmap_path, dtype=np.float32, mode="w+", shape=(n_fp, n_cols))
    col_hashes: dict[str, str] = {}

    def put_2d(name: str, arr2d: np.ndarray) -> None:
        vec = np.asarray(arr2d, dtype=np.float32).ravel()[fp_idx]
        mm[:, col_index[name]] = vec
        col_hashes[name] = hashlib.sha256(vec.tobytes()).hexdigest()[:16]

    def put_1d(name: str, vec1d: np.ndarray) -> None:
        vec = np.asarray(vec1d, dtype=np.float32)
        mm[:, col_index[name]] = vec
        col_hashes[name] = hashlib.sha256(vec.tobytes()).hexdigest()[:16]

    # --- 1. Core 19 geophysical/geodetic/topographic bands ---
    keep_core: dict[str, np.ndarray] = {}
    with rasterio.open(data_dir / "training_features.tif") as src:
        for b_idx, b_name in CORE_19_BANDS:
            raw = src.read(b_idx).astype(np.float32)
            valid = footprint & np.isfinite(raw) & (raw > SENTINEL_FLOOR)
            clean = _fill_nearest(raw, valid)
            put_2d(b_name, clean)
            if b_name in (
                "tmi_hg",
                "tmi_vg",
                "iso_grav_anom_hg",
                "iso_grav_anom_vg",
                "depth_to_base_surf",
                "cond_surf",
                "det_elev",
            ):
                keep_core[b_name] = clean
            del raw

    # GeoDAWN extensions (need TMI_up150 for Group B & Group C)
    with rasterio.open(ext_dir / "geodawn_extensions_u8.tif") as src:
        ext_names = ["ext_ThK", "ext_UK", "ext_UTh", "tmi_up150"]
        tmi_up150 = None
        for b_idx, b_name in enumerate(ext_names, start=1):
            q = src.read(b_idx)
            arr = _fill_nearest(q.astype(np.float32), footprint & (q > 0))
            put_2d(b_name, arr)
            if b_name == "tmi_up150":
                tmi_up150 = arr

    assert tmi_up150 is not None
    tmi_up150_grad = _grad_mag(tmi_up150, sigma=1.2)
    put_2d("tmi_up150_grad", tmi_up150_grad)
    tmi_hg_scaled = _robust_pos_scale(np.abs(keep_core["tmi_hg"]), footprint)
    tmi_up_scaled = _robust_pos_scale(tmi_up150_grad, footprint)
    put_2d("mag_depth_persistence_150m", tmi_up_scaled / (tmi_hg_scaled + 0.35))
    del tmi_hg_scaled, tmi_up_scaled, tmi_up150_grad

    put_2d(
        "mag_tilt_edge",
        np.abs(np.cos(np.arctan2(keep_core["tmi_vg"], np.abs(keep_core["tmi_hg"]) + 1e-3))),
    )
    put_2d(
        "grav_tilt_edge",
        np.abs(
            np.cos(
                np.arctan2(
                    keep_core["iso_grav_anom_vg"],
                    np.abs(keep_core["iso_grav_anom_hg"]) + 1e-3,
                )
            )
        ),
    )
    put_2d("basement_grad", _grad_mag(keep_core["depth_to_base_surf"], sigma=1.5))
    depth_pos = np.maximum(keep_core["depth_to_base_surf"], 0.0)
    put_2d(
        "piedmont_margin_score",
        np.exp(-(((np.log1p(depth_pos) - np.log1p(450.0)) / 1.15) ** 2)),
    )
    put_2d("cond_surf_grad", _grad_mag(keep_core["cond_surf"], sigma=1.5))
    put_2d("det_elev_ridge_s1p2", _hessian_ridge(keep_core["det_elev"], sigma=1.2))
    put_2d("det_elev_ridge_s2p5", _hessian_ridge(keep_core["det_elev"], sigma=2.5))
    put_2d("tmi_demag_trough", gaussian_filter(tmi_up150, 10.0) - tmi_up150)
    keep_core.clear()
    del depth_pos, tmi_up150

    # --- 2. 1 m LiDAR scarp tensor with 200 m tile-seam erosion & signed polarity asymmetry ---
    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as src:
        lidar_valid_raw = (src.read(12) > 0) & footprint
        # Erode 2 px (200 m) inside LiDAR coverage to eliminate rectangular tile-seam cliff artifacts
        lidar_valid = binary_erosion(lidar_valid_raw, iterations=2)
        has_lid_fp = lidar_valid.ravel()[fp_idx]
        put_1d("has_lidar", has_lid_fp.astype(np.float32))

        lid_map = {
            1: "lidar_ex_max",
            3: "lidar_step_max",
            4: "lidar_lapneg_max",
            5: "lidar_lappos_max",
            6: "lidar_downface_max",
            7: "lidar_upface_max",
            9: "lidar_relief",
            10: "lidar_coh100",
        }
        lid_fp: dict[str, np.ndarray] = {}
        for b_idx, b_name in lid_map.items():
            v = src.read(b_idx).ravel()[fp_idx].astype(np.float32)
            v[~has_lid_fp] = np.nan
            put_1d(b_name, v)
            lid_fp[b_name] = v

    asym = np.abs(lid_fp["lidar_downface_max"] - lid_fp["lidar_upface_max"]) / (
        lid_fp["lidar_downface_max"] + lid_fp["lidar_upface_max"] + 4.0
    )
    asym_step = lid_fp["lidar_step_max"] * (0.35 + 0.65 * asym)
    dipole = np.sqrt(np.maximum(0.0, lid_fp["lidar_lapneg_max"] * lid_fp["lidar_lappos_max"]))
    sharp = lid_fp["lidar_step_max"] / (lid_fp["lidar_relief"] + 5.0)
    put_1d("lidar_scarp_asymmetry", asym)
    put_1d("lidar_asymmetric_step", asym_step)
    put_1d("lidar_crest_toe_dipole", dipole)
    put_1d("lidar_scarp_sharpness", sharp)
    del lid_fp, asym, dipole, sharp

    # --- 3. Seamless 10 m 3DEP DEM breaklines (100% coverage across LiDAR voids) ---
    topo_names = [
        "topo10_slope_p90",
        "topo10_slope_max",
        "topo10_steep_frac",
        "topo10_slope_std",
        "topo10_relief_local",
        "topo10_curv_prof_absmax",
        "topo10_aspect_coherence",
        "topo10_hs_lineament",
    ]
    topo_keep: dict[str, np.ndarray] = {}
    with rasterio.open(ext_dir / "topo_10m_derived_100m_u8.tif") as src:
        for b_idx, b_name in enumerate(topo_names, start=1):
            q = src.read(b_idx)
            arr = _fill_nearest(q.astype(np.float32), footprint & (q > 0))
            put_2d(b_name, arr)
            if b_name in ("topo10_relief_local", "topo10_curv_prof_absmax", "topo10_hs_lineament"):
                topo_keep[b_name] = arr
    put_2d("topo10_hs_dog", topo_keep["topo10_hs_lineament"] - gaussian_filter(topo_keep["topo10_hs_lineament"], 6.0))
    put_2d(
        "topo10_curv_dog",
        topo_keep["topo10_curv_prof_absmax"] - gaussian_filter(topo_keep["topo10_curv_prof_absmax"], 6.0),
    )

    # --- 4. Fluvial chi / ksn knickzones + Lake Lahontan / Bonneville shoreline bench score ---
    with rasterio.open(ext_dir / "dem10_chi_100m_i16.tif") as src:
        chi_specs = [
            (1, "chi_step_max"),
            (3, "chi_ksn_max"),
            (4, "chi_log10_area"),
            (5, "chi_zmean_m"),
        ]
        chi_keep: dict[str, np.ndarray] = {}
        for b_idx, b_name in chi_specs:
            raw = src.read(b_idx).astype(np.float32)
            arr = _fill_nearest(raw, footprint & (raw > -30000.0))
            put_2d(b_name, arr)
            if b_name in ("chi_step_max", "chi_zmean_m"):
                chi_keep[b_name] = arr

    put_2d(
        "chi_tectonic_step_ratio",
        np.maximum(chi_keep["chi_step_max"], 0.0) / (topo_keep["topo10_relief_local"] + 10.0),
    )
    z_arr = chi_keep["chi_zmean_m"]
    d_shore = np.minimum(
        np.abs(z_arr - 1332.0),
        np.minimum(np.abs(z_arr - 1463.0), np.abs(z_arr - 1552.0)),
    ).astype(np.float32)
    put_2d("pluvial_shoreline_elev_dist_m", d_shore)
    put_2d(
        "pluvial_bench_mimic_score",
        np.exp(-d_shore / 18.0) / (1.0 + 0.01 * np.maximum(chi_keep["chi_step_max"], 0.0)),
    )
    del z_arr, d_shore, chi_keep

    # --- 5. Census TIGER/Line 2024 road-embankment decontaminant ---
    with rasterio.open(ext_dir / "tiger_road_distance_m.tif") as src:
        road_raw = src.read(1).astype(np.float32)
        road_m = _fill_nearest(np.maximum(road_raw, 0.0), footprint & np.isfinite(road_raw))
    put_2d("tiger_road_logdist", np.log1p(road_m))
    road_w_fp = (1.0 - np.exp(-road_m.ravel()[fp_idx] / 150.0)).astype(np.float32)
    put_1d("lidar_step_road_decontam", asym_step * road_w_fp)
    put_2d(
        "topo10_curv_road_decontam",
        topo_keep["topo10_curv_prof_absmax"] * (1.0 - np.exp(-road_m / 150.0)),
    )
    topo_keep.clear()
    del road_raw, road_m, road_w_fp, asym_step

    # --- 6. GeoDAWN airborne gamma-ray spectrometry ---
    with rasterio.open(ext_dir / "geodawn_rad_u8.tif") as src:
        rad_k = None
        for b_idx, b_name in enumerate(["rad_K", "rad_Th", "rad_U", "rad_TC"], start=1):
            q = src.read(b_idx)
            arr = _fill_nearest(q.astype(np.float32), footprint & (q > 0))
            put_2d(b_name, arr)
            if b_name == "rad_K":
                rad_k = arr
    assert rad_k is not None
    put_2d("rad_K_alteration_halo", rad_k - gaussian_filter(rad_k, 10.0))
    del rad_k

    # --- 7. Label-free INGENIOUS hydrothermal upflow (2m probes, spring geothermometers, sinter/tufa) ---
    imp_dab = _parse_2m_probes_dbf(
        ext_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip", affine_tr, shape
    )
    put_2d("probe2m_dab_s5", gaussian_filter(np.log1p(imp_dab), 5.0))
    put_2d("probe2m_dab_s14", gaussian_filter(np.log1p(imp_dab), 14.0))
    del imp_dab

    imp_ws = np.zeros(shape, dtype=np.float32)
    with (ext_dir / "gdr_wellspring_in_footprint.csv").open(newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames is not None
        used_cols = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c")
        assert set(used_cols).isdisjoint(FORBIDDEN_POINT_COLUMNS)
        for row in reader:
            rr, cc = int(row["row"]), int(row["col"])
            if not (0 <= rr < shape[0] and 0 <= cc < shape[1]):
                continue
            excess = []
            for k_col, base_t in (
                ("temp_c", 20.0),
                ("geothermquartz_c", 70.0),
                ("geothermchalc_c", 60.0),
                ("geothermcat_c", 75.0),
            ):
                s = row.get(k_col, "")
                if s and s != "nan":
                    try:
                        excess.append(max(0.0, float(s) - base_t))
                    except ValueError:
                        pass
            if excess:
                val = float(np.log1p(max(excess)))
                if val > imp_ws[rr, cc]:
                    imp_ws[rr, cc] = val
    put_2d("gdr_thermal_upflow_s5", gaussian_filter(imp_ws, 5.0))
    put_2d("gdr_thermal_upflow_s16", gaussian_filter(imp_ws, 16.0))
    del imp_ws

    imp_paleo = _parse_paleo_geothermal_zip(
        ext_dir / "paleo_geothermal_regional.zip", affine_tr, shape
    )
    put_2d("paleo_sinter_tufa_s5", gaussian_filter(imp_paleo, 5.0))
    put_2d("paleo_sinter_tufa_s14", gaussian_filter(imp_paleo, 14.0))
    del imp_paleo

    mm.flush()
    digest = hashlib.sha256(json.dumps(col_hashes, sort_keys=True).encode("utf-8")).hexdigest()
    meta = {
        "schema_version": 1,
        "n_footprint_pixels": n_fp,
        "n_features": n_cols,
        "feature_names": all_names,
        "groups": {
            "group_b": group_b_names,
            "group_a": group_a_names,
            "group_c": group_c_names,
        },
        "column_sha256_prefix16": col_hashes,
        "cache_digest_sha256": digest,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    mm_ro = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_cols))
    return {
        "memmap": mm_ro,
        "meta": meta,
        "footprint": footprint,
        "fp_idx": fp_idx,
        "shape": shape,
    }


def compute_visible_continuation(visible_2d: np.ndarray, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Compute strictly fold-local visible-only structural continuation fields.

    Consumes ONLY ``visible_2d`` (e.g. ``fold["visible"]`` or internal sub-fold
    ``visible_sub``). Never reads withheld segments.
    Returns 3 full-grid float32 arrays:
      - ``vis_relay_band_300_3500m``: band-passed step-over/relay zone peaking at ~1.8 km
      - ``vis_tip_propagation_lobe``: multi-scale endpoint stress halo around trace tips
      - ``vis_belt_density_2p5km``: regional 2.5 km structural fault-belt density
    """
    vis = np.asarray(visible_2d, dtype=bool) & np.asarray(footprint, dtype=bool)
    if not vis.any():
        z = np.zeros(footprint.shape, dtype=np.float32)
        return {
            "vis_relay_band_300_3500m": z,
            "vis_tip_propagation_lobe": z.copy(),
            "vis_belt_density_2p5km": z.copy(),
        }

    d_vis = distance_transform_edt(~vis).astype(np.float32)
    # Band-passed relay/step-over zone: zero on the trace (d<=2), peaks around 18 px (1.8 km)
    relay = (
        np.exp(-(((d_vis - 18.0) / 14.0) ** 2))
        * np.clip((d_vis - 2.0) / 4.0, 0.0, 1.0)
    ).astype(np.float32)

    # Identify trace tips (pixels on visible faults with <= 2 8-connected fault neighbors)
    nbr_k = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int16)
    nbr_cnt = convolve(vis.astype(np.int16), nbr_k, mode="constant", cval=0)
    comp, n_comp = ndi_label(vis, structure=np.ones((3, 3), dtype=int))
    comp_sizes = np.bincount(comp.ravel())
    # Weight tips by log1p(host segment length) so major range-front terminations project stronger lobes
    host_w = np.zeros_like(d_vis)
    if n_comp > 0:
        log_sz = np.log1p(comp_sizes).astype(np.float32)
        log_sz[0] = 0.0
        host_w = log_sz[comp]
    tips = vis & (nbr_cnt >= 1) & (nbr_cnt <= 2)
    tip_imp = np.where(tips, host_w, 0.0).astype(np.float32)
    tip_lobe = (
        0.65 * gaussian_filter(tip_imp, sigma=8.0)
        + 0.35 * gaussian_filter(tip_imp, sigma=20.0)
    ).astype(np.float32)

    belt = gaussian_filter(vis.astype(np.float32), sigma=25.0).astype(np.float32)
    return {
        "vis_relay_band_300_3500m": relay,
        "vis_tip_propagation_lobe": tip_lobe,
        "vis_belt_density_2p5km": belt,
    }
