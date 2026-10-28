import json
import re
from pathlib import Path

from scripts.audit_upstream_prerequisites import validate_receipt

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text())


def test_current_preflight_is_fail_closed_and_budget_is_not_reset():
    receipt = load("evidence/session-20261028-preflight.json")
    assert receipt["snapshot_not_live"] is True
    assert receipt["research_ready"] is False
    assert receipt["submit_ready"] is False
    assert receipt["slot_authorized"] is False
    assert receipt["experiments_used"] == 0
    assert receipt["submission_slots_used"] == 0
    assert any("time budget exhausted" in item.lower() for item in receipt["failures"])
    assert receipt["holdout_dti"] is None
    assert receipt["leaderboard_estimate"] is None
    assert receipt["input_organizer_authenticated"] is False


def test_current_peer_observations_are_hash_bound_claims_not_approval():
    feed = load("evidence/session-20261028-focus-feed.json")
    observations = load("evidence/session-20261028-peer-source-observations.json")
    assert feed["registry_complete"] is False
    assert len(feed["rows"]) == len(observations["rows"]) == 9
    assert observations["sources_are_official_competition_records"] is False
    assert observations["all_sites_explicitly_not_approved_by_this_review"] is True
    by_site = {row["site"]: row for row in feed["rows"]}
    for row in observations["rows"]:
        assert row["site"] in by_site
        assert row["commit"] == by_site[row["site"]]["commit"]
        assert re.fullmatch(r"[0-9a-f]{64}", row["page_sha256"])
        assert row["score_receipt_present"] is False
        assert row["independently_replayed"] is False
        assert row["approved_for_submission"] is False
        assert row["evidence_class"] == "PARTICIPANT_PAGE_CLAIM_NOT_OFFICIAL_SCORE_RECEIPT"


def test_current_upstream_receipt_and_synthetic_diagnostic_stay_separate_from_scores():
    receipt = load("evidence/session-20261028-upstream-prerequisites.json")
    assert validate_receipt(receipt) == []
    assert receipt["participant_source"]["head_commit"] == "109f364fb39030e40ef51b839b79cf694123b51b"
    assert receipt["current_shared_files_byte_identical_to_pinned"] is False
    assert receipt["canonical_feature_cache"]["declared_sha256"] is None
    assert receipt["canonical_feature_cache"]["cache_bytes_in_repository_tree"] is False
    assert receipt["holdout_dti"] is None
    assert receipt["leaderboard_estimate"] is None

    diagnostic = load("evidence/session-20261028-upstream-operator-audit.json")
    assert diagnostic["kind"].endswith("NOT HOLDOUT-DTI")
    assert diagnostic["geological_data_used"] is False
    assert diagnostic["candidate_raster_generated"] is False
    assert diagnostic["score_claimed"] is False
    assert diagnostic["results"]["fold_false_positive_mass"] == 1.0
    assert diagnostic["results"]["pooled_block_false_positive_mass"] == 0.0
    assert 0.9722 < diagnostic["results"]["conservation_recomputed_diagnostic"] < 0.9723
    assert diagnostic["soft_mask_validation"]["rejected"] is True


def test_current_run_card_has_no_candidate_score_or_submission_authority():
    card = load("evidence/session-20261028-run-card.json")
    assert card["assigned_method_paragraph"] is None
    assert card["geological_experiments_this_session"] == 0
    assert card["experiment_budget"]["fixed_clock_expired"] is True
    assert card["experiment_budget"]["new_budget_authorized"] is False
    assert card["holdout_dti"] is None and card["holdout_ci95"] is None
    assert card["evaluator_version"] is None and card["withheld_positive_count"] is None
    assert card["raster_sha256"] is None
    assert card["correlation_overlap_vs_registry"]["pre_placement_surface"]["max_abs_spearman_rho"] is None
    assert card["correlation_overlap_vs_registry"]["final_dot_mask"]["max_directed_dot_overlap_3px"] is None
    assert card["validator_output"]["status"].startswith("NOT RUN")
    assert card["validator_output"]["single_band_float32"] is None
    assert card["validator_output"]["crs_shape_transform_match"] is None
    assert card["submission_name"] is None
    assert 0 < len(card["submission_note"]) <= 140
    assert card["candidate_generated"] is False
    assert card["leaderboard_estimate"] is None
    assert card["slot_authorized"] is False
    assert card["ok_to_download_for_submission"] is False
    assert card["ok_to_submit"] is False
    assert card["verdict"] == "negative"


def test_one_canonical_hypothesis_queue_is_conditional_not_a_lane():
    rows = load("research/hypotheses.json")
    assert len(rows) == 4
    assert [row["rank"] for row in rows] == [1, 2, 3, 4]
    required = {"layers", "signature", "missing_fault_rationale", "difference", "non_fault_mimic", "cost", "expected_improvement", "viability", "source"}
    assert all(required <= set(row) for row in rows)
    text = (ROOT / "research/hypotheses.md").read_text()
    assert "only active qualitative queue" in text
    assert "missing assigned method paragraph" in text
    assert "clock inherited" in text and "is exhausted" in text


def test_site_builder_publishes_latest_negative_evidence_without_a_download():
    homepage = (ROOT / "docs/index.html").read_text()
    assert "28 October 2026" in homepage
    assert "Raw core TIFFs" in homepage
    assert "Current-source review" in homepage
    assert "What each pinned participant page says now" in homepage
    assert "Current negative JSON card" in homepage
    assert "109f364fb390" in homepage
    assert "DO NOT SUBMIT" in homepage
    assert 'download="KANLER_GEMS' not in homepage
    assert (ROOT / "docs/data/session-20261028-run-card.json").read_bytes() == (ROOT / "evidence/session-20261028-run-card.json").read_bytes()
    assert (ROOT / "docs/data/session-20261028-preflight.json").is_file()
    assert json.loads((ROOT / "docs/data/current-hypotheses.json").read_text()) == load("research/hypotheses.json")
    assert len(list((ROOT / "docs/sites").glob("GEMSDOE*.html"))) == 9
    for path in (ROOT / "docs/sites").glob("GEMSDOE*.html"):
        text = path.read_text()
        assert "Latest participant-page observation" in text
        assert "not an organizer record" in text
