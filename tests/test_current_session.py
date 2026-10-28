import json
from pathlib import Path

from scripts.audit_upstream_prerequisites import ISSUES, validate_receipt

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def test_corrected_upstream_prerequisite_receipt_is_fail_closed_and_scoped():
    receipt = load("evidence/session-20261028-upstream-prerequisites.json")
    assert validate_receipt(receipt) == []
    assert {row["number"] for row in receipt["upstream_issues"]} == set(ISSUES)
    assert all(row["state"] == "OPEN" for row in receipt["upstream_issues"])
    assert receipt["participant_source"]["head_commit"] == "109f364fb39030e40ef51b839b79cf694123b51b"
    assert receipt["current_shared_files_byte_identical_to_pinned"] is False
    contracts = receipt["source_contract_review"]
    assert contracts["binary_soft_input_guard"]["status"] == "SOURCE_GUARD_PRESENT_NOT_DYNAMICALLY_TESTED"
    assert contracts["binary_soft_input_guard"]["dynamic_test_at_current_head"] is False
    assert contracts["outside_footprint_validator"]["status"] == "SOURCE_GUARD_PRESENT_NOT_DYNAMICALLY_TESTED"
    assert contracts["zero_truth_cell_pooled_fp"]["status"] == "SOURCE_LEVEL_OMISSION_PRESENT"
    assert contracts["zero_truth_cell_pooled_fp"]["dynamic_test_at_current_head"] is False
    assert contracts["strict_all_registry_dot_gate"]["status"] == "LATTICE_EXCLUDED_FROM_ONE_RUNNER_OVERLAP_THRESHOLD"
    cache = receipt["canonical_feature_cache"]
    assert cache["receipt_declares_sha256"] is False
    assert cache["declared_sha256"] is None
    assert cache["cache_bytes_in_repository_tree"] is False
    assert cache["usable_for_protocol_reuse"] is False
    assert receipt["local_synthetic_operator_audit"]["tested_source_commit"] == "400b60d4a6d99f425ee90504e6c4552227556dd1"
    assert receipt["local_synthetic_operator_audit"]["current_head_dynamic_tested"] is False
    assert receipt["local_synthetic_operator_audit"]["geological_model_evaluated"] is False
    assert receipt["research_ready"] is False
    assert receipt["candidate_generated"] is False
    assert receipt["holdout_dti"] is None
    assert receipt["leaderboard_estimate"] is None
    assert receipt["ok_to_submit"] is False


def test_current_run_card_has_no_candidate_score_or_slot_and_note_is_bounded():
    card = load("evidence/session-20261028-run-card.json")
    config = load("config/research-session-e2903b2e.json")
    assert card["session_id"] == "session-20261028-review"
    assert config["assigned_method_paragraph"] is None
    assert card["geological_experiments"] == 0
    assert card["experiment_budget"]["status"] == "EXPIRED"
    assert card["experiment_budget"]["reset_or_extended"] is False
    assert card["holdout_dti"] is None
    assert card["holdout_ci95"] is None
    assert card["surface_registry_comparison"]["performed"] is False
    assert card["final_dot_registry_comparison"]["performed"] is False
    assert card["raster_sha256"] is None
    assert card["validator_output"]["status"] == "NOT_RUN_NO_CANDIDATE"
    assert card["submission_name"] is None
    assert len(card["submission_note"]) == card["submission_note_character_count"] <= 140
    assert card["ok_to_download_for_submission"] is False
    assert card["ok_to_submit"] is False
    assert card["slot_authorized"] is False
    assert card["verdict"] == "negative"


def test_current_negative_card_and_source_audit_are_published_without_download():
    source_card = ROOT / "evidence/session-20261028-run-card.json"
    published_card = ROOT / "docs/data/session-20261028-run-card.json"
    source_audit = ROOT / "evidence/session-20261028-upstream-prerequisites.json"
    published_audit = ROOT / "docs/upstream-prerequisites-20261028.json"
    page = (ROOT / "docs/index.html").read_text()
    assert published_card.read_bytes() == source_card.read_bytes()
    assert published_audit.read_bytes() == source_audit.read_bytes()
    assert "No eligible TIFF yet" in page
    assert "Download unavailable · DO NOT SUBMIT" in page
    assert "Current participant-page decisions" in page
    assert "All nine current pages say no-submit" in page
    assert "109f364fb390" in page
    assert "upstream-prerequisites-20261028.json" in page
    assert "focus-source-review-20261028.json" in page
    assert "session-20261028-run-card.json" in page
    assert 'download="KANLER_GEMS' not in page


def test_persistent_prompt_is_kept_in_readme_and_project_file():
    readme = (ROOT / "README.md").read_text()
    prompt = (ROOT / "PROJECT_PROMPT.md").read_text()
    assert "## Full standing user request" in readme
    assert "Maximize P(Win)" in readme
    assert "Own the Outcome" in readme
    assert "Maximize P(Win)" in prompt
    assert "Own the Outcome" in prompt
