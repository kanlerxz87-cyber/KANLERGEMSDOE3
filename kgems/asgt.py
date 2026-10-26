"""K3-H1 Antislope-scarp grain traces (ASGT) detector and DTI-oriented dot emission.

Physical idea: an uphill-facing (antislope) scarp in the 1 m DEM is a near-diagnostic tectonic landform;
requiring it to be coherent and parallel to the local fault grain (orientation of the *visible* catalogue
only) suppresses channel banks, landslide headscarps and roads.  All LiDAR inputs come from the
GEMSDOE24 product built from USGS 3DEP 1 m DEM tiles (band semantics in data/external metadata).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import common as C


def decode_sqrt(q: np.ndarray, xmax: float = 1.0) -> np.ndarray:
    """Invert q = 1 + round(254 * sqrt(clip(x/xmax))) ; 0 = no lidar -> 0."""
    q = q.astype(np.float32)
    t = np.clip((q - 1.0) / 254.0, 0.0, 1.0)
    return np.where(q > 0, xmax * t * t, 0.0).astype(np.float32)


def pct_rank(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Percentile rank in [0,1] of a over mask (ties averaged); 0 outside mask."""
    out = np.zeros(a.shape, np.float32)
    v = a[mask]
    order = np.argsort(v, kind="stable")
    ranks = np.empty(v.size, np.float64)
    ranks[order] = np.arange(v.size)
    # average ties
    sv = v[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sv)) + 1]
    ends = np.r_[starts[1:], sv.size]
    mean_rank = (starts + ends - 1) / 2.0
    tie_rank = np.repeat(mean_rank, ends - starts)
    ranks[order] = tie_rank
    out[mask] = (ranks / max(v.size - 1, 1)).astype(np.float32)
    return out


def orientation_field(field: np.ndarray, sigma_grad: float = 1.0, sigma_tensor: float = 2.0):
    """Lineament azimuth (deg, clockwise from north, [0,180)) and coherence of a scalar field."""
    f = ndi.gaussian_filter(field.astype(np.float32), sigma_grad)
    gy, gx = np.gradient(f)
    jxx = ndi.gaussian_filter(gx * gx, sigma_tensor)
    jyy = ndi.gaussian_filter(gy * gy, sigma_tensor)
    jxy = ndi.gaussian_filter(gx * gy, sigma_tensor)
    del gx, gy, f
    diff = jxx - jyy
    tr = jxx + jyy
    coh = (np.sqrt(diff * diff + 4 * jxy * jxy) / np.maximum(tr, 1e-12)).astype(np.float32)
    theta = 0.5 * np.arctan2(2 * jxy, diff) + np.pi / 2.0
    az = (np.degrees(np.arctan2(np.cos(theta), -np.sin(theta))) % 180.0).astype(np.float32)
    return az, coh


def grain_field(visible: np.ndarray, sigma_px: float = 30.0):
    """Regional fault-grain azimuth + confidence from the VISIBLE catalogue only (doubled-angle mean)."""
    import sys
    from . import ROOT
    sys.path.insert(0, str(ROOT / "vendor"))
    from gems57.network import local_strike
    st, coh = local_strike(visible, smooth_px=2.0)
    on = np.asarray(visible, bool) & np.isfinite(st)
    w = np.where(on, coh, 0.0).astype(np.float32)
    th = np.radians(np.where(on, st, 0.0)).astype(np.float32)
    c = ndi.gaussian_filter(w * np.cos(2 * th), sigma_px)
    s = ndi.gaussian_filter(w * np.sin(2 * th), sigma_px)
    ww = ndi.gaussian_filter(w, sigma_px)
    del st, coh, th, w
    R = np.where(ww > 1e-6, np.hypot(c, s) / np.maximum(ww, 1e-12), 0.0).astype(np.float32)
    az = (np.degrees(0.5 * np.arctan2(s, c)) % 180.0).astype(np.float32)
    ref = np.quantile(ww[C.footprint()], 0.75)
    conf = (np.clip(R, 0, 1) * np.clip(ww / max(ref, 1e-12), 0, 1)).astype(np.float32)
    return az, conf


def acute(a, b):
    d = np.abs(a - b) % 180.0
    return np.where(d > 90.0, 180.0 - d, d)


def asgt_components(visible: np.ndarray) -> dict:
    """All score components on the full grid (float32, 0 where no lidar / outside footprint)."""
    foot = C.footprint()
    valid = (C.lidar("valid") > 0) & foot
    up = decode_sqrt(C.lidar("upface_max"))
    dn = decode_sqrt(C.lidar("downface_max"))
    cr = decode_sqrt(C.lidar("cross_max"))
    p_up = pct_rank(up, valid)
    dom = np.where(valid, up / np.maximum(up + dn + cr, 1e-6), 0.0).astype(np.float32)   # antislope share
    del dn, cr
    rel = decode_sqrt(C.lidar("relief"), 300.0)
    p_rel = pct_rank(rel, valid)
    del rel
    az_s, coh_s = orientation_field(p_up)
    az_g, conf_g = grain_field(visible)
    compat = np.cos(np.radians(acute(az_s, az_g))) ** 2
    G = (conf_g * compat + (1.0 - conf_g) * 0.5).astype(np.float32)
    del az_s, az_g, compat
    step = decode_sqrt(C.lidar("step_max"))
    p_step = pct_rank(step, valid)
    del step
    return dict(valid=valid, p_up=p_up, dom=dom, p_rel=p_rel, coh_s=coh_s, G=G, conf_g=conf_g, p_step=p_step)


def asgt_score(comp: dict) -> np.ndarray:
    """ASGT = P(upface) x antislope share x grain compatibility x lineament coherence x relief veto."""
    veto = np.where(comp["p_rel"] > 0.98, 0.5, 1.0).astype(np.float32)
    s = comp["p_up"] * np.sqrt(np.clip(comp["dom"], 0, 1)) * comp["G"] * (0.5 + 0.5 * comp["coh_s"]) * veto
    return np.where(comp["valid"], s, 0.0).astype(np.float32)


def disk_offsets(r: float):
    k = int(np.ceil(r))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    m = (yy * yy + xx * xx) <= r * r + 1e-9
    return yy[m], xx[m]


def nms_dots(score: np.ndarray, allowed: np.ndarray, n: int, r: float = 2.8,
             forbid: np.ndarray | None = None) -> np.ndarray:
    """Greedy non-maximum suppression: highest score first, no two dots closer than r px."""
    Hh, Ww = score.shape
    pad = int(np.ceil(r)) + 1
    blocked = np.zeros((Hh + 2 * pad, Ww + 2 * pad), bool)
    if forbid is not None:
        blocked[pad:-pad, pad:-pad] |= forbid
    cand = np.flatnonzero((allowed & (score > 0)).ravel())
    order = cand[np.argsort(-score.ravel()[cand], kind="stable")]
    dy, dx = disk_offsets(r)
    Wp = Ww + 2 * pad
    offs = dy * Wp + dx
    bflat = blocked.ravel()
    out = np.zeros(Hh * Ww, bool)
    taken = 0
    for f in order:
        y, x = divmod(int(f), Ww)
        pf = (y + pad) * Wp + (x + pad)
        if bflat[pf]:
            continue
        out[f] = True
        bflat[pf + offs] = True
        taken += 1
        if taken >= n:
            break
    return out.reshape(Hh, Ww)
