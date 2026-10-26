#!/usr/bin/env python3
"""Assemble the final JSON run card from committed evidence files only (deterministic; no data/ needed).

The verdict is computed, not typed: (1) the pre-registered decision rules
(research/preregistration-20261026.md) and (2) the repository's automated promotion gate
(scripts/promotion_gate.py).  Either one failing => verdict "negative".
Writes evidence/k3h1-run-card.json and docs/k3h1-run-card.json (identical).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from promotion_gate import assess  # noqa: E402

FOCUS = {  # site -> live-ledger submission name of that site's best scored file (OWNER-REPORT scores)
    "GEMSDOE24": "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan",
    "GEMSDOE25": "dotted-h19-5-d2-8-20261002-e56ea318af89-nan",
    "GEMSDOE27": "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan",
    "GEMSDOE28": "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan",
    "GEMSDOE30": "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca",
    "GEMSDOE31": "h27-4-solo-d28-20261004-8acb75e1-nan",
    "GEMSDOE32": "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
    "GEMSDOE33": "h33d-analog-tip-stepover-r30-20261004-cb490425926e",
    "GEMSDOE36": "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros",
}


def load(p: str):
    return json.loads((ROOT / p).read_text())


def r4(x):
    return None if x is None else round(float(x), 4)


def main() -> int:
    e1, e2, e3 = load("evidence/e1_holdout.json"), load("evidence/e2_unique.json"), load("evidence/e3_hybrid.json")
    can3, uq, val = load("evidence/e3_canary.json"), load("evidence/uniqueness_final.json"), load("evidence/validator_final.json")
    log = load("evidence/experiment_log.json")
    receipt_path = sorted((ROOT / "docs" / "downloads").glob("kanler3-k3h1-*-zeros.json"))
    assert len(receipt_path) == 1, receipt_path
    rc = json.loads(receipt_path[0].read_text())
    assert rc["sha256"] == uq["candidate_file_sha256"] == val["submit_safe"]["sha256"], "evidence refers to different bytes"
    ho = e3["holdout"]["pooled"]
    s_e3, s_c1 = ho["scores"]["E3_HYBRID"], ho["scores"]["C1"]
    d = ho["paired_differences"]["C1"]
    proj, proj_ch = e3["live"]["projection"]["dti"], e3["live"]["champion_projection_same_fit"]["dti"]
    max_auc = max(e1["leakage_canary"]["max_oriented_auc"], can3["max_oriented_auc"])
    checks = rc["validator"]["checks"]
    rows = {r["submission"]: r for r in uq["rows"] if "error" not in r}
    focus = []
    for site, sub in FOCUS.items():
        r = rows.get(sub)
        focus.append({"site": site, "submission": sub, "sha256": r["sha256"] if r else None,
                      "owner_reported_live_score": r["owner_reported_live_score"] if r else None,
                      "their_dots": r["their_dots"] if r else None,
                      "candidate_overlap_3px": r4(r["my_dots_within_3px_of_theirs"]) if r else None,
                      "candidate_spearman": r4(r["spearman_full_footprint"]) if r else None})
    prereg_rules = {
        "format_valid": bool(rc["validator"]["all_checks_passed"] and val["official_format"]["ok"]),
        "unique": bool(uq["unique"]),
        "holdout_ge_best_control": bool(s_e3["dti"] >= s_c1["dti"]),
        "projection_ge_champion_same_fit": bool(proj >= proj_ch),
    }
    card = {
        "schema_version": 2,
        "run_id": "kanler3-k3h1-20261026",
        "lane": "K3-H1 ASGT: antislope-scarp grain traces (self-assigned and pre-registered; IR-K3-LANE-01: the prompt's lane paragraph is missing)",
        "preregistration": log["preregistration"],
        "hypothesis": ("Scarps that face UPHILL (against the 100 m regional slope), are coherent over >=300 m and parallel the "
                       "local fault grain are tectonic; small antislope scarps visible only in 1 m lidar are what pre-lidar "
                       "fault compilations miss, so they should mark uncatalogued faults."),
        "mechanism": ("Normal faulting in the Basin and Range produces antithetic/synthetic scarps whose free face can oppose the "
                      "topographic slope; erosion, deposition, terraces and shorelines produce downhill-facing risers. Facing "
                      "polarity x grain compatibility x coherence is therefore a fault-specific geomorphic signature."),
        "non_fault_mimic": ("Landslide and sackung headscarps (uphill-facing ridge-top scarps: relief veto), channel banks "
                            "(cross-slope dominance), roads/berms (short, straight; grain/coherence down-weight), lake shorelines "
                            "(downhill-facing: excluded)."),
        "experiments": [
            {"id": "E1", "question": "Does the ASGT mechanism recover withheld catalogue faults?",
             "result": f"HOLDOUT-DTI ASGT {r4(e1['pooled']['scores']['ASGT']['dti'])} vs ablation A (upface only) "
                       f"{r4(e1['pooled']['scores']['ABL_A']['dti'])}: paired delta "
                       f"{r4(e1['pooled']['paired_differences']['ABL_A']['delta'])} CI95 "
                       f"{[r4(x) for x in e1['pooled']['paired_differences']['ABL_A']['ci95']]} -> mechanism supported; "
                       f"vs C1 {r4(e1['pooled']['paired_differences']['C1']['delta'])} CI95 "
                       f"{[r4(x) for x in e1['pooled']['paired_differences']['C1']['ci95']]} (tie)",
             "evidence": "evidence/e1_holdout.json"},
            {"id": "E2", "question": "Does a protocol-unique pure-ASGT file project competitively on the live ledger?",
             "result": f"No: 16 files (30-60k dots, exclusion 3/5 px, capped/uncapped) PROJECTION "
                       f"{min(g['lli_projection'] for g in e2['grid']):.3f}-{max(g['lli_projection'] for g in e2['grid']):.3f} "
                       f"vs champion {e2['champion_projection_same_fit']:.4f} (same fit); ASGT dots sit ~70% off the H19-5 network",
             "evidence": "evidence/e2_unique.json"},
            {"id": "E3", "question": "ASGT-ranked H19-5 core (<=69.5%) + ASGT novel share (>=30.5%)",
             "result": f"PROJECTION {proj:.4f} vs champion {proj_ch:.4f}; HOLDOUT-DTI {s_e3['dti']:.4f} vs C1 {s_c1['dti']:.4f}, "
                       f"paired delta {d['delta']:+.4f} CI95 [{d['ci95'][0]:+.4f}, {d['ci95'][1]:+.4f}]",
             "evidence": "evidence/e3_hybrid.json"},
        ],
        "budget": log["budget"],
        "deviations": log["deviations"],
        "holdout": {"class": "HOLDOUT-DTI", "evaluator_version": ho["evaluator_version"],
                    "withheld_positives": int(s_e3["withheld_positive_pixels"]), "value": round(s_e3["dti"], 4),
                    "ci95": [round(x, 4) for x in s_e3["ci95"]], "alpha": 0.2, "beta": 0.8, "kernel_m": 300,
                    "kernel": "triangular", "aggregation": "pooled",
                    "split": "gems57 buffered_component_draw seed 20: 20% whole components withheld per label-blind quadrant, "
                             "3-px collar, 12-px fold boundary buffer, visible catalogue masked pixel-exactly",
                    "bootstrap": ho["bootstrap"], "incumbent": "C1 = H19-5 dotted at 2.8 px with fold-local 2-px catalogue "
                    "exclusion (the champion recipe; leak-advantaged)", "incumbent_value": round(s_c1["dti"], 4),
                    "incumbent_ci95": [round(x, 4) for x in s_c1["ci95"]]},
        "paired_improvement_ci95": [round(x, 4) for x in d["ci95"]],
        "paired_improvement_delta": round(d["delta"], 4),
        "projection": {"class": "PROJECTION (live-ledger inversion; NOT a score)", "value": round(proj, 4),
                       "champion_same_fit": round(proj_ch, 4), "champion_owner_reported_live": 0.2778,
                       "model": "GEMSDOE32 LLI S3 archived fit reused unchanged (vendor/gems32lli); 111 scored rasters",
                       "loo_mae": round(e2["lli"]["loo"]["mae"], 4), "loo_abs_err_q90": round(e2["lli"]["loo"]["abs_err_q90"], 4)},
        "leakage_canary": {"threshold": 0.90, "max_oriented_auc": max_auc, "passed": max_auc <= 0.90,
                           "e1_max_feature": e1["leakage_canary"]["max_feature"], "e3": "evidence/e3_canary.json"},
        "max_feature_auc": max_auc,
        "registry": {k: uq[k] for k in ("registry_rasters_listed", "registry_rasters_compared", "worst_overlap_non_space_filling",
                                        "worst_spearman_final_dots", "worst_spearman_surface_preplacement", "byte_unique",
                                        "pixel_unique", "duplicates_non_space_filling", "unique", "scope",
                                        "literal_rule_blocked_only_by_space_filling", "space_filling_rasters",
                                        "registry_rasters_not_comparable")},
        "focus_sites": focus,
        "surface_max_rank_correlation": uq["worst_spearman_surface_preplacement"]["value"],
        "final_max_rank_correlation": uq["worst_spearman_final_dots"]["value"],
        "surface_dot_overlap_3px": e3["live"]["worst_overlap_non_space_filling"],
        "final_dot_overlap_3px": uq["worst_overlap_non_space_filling"]["value"],
        "raster_file": rc["file"], "raster_sha256": rc["sha256"], "raster_bytes": rc["bytes"],
        "zip_file": rc["zip_file"], "zip_sha256": rc["zip_sha256"],
        "validator": {"single_band": checks["single_band"],
                      "no_nan_inside_footprint": checks["in_footprint_all_finite"] and checks["no_nan_anywhere"],
                      "values_0_1_inside_footprint": checks["in_footprint_range_0_1"],
                      "all_finite": checks["no_nan_anywhere"] and checks["no_inf_anywhere"],
                      "range_0_1": checks["range_0_1_guaranteed"] and checks["min_ge_0"] and checks["max_le_1"],
                      "crs_match": checks["crs_epsg_32611"], "shape_match": checks["dimensions_3730x3292"],
                      "transform_match": checks["transform_matches_sample_submission"],
                      "shared_validator_checks": checks, "official_format_ok": val["official_format"]["ok"],
                      "validator_versions": [val["validator_version"], "vendor/gems57/validate.py (unchanged)"]},
        "submission_name": rc["submission_name"], "submission_note": rc["note"], "submission_note_chars": len(rc["note"]),
        # protocol items, stated honestly (false = not satisfied or not verifiable here)
        "lane_recorded": True,
        "shared_template_pinned": True,
        "whole_segment_buffered_holdout": True,
        "visible_only_features": False,
        "pixel_exact_visible_mask": True,
        "all_features_canary_tested": True,
        "same_evaluator_incumbent": True,
        "registry_complete": False,
        "surface_checked_before_placement": False,
        "final_dots_checked": True,
        "saved_bytes_validated": True,
        "template_provenance_verified": False,
        "protocol_notes": {
            "visible_only_features": "ASGT itself uses only visible faults; the E3 core inherits H19-5 (built with the full catalogue).",
            "registry_complete": "433 comparable rasters from GEMSDOE focus manifests + scored live ledger; other teams' files are unknowable.",
            "surface_checked_before_placement": "Registry overlap was enforced DURING placement (constrained allocator); the surface Spearman "
                                                "check (max 0.146) was computed after placement on the pre-placement surface.",
            "template_provenance_verified": "sample_submission.tif comes from a participant data mirror (SHA-verified against that mirror); "
                                            "the official data page requires login, so organizer bytes were not compared.",
        },
        "preregistered_rules": prereg_rules,
    }
    gate = assess(card)
    card["promotion_gate"] = gate
    card["verdict"] = "promote" if (all(prereg_rules.values()) and gate["verdict"] == "promote") else "negative"
    card["download"] = {
        "ok_to_download": True,
        "ok_to_upload_format": bool(prereg_rules["format_valid"]),
        "recommended_for_weekly_slot": card["verdict"] == "promote",
        "bottom_line": ("VALID + UNIQUE research file. NOT expected to beat 0.2778 (PROJECTION %.3f vs %.3f for the champion under the "
                        "same model; HOLDOUT-DTI not better than the best control). Upload only if you want a protocol-unique entry; "
                        "do not spend a slot expecting a higher score." % (proj, proj_ch)),
    }
    card["slots_used"] = 0
    txt = json.dumps(card, indent=1, default=float) + "\n"
    (ROOT / "evidence" / "k3h1-run-card.json").write_text(txt)
    (ROOT / "docs" / "k3h1-run-card.json").write_text(txt)
    print(json.dumps({"verdict": card["verdict"], "preregistered_rules": prereg_rules, "gate": gate}, indent=1))
    return 0


if __name__ == "__main__":
    from archive_guard import stop_archived_cli
    stop_archived_cli()
    sys.exit(main())
