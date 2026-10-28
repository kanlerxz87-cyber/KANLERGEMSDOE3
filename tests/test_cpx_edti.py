"""Tests for lane L-K3-CPX-EDTI emission + fusion (synthetic, no data needed)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.kanlergems3_cpx.emission import edti_greedy_emit  # noqa: E402
from src.kanlergems3_cpx.physics import _rank01, rank_fusion  # noqa: E402


def test_edti_picks_exact_peaks_first():
    q = np.zeros((30, 30), dtype=np.float32)
    q[15, 15] = 1.0
    q[5, 5] = 0.8
    dots, order = edti_greedy_emit(q, np.ones((30, 30), bool), 2)
    assert int(dots.sum()) == 2
    assert divmod(int(order[0]), 30) == (15, 15)
    assert divmod(int(order[1]), 30) == (5, 5)


def test_edti_respects_budget_eligibility_and_spacing():
    rng = np.random.default_rng(7)
    q = rng.random((80, 80)).astype(np.float32)
    elig = np.ones((80, 80), bool)
    elig[:10] = False
    dots, order = edti_greedy_emit(q, elig, 50, min_spacing_px=2.0)
    assert int(dots.sum()) == 50 == len(order)
    assert not dots[:10].any()
    ys, xs = np.nonzero(dots)
    pts = np.column_stack([ys, xs]).astype(float)
    d2 = ((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(d2, np.inf)
    assert np.sqrt(d2.min()) > 2.0


def test_edti_concentrates_on_lineament_not_noise():
    rng = np.random.default_rng(0)
    H = W = 120
    q = (rng.random((H, W)) * 0.02).astype(np.float32)
    for t in range(10, 110):
        q[t, t] = 0.9
    dots, _ = edti_greedy_emit(q, np.ones((H, W), bool), 40)
    ys, xs = np.nonzero(dots)
    on = sum(1 for y, x in zip(ys, xs) if abs(int(y) - int(x)) <= 3)
    assert on >= 38


def test_edti_empty_and_zero_budget():
    q = np.zeros((10, 10), dtype=np.float32)
    dots, order = edti_greedy_emit(q, np.zeros((10, 10), bool), 5)
    assert not dots.any() and len(order) == 0
    dots, order = edti_greedy_emit(q, np.ones((10, 10), bool), 0)
    assert not dots.any() and len(order) == 0


def test_rank01_bounds_and_monotonicity():
    v = np.array([3.0, 1.0, 2.0, 2.0], dtype=np.float32)
    r = _rank01(v)
    assert r.min() == 0.0 and r.max() == 1.0
    assert r[1] < r[2] <= r[3] < r[0]


def test_rank_fusion_confined_to_domain():
    a = np.arange(100, dtype=np.float32).reshape(10, 10)
    b = np.flipud(a).copy()
    dom = np.zeros((10, 10), bool)
    dom[2:8, 2:8] = True
    out = rank_fusion([a, b], [0.5, 0.5], dom)
    assert np.all(out[~dom] == 0)
    assert out[dom].min() >= 0 and out[dom].max() <= 1
    assert np.isfinite(out).all()


@pytest.mark.skipif(not (ROOT / "evidence/preregistration_cpx_20261028.json").exists(),
                    reason="preregistration not present")
def test_preregistration_hash_stable():
    import hashlib
    h = hashlib.sha256(
        (ROOT / "evidence/preregistration_cpx_20261028.json").read_bytes()).hexdigest()
    assert h == "35d2fc2ca5f2104b62b3c35dc7032a75274202155f7222988bf8c3fedb1ec265"
