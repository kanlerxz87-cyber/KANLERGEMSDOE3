#!/usr/bin/env python3
"""Build the submission desk page and the session run card from recorded evidence.

Inputs (all read-only, nothing is recomputed here):
  evidence/catalogue-blind-e123-20261028.json        candidate run (E1-E3, chosen E2, gates, verdict)
  evidence/catalogue-blind-audits-20261028.json      incumbents, controls, canary, proximity, saturation
  sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json   pairwise overlap, lineage, refs
  registry/focus9_champions.json                     best supplied file per priority site (owner claims)
Outputs:
  evidence/run-card-catalogue-blind-20261028.json
  docs/submission-desk.html

Usage:  python scripts/build_submission_desk.py          # write
        python scripts/build_submission_desk.py --check  # exit 1 if outputs are stale
Labels: every proxy number is HOLDOUT-DTI; organizer-confirmed score is none; owner claims are quoted
as unverified text and never placed in a score column.
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E123 = ROOT / "evidence/catalogue-blind-e123-20261028.json"
AUD = ROOT / "evidence/catalogue-blind-audits-20261028.json"
OVL = ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json"
CHAMP = ROOT / "registry/focus9_champions.json"
CARD = ROOT / "evidence/run-card-catalogue-blind-20261028.json"
PAGE = ROOT / "docs/submission-desk.html"
CFRP_AUDIT = ROOT / "evidence/uniqueness-audit-kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros-20261028.json"
DUP_LIMIT = 0.70
SITES = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build() -> tuple[dict, str]:
    e123, aud, ovl, champ = load(E123), load(AUD), load(OVL), load(CHAMP)
    inc = aud["incumbents_same_evaluator"]
    pair = {(r["candidate_repo"], r["reference_repo"]): r["directional_within_3px_fraction"] for r in ovl["pairwise_directional_3px_overlap"]}
    entries = {e["site"]: e for e in champ["entries"]}
    assert set(entries) == set(SITES), "champion list must cover the nine priority sites"
    assert len(pair) == 72, "expected 72 directed pairs among nine winners"

    rows = []
    for s in SITES:
        others = {r: v for (c, r), v in pair.items() if c == s}
        worst_ref = max(others, key=others.get)
        mx = others[worst_ref]
        e = entries[s]
        rows.append({
            "site": s,
            "file": e["path"],
            "file_sha256_claimed": e["sha256"],
            "owner_claim_unverified": e["score_owner_reported"],
            "estimated_score_organizer_confirmed": None,
            "estimated_score_label": "NOT ESTIMABLE — no organizer receipt; no projection written",
            "max_directed_overlap_3px_vs_other_priority_sites": round(mx, 4),
            "max_overlap_reference_site": worst_ref,
            "literal_duplicate_stop_triggered": mx > DUP_LIMIT,
            "proxy_hide_recover_holdout_dti": inc[s]["hide_recover_pooled_dti"],
            "proxy_sgmc_raw_holdout_dti": inc[s]["sgmc_raw_pooled_dti"],
            "dots_within_2px_of_full_catalogue": aud["catalogue_proximity"][s]["dots_within_2px_of_catalogue"],
            "status": "DO NOT SUBMIT — literal duplicate of another priority site" if mx > DUP_LIMIT else "REVIEW",
            "label_proxy": "HOLDOUT-DTI",
        })
    assert all(r["literal_duplicate_stop_triggered"] for r in rows), "all nine winners are expected to trip the stop"

    fin = e123["final_file"]
    learn = ROOT / "docs/candidate_downloads/kanler3-catalogue-blind-e2-ridgecoh-37654-20261028.tif"
    assert sha256(learn) == fin["sha256"], "published learning file does not match the recorded sha256"
    fmt = fin["format"]
    hold = fin["holdout_on_file"]
    uniq_final = e123["uniqueness"]["final_dots"]
    rows_u = e123["uniqueness_rows_final"]
    non_sat = [r for r in rows_u if r.get("comparable") and r["id"] not in uniq_final["saturated_probe_flags"]]
    sat = [r for r in rows_u if r["id"] in uniq_final["saturated_probe_flags"]]
    max_non_sat = max(non_sat, key=lambda r: r["directed_dot_overlap_3px"])
    comparable_rows = [r for r in rows_u if r.get("comparable")]
    assert len(comparable_rows) == uniq_final["registry_compared"], "comparable rows must equal registry_compared"
    max_rank = max(abs(r["rank_correlation"]) for r in comparable_rows)
    cand_name = e123["name"]
    cand_note = e123["note"]
    assert len(cand_note) <= 140 and len(cand_name) <= 140

    card = {
        "schema": "kanler3.run_card.v1",
        "date_utc": "2026-10-28",
        "lane": "NOT DEFINED — the user's single-method lane paragraph is absent from the repo; none invented. Self-declared lane: catalogue-blind dot fields (label-free).",
        "question": "Can a catalogue-blind, unique single-band dot field pass the pre-registered holdout gate against the same-evaluator incumbents?",
        "experiments": {"budget": 3, "used": 3, "ids": ["E1_ridge2_nms", "E2_ridge2xcoh_nms", "E3_half_nms_half_bluenoise"], "chosen": e123["chosen"], "selection": "label-free; pre-registered before scoring"},
        "time_budget_minutes": 120,
        "pipeline_seconds_recorded": e123.get("seconds"),
        "duplicate_stop": {
            "spearman_limit": 0.90, "max_abs_rank_correlation": round(max_rank, 4), "spearman_triggered": max_rank > 0.90,
            "overlap_limit_3px": 0.70,
            "non_saturated_max_directed_overlap": round(max_non_sat["directed_dot_overlap_3px"], 4),
            "non_saturated_reference": max_non_sat["id"],
            "saturated_probe": sat[0]["id"] if sat else None,
            "saturated_probe_directed_overlap": round(sat[0]["directed_dot_overlap_3px"], 4) if sat else None,
            "triggered_literal": bool(sat) and sat[0]["directed_dot_overlap_3px"] > 0.70,
            "interpretation": "Literal stop trips only on the saturated lattice probe; uniform random dots also trip it (audit saturation_lattice_r13). Reported as a rule defect, not waived."},
        "leakage_canary": {
            "threshold_auc": 0.90,
            "single_feature_max_auc_vs_offcatalogue_sgmc": aud["leakage_canary_auc_vs_sgmc_offcatalogue"]["max_auc"],
            "single_feature_channels_above_threshold": aud["leakage_canary_auc_vs_sgmc_offcatalogue"]["channels_above_0_90"],
            "hide_recover_full_catalogue_distance_auc": aud["hide_recover_distance_canary"]["auc_distance_to_FULL_catalogue"],
            "hide_recover_visible_catalogue_distance_auc": aud["hide_recover_distance_canary"]["auc_distance_to_VISIBLE_catalogue"],
            "interpretation": "Candidate features pass (max 0.7685). The full-catalogue distance AUC of 1.0 is leakage in the proxy design; it was not used in selection."},
        "hypothesis": {
            "H_primary": "A label-free ridge-times-coherence dot field (E2) beats the same-evaluator incumbent on both proxies.",
            "result": "NOT SUPPORTED on hide-and-recover (0.0268 vs 0.0967; file 0.0204). Partly on SGMC raw (0.1171 vs 0.1024), but the CIs overlap the incumbents and the gate requires both.",
            "mechanism_hypothesis": "Hide-and-recover rewards proximity to visible catalogue traces; catalogue-blind dots lose that reward. SGMC agrees with the leaderboard direction in only part of the set.",
            "named_non_fault_mimic": "Catalogue-mapping completeness and relief: dots follow mapped traces and high relief, which can mimic fault signal without new-fault skill.",
            "status": "PARTIALLY SUPPORTED / UNTESTED on the organizer leaderboard"},
        "candidate": {
            "name": cand_name, "note": cand_note, "note_chars": len(cand_note),
            "file": "docs/candidate_downloads/kanler3-catalogue-blind-e2-ridgecoh-37654-20261028.tif",
            "sha256": fin["sha256"], "bytes": fin["bytes"], "dots_after_catalogue_removal": fin["dots_after_catalogue_removal"],
            "catalogue_pixels_removed": fin["catalogue_pixels_removed"],
            "format": fmt,
            "holdout_on_file": hold,
            "label": "HOLDOUT-DTI",
            "authorized": False,
            "cleared_for_submission": False,
            "safety": "NOT SAFE TO SUBMIT — learning artifact only"},
        "gates": e123["gates"],
        "verdict": e123["verdict"],
        "slot_authorized": e123["slot_authorized"],
        "weekly_slots_spent": 0,
        "organizer_confirmed_scores": [],
        "incumbent_comparison_same_evaluator": {"hide_recover": e123["incumbent_best_same_evaluator"]["hide_recover"], "sgmc_raw": e123["incumbent_best_same_evaluator"]["sgmc_raw"]},
        "audits_file": "evidence/catalogue-blind-audits-20261028.json",
        "e123_file": "evidence/catalogue-blind-e123-20261028.json",
        "prereg_file": "research/catalogue-blind-prereg-20261028.md",
        "generated_by": "scripts/build_submission_desk.py",
    }
    cfrp = load(CFRP_AUDIT)
    assert cfrp["same_evaluator_holdout"]["incumbent_best_same_evaluator"] == {"hide_recover": 0.0967, "sgmc_raw": 0.1024}
    card["other_lane_on_main"] = {
        "file": "docs/cfrp-20261028/downloads/kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros.tif",
        "sha256": cfrp["candidate_sha256"],
        "status": "CONTESTED — another lane's page on main labels it eligible; this lane's audit does not support that. Decision required.",
        "same_evaluator_holdout": cfrp["same_evaluator_holdout"],
        "registry_max_directed_overlap_3px_non_saturated": round(cfrp["max_directed_overlap_3px_non_saturated"], 4),
        "registry_saturated_probe_flags": cfrp["saturated_probe_flags"],
        "audit_file": str(CFRP_AUDIT.relative_to(ROOT)),
    }
    return card, build_html(card, rows, aud, ovl, inc, rows_u, uniq_final)


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def build_html(card: dict, rows: list, aud: dict, ovl: dict, inc: dict, rows_u: list, uniq_final: dict) -> str:
    esc = html.escape
    cand = card["candidate"]
    h = cand["holdout_on_file"]
    fmt = cand["format"]
    cfrp = card["other_lane_on_main"]
    cfrp = {"same_evaluator_holdout": cfrp["same_evaluator_holdout"], "max_directed_overlap_3px_non_saturated": cfrp["registry_max_directed_overlap_3px_non_saturated"]}
    e123 = load(E123)
    cands = e123["candidates"]
    body_rows = []
    for r in rows:
        ref = ovl["refs"][r["site"]]
        link = f'<a href="https://github.com/buffedlizard55-lab/{esc(r["site"])}/blob/{ref}/{esc(r["file"])}">{esc(Path(r["file"]).name)}</a>'
        body_rows.append(
            f'<tr><th scope="row">{esc(r["site"])}</th>'
            f'<td>{link}</td>'
            f'<td><strong>Not estimable</strong><small>ORGANIZER-CONFIRMED: none</small></td>'
            f'<td>{pct(r["max_directed_overlap_3px_vs_other_priority_sites"])} vs {esc(r["max_overlap_reference_site"])}<small>DUPLICATE (&gt;70%)</small></td>'
            f'<td>{r["proxy_hide_recover_holdout_dti"]:.4f} / {r["proxy_sgmc_raw_holdout_dti"]:.4f}<small>HOLDOUT-DTI</small></td>'
            f'<td><span class="tag negative">DO NOT SUBMIT</span></td></tr>')
    cand_rows = []
    for k, v in cands.items():
        cand_rows.append(f'<tr><th scope="row">{esc(k)}{" (chosen)" if k == card["experiments"]["chosen"] else ""}</th>'
                         f'<td>{v["hide_recover_pooled_dti"]:.4f} [{v["hide_recover_ci95"][0]:.4f}, {v["hide_recover_ci95"][1]:.4f}]</td>'
                         f'<td>{v["sgmc_raw_pooled_dti"]:.4f} [{v["sgmc_raw_ci95"][0]:.4f}, {v["sgmc_raw_ci95"][1]:.4f}]</td>'
                         f'<td>{v["sgmc_calibrated_dti"]:.4f}</td><td>HOLDOUT-DTI</td></tr>')
    inc_rows = []
    for s in SITES:
        i = inc[s]
        inc_rows.append(f'<tr><th scope="row">{esc(s)}</th><td>{i["hide_recover_pooled_dti"]:.4f}</td><td>{i["sgmc_raw_pooled_dti"]:.4f}</td><td>{pct(aud["catalogue_proximity"][s]["dots_within_2px_of_catalogue"])}</td><td>HOLDOUT-DTI</td></tr>')
    ctrl = aud["control_uniform_random"]
    h33 = inc["GEMSDOE32"]
    h33_prox = aud["catalogue_proximity"]["GEMSDOE32"]["dots_within_2px_of_catalogue"]
    sat = aud["saturation_lattice_r13"]
    lineage = [r for r in ovl["exact_mask_relations"]]
    lx = aud["lineage_exact"]
    assert lx["GEMSDOE32_subset_of_GEMSDOE31"] and lx["removed_31_to_32"] == lx["removed_31_to_32_within_2px_of_catalogue"] == 2545
    lin_html = "".join(f'<li><code>{esc(" + ".join(x["pair"]) if "pair" in x else "")}</code>: {esc(str(x.get("interpretation") or x.get("parent_child") or ""))} (XOR positive pixels: {x.get("xor_positive_pixels")})</li>' for x in lineage)
    uniq_rows = "".join(f'<li>{esc(r["id"])}: directed {pct(r["directed_dot_overlap_3px"])}, Spearman {r["rank_correlation"]:+.4f}{" — saturated probe" if r["id"] in uniq_final["saturated_probe_flags"] else ""}</li>' for r in rows_u if r["id"] in uniq_final["saturated_probe_flags"])

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Submission desk — GEMSDOE priority sites</title>
<link rel="stylesheet" href="assets/site.css">
<meta name="description" content="Best-available file per priority site, learning artifact status, holdout evidence, and the rule on what may be submitted.">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="bar"><a class="brand" href="index.html">KANLER GEMSDOE · Submission desk</a><nav aria-label="Pages"><a href="index.html">Home</a> · <a href="SUBMISSION_GUIDE.md">Guide</a> · <a href="EXECUTIVE_SUMMARY.md">Executive summary</a></nav></div></header>
<main id="main" class="section">
<section class="page-intro"><p class="eyebrow">Submission desk · 28 Oct 2026 · priority sites GEMSDOE24/25/27/28/30/31/32/33/36</p>
<h1 class="subtitle-page">Which file to submit?<br>None is cleared today.</h1>
<p>Every number is labelled <strong>HOLDOUT-DTI</strong> (our hide-and-recover or SGMC proxy, same evaluator for all rows) or <strong>ORGANIZER-CONFIRMED</strong> (none exists). Projections are never written as scores.</p></section>

<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — no file is cleared.</strong><p>The published learning artifact below is <strong>NOT SAFE TO SUBMIT</strong>: it failed the pre-registered holdout gate. Previous submissions may be studied, not resubmitted as new work.</p></div></div>

<section class="section panel"><h2>1. Best supplied file per priority site</h2>
<p>Owner claims (0.2449–0.2778) are <strong>unverified</strong>, not organizer receipts, and are not shown as scores. Overlap compares each winner with the other eight priority winners (directed, 3 px). Every site exceeds the 70% literal stop against at least one other winner.</p>
<div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">File (GitHub)</th><th scope="col">Estimated score</th><th scope="col">Uniqueness vs other GEMSDOE sites</th><th scope="col">Proxy hide-recover / SGMC raw</th><th scope="col">Status</th></tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>
<p class="table-note">Owner-claimed scores per site are in <code>registry/focus9_champions.json</code> and are not labelled as scores here.</p></section>

<section class="section panel"><h2>2. Learning artifact (not cleared)</h2>
<p><strong>{esc(cand["name"])}</strong> — note (≤140 chars, {cand["note_chars"]}): <em>{esc(card["candidate"]["note"])}</em></p>
<p><span class="tag negative">NOT SAFE TO SUBMIT</span> Learning and education only. Authorized: <strong>no</strong>. Verdict: <code>{esc(card["verdict"])}</code>.</p>
<ul><li>File: <a href="candidate_downloads/kanler3-catalogue-blind-e2-ridgecoh-37654-20261028.tif">download the learning TIFF</a> ({cand["bytes"]:,} bytes; sha256 <code>{esc(cand["sha256"])}</code>)</li>
<li>Format (automated, no human gate): single band, float32, EPSG:32611, 3730×3292, 100 m transform, values in {{0, 1}}, footprint {fmt["footprint_pixels"]:,} px, {fmt["emitted_positive_pixels"]:,} positives, {cand["catalogue_pixels_removed"]} catalogue pixels removed. Format valid: <strong>{str(fmt["format_valid"]).lower()}</strong>. A format pass never authorizes submission.</li>
<li>Holdout on the file (HOLDOUT-DTI): hide-and-recover <strong>{h["hide_recover_pooled_dti"]:.4f}</strong> [{h["hide_recover_ci95"][0]:.4f}, {h["hide_recover_ci95"][1]:.4f}]; SGMC raw <strong>{h["sgmc_raw_pooled_dti"]:.4f}</strong> [{h["sgmc_raw_ci95"][0]:.4f}, {h["sgmc_raw_ci95"][1]:.4f}]; SGMC calibrated {h["sgmc_calibrated_dti"]:.4f}.</li>
<li>Gates: format <strong>{str(card["gates"]["format"]).lower()}</strong>; unique vs non-saturated registry <strong>{str(card["gates"]["unique_vs_compared_registry_non_saturated"]).lower()}</strong>; saturated probe flagged <strong>{str(card["gates"]["saturated_probe_flagged_literal_stop"]).lower()}</strong>; beats same-evaluator incumbent on both proxies <strong>{str(card["gates"]["beats_same_evaluator_incumbent_on_both_proxies"]).lower()}</strong>; registry complete <strong>{str(card["gates"]["registry_complete"]).lower()}</strong>.</li></ul>
</section>

<section class="section panel"><h2>3. Experiments (pre-registered, label-free, budget 3)</h2>
<div class="table-wrap"><table><thead><tr><th scope="col">Candidate</th><th scope="col">Hide-recover DTI [95% CI]</th><th scope="col">SGMC raw [95% CI]</th><th scope="col">SGMC calibrated</th><th scope="col">Label</th></tr></thead><tbody>{"".join(cand_rows)}</tbody></table></div>
<p class="table-note">Incumbent best on the same evaluators: hide-recover {e123["incumbent_best_same_evaluator"]["hide_recover"]:.4f}; SGMC raw {e123["incumbent_best_same_evaluator"]["sgmc_raw"]:.4f}. Random uniform 37,654 dots: hide-recover {ctrl["hide_recover_pooled_dti"]:.4f}, SGMC raw {ctrl["sgmc_raw_pooled_dti"]:.4f}.</p>
<p>Chosen: <code>{esc(card["experiments"]["chosen"])}</code>. The remaining two experiments are not used to pick a winner. Weekly slots spent: <strong>0</strong>.</p></section>

<section class="section panel"><h2>4. GEMSDOE32 h33-h33-2-b2 (owner claim 0.2778): what the evidence shows</h2>
<p>Owner claim 0.2778 is <strong>unverified</strong>. Its same-evaluator proxies are low: hide-recover <strong>{h33["hide_recover_pooled_dti"]:.4f}</strong> and SGMC raw <strong>{h33["sgmc_raw_pooled_dti"]:.4f}</strong> (HOLDOUT-DTI). Only {pct(h33_prox)} of its dots lie within 2 px of the full catalogue (labels.tif).</p>
<ul>{lin_html}</ul>
<p>Exact set comparison (audit <code>lineage_exact</code>): GEMSDOE32 is a strict subset of GEMSDOE31. The {lx["removed_31_to_32"]:,} removed dots are {lx["removed_31_to_32_within_2px_of_catalogue"]:,} of GEMSDOE31's {lx["GEMSDOE31_dots_within_2px_of_catalogue"]:,} dots within 2 px of the catalogue, so the removal is exactly the catalogue-adjacent set. GEMSDOE36 adds {lx["added_32_to_36"]:,} dots, none within 2 px of the catalogue ({lx["added_32_to_36_within_2px_of_catalogue"]} of {lx["added_32_to_36"]:,}).</p>
<p>Owner claims go from 0.2708 (GEMSDOE31) to 0.2778 (GEMSDOE32), and GEMSDOE36 (0.2750) added dots away from the catalogue. These are single owner-reported observations, not organizer receipts. Our proxies move the other way: GEMSDOE32 has the lowest hide-recover score of the nine (0.0045). The proxy and the claim disagree, so no mechanism is established.</p></section>

<section class="section panel"><h2>5. Catalogue proximity and proxy audit</h2>
<div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Hide-recover DTI</th><th scope="col">SGMC raw DTI</th><th scope="col">Dots within 2 px of full catalogue</th><th scope="col">Label</th></tr></thead><tbody>{"".join(inc_rows)}</tbody></table></div>
<p class="table-note">Leakage canary: max single-feature AUC vs off-catalogue SGMC = {card["leakage_canary"]["single_feature_max_auc_vs_offcatalogue_sgmc"]:.4f} (threshold 0.90, pass). Full-catalogue distance AUC in the hide-recover proxy = {card["leakage_canary"]["hide_recover_full_catalogue_distance_auc"]:.1f} (leaky by construction; not used in selection).</p></section>

<section class="section panel"><h2>6. Uniqueness and the saturated probe</h2>
<p>Non-saturated registry rasters: no duplicate under the 70% stop. The 13-GEMSDOE lattice probe, however, trips the literal rule: uniform random dots score {pct(sat["uniform_random_directed_overlap_trials"][0])} against it, so the stop cannot discriminate. This is a rule-owner decision, not a pass.</p>
<ul>{uniq_rows}</ul>
<p>Lattice covers {pct(sat["footprint_fraction_within_3px"])} of the footprint within 3 px.</p></section>

<section class="section panel"><h2>7. How to submit when a file is cleared</h2>
<ol><li>Only a file whose status reads <strong>CLEARED — SAFE TO SUBMIT</strong> here may be uploaded. Today there is none.</li>
<li>Re-run the automated validator on the exact bytes; the sha256 must match this page.</li>
<li>Use a note of at most 140 characters, and disclose generative-AI use in the narrative (NLR Official Rules, Sep 2026).</li>
<li>The competition allows 3 submissions per week; experiments do not spend slots.</li></ol>
<p>Sources: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData competition page</a> (metric, format, weekly limit); <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR Official Rules (Sep 2026)</a> (single GeoTIFF, disclosure).</p></section>

<section class="section panel"><h2>8. Irregularities</h2>
<ul>
<li>Owner-claimed scores (0.2449–0.2778) are about three times the proxy scale and have no organizer receipt. They appear here only as quoted claims.</li>
<li>GEMSDOE32 scores below uniform random on hide-recover (0.0045 vs 0.0447) because its dots lie on mapped catalogue traces that the holdout masks out.</li>
<li>Literal 70% uniqueness stop trips on the saturated lattice probe, and on uniform random dots as well. A rule-owner decision is required.</li>
<li>The lattice registry entry's provenance and score are not verified in this session. Three registry rasters were not restored.</li>
<li>Vendor <code>gems32/grid.py</code> documents a footprint of 5,165,852 px; the restored sample footprint and <code>src/gems/submission.py</code> give 5,167,373 px. Unresolved.</li>
<li>The earlier rejected "[0,1]" upload was never supplied; its cause is unknown and no fix is proven.</li>
<li>The single-method lane paragraph is absent from the repo. None has been invented.</li>
</ul></section>

<section class="section panel"><h2>9. Other lane on main: CFRP file — CONTESTED</h2>
<p>Another session merged a CFRP subpage (<code>docs/cfrp-20261028/</code>) that says its file is <strong>the only eligible file</strong>. This lane does not accept that label. Its own validator records <code>organizer_acceptance: NOT_TESTED</code>. Its 0.1388 holdout uses a different evaluator (<code>gems-segment-pooled-v1</code>) and is not on this page's scale. Its uniqueness check covers focus-9 champions only.</p>
<p>Same audit, applied here (read-only, no slot): the file scores <strong>{cfrp["same_evaluator_holdout"]["hide_recover_pooled_dti"]:.4f}</strong> on hide-recover (CI [{cfrp["same_evaluator_holdout"]["hide_recover_ci95"][0]:.4f}, {cfrp["same_evaluator_holdout"]["hide_recover_ci95"][1]:.4f}]) and <strong>{cfrp["same_evaluator_holdout"]["sgmc_raw_pooled_dti"]:.4f}</strong> on SGMC raw (HOLDOUT-DTI), against incumbent bests of 0.0967 and 0.1024. It does not beat either. Full-registry uniqueness: non-saturated max directed overlap {pct(cfrp["max_directed_overlap_3px_non_saturated"])} (below 70%), and it trips the saturated lattice probe like every other dot field tested.</p>
<p><strong>Decision required:</strong> whether the CFRP page's "download and submit" label stands. This desk does not clear it. The same-evaluator evidence does not support that label, and it stays a decision for the user.</p>
<p class="table-note">Audit: <a href="../evidence/uniqueness-audit-kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros-20261028.json">evidence/uniqueness-audit-…-zeros-20261028.json</a> (<code>scripts/audit_candidate_uniqueness.py --holdout</code>).</p></section>

<p class="table-note">Generated by <code>scripts/build_submission_desk.py</code> from evidence files. Run card: <a href="../evidence/run-card-catalogue-blind-20261028.json">evidence/run-card-catalogue-blind-20261028.json</a>. Pre-registration: <a href="../research/catalogue-blind-prereg-20261028.md">research/catalogue-blind-prereg-20261028.md</a>.</p>
</main></body></html>
'''


def main(argv: list[str]) -> int:
    card, page = build()
    card_text = json.dumps(card, indent=2) + "\n"
    if "--check" in argv:
        ok = CARD.exists() and CARD.read_text() == card_text and PAGE.exists() and PAGE.read_text() == page
        print("up to date" if ok else "STALE: run scripts/build_submission_desk.py")
        return 0 if ok else 1
    CARD.write_text(card_text)
    PAGE.write_text(page)
    print("wrote", CARD.relative_to(ROOT), PAGE.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
