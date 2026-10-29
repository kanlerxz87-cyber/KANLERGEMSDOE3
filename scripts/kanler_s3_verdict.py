#!/usr/bin/env python3
"""Combine the receipts into one verdict card for the KS3-strain candidate.

Gates (all must pass to DOWNLOAD; the value gate must also pass to SUBMIT):
  G1 format      - vendored 12-point validator passed on the published bytes
  G2 range       - every value in [0,1], full grid finite (zeros variant), footprint values finite
  G3 grid        - CRS EPSG:32611, shape 3730x3292, transform equal to the sample template
  G4 uniqueness  - no overlap > 70% within 3 px and no rank correlation > 0.90 against any
                   COMPARED GEMSDOE TIFF in the inventory; inventory must be COMPLETE
  G5 leakage     - zero dots on the known catalogue (pixel-exact mask)
  G6 value       - SGMC-CAL proxy >= the H33 B2 reference (pre-registered rule)
  G7 provenance  - inputs are owner mirrors; organizer authentication is NOT established (warn)
Nothing here is an organizer score.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
OUT = EV / "kanler-s3-verdict-20261029.json"


def load(name: str):
    return json.loads((EV / name).read_text())


def main() -> dict:
    mat = load("kanler-s3-materialize-20261029.json")
    uniq = load("kanler-s3-uniqueness-20261029.json")  # v2 receipt (rule_version v2)
    assert str(uniq.get("rule_version", "")).startswith("v2"), "verdict must use the v2 uniqueness receipt"
    e2 = load("kanler-s3-e2-candidates-20261029.json")["results"]
    inv = load("peer-tif-inventory-20261029.json")
    e1 = load("kanler-s3-e1-canary-20261029.json")

    v = mat["validator"]
    checks = mat["checks"]
    g1 = bool(mat["checks"] and all(checks.values()))
    g2 = bool(v["in_footprint_min"] >= 0.0 and v["in_footprint_max"] <= 1.0 and v["full_grid_finite_pixels"] == 3730 * 3292)
    g3 = (v["crs"].endswith("32611") and v["shape"] == [3730, 3292]
          and v["transform"] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0])
    complete = inv["repos_not_complete"] == 0
    g4 = bool(uniq["unique_vs_inventory"] is True and complete)
    g5 = v["on_catalogue_positive_pixels"] == 0
    ref = e2["REFERENCE_H33_B2"]["sgmc"]["sgmc_prevalence_calibrated_dti"]
    cand = e2["KS3-strain"]["sgmc"]["sgmc_prevalence_calibrated_dti"]
    g6 = bool(cand >= ref)
    g7 = False  # owner mirrors only; organizer authentication not established
    download_ok = bool(g1 and g2 and g3 and g4 and g5)
    submit_ok = bool(download_ok and g6 and g7)

    blockers = []
    if not g1: blockers.append("G1 format validator failed")
    if not g2: blockers.append("G2 range/finite grid failed")
    if not g3: blockers.append("G3 grid mismatch")
    if not g4: blockers.append("G4 not unique under the two-way rule (see duplicate_flags)")
    if not g5: blockers.append("G5 catalogue dots present")
    if not g6: blockers.append("G6 proxy below H33 reference")
    if not g7: blockers.append("G7 organizer provenance not established")
    if submit_ok:
        verdict = "SUBMIT ALLOWED"
    elif download_ok:
        verdict = "DOWNLOAD FOR RECORD ONLY - DO NOT SUBMIT"
    elif not g4:
        verdict = "DO NOT DOWNLOAD OR SUBMIT - NOT UNIQUE"
    else:
        verdict = "DO NOT DOWNLOAD OR SUBMIT"

    card = {
        "kind": "VERDICT CARD - KS3-strain candidate (proxies, not organizer scores)",
        "date_utc": "2026-10-29",
        "file": mat["published_file"],
        "sha256": mat["sha256"],
        "bytes": mat["bytes"],
        "name": "KANLER-S3-strain-37654-20261029",
        "note": mat["note"],
        "note_chars": mat["note_chars"],
        "gates": {
            "G1_format_validator_passed": g1,
            "G2_range_0_1_full_grid_finite": g2,
            "G3_grid_crs_shape_transform": g3,
            "G4_unique_vs_inventory_and_inventory_complete": g4,
            "G4_detail": {"files_compared": uniq["files_compared"], "files_inventoried": uniq["files_inventoried"],
                          "not_comparable": uniq["files_not_comparable"], "unreadable": uniq["files_unreadable"],
                          "max_coverage_candidate_dots": uniq["max_coverage_candidate_dots"],
                          "max_coverage_peer_dots": uniq["max_coverage_peer_dots"],
                          "max_rank_corr": uniq["max_rank_corr"],
                          "duplicate_flags": uniq["duplicate_flags"],
                          "repos_listed": inv["repos_listed"], "repos_available": inv["repos_available"],
                          "repos_not_complete": inv["repos_not_complete"]},
            "G5_zero_catalogue_dots": g5,
            "G6_value_gate_sgmc_cal_ge_H33": g6,
            "G6_detail": {"candidate_sgmc_cal": cand, "H33_B2_reference_sgmc_cal": ref,
                          "candidate_ci95": e2["KS3-strain"]["sgmc"]["sgmc_calibrated_ci95"],
                          "H33_ci95": e2["REFERENCE_H33_B2"]["sgmc"]["sgmc_calibrated_ci95"]},
            "G7_organizer_provenance": g7,
        },
        "download_allowed": download_ok,
        "submit_allowed": submit_ok,
        "verdict": verdict,
        "blockers": blockers,
        "duplicate_flags": uniq["duplicate_flags"],
        "estimated_leaderboard_score": "NOT ESTIMATED",
        "e1_canary_max_auc": e1["max_auc_feature"],
        "slot_authorized": False,
        "weekly_slots_used_this_session": 0,
    }
    OUT.write_text(json.dumps(card, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "download_allowed": download_ok, "submit_allowed": submit_ok,
                      "gates": {k: v for k, v in card["gates"].items() if not k.endswith("detail")}}, indent=1))
    return card


if __name__ == "__main__":
    main()
