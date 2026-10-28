import json
from pathlib import Path

from scripts.audit_upstream_prerequisites import ISSUES, validate_receipt

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def test_upstream_prerequisite_receipt_is_fail_closed_and_complete():
    receipt = load("evidence/session-e2903b2e-upstream-prerequisites.json")
    assert validate_receipt(receipt) == []
    assert {row["number"] for row in receipt["upstream_issues"]} == set(ISSUES)
    assert all(row["state"] == "OPEN" for row in receipt["upstream_issues"])
    assert receipt["current_shared_files_byte_identical_to_pinned"] is True
    cache = receipt["canonical_feature_cache"]
    assert cache["receipt_declares_sha256"] is False
    assert cache["declared_sha256"] is None
    assert cache["cache_bytes_in_repository_tree"] is False
    assert cache["usable_for_protocol_reuse"] is False
    assert receipt["local_synthetic_operator_audit"]["ok"] is False
    assert receipt["candidate_generated"] is False
    assert receipt["holdout_dti"] is None
    assert receipt["leaderboard_estimate"] is None
    assert receipt["ok_to_submit"] is False


def test_current_session_card_does_not_invent_a_candidate_or_score():
    card = load("evidence/session-e2903b2e-run-card.json")
    config = load("config/research-session-e2903b2e.json")
    assert card["session_id"] == config["session_id"] == "e2903b2e"
    assert config["assigned_method_paragraph"] is None
    assert config["geological_experiments"] == []
    assert card["geological_experiments_this_session"] == 0
    assert card["holdout_dti"] is None
    assert card["holdout_ci95"] is None
    assert card["surface_registry_comparison"] is None
    assert card["final_dot_registry_comparison"] is None
    assert card["raster_sha256"] is None
    assert card["validator_output"]["status"].startswith("NOT RUN")
    assert card["submission_name"] is None
    assert 0 < len(card["submission_note"]) <= 140
    assert card["ok_to_download_for_submission"] is False
    assert card["ok_to_submit"] is False
    assert card["slot_authorized"] is False
    assert card["verdict"] == "negative"


def test_current_negative_card_and_prerequisites_are_published_without_download():
    source_card = ROOT / "evidence/session-e2903b2e-run-card.json"
    published_card = ROOT / "docs/data/session-e2903b2e-run-card.json"
    assert published_card.read_bytes() == source_card.read_bytes()
    page = (ROOT / "docs/index.html").read_text()
    assert "No eligible TIFF yet" in page
    assert "Download unavailable · DO NOT SUBMIT" in page
    assert "Issue #53" in page
    assert "upstream-prerequisites-20261027.json" in page
    assert "session-e2903b2e-run-card.json" in page
    assert "download=\"KANLER_GEMS" not in page


def test_future_cache_metadata_alone_cannot_approve_reuse():
    import copy
    receipt = load("evidence/session-e2903b2e-upstream-prerequisites.json")
    future = copy.deepcopy(receipt)
    cache = future["canonical_feature_cache"]
    cache.update(receipt_declares_sha256=True, declared_sha256="a" * 64,
                 cache_bytes_in_repository_tree=True, usable_for_protocol_reuse=False)
    assert validate_receipt(future) == []
    cache["usable_for_protocol_reuse"] = True
    assert "cache_reuse_claim" in validate_receipt(future)


def test_failed_prerequisite_refresh_replaces_stale_snapshot(tmp_path, monkeypatch):
    import sys
    import scripts.audit_upstream_prerequisites as audit
    output = tmp_path / "snapshot.json"
    output.write_text('{"research_ready":true}')
    def fail():
        raise ValueError("offline")
    monkeypatch.setattr(audit, "audit", fail)
    monkeypatch.setattr(sys, "argv", ["audit", "--output", str(output)])
    assert audit.main() == 1
    result = json.loads(output.read_text())
    assert result["status"] == "UNKNOWN_REFRESH_FAILED"
    assert result["research_ready"] is False
    assert result["ok_to_submit"] is False
    assert result["slot_authorized"] is False
