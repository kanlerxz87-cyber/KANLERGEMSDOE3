import sys

import numpy as np
import pytest

from bootstrap import ensure_template

sys.path.insert(0, str(ensure_template() / "vendor"))
from gems57 import metric, evaluate_holdout  # noqa: E402


def brute_force(p, truth):
    """Independent literal transcription of organizer's probabilistic formula."""
    gs = np.argwhere(truth)
    xs = np.argwhere(p > 0)
    def k(a, b):
        return max(1.0 - float(np.linalg.norm(a - b)) / 3.0, 0.0)
    tp = sum(max((p[tuple(x)] * k(g, x) for x in xs), default=0.0) for g in gs)
    fp = sum(p[tuple(x)] * (1 - max((k(x, g) for g in gs), default=0.0)) for x in xs)
    fn = len(gs) - tp
    return tp, fp, fn, tp / (tp + .2 * fp + .8 * fn + metric.EPS)


def test_shared_soft_metric_matches_literal_organizer_equations():
    p = np.zeros((7, 8), np.float64)
    p[1, 1] = .25; p[1, 2] = .8; p[4, 5] = 1; p[6, 0] = .4
    g = np.zeros_like(p, dtype=bool)
    g[1, 1] = True; g[2, 3] = True; g[5, 5] = True
    expected = brute_force(p, g)
    actual = metric.dti_exact(p, g)
    np.testing.assert_allclose([actual[k] for k in ("tp", "fp", "fn", "dti")], expected, atol=1e-12)
    assert metric.ALPHA == .2 and metric.BETA == .8 and metric.R_M == 300


def test_one_prediction_can_cover_multiple_truth_cells():
    # The upstream metric docstring says dT <= k_self; that is false in general.
    p = np.zeros((5, 5), np.float64); p[2, 2] = 1
    g = np.zeros_like(p, dtype=bool); g[2, 1] = g[2, 3] = True
    result = metric.dti_exact(p, g)
    self_credit = 2 / 3
    assert result["tp"] == pytest.approx(4 / 3)
    assert result["tp"] > self_credit
    # The shared implementation computes the sum correctly; the defect is prose.


def test_holdout_masks_visible_pixels_exactly_before_scoring():
    p = np.zeros((8, 9), dtype=np.float32)
    p[2, 2] = 1; p[6, 7] = .75
    g = np.zeros_like(p, bool); g[2, 2] = True; g[6, 7] = True
    visible = np.zeros_like(g); visible[2, 2] = True
    fold = {"truth": g, "visible": visible, "region": np.ones_like(g)}
    result, terms = evaluate_holdout.evaluate(p, fold, np.ones_like(g), block_side=3)
    assert result["n_truth"] == 1 and result["n_emitted"] == 1
    assert result["tpw"] == pytest.approx(.75)
    np.testing.assert_allclose(terms.sum(axis=0), [result["tpw"], result["fpw"], result["fnw"], 1])
    assert result["evaluator_version"] == "gems57-pooled-hide-v2"


def test_pooled_evaluator_rejects_unpaired_truth_counts():
    a = np.zeros((3, 4)); b = a.copy()
    a[0, 3] = 2; b[0, 3] = 1
    with pytest.raises(ValueError, match="same integer truth count"):
        evaluate_holdout.pooled_summary({"candidate": a, "control": b}, draws=20, candidate="candidate")
