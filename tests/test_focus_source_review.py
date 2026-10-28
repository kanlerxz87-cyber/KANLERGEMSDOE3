from __future__ import annotations

import json
from pathlib import Path

from scripts.build_focus_source_review import build

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str):
    return json.loads((ROOT / relative).read_text())


def test_current_nine_site_review_is_pinned_negative_and_not_a_raster_audit():
    receipt = read("evidence/session-20261028-focus-source-review.json")
    rebuilt = build()
    assert receipt["feed_hashes"] == rebuilt["feed_hashes"]
    assert receipt["feeds_consistent_for_all_nine"] is True
    assert receipt["all_nine_heads_differ_from_previous_registry"] is True
    assert receipt["raster_audit"]["current_refreshed_tree_raster_audit_performed"] is False
    assert receipt["raster_audit"]["complete_representation_resolved_registry"] is False
    assert receipt["raster_audit"]["novelty_clearance"] is False
    assert receipt["decision"].startswith("DO NOT SUBMIT")
    assert receipt["candidate_generated"] is False
    assert receipt["slot_authorized"] is False
    assert receipt["organizer_confirmed_score"] is None
    assert receipt["leaderboard_estimate"] is None


def test_each_current_participant_page_is_bound_to_its_pinned_source_blob():
    receipt = read("evidence/session-20261028-focus-source-review.json")
    feed = read("docs/data/focus-feed.json")
    by_site = {row["site"]: row for row in feed["rows"]}
    assert len(receipt["current_site_decisions"]) == 9
    for row in receipt["current_site_decisions"]:
        current = by_site[row["site"]]
        assert row["commit"] == current["commit"]
        assert row["source_page"] == current["source_page"]
        assert row["source_url"] == current["source_url"]
        assert len(row["source_page_sha256"]) == 64
        assert len(row["source_page_git_blob_sha1"]) == 40
        assert row["evidence_class"] == "PARTICIPANT_SOURCE_PAGE_NOT_ORGANIZER_RECEIPT"
        assert "SUBMIT" in row["participant_page_decision_summary"].upper()
