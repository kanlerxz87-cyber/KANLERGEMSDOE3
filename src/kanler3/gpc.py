"""Amplitude-Invariant Gradient-Phase Concordance (GPC) transforms.

Physical idea
------------
A buried/under-mapped normal fault juxtaposes rock units, so several
*independent* physical fields change across the same line: reduced-to-pole
magnetics (02_rtp), isostatic gravity (13_iso_grav_anom), depth-to-basement
(15_depth_to_base_surf) and detrended elevation (12_det_elev).  Their gradient
*magnitudes* are not comparable (nT, mGal, m, m) and are dominated by the
strongest lithology in each survey.  Their gradient *directions* (phase) are
comparable: at a fault the unit gradient vectors of independent fields point
the same way (or exactly opposite, if a contrast polarity flips), while at a
single-survey artefact (flight-line seam, playa shoreline, volcanic flow edge)
only one field turns.

GPC therefore discards amplitude (after a local relative-sharpness term) and
keeps, per pixel:
  * pairwise |unit-grad_i . unit-grad_j| concordance (mean and minimum),
  * double-angle consensus orientation and its resultant length R in [0,1],
  * how many fields agree with the consensus within 25 degrees,
  * cross-scale (1 px vs 3 px = 100 m vs 300 m) orientation persistence,
  * Laplacian zero-crossing concordance (fields change sign across the line),
  * the two geologically diagnostic signed pairs (RTP-gravity polarity).

No catalogue/label pixel is read here: every GPC feature is label-free and
therefore fold-safe by construction under hide-and-recover.  The named
non-fault mimic is a lithologic contact / playa shoreline / flight-line seam:
it can align two fields, which is why the *minimum* pairwise concordance and
the >=3-field consensus count are included -- a mimic must fool magnetic,
gravity, basement-depth and elevation simultaneously to score highly.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter, minimum_filter

GPC_FIELDS = ("rtp", "iso_grav_anom", "depth_to_base_surf", "det_elev")

GPC_FEATURE_NAMES: tuple[str, ...] = (
    "gpc_mean_absdot_s1",
    "gpc_mean_absdot_s3",
    "gpc_min_absdot_s1",
    "gpc_consensus_R_s1",
    "gpc_consensus_R_s3",
    "gpc_consensus_count_s1",
    "gpc_crossscale_orient",
    "gpc_crossscale_product",
    "gpc_local_sharpness",
    "gpc_zerocross_mean",
    "gpc_pair_rtpgrav_abs_s1",
    "gpc_pair_baseelev_abs_s1",
    "gpc_pair_rtpgrav_signed_s1",
    "gpc_cons_cos2_s1",
    "gpc_cons_sin2_s1",
)

_CONS_COS25 = float(np.cos(np.deg2rad(25.0)))


def _filled(field: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    a = np.asarray(field, dtype=np.float32)
    good = footprint & np.isfinite(a) & (a > -1e30)
    if not good.any():
        raise ValueError("GPC field has no finite footprint values")
    med = float(np.median(a[good]))
    return np.where(good, a, med).astype(np.float32)


def _unit_gradients(field: np.ndarray, footprint: np.ndarray, sigma: float):
    """Return (ux, uy, mag): unit gradient (east, north) and magnitude at `sigma` px."""
    z = _filled(field, footprint)
    sm = gaussian_filter(z, sigma, mode="nearest")
    gy, gx = np.gradient(sm)  # gy: d/drow (south), gx: d/dcol (east)
    mag = np.hypot(gx, gy).astype(np.float32)
    scale = float(np.median(mag[footprint])) if footprint.any() else 0.0
    eps = max(0.05 * scale, 1e-12)
    ux = (gx / (mag + eps)).astype(np.float32)
    uy = (-gy / (mag + eps)).astype(np.float32)  # north component
    return ux, uy, mag


def _scale_features(fields: dict[str, np.ndarray], footprint: np.ndarray, sigma: float, suffix: str):
    units: list[tuple[np.ndarray, np.ndarray]] = []
    mags: list[np.ndarray] = []
    for name in GPC_FIELDS:
        ux, uy, mag = _unit_gradients(fields[name], footprint, sigma)
        units.append((ux, uy))
        mags.append(mag)
    pair_abs: list[np.ndarray] = []
    pair_signed: dict[tuple[int, int], np.ndarray] = {}
    for i in range(len(units)):
        for j in range(i + 1, len(units)):
            d = units[i][0] * units[j][0] + units[i][1] * units[j][1]
            pair_abs.append(np.abs(d))
            pair_signed[(i, j)] = d
    pair_stack_mean = np.mean(pair_abs, axis=0).astype(np.float32)
    pair_stack_min = np.min(pair_abs, axis=0).astype(np.float32)
    # Double-angle consensus: average (cos2t, sin2t) of unit gradients.
    cos2 = np.zeros_like(pair_stack_mean)
    sin2 = np.zeros_like(pair_stack_mean)
    for ux, uy in units:
        cos2 += ux * ux - uy * uy
        sin2 += 2.0 * ux * uy
    cos2 /= len(units)
    sin2 /= len(units)
    resultant = np.hypot(cos2, sin2).astype(np.float32)
    # Consensus direction (unit, axial): normalise double-angle vector, halve angle.
    norm = np.maximum(resultant, 1e-12)
    c_half = np.sqrt(np.maximum(0.0, (1.0 + cos2 / norm) / 2.0))
    s_half = np.sign(sin2) * np.sqrt(np.maximum(0.0, (1.0 - cos2 / norm) / 2.0))
    count = np.zeros_like(pair_stack_mean)
    for ux, uy in units:
        count += (np.abs(ux * c_half + uy * s_half) > _CONS_COS25)
    feats = {
        f"gpc_mean_absdot_{suffix}": pair_stack_mean,
        f"gpc_consensus_R_{suffix}": resultant,
    }
    extra = {}
    if suffix == "s1":
        feats[f"gpc_min_absdot_{suffix}"] = pair_stack_min
        feats[f"gpc_consensus_count_{suffix}"] = (count / len(units)).astype(np.float32)
        feats["gpc_pair_rtpgrav_abs_s1"] = np.abs(pair_signed[(0, 1)]).astype(np.float32)
        feats["gpc_pair_baseelev_abs_s1"] = np.abs(pair_signed[(2, 3)]).astype(np.float32)
        feats["gpc_pair_rtpgrav_signed_s1"] = pair_signed[(0, 1)].astype(np.float32)
        feats["gpc_cons_cos2_s1"] = cos2.astype(np.float32)
        feats["gpc_cons_sin2_s1"] = sin2.astype(np.float32)
        # Local relative sharpness: magnitude vs its own 5-px neighbourhood mean.
        sharp = []
        for mag in mags:
            local = gaussian_filter(mag, 5.0, mode="nearest")
            sharp.append(np.clip(mag / (local + 1e-12), 0.0, 5.0))
        extra["gpc_local_sharpness"] = np.mean(sharp, axis=0).astype(np.float32)
        # Laplacian zero-crossing concordance at 1 px.
        zc = []
        for name in GPC_FIELDS:
            z = _filled(fields[name], footprint)
            sm = gaussian_filter(z, 1.0, mode="nearest")
            gy, gx = np.gradient(sm)
            hyy, _ = np.gradient(gy)
            _, hxx = np.gradient(gx)
            lap = (hxx + hyy).astype(np.float32)
            zc.append(((maximum_filter(lap, size=3) > 0) & (minimum_filter(lap, size=3) < 0)).astype(np.float32))
        extra["gpc_zerocross_mean"] = np.mean(zc, axis=0).astype(np.float32)
    return feats, extra, cos2, sin2, resultant


def compute_gpc_features(fields: dict[str, np.ndarray], footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Compute all GPC_FEATURE_NAMES full-grid float32 arrays from the 4 named fields."""
    missing = [n for n in GPC_FIELDS if n not in fields]
    if missing:
        raise ValueError(f"Missing GPC fields: {missing}")
    footprint = np.asarray(footprint, bool)
    f1, extra, cos2_1, sin2_1, r1 = _scale_features(fields, footprint, 1.0, "s1")
    f3, _, cos2_3, sin2_3, r3 = _scale_features(fields, footprint, 3.0, "s3")
    cross = np.abs(cos2_1 * cos2_3 + sin2_1 * sin2_3).astype(np.float32)  # |cos(2*dt)|
    out: dict[str, np.ndarray] = {}
    out.update(f1)
    out.update(f3)
    out.update(extra)
    out["gpc_crossscale_orient"] = cross
    out["gpc_crossscale_product"] = (np.sqrt(np.maximum(r1 * r3, 0.0)) * cross).astype(np.float32)
    for name in GPC_FEATURE_NAMES:
        if name not in out:
            raise RuntimeError(f"GPC feature not computed: {name}")
        out[name] = np.asarray(out[name], dtype=np.float32)
        out[name][~footprint] = 0.0
    return out
