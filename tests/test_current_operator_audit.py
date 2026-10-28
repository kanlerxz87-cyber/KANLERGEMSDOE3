"""Read-only current-source audit must never execute an unreviewed commit."""
import json
from pathlib import Path

import pytest

from scripts import audit_current_shared_operator as audit

ROOT = Path(__file__).resolve().parents[1]


def test_only_the_reviewed_commit_and_exact_source_bytes_are_executable(monkeypatch):
    calls = []
    def unexpected(*args):
        calls.append(args)
        raise AssertionError("unexpected fetch")
    monkeypatch.setattr(audit, "content_at", unexpected)
    with pytest.raises(ValueError, match="reviewed"):
        audit.audit("a" * 40)
    assert not calls
    def altered(path, commit):
        return {"sha": "a" * 40}, b"not the pinned source"
    monkeypatch.setattr(audit, "content_at", altered)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        audit.audit(audit.AUDITED_COMMIT)


def test_recorded_current_operator_result_is_a_synthetic_negative():
    report = json.loads((ROOT / "evidence/session-cfcca804-upstream-operator.json").read_text())
    assert report["commit"] == audit.AUDITED_COMMIT
    assert {Path(row["path"]).name: row["sha256"] for row in report["sources"]} == audit.SOURCES
    assert report["checks"]["empty_truth_fp_preserved"] is False
    assert report["checks"]["soft_input_behavior"] == "REJECTED"
    assert report["source_repinned"] is False and report["slot_authorized"] is False
