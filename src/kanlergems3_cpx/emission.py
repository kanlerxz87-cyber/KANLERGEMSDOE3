"""Kernel-exact expected-DTI greedy emission for L-K3-CPX-EDTI.

The official metric (alpha=0.2, beta=0.8, 300 m triangular kernel k) obeys
    DTI = TPw / (0.2*(TPw+FPw) + 0.8*|G|)        (since FNw = |G| - TPw)
so - to first order in a fractional-programming sense - a dot should be
added where its marginal expected coverage gain most exceeds 0.2x its
expected false-positive mass.  Given a posterior-like surface q(y) over a
mass domain, this allocator greedily maximizes

    G(x | S) = sum_y q(y) * max(k(d(x,y)) - cover_S(y), 0)  -  0.2 * fp(x),
    fp(x)    = 1 - max_y q(y) * k(d(x,y))           (constant in S),

with cover_S(y) = max_{x in S} k(d(x,y)).  The coverage term is monotone
submodular and fp(x) is S-independent, so stale heap gains are valid upper
bounds and CELF lazy evaluation is exact.  This differs from the repo's
fixed-spacing CELF (which maximizes coverage only, under a hard 2.85 px
spacing) by pricing false positives into every placement and letting the
300 m kernel itself - not a spacing constant - set the dot geometry
(a 2.0 px minimum spacing is retained only as a guard against degenerate
doubling on a single-pixel posterior spike).
"""
from __future__ import annotations

import heapq

import numpy as np
from scipy.ndimage import convolve

RADIUS_PX = 3.0
ALPHA = 0.2


def _kernel_offsets(radius: float = RADIUS_PX) -> list[tuple[int, int, float]]:
    r = int(np.ceil(radius))
    offs = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dy, dx))
            k = max(1.0 - d / radius, 0.0)
            if k > 0.0:
                offs.append((dy, dx, k))
    return offs


OFFSETS = _kernel_offsets()
_KGRID = np.zeros((7, 7), dtype=np.float32)
for _dy, _dx, _k in OFFSETS:
    _KGRID[_dy + 3, _dx + 3] = _k


def _expected_fp(q: np.ndarray) -> np.ndarray:
    """fp(x) = 1 - max_y q(y) k(d(x,y)) via shifted maxima."""
    best = np.zeros(q.shape, dtype=np.float32)
    H, W = q.shape
    for dy, dx, k in OFFSETS:
        y0, y1 = max(0, dy), min(H, H + dy)
        x0, x1 = max(0, dx), min(W, W + dx)
        sy0, sy1 = max(0, -dy), min(H, H - dy)
        sx0, sx1 = max(0, -dx), min(W, W - dx)
        cand = q[sy0:sy1, sx0:sx1] * np.float32(k)
        tgt = best[y0:y1, x0:x1]
        np.maximum(tgt, cand, out=tgt)
    return (1.0 - best).astype(np.float32)


def edti_greedy_emit(
    prob_2d: np.ndarray,
    eligible_2d: np.ndarray,
    budget: int,
    *,
    mass_mask: np.ndarray | None = None,
    alpha: float = ALPHA,
    min_spacing_px: float = 2.0,
    pool_multiplier: int = 10,
) -> tuple[np.ndarray, np.ndarray]:
    """Emit ``budget`` dots; returns (bool mask, flat indices in selection order)."""
    prob = np.asarray(prob_2d, dtype=np.float32)
    elig = np.asarray(eligible_2d, dtype=bool)
    if prob.shape != elig.shape or budget < 0:
        raise ValueError("Aligned 2D grids and nonnegative budget required")
    H, W = elig.shape
    if budget == 0 or not elig.any():
        return np.zeros(elig.shape, bool), np.empty(0, dtype=np.intp)
    mass = elig if mass_mask is None else np.asarray(mass_mask, bool)
    q = np.where(mass & np.isfinite(prob) & (prob > 0), np.clip(prob, 0, 1), 0.0).astype(np.float32)

    gain0 = convolve(q, _KGRID, mode="constant", cval=0.0)
    fp = _expected_fp(q)
    gain0 = gain0 - np.float32(alpha) * fp
    gain0 = np.where(elig, gain0, -np.inf)

    n_pool = int(min(int(elig.sum()), max(budget * pool_multiplier, budget)))
    flat_gain = gain0.ravel()
    if n_pool < flat_gain.size:
        pool = np.argpartition(flat_gain, -n_pool)[-n_pool:]
    else:
        pool = np.flatnonzero(elig.ravel())
    pool = pool[np.isfinite(flat_gain[pool])]
    pool = pool[np.argsort(-flat_gain[pool], kind="mergesort")]
    py, px = np.divmod(pool, W)
    fp_pool = fp.ravel()[pool].astype(np.float64)

    cover = np.zeros((H, W), dtype=np.float32)
    blocked = np.zeros((H, W), dtype=bool)
    # Spacing exclusion disc.
    sr = int(np.floor(min_spacing_px + 1e-9))
    disc = [(dy, dx) for dy in range(-sr, sr + 1) for dx in range(-sr, sr + 1)
            if float(np.hypot(dy, dx)) <= min_spacing_px + 1e-9]

    heap: list[tuple[float, int]] = [(-float(flat_gain[p]), i) for i, p in enumerate(pool)]
    heapq.heapify(heap)
    alive = np.ones(len(pool), dtype=bool)

    def marginal(i: int) -> float:
        y, x = int(py[i]), int(px[i])
        y0, y1 = max(0, y - 3), min(H, y + 4)
        x0, x1 = max(0, x - 3), min(W, x + 4)
        ky0, ky1 = y0 - (y - 3), 7 - ((y + 4) - y1)
        kx0, kx1 = x0 - (x - 3), 7 - ((x + 4) - x1)
        kpatch = _KGRID[ky0:ky1, kx0:kx1]
        gain = float((q[y0:y1, x0:x1] *
                      np.maximum(kpatch - cover[y0:y1, x0:x1], 0.0)).sum())
        return gain - alpha * float(fp_pool[i])

    chosen: list[int] = []
    while heap and len(chosen) < budget:
        neg_g, i = heapq.heappop(heap)
        if not alive[i] or blocked[py[i], px[i]]:
            alive[i] = False
            continue
        g = marginal(i)
        if heap and g < -heap[0][0] - 1e-12:
            heapq.heappush(heap, (-g, i))
            continue
        # Select i.
        y, x = int(py[i]), int(px[i])
        chosen.append(int(pool[i]))
        alive[i] = False
        y0, y1 = max(0, y - 3), min(H, y + 4)
        x0, x1 = max(0, x - 3), min(W, x + 4)
        ky0, ky1 = y0 - (y - 3), 7 - ((y + 4) - y1)
        kx0, kx1 = x0 - (x - 3), 7 - ((x + 4) - x1)
        np.maximum(cover[y0:y1, x0:x1], _KGRID[ky0:ky1, kx0:kx1],
                   out=cover[y0:y1, x0:x1])
        for dy, dx in disc:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W:
                blocked[yy, xx] = True

    order = np.asarray(chosen, dtype=np.intp)
    out = np.zeros(elig.shape, dtype=bool)
    out.ravel()[order] = True
    return out, order
