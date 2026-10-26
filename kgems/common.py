"""Data access and registry-overlap helpers (memory-light: one band at a time)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import rasterio

from . import ROOT

DATA = ROOT / "data"
H, W = 3730, 3292
FEATURE_BANDS = {
    "mag_anom": 1, "rtp": 2, "tmi_hg": 3, "geod_2ndinv": 4, "iso_grav_anom_slope": 5, "tc": 6,
    "geod_shearrate": 7, "geod_dilaterate": 8, "tmi_vg": 9, "deq_n100a15": 10, "iso_grav_anom_vg": 11,
    "det_elev": 12, "iso_grav_anom": 13, "tmi": 14, "depth_to_base_surf": 15, "ieq_n100a15": 16,
    "cond_surf": 17, "iso_grav_anom_hg": 18, "det_elev_slope": 19,
}
LIDAR_BANDS = {"ex_max": 1, "ex_mean": 2, "step_max": 3, "lapneg_max": 4, "lappos_max": 5,
               "downface_max": 6, "upface_max": 7, "cross_max": 8, "relief": 9, "coh100": 10,
               "strike": 11, "valid": 12}
H19_5_SHA = "ef2ae808eb71"      # 19GEMSDOE h19-5 solid network (121,131 px), OWNER-REPORT 0.1922
CHAMPION_SHA = "c55bafc47005"   # GEMSDOE32 h33-h33-2-b2 zeros (37,654 dots), OWNER-REPORT 0.2778


@lru_cache(maxsize=1)
def footprint() -> np.ndarray:
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        return np.isfinite(ds.read(1))


@lru_cache(maxsize=1)
def catalogue() -> np.ndarray:
    with rasterio.open(DATA / "labels.tif") as ds:
        return (ds.read(1) == 1) & footprint()


def feature(name: str) -> np.ndarray:
    """One training-feature band as float32 with NaN for nodata."""
    with rasterio.open(DATA / "training_features.tif") as ds:
        a = ds.read(FEATURE_BANDS[name]).astype(np.float32)
    a[~np.isfinite(a) | (a < -1e30)] = np.nan
    return a


def lidar(name: str) -> np.ndarray:
    with rasterio.open(DATA / "external" / "lidar_scarp_features_u8.tif") as ds:
        return ds.read(LIDAR_BANDS[name])


def registry_path(sha_prefix: str) -> Path:
    hits = sorted((DATA / "registry").glob(f"{sha_prefix}*.tif"))
    if len(hits) != 1:
        raise FileNotFoundError(f"registry raster {sha_prefix}: {len(hits)} matches")
    return hits[0]


def read_support(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.isfinite(a) & (a > 0)


class RegistryOverlap:
    """Fast forward-overlap lookups against the packed 3-px buffers of every registry raster."""

    def __init__(self):
        st = json.loads((DATA / "registry_cache" / "registry_stats.json").read_text())
        self.rows = st["rows"]
        self.packed = np.load(DATA / "registry_cache" / "buffers_packed.npy", mmap_mode="r")
        self.ok = np.array(["error" not in r for r in self.rows])
        self.space_filling = np.array([bool(r.get("space_filling", False)) for r in self.rows])

    def overlaps(self, flat_idx: np.ndarray) -> np.ndarray:
        """Fraction of the given dots inside each registry raster's 3-px buffer (NaN for errors)."""
        flat_idx = np.asarray(flat_idx, np.int64)
        byte = flat_idx >> 3
        shift = 7 - (flat_idx & 7)
        out = np.full(len(self.rows), np.nan)
        if flat_idx.size == 0:
            return out
        for i in np.nonzero(self.ok)[0]:
            row = np.asarray(self.packed[i])
            out[i] = float(((row[byte] >> shift) & 1).mean())
        return out

    def buffer_mask(self, i: int) -> np.ndarray:
        return np.unpackbits(np.asarray(self.packed[i]))[: H * W].reshape(H, W).astype(bool)

    def label(self, i: int) -> str:
        r = self.rows[i]
        sc = [s.get("owner_reported_live_score") for s in r["sources"]
              if s.get("owner_reported_live_score") is not None]
        return f"{r['repo']}/{Path(r['path']).name}" + (f" (OWNER-REPORT {sc[0]})" if sc else "")


def ensure_bridge() -> Path:
    """Create data/bridge/{existing_faults,sample_submission}.tif symlinks expected by gems57.grid.load_grid.

    The shared loader re-verifies both files by SHA-256, so a wrong target fails closed there.
    """
    bridge = DATA / "bridge"
    bridge.mkdir(parents=True, exist_ok=True)
    for name, target in (("existing_faults.tif", "../labels.tif"), ("sample_submission.tif", "../sample_submission.tif")):
        link = bridge / name
        if not link.exists():
            if link.is_symlink():
                link.unlink()
            link.symlink_to(target)
    return bridge
