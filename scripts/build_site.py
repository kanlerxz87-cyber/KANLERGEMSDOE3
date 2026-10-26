#!/usr/bin/env python3
"""Deterministic static evidence desk built ONLY from checked-in audit receipts.

No training, scraping, score estimation, file promotion or raster download occurs
at build time. An unavailable candidate must never become a download button.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read(path: str):
    return json.loads((ROOT / path).read_text())


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, content: str, active: str = "summary", prefix: str = "") -> str:
    links = [("summary", "index.html", "Executive summary"), ("research", "research.html", "Research"), ("sources", "sources.html", "Evidence"), ("guide", "executive-summary.html", "How to submit")]
    nav = "".join(f'<a href="{prefix}{path}"' + (' aria-current="page"' if key == active else '') + f'>{text}</a>' for key, path, text in links)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Evidence-first DOE GEMS fault discovery. Exact historical files, automated validation and a clear submission decision.">
<title>{esc(title)} · GEMS research desk</title><link rel="stylesheet" href="{prefix}assets/site.css">
<script src="{prefix}assets/site.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="bar">
<a class="brand" href="{prefix}index.html"><span class="mark" aria-hidden="true">G</span><span>GEMS<small>Fault discovery / research desk</small></span></a>
<nav aria-label="Main navigation">{nav}</nav><span class="nav-status">Research blocked</span></div></header>
<main id="main">{content}</main>
<footer class="footer"><div><strong>KANLERGEMSDOE3</strong> · Evidence before promotion<br>Maximize P(Win). Own the outcome. No fabricated scores or renamed submissions.</div>
<div>Reviewed 26 Oct 2026 · <a href="{prefix}run-card.json">Active JSON run card</a><br>Source changes do not authorize an upload. No competition submission is automated.</div></footer></body></html>\n'''


def historical_url(row: dict) -> str:
    return f"https://github.com/buffedlizard55-lab/{row['repo']}/blob/{row['head']}/{row['file']}"


def source_cards(feed: dict) -> str:
    out = []
    for row in feed["rows"]:
        commit = row.get("commit")
        if commit:
            out.append(f'''<article class="source-card" data-source-repo="{esc(row['repository'])}" data-reviewed-sha="{commit}">
<a href="{esc(row['source_url'])}">{esc(row['site'])} ↗</a><code>Reviewed commit {commit[:10]}</code>
<span class="freshness" aria-live="polite">Live source check pending; snapshot retained.</span></article>''')
        else:
            out.append(f'<article class="source-card"><strong>{esc(row["site"])}</strong><span class="freshness unavailable">Refresh failed — source freshness unknown.</span></article>')
    return "".join(out)


def comparison_table(rows: list[dict]) -> str:
    out = []
    for index, row in enumerate(sorted(rows, key=lambda r: -r["owner_reported_leaderboard_score"])):
        top = index == 0
        name = Path(row["file"]).name
        profiles = row["local_validation"]["encoding_profiles"]
        encoding = "finite-grid" if profiles["finite-grid"] else "template-mask" if profiles["template-mask"] else "neither"
        out.append(f'''<tr{' class="history-top"' if top else ''}><td><a class="site-name" href="sites/{row['repo']}.html">{row['repo']} ↗</a>{'<span class="top-label">TOP HISTORICAL CLAIM</span>' if top else ''}</td>
<td><span class="not-approved">None approved</span><details><summary>Historical file · audit only</summary><a href="{esc(historical_url(row))}">{esc(name)}</a><code>SHA-256 {row['sha256']}</code><small>Not a new submission. Do not upload this reference.</small></details></td>
<td><span class="score">{row['owner_reported_leaderboard_score']:.4f}</span><small>Unverified owner report.<br>No score-to-file receipt.</small></td>
<td>Not estimable<small>No validated leaderboard forecast</small></td>
<td><span class="tag negative">Duplicate</span><small>{row['max_overlap_3px']:.2%} maximum directed dot overlap within 3 px</small></td>
<td><span class="tag unknown">{encoding}</span><small>Local encoding check only.<br>Portal acceptance unknown.</small></td>
<td><span class="not-approved">NO</span><small>No slot selected</small></td></tr>''')
    return '''<div class="table-wrap"><table><caption class="skip">Nine priority-site historical reference comparison; none is a submission recommendation.</caption><thead><tr><th scope="col">Site</th><th scope="col">File to download / submit</th><th scope="col">Historical claim</th><th scope="col">Leaderboard estimate</th><th scope="col">Unique?</th><th scope="col">Encoding profile</th><th scope="col">Submit?</th></tr></thead><tbody>''' + "".join(out) + "</tbody></table></div>"


def heatmap(audit: dict) -> str:
    names = [row["repo"] for row in audit["rows"]]
    pairs = {(row["candidate"], row["reference"]): row["overlap_3px"] for row in audit["pairs"]}
    pieces = ['<svg class="heatmap" viewBox="0 0 590 540" role="img" aria-labelledby="heat-title heat-desc"><title id="heat-title">Historical directed dot overlap</title><desc id="heat-desc">Rows are candidate sites, columns are reference sites. All 72 cross-site comparisons exceed the 70 percent duplicate stop. Values are geometric measurements, not scores.</desc>']
    for i, name in enumerate(names):
        short = name.replace("GEMSDOE", "")
        pieces.append(f'<text x="{112+i*50}" y="44" text-anchor="middle">{short}</text><text x="74" y="{81+i*50}" text-anchor="end">{short}</text>')
        for j, reference in enumerate(names):
            value = pairs.get((name, reference))
            fill = "#f0f3ef" if value is None else "#d8e9db" if value < .95 else "#b8d4c0"
            label = "—" if value is None else f"{value:.0%}"
            pieces.append(f'<rect x="{89+j*50}" y="{56+i*50}" width="46" height="46" rx="5" fill="{fill}"/><text class="tiny" x="{112+j*50}" y="{83+i*50}" text-anchor="middle">{label}</text>')
    pieces.append('<text x="310" y="525" text-anchor="middle">Reference site → · candidate rows · ≤3 px, directed</text></svg>')
    return "".join(pieces)


def hypothesis_cards(hypotheses: list[dict], detailed: bool = False) -> str:
    pieces = []
    for row in hypotheses:
        details = f'''<dl><dt>Physical signature</dt><dd>{esc(row['signature'])}</dd><dt>Why missing from the catalogue?</dt><dd>{esc(row['missing_fault_rationale'])}</dd><dt>Difference from prior work</dt><dd>{esc(row['difference'])}</dd><dt>Non-fault mimic</dt><dd>{esc(row['non_fault_mimic'])}</dd><dt>Availability / viability</dt><dd>{esc(row['viability'])} <a href="{esc(row['source'])}">Source ↗</a></dd><dt>Expected DTI improvement</dt><dd>{esc(row['expected_improvement'])}</dd></dl>''' if detailed else f'<p>{esc(row["signature"])}</p><p><strong>Confounder:</strong> {esc(row["non_fault_mimic"])}</p>'
        pieces.append(f'''<article class="hypothesis"><span class="rank" aria-hidden="true">0{row['rank']}</span><h3>{esc(row['name'])}</h3><span class="tag unknown">Untested</span><span class="tag">{esc(row['cost'])} cost</span><p>{esc(row['layers'])}</p>{details}</article>''')
    return '<div class="hypothesis-grid">' + "".join(pieces) + '</div>'


def guide() -> str:
    return '''<div class="page-intro"><p class="eyebrow">Submission guide / automated checks first</p><h1 class="subtitle-page">From an idea to an eligible GeoTIFF.</h1><p>Validation is executed by code, not a human raster inspector. A scientific promotion and permission to spend a weekly slot are separate decisions.</p></div>
<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>Current state: DO NOT SUBMIT</strong><p>No eligible file, unique submission name or competition note exists yet. No download is authorized. The examples below are instructions, not generated submissions.</p></div></div>
<ol class="rule-list">
<li><strong>Restore and audit the pinned inputs.</strong>Run the commands below. This public participant mirror is hash-verified, not organizer-authenticated. Preparation delegates to the shared template and sanitizes raw-band sentinels; it does not generate predictions or privately rebuild the canonical feature stack.<pre>python -m venv .venv
.venv/bin/pip install -r requirements.txt
bash scripts/download_competition_data.sh
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/audit_shared_tools.py
.venv/bin/python scripts/preflight.py</pre>A negative audit/preflight exits nonzero intentionally. Do not override it with a success label.</li>
<li><strong>Establish the assigned lane and trustworthy instruments.</strong>The method paragraph is absent. The shared cache bytes/digest and same-fold incumbent are absent. The shared evaluator has an open <a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41">operator defect</a>. Repair the shared template centrally, pin its corrected commit, and rerun operator tests. Never patch a private scoring fork.</li>
<li><strong>Validate one preregistered geological candidate.</strong>Hide whole fault segments with a buffer. Recompute distance, tip, density, orientation and every other catalogue-derived feature using only visible faults. Mask visible faults pixel-exactly. Run every feature alone as a leakage canary; AUC above 0.90 blocks trust until explained. Canonical hide-and-recover currently takes binary masks; it must not silently evaluate soft probabilities as their nonzero support.</li>
<li><strong>Beat the recorded holdout best before any slot decision.</strong>Use pooled HOLDOUT-DTI, alpha 0.2, beta 0.8 and a 300 m triangular kernel. Save evaluator version, withheld-positive count, 95% spatial-block CI and paired improvement CI on identical folds. Require the lower bound of paired improvement to be positive. A holdout number is not a public leaderboard estimate. Stop after three experiments or two hours.</li>
<li><strong>Check semantic uniqueness twice.</strong>Before writing: compare the continuous surface and explicit preview dots against every registry raster. After writing: repeat on the exact final dots, and bind the report to their hash. Rank correlation above 0.90 or directed dot overlap above 70% within Euclidean 3 px means duplicate: log and stop. A partial registry, a constant/empty comparison or a new filename is not a uniqueness pass.<pre>.venv/bin/python scripts/check_uniqueness.py --help</pre>The current nine historical winners already fail this stop; copying any of them is not an experiment.</li>
<li><strong>Write through the canonical writer, then inspect the saved bytes automatically.</strong>Use the unmodified shared <code>vendor/shared-template/scripts/submission_writer.py</code> only after the research gates pass. Write to ignored <code>data/research/</code>, not the website. Do not pass invalid, NaN or arbitrary soft values and rely on binarization/clipping to repair them. A write receipt is not scientific approval.<pre>.venv/bin/python scripts/validate_submission.py data/core/sample_submission.tif data/research/CANDIDATE.tif --profile finite-grid
.venv/bin/python scripts/validate_submission.py data/core/sample_submission.tif data/research/CANDIDATE.tif --profile template-mask</pre>The reports explicitly separate the two local padding contracts. The official page requires float32, matching grid/bounds and null/NaN outside bounds; do not claim the local whole-grid check overrides it. Resolve the official encoding interpretation before promotion. The validator never repairs a file.</li>
<li><strong>Bind name, note, hash and quality evidence.</strong>The exact output must be single-band float32 on the template's CRS/shape/transform, with no NaN/Inf/nodata inside and values in [0,1]. Record SHA-256 and all automated receipts. A future name may encode project, lane, UTC and content digest; it is not uniqueness evidence. A short note must be at most 140 characters. No real filename or note is offered while no candidate exists.</li>
<li><strong>Let the separate selector authorize a slot.</strong>The <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules, section 3.4</a>, specify up to three submissions per week. The logged-in submission page determines the account's actual remaining cap; it has not been verified here. No slot is selected automatically by this research session.</li>
<li><strong>Only then download and upload the exact approved file.</strong>After evidence-bound promotion, an approved TIFF link must appear at the beginning of the executive summary with its exact hash/name and note. On DrivenData choose Submit → Make new submission, select the single-band TIFF (or the portal-supported single-TIFF ZIP), and paste the saved note. Preserve the resulting submission-page receipt and submitted hash. Only that receipt establishes ORGANIZER-CONFIRMED per-file performance. The site cannot submit under an unauthenticated account.</li>
<li><strong>Preserve reproducibility and required disclosures.</strong>Retain complete code, input provenance, licenses and the winning-model documentation. Official rules section 3.2 requires disclosure of generative-AI assistance. AI was used here for research synthesis, code, tests and documentation; no claim is made of field-confirmed geological discovery.</li></ol>
<section class="panel"><h2>About the range error</h2><p>The rejected upload's bytes were not supplied, so its exact cause is unknown. Possible mechanisms include NaN/Inf, raw feature nodata sentinels, incorrect bands, values below zero or above one, or a padding contract mismatch. Automated validation must inspect the exact saved TIFF, not just the in-memory array. Do not change the file after hashing; a ZIP must contain only the approved TIFF.</p></section>'''


def build() -> None:
    audit = read("docs/audit.json")
    card = read("docs/run-card.json")
    readiness = read("docs/data/readiness.json")
    feed = read("docs/data/focus-feed.json")
    hypotheses = read("research/hypotheses.json")
    official = read("evidence/official-claims-20261026.json")
    # This desk has no release/publisher implementation or eligible artifact.
    # Fail rather than render an optimistic state if somebody edits a card alone.
    if card.get("verdict") != "negative" or card.get("raster_sha256") is not None or readiness.get("submit_ready") is not False:
        raise ValueError("No evidence-bound publisher exists for a positive decision; do not manufacture a download link")
    resolved = "".join(f'<div class="progress-item"><span aria-hidden="true">✓</span><div><strong>{esc(text)}</strong><small>Automated integrity checks; not scientific approval.</small></div></div>' for text in readiness["resolved"])
    blockers = "".join(f'<div class="progress-item"><span aria-hidden="true">—</span><div><strong>{esc(text)}</strong></div></div>' for text in readiness["failures"])
    main = f'''<section class="hero"><div><p class="eyebrow">Executive summary / DOE GEMS</p><h1>Better fault predictions.<br><em>Evidence before a slot.</em></h1><p class="lede">An honest decision desk for the nine priority sites. See exactly what can be downloaded, what has been tested, and what still blocks a genuinely new submission.</p><p class="date">26 October 2026 · Audited evidence, not a score projection</p></div>
<aside class="download-card" aria-label="Submission file status"><p class="eyebrow">Your competition file</p><h2>No eligible TIFF yet.</h2><p>The required scientific and uniqueness gates have not passed. No historical file is being relabelled as new.</p><div class="file-unavailable"><svg width="27" height="32" viewBox="0 0 27 32" fill="none" aria-hidden="true"><path d="M4 1h12l7 7v22H4zM16 1v8h7M9 16h9M9 21h9" stroke="currentColor" stroke-width="1.4"/></svg><div><strong>Download unavailable · DO NOT SUBMIT</strong><small>No placeholder file. No authorized slot.</small></div></div><div class="download-meta"><div><span>Score estimate</span><strong>Not estimable</strong></div><div><span>Unique candidate</span><strong>Not generated</strong></div><div><span>Weekly slots used</span><strong>None this session</strong></div></div></aside></section>
<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — historical winners duplicate; no new candidate qualifies.</strong><p>The historical family fails your literal overlap stop. Core data are now restored, but the assigned lane/cache/incumbent are missing and the shared evaluator needs a central repair. This is a negative research deliverable, not a completed high-scoring model.</p></div></div>
<div class="stats"><article class="stat"><span class="label">Historical uniqueness</span><strong>9 / 9 stopped</strong><small>Geometric audit · not DTI scores</small></article><article class="stat"><span class="label">Data placement</span><strong>Recovered</strong><small>19-band input · pinned participant mirror</small></article><article class="stat"><span class="label">Shared instruments</span><strong>Blocked</strong><small>Source-locked · operator defect reproduced</small></article><article class="stat"><span class="label">Geological experiments</span><strong>0 / 3</strong><small>No lane silently assigned · no slot spent</small></article></div>
<section class="section" id="comparison"><div class="section-heading"><div><p class="eyebrow">Priority portfolio</p><h2>One clear decision for every site.</h2><p>Sorted by historical owner-reported claims, not by a validated score forecast or a recommendation.</p></div><a href="audit.json">Exact hashes &amp; all comparisons ↗</a></div>
{comparison_table(audit['rows'])}<div class="table-note"><span><strong>Claims are quarantined:</strong> no organizer submission-page receipt binds any historical score to a file. No new HOLDOUT-DTI exists.</span><span>Local encoding compatibility ≠ portal acceptance ≠ scientific promotion.</span></div></section>
<section class="section grid-two"><article class="panel"><p class="eyebrow">Understanding the reported 0.2778</p><h2>A stronger emission budget,<br>not proven new geology.</h2><p>H33 B2 on GEMSDOE32 is the highest historical claim in this priority list. Its 37,654 dots have extremely high spatial overlap with the other winners. Sparse thinning may remove uncredited prediction mass without losing much coverage—but it can also increase missed faults.</p><p>The metric offers a plausible efficiency explanation, not a causal proof. Without a score-to-file receipt and paired out-of-fold ablation, a better leaderboard result cannot be promised.</p><a class="link-button" href="research.html#h33">Read the scientific analysis →</a></article><article class="panel"><p class="eyebrow">Why a renamed file is not new</p><h2>The historical family trips the stop.</h2><p>The smallest of all 72 directed cross-winner overlaps is <strong>{min(p['overlap_3px'] for p in audit['pairs']):.2%}</strong>, above the 70% threshold. Compression, filenames and nodata encodings can change the hash while retaining the same predictions.</p><details><summary>View the nine-site geometric overlap matrix</summary>{heatmap(audit)}</details><p class="subtext">Continuous historical surfaces are not available. Their rank correlations are unknown; dot overlap alone is sufficient to reject these references.</p></article></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">This session / actual progress</p><h2>Resolve prerequisites. Don’t invent results.</h2></div><a href="data/readiness.json">Automated preflight ↗</a></div><div class="grid-two"><article class="panel"><h3>Recovered and verified</h3>{resolved}<p><a href="sources.html#data">Core grid, raw-band and sentinel audit →</a></p></article><article class="panel"><h3>Still blocking research</h3>{blockers}<p><a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41">Shared-template defect: existing upstream issue #41 ↗</a></p></article></div></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">Scientific queue / before implementation</p><h2>Four hypotheses. No performance claims.</h2><p>Qualitative improvement potential and cost; none is an assigned lane or a validated discovery.</p></div><a href="research.html">Mechanisms, layers &amp; viability →</a></div>{hypothesis_cards(hypotheses)}</section>
<section class="section" id="feed"><div class="section-heading"><div><p class="eyebrow">Source-change feed</p><h2>Current sources, separate from approval.</h2><p>Pinned participant repositories checked {esc(feed['checked_utc'])}. Browser checks only detect later source commits—not scores, reviews or permission.</p></div><button class="refresh-button" type="button" id="refresh-sources">Check source changes</button></div>{'<div class="source-grid">'+source_cards(feed)+'</div>'}<p class="subtext" id="feed-summary" aria-live="polite">Automatic source checks are read-only. Failed API access is shown as unknown; this reviewed snapshot is retained.</p></section>
<section class="evidence-strip"><div><h3>A valid raster is necessary. It is not enough.</h3><p>The published format, two explicit local encoding profiles, holdout evidence, semantic novelty and slot authorization are separate checks. The earlier blanket rejection of zero-outside files is withdrawn; no portal acceptance is claimed.</p></div><a class="link-button" href="executive-summary.html">How to make a submission →</a></section>'''
    (DOCS / "index.html").write_text(page("Executive summary", main))
    for path in ("executive-summary.html", "submission.html"):
        (DOCS / path).write_text(page("How to submit", guide(), "guide"))
    research = f'''<div class="page-intro"><p class="eyebrow">Scientific research / preregistered proposals</p><h1 class="subtitle-page">Contrarian mechanisms.<br>Conservative evidence.</h1><p>The competition predicts previously unmapped faults, not directly geothermal vents. Geological plausibility is a hypothesis; only a leakage-safe, paired experiment can establish holdout improvement.</p></div><div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>No method lane was supplied. No geological experiment was run.</strong><p>These proposals were recorded before method implementation. “Untested” does not mean globally novel. New-data variants are not viable until the official bytes and required coverage are obtainable.</p></div></div>
{hypothesis_cards(hypotheses, detailed=True)}
<section class="section panel prose" id="h33"><p class="eyebrow">H33 B2 / mechanism vs inference</p><h2>Why thinning can help—and why that is not a forecast.</h2><p>The official DTI credits a ground-truth pixel with its best nearby prediction, not the sum of every nearby dot. Redundant dots can add false-positive mass without improving coverage. Removing those dots can improve emission efficiency; removing the wrong dots loses recall. H33’s historical geometry strongly overlaps the other high-claim entries, so its reported result does not isolate a new geological signal.</p><p>The triangular kernel has zero credit exactly at 300 m. At alpha 0.2 and beta 0.8, missed faults are penalized more heavily than false positives. It is therefore wrong to infer that sparser is always better, or that one fixed dot count should be copied across geological settings.</p><p>Staff clarify that existing catalogue pixels are excluded in both rounds. A fold-local catalogue mask must exclude only visible faults, not withheld positives. A final submission already zeroed with the complete catalogue cannot stand in for an honest hide-and-recover prediction.</p><div class="score-disclaimer">Historical 0.2778 is an unverified owner report. No organizer receipt binds it to a hash, and no paired causal ablation is available. No leaderboard estimate is emitted.</div><a href="review.md">Full scientific review, uncertainty and next steps →</a></section>
<section class="section panel prose"><h2>What could mimic the signal?</h2><p>USGS describe GeoDAWN radiometrics as surface geology/soil information and magnetics as subsurface structure/geology information. Variable terrain clearance, flight geometry and levelling can create persistent line-like signatures. Lithologic contacts may explain cross-layer edges without a fault; stream capture can explain apparent drainage offsets; groundwater transport and seasonal sampling can explain thermal residuals.</p><p>Even a correct mapped-fault holdout has population shift: mapped/exposed faults are not necessarily representative of concealed expert-labeled faults. AUC below the canary threshold does not prove that feature lineage is leak-free. A passing format validator says nothing about those scientific issues.</p><p><a href="sources.html">Verified source excerpts and what they actually establish →</a></p></section>'''
    (DOCS / "research.html").write_text(page("Research queue", research, "research"))
    source_rows = []
    for claim in official["claims"]:
        quotes = claim.get("quotes", [claim["quote"]] if "quote" in claim else [])
        quotation = "".join(f'<blockquote>{esc(quote)}</blockquote>' for quote in quotes)
        source_rows.append(f'<tr><td><strong>{esc(claim["id"])}</strong></td><td>{esc(claim["claim"])}{quotation}</td><td><a href="{esc(claim["source"])}">Official source ↗</a><small>{esc(claim.get("verified_scope", claim.get("binary_obtainability", "See source record for limits.")))}</small></td></tr>')
    data = read("evidence/input-integrity.json")
    sources = f'''<div class="page-intro"><p class="eyebrow">Evidence / provenance and limitations</p><h1 class="subtitle-page">Know what each source proves.</h1><p>Official task pages define rules and physics context. Participant mirrors prove only hash consistency. A public leaderboard observation is not a submission-page receipt tied to our raster. Hypotheses and operator tests are separate from measured geological performance.</p></div>
<section class="panel prose"><h2>Current official observations</h2><p>The official public leaderboard fetched on 26 October displays xiaofanhu first with <strong>0.4437</strong>. This is an official-page observation, not an accepted per-file score receipt and not a forecast. The conflicting “current” figures in the prompt should not be optimized against as verified thresholds.</p><p>The official rules specify up to three submissions per week. The account’s actual remaining allowance is unknown; no slot is authorized. The official data page still redirects an unauthenticated request to login.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Review the live official leaderboard ↗</a></p></section>
<section class="section" id="data"><div class="section-heading"><div><p class="eyebrow">Data-placement blocker / removed</p><h2>Core bytes restored. Provenance kept explicit.</h2></div></div><div class="grid-two"><article class="panel"><dl class="key-value"><dt>Grid</dt><dd>EPSG:{data['grid']['epsg']} · {data['grid']['height']} × {data['grid']['width']} · 100 m</dd><dt>Raw features</dt><dd>19 bands, restored from immutable participant mirrors</dd><dt>Footprint pixels</dt><dd>{data['counts']['footprint_valid_pixels']:,}</dd><dt>Catalogue positives</dt><dd>{data['counts']['positive_catalogue_label_pixels']:,}</dd><dt>Sentinel-affected pixels</dt><dd>{data['counts']['unique_footprint_pixels_with_any_sentinel']:,} unique footprint pixels; {data['counts']['total_sentinel_band_pixels_inside_footprint']:,} summed across bands</dd><dt>Derived cache</dt><dd>Not obtained; not privately regenerated</dd><dt>Organizer authentication</dt><dd>Not established by the mirror hashes</dd></dl></article><article class="panel"><h3>Shared tool audit</h3><p>The source-locked evaluator drops pooled false-positive mass from an empty-truth cell. A synthetic operator test reproduces the defect, without evaluating a geological candidate. This does not show that any historical competition score was affected.</p><p>The tool also binarizes nonzero soft inputs. It cannot be trusted as a probability evaluator merely because it accepts a float array.</p><p><a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41">Existing central repair issue ↗</a> · <a href="tool-audit.json">Synthetic operator receipt ↗</a></p></article></div></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">Claim-by-claim source ledger</p><h2>Verified excerpts. Bounded conclusions.</h2><p>Transcribed excerpts from fetched pages; not hashes of the original HTML/PDF bytes. Full source retrieval or a resource index is not proof that every linked dataset was downloaded.</p></div><a href="official-claims.json">Machine-readable ledger ↗</a></div><div class="table-wrap"><table class="source-table"><thead><tr><th>Claim</th><th>Observation / exact excerpt</th><th>Source and verification scope</th></tr></thead><tbody>{''.join(source_rows)}</tbody></table></div></section>'''
    (DOCS / "sources.html").write_text(page("Evidence ledger", sources, "sources"))
    (DOCS / "sites").mkdir(exist_ok=True)
    current = {row["site"]: row for row in feed["rows"]}
    for row in audit["rows"]:
        other = sorted((pair for pair in audit["pairs"] if pair["candidate"] == row["repo"]), key=lambda x: -x["overlap_3px"])
        profiles = row["local_validation"]["encoding_profiles"]
        peer_list = "".join(f'<li>{pair["reference"]}: {pair["overlap_3px"]:.4%} directed overlap within 3 px</li>' for pair in other)
        now = current[row["repo"]]
        text = f'''<p class="breadcrumb"><a href="../index.html#comparison">← Priority-site comparison</a></p><div class="page-intro"><p class="eyebrow">Individual executive summary / {row['repo']}</p><h1 class="subtitle-page">Historical evidence.<br>No eligible new download.</h1><p>Best supplied historical claim: <strong>{row['owner_reported_leaderboard_score']:.4f}</strong>, owner-reported without a submission-page receipt. It is not an approved recommendation or an estimate for a new file.</p></div><div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — duplicate under your protocol.</strong><p>No new unique TIFF is available for this site. The historical reference exceeds the 70% directed overlap stop against priority peers. Estimated leaderboard score: not estimable. No slot selected.</p></div></div>
<div class="grid-two"><section class="panel"><h2>Exact historical file</h2><p><a href="{esc(historical_url(row))}">{esc(Path(row['file']).name)}</a></p><p>Forensic reference only; not a new competition download.</p><dl class="key-value"><dt>File SHA-256</dt><dd><code>{row['sha256']}</code></dd><dt>Source commit</dt><dd><code>{row['head']}</code></dd><dt>Positive dots</dt><dd>{row['dots']:,} · geometric audit</dd><dt>Template-mask profile</dt><dd>{'PASS' if profiles['template-mask'] else 'FAIL'} · local contract only</dd><dt>Finite-grid profile</dt><dd>{'PASS' if profiles['finite-grid'] else 'FAIL'} · local contract only</dd><dt>Portal acceptance</dt><dd>Unknown; local checks are not a receipt</dd><dt>New file / estimate</dt><dd>None / not estimable</dd></dl></section><section class="panel"><h2>Semantic-uniqueness result</h2><span class="tag negative">Stop duplicate</span><p>Comparison is candidate-to-reference, not a symmetric similarity. Dot hashes alone cannot establish novelty. Historical continuous-surface correlation is not measured.</p><ul>{peer_list}</ul></section></div>
<section class="section panel"><h2>Current source snapshot</h2><p>The historical file above is pinned independently from the newer homepage. Homepage statements are participant claims, not this project’s selector decision.</p><p><a href="{esc(now.get('source_url','../sources.html'))}">Reviewed participant page at {esc(str(now.get('commit') or 'unknown')[:10])} ↗</a></p><p><a href="../research.html">Shared-family performance interpretation and conditional research queue →</a></p></section>'''
        (DOCS / "sites" / f"{row['repo']}.html").write_text(page(row["repo"] + " executive summary", text, prefix="../"))
    for source, dest in [("evidence/official-claims-20261026.json", "official-claims.json"), ("evidence/shared_tool_audit.json", "tool-audit.json"), ("evidence/input-integrity.json", "input-integrity.json")]:
        shutil.copyfile(ROOT / source, DOCS / dest)
    for name in ("review", "hypotheses"):
        (DOCS / f"{name}.md").write_text((ROOT / "research" / f"{name}.md").read_text())


if __name__ == "__main__":
    build()
