"""Exact Minoux/CELF lazy-greedy 300 m submodular DTI dot allocator & spacing baseline."""
from __future__ import annotations

import heapq
import numpy as np

RADIUS_PX = 3.0


def _build_kernel_offsets(radius: float = RADIUS_PX) -> list[tuple[int, int, float]]:
    r = int(np.ceil(radius))
    offs: list[tuple[int, int, float]] = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dy, dx))
            k = max(1.0 - d / radius, 0.0)
            if k > 0.0:
                offs.append((dy, dx, k))
    return offs


def _build_disk_offsets(radius: float) -> list[tuple[int, int]]:
    r = int(np.floor(radius + 1e-9))
    offs: list[tuple[int, int]] = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if float(np.hypot(dy, dx)) <= radius + 1e-9:
                offs.append((dy, dx))
    return offs


KERNEL_300M = _build_kernel_offsets(RADIUS_PX)


def celf_submodular_emit_300m(
    prob_2d: np.ndarray,
    eligible_2d: np.ndarray,
    budget: int,
    *,
    active_mass_mask: np.ndarray | None = None,
    min_self_spacing_px: float = 2.5,
    pool_multiplier: int = 12,
) -> np.ndarray:
    """Allocate ``budget`` binary dots maximizing monotone submodular expected 300 m TP_w.

    Objective:
        F(S) = sum_{y in active} q(y) * max_{x in S} max(1 - d(x, y) / 3.0, 0)
    subject to |S| = budget and d(x_i, x_j) > min_self_spacing_px.
    """
    prob = np.asarray(prob_2d, dtype=np.float32)
    elig = np.asarray(eligible_2d, dtype=bool)
    if prob.shape != elig.shape or budget < 0:
        raise ValueError("Aligned 2D grids and nonnegative budget required")
    if budget == 0 or not elig.any():
        return np.zeros(elig.shape, dtype=bool)

    mass_mask = elig if active_mass_mask is None else np.asarray(active_mass_mask, dtype=bool)
    q = np.where(mass_mask & np.isfinite(prob) & (prob > 0.0), prob, 0.0).astype(np.float32)
    H, W = q.shape
    pad = 4
    q_pad = np.pad(q, pad, mode="constant", constant_values=0.0)
    cov_pad = np.zeros((H + 2 * pad, W + 2 * pad), dtype=np.float32)
    blk_pad = np.zeros((H + 2 * pad, W + 2 * pad), dtype=bool)

    # Vectorized exact singleton marginal gain G_0(x) across all 29 kernel offsets
    init_gain = np.zeros((H, W), dtype=np.float32)
    for dy, dx, k in KERNEL_300M:
        init_gain += k * q_pad[pad + dy : pad + dy + H, pad + dx : pad + dx + W]

    elig_flat = np.flatnonzero(elig & (init_gain > 0.0))
    if len(elig_flat) == 0:
        elig_flat = np.flatnonzero(elig)
    pool_size = min(len(elig_flat), max(budget * pool_multiplier, 120_000))
    gains_elig = init_gain.ravel()[elig_flat]
    if len(elig_flat) > pool_size:
        part = np.argpartition(-gains_elig, pool_size - 1)[:pool_size]
        cand_flat = elig_flat[part]
        cand_gains = gains_elig[part]
    else:
        cand_flat = elig_flat
        cand_gains = gains_elig

    # Deterministic Minoux max-heap via (-upper_bound, flat_idx)
    heap: list[tuple[float, int]] = [(-float(g), int(idx)) for g, idx in zip(cand_gains, cand_flat)]
    heapq.heapify(heap)

    W_pad = W + 2 * pad
    k_strides = [dy * W_pad + dx for dy, dx, _ in KERNEL_300M]
    k_weights = [float(k) for _, _, k in KERNEL_300M]
    blk_offs = _build_disk_offsets(min_self_spacing_px) if min_self_spacing_px > 0 else [(0, 0)]
    blk_strides = [dy * W_pad + dx for dy, dx in blk_offs]

    q_flat = q_pad.ravel()
    cov_flat = cov_pad.ravel()
    blk_flat = blk_pad.ravel()

    out = np.zeros((H, W), dtype=bool)
    out_flat = out.ravel()
    selected = 0

    while selected < budget and heap:
        neg_ub, f_idx = heapq.heappop(heap)
        r = f_idx // W
        c = f_idx - r * W
        p_idx = (r + pad) * W_pad + (c + pad)
        if blk_flat[p_idx]:
            continue

        # Recompute exact current marginal gain over 29-point 300 m kernel
        cur_gain = 0.0
        for st, kw in zip(k_strides, k_weights):
            nb = p_idx + st
            qv = float(q_flat[nb])
            if qv > 0.0:
                diff = kw - float(cov_flat[nb])
                if diff > 0.0:
                    cur_gain += qv * diff

        # Lazy-greedy optimality check: if cur_gain >= next best upper bound in heap, accept!
        next_ub = -heap[0][0] if heap else -1.0
        if cur_gain + 1e-12 >= next_ub:
            out_flat[f_idx] = True
            selected += 1
            for st, kw in zip(k_strides, k_weights):
                nb = p_idx + st
                if kw > cov_flat[nb]:
                    cov_flat[nb] = kw
            for bst in blk_strides:
                blk_flat[p_idx + bst] = True
        elif cur_gain > 0.0:
            heapq.heappush(heap, (-cur_gain, f_idx))

    # Fallback if ultra-strict spacing exhausted high-gain pool before budget (rare)
    if selected < budget:
        rem = np.flatnonzero(elig & ~out)
        if len(rem):
            rem_scores = prob.ravel()[rem]
            order = np.argsort(-rem_scores, kind="mergesort")
            for idx in rem[order]:
                r = int(idx) // W
                c = int(idx) - r * W
                p_idx = (r + pad) * W_pad + (c + pad)
                if blk_flat[p_idx]:
                    continue
                out_flat[idx] = True
                selected += 1
                for bst in blk_strides:
                    blk_flat[p_idx + bst] = True
                if selected >= budget:
                    break

    return out


def greedy_spacing_emit(
    score_2d: np.ndarray,
    eligible_2d: np.ndarray,
    budget: int,
    *,
    min_spacing_px: float = 2.8,
) -> np.ndarray:
    """Standard greedy non-maximum spacing emitter (for matched regional baseline)."""
    score = np.asarray(score_2d, dtype=np.float32)
    elig = np.asarray(eligible_2d, dtype=bool)
    H, W = elig.shape
    out = np.zeros((H, W), dtype=bool)
    if budget <= 0 or not elig.any():
        return out

    cand = np.flatnonzero(elig & np.isfinite(score))
    vals = score.ravel()[cand]
    pool = min(len(cand), max(budget * 14, 140_000))
    if len(cand) > pool:
        part = np.argpartition(-vals, pool - 1)[:pool]
        cand = cand[part]
        vals = vals[part]
    order = np.lexsort((cand, -vals))
    cand = cand[order]

    pad = int(np.ceil(min_spacing_px)) + 1
    W_pad = W + 2 * pad
    blk = np.zeros((H + 2 * pad) * W_pad, dtype=bool)
    offs = [dy * W_pad + dx for dy, dx in _build_disk_offsets(min_spacing_px)]
    out_flat = out.ravel()
    selected = 0
    for idx in cand:
        ii = int(idx)
        r = ii // W
        c = ii - r * W
        p_idx = (r + pad) * W_pad + (c + pad)
        if blk[p_idx]:
            continue
        out_flat[ii] = True
        selected += 1
        for st in offs:
            blk[p_idx + st] = True
        if selected >= budget:
            break
    return out
