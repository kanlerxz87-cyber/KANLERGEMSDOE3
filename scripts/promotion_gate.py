#!/usr/bin/env python3
"""Decision-only schema gate; never an evaluator, evidence authenticator or slot selector.

All booleans/numbers must come from trusted source-locked runners and hash-bound
receipts. A hand-entered card or a passing synthetic fixture is not proof of
scientific quality, provenance, a complete registry or permission to upload.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re


REQUIRED_TRUE = (
    "lane_recorded", "shared_template_pinned", "canonical_cache_verified",
    "shared_operator_audit_passed", "whole_segment_buffered_holdout",
    "visible_only_features", "pixel_exact_visible_mask", "out_of_fold_lineage_verified",
    "all_features_canary_tested", "same_evaluator_incumbent", "registry_complete",
    "surface_checked_before_placement", "preview_dots_checked_before_writing",
    "final_dots_checked", "preview_final_support_matches", "saved_bytes_validated",
    "template_provenance_verified", "outside_encoding_contract_verified", "budget_verified",
)
VALIDATOR_CHECKS = (
    "single_band", "dtype_float32", "no_nan_inside_footprint", "no_masked_inside_footprint",
    "inside_range_0_1", "crs_match", "shape_match", "transform_match", "selected_encoding",
)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def interval(value, lower: float, upper: float) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(finite(x) for x in value) and lower <= value[0] <= value[1] <= upper


def assess(card):
    failures = []
    if not isinstance(card, dict):
        return {"verdict": "negative", "schema_status": "incomplete", "failures": ["run card must be an object"], "promotion_evaluated": False, "slot_authorized": False}
    failures.extend(field for field in REQUIRED_TRUE if card.get(field) is not True)
    for field in ("surface_max_rank_correlation", "final_max_rank_correlation"):
        value = card.get(field)
        # The literal protocol tests rho > 0.90, not |rho| > 0.90.
        if not finite(value) or not -1 <= value <= .90:
            failures.append(field)
    for field in ("surface_dot_overlap_3px", "final_dot_overlap_3px"):
        value = card.get(field)
        if not finite(value) or not 0 <= value <= .70:
            failures.append(field)
    auc = card.get("max_feature_auc")
    if not finite(auc) or not 0 <= auc <= .90:
        failures.append("leakage_canary")
    improvement = card.get("paired_improvement_ci95")
    if not interval(improvement, -1, 1) or improvement[0] <= 0:
        failures.append("paired_holdout_improvement")
    metric = card.get("holdout") if isinstance(card.get("holdout"), dict) else {}
    # An interval versus an easy baseline is not evidence of improvement over
    # the named best incumbent. These fields provide only schema-level binding;
    # the underlying fold predictions and receipts still need authentication.
    pair = card.get("paired_comparison") if isinstance(card.get("paired_comparison"), dict) else {}
    incumbent = card.get("incumbent_comparison") if isinstance(card.get("incumbent_comparison"), dict) else {}
    candidate_id, incumbent_id = card.get("candidate_id"), incumbent.get("strongest_same_evaluator_incumbent")
    fold_digest = metric.get("fold_sha256")
    candidate_value, incumbent_value = pair.get("candidate_value"), pair.get("incumbent_value")
    delta = pair.get("delta")
    paired_bound = (
        isinstance(candidate_id, str) and bool(candidate_id.strip())
        and isinstance(incumbent_id, str) and bool(incumbent_id.strip())
        and candidate_id != incumbent_id
        and pair.get("candidate_id") == candidate_id and pair.get("incumbent_id") == incumbent_id
        and isinstance(fold_digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", fold_digest))
        and pair.get("fold_sha256") == fold_digest
        and isinstance(metric.get("evaluator_version"), str) and bool(metric["evaluator_version"].strip())
        and pair.get("evaluator_version") == metric.get("evaluator_version")
        and type(metric.get("withheld_positives")) is int and metric["withheld_positives"] > 0
        and type(pair.get("withheld_positives")) is int
        and pair.get("withheld_positives") == metric["withheld_positives"]
        and finite(candidate_value) and finite(incumbent_value) and finite(delta)
        and finite(metric.get("value")) and finite(incumbent.get("incumbent_holdout_dti"))
        and 0 <= incumbent_value < candidate_value <= 1
        and math.isclose(candidate_value, metric["value"], rel_tol=0, abs_tol=1e-12)
        and math.isclose(incumbent_value, incumbent["incumbent_holdout_dti"], rel_tol=0, abs_tol=1e-12)
        and math.isclose(delta, candidate_value - incumbent_value, rel_tol=0, abs_tol=1e-12)
        and interval(improvement, -1, 1) and pair.get("ci95") == improvement
    )
    if not paired_bound:
        failures.append("paired_incumbent_binding")
    version = metric.get("evaluator_version")
    if metric.get("class") != "HOLDOUT-DTI" or not isinstance(version, str) or not version.strip():
        failures.append("holdout_identity")
    n = metric.get("withheld_positives")
    if type(n) is not int or n <= 0:
        failures.append("withheld_positives")
    score = metric.get("value")
    if not finite(score) or not 0 <= score <= 1:
        failures.append("holdout_value")
    ci = metric.get("ci95")
    if not interval(ci, 0, 1) or (finite(score) and not ci[0] <= score <= ci[1]):
        failures.append("holdout_ci95")
    if (metric.get("alpha"), metric.get("beta"), metric.get("kernel_m")) != (.2, .8, 300) or metric.get("kernel") != "triangular" or metric.get("aggregation") != "pooled":
        failures.append("metric_definition")
    validator = card.get("validator") if isinstance(card.get("validator"), dict) else {}
    failures.extend("validator." + field for field in VALIDATOR_CHECKS if validator.get(field) is not True)
    sha = card.get("raster_sha256")
    if not isinstance(sha, str) or not re.fullmatch("[0-9a-f]{64}", sha):
        failures.append("raster_sha256")
    for field in ("hypothesis", "mechanism", "non_fault_mimic"):
        if not isinstance(card.get(field), str) or not card[field].strip():
            failures.append(field)
    name = card.get("submission_name")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,120}", name):
        failures.append("submission_name")
    note = card.get("submission_note")
    if not isinstance(note, str) or not 0 < len(note.strip()) <= len(note) <= 140 or any(ord(c) < 32 for c in note):
        failures.append("submission_note")
    # Preserve main's safety quarantine: a complete schema is not authenticated
    # scientific evidence. This helper has no promotion implementation.
    return {"verdict": "negative", "schema_status": "incomplete" if failures else "complete", "failures": failures, "promotion_evaluated": False, "slot_authorized": False, "scope": "Schema validation only; does not authenticate evidence, promote, publish or spend a competition slot."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    args = parser.parse_args()
    try:
        card = json.loads(args.card.read_text())
    except (OSError, ValueError) as exc:
        result = {"verdict": "negative", "failures": ["Unable to read run card: " + str(exc)], "slot_authorized": False}
    else:
        result = assess(card)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
