"""Bounded geometry, receipt binding and publication fail-closed regressions."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from scripts.audit_s2d36_peer import compare_dots
from scripts.build_cadg_site import build as build_cadg, check_session_receipt as check_cadg
from scripts.build_site import build as build_root, check_s2d36_receipt

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def test_directional_overlap_and_strict_seventy_percent_boundary():
    foot = np.ones((32, 32), dtype=bool)
    candidate = np.zeros_like(foot)
    for p in ((5, 5), (5, 6), (5, 4), (4, 5), (6, 5), (4, 6), (6, 4), (20, 20), (20, 21), (21, 20)):
        candidate[p] = True
    reference = np.zeros_like(foot)
    reference[5, 5] = True
    exactly = compare_dots(candidate, reference, foot)
    assert exactly["candidate_dots_within_3px"] == 7
    assert exactly["directed_overlap_3px"] == .70
    assert exactly["duplicate"] is False
    assert compare_dots(reference, candidate, foot)["directed_overlap_3px"] == 1.0
    candidate[20, 20] = False
    candidate[6, 6] = True
    above = compare_dots(candidate, reference, foot)
    assert above["directed_overlap_3px"] == .80
    assert above["duplicate"] is True


def test_soft_empty_outside_and_misaligned_dot_inputs_fail_closed():
    foot = np.ones((8, 8), dtype=bool)
    dots = np.zeros_like(foot)
    dots[1, 1] = True
    with pytest.raises(ValueError, match="boolean"):
        compare_dots(dots.astype(float) * .05, dots, foot)
    with pytest.raises(ValueError, match="nonempty"):
        compare_dots(np.zeros_like(dots), dots, foot)
    with pytest.raises(ValueError, match="share a grid"):
        compare_dots(dots, np.ones((4, 4), dtype=bool), foot)
    foot[1, 1] = False
    with pytest.raises(ValueError, match="inside"):
        compare_dots(dots, dots, foot)


def test_s2d_peer_receipt_binds_card_references_counts_and_negative_status():
    report = load("evidence/session-30454eca-s2d36-audit.json")
    card = (ROOT / "evidence/peer-s2d36-card-21eec80b.json").read_bytes()
    audit, registry = load("docs/audit.json"), load("research/registry-lock.json")
    check_s2d36_receipt(report, card, audit, registry)
    assert report["lattice"]["candidate_dots_within_3px_of_lattice"] == 37458
    bad_cases = []
    for field, value in (("surface_compared", True), ("complete_registry_compared", True),
                         ("slot_authorized", True), ("verdict", "promote")):
        changed = copy.deepcopy(report); changed[field] = value; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["peer"]["sha256"] = "0" * 64; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["peer"]["source_holdout"]["ci95"] = [0.9, 1]; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["nine_historical_final_dot_comparisons"].pop(); bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["nine_historical_final_dot_comparisons"][0]["duplicate"] = False; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["nine_historical_final_dot_comparisons"][0]["directed_overlap_3px"] = .1; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["validator"]["portal_acceptance_verified"] = True; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["validator"]["checks"]["no_nan_inside_footprint"] = False; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["lattice"]["geometry"]["crs"] = "EPSG:4326"; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["lattice"]["strict_nan_outside"] = True; bad_cases.append(changed)
    changed = copy.deepcopy(report); changed["lattice"]["candidate_dots_within_3px_of_lattice"] = 1; bad_cases.append(changed)
    for bad in bad_cases:
        with pytest.raises(ValueError):
            check_s2d36_receipt(bad, card, audit, registry)
    with pytest.raises(ValueError):
        check_s2d36_receipt(report, card + b" ", audit, registry)


def test_cadg_receipt_keeps_full_and_catalogue_excluded_scopes_distinct():
    card, report = load("evidence/cadg-submod-run-card.json"), load("evidence/session-30454eca-cadg-lattice.json")
    check_cadg(card, report)
    assert report["full_registered_lattice"]["candidate_dots_within_3px_of_lattice"] == 37630
    assert report["catalogue_excluded_lattice"]["candidate_dots_within_3px"] == 37553
    assert report["full_registered_lattice"]["candidate_dot_overlap_fraction"] > report["catalogue_excluded_lattice"]["directed_overlap_3px"] > .70
    for field, bad in (("candidate_sha256", "0" * 64), ("candidate_dots_within_3px_of_lattice", 1),
                       ("duplicate_over_70_percent", False)):
        changed = copy.deepcopy(report); changed["full_registered_lattice"][field] = bad
        with pytest.raises(ValueError):
            check_cadg(card, changed)
    changed = copy.deepcopy(report); changed["slot_authorized"] = True
    with pytest.raises(ValueError):
        check_cadg(card, changed)
    assert (ROOT / "evidence/cadg-submod-run-card.json").read_bytes() == (ROOT / "docs/cadg-submod/run-card.json").read_bytes()


def test_both_generated_sites_and_public_receipts_are_consistent_without_writes():
    build_root(check_only=True)
    build_cadg(check_only=True)
    for name in ("session-30454eca-s2d36-audit.json", "session-30454eca-cadg-lattice.json",
                 "session-30454eca-saturation.json", "session-30454eca-run-card.json"):
        assert (ROOT / "evidence" / name).read_bytes() == (ROOT / "docs/data" / name).read_bytes()
    for page in (ROOT / "docs/cadg-submod/index.html", ROOT / "docs/cadg-submod/executive-summary.html",
                 ROOT / "docs/cadg-submod/EXECUTIVE_SUMMARY.md", ROOT / "docs/cadg-submod/README.md"):
        text = page.read_text()
        assert "DO NOT SUBMIT" in text
        assert "99.94%" in text or "99.9363%" in text
        assert "99.73%" in text or "99.7318%" in text
        assert "prevents \"Predicted values" not in text
        assert "After Human Selector Sign-Off" not in text
        assert 'href="downloads/' not in text.lower()


def test_staging_and_legacy_builder_refuse_stale_or_obsolete_root_pages():
    from scripts.build_site_previous import build as legacy_build
    page = ROOT / "docs/index.html"
    original = page.read_bytes()
    with pytest.raises(RuntimeError, match="Archived builder"):
        legacy_build()
    assert page.read_bytes() == original
    try:
        page.write_text("stale test sentinel")
        with pytest.raises(ValueError, match="stale"):
            build_root(check_only=True)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/stage_pages.py")], capture_output=True, text=True)
        assert result.returncode != 0
        assert "stale" in result.stderr
        assert page.read_text() == "stale test sentinel"
    finally:
        page.write_bytes(original)
    build_root(check_only=True)


def test_cadg_check_mode_does_not_repair_stale_page():
    page = ROOT / "docs/cadg-submod/executive-summary.html"
    original = page.read_bytes()
    try:
        page.write_text("stale CADG sentinel")
        with pytest.raises(ValueError, match="stale"):
            build_cadg(check_only=True)
        assert page.read_text() == "stale CADG sentinel"
    finally:
        page.write_bytes(original)
    build_cadg(check_only=True)


def test_publication_workflows_check_before_mutating_tests():
    for name in ("checks.yml", "pages.yml", "ssp1-pages.yml"):
        workflow = (ROOT / ".github/workflows" / name).read_text()
        assert workflow.index("build_site.py --check") < workflow.index("pytest -q"), name
        assert workflow.index("build_cadg_site.py --check") < workflow.index("pytest -q"), name
