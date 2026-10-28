#!/usr/bin/env python3
"""Audit the preserved ATSC research artifacts, not an organizer submission.

Only three immutable participant-mirror inputs are needed. ``--restore`` obtains
those exact hashes through GitHub; it does not rebuild features, evaluate a model,
write a candidate or change a historical card. A duplicate is an intentional
negative result. Saved bytes and local encoding profiles are not portal approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.audit_parallel_candidate import audit as lattice_audit  # noqa: E402
from scripts.github_source import GitHubSource, sha256_file  # noqa: E402
from scripts.validate_submission import PROFILES, validate  # noqa: E402
from src.kanlergems3_atsc.features import STAGE2_CORRIDOR_NAMES  # noqa: E402
from vendor.gems24_template.metric import (  # noqa: E402
    dti_components_exact,
    marginal_inclusion_threshold,
)

CARD_PATH = ROOT / "evidence/atsc-submod-run-card.json"
CANARY_PATH = ROOT / "evidence/atsc_leakage_canary_20261027.json"
MANIFEST_PATH = ROOT / "sources/GEMSDOE32/registry/data_manifest.json"
LATTICE_ID = "calib_13gems_20261001_r13-lattice-s5_v2_nan-ou"
INPUT_HASHES = {
    "sample_submission": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    LATTICE_ID: "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2",
}
ARTIFACT_HASHES = {
    "zeros": "bf21ac69a0e5e6325d9725e7188be210a24b2e68b68060574db56af0d5972566",
    "nan": "c5aa1f764151a4c3f7116bf635c3dc7fa337bc07b18ad905f3307e2a94776f29",
}


def input_paths(data_dir: Path, *, restore: bool = False) -> dict[str, Path]:
    """Resolve only SHA-pinned inputs; never accept a same-named replacement."""
    rows = json.loads(MANIFEST_PATH.read_text())["files"]
    source = GitHubSource() if restore else None
    paths: dict[str, Path] = {}
    for identifier, expected in INPUT_HASHES.items():
        matches = [row for row in rows if row.get("id") == identifier]
        if len(matches) != 1:
            raise ValueError(f"Missing or duplicate pinned input: {identifier}")
        row = matches[0]
        if row.get("sha256") != expected:
            raise ValueError(f"Pinned SHA-256 changed: {identifier}")
        dest = Path(row["dest"])
        if dest.is_absolute() or ".." in dest.parts:
            raise ValueError(f"Unsafe input destination: {identifier}")
        path = data_dir / dest
        if source is not None:
            source.restore(row["repo"], row["ref"], row["path"], path, expected)
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Missing or mismatched input: {identifier}; use --restore")
        paths[identifier] = path
    return paths


def saved_artifacts(card: dict) -> dict[str, Path]:
    """Bind historical card names to immutable repository files and known hashes."""
    art = card["submission_artifacts"]
    if card.get("verdict") != "negative" or card.get("slot_authorized") is not False:
        raise ValueError("Historical ATSC card must remain negative")
    paths: dict[str, Path] = {}
    parent = (ROOT / "docs/atsc-submod/downloads").resolve()
    for kind, key, sha_key in (
        ("zeros", "primary_zeros_tif", "primary_zeros_sha256"),
        ("nan", "official_nan_twin_tif", "official_nan_twin_sha256"),
    ):
        raw = ROOT / art[key]
        path = raw.resolve()
        if raw.is_symlink() or path.parent != parent or path.suffix.lower() != ".tif":
            raise ValueError(f"Unsafe historical artifact path: {kind}")
        if art[sha_key] != ARTIFACT_HASHES[kind] or not path.is_file() or sha256_file(path) != ARTIFACT_HASHES[kind]:
            raise ValueError(f"Historical artifact hash mismatch: {kind}")
        paths[kind] = path
    if card.get("raster_sha256") != ARTIFACT_HASHES["zeros"]:
        raise ValueError("Historical card raster hash mismatch")
    return paths


def canary_coverage(canary: dict) -> dict:
    """Compare the recorded canary names with actual Stage-2 input names."""
    rows = canary.get("all_features")
    if not isinstance(rows, list) or any(not isinstance(r, dict) or not isinstance(r.get("feature"), str) for r in rows):
        raise ValueError("Malformed historical canary inventory")
    names = [row["feature"] for row in rows]
    if len(names) != len(set(names)) or canary.get("tested_features_count") != len(names):
        raise ValueError("Duplicate or inconsistent historical canary inventory")
    expected = list(STAGE2_CORRIDOR_NAMES)
    missing = [name for name in expected if name not in names]
    return {
        "recorded_feature_count": len(names),
        "stage2_corridor_feature_count": len(expected),
        "stage2_corridor_features_in_recorded_inventory": len(expected) - len(missing),
        "stage2_corridor_features_missing_from_inventory": missing,
        "all_stage2_corridor_features_individually_tested_by_record": not missing,
        "full_feature_canary_gate_proven": False,
        "scope": "Name-level comparison only; absence is not proof of actual leakage or of the missing features' AUCs. Presence alone does not establish full-model canary coverage.",
    }


def paired_evidence_scope(card: dict) -> dict:
    """Expose which baseline actually owns the preserved paired interval."""
    holdout = card["holdout"]
    incumbent = card["incumbent_comparison"]
    comparison = incumbent["paired_vs_b0_regional_d28"]
    interval = card["paired_improvement_ci95"]
    if interval != comparison["paired_delta_ci95"]:
        raise ValueError("Historical paired interval no longer matches the B0 comparison")
    cand = float(holdout["value"])
    baseline = float(comparison["baseline_dti"])
    best = float(incumbent["incumbent_holdout_dti"])
    if not math.isclose(float(comparison["candidate_dti"]), cand, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Historical B0 comparison does not match the candidate")
    return {
        "label": "HOLDOUT-DTI (historical report, not rerun)",
        "evaluator_version": holdout["evaluator_version"],
        "withheld_positives": holdout["withheld_positives"],
        "candidate_value": cand,
        "candidate_ci95": holdout["ci95"],
        "named_strongest_incumbent": incumbent["strongest_same_evaluator_incumbent"],
        "incumbent_value": best,
        "point_difference_vs_named_incumbent": cand - best,
        "paired_interval": interval,
        "paired_interval_baseline": "B0_regional_d28",
        "paired_interval_baseline_value": baseline,
        "paired_interval_for_named_incumbent_established": False,
        "scope": "The recorded CI compares ATSC with B0, not the named CADG incumbent; no paired CADG interval is supplied.",
    }


def marginal_counterexample() -> dict:
    """Synthetic numerical check only; not a geological model or holdout score."""
    prediction = np.zeros((12, 12), dtype=float)
    truth = np.zeros_like(prediction)
    prediction[5, 5] = 1.0
    truth[5, 5] = truth[7, 8] = 1.0
    before = dti_components_exact(prediction, truth)
    prediction[5, 6] = 1.0
    after = dti_components_exact(prediction, truth)
    delta_tp = after["TP_w"] - before["TP_w"]
    delta_fp = after["FP_w"] - before["FP_w"]
    threshold = marginal_inclusion_threshold(before["dti"])
    if not (after["dti"] > before["dti"] and delta_tp < threshold):
        raise ValueError("Synthetic marginal-threshold counterexample no longer reproduces")
    return {
        "kind": "SYNTHETIC METRIC FIXTURE — NOT HOLDOUT-DTI OR AN ORGANIZER SCORE",
        "baseline_metric": before["dti"],
        "after_metric": after["dti"],
        "incremental_tp": delta_tp,
        "incremental_fp": delta_fp,
        "claimed_unconditional_threshold": threshold,
        "unconditional_iff_claim_disproved": True,
        "relation": "Delta TP * (1 - (1 - beta) * DTI) > alpha * DTI * Delta FP, for a positive denominator.",
        "upstream_issue": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50",
    }


def audit(data_dir: Path, *, restore: bool = False) -> dict:
    inputs = input_paths(data_dir, restore=restore)
    card = json.loads(CARD_PATH.read_text())
    files = saved_artifacts(card)
    sample, labels, lattice = inputs["sample_submission"], inputs["labels"], inputs[LATTICE_ID]
    measurements = {}
    for kind, candidate in files.items():
        geometry = lattice_audit(candidate, lattice, sample, labels)
        profiles = {}
        for profile in PROFILES:
            result = validate(sample, candidate, profile=profile, expected_dots=37654)
            profiles[profile] = {
                "ok": result["ok"],
                "errors": result["errors"],
                "candidate_sha256": result["candidate_sha256"],
                "nonfinite_inside": result["nonfinite_inside"],
                "raw_nan_pixels": result["raw_range_diagnostics"]["nan_pixels"],
                "inside_range_0_1": result["checks"]["inside_range_0_1"],
                "crs_match": result["checks"]["crs_match"],
                "shape_match": result["checks"]["shape_match"],
                "transform_match": result["checks"]["transform_match"],
            }
        zip_key = "primary_zeros_zip" if kind == "zeros" else "official_nan_twin_zip"
        zip_path = (ROOT / card["submission_artifacts"][zip_key]).resolve()
        if zip_path.parent != candidate.parent or zip_path != candidate.with_suffix(".zip"):
            raise ValueError("Unsafe ZIP path")
        with zipfile.ZipFile(zip_path) as archive:
            info = archive.infolist()
            zip_exact = (len(info) == 1 and info[0].filename == candidate.name
                         and info[0].file_size == candidate.stat().st_size
                         and hashlib.sha256(archive.read(info[0])).hexdigest() == sha256_file(candidate))
        if not zip_exact:
            raise ValueError(f"Historical ZIP differs from TIFF: {kind}")
        measurements[kind] = {"geometry": geometry, "local_profiles": profiles,
                              "zip_sha256": sha256_file(zip_path), "zip_contains_exact_tiff_only": True}

    with rasterio.open(sample) as src:
        fp = (src.dataset_mask() > 0) & np.isfinite(src.read(1))
    with rasterio.open(files["zeros"]) as src:
        zeros = src.read(1, masked=False)
    with rasterio.open(files["nan"]) as src:
        nan = src.read(1, masked=False)
    same_inside = bool(np.array_equal(zeros[fp], nan[fp]))
    if not same_inside or not all(row["geometry"]["duplicate_over_70_percent"] for row in measurements.values()):
        raise ValueError("Historical twins or expected literal duplicate stop changed")

    return {
        "schema_version": 1,
        "kind": "HISTORICAL ATSC SAVED-BYTE AUDIT — NOT A NEW MODEL OR ORGANIZER RECEIPT",
        "source_card_sha256": sha256_file(CARD_PATH),
        "canary_evidence_sha256": sha256_file(CANARY_PATH),
        "input_sha256": INPUT_HASHES,
        "artifacts": {kind: {"file": str(path.relative_to(ROOT)), "sha256": ARTIFACT_HASHES[kind]} for kind, path in files.items()},
        "measurements": measurements,
        "equal_predictions_inside_mirrored_footprint": same_inside,
        "canary_coverage": canary_coverage(json.loads(CANARY_PATH.read_text())),
        "paired_evidence_scope": paired_evidence_scope(card),
        "synthetic_marginal_counterexample": marginal_counterexample(),
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
    """Check a frozen audit against its source files, arithmetic and negative scope.

    This is not a fresh replay of the mirrored lattice or an authenticator of the
    historic model result. The exact inputs are needed to reproduce the audit.
    """
    try:
        card = json.loads(CARD_PATH.read_text())
        files = saved_artifacts(card)
        good = (receipt["source_card_sha256"] == sha256_file(CARD_PATH)
                and receipt["canary_evidence_sha256"] == sha256_file(CANARY_PATH)
                and receipt["input_sha256"] == INPUT_HASHES
                and receipt["canary_coverage"] == canary_coverage(json.loads(CANARY_PATH.read_text()))
                and receipt["paired_evidence_scope"] == paired_evidence_scope(card)
                and receipt["equal_predictions_inside_mirrored_footprint"] is True
                and receipt["full_registry_compared"] is False
                and receipt["surface_registry_comparison"] is None
                and receipt["template_organizer_authenticated"] is False
                and receipt["portal_acceptance_verified"] is False
                and receipt["candidate_generated"] is False
                and receipt["geological_experiments_this_session"] == 0
                and receipt["weekly_slots_used_this_session"] == 0
                and receipt["ok_to_submit"] is False and receipt["slot_authorized"] is False
                and receipt["verdict"] == "negative")
        for kind, path in files.items():
            artifact = receipt["artifacts"][kind]
            row = receipt["measurements"][kind]
            geometry = row["geometry"]
            count, nearby = geometry["candidate_dots"], geometry["candidate_dots_within_3px_of_lattice"]
            expected_profiles = {"template-mask": kind == "nan", "finite-grid": kind == "zeros", "masked-finite": False}
            good = (good and artifact["file"] == str(path.relative_to(ROOT))
                    and artifact["sha256"] == ARTIFACT_HASHES[kind] == geometry["candidate_sha256"]
                    and geometry["lattice_sha256"] == INPUT_HASHES[LATTICE_ID]
                    and geometry["sample_mirror_sha256"] == INPUT_HASHES["sample_submission"]
                    and geometry["label_mirror_sha256"] == INPUT_HASHES["labels"]
                    and type(count) is int and type(nearby) is int and count == 37654 and 0 <= nearby <= count
                    and math.isclose(geometry["candidate_dot_overlap_fraction"], nearby / count, rel_tol=0, abs_tol=1e-12)
                    and nearby / count > .70 and geometry["duplicate_over_70_percent"] is True
                    and geometry["in_footprint_nan"] == 0 and geometry["in_footprint_inf"] == 0
                    and geometry["in_footprint_min"] >= 0 and geometry["in_footprint_max"] <= 1
                    and row["zip_contains_exact_tiff_only"] is True)
            for profile, expected in expected_profiles.items():
                item = row["local_profiles"][profile]
                good = (good and item["ok"] is expected and item["candidate_sha256"] == ARTIFACT_HASHES[kind]
                        and item["nonfinite_inside"] == 0 and item["inside_range_0_1"] is True
                        and item["crs_match"] is True and item["shape_match"] is True and item["transform_match"] is True)
            zip_key = "primary_zeros_zip" if kind == "zeros" else "official_nan_twin_zip"
            zip_path = (ROOT / card["submission_artifacts"][zip_key]).resolve()
            if zip_path != path.with_suffix(".zip"):
                good = False
            else:
                with zipfile.ZipFile(zip_path) as archive:
                    info = archive.infolist()
                    good = (good and row["zip_sha256"] == sha256_file(zip_path) and len(info) == 1
                            and info[0].filename == path.name and info[0].file_size == path.stat().st_size
                            and hashlib.sha256(archive.read(info[0])).hexdigest() == ARTIFACT_HASHES[kind])
        example = receipt["synthetic_marginal_counterexample"]
        recomputed = marginal_counterexample()
        good = (good and example["unconditional_iff_claim_disproved"] is True
                and all(math.isclose(example[k], recomputed[k], rel_tol=0, abs_tol=1e-10)
                        for k in ("baseline_metric", "after_metric", "incremental_tp", "incremental_fp", "claimed_unconditional_threshold")))
    except (KeyError, TypeError, ValueError, OSError, ZeroDivisionError, zipfile.BadZipFile):
        good = False
    if not good:
        raise ValueError("ATSC historical receipt or saved artifact is inconsistent; refuse publication")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".cache/gems_data")
    parser.add_argument("--restore", action="store_true", help="Restore only the three immutable mirror inputs")
    parser.add_argument("--output", type=Path, help="Optional receipt destination; defaults to stdout")
    args = parser.parse_args()
    try:
        result = audit(args.data_dir, restore=args.restore)
        code = 1  # the saved candidate is a confirmed literal duplicate
    except Exception as exc:
        result = {"kind": "ATSC AUDIT FAILED", "error": str(exc), "candidate_generated": False,
                  "verdict": "negative", "ok_to_submit": False, "slot_authorized": False}
        code = 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
