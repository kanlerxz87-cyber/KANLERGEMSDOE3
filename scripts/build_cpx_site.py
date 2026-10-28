#!/usr/bin/env python3
"""Build the isolated L-K3-CPX-EDTI portal under docs/cpx-edti/ from evidence only.

Fail-closed: refuses to render if the saved TIFF hash differs from the run card,
if any evidence file is missing, or if the verdict fields are malformed.
No score is computed or estimated here.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "docs/cpx-edti"


def load(p: str):
    return json.loads((ROOT / p).read_text())


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


CSS = """
:root{--bg:#f4f7f9;--surface:#fff;--border:#d8e1e8;--text:#0f172a;--muted:#475569;
--accent:#0f766e;--red:#b91c1c;--redbg:#fef2f2;--amber:#92400e;--amberbg:#fffbeb;
--greenbg:#ecfdf5;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
--sans:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);line-height:1.55}
.container{max-width:1240px;margin:0 auto;padding:26px 20px 60px}
nav{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 18px;margin-bottom:18px}
nav a{color:var(--accent);text-decoration:none;font-weight:600;margin-right:14px}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 22px;margin-bottom:18px}
.banner{border-radius:12px;padding:22px;margin-bottom:18px;border:2px solid var(--red);background:var(--redbg)}
.banner h1{margin:0 0 6px;font-size:1.7rem;color:var(--red)}
table{width:100%;border-collapse:collapse;font-size:.92rem}th,td{border-bottom:1px solid var(--border);padding:8px 10px;text-align:left;vertical-align:top}
th{background:#f8fafc}code{font-family:var(--mono);font-size:.82rem;word-break:break-all}
.tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.78rem;font-weight:700}
.no{background:var(--redbg);color:var(--red);border:1px solid var(--red)}
.ok{background:var(--greenbg);color:#065f46;border:1px solid #10b981}
.warn{background:var(--amberbg);color:var(--amber);border:1px solid #f59e0b}
small{color:var(--muted)}.wrap{overflow-x:auto}a{color:var(--accent)}
.btn{display:inline-block;background:var(--accent);color:#fff!important;padding:9px 16px;border-radius:8px;text-decoration:none;font-weight:700;margin:4px 6px 4px 0}
.btn.ghost{background:#fff;color:var(--accent)!important;border:1px solid var(--accent)}
h2{margin-top:0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
"""


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · L-K3-CPX-EDTI</title><style>{CSS}</style></head>
<body><div class="container">
<nav><div><strong>KANLERGEMSDOE3</strong> · L-K3-CPX-EDTI</div>
<div><a href="index.html">Executive summary</a><a href="hypotheses.html">Hypotheses</a><a href="submission-guide.html">How to submit</a><a href="../index.html">Main research desk</a></div></nav>
{body}
<footer><small>Maximize P(Win) · Own the Outcome · Every number labels its evidence class
(HOLDOUT-DTI / OWNER-REPORTED / GEOMETRY / ALGEBRA). No leaderboard projection is a score.
Run card: <a href="run-card.json">run-card.json</a></small></footer>
</div></body></html>
"""


def fmt(x, nd=4):
    return f"{float(x):.{nd}f}"


def main() -> int:
    card = load("evidence/cpx-run-card.json")
    hold = load("evidence/cpx_holdout_20261028.json")
    canary = load("evidence/cpx_leakage_canary_20261028.json")
    uniq = load("evidence/cpx_uniqueness_20261028.json")
    forensics = load("evidence/cpx_forensics_20261028.json")
    hyps = load("evidence/cpx_hypotheses_20261028.json")
    winners = load("sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json")["historical_winners"]
    audit = uniq["audit"]
    assert card["verdict"] in ("promote", "negative")
    zfile = card["submission_file_zeros"]
    zpath = PORTAL / "downloads" / zfile
    assert sha(zpath) == card["raster_sha256"], "TIFF hash != run card"
    assert card["note_characters"] <= 140
    e2 = hold["summaries"]["Exp-CPX-2"]
    verdict = card["verdict"]
    banner_cls = "banner" if verdict == "negative" else "panel"
    decision = ("DO NOT SUBMIT — yet" if verdict == "negative" else "PROMOTE (selector still required)")
    det_by_id = {r["id"]: r for r in audit["detector_comparisons"]}

    # ---- decision table rows ----
    rows = []
    rows.append(f"""<tr><td><strong>NEW — this lane (L-K3-CPX-EDTI)</strong><br>
<a href="downloads/{esc(zfile)}">{esc(zfile)}</a> (research TIFF)<br><code>SHA-256 {card['raster_sha256']}</code></td>
<td><strong>{fmt(e2['dti'],4)}</strong> HOLDOUT-DTI [{fmt(e2['ci95']['interval'][0])}, {fmt(e2['ci95']['interval'][1])}]<br>
<small>gems-segment-pooled-v1 · {int(e2['n_truth']):,} withheld px · NOT a leaderboard estimate (none exists — see §Why)</small></td>
<td><span class="tag ok">YES vs genuine detectors</span><br><small>max 3-px overlap {audit['final_dots']['genuine_detectors_max_candidate_fraction_within_3px']:.1%} ≤ 70%, |ρ|max {audit['final_dots']['genuine_detectors_max_abs_spearman_rho']:.3f} ≤ 0.90 across {audit['genuine_detector_rasters_checked']} genuine rasters; 37.5–42.2% vs each focus-9 winner. Literal rule incl. calibration lattice: mathematically impossible at this budget (≥82.34% for any file).</small></td>
<td>{'—' if verdict=='negative' else '—'}</td>
<td><span class="tag no">{decision}</span><br><small>Failed preregistered holdout gates (below). Download is for research/audit only.</small></td></tr>""")

    atsc = load("evidence/atsc-submod-run-card.json")
    atsc_ov = atsc["uniqueness_registry_summary"]["genuine_final_dot_overlap_3px"]
    rows.append(f"""<tr><td><strong>Repo holdout incumbent — ATSC (prior lane)</strong><br>
<a href="../atsc-submod/index.html">kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros.tif</a><br>
<code>SHA-256 bf21ac69a0e5e6325d9725e7188be210a24b2e68b68060574db56af0d5972566</code></td>
<td><strong>{fmt(atsc['holdout']['value'],4)}</strong> HOLDOUT-DTI [{fmt(atsc['holdout']['ci95'][0])}, {fmt(atsc['holdout']['ci95'][1])}]<br>
<small>Same evaluator/split (recorded, not rerun this session). Best HOLDOUT-DTI in repo. NOT a leaderboard estimate.</small></td>
<td><span class="tag ok">YES vs genuine detectors</span><br><small>{atsc_ov:.1%} max final 3-px overlap across its 87-detector audit; same lattice impossibility.</small></td><td>—</td>
<td><span class="tag warn">NEAREST TO READY — selector decision required</span><br><small>Its own card holds verdict negative on literal-lattice + provenance items. If a selector accepts the genuine-detector scope, this is the rational single slot candidate. Check weekly cap first.</small></td></tr>""")

    fam = {
        "GEMSDOE24": "Dotted H19-5 ridge, d=1.5 spacing",
        "GEMSDOE25": "Dotted H19-5 ridge, d=2.8 (mask = GEMSDOE30)",
        "GEMSDOE27": "DEM topo gap-closure on the d=1.5 dotted base",
        "GEMSDOE28": "Rung-30 blind dotted family (solo/prethin/euler variants 0.2649–0.2710)",
        "GEMSDOE30": "Poisson 300 m off-catalogue thinning of D28 surface",
        "GEMSDOE31": "Solo D28 dotted (H27-4)",
        "GEMSDOE32": "H33 B2 = GEMSDOE30 mask minus 6,436 dots ≤2 px of catalogue",
        "GEMSDOE33": "Analogue tip/stepover dotted (r30)",
        "GEMSDOE36": "Andersonian geothermal PINN dotted, 38,854 dots",
    }
    focus_static = forensics["focus9_static"]
    site_rows = []
    for w in sorted(winners, key=lambda r: -r["owner_reported_leaderboard_score"]):
        repo = w["repo"]
        st = focus_static[repo]
        cand_ov = det_by_id.get(f"registry:{repo}", {}).get("final_3px_overlap")
        rows.append(f"""<tr><td><strong>{repo}</strong> — historical winner<br><small>{esc(Path(w['file']).name)}</small><br><code>SHA-256 {w['sha256'][:16]}…</code></td>
<td><strong>{fmt(w['owner_reported_leaderboard_score'],4)}</strong> OWNER-REPORTED<br><small>No submission-page receipt; not a forecast for any new file.</small></td>
<td><span class="tag no">NO — one geometric family</span><br><small>GEMSDOE32 dots are 99.9–100% within 3 px of every other winner; new CPX file is {cand_ov:.1%} vs this one.</small></td>
<td><small>{esc(fam[repo])}</small></td>
<td><span class="tag no">DO NOT RESUBMIT</span><br><small>Already submitted historically; re-upload duplicates the family.</small></td></tr>""")
        site_rows.append(f"""<article class="panel"><h3>{repo} — {fmt(w['owner_reported_leaderboard_score'],4)} <small>OWNER-REPORTED</small></h3>
<p><strong>Family (from filename/owner pages; implementation not re-audited):</strong> {esc(fam[repo])}.</p>
<p><strong>Measured here (GEOMETRY):</strong> {st['dots']:,} dots · {st['on_catalogue']} on catalogue ·
{st['frac_within_2px_catalogue']:.1%} within 2 px of catalogue · median catalogue distance {st['median_dist_to_catalogue_px']:.1f} px ·
PROXY-DTI vs SGMC off-catalogue faults {fmt(st['proxy_dti_vs_sgmc_off'])} (proxy does not rank LB winners).</p>
<p><strong>Vs new CPX candidate:</strong> {cand_ov:.1%} of CPX dots within 3 px (≤70% = unique) ·
<strong>Verdict:</strong> historical reference only — do not resubmit.</p>
<p><small>Site: <a href="https://buffedlizard55-lab.github.io/{repo}/">buffedlizard55-lab.github.io/{repo}</a> ·
bytes pinned at commit <code>{w['head'][:10]}</code></small></p></article>""")

    sums = hold["summaries"]
    series_rows = "".join(
        f"<tr><td>{k}</td><td>{fmt(v['dti'],4)}</td><td>[{fmt(v['ci95']['interval'][0])}, {fmt(v['ci95']['interval'][1])}]</td></tr>"
        for k, v in sums.items() if not k.startswith("static_"))
    paired = hold["paired"]
    g = card["scientific_gates"]
    gate_rows = "".join(
        f"<tr><td>{esc(k)}</td><td><span class='tag {'ok' if v else 'no'}'>{'PASS' if v else 'FAIL'}</span></td></tr>"
        for k, v in g.items())
    whole = card["whole_array_scan_zeros_tif"]

    index = f"""
<div class="{banner_cls}"><h1>{'⛔ ' if verdict=='negative' else ''}{decision}</h1>
<p><strong>Obvious answer first:</strong> the new unique TIFF from this session's lane
(<code>{esc(zfile)}</code>) is a <strong>research deliverable, not an approved submission</strong> —
it failed its preregistered holdout gates. <strong>No file in this repo currently clears every gate.</strong>
The nearest-to-ready file is the prior ATSC lane (table below); spending a real weekly slot on it is a
<strong>separate selector decision</strong> requiring acceptance of the genuine-detector uniqueness scope
(the literal lattice rule is mathematically unsatisfiable) and a weekly-cap check. This session spent no slot.</p>
<p><a class="btn ghost" href="downloads/{esc(zfile)}">⬇ Download CPX research TIFF (-zeros, portal-safe encoding)</a>
<a class="btn ghost" href="downloads/{esc(zfile.replace('.tif','.zip'))}">⬇ ZIP twin</a>
<a class="btn ghost" href="run-card.json">Run card (JSON)</a></p>
<p><small>SHA-256 <code>{card['raster_sha256']}</code> · 37,654 dots · whole-array scan: {whole['cells']:,} cells,
all finite, min {whole['min']} / max {whole['max']} — the portal error
“Predicted values must be in range [0, 1]” cannot trigger on this file's values.
Paste-ready note ({card['note_characters']} chars): <code>{esc(card['submission_note'])}</code></small></p></div>

<section class="panel"><h2>Decision table — what to download, estimated score, uniqueness</h2>
<p><small>“Estimated score” is shown only with its evidence class. <strong>No defensible numeric leaderboard
forecast exists for any new file</strong>: catalogue-recovery HOLDOUT-DTI measures a different population than the
leaderboard (the verified 0.2778 file scores 0.0067 on it). Historical values are OWNER-REPORTED without receipts.</small></p>
<div class="wrap"><table><thead><tr><th>File to download</th><th>Estimated score (labelled)</th><th>Unique?</th><th>Method family</th><th>Submit?</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></section>

<section class="panel"><h2>Why did 0.2778 win — and can it be beaten? (short answer)</h2>
<p>GEMSDOE32's file is <strong>pixel-identical to GEMSDOE30/GEMSDOE25's 44,090-dot mask after deleting the
6,436 dots within 200 m of mapped faults</strong> — zero dots added (GEOMETRY, replicated this session).
DTI algebra on the two owner-reported scores bounds the deleted dots' lost true-positive credit at
≤ ~2% of TP<sub>w</sub> while ~4.5–6.4k of false-positive mass was removed: <strong>pure denominator
discipline raised the score</strong>. The hidden faults are therefore a genuinely off-catalogue population;
near-catalogue dots are wasted budget. Beating 0.2778 requires a better <em>off-catalogue ranking surface</em>
at the same dotted emission discipline — not more catalogue recovery. Full analysis:
<a href="why-02778.md">why-02778.md</a> · <a href="../research/why-02778.md">prior desk note</a>.</p></section>

<section class="panel"><h2>This lane's holdout results (HOLDOUT-DTI, gems-segment-pooled-v1, 60,988 withheld px)</h2>
<div class="wrap"><table><thead><tr><th>Series</th><th>Pooled DTI</th><th>95% CI (10 km block bootstrap)</th></tr></thead><tbody>{series_rows}</tbody></table></div>
<p><small>Paired: Exp-CPX-2 vs B0 Δ {fmt(paired['Exp-CPX-2_vs_B0']['paired_delta_dti'])} CI [{fmt(paired['Exp-CPX-2_vs_B0']['paired_delta_ci95'][0])}, {fmt(paired['Exp-CPX-2_vs_B0']['paired_delta_ci95'][1])}] (includes 0) ·
vs Exp-CPX-1 Δ {fmt(paired['Exp-CPX-2_vs_Exp-CPX-1']['paired_delta_dti'])} (emission lost to spacing CELF) ·
vs Exp-CPX-3 Δ {fmt(paired['Exp-CPX-2_vs_Exp-CPX-3']['paired_delta_dti'])} (physics fusion hurt catalogue recovery).
Recorded repo best: ATSC 0.1637. Static historical dots on the same folds (leaky benchmarks, not lanes):
GEMSDOE30 {fmt(sums['static_GEMSDOE30_D28']['dti'])} · GEMSDOE32 {fmt(sums['static_GEMSDOE32_H33B2']['dti'])}.
Leakage canary: {canary['n_features']} features, max AUC {fmt(canary['max_two_polarity_auc'])} ≤ 0.90 — PASS.</small></p></section>

<section class="panel"><h2>Preregistered gates for the CPX candidate</h2>
<div class="wrap"><table><tbody>{gate_rows}</tbody></table></div>
<p><small>Preregistration SHA-256 <code>{card['preregistration_sha256']}</code> (written before any holdout run).
Schema gate (promotion_gate.py, verbatim): <code>{esc(json.dumps(card['promotion_gate_schema_assessment']['failures']))}</code> —
includes unverifiable-by-design items (mirror provenance, portal contract) that apply equally to every historical file.
What would flip the decision: a preregistered lane that (1) beats 0.1637 HOLDOUT-DTI paired on identical folds,
(2) keeps genuine-detector uniqueness, (3) is selected by a human selector after checking the weekly cap.</small></p></section>

<section><h2 style="padding:0 4px">Executive summary per priority site</h2><div class="grid">{''.join(site_rows)}</div></section>
"""

    hyp_cards = "".join(f"""<article class="panel"><h3>#{h['rank']} {esc(h['id'])} — {esc(h['name'])}</h3>
<p><span class="tag {'ok' if h['rank']==1 else 'warn'}">{esc(h['status'])}</span> <small>Cost: {esc(h['cost'])} · External data: {esc(h['external_data_needed'])}</small></p>
<p><strong>Layers:</strong> {esc(h['layers'])}<br><strong>Signature:</strong> {esc(h['signature'])}<br>
<strong>Why off-catalogue:</strong> {esc(h['why_off_catalogue'])}<br><strong>Difference:</strong> {esc(h['difference'])}<br>
<strong>Non-fault mimic:</strong> {esc(h['mimic'])}</p></article>""" for h in hyps["hypotheses"])
    hypotheses = f"""<section class="panel"><h1>Candidate hypotheses (ranked before implementation)</h1>
<p><small>{esc(hyps['note'])}</small></p></section>{hyp_cards}"""

    guide = f"""<section class="panel"><h1>How to make a submission (executive guide)</h1>
<p><span class="tag no">CURRENT DECISION: {decision}</span> &nbsp;<small>Do not upload the CPX research TIFF.
The steps below are the exact, validated path to use <em>once a selector approves a file and a weekly slot</em>.</small></p>
<h2>1 · Pick the approved file and verify its bytes</h2>
<ol><li>Download the selector-approved <code>-zeros.tif</code> (or its <code>.zip</code>) from this portal.</li>
<li>Verify SHA-256 matches the run card before uploading:
<code>sha256sum {esc(zfile)}</code> → for the CPX research file: <code>{card['raster_sha256']}</code>.</li>
<li>Local re-validation (optional, writer already checked saved bytes):
<code>python scripts/validate_submission.py &lt;sample_submission.tif&gt; &lt;file.tif&gt; --profile finite-grid</code>.</li></ol>
<h2>2 · Why you will not see “Predicted values must be in range [0, 1]”</h2>
<p>That portal error fires when a whole-array scan finds NaN, nodata sentinels, or values outside [0,1].
The <code>-zeros</code> encoding writes <strong>finite values in [0,1] in every one of the 12,279,160 cells</strong>
(0 outside the study footprint, verified on saved bytes: min {whole['min']}, max {whole['max']}, 0 NaN).
A <code>-nan</code> twin (NaN outside footprint, matching the literal sample) is shipped alongside.
Upload <strong>one</strong> of them — the <code>-zeros</code> file is the primary deliverable; both contain identical predictions inside the footprint.</p>
<h2>3 · Upload on DrivenData</h2>
<ol><li>Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a>, sign in, check your remaining weekly submissions (rules: 3/week — verify live).</li>
<li><strong>Submit → Make new submission</strong>. Choose the single <code>.tif</code> (or a <code>.zip</code> containing exactly one GeoTIFF — both provided).</li>
<li>Paste the run-card note into <strong>Note</strong> (≤140 chars). For CPX: <code>{esc(card['submission_note'])}</code></li>
<li>Submit, then <strong>record the organizer receipt and bind it to the file SHA-256</strong> — only that receipt creates an ORGANIZER-CONFIRMED score.</li></ol>
<h2>4 · Format contract (validated locally; portal acceptance still only proven by a receipt)</h2>
<p><small>Single-band float32 GeoTIFF · EPSG:32611 · shape 3730×3292 · transform identical to sample (100 m px, origin 243350 / 4508550) ·
predictions finite in [0,1] inside footprint · unique filename per content hash. Sources:
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a> ·
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules PDF</a> ·
<a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a>.</small></p></section>"""

    PORTAL.mkdir(parents=True, exist_ok=True)
    (PORTAL / "index.html").write_text(page("Executive summary", index))
    (PORTAL / "executive-summary.html").write_text(page("Executive summary", index))
    (PORTAL / "hypotheses.html").write_text(page("Hypotheses", hypotheses))
    (PORTAL / "submission-guide.html").write_text(page("How to submit", guide))
    (PORTAL / "why-02778.md").write_text((ROOT / "research/cpx_why_02778_20261028.md").read_text())
    (PORTAL / "run-card.json").write_text((ROOT / "evidence/cpx-run-card.json").read_text())
    md = f"""# L-K3-CPX-EDTI — Executive summary (2026-10-28)

**Decision: {decision}.** New unique research TIFF
`downloads/{zfile}` (SHA-256 `{card['raster_sha256']}`, 37,654 dots,
whole array finite in [0,1]) scored **{fmt(e2['dti'],4)} HOLDOUT-DTI**
[{fmt(e2['ci95']['interval'][0])}, {fmt(e2['ci95']['interval'][1])}]
(gems-segment-pooled-v1, {int(e2['n_truth'])} withheld px) — below the recorded repo best
ATSC 0.1637 and failing its preregistered paired/mechanism gates, so it must not spend a
competition slot. It **is** unique vs all {audit['genuine_detector_rasters_checked']} genuine
registry detectors (max final 3-px overlap
{audit['final_dots']['genuine_detectors_max_candidate_fraction_within_3px']:.1%});
the literal rule against the calibration lattice is unsatisfiable for any file at this
budget (counting proof in run card). No leaderboard estimate exists or is claimed.
Full tables: index.html · Science: why-02778.md · Steps: submission-guide.html ·
Machine record: run-card.json.
"""
    (PORTAL / "EXECUTIVE_SUMMARY.md").write_text(md)
    (PORTAL / "README.md").write_text(md)
    print(f"[cpx-site] wrote portal pages; verdict={verdict}; file={zfile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
