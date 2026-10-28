#!/usr/bin/env python3
"""Snapshot shared-template prerequisite status from immutable GitHub evidence.

This is a participant-source audit, not an organizer audit, model run, score,
registry clearance, or submission authorization. It never writes a raster.
"""
from __future__ import annotations

import argparse
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
# A refresh must never overwrite a previous session's frozen receipt.
DEFAULT_OUTPUT = ROOT / "data" / "upstream-prerequisites-latest.json"
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
        declared = cache.get("declared_sha256")
        valid_digest = isinstance(declared, str) and bool(HEX64.fullmatch(declared))
        if type(cache.get("receipt_declares_sha256")) is not bool or cache["receipt_declares_sha256"] != valid_digest:
            errors.append("cache_digest_claim")
        if type(cache.get("cache_bytes_in_repository_tree")) is not bool:
            errors.append("cache_bytes_claim")
        # A tree entry and a declared digest are not a verification of cache
        # bytes, feature lineage or licensing. This auditor never downloads or
        # authenticates the cache, so it must not call it usable.
        if cache.get("usable_for_protocol_reuse") is not False:
            errors.append("cache_reuse_claim")
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
    )
    files = []
    for path in source_paths:
        metadata, _ = content_at(path, head)
        lock = pinned[path]
        files.append({
            "path": path,
            "pinned_commit": provenance["commit"],
            "pinned_git_blob_sha1": lock["git_blob_sha1"],
            "current_head": head,
            "current_git_blob_sha1": metadata["sha"],
            "byte_identical_to_pinned": metadata["sha"] == lock["git_blob_sha1"],
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
    blockers = [
        "No explicit single-method paragraph is present in the received request.",
        "The pinned shared evaluator has a locally reproduced empty-truth false-positive defect; see issue 41 and independently test any newer source.",
        "The pinned shared evaluator/writer silently binarize soft positive values; changed upstream files require a fresh audit and repin, not an assumed fix.",
        "The pinned shared surface gate has an open preview-dot overlap issue.",
        "The pinned shared Hessian ridge implementation has an open eigenvalue-selection issue.",
        "Canonical feature-cache bytes, digest and lineage have not been independently verified by this source-only audit.",
        "A complete, representation-resolved registry and same-fold incumbent are not established.",
    ]
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
        "canonical_feature_cache": {
            "receipt_path": "registry/feature_receipt.json",
            "receipt_git_blob_sha1": feature_meta["sha"],
            "declared_path": cache_path,
            "declared_channels": feature.get("n_channels"),
            "declared_shape": feature.get("shape"),
            "receipt_declares_sha256": digest_valid,
            "declared_sha256": declared_digest if digest_valid else None,
            "cache_bytes_in_repository_tree": cache_present,
            "cache_bytes_downloaded_and_verified": False,
            "usable_for_protocol_reuse": False,
            "upstream_request": f"https://github.com/{REPOSITORY}/issues/53",
        },
        "local_synthetic_operator_audit": {
            "receipt": "evidence/shared_tool_audit.json",
            "source_scope": "Pinned source only; not an audit of the observed upstream head.",
            "ok": local_operator.get("ok"),
            "reproduced_blocking_findings": local_reproduced,
            "geological_model_evaluated": False,
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
        # Do not leave an old successful-looking refresh in place on failure.
        failure = {"kind": "PARTICIPANT-SOURCE PREREQUISITE REFRESH FAILED",
                   "ok": False, "candidate_generated": False, "research_ready": False,
                   "ok_to_submit": False, "slot_authorized": False, "verdict": "negative",
                   "error": str(exc)}
        text = json.dumps(failure, indent=2, allow_nan=False) + "\n"
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        except OSError:
            pass
        print(text, end="")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
