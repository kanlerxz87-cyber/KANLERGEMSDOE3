"""Readiness receipts are consistency evidence, never organizer authentication."""
from copy import deepcopy

import pytest

from scripts.preflight import operator_receipt_matches


def fixture():
    lock = {"ok": True, "commit": "a" * 40, "repository": "example/repo",
            "manifest_sha256": "b" * 64, "files_checked": 13, "failures": []}
    receipt = {"schema_version": 1,
               "kind": "SYNTHETIC OPERATOR AUDIT — NOT HOLDOUT-DTI",
               "ok": True, "source_lock": deepcopy(lock), "blocking_findings": [],
               "checks": {"empty_truth_cell_fp_preserved_in_pooled_totals": True}}
    return lock, receipt


def test_matching_receipt():
    lock, receipt = fixture()
    assert operator_receipt_matches(receipt, lock)


@pytest.mark.parametrize("field,value", [
    ("manifest_sha256", "c" * 64), ("repository", "different/repo"),
    ("files_checked", 12), ("ok", False), ("failures", ["modified"]),
])
def test_commit_label_cannot_override_other_source_identity(field, value):
    lock, receipt = fixture()
    receipt["source_lock"][field] = value
    assert not operator_receipt_matches(receipt, lock)


@pytest.mark.parametrize("receipt", [None, [], {}, {"ok": True}])
def test_missing_or_malformed_receipt(receipt):
    lock, _ = fixture()
    assert not operator_receipt_matches(receipt, lock)


def test_contradictory_check_or_blocking_finding_cannot_pass():
    lock, receipt = fixture()
    receipt["checks"]["empty_truth_cell_fp_preserved_in_pooled_totals"] = False
    assert not operator_receipt_matches(receipt, lock)
    lock, receipt = fixture()
    receipt["blocking_findings"] = ["unresolved defect"]
    assert not operator_receipt_matches(receipt, lock)
    lock, receipt = fixture()
    del lock["manifest_sha256"]
    assert not operator_receipt_matches(receipt, lock)
