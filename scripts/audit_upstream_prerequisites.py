#!/usr/bin/env python3
"""Snapshot shared-template prerequisite status from immutable GitHub evidence.

This is a participant-source audit, not an organizer audit, model run, score,
registry clearance, or submission authorization. It never writes a raster.
"""
from __future__ import annotations

import argparse
import ast
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "buffedlizard55-lab/GEMSDOE32"
ISSUES = (37, 39, 41, 42, 49, 51, 53)
PROVENANCE = ROOT / "vendor" / "shared-template" / "PROVENANCE.json"
DEFAULT_OUTPUT = ROOT / "evidence" / "session-20261028-upstream-prerequisites.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def gh_json(endpoint: str) -> Any:
    """Read one GitHub API endpoint through the authenticated gh transport."""
    result = subprocess.run(
        ["gh", "api", endpoint], check=True, capture_output=True, text=True, timeout=120
    )
    return json.loads(result.stdout)


def content_at(path: str, ref: str) -> tuple[dict, bytes]:
    payload = gh_json(f"repos/{REPOSITORY}/contents/{path}?ref={ref}")
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise ValueError(f"Expected a regular GitHub file: {path}")
    try:
        # The contents API wraps base64 at 60 characters; whitespace is valid.
        raw = base64.b64decode(payload["content"], validate=False)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Cannot decode GitHub file: {path}") from exc
    if len(raw) != payload.get("size"):
        raise ValueError(f"GitHub size mismatch: {path}")
    git_blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if git_blob != payload.get("sha"):
        raise ValueError(f"GitHub blob identity mismatch: {path}")
    return payload, raw


def _call_targets_pooled_fp(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    is_add_at = (isinstance(func, ast.Attribute) and func.attr == "at"
                 and isinstance(func.value, ast.Attribute) and func.value.attr == "add"
                 and isinstance(func.value.value, ast.Name) and func.value.value.id == "np")
    return bool(is_add_at and node.args and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "fp_blk")


def zero_truth_branch_skips_pooled_fp(source: str) -> bool:
    """Static source check for a zero-truth early continue before pooled FP addition."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) or function.name != "evaluate_hide_and_recover":
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
                continue
            test = node.test
            zero_truth = (isinstance(test.left, ast.Name) and test.left.id == "n_t"
                          and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)
                          and len(test.comparators) == 1 and isinstance(test.comparators[0], ast.Constant)
                          and test.comparators[0].value == 0)
            if not zero_truth:
                continue
            has_early_continue = any(isinstance(child, ast.Continue) for child in ast.walk(node))
            adds_pooled_fp = any(_call_targets_pooled_fp(child) for child in ast.walk(node))
            if has_early_continue and not adds_pooled_fp:
                return True
    return False


def validate_receipt(receipt: object) -> list[str]:
    """Return fail-closed structural errors for a saved prerequisite receipt."""
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ["receipt_not_object"]
    if receipt.get("schema_version") != 1:
        errors.append("schema_version")
    source = receipt.get("participant_source")
    if not isinstance(source, dict) or source.get("repository") != REPOSITORY:
        errors.append("participant_source")
    elif not isinstance(source.get("head_commit"), str) or not HEX40.fullmatch(source["head_commit"]):
        errors.append("head_commit")
    issues = receipt.get("upstream_issues")
    if not isinstance(issues, list) or {row.get("number") for row in issues if isinstance(row, dict)} != set(ISSUES):
        errors.append("upstream_issues")
    elif any(row.get("state") not in {"OPEN", "CLOSED"} for row in issues):
        errors.append("issue_state")
    files = receipt.get("shared_files")
    if not isinstance(files, list) or len(files) < 5:
        errors.append("shared_files")
    elif any(not HEX40.fullmatch(str(row.get("current_git_blob_sha1", ""))) for row in files):
        errors.append("shared_file_blob")
    cache = receipt.get("canonical_feature_cache")
    if not isinstance(cache, dict):
        errors.append("canonical_feature_cache")
    else:
        if cache.get("receipt_declares_sha256") is not False:
            errors.append("cache_digest_claim")
        if cache.get("cache_bytes_in_repository_tree") is not False:
            errors.append("cache_bytes_claim")
        if cache.get("usable_for_protocol_reuse") is not False:
            errors.append("cache_reuse_claim")
    source_review = receipt.get("source_contract_review")
    if source_review is not None:
        if not isinstance(source_review, dict):
            errors.append("source_contract_review")
        else:
            soft = source_review.get("binary_soft_input_guard")
            empty = source_review.get("zero_truth_cell_pooled_fp")
            if not isinstance(soft, dict) or soft.get("status") not in {"SOURCE_GUARD_PRESENT_NOT_DYNAMICALLY_TESTED", "NOT_CONFIRMED"}:
                errors.append("binary_soft_input_review")
            if not isinstance(empty, dict) or empty.get("status") not in {"SOURCE_LEVEL_OMISSION_PRESENT", "NOT_REPRODUCED_BY_STATIC_CHECK"}:
                errors.append("empty_truth_source_review")
            if isinstance(soft, dict) and soft.get("status") == "SOURCE_GUARD_PRESENT_NOT_DYNAMICALLY_TESTED" and soft.get("dynamic_test_at_current_head") is not False:
                errors.append("binary_guard_test_scope")
            if isinstance(empty, dict) and empty.get("status") == "SOURCE_LEVEL_OMISSION_PRESENT" and empty.get("dynamic_test_at_current_head") is not False:
                errors.append("empty_truth_test_scope")
    if receipt.get("research_ready") is not False:
        errors.append("research_ready")
    if receipt.get("candidate_generated") is not False or receipt.get("raster_sha256") is not None:
        errors.append("candidate_claim")
    if receipt.get("holdout_dti") is not None or receipt.get("leaderboard_estimate") is not None:
        errors.append("score_claim")
    if receipt.get("slot_authorized") is not False or receipt.get("weekly_slots_used") != 0:
        errors.append("slot_claim")
    if receipt.get("verdict") != "negative" or receipt.get("ok_to_submit") is not False:
        errors.append("verdict")
    return errors


def audit() -> dict:
    provenance = json.loads(PROVENANCE.read_text())
    pinned = {row["path"]: row for row in provenance["files"]}
    repo = gh_json(f"repos/{REPOSITORY}")
    branch = repo["default_branch"]
    head = gh_json(f"repos/{REPOSITORY}/commits/{branch}")["sha"]
    if not HEX40.fullmatch(head):
        raise ValueError("Invalid source head returned by GitHub")

    issue_rows = []
    for number in ISSUES:
        item = gh_json(f"repos/{REPOSITORY}/issues/{number}")
        if "pull_request" in item:
            raise ValueError(f"Expected issue, received pull request #{number}")
        issue_rows.append({
            "number": number,
            "title": item["title"],
            "state": str(item["state"]).upper(),
            "updated_at": item["updated_at"],
            "url": item["html_url"],
            "evidence_scope": "GitHub issue status and report text; not proof of organizer impact",
        })

    source_paths = (
        "src/gems32/holdout.py",
        "src/gems32/features.py",
        "src/gems32/submission.py",
        "scripts/evaluate_holdout.py",
        "scripts/submission_writer.py",
        "scripts/arena8a_run_experiments.py",
    )
    files = []
    source_bytes: dict[str, bytes] = {}
    for path in source_paths:
        metadata, raw = content_at(path, head)
        source_bytes[path] = raw
        lock = pinned.get(path, {})
        files.append({
            "path": path,
            "pinned_commit": provenance["commit"] if path in pinned else None,
            "pinned_git_blob_sha1": lock.get("git_blob_sha1"),
            "current_head": head,
            "current_git_blob_sha1": metadata["sha"],
            "byte_identical_to_pinned": metadata["sha"] == lock.get("git_blob_sha1") if path in pinned else None,
            "url": f"https://github.com/{REPOSITORY}/blob/{head}/{path}",
        })

    feature_meta, feature_raw = content_at("registry/feature_receipt.json", head)
    feature = json.loads(feature_raw)
    tree = gh_json(f"repos/{REPOSITORY}/git/trees/{head}?recursive=1")
    if tree.get("truncated") is not False:
        raise ValueError("GitHub returned a missing or truncated source tree")
    tree_paths = {row.get("path") for row in tree.get("tree", []) if isinstance(row, dict)}
    cache_path = feature.get("path")
    declared_digest = feature.get("sha256")
    digest_valid = isinstance(declared_digest, str) and bool(HEX64.fullmatch(declared_digest))
    cache_present = isinstance(cache_path, str) and cache_path in tree_paths

    local_operator = json.loads((ROOT / "evidence" / "shared_tool_audit.json").read_text())
    local_reproduced = [finding["id"] for finding in local_operator.get("blocking_findings", [])]
    holdout_source = source_bytes["src/gems32/holdout.py"].decode("utf-8")
    submission_source = source_bytes["src/gems32/submission.py"].decode("utf-8")
    evaluator_wrapper = source_bytes["scripts/evaluate_holdout.py"].decode("utf-8")
    writer_wrapper = source_bytes["scripts/submission_writer.py"].decode("utf-8")
    uniqueness_runner = source_bytes["scripts/arena8a_run_experiments.py"].decode("utf-8")
    binary_guard_present = (
        "def require_binary_mask" in submission_source
        and "no implicit thresholding" in submission_source
        and "require_binary_mask" in evaluator_wrapper
        and "require_binary_mask" in writer_wrapper
    )
    outside_footprint_guard_present = (
        "outside_footprint_compliant" in submission_source
        and "out_foot_ok" in submission_source
        and "np.all(out_foot == 0.0)" in submission_source
        and "np.all(np.isnan(out_foot))" in submission_source
    )
    empty_truth_fp_omission = zero_truth_branch_skips_pooled_fp(holdout_source)
    lattice_exempt_overlap_gate = (
        'is_synthetic_lattice = "SYNTHETIC_LATTICE" in name' in uniqueness_runner
        and "if not is_synthetic_lattice and frac_fwd > worst_within3_model" in uniqueness_runner
        and '"lane_unique_pass": bool(surface_ok and dots_rho_ok and overlap_model_ok)' in uniqueness_runner
    )
    issue_by_number = {row["number"]: row for row in issue_rows}
    blockers = [
        "No explicit single-method paragraph is present in the received request; the lane paragraph is a placeholder, so no method was assigned.",
        "Current holdout.py still early-continues on zero-truth cells before adding their prediction FP mass to pooled fp_blk totals (source inspection, not a dynamic retest at this head).",
        "The 35-channel cache receipt has no SHA-256 and the declared cache bytes are absent from the current source tree; do not privately rebuild it.",
        "The current registry is not representation-resolved or complete for all source trees at the refreshed heads, and no same-fold incumbent is bound to this evaluator.",
        "One current experiment runner excludes a synthetic lattice from its 3-px overlap threshold; this conflicts with the user's strict all-registry stop and is not an authorized exception.",
        "The fixed e2903b2e two-hour experiment clock is elapsed; it was not reset and no geological experiment ran.",
    ]
    if not binary_guard_present:
        blockers.append("Current wrappers do not all call the binary-only prediction guard; the soft-input contract needs source-level review.")
    if not outside_footprint_guard_present:
        blockers.append("Current shared submission validator's outside-footprint rule is not confirmed in the inspected source.")
    result = {
        "schema_version": 1,
        "kind": "PARTICIPANT-SOURCE PREREQUISITE AUDIT — NOT HOLDOUT-DTI",
        "observed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "participant_source": {
            "repository": REPOSITORY,
            "default_branch": branch,
            "head_commit": head,
            "url": f"https://github.com/{REPOSITORY}/tree/{head}",
            "organizer_source": False,
        },
        "upstream_issues": issue_rows,
        "shared_files": files,
        "current_shared_files_byte_identical_to_pinned": all(row["byte_identical_to_pinned"] for row in files),
        "source_contract_review": {
            "scope": "Static inspection of participant source at this exact head; not a dynamic operator test, organizer audit, or promotion receipt.",
            "binary_soft_input_guard": {
                "status": "SOURCE_GUARD_PRESENT_NOT_DYNAMICALLY_TESTED" if binary_guard_present else "NOT_CONFIRMED",
                "helper": "require_binary_mask",
                "paths": ["src/gems32/submission.py", "scripts/evaluate_holdout.py", "scripts/submission_writer.py"],
                "dynamic_test_at_current_head": False,
                "reported_issues_still_open": [n for n in (37, 51) if issue_by_number.get(n, {}).get("state") == "OPEN"],
                "interpretation": "The inspected head rejects non-finite and non-exact {0,1} in-footprint inputs; open issue titles describe older behavior and are not treated as source proof of a current soft-input defect.",
            },
            "outside_footprint_validator": {
                "status": "SOURCE_GUARD_PRESENT_NOT_DYNAMICALLY_TESTED" if outside_footprint_guard_present else "NOT_CONFIRMED",
                "path": "src/gems32/submission.py",
                "interpretation": "The inspected validator checks zero-outside or NaN-outside mode; this is source review, not organizer acceptance.",
            },
            "zero_truth_cell_pooled_fp": {
                "status": "SOURCE_LEVEL_OMISSION_PRESENT" if empty_truth_fp_omission else "NOT_REPRODUCED_BY_STATIC_CHECK",
                "path": "src/gems32/holdout.py",
                "issue": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41",
                "dynamic_test_at_current_head": False,
                "interpretation": "The n_t == 0 branch records per-fold emitted FP and continues before pooled fp_blk accumulation.",
            },
            "strict_all_registry_dot_gate": {
                "status": "LATTICE_EXCLUDED_FROM_ONE_RUNNER_OVERLAP_THRESHOLD" if lattice_exempt_overlap_gate else "NOT_CONFIRMED",
                "path": "scripts/arena8a_run_experiments.py",
                "issue": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42",
                "interpretation": "One runner's lane_unique_pass uses a worst-overlap statistic that excludes synthetic lattice entries; this conflicts with the user's all-registry rule. Other current source reports are participant claims and were not re-audited here.",
            },
            "hessian_feature": {
                "status": "PINNED_FEATURE_IMPLEMENTATION_UNCHANGED" if any(row["path"] == "src/gems32/features.py" and row["byte_identical_to_pinned"] is True for row in files) else "CHANGED_OR_UNKNOWN",
                "issue": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/49",
                "issue_state": issue_by_number.get(49, {}).get("state"),
                "interpretation": "This is relevant only to methods that consume the affected Hessian ridge feature; no candidate feature was evaluated.",
            },
        },
        "canonical_feature_cache": {
            "receipt_path": "registry/feature_receipt.json",
            "receipt_git_blob_sha1": feature_meta["sha"],
            "declared_path": cache_path,
            "declared_channels": feature.get("n_channels"),
            "declared_shape": feature.get("shape"),
            "receipt_declares_sha256": digest_valid,
            "declared_sha256": declared_digest if digest_valid else None,
            "cache_bytes_in_repository_tree": cache_present,
            "usable_for_protocol_reuse": bool(digest_valid and cache_present),
            "upstream_request": f"https://github.com/{REPOSITORY}/issues/53",
        },
        "local_synthetic_operator_audit": {
            "receipt": "evidence/shared_tool_audit.json",
            "tested_source_commit": local_operator.get("source_lock", {}).get("commit"),
            "current_head_dynamic_tested": False,
            "ok": local_operator.get("ok"),
            "reproduced_blocking_findings": local_reproduced,
            "geological_model_evaluated": False,
            "interpretation": "The synthetic receipt is scoped to the pinned vendor version; it is not a dynamic test of the newer observed HEAD. Current source conclusions are separately labeled static in source_contract_review.",
        },
        "blockers": blockers,
        "research_ready": False,
        "candidate_generated": False,
        "holdout_dti": None,
        "leaderboard_estimate": None,
        "raster_sha256": None,
        "slot_authorized": False,
        "weekly_slots_used": 0,
        "ok_to_submit": False,
        "verdict": "negative",
        "note": "GitHub participant-source status only; no official score, model result, candidate, or upload permission.",
    }
    errors = validate_receipt(result)
    if errors:
        raise ValueError("Generated prerequisite receipt failed self-validation: " + ", ".join(errors))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = audit()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "candidate_generated": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
