"""Deterministic ridge-NMS + >=3 px spaced dot emission (generic DTI emission).

Uses only the shared-template primitive gems.metric.ridge_nms.  Candidates are
ridge pixels first (descending surface, flat-index tie-break), then remaining
eligible positive pixels, each accepted only if no accepted dot lies in its
5x5 neighbourhood (=> >=3 px Euclidean spacing).  This is an emission rule,
not a detector and not a copy of any registry dot set.
"""
from __future__ import annotations

import numpy as np


def _greedy(order_flat: np.ndarray, shape: tuple[int, int], budget: int, blocked: np.ndarray | None = None) -> np.ndarray:
    h, w = shape
    taken = np.zeros(shape, bool) if blocked is None else blocked.copy()
    out = np.zeros(shape, bool)
    n = 0
    ys, xs = np.divmod(order_flat, w)
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        if taken[y, x]:
            continue
        out[y, x] = True
        taken[max(0, y - 2): y + 3, max(0, x - 2): x + 3] = True
        n += 1
        if n >= budget:
            break
    return out


def emit_dots(score: np.ndarray, eligible: np.ndarray, budget: int, *, sigma: float = 1.0) -> np.ndarray:
    from gems.metric import ridge_nms

    score = np.asarray(score, np.float32)
    eligible = np.asarray(eligible, bool) & np.isfinite(score) & (score > 0)
    ridge = ridge_nms(np.where(eligible, score, 0.0), eligible, sigma=sigma) & eligible
    flat = score.ravel()
    r_ids = np.flatnonzero(ridge.ravel())
    r_ord = r_ids[np.lexsort((r_ids, -flat[r_ids]))]
    dots = _greedy(r_ord, score.shape, int(budget))
    short = int(budget) - int(dots.sum())
    if short > 0:
        o_ids = np.flatnonzero((eligible & ~ridge).ravel())
        o_ord = o_ids[np.lexsort((o_ids, -flat[o_ids]))]
        blocked = np.zeros(score.shape, bool)
        for y, x in np.argwhere(dots):
            blocked[max(0, y - 2): y + 3, max(0, x - 2): x + 3] = True
        dots |= _greedy(o_ord, score.shape, short, blocked=blocked)
    return dots
