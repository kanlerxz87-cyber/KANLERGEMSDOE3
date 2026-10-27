#!/usr/bin/env python3
"""Fail-closed evidence gate; never selects or submits a competition entry.

A positive result means only that a *separate* weekly-slot selector may consider
this candidate. This program does not run a model or replace the shared raster
validator. The input validator receipt must have been produced by that validator
on the saved bytes; this gate re-hashes the file to bind the receipt to it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def number(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha(value: object) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


def interval(value: object) -> bool:
    return (isinstance(value, list) and len(value) == 2 and
            all(number(x) for x in value) and value[0] <= value[1])


def as_object(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def resolve_in_root(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    p = (root / value).resolve()
    return p if p.is_relative_to(root.resolve()) and p.is_file() else None


def validate_with_shared(root: Path, candidate: Path, validator: dict) -> bool:
    """Reopen candidate using the hash-pinned shared auditor, not a local fork."""
    sample = resolve_in_root(root, validator.get("template_path"))
    labels = resolve_in_root(root, validator.get("labels_path"))
    if not sample or not labels or not sha(validator.get("template_sha256")) or not sha(validator.get("labels_sha256")):
        return False
    if digest(sample) != validator["template_sha256"] or digest(labels) != validator["labels_sha256"]:
        return False
    # A match to an owner mirror is not organizer authentication. This must
    # be established separately before any selector may consider a candidate.
    if (validator.get("organizer_template_authenticated") is not True
            or validator.get("authenticated_template_sha256") != validator["template_sha256"]):
        return False
    try:
        template_root = subprocess.check_output(
            ["bash", str(root / "scripts/bootstrap_template.sh")], text=True, timeout=180
        ).strip()
        output = subprocess.check_output(
            [sys.executable, str(root / "scripts/reopen_with_template.py"), "--template-root", template_root,
             "--sample", str(sample), "--labels", str(labels), "--candidate", str(candidate)],
            text=True, timeout=180,
        )
        result = json.loads(output)
        return result.get("all_checks_passed") is True and result.get("sha256") == digest(candidate)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return False


def evaluate(card: dict, root: Path = ROOT, shared_validator=validate_with_shared) -> dict:
    card = as_object(card)
    checks: dict[str, bool] = {}
    lane = as_object(card.get("lane"))
    checks["explicit_method_lane"] = (lane.get("explicitly_assigned") is True
        and isinstance(lane.get("assigned_method"), str) and bool(lane["assigned_method"].strip()))
    cache = as_object(card.get("feature_cache"))
    cache_path = resolve_in_root(root, cache.get("path"))
    checks["shared_feature_cache_provenance"] = bool(
        cache.get("provenance_verified") is True and sha(cache.get("sha256"))
        and cache_path and digest(cache_path) == cache["sha256"]
    )
    budget = as_object(card.get("budget"))
    experiments, hours = budget.get("experiments"), budget.get("hours")
    checks["budget"] = (isinstance(experiments, int) and not isinstance(experiments, bool) and 0 <= experiments <= 3
                        and number(hours) and 0 <= hours <= 2)

    canary = as_object(card.get("leakage_canaries"))
    expected, results = canary.get("expected_features"), canary.get("results")
    checks["all_feature_canaries"] = bool(
        canary.get("complete") is True and isinstance(expected, list) and expected
        and all(isinstance(x, str) and x for x in expected) and len(set(expected)) == len(expected)
        and isinstance(results, dict) and set(results) == set(expected)
        and all(number(v) and .5 <= v <= .90 for v in results.values())
    )

    hold = as_object(card.get("holdout"))
    candidate, incumbent = hold.get("candidate"), hold.get("same_evaluator_best")
    paired = hold.get("paired_delta_ci95")
    comparable = False
    protocol = as_object(hold.get("protocol"))
    protocol_ok = (protocol.get("whole_segments_with_buffer") is True
                   and protocol.get("catalogue_features_visible_only") is True
                   and protocol.get("visible_mask_pixel_exact") is True
                   and protocol.get("pooled_dti") is True
                   and protocol.get("alpha") == .2 and protocol.get("beta") == .8
                   and protocol.get("kernel_radius_m") == 300)
    if isinstance(candidate, dict) and isinstance(incumbent, dict):
        a, b = candidate, incumbent
        comparable = bool(
            protocol_ok and isinstance(a.get("evaluator"), str) and a.get("evaluator") and a.get("evaluator") == b.get("evaluator")
            and isinstance(a.get("withheld_positives"), int) and not isinstance(a.get("withheld_positives"), bool)
            and a["withheld_positives"] > 0 and a["withheld_positives"] == b.get("withheld_positives")
            and sha(a.get("folds_sha256")) and a.get("folds_sha256") == b.get("folds_sha256")
            and all(number(v) and 0 <= v <= 1 for v in (a.get("dti"), b.get("dti")))
            and interval(a.get("ci95")) and interval(b.get("ci95"))
            and 0 <= a["ci95"][0] <= a["dti"] <= a["ci95"][1] <= 1
            and 0 <= b["ci95"][0] <= b["dti"] <= b["ci95"][1] <= 1
            and a["dti"] > b["dti"] and interval(paired) and 0 < paired[0] <= paired[1] <= 1
        )
    checks["comparable_holdout_and_paired_win"] = comparable

    u = as_object(card.get("uniqueness"))
    pre, final = as_object(u.get("surface")), as_object(u.get("final_dots"))
    snap = u.get("registry_snapshot_sha256")
    checks["literal_all_registry_uniqueness"] = bool(
        u.get("complete") is True and u.get("current_snapshot_verified") is True and sha(snap)
        and isinstance(u.get("raster_count"), int) and not isinstance(u.get("raster_count"), bool)
        and u["raster_count"] > 0 and type(u.get("missing_or_incompatible")) is int
        and u.get("missing_or_incompatible") == 0
        and pre.get("snapshot_sha256") == snap and final.get("snapshot_sha256") == snap
        and pre.get("complete") is True and final.get("complete") is True
        and number(pre.get("max_abs_spearman")) and 0 <= pre["max_abs_spearman"] <= .90
        and number(pre.get("max_within_3px")) and 0 <= pre["max_within_3px"] <= .70
        and number(final.get("max_abs_spearman")) and 0 <= final["max_abs_spearman"] <= .90
        and number(final.get("max_within_3px")) and 0 <= final["max_within_3px"] <= .70
    )

    sub, val = as_object(card.get("submission")), as_object(card.get("validator"))
    file_hash = sub.get("sha256")
    file_path = sub.get("file")
    valid_file = False
    p = resolve_in_root(root, file_path)
    if p and sha(file_hash) and digest(p) == file_hash:
        valid_file = shared_validator(root, p, val)
    required = ("single_band", "float32", "no_nan_or_inf_inside_footprint", "values_in_0_1",
                "crs_shape_transform_match", "outside_matches_official_spec")
    checks["saved_bytes_and_validator"] = bool(
        valid_file and val.get("sha256") == file_hash and sha(val.get("template_sha256"))
        and val.get("receipt_source") == "shared-template-reopened-geotiff"
        and all(val.get(k) is True for k in required)
        and final.get("raster_sha256") == file_hash
    )
    note, name = sub.get("note"), sub.get("name")
    checks["submission_name_and_note"] = bool(
        isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", name)
        and isinstance(note, str) and bool(note.strip()) and len(note) <= 140
        and all(ord(c) >= 32 and ord(c) != 127 for c in note)
    )
    return {
        "eligible_for_separate_selector": all(checks.values()),
        "ok_to_submit": False,
        "reason": "This gate never chooses a weekly slot or submits a file.",
        "checks": checks,
        "failed_checks": [key for key, passed in checks.items() if not passed],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("card", nargs="?", type=Path, default=ROOT / "evidence/run-card.json")
    args = ap.parse_args()
    print(json.dumps(evaluate(json.loads(args.card.read_text())), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
