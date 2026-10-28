"""Schema-only paired-comparison regressions; no fabricated card can authorize a slot."""
import copy

import pytest

from scripts.promotion_gate import REQUIRED_TRUE, VALIDATOR_CHECKS, assess


def valid_fixture():
    card = {name: True for name in REQUIRED_TRUE}
    card.update({
        "surface_max_rank_correlation": .3, "final_max_rank_correlation": .2,
        "surface_dot_overlap_3px": .3, "final_dot_overlap_3px": .2,
        "max_feature_auc": .7, "candidate_id": "candidate", "paired_improvement_ci95": [.01, .03],
        "holdout": {"class": "HOLDOUT-DTI", "evaluator_version": "fixture-v1", "withheld_positives": 20,
                    "value": .3, "ci95": [.2, .4], "alpha": .2, "beta": .8,
                    "kernel_m": 300, "kernel": "triangular", "aggregation": "pooled", "fold_sha256": "b" * 64},
        "incumbent_comparison": {"strongest_same_evaluator_incumbent": "best", "incumbent_holdout_dti": .28},
        "paired_comparison": {"candidate_id": "candidate", "incumbent_id": "best", "candidate_value": .3,
                              "incumbent_value": .28, "delta": .02, "ci95": [.01, .03],
                              "evaluator_version": "fixture-v1", "withheld_positives": 20, "fold_sha256": "b" * 64},
        "validator": {name: True for name in VALIDATOR_CHECKS}, "raster_sha256": "a" * 64,
        "hypothesis": "synthetic", "mechanism": "test", "non_fault_mimic": "test",
        "submission_name": "fixture", "submission_note": "fixture only",
    })
    return card


def test_bound_synthetic_schema_is_not_permission_to_submit():
    result = assess(valid_fixture())
    assert result["schema_status"] == "complete"
    assert result["verdict"] == "negative" and not result["promotion_evaluated"] and not result["slot_authorized"]


@pytest.mark.parametrize("mutation", [
    lambda c: c["paired_comparison"].update(incumbent_id="easier_baseline"),
    lambda c: c["paired_comparison"].update(candidate_id="different_candidate"),
    lambda c: c["paired_comparison"].update(fold_sha256="c" * 64),
    lambda c: c["paired_comparison"].update(evaluator_version="different-version"),
    lambda c: c["paired_comparison"].update(withheld_positives=19),
    lambda c: c["paired_comparison"].update(withheld_positives=True),
    lambda c: c["paired_comparison"].update(incumbent_value=.27),
    lambda c: c["paired_comparison"].update(candidate_value=.31),
    lambda c: c["paired_comparison"].update(delta=.019),
    lambda c: c["paired_comparison"].update(ci95=[.02, .04]),
    lambda c: c["holdout"].update(fold_sha256="bad"),
    lambda c: c.update(paired_comparison=None),
])
def test_unbound_or_malformed_paired_evidence_fails_closed(mutation):
    card = copy.deepcopy(valid_fixture())
    mutation(card)
    result = assess(card)
    assert result["schema_status"] == "incomplete"
    assert "paired_incumbent_binding" in result["failures"]
    assert not result["slot_authorized"]
