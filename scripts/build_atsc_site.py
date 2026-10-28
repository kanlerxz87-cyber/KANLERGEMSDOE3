#!/usr/bin/env python3
"""Render the ATSC archive from a hash-bound, negative forensic receipt.

Historical model results are not recomputed here. No candidate is produced,
selected, promoted or made available as a competition download. --check is
read-only and fails if any generated page, receipt alias or saved byte is stale.
"""
from __future__ import annotations

import argparse
from html import escape
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_atsc_archive import check_receipt  # noqa: E402
from scripts.build_site import page  # noqa: E402

OUT = ROOT / "docs/atsc-submod"
RECEIPT = ROOT / "evidence/session-cfcca804-atsc-audit.json"
CARD = ROOT / "evidence/atsc-submod-run-card.json"
PEER_RECEIPT = ROOT / "evidence/atsc-current-peer-audit-20261028.json"


def check_bounded_peer_receipt(report: dict, card: dict) -> None:
    """Check a separate bounded peer receipt without claiming registry completeness."""
    try:
        candidate, scope, result = report["candidate"], report["peer_registry_scope"], report["result"]
        rows = report["comparisons"]
        good = (candidate["sha256"] == card["raster_sha256"]
                and candidate["path"] == card["submission_artifacts"]["primary_zeros_tif"]
                and candidate["dots_in_footprint"] == 37654
                and candidate["preplacement_surface_comparison"] is None
                and scope["complete_registry"] is False and result["surface_gate_evaluated"] is False
                and isinstance(rows, list) and scope["rasters_compared"] == len(rows)
                and result["literal_duplicate_stop"] is True)
        for row in rows:
            hits = row["candidate_dots_within_3px"]
            fraction = row["candidate_dot_overlap_3px"]
            good = (good and type(row["is_calibration_probe"]) is bool
                    and type(hits) is int and 0 <= hits <= candidate["dots_in_footprint"]
                    and isinstance(row["sha256"], str) and bool(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]))
                    and type(fraction) in (int, float) and math.isfinite(fraction)
                    and math.isclose(fraction, hits / candidate["dots_in_footprint"], rel_tol=0, abs_tol=5.1e-9)
                    and row["duplicate_over_70_percent"] is (hits / candidate["dots_in_footprint"] > .70))
        genuine = [row for row in rows if not row["is_calibration_probe"]]
        probes = [row for row in rows if row["is_calibration_probe"]]
        good = (good and len(genuine) == scope["genuine_detectors_compared"]
                and len(probes) == scope["calibration_or_continuous_probes_compared"]
                and bool(genuine) and bool(probes)
                and math.isclose(result["max_final_dot_overlap_3px_all_compared"], max(row["candidate_dot_overlap_3px"] for row in rows), abs_tol=1e-8)
                and math.isclose(result["max_final_dot_overlap_3px_genuine_detectors"], max(row["candidate_dot_overlap_3px"] for row in genuine), abs_tol=1e-8)
                and math.isclose(result["max_final_dot_overlap_3px_calibration_or_continuous_probes"], max(row["candidate_dot_overlap_3px"] for row in probes), abs_tol=1e-8))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        good = False
    if not good:
        raise ValueError("Bounded ATSC peer receipt is inconsistent; refuse publication")


def e(value: object) -> str:
    return escape(str(value), quote=True)


def priority_table(rows: list[dict]) -> str:
    rendered = []
    for row in sorted(rows, key=lambda r: -r["owner_reported_leaderboard_score"]):
        filename = Path(row["file"]).name
        rendered.append(f'''<tr><td><a href="../sites/{e(row['repo'])}.html">{e(row['repo'])}</a></td>
<td><code>{e(filename)}</code><small>Historical reference, not an approved download</small></td>
<td>{row['owner_reported_leaderboard_score']:.4f}<small>Owner-reported; no file-bound organizer receipt</small></td>
<td>Not estimable</td><td>Duplicate<small>{row['max_overlap_3px']:.2%} directed maximum among the nine</small></td>
<td><strong>NO</strong></td></tr>''')
    return '''<div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical file</th>
<th>Historical claim</th><th>New-file estimate</th><th>Unique?</th><th>Submit?</th></tr></thead><tbody>''' + "".join(rendered) + "</tbody></table></div>"


def build(check_only: bool = False) -> None:
    raw_receipt = RECEIPT.read_text()
    receipt = json.loads(raw_receipt)
    check_receipt(receipt)
    raw_card = CARD.read_text()
    card = json.loads(raw_card)
    raw_peer = PEER_RECEIPT.read_text()
    peer = json.loads(raw_peer)
    check_bounded_peer_receipt(peer, card)
    rows = json.loads((ROOT / "docs/audit.json").read_text())["rows"]
    if len(rows) != 9 or len({row["repo"] for row in rows}) != 9:
        raise ValueError("The priority-site audit must contain nine distinct sites")

    geom = receipt["measurements"]["zeros"]["geometry"]
    canary = receipt["canary_coverage"]
    hold = card["holdout"]
    pair = receipt["paired_evidence_scope"]
    name = Path(receipt["artifacts"]["zeros"]["file"]).name
    short_note = card["submission_note"]
    if not isinstance(short_note, str) or not 0 < len(short_note) <= 140:
        raise ValueError("Historical note must be at most 140 characters")

    warning = f'''<div class="notice"><span class="icon" aria-hidden="true">!</span><div>
<strong>DO NOT SUBMIT · no approved TIFF or competition slot</strong>
<p>This prior research artifact failed the literal duplicate stop: {geom['candidate_dots_within_3px_of_lattice']:,} / {geom['candidate_dots']:,} saved dots
({geom['candidate_dot_overlap_fraction']:.2%}) are within 3 pixels of a registered binary lattice. A selector cannot waive this rule.
The {canary['recorded_feature_count']} recorded canaries omit all {canary['stage2_corridor_feature_count']} Stage-2 corridor features by name;
this is missing evidence, not proof of leakage. The artifact and historical card remain available for audit only.</p></div></div>'''

    identity = f'''<section class="section panel prose"><h2>What was checked</h2>
<p>Prior zero-outside TIFF: <code>{e(name)}</code><br>SHA-256: <code>{e(receipt['artifacts']['zeros']['sha256'])}</code>.
Its NaN-outside twin has the same in-footprint values. Both fail the lattice stop.
The zero twin passes only the local <code>finite-grid</code> profile; the NaN twin passes only <code>template-mask</code>.
Neither passes <code>masked-finite</code>. Both have finite in-footprint values in [0,1] on the mirrored, unverified grid.
The rejected upload was not supplied, so its range-error cause and portal acceptance remain unknown.</p>
<p><a href="atsc-audit.json">Independent saved-byte and canary audit →</a> · <a href="run-card.json">Unchanged historical card →</a> ·
<a href="../executive-summary.html">Repository submission guide →</a></p></section>'''

    peer_scope = peer["peer_registry_scope"]
    peer_result = peer["result"]
    bounded_peer = f'''<section class="section panel prose"><h2>Fresh bounded final-dot audit (28 Oct): STOP.</h2>
<p>A separate peer audit compared {peer_scope['rasters_compared']} selected raster bytes, including
{peer_scope['genuine_detectors_compared']} that it classified as detectors. Its largest recorded overlap is
{peer_result['max_final_dot_overlap_3px_all_compared']:.2%} under its positive-support convention.
Some references are continuous diagnostics, not established dot fields; their representation remains unresolved.
The sample is incomplete and does not include a pre-placement surface. The independent binary-lattice stop above is sufficient.</p>
<p><code>verdict=negative</code>, <code>slot_authorized=false</code>. <a href="current-peer-audit-20261028.json">Separate bounded peer receipt →</a></p></section>'''

    limitations = f'''<section class="section panel prose"><h2>Historical holdout: not a leaderboard estimate</h2>
<p>The prior card reports <strong>HOLDOUT-DTI {hold['value']:.6f}</strong>, 95% CI
[{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], evaluator <code>{e(hold['evaluator_version'])}</code>,
{hold['withheld_positives']:,} withheld positives. It was not rerun in this review and is not an organizer score or a forecast.
The study used an older, different evaluator/cache, so it does not satisfy the current shared-template protocol by assertion alone.</p>
<p>Its named strongest prior CADG incumbent was reported at HOLDOUT-DTI {pair['incumbent_value']:.6f},
95% CI [{card['incumbent_comparison']['incumbent_ci95'][0]:.6f}, {card['incumbent_comparison']['incumbent_ci95'][1]:.6f}],
<code>{e(hold['evaluator_version'])}</code>, {hold['withheld_positives']:,} withheld positives;
that point difference is not a paired confidence interval. The saved positive paired interval belongs to B0, not CADG.
The omitted Stage-2 canaries, unverified cache/provenance and literal duplicate stop prevent scientific promotion.
The historical <code>registry_complete</code> and <code>all_features_canary_tested</code> flags are not independent proof.</p></section>'''

    intro = f'''<p class="breadcrumb"><a href="../index.html">← Repository executive desk</a></p>
<div class="page-intro"><p class="eyebrow">ATSC research archive · reviewed 28 October 2026</p>
<h1 class="subtitle-page">One prior study.<br>No eligible submission.</h1>
<p>Research-only forensic review, not a new run. The competition targets unmapped fault geometry; it does not by itself establish a geothermal vent or a commercial resource.</p></div>'''

    index_body = intro + warning + identity + bounded_peer + limitations + f'''<section class="section" id="comparison"><div class="section-heading"><div><h2>Nine priority sites</h2><p>Supplied historical claims are unverified and no file below is approved.</p></div></div>{priority_table(rows)}</section>'''

    guide_body = f'''<p class="breadcrumb"><a href="index.html">← ATSC archive</a></p>
<div class="page-intro"><p class="eyebrow">Submission guide · conditional future use</p>
<h1 class="subtitle-page">Do not upload this archive.</h1><p>There is currently no eligible file to download. The steps below describe a future authorized submission, not permission to upload this TIFF.</p></div>{warning}
<section class="section panel prose"><h2>Once a future candidate clears every gate</h2><ol>
<li>Verify the assigned method, whole-segment buffered holdout, every model-feature canary, the same-fold best incumbent and the complete registry, including the pre-placement surface and final dots.</li>
<li>Run the saved-byte validator against an organizer-authenticated template: one float32 band, matching CRS, shape and transform, finite [0,1] values inside the footprint, and the organizer-confirmed exterior encoding.</li>
<li>Only a separate selector may check the account's actual weekly allowance and authorize a slot. Then choose the approved single GeoTIFF or one-GeoTIFF ZIP on the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a>, enter the approved unique name and note, and retain the organizer receipt.</li>
</ol><p>The archived note below is an identifier for historical research, not an approved submission note:</p><pre>{e(short_note)}</pre></section>{identity}'''

    hyp_body = f'''<p class="breadcrumb"><a href="index.html">← ATSC archive</a></p>
<div class="page-intro"><p class="eyebrow">Conditional research · not a new lane</p>
<h1 class="subtitle-page">Geological ideas are hypotheses, not confirmations.</h1>
<p>The earlier ATSC shortlist is preserved for context. No new single-method assignment or experiment is inferred in this review.</p></div>{warning}
<section class="section panel prose"><h2>Prior shortlist and confounders</h2><ol>
<li><strong>Dip-offset structural edges:</strong> compare basinward gravity/magnetic gradients and topographic breaks. Buried faults are plausible, but volcanic contacts can mimic them. High implementation and provenance cost.</li>
<li><strong>Radiometric contrast and survey seams:</strong> examine U/Th/K contrasts along geophysical edges. Lithologic contacts and variable soils can mimic alteration. Medium-to-high cost; official data bytes and usable coverage need verification.</li>
<li><strong>Visible fault tips and relay zones:</strong> derive structural context from fold-visible traces only. Erosional fan channels can mimic a relay. Medium cost; mapping bias can reduce transferability.</li>
<li><strong>Raw flight lines or deformation data:</strong> test independent line profiles or displacement only if official coverage, licensing and downloads are established. Pumping-related subsidence can mimic strain. High cost; not currently verified as viable.</li>
</ol><p>These are conditional priorities, not predicted DTI improvements. Relevant sources: <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN (DOI 10.5066/P93LGLVQ)</a>,
<a href="https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa">USGS structural discontinuities</a>, and
<a href="https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and">USGS blind geothermal play-fairway report</a>.</p></section>
<section class="section panel prose"><h2>Why the H33 claim cannot be causally explained</h2>
<p>The owner-reported 0.2778 has no submission-page receipt bound to the bytes. The pinned geometry shows the GEMSDOE32 dot mask equals the GEMSDOE25/30 mask after removing 6,436 dots near mirrored catalogue pixels, without additions. Lower redundant false-positive mass is plausible, but hidden truth and paired ablation are unavailable. Known-fault masking is pixel-exact, not a 200 m dead zone.</p>
<p>The prior universal marginal-threshold claim is false: truth coverage and incremental weighted false positives are distinct. A reproducible synthetic counterexample is in <a href="atsc-audit.json">the audit</a>; see the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric">organizer metric definition</a> and <a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50">shared issue 50</a>. It is not evidence of a particular hidden score.</p></section>{limitations}'''

    md = f'''# ATSC research archive — DO NOT SUBMIT

No competition TIFF is approved. The historic `{name}` has {geom['candidate_dots_within_3px_of_lattice']:,} / {geom['candidate_dots']:,} dots ({geom['candidate_dot_overlap_fraction']:.2%}) within 3 px of the registered lattice; a selector cannot waive the stop.

The historical card reports HOLDOUT-DTI {hold['value']:.6f} (95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], `{hold['evaluator_version']}`, {hold['withheld_positives']:,} withheld positives). This was not rerun and is not an organizer score or leaderboard forecast. The positive paired interval is vs B0, not the named CADG incumbent. The {canary['recorded_feature_count']} recorded canaries omit all {canary['stage2_corridor_feature_count']} Stage-2 corridor features by name; absence does not prove leakage.

The zero TIFF locally passes `finite-grid`, not `template-mask`; the NaN twin passes `template-mask`, not `finite-grid`. Neither passes `masked-finite`. Portal acceptance and the earlier rejected-file cause are unknown. See [the forensic receipt](atsc-audit.json), [historical card](run-card.json), and [repository executive desk](../index.html).
'''
    outputs = {
        OUT / "index.html": page("ATSC archive", index_body, prefix="../"),
        OUT / "executive-summary.html": page("ATSC submission guide", guide_body, prefix="../"),
        OUT / "hypotheses.html": page("ATSC hypotheses", hyp_body, prefix="../"),
        OUT / "EXECUTIVE_SUMMARY.md": md,
        OUT / "README.md": md,
        OUT / "atsc-audit.json": raw_receipt,
        OUT / "current-peer-audit-20261028.json": raw_peer,
        OUT / "run-card.json": raw_card,
    }
    if check_only:
        stale = [str(p.relative_to(ROOT)) for p, content in outputs.items() if not p.is_file() or p.read_text() != content]
        if stale:
            raise ValueError("Stale ATSC archive files: " + ", ".join(stale))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content)
    print("Built the fail-closed ATSC research archive; no competition TIFF was generated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(check_only=parser.parse_args().check)
