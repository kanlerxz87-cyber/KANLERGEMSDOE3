#!/usr/bin/env python3
"""Autonomous, fail-closed readiness audit. No model or submission is generated."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import sha256_file
from scripts.shared_tools import TEMPLATE, verify_template


def assess(config: dict, root: Path = ROOT, now: datetime | None = None) -> dict:
    failures = []
    resolved = []
    if not isinstance(config, dict):
        return {"research_ready": False, "submit_ready": False, "failures": ["Malformed session configuration"]}
    lane = config.get("assigned_method_paragraph")
    if not isinstance(lane, str) or not lane.strip():
        failures.append("Missing assigned single-method lane paragraph")
    lock = verify_template(root / "vendor" / "shared-template")
    if lock["ok"]:
        resolved.append("Shared evaluator/writer and dependencies restored unmodified and hash-locked")
    else:
        failures.append("Shared template source-lock verification failed")
    receipt_path = root / "data" / "input_receipt.json"
    input_rows = []
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        entries = {row["id"]: row for row in json.loads((root / "vendor" / "shared-template" / "registry" / "data_manifest.json").read_text())["files"]}
        for row in receipt.get("files", []):
            canonical = entries.get(row["id"], {})
            path = (root / row["path"]).resolve()
            ok = bool(path.is_relative_to(root.resolve()) and path.is_file() and row["sha256"] == canonical.get("sha256") and sha256_file(path) == row["sha256"])
            input_rows.append({"id": row["id"], "sha256": row["sha256"], "verified": ok})
        required = {"training_features", "labels", "sample_submission", "ext_derived_sgmc_faults_100m_u8"}
        if required <= {row["id"] for row in input_rows if row["verified"]}:
            resolved.append("Hash-pinned participant-mirror core data restored; data-placement blocker removed")
        else:
            failures.append("Core data absent, corrupt or incomplete")
    else:
        failures.append("Core data restoration receipt absent")
    audit_path = root / "evidence" / "shared_tool_audit.json"
    tool_audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
    if tool_audit.get("ok") is not True or tool_audit.get("source_lock", {}).get("commit") != lock["commit"]:
        failures.append("Shared evaluator operator audit fails or is missing; central repair required")
    cache = config.get("shared_cache") if isinstance(config.get("shared_cache"), dict) else {}
    cache_path = (root / cache["path"]).resolve() if isinstance(cache.get("path"), str) and cache["path"] else None
    if not cache_path or not cache_path.is_relative_to(root.resolve()) or not cache_path.is_file() or not isinstance(cache.get("sha256"), str) or sha256_file(cache_path) != cache["sha256"]:
        failures.append("Authenticated shared feature cache/digest not restored; no private rebuild permitted")
    registry = config.get("registry") if isinstance(config.get("registry"), dict) else {}
    if registry.get("complete") is not True:
        failures.append("Complete raster/surface registry not available")
    incumbent = config.get("same_evaluator_incumbent")
    if not isinstance(incumbent, dict) or not all(incumbent.get(key) is not None for key in ("evaluator_version", "fold_sha256", "value", "ci95", "withheld_positives")):
        failures.append("Same-evaluator, same-fold incumbent evidence absent")
    experiments = config.get("geological_experiments")
    ledger_ok = isinstance(experiments, list)
    if not ledger_ok:
        experiments = []
    try:
        started = datetime.fromisoformat(config["session_started_utc"])
        elapsed = ((now or datetime.now(timezone.utc)) - started).total_seconds()
        budget_ok = (ledger_ok and type(config["max_seconds"]) is int and type(config["max_experiments"]) is int and started.utcoffset() is not None and 0 <= elapsed < config["max_seconds"] <= 7200 and len(experiments) < config["max_experiments"] <= 3)
    except (KeyError, TypeError, ValueError):
        budget_ok = False
    if not budget_ok:
        failures.append("Experiment/time budget exhausted or malformed")
    # Authentication and slot accounting are separate from research readiness.
    submission_failures = list(failures)
    if config.get("organizer_template_authenticated") is not True:
        submission_failures.append("Official organizer-template provenance not authenticated")
    submission_failures.extend(["No candidate has beaten the paired HOLDOUT-DTI incumbent", "No unique candidate saved bytes/validator receipt exist", "Separate selector has not authorized a weekly slot"])
    return {"schema_version": 1, "research_ready": not failures, "submit_ready": False, "slot_authorized": False, "experiments_used": len(experiments), "submission_slots_used": 0, "resolved": resolved, "failures": failures, "submission_failures": submission_failures, "template": lock, "input_integrity": input_rows, "input_organizer_authenticated": False, "holdout_dti": None, "leaderboard_estimate": None, "scope": "Automated prerequisites only; not a score, no human raster inspection required."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "research-session.json")
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "data" / "readiness.json")
    args = parser.parse_args()
    result = assess(json.loads(args.config.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["research_ready"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"research_ready": False, "submit_ready": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
