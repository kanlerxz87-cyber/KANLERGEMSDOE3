"""Structural, fail-closed RESEARCH gate; real slot selection is separate.

Callers must independently replay the unchanged shared tools and verify that
receipts are hash-bound to actual artifacts. This schema check cannot itself
authenticate a manifest, holdout, organizer receipt, or weekly allocation.
"""
from __future__ import annotations

import math
import re


def _number(x, lo, hi):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and lo <= x <= hi


def _sha(x):
    return isinstance(x, str) and re.fullmatch(r"[0-9a-f]{64}", x) is not None


def _ci(x, lo, hi):
    return (isinstance(x, (list, tuple)) and len(x) == 2 and
            all(_number(v, lo, hi) for v in x) and x[0] <= x[1])


def _registry(a, phase, artifact_sha):
    if not isinstance(a, dict):
        return False
    n, checked = a.get("registry_rasters_expected"), a.get("registry_rasters_checked")
    valid_counts = type(n) is int and type(checked) is int and n > 0 and checked == n
    missing, duplicates, positives = a.get("missing_or_invalid"), a.get("duplicate_count"), a.get("candidate_positive_pixels")
    return bool(a.get("phase") == phase and a.get("complete_applicable_registry") is True
                and a.get("complete_accessible_scan") is True and valid_counts
                and type(missing) is int and missing == 0 and a.get("source_errors") == []
                and type(duplicates) is int and duplicates == 0
                and type(positives) is int and positives > 0
                and _number(a.get("worst_spearman_full_footprint"), -1, .90)
                and _number(a.get("worst_dot_overlap"), 0, .70)
                and _sha(a.get("registry_manifest_sha256"))
                and a.get("artifact_sha256") == artifact_sha and _sha(artifact_sha))


def decide(card):
    """Check a claimed run-card schema; never approve a competition submission."""
    if not isinstance(card, dict):
        card = {}
    candidate_sha, surface_sha = card.get("raster_sha256"), card.get("surface_sha256")
    fmt = card.get("validator_output") if isinstance(card.get("validator_output"), dict) else {}
    features = card.get("features_used")
    canary = card.get("feature_canary")
    canary_ok = (isinstance(features, list) and len(features) > 0
                 and all(isinstance(s, str) and s.strip() for s in features)
                 and len(set(features)) == len(features) and isinstance(canary, dict)
                 and set(features) == set(canary)
                 and all(_number(canary[s], .5, .90) for s in features))
    ho = card.get("holdout") if isinstance(card.get("holdout"), dict) else {}
    baseline = ho.get("baseline") if isinstance(ho.get("baseline"), dict) else {}
    withheld = ho.get("withheld_positive_pixels")
    holdout_ok = (
        ho.get("evidence_class") == "HOLDOUT-DTI" and isinstance(ho.get("evaluator_version"), str)
        and bool(ho.get("evaluator_version")) and type(withheld) is int and withheld > 0
        and ho.get("whole_segment_buffered") is True and ho.get("catalogue_features_visible_only") is True
        and ho.get("visible_faults_masked_pixel_exact") is True
        and (ho.get("alpha"), ho.get("beta"), ho.get("kernel_m"), ho.get("kernel"), ho.get("aggregation"))
            == (.2, .8, 300, "triangular", "pooled")
        and _sha(ho.get("folds_sha256")) and _number(ho.get("dti"), 0, 1) and _ci(ho.get("ci95"), 0, 1)
        and baseline.get("evidence_class") == "HOLDOUT-DTI"
        and baseline.get("evaluator_version") == ho.get("evaluator_version")
        and baseline.get("withheld_positive_pixels") == withheld
        and baseline.get("folds_sha256") == ho.get("folds_sha256")
        and baseline.get("verified_current_best") is True
        and _number(baseline.get("dti"), 0, 1) and _ci(baseline.get("ci95"), 0, 1)
        and ho.get("dti", 0) > baseline.get("dti", 1)
        and _ci(ho.get("paired_delta_ci95"), -1, 1) and ho["paired_delta_ci95"][0] > 0
    )
    surface, final = card.get("surface_registry"), card.get("final_registry")
    same_inventory = (isinstance(surface, dict) and isinstance(final, dict)
                      and _sha(surface.get("registry_manifest_sha256"))
                      and surface.get("registry_manifest_sha256") == final.get("registry_manifest_sha256"))
    final_count_bound = isinstance(final, dict) and final.get("candidate_positive_pixels") == card.get("candidate_positive_pixels")
    name, note = card.get("submission_name"), card.get("submission_note")
    positives, experiments = card.get("candidate_positive_pixels"), card.get("experiment_count")
    lane = card.get("method_lane")
    gates = {
        "assigned_lane_and_shared_template": (isinstance(lane, str) and bool(lane.strip())
                                               and _sha(card.get("shared_template_manifest_sha256"))
                                               and card.get("template_provenance_verified") is True),
        "pinned_candidate_and_exact_on_disk_format": (_sha(candidate_sha) and fmt.get("sha256") == candidate_sha
                                                       and fmt.get("all_checks_passed") is True
                                                       and type(positives) is int and positives > 0),
        "each_feature_canary_at_most_0_90": bool(canary_ok),
        "surface_full_registry": _registry(surface, "surface", surface_sha),
        "final_full_registry": _registry(final, "final", candidate_sha) and final_count_bound,
        "same_registry_both_phases": bool(same_inventory),
        "matched_holdout_beats_current_best_with_paired_ci": bool(holdout_ok),
        "experiment_and_time_budget": (type(experiments) is int and 1 <= experiments <= 3
                                       and _number(card.get("elapsed_minutes"), 0, 120)),
        "name_and_note_at_most_140_chars": (isinstance(name, str) and 0 < len(name.strip()) <= 140
                                              and isinstance(note, str) and 0 < len(note.strip()) <= 140),
    }
    eligible = all(gates.values())
    return {"gates": gates, "eligible_for_separate_selector": eligible,
            "verdict": "promote" if eligible else "negative",
            "failures": [k for k, passed in gates.items() if not passed],
            "selector_approval": False, "slot_authorized": False, "ok_to_submit": False,
            "caveat": "Structural gate only; claims and receipts must be independently verified. Slot selection is not performed here."}
