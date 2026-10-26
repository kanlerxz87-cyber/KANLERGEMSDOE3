"""Render the active evidence-led static site from committed, checked receipts.

No fetching, model fitting, upload, or score inference is performed by this build.
Integrates both the KANLER-H1 (DCAP-LHC) 37,654-dot research deliverable and all
preserved parallel session receipts (`evidence/run-card.json`, `evidence/run_card.json`,
`evidence/registry_saturation_20261026.json`).
"""
from pathlib import Path
import argparse
import hashlib
import json
from html import escape as e

import markdown
try:
    from .check_run import check
    from .check_parallel_audit import check as check_parallel
except ImportError:  # python scripts/build_site.py
    from check_run import check
    from check_parallel_audit import check as check_parallel

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs'


def layout(title, body):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | GEMS Evidence Lab</title><meta name="description" content="Evidence-led fault mapping research and submission readiness.">
<link rel="stylesheet" href="experiment.css"></head><body>
<header class="top"><div class="wrap top-inner"><a class="brand" href="index.html"><span class="mark">G</span><span><strong>GEMS</strong><small>Evidence lab / KANLERGEMSDOE3</small></span></a>
<nav aria-label="Main navigation"><a href="index.html#kanler-h1">KANLER-H1</a><a href="index.html#results">Experiments</a><a href="index.html#comparison">Site comparison</a><a href="index.html#sources">Sources</a><a class="nav-cta" href="executive-summary.html">Submission guide ↗</a></nav></div></header>
<main>{body}</main><footer><div class="wrap"><span>GEMS Evidence Lab &nbsp; / &nbsp; Maximize P(Win) · Own the Outcome</span><span>Research snapshot · No competition slot spent</span></div></footer>
<script src="source-status.js" defer></script></body></html>'''


def render_markdown(source):
    """Render trusted project Markdown with local, published evidence links."""
    text = source.read_text(encoding='utf-8')
    substitutions = {
        '../evidence/registry_saturation_20261026.json': 'data/registry_saturation.json',
        '../evidence/feature_cache_recovery_20261026.json': 'data/feature_cache_recovery.json',
        '../evidence/run-card.json': 'run-card.json',
        '../evidence/parallel-lattice-audit.json': 'parallel-lattice-audit.json',
        '../registry/shared_template_pins.json': 'data/shared_template_pins.json',
        '../docs/audit.json': 'audit.json',
        '../archive/recovery/concurrent-main-research-review.md': 'https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/archive/recovery/concurrent-main-research-review.md',
        '](preregistration.md)': '](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/research/preregistration.md)',
        '](review.md)': '](research.html)',
        '](hypotheses.md)': '](hypotheses.html)',
        '](SOURCES.md)': '](sources.html)',
        '](SUBMISSION_GUIDE.md)': '](executive-summary.html)',
    }
    for old, new in substitutions.items():
        text = text.replace(old, new)
    rendered = markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists'])
    rendered = rendered.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')
    return f'<div class="wrap"><article class="panel panel-pad markdown-page">{rendered}</article></div>'


def check_saturation(saturation, registry_bytes):
    """Check the pinned evidence identity and invariant, not a geological result."""
    registry_sha = 'e1f10c7bf4c0b9c61a427a6106a0073ca2ea449f6d30b2b787931fbda2d2e104'
    witness_sha = '975c217ef803a45041077a219ba460134a8c84c8ea9f7ffc0414ddb47cb54ccd'
    measurement = saturation['measurement']
    registry = json.loads(registry_bytes)
    matches = [r for r in registry['rasters'] if r.get('repo') == 'GEMSDOE48'
               and r.get('ref') == '268ec599f51c517cc3485da077c24d83af5be81d'
               and r.get('path') == 'docs/downloads/GEMSDOE48-unassigned-mass-20261006.tif'
               and r.get('sha256') == witness_sha]
    if (hashlib.sha256(registry_bytes).hexdigest() != registry_sha
            or saturation['registry_sha256'] != registry_sha
            or saturation['sample_sha256'] != '2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc'
            or measurement['witness_sha256'] != witness_sha or len(matches) != 1
            or measurement['uncovered_allowed_pixels'] != 0
            or measurement['positive_pixels'] != measurement['allowed_pixels']
            or measurement['allowed_pixels'] != 5167373
            or measurement['universal_overlap_blocker'] is not True
            or 'continuous' not in saturation['scope_caveat']):
        raise ValueError('Saturation receipt and pinned registry disagree; refuse to build')
    return measurement


def build(check_only=False):
    card_text = (ROOT / 'evidence/run-card.json').read_text()
    card = json.loads(card_text)
    registry = json.loads((ROOT / 'research/registry-lock.json').read_text())
    check(card, registry)

    parallel_text = (ROOT / 'evidence/parallel-lattice-audit.json').read_text()
    parallel = json.loads(parallel_text)
    parallel_card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    check_parallel(parallel, parallel_card, registry)

    h1_card_text = (ROOT / 'evidence/kanler_h1/run-card.json').read_text()
    h1 = json.loads(h1_card_text)
    if h1['verdict'] != 'negative' or h1['ok_to_submit'] is not False:
        raise ValueError('KANLER-H1 Run Card must remain fail-closed negative until global holdout incumbent is beaten')
    h1_cand = h1['holdout_dti']
    h1_uniq = h1['correlation_overlap_vs_registry']
    h1_z = h1['validator']['primary_zeros_tif']

    portfolio = json.loads((ROOT / 'evidence/portfolio-audit.json').read_text())
    saturation = json.loads((ROOT / 'evidence/registry_saturation_20261026.json').read_text())
    registry_bytes = (ROOT / 'evidence/upstream/GEMSDOE31/registry/raster_registry.json').read_bytes()
    measurement = check_saturation(saturation, registry_bytes)
    recovery_card = json.loads((ROOT / 'evidence/recovery-run-card.json').read_text())
    if recovery_card['verdict'] != 'negative' or recovery_card['raster_sha256'] is not None:
        raise ValueError('Recovery card cannot authorize a TIFF')

    audit = json.loads((DOC / 'audit.json').read_text())
    audit_by_site = {r['repo']: r for r in audit['rows']}
    candidate = card['holdout_dti']['scores']['candidate']
    ablation = card['holdout_dti']['scores']['ablation']
    delta = card['holdout_dti']['paired_differences']['ablation']
    max_rho = card['surface_registry']['full_fit_surface']['max_abs_rho']
    overlap = card['correlation_overlap_vs_registry']['candidate_within_3px_of_reference']

    rows = []
    for r in portfolio['files']:
        audited = audit_by_site[r['site']]
        url = f"https://github.com/{r['repo']}/blob/{audited['head']}/{audited['file']}"
        site_path = {'GEMSDOE31': 'docs/', 'GEMSDOE32': 'docs/index.html', 'GEMSDOE36': 'docs/'}.get(r['site'], '')
        site_url = f"https://buffedlizard55-lab.github.io/{r['site']}/{site_path}"
        local = audited['local_validation']
        fmt = 'Pass' if local['format_pass'] else 'Fail'
        peer = max((p for p in audit['pairs'] if p['candidate'] == r['site']), key=lambda p: p['overlap_3px'])
        rows.append(f'''<tr><td><a href="{e(site_url,quote=True)}">{e(r['site'])}</a></td>
<td><a class="file" href="{e(url,quote=True)}">{e(Path(audited['file']).name)}</a><small>Historical file · research reference only; score not bound to bytes</small></td>
<td><strong>{r['owner_reported_score']:.4f}</strong><small>Owner-reported / unverified</small></td>
<td>Not estimable<small>No calibrated score forecast</small></td>
<td><span class="badge">DUPLICATE</span><small>{peer['overlap_3px']:.2%} near {e(peer['reference'])}</small></td>
<td><strong>NO</strong></td><td>{fmt}<small>Local mask policy; not a portal verdict</small></td></tr>''')
    table = ''.join(rows)

    body = f'''<div class="wrap">
<section class="hero"><div><div class="eyebrow"><span>Executive summary &amp; research snapshot</span> 26 OCTOBER 2026 · NEVADA, USA</div>
<h1>Better fault maps start with <em>better evidence.</em></h1>
<p class="lede">Autonomous multi-lane fault discovery for DOE GEMS Prize #306 — combining 9-site forensic review, PhD attribution of <code>0.2778</code>, and the validated <code>KANLER-H1 (DCAP-LHC)</code> 37,654-dot GeoTIFF deliverable.</p>
<div class="hero-actions"><a class="button primary" href="#kanler-h1">Inspect KANLER-H1 &amp; Research GeoTIFF <span>↓</span></a><a class="button" href="kanler-h1-run-card.json">KANLER-H1 JSON Run Card <span>↗</span></a><a class="button" href="executive-summary.html">Contest Submission Guide <span>↗</span></a></div></div>
<aside class="hero-card" aria-label="Latest research checkpoint"><div class="label">Latest lane &nbsp; / &nbsp; KANLER-H1 (DCAP-LHC)</div><h2>Unique vs 416 detectors.<br>Honest negative gate.</h2><p>Dip-coupled piedmont + 1 m 3DEP LiDAR + upward-continued GeoDAWN/hydrothermal concordance (<code>3/3</code> frozen experiments).</p>
<div class="mini-row"><span>Format &amp; [0, 1] / Canary</span><strong>PASS · max AUC {h1['max_feature_auc']:.4f}</strong></div>
<div class="mini-row"><span>Detector 3-px uniqueness</span><strong>PASS · {h1_uniq['final_dots_max_within_3px_detector_lanes']['val']*100:.2f}% &le; 70%</strong></div>
<div class="mini-row"><span>Pooled HOLDOUT-DTI (Q3 win)</span><strong>{h1_cand['dti']:.4f} (Q3 {h1_cand['quadrant_3_walker_lane_win']['H1_MULTI_Q3_dti']:.4f})</strong></div>
<div class="mini-row"><span>Live weekly slot</span><strong class="fail">DO NOT SUBMIT</strong></div></aside></section>

<section class="verdict" aria-label="Submission verdict"><span class="verdict-icon">!</span><div><h2>DO NOT SUBMIT — VERDICT: NEGATIVE (LIVE WEEKLY SLOT NOT AUTHORIZED)</h2><p><code>KANLER-H1</code> generated a 100% format-valid, canary-clean, genuinely unique 37,654-dot GeoTIFF across all 416 detector rasters (<code>39.74%</code> near <code>GEMSDOE32 0.2778</code>; <code>25.81%</code> near <code>GPC-3</code>; <code>|&rho;| &le; 0.1599</code>) and beat <code>REF_H31X</code> in Walker Lane Quadrant 3 (<code>0.1726 vs 0.1602</code>), but trailed <code>REF_H31X</code> globally on <code>gems57-pooled-hide-v2</code> (<code>0.1253 vs 0.1674</code>) due to 47.4% missing 1 m LiDAR in Quadrant 1. Research GeoTIFF files are linked below for inspection only — do not spend a live weekly slot.</p></div><span class="tag">NEGATIVE VERDICT</span></section>

<section class="panel panel-pad" id="kanler-h1" style="margin-top:18px">
<div class="section-kicker">00 / New KANLER-H1 (DCAP-LHC) research artifact (unapproved for live slot)</div>
<h2>Validated Unique GeoTIFF Deliverable &amp; Metadata</h2>
<p><strong>Unique Submission Name:</strong> <code>{e(h1['submission_name'])}-zeros.tif</code> &nbsp; · &nbsp; <strong>DrivenData Note ({len(h1['submission_note'])}/140 chars):</strong> <code>{e(h1['submission_note'])}</code></p>
<p><strong>Grid &amp; Range Verification:</strong> Single-band <code>float32</code> · <code>EPSG:32611</code> · <code>3730 &times; 3292</code> · transform <code>(100, 0, 243350, 0, -100, 4508550)</code> · <code>0</code> NaN/Inf inside footprint · values strictly in <code>[0.0, 1.0]</code> · <code>37,654</code> binary dots · <code>0</code> positive pixels on known <code>labels.tif</code> · SHA-256 <code>{e(h1_z['sha256'])}</code>.</p>
<p><strong>Research Inspection Files (not authorized for live DrivenData upload):</strong>
<a href="downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.tif">All-finite -zeros.tif (139 KB) ↗</a> ·
<a href="downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.zip">Single-TIFF -zeros.zip (102 KB) ↗</a> ·
<a href="downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-nan.tif">Template-mask -nan.tif (352 KB) ↗</a> ·
<a href="downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-nan.zip">Single-TIFF -nan.zip (217 KB) ↗</a> ·
<a href="kanler-h1-run-card.json">KANLER-H1 JSON Run Card ↗</a> ·
<a href="research.html">Full PhD Review ↗</a> ·
<a href="hypotheses.html">5 Ranked Hypotheses &amp; Forensics ↗</a></p>
</section>

<section class="panel panel-pad" style="margin-top:18px"><h2>Additional registry stop: full-footprint witness &amp; synthetic 5-px lattice</h2><p>A pinned continuous diagnostic has positive support on all {measurement['allowed_pixels']:,} mirrored footprint cells, and synthetic grid <code>13gems_r13-lattice-s5</code> covers 99.87% of footprint cells within 3 px. Under the shared template’s literal positive-cell-as-dot rule, every nonempty 37,654-dot candidate exceeds 70% overlap against those synthetic probes (Pigeonhole lower bound 82.16%). Both literal and detector-lane readings are reported side by side without silent exemption.</p><p><a href="data/registry_saturation.json">View the reproducible certificate ↗</a> · <a href="research.html">Scientific review ↗</a> · <a href="data/recovery-run-card.json">Recovery-session run card ↗</a></p></section>

<section class="stats" aria-label="Key experiment figures"><div class="stat"><span class="label">KANLER-H1 HOLDOUT-DTI</span><strong>{h1_cand['dti']:.4f}</strong><small>95% CI [{h1_cand['ci95'][0]:.4f}, {h1_cand['ci95'][1]:.4f}] · Q3 = 0.1726</small></div>
<div class="stat"><span class="label">Piedmont &le;6&deg; SGMC lift</span><strong>+28.1%</strong><small>0.0569 vs REF_H31X 0.0444</small></div>
<div class="stat"><span class="label">Detector rasters checked</span><strong>{h1_uniq['detector_lane_rasters_checked']}</strong><small>Max 3-px {h1_uniq['final_dots_max_within_3px_detector_lanes']['val']*100:.2f}% · |&rho;| {h1['surface_max_rank_correlation']:.4f}</small></div>
<div class="stat"><span class="label">Submission slots used</span><strong>0</strong><small>No upload or receipt</small></div></section>

<section class="section" id="results"><div class="section-head"><div><div class="section-kicker">01 / Archived &amp; active lanes</div><h2>What the spatial holdout experiments say.</h2><p>Both <code>KANLER-H1 (0.1253)</code> and the preserved bilateral K/Th lane (<code>{candidate['dti']:.4f}</code>) were evaluated under <code>gems57-pooled-hide-v2</code> ($N = 60,988$ withheld positives) — never as a predicted leaderboard score.</p></div><a class="text-link" href="run-card.json">Archived bilateral run card ↗</a></div>
<div class="result-grid"><article class="panel panel-pad"><h3>Preserved lane: Bilateral K/Th texture &times; LiDAR scarp</h3><p>Tested matching radiometric textures on opposite sides of a coherent surface break across 4 spatial folds.</p>
<div class="score-row"><span class="big-score">{candidate['dti']:.4f}</span><span class="score-copy">HOLDOUT-DTI · {e(candidate['evaluator_version'])}<br>95% spatial-block CI [{candidate['ci95'][0]:.4f}, {candidate['ci95'][1]:.4f}]<br>{candidate['withheld_positive_pixels']:,} withheld positive pixels</span></div>
<div class="interval"><strong>Paired difference vs feature ablation: {delta['delta']:+.4f}</strong><p>HOLDOUT-DTI · same evaluator and positives · 95% CI [{delta['ci95'][0]:+.4f}, {delta['ci95'][1]:+.4f}]. Ablation scored {ablation['dti']:.4f} (95% CI [{ablation['ci95'][0]:.4f}, {ablation['ci95'][1]:.4f}]).</p></div></article>
<article class="panel panel-pad"><h3>Active lane: KANLER-H1 (DCAP-LHC)</h3><ul class="gate-list"><li><span class="gate-dot">✓</span><span>Single-feature &amp; surface canaries (10 checks)</span><span>max AUC {h1['max_feature_auc']:.4f} &le; 0.90</span></li>
<li><span class="gate-dot">✓</span><span>Surface &amp; dot rank vs 418 rasters</span><span>max |&rho;| {h1['surface_max_rank_correlation']:.4f} / {max_rho:.4f}*</span></li>
<li><span class="gate-dot">✓</span><span>Final dots vs 416 detector rasters</span><span>max {h1_uniq['final_dots_max_within_3px_detector_lanes']['val']*100:.2f}% &le; 70%</span></li>
<li><span class="gate-dot stop">&times;</span><span>Literal 5-px synthetic lattice probe</span><span>{overlap:.0%} / 99.997%</span></li>
<li><span class="gate-dot stop">&times;</span><span>Global holdout vs REF_H31X (0.1674)</span><span>0.1253 (Q3: 0.1726 win)</span></li></ul><p class="notice">*See <a href="data/feature_cache_recovery.json">feature cache recovery ↗</a> and <a href="parallel-lattice-audit.json">parallel GPC-3 lattice audit ({parallel["within_3px"]:,}/{parallel["candidate_dots"]:,}) ↗</a>.</p></article></div></section>

<section class="section" id="comparison"><span id="portfolio" aria-hidden="true"></span><div class="section-head"><div><div class="section-kicker">02 / Nine-site comparison</div><h2>Learn from the field.</h2><p>Exact historical files across <code>GEMSDOE24..36</code> are linked for study, not resubmission. All nine fail the 70% final-dot overlap rule against at least one peer (86.72%–100%).</p></div><a class="text-link" href="audit.json">Prior independent audit ↗</a></div>
<div class="table-wrap"><table><thead><tr><th>Project</th><th>Historical reference variant</th><th>Reported figure</th><th>Forecast</th><th>3 px uniqueness</th><th>Submit?</th><th>Local format</th></tr></thead><tbody>{table}</tbody></table></div>
<p class="notice">Reported figures are owner-provided and <strong>not organizer-confirmed</strong>; no receipt ties them to the listed file hashes. Non-<code>H19-5</code> live reference: <code>GEMSDOE70 p5-dual-submod300-oof38k = 0.2478</code> (owner-reported); shared holdout best: <code>GEMSDOE31 H31-X = 0.1661 HOLDOUT-DTI</code>.</p></section>

<section class="section"><div class="section-head"><div><div class="section-kicker">03 / PhD Structural &amp; Metric Attribution</div><h2>Why GEMSDOE32 (0.2778) stood out — and how to surpass it.</h2></div></div><div class="reason-grid">
<article class="panel"><h3>1. MAX-vs-SUM DTI Geometry &amp; B2 Collar Pruning</h3><p>In the pinned mirrors, <code>H33-B2</code> equals the 44,090-dot <code>D2.8</code> mask minus the 6,436 dots within <code>&le; 2 px</code> of mapped <code>labels.tif</code>, leaving 37,654 dots. Under pooled DTI (&alpha;=0.2, &beta;=0.8, 300 m kernel), <code>TP_w</code> uses <code>max</code> while <code>FP_w</code> uses <code>sum</code>: 2.8 px thinning + pixel-exact 200 m collar removal (<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">DrivenData staff ruling #11516</a>) strips scarp-flank false positives while preserving &gt;300 m splay/step-over recall. Its <strong>0.2778 is an unverified owner report</strong>.</p></article>
<article class="panel"><h3>2. Breaking Past 0.2778 Toward 0.33–0.4437</h3><p><code>KANLER-H1</code> proved in Walker Lane Quadrant 3 (92.9% LiDAR coverage) that combining scale-normalized break asymmetry, down-dip gravity steps, road-vetoed 1 m LiDAR scarplets, and blind magnetic/hydrothermal contacts beats <code>REF_H31X</code> (<code>0.1726 vs 0.1602</code>) at only <code>39.74%</code> overlap with <code>GEMSDOE32</code>. Fixing Quadrant-1 missing-LiDAR starvation via conditional quantile normalization (<code>KANLER-H1.1</code>) is the immediate next step. <a href="research.html">Read full PhD analysis ↗</a></p></article></div></section>

<section class="section" id="sources"><div class="section-head"><div><div class="section-kicker">04 / Source discipline</div><h2>Official rules, prizes &amp; primary geoscience archives.</h2><p>Public leaderboard #1 observed at <strong>0.4437 on 26 October 2026</strong>; competition closes <strong>Dec. 3, 2026</strong> with a <strong>$300,000</strong> prize pool ($50k Phase 1 + $250k Phase 2 per <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official DOE Rules PDF</a>).</p></div><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Open official leaderboard ↗</a></div>
<div class="panel source-strip"><div><p><strong>Automated source health, not automated leaderboard scraping.</strong></p><p class="source-status" data-github-status>Checking GitHub source freshness; no competition website is requested by this page.</p></div><a class="text-link" href="https://www.drivendata.org/termsofuse/">Why no live leaderboard feed? ↗</a></div>
<p class="notice">Official primary archives: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData Problem Description</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official Reference Repo</a> · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN (CC0)</a> · <a href="https://gdr.openei.org/submissions/1391">OpenEI GDR #1391 (CC-BY-4.0)</a> · <a href="https://gbcge.org/current-projects/ingenious/">GBCGE INGENIOUS</a>.</p></section></div>'''

    guide = f'''<div class="wrap"><div class="page-title"><div class="section-kicker">Executive summary / contest submission guide</div><h1>From evidence to upload.</h1><p>Exact DrivenData contest upload steps, fixing the <code>[0, 1]</code> portal error, and why no live weekly slot is authorized in this session.</p></div>
<div class="guide"><div><section class="panel warn"><h2>Current decision: <strong>DO NOT SUBMIT</strong></h2><p>Do not spend a live weekly submission slot right now. <code>KANLER-H1</code> (<code>{e(h1['submission_name'])}-zeros.tif</code>, <code>HOLDOUT-DTI = {h1_cand['dti']:.4f}</code>) passed format, canary, and 416-detector uniqueness (<code>58.47% &le; 70%</code>), and beat <code>REF_H31X</code> in Q3 (<code>0.1726 vs 0.1602</code>), but trailed global holdout incumbent <code>REF_H31X</code> (<code>0.1674</code>) due to Q1 missing-LiDAR starvation. Archived parallel runs also remain negative ({parallel["candidate_overlap"]:.0%} lattice overlap).</p><a class="button" href="kanler-h1-run-card.json">Open KANLER-H1 run card ↗</a></section>
<section class="panel"><h2>The four mandatory gates before any live upload</h2><ol><li><strong>Science &amp; Holdout:</strong> stay inside one pre-registered method lane; withhold whole fault segments with a 500–1,500 m buffer; compute catalogue features from visible faults only; pass single-feature leakage canaries (<code>AUC &le; 0.90</code>); beat same-evaluator holdout best on paired 95% block-bootstrap CI.</li><li><strong>Cross-Registry Uniqueness:</strong> check both the continuous surface before placement (<code>|Spearman| &le; 0.90</code>) and final dots (<code>&le; 70%</code> within <code>3 px</code>).</li><li><strong>Standalone GeoTIFF Format:</strong> single-band <code>float32</code>, <code>EPSG:32611</code>, <code>3730 &times; 3292</code>, transform <code>(100, 0, 243350, 0, -100, 4508550)</code>, no <code>NaN</code>/<code>Inf</code> inside footprint, values strictly in <code>[0, 1]</code>, reopened from disk and verified automatically.</li><li><strong>Weekly Slot Selector:</strong> verify live DrivenData portal slot counter (<a href="https://community.drivendata.org/raw/11553">Staff clarification #11553</a>) and archive the portal receipt alongside the file SHA-256.</li></ol></section>
<section class="panel"><h2>Understanding &amp; preventing <code>"Predicted values must be in range [0, 1]"</code></h2><p>The exact cause of the prior error is unknown: we do not have its rejected bytes or portal receipt. Typical root causes are: (1) unclipped raw logits/z-scores (&lt; 0 or &gt; 1), (2) numeric nodata sentinels such as <code>-9999.0</code> or <code>-3.4028235e38</code> read by an array check that only skips <code>NaN</code>, (3) <code>NaN</code>/<code>Inf</code> inside the active footprint, or (4) multi-band exports.</p><p>Our shared writer emits both an all-finite <code>-zeros.tif</code> (every cell in <code>3730 &times; 3292</code> finite in <code>[0.0, 1.0]</code>, <code>nodata=None</code>) and a strict template-mask <code>-nan.tif</code> twin (<code>NaN</code> outside footprint, identical <code>37,654</code> in-footprint predictions) plus single-TIFF <code>.zip</code> packages for &lt;1 s upload.</p></section>
<section class="panel"><h2>Step-by-step upload checklist (only after a future run reaches <code>verdict: promote</code>)</h2><ol><li>Verify <code>verdict == "promote"</code> in the JSON Run Card and run <code>python scripts/validate_submission.py data/raw/sample_submission.tif &lt;file&gt;.tif --allow-zero-outside</code> (<code>"ok": true</code>).</li><li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData Submissions</a> and check remaining weekly slots.</li><li>Upload the single-TIFF <code>.zip</code> (or <code>-zeros.tif</code>) and paste the &le;140-character Run Card note verbatim.</li><li>Record the returned portal score with timestamp and SHA-256 receipt (only then may a score be labeled <code>ORGANIZER-CONFIRMED</code>), and remember Phase 1/Phase 2 both evaluate your single selected submission (deadline <strong>Dec. 3, 2026</strong>; mandatory AI disclosure in finalist report per <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official Rules Sec. 3.2</a>).</li></ol></section></div>
<aside><section class="panel"><div class="section-kicker">KANLER-H1 summary</div><h3>Measured holdout</h3><p><code>{h1_cand['dti']:.4f}</code> HOLDOUT-DTI · 95% CI [{h1_cand['ci95'][0]:.4f}, {h1_cand['ci95'][1]:.4f}] · {h1_cand['withheld_positives']:,} positives · {e(h1_cand['evaluator_version'])} (Q3 Walker Lane: <code>0.1726 vs 0.1602</code>).</p><h3>Archived bilateral lane</h3><p><code>{candidate['dti']:.4f}</code> HOLDOUT-DTI · 95% CI [{candidate['ci95'][0]:.4f}, {candidate['ci95'][1]:.4f}].</p><h3>Unique name &amp; note</h3><p><code>{e(h1['submission_name'])}-zeros.tif</code><br><small>{e(h1['submission_note'])} ({len(h1['submission_note'])}/140 chars)</small></p><h3>Research files</h3><p><a href="downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.tif">-zeros.tif ↗</a> · <a href="downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-nan.tif">-nan.tif ↗</a> · <a href="kanler-h1-run-card.json">JSON card ↗</a></p></section>
<section class="panel"><div class="section-kicker">Next session: KANLER-H1.1</div><h3>Fix Q1 LiDAR starvation</h3><p>Apply conditional rank normalization separately inside <code>lidar_valid == 1</code> (75.4%) and <code>lidar_valid == 0</code> (24.6%, 47.4% of Q1) plus pure slope-asymmetry gating to preserve Q3 gains across all 4 quadrants.</p></section></aside></div></div>'''

    outputs = {
        DOC / 'index.html': layout('Research & evidence', body),
        DOC / 'executive-summary.html': layout('Executive summary & submission guide', guide),
        DOC / 'run-card.json': card_text,
        DOC / 'kanler-h1-run-card.json': h1_card_text,
        DOC / 'parallel-lattice-audit.json': parallel_text,
        ROOT / 'run-card.json': card_text,
        DOC / 'data/run_card.json': card_text,
        DOC / 'data/run-card.json': card_text,
        DOC / 'data/recovery-run-card.json': (ROOT / 'evidence/recovery-run-card.json').read_text(),
        DOC / 'data/registry_saturation.json': (ROOT / 'evidence/registry_saturation_20261026.json').read_text(),
        DOC / 'data/feature_cache_recovery.json': (ROOT / 'evidence/feature_cache_recovery_20261026.json').read_text(),
        DOC / 'data/shared_template_pins.json': (ROOT / 'registry/shared_template_pins.json').read_text(),
        DOC / 'research.html': layout('Scientific review', render_markdown(ROOT / 'research/review.md')),
        DOC / 'hypotheses.html': layout('Research hypotheses', render_markdown(ROOT / 'research/hypotheses.md')),
        DOC / 'sources.html': layout('Source register', render_markdown(DOC / 'SOURCES.md')),
        DOC / 'summary.html': layout('Executive summary', render_markdown(DOC / 'EXECUTIVE_SUMMARY.md')),
        DOC / 'submission.html': layout('Executive summary & submission guide', guide),
        DOC / 'research.md': (ROOT / 'research/review.md').read_text(),
        DOC / 'submission.md': (DOC / 'SUBMISSION_GUIDE.md').read_text(),
        DOC / 'verification.md': (ROOT / 'research/verification.md').read_text(),
        DOC / 'preregistration_kanler_h1.md': (ROOT / 'research/preregistration_kanler_h1.md').read_text(),
        **{DOC / f'{src}.md': (ROOT / f'research/{src}.md').read_text() for src in ['review', 'hypotheses']},
    }
    if check_only:
        stale = [str(path.relative_to(ROOT)) for path, text in outputs.items()
                 if not path.is_file() or path.read_text() != text]
        if stale:
            raise ValueError('Generated site is stale: ' + ', '.join(stale))
    else:
        for path, text in outputs.items():
            path.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify committed outputs without writing')
    build(check_only=parser.parse_args().check)
