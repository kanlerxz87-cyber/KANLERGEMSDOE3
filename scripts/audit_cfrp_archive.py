#!/usr/bin/env python3
"""Audit a concurrent CFRP TIFF against the pinned lattice; never promote it.

This is a saved-byte comparison and local format check, not a new model run,
leaderboard estimate, complete-registry audit or organizer acceptance receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.audit_atsc_archive import INPUT_HASHES, LATTICE_ID, input_paths  # noqa: E402
from scripts.audit_parallel_candidate import audit as lattice_audit  # noqa: E402
from scripts.github_source import sha256_file  # noqa: E402
from scripts.validate_submission import PROFILES, validate  # noqa: E402

CARD = ROOT / "evidence/cfrp_run_card_20261028.json"
TIFF = ROOT / "docs/cfrp-20261028/downloads/kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros.tif"
EXPECTED_SHA = "7fb488c0560820dfb3f26b62316140d2987107726e3e9753bdd789b6c4d684fd"


def audit(data_dir: Path, *, restore: bool = False) -> dict:
    inputs = input_paths(data_dir, restore=restore)
    if not TIFF.is_file() or TIFF.is_symlink() or sha256_file(TIFF) != EXPECTED_SHA:
        raise ValueError("Missing or mismatched CFRP saved TIFF")
    card = json.loads(CARD.read_text())
    if card.get("raster_sha256") != EXPECTED_SHA:
        raise ValueError("Historical CFRP card hash does not match saved TIFF")
    sample, labels, lattice = inputs["sample_submission"], inputs["labels"], inputs[LATTICE_ID]
    geometry = lattice_audit(TIFF, lattice, sample, labels)
    if not geometry["duplicate_over_70_percent"]:
        raise ValueError("The expected literal duplicate stop did not reproduce")
    profiles = {}
    for profile in PROFILES:
        result = validate(sample, TIFF, profile=profile, expected_dots=44090)
        profiles[profile] = {
            "ok": result["ok"], "errors": result["errors"],
            "candidate_sha256": result["candidate_sha256"],
            "nonfinite_inside": result["nonfinite_inside"],
            "inside_range_0_1": result["checks"]["inside_range_0_1"],
            "crs_match": result["checks"]["crs_match"],
            "shape_match": result["checks"]["shape_match"],
            "transform_match": result["checks"]["transform_match"],
        }
    return {
        "schema_version": 1,
        "kind": "CFRP HISTORICAL SAVED-BYTE AUDIT — NOT A NEW MODEL OR ORGANIZER RECEIPT",
        "historical_card_sha256": sha256_file(CARD),
        "candidate_file": str(TIFF.relative_to(ROOT)),
        "candidate_sha256": EXPECTED_SHA,
        "input_sha256": INPUT_HASHES,
        "geometry": geometry,
        "local_profiles": profiles,
        "full_registry_compared": False,
        "surface_registry_comparison": None,
        "template_organizer_authenticated": False,
        "portal_acceptance_verified": False,
        "candidate_generated": False,
        "geological_experiments_this_session": 0,
        "weekly_slots_used_this_session": 0,
        "ok_to_submit": False,
        "slot_authorized": False,
        "verdict": "negative",
    }


def check_receipt(receipt: dict) -> None:
    """Verify identity, arithmetic and scope of a frozen receipt, not the model."""
    try:
        card = json.loads(CARD.read_text())
        geometry = receipt["geometry"]
        count, nearby = geometry["candidate_dots"], geometry["candidate_dots_within_3px_of_lattice"]
        good = (not TIFF.is_symlink() and sha256_file(TIFF) == EXPECTED_SHA
                and card["raster_sha256"] == receipt["candidate_sha256"] == EXPECTED_SHA
                and receipt["historical_card_sha256"] == sha256_file(CARD)
                and receipt["candidate_file"] == str(TIFF.relative_to(ROOT))
                and receipt["input_sha256"] == INPUT_HASHES
                and geometry["candidate_sha256"] == EXPECTED_SHA
                and geometry["lattice_sha256"] == INPUT_HASHES[LATTICE_ID]
                and geometry["sample_mirror_sha256"] == INPUT_HASHES["sample_submission"]
                and geometry["label_mirror_sha256"] == INPUT_HASHES["labels"]
                and type(count) is int and type(nearby) is int and count == 44090 and 0 <= nearby <= count
                and geometry["candidate_dot_overlap_fraction"] == nearby / count > .70
                and geometry["duplicate_over_70_percent"] is True
                and receipt["full_registry_compared"] is False
                and receipt["surface_registry_comparison"] is None
                and receipt["template_organizer_authenticated"] is False
                and receipt["portal_acceptance_verified"] is False
                and receipt["candidate_generated"] is False
                and receipt["geological_experiments_this_session"] == 0
                and receipt["weekly_slots_used_this_session"] == 0
                and receipt["ok_to_submit"] is False and receipt["slot_authorized"] is False
                and receipt["verdict"] == "negative")
        for profile, expected in {"template-mask": False, "finite-grid": True, "masked-finite": False}.items():
            item = receipt["local_profiles"][profile]
            good = (good and item["ok"] is expected and item["candidate_sha256"] == EXPECTED_SHA
                    and item["nonfinite_inside"] == 0 and item["inside_range_0_1"] is True
                    and item["crs_match"] is True and item["shape_match"] is True and item["transform_match"] is True)
    except (KeyError, TypeError, ValueError, OSError, ZeroDivisionError):
        good = False
    if not good:
        raise ValueError("CFRP historical receipt or saved artifact is inconsistent; refuse publication")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".cache/gems_data")
    parser.add_argument("--restore", action="store_true", help="Restore three immutable mirror inputs")
    parser.add_argument("--output", type=Path, help="Optional receipt destination; stdout otherwise")
    args = parser.parse_args()
    try:
        result, code = audit(args.data_dir, restore=args.restore), 1
    except Exception as exc:
        result, code = {"kind": "CFRP AUDIT FAILED", "error": str(exc), "candidate_generated": False,
                        "verdict": "negative", "ok_to_submit": False, "slot_authorized": False}, 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
