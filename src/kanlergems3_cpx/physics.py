"""Label-free coincident-ridge physics channels for L-K3-CPX-EDTI.

Physical hypothesis (H-CPX-1): concealed Quaternary normal faults that are
missing from the USGS/INGENIOUS catalogue still offset (a) density boundaries
(isostatic gravity), (b) magnetic basement (TMI/RTP), (c) the conductive
basement surface and (d) the actively extending strain fabric (geodetic
second invariant / shear). No single field is specific - lithologic contacts
mimic each one - but a *spatially coincident, orientation-agreeing* ridge in
independent physics is far harder for a non-fault contact to mimic. These
channels therefore encode multi-scale Hessian ridge strength, cross-scale
"worm" persistence, tilt-derivative edges, and gravity-vs-magnetic gradient
orientation agreement, computed ONLY from the 19 competition bands.
Neither labels.tif nor existing_faults.tif nor sample values are read
(sample supplies the finite footprint mask only, as in the shared cache).

Named non-fault mimic: buried caldera ring margins and tilted ash-flow tuff
hogbacks can align gravity, magnetic and strain gradients without a
through-going Quaternary fault.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.kanlergems3.features import (  # noqa: E402
    CORE_19_BANDS,
    SENTINEL_FLOOR,
    _fill_nearest,
    _hessian_ridge,
    _robust_pos_scale,
)

# Ordered physics channels (all label-free, from the 19 bands only).
PHYSICS_NAMES = [
    "cpx_ridge_grav_s1", "cpx_ridge_grav_s2p5", "cpx_persist_grav",
    "cpx_ridge_mag_s1", "cpx_ridge_mag_s2p5", "cpx_persist_mag",
    "cpx_ridge_base_s1p5", "cpx_ridge_cond_s1p5",
    "cpx_ridge_strain_s1p5", "cpx_ridge_shear_s1p5",
    "cpx_ridge_elev_s1", "cpx_dog_grav", "cpx_dog_mag",
    "cpx_tilt_edge_mag", "cpx_orient_coincide_gm", "cpx_coincide_minrank",
]
# Channels entering the unsupervised physics coincidence score.
COINCIDENCE_PARTS = [
    "cpx_persist_grav", "cpx_persist_mag", "cpx_ridge_base_s1p5",
    "cpx_ridge_cond_s1p5", "cpx_ridge_strain_s1p5", "cpx_tilt_edge_mag",
    "cpx_orient_coincide_gm", "cpx_ridge_elev_s1",
]


def _rank01(vec: np.ndarray) -> np.ndarray:
    """Deterministic midrank percentile in [0,1] (ties broken by order)."""
    v = np.asarray(vec, dtype=np.float32)
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v), dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, len(v), dtype=np.float32)
    return ranks


def _gradients(arr: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sm = gaussian_filter(arr.astype(np.float32), sigma=sigma)
    gy, gx = np.gradient(sm)
    return gy.astype(np.float32), gx.astype(np.float32), np.hypot(gy, gx).astype(np.float32)


def build_or_load_physics_cache(data_dir: Path, cache_dir: Path) -> dict[str, Any]:
    """Stream the 16-column label-free physics memmap over footprint cells."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    meta_path = cache_dir / "physics_meta_v1.json"
    mmap_path = cache_dir / "physics_fp_v1.f32"

    with rasterio.open(data_dir / "sample_submission.tif") as tpl:
        footprint = np.isfinite(tpl.read(1))
        shape = tpl.shape
    fp_idx = np.flatnonzero(footprint.ravel())
    n_fp = int(len(fp_idx))

    if meta_path.is_file() and mmap_path.is_file():
        meta = json.loads(meta_path.read_text())
        if meta.get("feature_names") == PHYSICS_NAMES and \
                mmap_path.stat().st_size == n_fp * len(PHYSICS_NAMES) * 4:
            mm = np.memmap(mmap_path, dtype=np.float32, mode="r",
                           shape=(n_fp, len(PHYSICS_NAMES)))
            return {"memmap": mm, "meta": meta, "footprint": footprint,
                    "fp_idx": fp_idx, "shape": shape}

    band_index = {name: idx for idx, name in CORE_19_BANDS}
    need = ["iso_grav_anom", "tmi", "depth_to_base_surf", "cond_surf",
            "geod_2ndinv", "geod_shearrate", "det_elev", "tmi_hg", "tmi_vg"]
    fields: dict[str, np.ndarray] = {}
    with rasterio.open(data_dir / "training_features.tif") as src:
        for name in need:
            raw = src.read(band_index[name]).astype(np.float32)
            valid = footprint & np.isfinite(raw) & (raw > SENTINEL_FLOOR)
            fields[name] = _fill_nearest(raw, valid)
            del raw

    out2d: dict[str, np.ndarray] = {}
    # Multi-scale ridges + cross-scale persistence (worm proxy).
    for tag, field in (("grav", fields["iso_grav_anom"]), ("mag", fields["tmi"])):
        r1 = _hessian_ridge(field, 1.0)
        r25 = _hessian_ridge(field, 2.5)
        out2d[f"cpx_ridge_{tag}_s1"] = _robust_pos_scale(r1, footprint)
        out2d[f"cpx_ridge_{tag}_s2p5"] = _robust_pos_scale(r25, footprint)
        a = np.zeros(shape, dtype=np.float32)
        b = np.zeros(shape, dtype=np.float32)
        a.ravel()[fp_idx] = _rank01(r1.ravel()[fp_idx])
        b.ravel()[fp_idx] = _rank01(r25.ravel()[fp_idx])
        out2d[f"cpx_persist_{tag}"] = np.minimum(a, b)
        del r1, r25, a, b
    out2d["cpx_ridge_base_s1p5"] = _robust_pos_scale(
        _hessian_ridge(fields["depth_to_base_surf"], 1.5), footprint)
    out2d["cpx_ridge_cond_s1p5"] = _robust_pos_scale(
        _hessian_ridge(fields["cond_surf"], 1.5), footprint)
    out2d["cpx_ridge_strain_s1p5"] = _robust_pos_scale(
        _hessian_ridge(fields["geod_2ndinv"], 1.5), footprint)
    out2d["cpx_ridge_shear_s1p5"] = _robust_pos_scale(
        _hessian_ridge(fields["geod_shearrate"], 1.5), footprint)
    out2d["cpx_ridge_elev_s1"] = _robust_pos_scale(
        _hessian_ridge(fields["det_elev"], 1.0), footprint)

    # Difference-of-Gaussians edge energy.
    for tag, field in (("grav", fields["iso_grav_anom"]), ("mag", fields["tmi"])):
        dog = np.abs(gaussian_filter(field, 1.0) - gaussian_filter(field, 3.0))
        out2d[f"cpx_dog_{tag}"] = _robust_pos_scale(dog.astype(np.float32), footprint)
        del dog

    # Tilt-derivative edge: |tilt| near zero crossing with strong horizontal gradient.
    hg = np.maximum(fields["tmi_hg"], 0.0)
    tilt = np.arctan2(fields["tmi_vg"], hg + 1e-6)
    hg_rank = np.zeros(shape, dtype=np.float32)
    hg_rank.ravel()[fp_idx] = _rank01(hg.ravel()[fp_idx])
    out2d["cpx_tilt_edge_mag"] = (np.exp(-np.abs(tilt) / 0.35) * hg_rank).astype(np.float32)
    del hg, tilt, hg_rank

    # Gravity-vs-magnetic gradient orientation agreement (axial, doubled angle).
    gy_g, gx_g, gm_g = _gradients(fields["iso_grav_anom"], 1.5)
    gy_m, gx_m, gm_m = _gradients(fields["tmi"], 1.5)
    cos2 = ((gx_g * gx_m + gy_g * gy_m) ** 2 - (gx_g * gy_m - gy_g * gx_m) ** 2) / \
        ((gm_g * gm_m) ** 2 + 1e-12)  # cos(2*dtheta) in [-1,1]
    agree = (0.5 * (np.clip(cos2, -1.0, 1.0) + 1.0)).astype(np.float32)
    g_rank = np.zeros(shape, dtype=np.float32)
    m_rank = np.zeros(shape, dtype=np.float32)
    g_rank.ravel()[fp_idx] = _rank01(gm_g.ravel()[fp_idx])
    m_rank.ravel()[fp_idx] = _rank01(gm_m.ravel()[fp_idx])
    out2d["cpx_orient_coincide_gm"] = agree * np.minimum(g_rank, m_rank)
    del gy_g, gx_g, gm_g, gy_m, gx_m, gm_m, cos2, agree, g_rank, m_rank

    # Weakest-link coincidence across the independent physics parts.
    parts = []
    for name in COINCIDENCE_PARTS:
        r = np.zeros(shape, dtype=np.float32)
        r.ravel()[fp_idx] = _rank01(out2d[name].ravel()[fp_idx])
        parts.append(r)
    out2d["cpx_coincide_minrank"] = np.minimum.reduce(parts)
    del parts, fields

    mm = np.memmap(mmap_path, dtype=np.float32, mode="w+", shape=(n_fp, len(PHYSICS_NAMES)))
    col_hashes: dict[str, str] = {}
    for j, name in enumerate(PHYSICS_NAMES):
        vec = np.nan_to_num(out2d[name].ravel()[fp_idx], nan=0.0,
                              posinf=0.0, neginf=0.0).astype(np.float32)
        mm[:, j] = vec
        col_hashes[name] = hashlib.sha256(vec.tobytes()).hexdigest()[:16]
    mm.flush()
    meta = {"feature_names": PHYSICS_NAMES, "coincidence_parts": COINCIDENCE_PARTS,
            "label_free": True, "source": "training_features.tif 19 bands only",
            "column_sha256_16": col_hashes}
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    mm_r = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, len(PHYSICS_NAMES)))
    return {"memmap": mm_r, "meta": meta, "footprint": footprint,
            "fp_idx": fp_idx, "shape": shape}


def physics_coincidence_surface(phys: dict[str, Any], domain: np.ndarray) -> np.ndarray:
    """Unsupervised coincidence score: mean rank of COINCIDENCE_PARTS in domain."""
    mm, meta = phys["memmap"], phys["meta"]
    fp_idx, footprint = phys["fp_idx"], phys["footprint"]
    col = {n: i for i, n in enumerate(meta["feature_names"])}
    dom_fp = np.flatnonzero(np.asarray(domain, bool).ravel()[fp_idx])
    acc = np.zeros(len(dom_fp), dtype=np.float32)
    for name in meta["coincidence_parts"]:
        acc += _rank01(np.asarray(mm[dom_fp, col[name]], dtype=np.float32))
    acc /= len(meta["coincidence_parts"])
    out = np.zeros(footprint.shape, dtype=np.float32)
    out.ravel()[fp_idx[dom_fp]] = acc
    return out


def rank_fusion(surfaces: list[np.ndarray], weights: list[float],
                domain: np.ndarray) -> np.ndarray:
    """Weighted mean of within-domain percentile ranks (label-free fusion)."""
    domain = np.asarray(domain, bool)
    idx = np.flatnonzero(domain)
    acc = np.zeros(len(idx), dtype=np.float32)
    wsum = float(sum(weights))
    for surf, w in zip(surfaces, weights):
        acc += (w / wsum) * _rank01(np.nan_to_num(
            np.asarray(surf, dtype=np.float32).ravel()[idx], nan=0.0))
    out = np.zeros(domain.shape, dtype=np.float32)
    out.ravel()[idx] = acc
    return out
