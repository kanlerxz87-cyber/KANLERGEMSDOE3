"""Cached feature stack for KANLERGEMSDOE3.

Base stack (59 features) is the shared multi-sensor stack used as the matched
control in the GEMSDOE36 lanes (org_* competition bands + multi-scale context
+ USGS 3DEP 1 m LiDAR scarp product + GeoDAWN radiometrics), rebuilt here from
the SHA-256-pinned rasters in registry/data_manifest.json.  It is label-free.
The only candidate-only additions are the 15 GPC features in kanler3.gpc;
no catalogue/label pixel is read by any feature builder in this module, so
every feature is fold-safe by construction.  No SGMC, QFaults, prior
submission or registry raster is read (asserted by token guard).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

from .gpc import GPC_FEATURE_NAMES, compute_gpc_features
from .paths import data_dir

NODATA_CUT = -1e30
BANNED_PATH_TOKENS = ("sgmc", "qfaults", "scored", "downloads", "registry")

LIDAR_BANDS = (
    "ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max", "downface_max",
    "upface_max", "cross_max", "relief", "coh100", "strike", "valid",
)
LIDAR_QUANT = {
    "ex_max": (1.5, "sqrt"), "ex_mean": (0.3, "sqrt"), "step_max": (1.0, "sqrt"),
    "lapneg_max": (0.05, "sqrt"), "lappos_max": (0.05, "sqrt"), "downface_max": (1.0, "sqrt"),
    "upface_max": (1.0, "sqrt"), "cross_max": (1.0, "sqrt"), "relief": (300.0, "sqrt"),
    "coh100": (1.0, "linear"), "strike": (180.0, "linear"), "valid": (1.0, "linear"),
}


def _assert_safe(path: Path) -> None:
    s = str(path).lower()
    for tok in BANNED_PATH_TOKENS:
        if tok in s:
            raise RuntimeError(f"Banned input path for this lane: {path}")


def dequantize(q: np.ndarray, xmax: float, transform: str) -> np.ndarray:
    q = q.astype(np.float32)
    t = (q - 1.0) / 254.0
    x = xmax * (t * t if transform == "sqrt" else t)
    return np.where(q > 0, x, np.nan).astype(np.float32)


@dataclass
class Grid:
    footprint: np.ndarray
    labels: np.ndarray
    transform: tuple
    shape: tuple

    @property
    def n_fp(self) -> int:
        return int(self.footprint.sum())


def load_grid(d: Path | None = None) -> Grid:
    d = d or data_dir()
    with rasterio.open(d / "labels.tif") as s:
        lab = s.read(1)
        tr = tuple(s.transform)[:6]
        shape = s.shape
    with rasterio.open(d / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    if not np.array_equal(foot, lab >= 0):
        raise ValueError("Footprint mismatch: sample_submission finite != labels >= 0")
    return Grid(footprint=foot, labels=(lab == 1) & foot, transform=tr, shape=shape)


class FeatureStore:
    """Footprint-only float32 columns, one .npy per feature (memory-safe)."""

    def __init__(self, cache_dir: Path, names: list[str], n_fp: int):
        self.cache_dir = Path(cache_dir)
        self.names = list(names)
        self.n_fp = int(n_fp)

    def column(self, name: str) -> np.ndarray:
        return np.load(self.cache_dir / f"{name}.npy", mmap_mode="r")

    def rows(self, idx: np.ndarray, names: list[str] | None = None) -> np.ndarray:
        names = self.names if names is None else names
        out = np.empty((len(idx), len(names)), np.float32)
        for j, n in enumerate(names):
            out[:, j] = self.column(n)[idx]
        return out


def build_feature_stack(cache_dir: Path, *, force: bool = False) -> tuple[FeatureStore, Grid]:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    d = data_dir()
    grid = load_grid(d)
    fp = grid.footprint
    meta_p = cache_dir / "kanler3_features.json"
    if meta_p.exists() and not force:
        meta = json.loads(meta_p.read_text())
        if all((cache_dir / f"{n}.npy").exists() for n in meta["names"]):
            return FeatureStore(cache_dir, meta["names"], grid.n_fp), grid

    names: list[str] = []

    def add(name: str, full: np.ndarray) -> None:
        np.save(cache_dir / f"{name}.npy", np.asarray(full[fp], dtype=np.float32))
        names.append(name)
        print(f"  feature {len(names):3d} {name}", flush=True)

    gpc_fields: dict[str, np.ndarray] = {}
    with rasterio.open(d / "training_features.tif") as s:
        _assert_safe(d / "training_features.tif")
        band_names = [desc.split(" - ")[0] if desc else f"b{i+1}" for i, desc in enumerate(s.descriptions)]
        keep_ctx = {}
        for i, name in enumerate(band_names, start=1):
            a = s.read(i).astype(np.float32)
            a[a < NODATA_CUT] = np.nan
            add(f"org_{name}", a)
            if name in ("det_elev", "det_elev_slope", "iso_grav_anom", "iso_grav_anom_hg", "tmi_hg", "rtp"):
                keep_ctx[name] = a
            if name in ("rtp", "iso_grav_anom", "depth_to_base_surf", "det_elev"):
                gpc_fields[name] = a
    for name, a in keep_ctx.items():
        filled = np.where(np.isfinite(a), a, np.nanmedian(a[fp])).astype(np.float32)
        for sig in (3.0, 10.0):
            g = gaussian_filter(filled, sig)
            add(f"ctx_{name}_g{int(sig)}", g)
            if sig == 3.0:
                add(f"ctx_{name}_anom3", filled - g)
    del keep_ctx

    lid_step = None
    lidar_path = d / "external" / "lidar_scarp_features_u8.tif"
    _assert_safe(lidar_path)
    with rasterio.open(lidar_path) as s:
        for i, name in enumerate(LIDAR_BANDS, start=1):
            q = s.read(i)
            xmax, t = LIDAR_QUANT[name]
            x = dequantize(q, xmax, t)
            if name == "strike":
                th = np.deg2rad(x)
                add("lid_strike_cos2", np.cos(2 * th))
                add("lid_strike_sin2", np.sin(2 * th))
            else:
                add(f"lid_{name}", x)
                if name == "step_max":
                    lid_step = x
    add("ctx_lid_step_g3", gaussian_filter(np.nan_to_num(lid_step, nan=0.0), 3.0))
    del lid_step

    for fname, bnames in (
        ("geodawn_rad_u8.tif", ("K", "Th", "U", "TC")),
        ("geodawn_extensions_u8.tif", ("ThK", "UK", "UTh", "TMI_up150")),
    ):
        p = d / "external" / fname
        _assert_safe(p)
        with rasterio.open(p) as s:
            for i, name in enumerate(bnames, start=1):
                q = s.read(i).astype(np.float32)
                add(f"gd_{name}", np.where(q > 0, q, np.nan))

    base_names = list(names)
    if len(base_names) != 59:
        raise RuntimeError(f"Expected 59 base features, built {len(base_names)}: {base_names}")

    gpc = compute_gpc_features(gpc_fields, fp)
    del gpc_fields
    for name in GPC_FEATURE_NAMES:
        add(name, gpc[name])
    del gpc

    meta_p.write_text(json.dumps({"names": names, "base59": base_names,
                                   "gpc": list(GPC_FEATURE_NAMES), "n_fp": grid.n_fp}, indent=1))
    return FeatureStore(cache_dir, names, grid.n_fp), grid
