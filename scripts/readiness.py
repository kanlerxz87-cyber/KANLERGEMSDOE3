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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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
    """Reopen saved bytes with the active locked auditor and local mask checks.

    The old wrapper bootstrapped a different historical template. Explicitly
    bind the active source lock, and never interpret either local check as a
    guarantee of portal acceptance or organizer provenance.
    """
    sample = resolve_in_root(root, validator.get("template_path"))
    labels = resolve_in_root(root, validator.get("labels_path"))
    if not sample or not labels or not sha(validator.get("template_sha256")) or not sha(validator.get("labels_sha256")):
        return False
    if digest(sample) != validator["template_sha256"] or digest(labels) != validator["labels_sha256"]:
        return False
    if (validator.get("organizer_template_authenticated") is not True
            or validator.get("authenticated_template_sha256") != validator["template_sha256"]):
        return False
    try:
        from scripts.shared_tools import verify_template
        template_root = root / "vendor" / "shared-template"
        lock = verify_template(template_root)
        if (lock.get("ok") is not True or not sha(lock.get("manifest_sha256"))
                or validator.get("shared_template_manifest_sha256") != lock["manifest_sha256"]):
            return False
        output = subprocess.check_output(
            [sys.executable, str(root / "scripts/reopen_with_template.py"), "--template-root", str(template_root),
             "--sample", str(sample), "--labels", str(labels), "--candidate", str(candidate), "--mode", "zeros"],
            text=True, timeout=180,
        )
        result = json.loads(output)
        # The shared zeros mode checks raw values, not the null mask. The
        # independent local profile additionally requires an embedded exterior
        # mask and finite [0,1] raw values everywhere. Both audits must see
        # the same saved file; neither establishes portal acceptance.
        local = json.loads(subprocess.check_output(
            [sys.executable, str(root / "scripts/validate_submission.py"), str(sample), str(candidate),
             "--profile", "masked-finite"], text=True, timeout=180,
        ))
        expected = digest(candidate)
        return (result.get("all_checks_passed") is True and result.get("mode") == "zeros"
                and result.get("sha256") == expected
                and local.get("ok") is True and local.get("encoding_profile") == "masked-finite"
                and local.get("sha256") == expected and local.get("template_sha256") == validator["template_sha256"]
                and digest(sample) == validator["template_sha256"] and digest(labels) == validator["labels_sha256"])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return False


def validate_shared_operator(root: Path, holdout: dict) -> bool:
    """Re-run the synthetic source-locked operator audit, not a model run."""
    try:
        from scripts.preflight import operator_receipt_matches
        from scripts.shared_tools import verify_template
        lock = verify_template(root / "vendor" / "shared-template")
        if lock.get("ok") is not True or not sha(lock.get("manifest_sha256")):
            return False
        candidate, baseline = as_object(holdout.get("candidate")), as_object(holdout.get("same_evaluator_best"))
        if any(x.get("template_manifest_sha256") != lock["manifest_sha256"] for x in (candidate, baseline)):
            return False
        # Isolated interpreter avoids accidentally importing another gems32
        # package. audit() is read-only; unlike its CLI it does not rewrite a receipt.
        probe = ("import json; from scripts.audit_shared_tools import audit; "
                 "from scripts.shared_tools import load_tool; "
                 "print(json.dumps({'audit': audit(), 'version': "
                 "load_tool('evaluate_holdout').holdout.HIDE_RECOVER_EVALUATOR_VERSION}, allow_nan=False))")
        result = json.loads(subprocess.check_output([sys.executable, "-c", probe], cwd=root, text=True, timeout=180))
        return (operator_receipt_matches(result.get("audit"), lock)
                and candidate.get("evaluator") == baseline.get("evaluator") == result.get("version"))
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return False


def _reports_match(recorded: dict, replay: dict) -> bool:
    """Match a stage receipt to the newly computed exact-byte comparisons."""
    if not isinstance(recorded, dict) or not isinstance(replay, dict):
        return False
    fields = ("kind", "stage", "status", "registry_manifest_sha256", "surface_sha256",
              "dots_sha256", "template_sha256", "registry_entries_declared",
              "registry_entries_compared", "registry_complete", "unique_under_protocol", "slot_authorized")
    if any(type(recorded.get(k)) is not type(replay.get(k)) or recorded.get(k) != replay.get(k) for k in fields):
        return False
    if replay.get("status") != "PASS_SCOPED_REGISTRY" or replay.get("unique_under_protocol") is not True:
        return False
    before, after = recorded.get("comparisons"), replay.get("comparisons")
    if not isinstance(before, list) or not isinstance(after, list) or len(before) != len(after) or not after:
        return False
    fixed = ("id", "sha256", "dots_sha256", "candidate_dots", "reference_dots",
             "duplicate", "comparable", "measurement_class")
    floats = ("rank_correlation", "directed_dot_overlap_3px", "reverse_dot_overlap_3px")
    for old, new in zip(before, after):
        if (not isinstance(old, dict) or any(type(old.get(k)) is not type(new.get(k))
                                             or old.get(k) != new.get(k) for k in fixed)):
            return False
        if any(not number(old.get(k)) or not number(new.get(k))
               or not math.isclose(old[k], new[k], rel_tol=0, abs_tol=1e-12) for k in floats):
            return False
    return True


def replay_uniqueness(root: Path, uniqueness: dict, submission: dict, validator: dict) -> dict:
    """Re-run both all-registry audits, binding every stage to its saved bytes.

    Registry completeness/freshness is still a separately asserted provenance
    claim. A receipt cannot prove when it was produced, and no result here
    chooses a submission slot. Any missing/incompatible data remains negative.
    """
    result = {"ok": False, "surface": None, "final_dots": None}
    try:
        from scripts.check_uniqueness import audit_registry
        manifest = resolve_in_root(root, uniqueness.get("registry_manifest_path"))
        template = resolve_in_root(root, validator.get("template_path"))
        candidate = resolve_in_root(root, submission.get("file"))
        pre, final = as_object(uniqueness.get("surface")), as_object(uniqueness.get("final_dots"))
        surface = resolve_in_root(root, pre.get("surface_file"))
        preview = resolve_in_root(root, pre.get("preview_dots_file"))
        if not all((manifest, template, candidate, surface, preview)):
            raise ValueError("Missing registry, template, candidate, surface or preview dots")
        if (digest(manifest) != uniqueness.get("registry_snapshot_sha256")
                or digest(template) != validator.get("template_sha256")
                or digest(candidate) != submission.get("sha256")):
            raise ValueError("Registry, template or candidate hash mismatch")
        for key, stage, layer, dots, item in (
            ("surface", "surface-before-writer", surface, preview, pre),
            ("final_dots", "final-dots", candidate, candidate, final),
        ):
            receipt_path = resolve_in_root(root, item.get("receipt_path"))
            if not receipt_path or not sha(item.get("receipt_sha256")) or digest(receipt_path) != item["receipt_sha256"]:
                raise ValueError("Missing or changed " + key + " uniqueness receipt")
            recorded = json.loads(receipt_path.read_text())
            measured = audit_registry(layer, dots, template, manifest, stage)
            result[key] = measured
            if not _reports_match(recorded, measured):
                raise ValueError(key + " uniqueness receipt differs from the fresh replay or is not a pass")
            if measured["registry_entries_compared"] != uniqueness.get("raster_count"):
                raise ValueError("Registry count differs from the run card")
            worst_rho = max(row["rank_correlation"] for row in measured["comparisons"])
            worst_overlap = max(row["directed_dot_overlap_3px"] for row in measured["comparisons"])
            if (not math.isclose(worst_rho, item["max_rank_correlation"], abs_tol=1e-12, rel_tol=0)
                    or not math.isclose(worst_overlap, item["max_within_3px"], abs_tol=1e-12, rel_tol=0)):
                raise ValueError(key + " summary does not match all replayed comparisons")
        result["ok"] = True
    except Exception as exc:
        result["error"] = str(exc)
    return result


def evaluate(card: dict, root: Path = ROOT, shared_validator=validate_with_shared,
             shared_operator=validate_shared_operator, uniqueness_validator=replay_uniqueness) -> dict:
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
    checks["budget"] = (isinstance(experiments, int) and not isinstance(experiments, bool) and 1 <= experiments <= 3
                        and number(hours) and 0 <= hours <= 2)

    hold = as_object(card.get("holdout"))
    candidate, incumbent = hold.get("candidate"), hold.get("same_evaluator_best")
    canary = as_object(card.get("leakage_canaries"))
    expected, results = canary.get("expected_features"), canary.get("results")
    a_canary = as_object(candidate)
    checks["all_feature_canaries"] = bool(
        canary.get("complete") is True and canary.get("two_polarities_checked") is True
        and isinstance(expected, list) and expected
        and all(isinstance(x, str) and x.strip() for x in expected) and len(set(expected)) == len(expected)
        and isinstance(results, dict) and set(results) == set(expected)
        and all(number(v) and .5 <= v <= .90 for v in results.values())
        and sha(canary.get("folds_sha256")) and canary["folds_sha256"] == a_canary.get("folds_sha256")
        and type(canary.get("withheld_positives")) is int and canary["withheld_positives"] > 0
        and canary["withheld_positives"] == a_canary.get("withheld_positives")
    )
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
            and type(a.get("withheld_positives")) is int and type(b.get("withheld_positives")) is int
            and a["withheld_positives"] > 0 and a["withheld_positives"] == b["withheld_positives"]
            and sha(a.get("folds_sha256")) and a.get("folds_sha256") == b.get("folds_sha256")
            and all(number(v) and 0 <= v <= 1 for v in (a.get("dti"), b.get("dti")))
            and interval(a.get("ci95")) and interval(b.get("ci95"))
            and 0 <= a["ci95"][0] <= a["dti"] <= a["ci95"][1] <= 1
            and 0 <= b["ci95"][0] <= b["dti"] <= b["ci95"][1] <= 1
            and a["dti"] > b["dti"] and interval(paired) and paired[0] > 0
            and paired[0] <= a["dti"] - b["dti"] <= paired[1]
        )
    checks["comparable_holdout_and_paired_win"] = comparable
    try:
        checks["shared_operator_correct_and_pinned"] = shared_operator(root, hold) is True
    except Exception:
        checks["shared_operator_correct_and_pinned"] = False

    u = as_object(card.get("uniqueness"))
    pre, final = as_object(u.get("surface")), as_object(u.get("final_dots"))
    snap = u.get("registry_snapshot_sha256")
    novelty_summary_ok = bool(
        u.get("complete") is True and u.get("current_snapshot_verified") is True and sha(snap)
        and isinstance(u.get("raster_count"), int) and not isinstance(u.get("raster_count"), bool)
        and u["raster_count"] > 0 and type(u.get("missing_or_incompatible")) is int
        and u.get("missing_or_incompatible") == 0
        and pre.get("snapshot_sha256") == snap and final.get("snapshot_sha256") == snap
        and pre.get("complete") is True and final.get("complete") is True
        and number(pre.get("max_rank_correlation")) and -1 <= pre["max_rank_correlation"] <= .90
        and number(final.get("max_rank_correlation")) and -1 <= final["max_rank_correlation"] <= .90
        and number(pre.get("max_within_3px")) and 0 <= pre["max_within_3px"] <= .70
        and number(final.get("max_within_3px")) and 0 <= final["max_within_3px"] <= .70
    )

    sub, val = as_object(card.get("submission")), as_object(card.get("validator"))
    file_hash = sub.get("sha256")
    file_path = sub.get("file")
    valid_file = False
    p = resolve_in_root(root, file_path)
    if p and sha(file_hash) and digest(p) == file_hash:
        try:
            valid_file = shared_validator(root, p, val) is True
        except Exception:
            valid_file = False
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
        isinstance(name, str) and name.strip() and isinstance(note, str) and note.strip() and len(note) <= 140
    )
    replay = {"ok": False, "reason": "Other prerequisites or two-stage summaries did not pass; uniqueness replay not run."}
    if novelty_summary_ok and all(checks.values()):
        try:
            replay = uniqueness_validator(root, u, sub, val)
        except Exception as exc:
            replay = {"ok": False, "error": str(exc)}
    checks["literal_all_registry_uniqueness"] = bool(novelty_summary_ok and isinstance(replay, dict) and replay.get("ok") is True)
    return {
        "eligible_for_separate_selector": all(checks.values()),
        "ok_to_submit": False,
        "reason": "This gate never chooses a weekly slot or submits a file; inventory completeness and receipt chronology are not independently authenticated.",
        "checks": checks,
        "uniqueness_replay": replay,
        "failed_checks": [key for key, passed in checks.items() if not passed],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("card", nargs="?", type=Path, default=ROOT / "evidence/run-card.json")
    args = ap.parse_args()
    print(json.dumps(evaluate(json.loads(args.card.read_text())), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
