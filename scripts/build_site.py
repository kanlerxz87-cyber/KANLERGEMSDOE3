"""Render the active evidence-led static site from committed, checked receipts.

No fetching, model fitting, upload, or score inference is performed by this build.
"""
from pathlib import Path
import json
from html import escape as e
try:
    from .check_run import check
except ImportError:  # python scripts/build_site.py
    from check_run import check

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs'


def layout(title, body):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | GEMS Evidence Lab</title><meta name="description" content="Evidence-led fault mapping research and submission readiness.">
<link rel="stylesheet" href="experiment.css"></head><body>
<header class="top"><div class="wrap top-inner"><a class="brand" href="index.html"><span class="mark">G</span><span><strong>GEMS</strong><small>Evidence lab / KANLERGEMSDOE3</small></span></a>
<nav aria-label="Main navigation"><a href="index.html#results">Experiment</a><a href="index.html#comparison">Site comparison</a><a href="index.html#sources">Sources</a><a class="nav-cta" href="executive-summary.html">Submission guide ↗</a></nav></div></header>
<main>{body}</main><footer><div class="wrap"><span>GEMS Evidence Lab &nbsp; / &nbsp; Maximize P(Win) · Own the Outcome</span><span>Research snapshot · No competition slot spent</span></div></footer>
<script src="source-status.js" defer></script></body></html>'''


def build():
    card_text=(ROOT/'evidence/run-card.json').read_text()
    card=json.loads(card_text)
    registry=json.loads((ROOT/'research/registry-lock.json').read_text())
    check(card,registry)
    portfolio=json.loads((ROOT/'evidence/portfolio-audit.json').read_text())
    candidate=card['holdout_dti']['scores']['candidate']
    ablation=card['holdout_dti']['scores']['ablation']
    delta=card['holdout_dti']['paired_differences']['ablation']
    max_rho=card['surface_registry']['full_fit_surface']['max_abs_rho']
    overlap=card['correlation_overlap_vs_registry']['candidate_within_3px_of_reference']
    rows=[]
    for r in portfolio['files']:
        url=f"https://github.com/{r['repo']}/blob/{r['ref']}/{r['file']}"
        site_url=f"https://buffedlizard55-lab.github.io/{r['site']}/"
        rows.append(f'''<tr><td><a href="{e(site_url,quote=True)}">{e(r['site'])}</a></td>
<td><a class="file" href="{e(url,quote=True)}">{e(Path(r['file']).name)}</a><small>Historical file · research reference only</small></td>
<td><strong>{r['owner_reported_score']:.4f}</strong><small>Owner-reported / unverified</small></td>
<td>Not estimable<small>No calibrated score forecast</small></td>
<td><span class="badge">DUPLICATE</span><small>{r['max_3px_peer']['candidate_within_3px']:.2%} near {e(r['max_3px_peer']['site'])}</small></td></tr>''')
    table=''.join(rows)
    body=f'''<div class="wrap">
<section class="hero"><div><div class="eyebrow"><span>Research snapshot</span> 26 OCTOBER 2026 · NEVADA, USA</div>
<h1>Better fault maps start with <em>better evidence.</em></h1>
<p class="lede">A reproducible effort to find previously unmapped faults that may inform geothermal exploration — with a clear line between a promising hypothesis and an upload-ready result.</p>
<div class="hero-actions"><a class="button primary" href="#results">Explore the experiment <span>↓</span></a><a class="button" href="run-card.json">View JSON run card <span>↗</span></a></div></div>
<aside class="hero-card" aria-label="Latest research checkpoint"><div class="label">Latest checkpoint &nbsp; / &nbsp; 01</div><h2>One hypothesis.<br>One honest stop.</h2><p>We tested radiometric texture across LiDAR scarps, then applied the same novelty rule to the final dots.</p>
<div class="mini-row"><span>Feature leakage canaries</span><strong>PASS</strong></div><div class="mini-row"><span>Frozen surface-rank screen</span><strong>PASS*</strong></div><div class="mini-row"><span>Final-dot uniqueness</span><strong class="fail">FAIL · {overlap:.0%}</strong></div><div class="mini-row"><span>GeoTIFF / slot</span><strong>NOT ISSUED</strong></div></aside></section>
<section class="verdict" aria-label="Submission verdict"><span class="verdict-icon">!</span><div><h2>DO NOT SUBMIT — NO CANDIDATE FILE</h2><p>Every final dot was within 3 pixels of a registered lattice dot. The literal duplicate rule requires us to stop, not adjust the map to evade it.</p></div><span class="tag">NEGATIVE VERDICT</span></section>
<section class="stats" aria-label="Key experiment figures"><div class="stat"><span class="label">Pooled HOLDOUT-DTI</span><strong>{candidate['dti']:.4f}</strong><small>95% CI [{candidate['ci95'][0]:.4f}, {candidate['ci95'][1]:.4f}]</small></div>
<div class="stat"><span class="label">Withheld positives</span><strong>{candidate['withheld_positive_pixels']:,}</strong><small>Whole-component spatial holdout</small></div>
<div class="stat"><span class="label">Surface references</span><strong>167</strong><small>Frozen snapshot; not globally complete</small></div>
<div class="stat"><span class="label">Submission slots used</span><strong>0</strong><small>No upload or receipt</small></div></section>
<section class="section" id="results"><div class="section-head"><div><div class="section-kicker">01 / The experiment</div><h2>What the data actually say.</h2><p>One preregistered provisional lane, evaluated as catalogue recovery — not as a predicted leaderboard score.</p></div><a class="text-link" href="run-card.json">Explore full run card ↗</a></div>
<div class="result-grid"><article class="panel panel-pad"><h3>Bilateral K/Th texture × LiDAR scarp</h3><p>The hypothesis is that matching radiometric textures on opposite sides of a coherent surface break may show a consistent along-strike displacement. Channels, rock contacts, roads and survey seams can mimic this pattern.</p>
<div class="score-row"><span class="big-score">{candidate['dti']:.4f}</span><span class="score-copy">HOLDOUT-DTI · {e(candidate['evaluator_version'])}<br>95% spatial-block CI [{candidate['ci95'][0]:.4f}, {candidate['ci95'][1]:.4f}]<br>{candidate['withheld_positive_pixels']:,} withheld positive pixels</span></div>
<div class="interval"><strong>Paired difference vs feature ablation: {delta['delta']:+.4f}</strong><p>HOLDOUT-DTI · same evaluator and positives · 95% CI [{delta['ci95'][0]:+.4f}, {delta['ci95'][1]:+.4f}]. The interval crosses zero. The ablation scored {ablation['dti']:.4f} (95% CI [{ablation['ci95'][0]:.4f}, {ablation['ci95'][1]:.4f}]). It is not the current best incumbent.</p></div>
<p class="notice">Pooled from four whole-component folds, with a 1.5 km training buffer, exact visible-fault masking and a 300 m triangular kernel. The bootstrap is conditional on the fitted folds and mapped catalogue.</p></article>
<article class="panel panel-pad"><h3>Gate-by-gate, not guesswork.</h3><ul class="gate-list"><li><span class="gate-dot">✓</span><span>Single-feature and OOF-model canaries</span><span>No AUC &gt; 0.90</span></li>
<li><span class="gate-dot">✓</span><span>Surface rank vs 167 pinned references</span><span>max |ρ| {max_rho:.4f}*</span></li>
<li><span class="gate-dot stop">×</span><span>Final dots vs one registered lattice</span><span>{overlap:.0%} near</span></li>
<li><span class="gate-dot stop">×</span><span>Improvement vs current comparable best</span><span>Not established</span></li>
<li><span class="gate-dot stop">—</span><span>Saved-file validator / organizer receipt</span><span>No file / none</span></li></ul><p class="notice">*Pass applies only to this frozen snapshot and surface stage. Global registry completeness, organizer-source authentication and redistribution rights remain unresolved.</p></article></div></section>
<section class="section" id="comparison"><div class="section-head"><div><div class="section-kicker">02 / Nine-site comparison</div><h2>Learn from the field.</h2><p>Exact historical files are linked for study, not resubmission. All nine fail the final-dot overlap rule against at least one of the other eight.</p></div><a class="text-link" href="audit.json">Prior independent audit ↗</a></div>
<div class="table-wrap"><table><thead><tr><th>Project</th><th>Historical best file</th><th>Reported figure</th><th>Forecast</th><th>3 px uniqueness</th></tr></thead><tbody>{table}</tbody></table></div>
<p class="notice">Reported figures are owner-provided and <strong>not organizer-confirmed</strong>; no receipt ties them to the listed file hashes. Percentages are observed directional overlap of the indicated row against one peer, not a score. Surface comparisons and other registries are not covered by this nine-file table.</p></section>
<section class="section"><div class="section-head"><div><div class="section-kicker">03 / Interpretation</div><h2>Why GEMSDOE32 stood out.</h2></div></div><div class="reason-grid">
<article class="panel"><h3>What we can verify</h3><p>In the pinned owner mirrors, H33-B2 is exactly the 44,090-dot D2.8 mask minus the 6,436 dots at or within two pixels of the mapped catalogue, leaving 37,654. Its <strong>0.2778 is an unverified owner report</strong>, not a receipt.</p></article>
<article class="panel"><h3>What we cannot infer</h3><p>Removing predictions can reduce false-positive mass, but can also lose valuable fault coverage. Hidden labels and causal ablation are unavailable, so thinning is a hypothesis, not proof of why a score changed. Whether any new method can surpass it is unknown.</p></article></div></section>
<section class="section" id="sources"><div class="section-head"><div><div class="section-kicker">04 / Source discipline</div><h2>Freshness without false certainty.</h2><p>Public leaderboard leader observed at <strong>0.4437 on 26 October 2026</strong>; this is a dated organizer-page snapshot, not a score for our file. It can change.</p></div><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Open official leaderboard ↗</a></div>
<div class="panel source-strip"><div><p><strong>Automated source health, not automated leaderboard scraping.</strong></p><p class="source-status" data-github-status>Checking GitHub source freshness; no competition website is requested by this page.</p></div><a class="text-link" href="https://www.drivendata.org/termsofuse/">Why no live leaderboard feed? ↗</a></div>
<p class="notice">DrivenData's terms prohibit automated monitoring. The status check uses only GitHub's public API. Peer mirrors are hash-pinned, not authenticated organizer originals; review their rights and the <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN source</a> before use. See the <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/research/preregistration.md">pre-registration</a> and <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/README.md">project README</a>.</p></section></div>'''
    guide=f'''<div class="wrap"><div class="page-title"><div class="section-kicker">Executive summary / submission guide</div><h1>From evidence to upload.</h1><p>What must be true before a file is considered — and why there is nothing to upload from this run.</p></div>
<div class="guide"><div><section class="panel warn"><h2>Current decision: <strong>DO NOT SUBMIT</strong></h2><p>No new candidate GeoTIFF exists. The final-dot uniqueness gate failed at {overlap:.0%} overlap, and paired improvement was not established. A format-only file would not satisfy the science or selection gates.</p><a class="button" href="run-card.json">Open the run card ↗</a></section>
<section class="panel"><h2>The separate gates</h2><ol><li><strong>Science:</strong> establish the actual named lane; withhold whole segments and buffers; fit catalogue-derived features only from visible faults. Run feature canaries and a paired comparison against the current best on identical folds, with a defensible interval.</li><li><strong>Novelty:</strong> inventory current registries, test the surface before placement and the final dots afterward. A rank correlation above 0.90 or more than 70% of dots within 3 pixels of any one reference is a hard stop. The current 167-file snapshot is not complete.</li><li><strong>Format:</strong> only after clearing those gates, use the pinned shared writer. Save one <code>float32</code> band in the template CRS, shape and transform, then reopen the saved bytes and validate range, finite footprint and metadata.</li><li><strong>Selector:</strong> a format pass is not approval. Separately check the current account-specific submission cap, rights and organizer provenance; do not spend a slot automatically.</li></ol></section>
<section class="panel"><h2>Understanding the “[0, 1]” error</h2><p>The exact cause of the prior error is unknown: we do not have its rejected bytes or portal receipt. Typical causes include NaN or infinity, a nodata sentinel, scores outside [0,1], or writing the wrong band. A CRS, shape or transform mismatch is a separate format failure.</p><p>As a conservative local policy, use finite zero outside the footprint and finite probabilities in [0,1] inside it; the public specification permits outside-footprint NaN. Do not silently clip or normalize a broken model. Reopen the saved TIFF and inspect <em>all stored cells</em>, single band, <code>float32</code>, CRS, dimensions and transform. An all-finite check is a precaution, not proof of the portal's past behavior or of scientific validity.</p></section>
<section class="panel"><h2>Only after explicit authorization</h2><p>Check the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official format</a>, current competition rules and account-specific cap. Select the exact validated filename and ≤140-character run-card note. Keep the file SHA-256 and the organizer's submission-page receipt together; only that receipt can support an organizer-confirmed result for that file.</p><p>No automatic upload, slot selection or expert geological review has taken place.</p></section></div>
<aside><section class="panel"><div class="section-kicker">Run summary</div><h3>Attempt</h3><p>Technical attempt 1 stopped on an orchestrator typo; fixed replay was attempt 2. Scientific settings did not change.</p><h3>Measured holdout</h3><p>{candidate['dti']:.4f} HOLDOUT-DTI · 95% CI [{candidate['ci95'][0]:.4f}, {candidate['ci95'][1]:.4f}] · {candidate['withheld_positive_pixels']:,} positives · {e(candidate['evaluator_version'])}.</p><h3>File &amp; hash</h3><p>None. Validation is not applicable until a legitimate candidate is saved.</p><h3>Current selector</h3><p>Not authorized. The submission cap was not checked for this account.</p></section>
<section class="panel"><div class="section-kicker">Next, not now</div><h3>Resolve the obstruction</h3><p>The 37,654-dot budget was recorded before candidate generation, not lowered to bypass the lattice. Any protocol change needs explicit authorization; do not secretly exempt the lattice or tune around its holes.</p></section></aside></div></div>'''
    (DOC/'index.html').write_text(layout('Research & evidence',body))
    (DOC/'executive-summary.html').write_text(layout('Executive summary & submission guide',guide))
    # The exact same canonical card is mirrored for root and Pages consumers.
    (DOC/'run-card.json').write_text(card_text)
    (ROOT/'run-card.json').write_text(card_text)
    for src in ['review','hypotheses']:
        (DOC/f'{src}.md').write_text((ROOT/f'research/{src}.md').read_text())

if __name__=='__main__': build()
