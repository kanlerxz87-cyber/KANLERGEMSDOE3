"""Invariants for the 28 Oct 2026 catalogue-blind submission desk and run card.

These read only committed evidence files; they do not need restored competition data.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "evidence/run-card-catalogue-blind-20261028.json"
PAGE = ROOT / "docs/submission-desk.html"
SITES = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}


def card():
    return json.loads(CARD.read_text())


def test_run_card_is_fail_closed():
    c = card()
    assert c["verdict"] == "NEGATIVE_HOLDOUT_NOT_BEATEN"
    assert c["slot_authorized"] is False
    assert c["weekly_slots_spent"] == 0
    assert c["organizer_confirmed_scores"] == []
    assert c["candidate"]["authorized"] is False
    assert c["candidate"]["cleared_for_submission"] is False
    assert "NOT SAFE" in c["candidate"]["safety"]


def test_budget_and_stop_rules_are_respected():
    c = card()
    assert c["experiments"]["used"] <= c["experiments"]["budget"] == 3
    assert c["time_budget_minutes"] == 120
    assert c["duplicate_stop"]["spearman_limit"] == 0.90
    assert c["duplicate_stop"]["overlap_limit_3px"] == 0.70
    assert c["duplicate_stop"]["spearman_triggered"] is False
    assert c["leakage_canary"]["single_feature_max_auc_vs_offcatalogue_sgmc"] <= c["leakage_canary"]["threshold_auc"]


def test_candidate_name_and_note_within_limit():
    c = card()["candidate"]
    assert len(c["name"]) <= 140
    assert len(c["note"]) <= 140
    assert c["note_chars"] == len(c["note"])


def test_candidate_format_and_holdout_recorded():
    c = card()["candidate"]
    assert c["format"]["format_valid"] is True
    assert c["format"]["footprint_pixels"] == 5_167_373
    assert c["holdout_on_file"]["label"] == "HOLDOUT-DTI"
    assert c["bytes"] == (ROOT / c["file"]).stat().st_size


def test_page_states_no_submission_and_labels_numbers():
    html = PAGE.read_text()
    assert "DO NOT SUBMIT" in html
    assert "NOT SAFE TO SUBMIT" in html
    assert "ORGANIZER-CONFIRMED" in html
    for site in SITES:
        assert site in html


def test_generator_check_mode_passes():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_submission_desk.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_lineage_claims_are_exact_and_audited():
    lx = json.loads((ROOT / "evidence/catalogue-blind-audits-20261028.json").read_text())["lineage_exact"]
    assert lx["GEMSDOE32_subset_of_GEMSDOE31"] is True
    assert lx["removed_31_to_32"] == lx["removed_31_to_32_within_2px_of_catalogue"] == lx["GEMSDOE31_dots_within_2px_of_catalogue"] == 2545
    assert lx["added_32_to_36"] == 1200 and lx["added_32_to_36_within_2px_of_catalogue"] == 0


def test_page_has_no_unrendered_template_fields():
    html = PAGE.read_text()
    import re
    assert re.search(r"\{[A-Za-z_]+[\[\]\"\x27]", html) is None
    assert "{0, 1}" in html
