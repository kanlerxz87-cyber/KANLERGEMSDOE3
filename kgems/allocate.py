"""Uniqueness-constrained dot allocation.

Dots are taken in descending detector score from a spacing-constrained candidate list; a dot is accepted
only if, for EVERY comparable non-space-filling registry raster, the count of accepted dots inside that
raster's 3-px buffer stays <= cap * N_target.  Only scored dots exist here (inside the footprint, off the
catalogue), so masked pixels can never be used to pad the denominator of the overlap fraction.
"""
from __future__ import annotations

import numpy as np

from .common import RegistryOverlap


def membership(reg: RegistryOverlap, flat_idx: np.ndarray, include_space_filling: bool = False):
    """Bool matrix (n_rasters_used, n_candidates): candidate inside raster j's 3-px buffer."""
    use = np.nonzero(reg.ok & (include_space_filling | ~reg.space_filling))[0]
    byte = flat_idx >> 3
    shift = (7 - (flat_idx & 7)).astype(np.uint8)
    M = np.zeros((use.size, flat_idx.size), bool)
    for r, i in enumerate(use):
        row = np.asarray(reg.packed[i])
        M[r] = ((row[byte] >> shift) & 1).astype(bool)
    return use, M


def constrained_greedy(order_idx: np.ndarray, M: np.ndarray, n_target: int, cap: float = 0.695):
    """order_idx: candidate positions (columns of M) in priority order.  Returns accepted positions."""
    limit = int(np.floor(cap * n_target))
    counts = np.zeros(M.shape[0], np.int64)
    accepted = []
    for j in order_idx:
        col = M[:, j]
        if col.any():
            if (counts[col] + 1 > limit).any():
                continue
            counts[col] += 1
        accepted.append(j)
        if len(accepted) >= n_target:
            break
    return np.asarray(accepted, np.int64), counts, limit
