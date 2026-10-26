import numpy as np
import pytest
from scipy.ndimage import binary_dilation
from scipy.stats import spearmanr

from audit_focus import binary_spearman, summarize_pair
from preflight import witness_certificate


def near3(x):
    y, z = np.ogrid[-3:4, -3:4]
    return binary_dilation(x, structure=(y*y + z*z <= 9))


def test_dense_is_a_universal_witness():
    footprint = np.ones((9, 9), bool)
    dense = np.full((9, 9), np.nextafter(np.float32(0), np.float32(1)))
    r = witness_certificate(footprint, dense, near3, budget=5)
    assert r['universal_blocker'] and r['positive_inside_footprint'] == 81
    assert r['overlap_lower_bound_at_example_budget'] == 1.0
    for y, x in [(0, 0), (4, 4), (8, 8)]:
        assert near3(dense > 0)[y, x]


def test_lower_bound_is_correct_with_uncovered_cells():
    valid = np.ones((8, 8), bool)
    witness = np.zeros_like(valid, dtype=float)
    witness[0, 0] = 1
    out = witness_certificate(valid, witness, near3, budget=60)
    uncovered = int((~near3(witness > 0)).sum())
    assert out['uncovered_cells'] == uncovered
    assert out['overlap_lower_bound_at_example_budget'] == pytest.approx(1 - uncovered/60)
    assert not out['universal_blocker']


def test_nonpositive_and_nan_not_support_and_footprint_is_respected():
    valid = np.ones((3, 3), bool)
    valid[2, 2] = False
    a = np.array([[np.nan, -1, 0], [0, 0, 0], [0, 0, 100.]])
    r = witness_certificate(valid, a, near3, budget=3)
    assert r['positive_inside_footprint'] == 0
    # Reference dots outside the footprint still count as nearby, per shared rule.
    assert r['fraction_within_3px'] > 0


@pytest.mark.parametrize('shape,budget', [((0, 0), 1), ((3,), 1), ((2, 2), 0), ((2, 2), 5)])
def test_invalid_preflight_never_produces_certificate(shape, budget):
    with pytest.raises(ValueError):
        witness_certificate(np.ones(shape, bool), np.ones(shape), lambda x: x, budget=budget)


def test_shape_and_broken_near_fail_closed():
    with pytest.raises(ValueError):
        witness_certificate(np.ones((3, 3)), np.ones((3, 4)), near3, budget=2)
    with pytest.raises(ValueError):
        witness_certificate(np.ones((3, 3)), np.ones((3, 3)), lambda x: x[:2], budget=2)


def test_binary_spearman_matches_scipy_midrank():
    rng = np.random.default_rng(2048)
    l = rng.random((50, 80)) < .2
    r = rng.random((50, 80)) < .35
    valid = rng.random((50, 80)) > .1
    assert binary_spearman(l, r, valid) == pytest.approx(spearmanr(l[valid], r[valid]).statistic)
    assert binary_spearman(np.zeros((2, 2)), np.ones((2, 2)), np.ones((2, 2))) is None


def test_overlap_is_directional_strict_and_empty_is_undefined():
    valid = np.ones((1, 10), bool)
    mine = valid.copy()
    theirs = np.array([[1, 1, 1, 1, 1, 1, 1, 0, 0, 0]], bool)
    # Constant mine makes rho undefined, isolating the 70% boundary.
    exact = summarize_pair(mine, theirs, valid, theirs)
    assert exact['forward_overlap_3px'] == pytest.approx(.7)
    assert not exact['duplicate_by_literal_threshold']
    more = summarize_pair(mine, theirs, valid, np.array([[1]*8 + [0]*2]))
    assert more['duplicate_by_literal_threshold']
    empty = summarize_pair(np.zeros_like(valid), theirs, valid, theirs)
    assert empty['forward_overlap_3px'] is None
    assert not empty['duplicate_by_literal_threshold']
    reverse = summarize_pair(theirs, mine, valid, mine)
    assert reverse['forward_overlap_3px'] == 1


def test_rho_alone_can_trigger_duplicate():
    valid = np.ones((4, 4), bool)
    mine = np.indices((4,4)).sum(axis=0) % 2 == 0
    result = summarize_pair(mine, mine, valid, np.zeros_like(valid))
    assert result['forward_overlap_3px'] == 0
    assert result['spearman'] == pytest.approx(1)
    assert result['duplicate_by_literal_threshold']
