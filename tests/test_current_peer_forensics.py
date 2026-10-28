"""Regression tests for the dated 2026-10-28 bounded peer audit.

These tests guard evidence scope and fail-closed presentation. They do not treat
participant source trees, local holdouts, or geometric comparisons as organizer
scores or upload permission.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str):
    return json.loads((ROOT / relative).read_text())


def test_focus_peer_forensics_is_bounded_and_all_nine_sites_are_present():
    report = load("evidence/nine_site_and_peer_forensics_20261028.json")
    assert report["repos_audited"] == 35
    assert len(report["priority_9_sites"]) == 9
    assert {row["site"] for row in report["priority_9_sites"]} == {
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    }
    assert report["peer_cache_unique_full_grid_rasters"] == 249
    assert all(0 < row["selected_unique_rasters"] <= 12 for row in report["priority_9_sites"])
    assert report["lattice_s5_footprint_geometry"]["footprint_pixels_uncovered_gt_3px"] == 6649
    assert report["lattice_s5_footprint_geometry"]["uncovered_within_5px_of_outer_border"] == 6493
    g30 = next(row for row in report["flagged_20261028_ecosystem_irregularities"] if row["id"] == "IR-20261028-G30-BORDER-TRAP")["details"]
    assert g30["dots_in_footprint"] == 6649
    assert g30["dots_within_5px_of_outer_survey_border"] == 6493
    assert g30["lattice_s5_3px_overlap"] == 0.0


def test_current_candidate_audit_is_bound_to_atsc_bytes_and_negative():
    audit = load("evidence/atsc-current-peer-audit-20261028.json")
    card = load("evidence/atsc-submod-run-card.json")
    assert audit["candidate"]["sha256"] == card["raster_sha256"]
    assert audit["candidate"]["dots_in_footprint"] == 37654
    scope = audit["peer_registry_scope"]
    assert scope["rasters_compared"] == 249
    assert scope["genuine_detectors_compared"] == 244
    assert scope["complete_registry"] is False
    result = audit["result"]
    assert result["max_final_dot_overlap_3px_genuine_detectors"] <= 0.70
    assert result["max_final_dot_overlap_3px_calibration_or_continuous_probes"] > 0.70
    assert result["literal_duplicate_stop"] is True
    assert result["surface_gate_evaluated"] is False
    assert audit["candidate"]["preplacement_surface_comparison"] is None


def test_generated_pages_expose_fresh_audit_without_authorizing_upload():
    root = (ROOT / "docs/index.html").read_text()
    atsc = (ROOT / "docs/atsc-submod/index.html").read_text()
    assert "Fresh focus-site evidence. No approval changed." in root
    assert "249 downloaded full-grid raster bytes" in root
    assert "GEMSDOE30 off-lattice irregularity" in root
    assert "No eligible TIFF yet" in root
    assert "Fresh bounded final-dot audit (28 Oct): STOP." in atsc
    assert "249" in atsc and "100.00%" in atsc
    assert "slot_authorized=false" in atsc
    assert "current-peer-audit-20261028.json" in atsc
    assert 'download="KANLER_GEMS' not in root
