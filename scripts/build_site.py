"""Render the active evidence-led static site from committed, checked receipts.

No fetching, model fitting, upload, or score inference is performed by this build.
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

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs'


def layout(title, body):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | GEMS Evidence Lab</title><meta name="description" content="Evidence-led fault mapping research and submission readiness.">
<link rel="stylesheet" href="experiment.css"></head><body>
<header class="top"><div class="wrap top-inner"><a class="brand" href="index.html"><span class="mark">G</span><span><strong>GEMS</strong><small>Evidence lab / KANLERGEMSDOE3</small></span></a>
<nav aria-label="Main navigation"><a href="index.html#results">Experiment</a><a href="index.html#comparison">Site comparison</a><a href="index.html#sources">Sources</a><a href="k3h1.html">K3-H1 lane</a><a class="nav-cta" href="executive-summary.html">Submission guide ↗</a></nav></div></header>
<main>{body}</main><footer><div class="wrap"><span>GEMS Evidence Lab &nbsp; / &nbsp; Maximize P(Win) · Own the Outcome</span><span>Research snapshot · No competition slot spent</span></div></footer>
<script src="source-status.js" defer></script></body></html>'''


def render_markdown(source):
    """Render trusted project Markdown with local, published evidence links."""
    text=source.read_text(encoding='utf-8')
    substitutions={
        '../evidence/registry_saturation_20261026.json':'data/registry_saturation.json',
        '../evidence/feature_cache_recovery_20261026.json':'data/feature_cache_recovery.json',
        '../evidence/run-card.json':'run-card.json',
        '../evidence/parallel-lattice-audit.json':'parallel-lattice-audit.json',
        '../registry/shared_template_pins.json':'data/shared_template_pins.json',
        '../docs/audit.json':'audit.json',
        '../archive/recovery/concurrent-main-research-review.md':'https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/archive/recovery/concurrent-main-research-review.md',
        '](preregistration.md)':'](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/research/preregistration.md)',
        '](review.md)':'](research.html)',
        '](hypotheses.md)':'](hypotheses.html)',
        '](SOURCES.md)':'](sources.html)',
        '](SUBMISSION_GUIDE.md)':'](executive-summary.html)',
    }
    for old,new in substitutions.items():
        text=text.replace(old,new)
    rendered=markdown.markdown(text,extensions=['tables','fenced_code','sane_lists'])
    rendered=rendered.replace('<table>','<div class="table-wrap"><table>').replace('</table>','</table></div>')
    return f'<div class="wrap"><article class="panel panel-pad markdown-page">{rendered}</article></div>'


def check_saturation(saturation, registry_bytes):
    """Check the pinned evidence identity and invariant, not a geological result."""
    registry_sha='e1f10c7bf4c0b9c61a427a6106a0073ca2ea449f6d30b2b787931fbda2d2e104'
    witness_sha='975c217ef803a45041077a219ba460134a8c84c8ea9f7ffc0414ddb47cb54ccd'
    measurement=saturation['measurement']
    registry=json.loads(registry_bytes)
    matches=[r for r in registry['rasters'] if r.get('repo')=='GEMSDOE48'
             and r.get('ref')=='268ec599f51c517cc3485da077c24d83af5be81d'
             and r.get('path')=='docs/downloads/GEMSDOE48-unassigned-mass-20261006.tif'
             and r.get('sha256')==witness_sha]
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


def k3_lane():
    """Load the K3-H1 run card and refuse to build if it disagrees with the published bytes."""
    card_text=(ROOT/'evidence/k3h1-run-card.json').read_text()
    card=json.loads(card_text)
    tif=DOC/'downloads'/card['raster_file']
    zipped=DOC/'downloads'/card['zip_file']
    if (hashlib.sha256(tif.read_bytes()).hexdigest()!=card['raster_sha256']
            or hashlib.sha256(zipped.read_bytes()).hexdigest()!=card['zip_sha256']):
        raise ValueError('K3-H1 run card does not match the published TIFF/ZIP bytes; refuse to build')
    if (not 0<len(card['submission_note'])<=140 or card['verdict'] not in ('promote','negative')
            or card['download']['recommended_for_weekly_slot']!=(card['verdict']=='promote')
            or card['holdout']['class']!='HOLDOUT-DTI' or 'NOT a score' not in card['projection']['class']):
        raise ValueError('K3-H1 run card is internally inconsistent; refuse to build')
    uq=json.loads((ROOT/'evidence/uniqueness_final.json').read_text())
    if uq['candidate_file_sha256']!=card['raster_sha256']:
        raise ValueError('K3-H1 uniqueness evidence refers to different bytes')
    summary={k:v for k,v in uq.items() if k!='rows'}
    summary['focus_sites']=card['focus_sites']
    return card, card_text, json.dumps(summary,indent=1)+'\n'


def k3_block(card):
    h=card['holdout']; p=card['projection']; r=card['registry']; d=card['download']
    tif=f"downloads/{card['raster_file']}"; zipped=f"downloads/{card['zip_file']}"
    ov=r['worst_overlap_non_space_filling']; rho=r['worst_spearman_final_dots']; srf=r['worst_spearman_surface_preplacement']
    slot='YES' if d['recommended_for_weekly_slot'] else 'NO'
    return f'''<section class="panel panel-pad" id="k3h1" aria-label="Generated K3-H1 GeoTIFF" style="margin-top:18px;border:2px solid #b84227">
<div class="section-kicker">New this session · K3-H1 lane · antislope-scarp grain traces</div>
<h2>Generated unique TIF — download: <strong>OK</strong> · upload format: <strong>OK</strong> · spend a slot: <strong class="fail">{slot}</strong></h2>
<p>{e(d['bottom_line'])}</p>
<div class="hero-actions"><a class="button primary" href="{e(tif,quote=True)}">Download TIF <span>↓</span></a><a class="button" href="{e(zipped,quote=True)}">Download ZIP <span>↓</span></a><a class="text-link" href="k3h1.html">Full lane report: why 0.2778, experiments, uniqueness ↗</a><a class="text-link" href="k3h1-run-card.json">JSON run card ↗</a></div>
<ul class="gate-list">
<li><span class="gate-dot">✓</span><span>Format: 15 shared-validator checks + official spec (finite, 0/1, zeros outside, EPSG:32611)</span><span>PASS · avoids the [0,1] error</span></li>
<li><span class="gate-dot">✓</span><span>Unique vs {r['registry_rasters_compared']-len(r['space_filling_rasters'])} non-space-filling registry rasters (focus sites + scored ledger)</span><span>max overlap {ov['value']:.3f} · max ρ {rho['value']:.3f} (surface {srf['value']:.3f})</span></li>
<li><span class="gate-dot stop">×</span><span>Literal rule: {len(r['space_filling_rasters'])} space-filling rasters + the full-footprint witness block <em>every</em> non-empty file</span><span>BLOCKED · needs your policy decision</span></li>
<li><span class="gate-dot stop">×</span><span>Expected to beat 0.2778?</span><span>No · PROJECTION {p['value']:.3f} vs {p['champion_same_fit']:.3f} (champion, same model)</span></li>
<li><span class="gate-dot stop">×</span><span>HOLDOUT-DTI vs best control · {e(h['evaluator_version'])} · {h['withheld_positives']:,} withheld</span><span>{h['value']:.4f} [{h['ci95'][0]:.4f}, {h['ci95'][1]:.4f}] vs {h['incumbent_value']:.4f}; Δ {card['paired_improvement_delta']:+.4f} [{card['paired_improvement_ci95'][0]:+.4f}, {card['paired_improvement_ci95'][1]:+.4f}]</span></li>
</ul>
<p><strong>File</strong> <code>{e(card['raster_file'])}</code><br><strong>SHA-256</strong> <code>{e(card['raster_sha256'])}</code><br><strong>Submission name</strong> <code>{e(card['submission_name'])}</code><br><strong>Note ({card['submission_note_chars']} chars)</strong> <code>{e(card['submission_note'])}</code></p>
<p class="notice">PROJECTION = live-ledger inversion (leave-one-out MAE {p['loo_mae']:.3f}); it is not a score. Verdict <strong>{e(card['verdict'])}</strong> is computed by the pre-registered rules and <code>scripts/promotion_gate.py</code>. No slot was used.</p></section>'''


def k3_row(card):
    p=card['projection']; r=card['registry']
    return f'''<tr><td><a href="k3h1.html">KANLERGEMSDOE3 · K3-H1 (new)</a></td>
<td><a class="file" href="downloads/{e(card['raster_file'],quote=True)}">{e(card['raster_file'])}</a><small>Generated this session · hybrid: ≤69.5% H19-5 core + ≥30.5% antislope-scarp dots</small></td>
<td><strong>—</strong><small>Never submitted</small></td>
<td>{p['value']:.3f}<small>PROJECTION, not a score · champion {p['champion_same_fit']:.3f} same model</small></td>
<td><span class="badge">UNIQUE*</span><small>max {r['worst_overlap_non_space_filling']['value']:.1%} vs any focus winner/registry raster · *literal rule blocks every file</small></td>
<td><strong>NO</strong><small>Format-safe; projected below 0.2778</small></td><td>Pass<small>15/15 shared checks + official spec</small></td></tr>'''


def build(check_only=False):
    k3card,k3_text,k3_uniqueness=k3_lane()
    card_text=(ROOT/'evidence/run-card.json').read_text()
    card=json.loads(card_text)
    registry=json.loads((ROOT/'research/registry-lock.json').read_text())
    check(card,registry)
    parallel_text=(ROOT/'evidence/parallel-lattice-audit.json').read_text()
    parallel=json.loads(parallel_text)
    parallel_card=json.loads((ROOT/'evidence/run_card.json').read_text())
    check_parallel(parallel,parallel_card,registry)
    portfolio=json.loads((ROOT/'evidence/portfolio-audit.json').read_text())
    saturation=json.loads((ROOT/'evidence/registry_saturation_20261026.json').read_text())
    registry_bytes=(ROOT/'evidence/upstream/GEMSDOE31/registry/raster_registry.json').read_bytes()
    measurement=check_saturation(saturation,registry_bytes)
    recovery_card=json.loads((ROOT/'evidence/recovery-run-card.json').read_text())
    if recovery_card['verdict'] != 'negative' or recovery_card['raster_sha256'] is not None:
        raise ValueError('Recovery card cannot authorize a TIFF')
    audit=json.loads((DOC/'audit.json').read_text())
    audit_by_site={r['repo']:r for r in audit['rows']}
    candidate=card['holdout_dti']['scores']['candidate']
    ablation=card['holdout_dti']['scores']['ablation']
    delta=card['holdout_dti']['paired_differences']['ablation']
    max_rho=card['surface_registry']['full_fit_surface']['max_abs_rho']
    overlap=card['correlation_overlap_vs_registry']['candidate_within_3px_of_reference']
    rows=[]
    for r in portfolio['files']:
        audited=audit_by_site[r['site']]
        url=f"https://github.com/{r['repo']}/blob/{audited['head']}/{audited['file']}"
        site_path={'GEMSDOE31':'docs/', 'GEMSDOE32':'docs/index.html', 'GEMSDOE36':'docs/'}.get(r['site'],'')
        site_url=f"https://buffedlizard55-lab.github.io/{r['site']}/{site_path}"
        local=audited['local_validation']
        fmt='Pass' if local['format_pass'] else 'Fail'
        peer=max((p for p in audit['pairs'] if p['candidate']==r['site']),key=lambda p:p['overlap_3px'])
        rows.append(f'''<tr><td><a href="{e(site_url,quote=True)}">{e(r['site'])}</a></td>
<td><a class="file" href="{e(url,quote=True)}">{e(Path(audited['file']).name)}</a><small>Historical file · research reference only; score not bound to bytes</small></td>
<td><strong>{r['owner_reported_score']:.4f}</strong><small>Owner-reported / unverified</small></td>
<td>Not estimable<small>No calibrated score forecast</small></td>
<td><span class="badge">DUPLICATE</span><small>{peer['overlap_3px']:.2%} near {e(peer['reference'])}</small></td>
<td><strong>NO</strong></td><td>{fmt}<small>Local mask policy; not a portal verdict</small></td></tr>''')
    table=''.join(rows)+k3_row(k3card)
    body=f'''<div class="wrap">
{k3_block(k3card)}
<section class="hero"><div><div class="eyebrow"><span>Research snapshot</span> 26 OCTOBER 2026 · NEVADA, USA</div>
<h1>Better fault maps start with <em>better evidence.</em></h1>
<p class="lede">A reproducible effort to find previously unmapped faults that may inform geothermal exploration — with a clear line between a promising hypothesis and an upload-ready result.</p>
<div class="hero-actions"><a class="button primary" href="#results">Explore the experiment <span>↓</span></a><a class="button" href="run-card.json">View JSON run card <span>↗</span></a></div></div>
<aside class="hero-card" aria-label="Latest research checkpoint"><div class="label">Latest checkpoint &nbsp; / &nbsp; 01</div><h2>One hypothesis.<br>One honest stop.</h2><p>We tested radiometric texture across LiDAR scarps, then applied the same novelty rule to the final dots.</p>
<div class="mini-row"><span>Feature leakage canaries</span><strong>PASS</strong></div><div class="mini-row"><span>Frozen surface-rank screen</span><strong>PASS*</strong></div><div class="mini-row"><span>Final-dot uniqueness</span><strong class="fail">FAIL · {overlap:.0%}</strong></div><div class="mini-row"><span>This lane: TIFF / slot</span><strong>NOT ISSUED</strong></div></aside></section>
<section class="verdict" aria-label="Submission verdict"><span class="verdict-icon">!</span><div><h2>DO NOT SUBMIT — NO ELIGIBLE FILE</h2><p>Our final dots, and a separate research TIFF already on main, each had 100% overlap with a registered lattice. The literal duplicate rule requires a stop, not an exemption.</p></div><span class="tag">NEGATIVE VERDICT</span></section>
<section class="panel panel-pad" style="margin-top:18px"><h2>Additional registry stop: full-footprint witness</h2><p>A pinned continuous diagnostic has positive support on all {measurement['allowed_pixels']:,} mirrored footprint cells. Under the shared template’s literal positive-cell-as-dot rule, every nonempty candidate in that footprint has 100% directed overlap and must stop. It is <strong>not established</strong> to be a previous dot submission; its inclusion in the registry comparison requires a common protocol decision, not a silent exemption.</p><p><a href="data/registry_saturation.json">View the reproducible certificate ↗</a> · <a href="research.html">Scientific review ↗</a> · <a href="data/recovery-run-card.json">Recovery-session run card ↗</a></p></section>
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
<li><span class="gate-dot stop">×</span><span>Shared stack in this experiment</span><span>Not reused*</span></li>
<li><span class="gate-dot stop">×</span><span>Final dots vs one registered lattice</span><span>{overlap:.0%} near</span></li>
<li><span class="gate-dot stop">×</span><span>Improvement vs current comparable best</span><span>Not established</span></li>
<li><span class="gate-dot stop">—</span><span>This run: saved file / organizer receipt</span><span>None / none</span></li></ul><p class="notice">*The surface pass applies only to the frozen snapshot. The 19 shared cached bands were recovered later and hash matched, but were not used by this experiment; organizer-source authentication and redistribution rights remain unresolved. <a href="data/feature_cache_recovery.json">Recovery evidence ↗</a></p><div class="interval"><strong>Parallel research TIFF: also a duplicate</strong><p>The separately committed GPC-3 file passed only a nine-champion comparison; our check found {parallel["within_3px"]:,} of {parallel["candidate_dots"]:,} dots within 3 pixels of the same registered lattice. <a href="parallel-lattice-audit.json">View independent audit ↗</a></p></div></article></div></section>
<section class="section" id="comparison"><span id="portfolio" aria-hidden="true"></span><div class="section-head"><div><div class="section-kicker">02 / Nine-site comparison</div><h2>Learn from the field.</h2><p>Exact historical files are linked for study, not resubmission. All nine fail the final-dot overlap rule against at least one of the other eight.</p></div><a class="text-link" href="audit.json">Prior independent audit ↗</a></div>
<div class="table-wrap"><table><thead><tr><th>Project</th><th>Historical reference variant</th><th>Reported figure</th><th>Forecast</th><th>3 px uniqueness</th><th>Submit?</th><th>Local format</th></tr></thead><tbody>{table}</tbody></table></div>
<p class="notice">Reported figures are owner-provided and <strong>not organizer-confirmed</strong>; no receipt ties them to the listed file hashes. Percentages are observed directional overlap of the indicated row against one peer, not a score. Format checks apply to the exact linked variant and the mirrored sample mask, not a portal verdict. Surface comparisons and other registries are not covered by this nine-file table.</p></section>
<section class="section"><div class="section-head"><div><div class="section-kicker">03 / Interpretation</div><h2>Why GEMSDOE32 stood out.</h2></div></div><div class="reason-grid">
<article class="panel"><h3>What we can verify</h3><p>In the pinned owner mirrors, H33-B2 is exactly the 44,090-dot D2.8 mask minus the 6,436 dots at or within two pixels of the mapped catalogue, leaving 37,654. Its <strong>0.2778 is an unverified owner report</strong>, not a receipt.</p></article>
<article class="panel"><h3>What we cannot infer</h3><p>Removing predictions can reduce false-positive mass, but can also lose valuable fault coverage. <a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">DrivenData staff</a> confirm known-fault pixels are masked exactly, not with a 300 m buffer; new truth can still be nearby. Hidden labels and causal ablation are unavailable, so thinning is a hypothesis, not proof of why a score changed. Whether any new method can surpass it is unknown.</p></article></div></section>
<section class="section" id="sources"><div class="section-head"><div><div class="section-kicker">04 / Source discipline</div><h2>Freshness without false certainty.</h2><p>Public leaderboard leader observed at <strong>0.4437 on 26 October 2026</strong>; this is a dated organizer-page snapshot, not a score for our file. It can change.</p></div><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Open official leaderboard ↗</a></div>
<div class="panel source-strip"><div><p><strong>Automated source health, not automated leaderboard scraping.</strong></p><p class="source-status" data-github-status>Checking GitHub source freshness; no competition website is requested by this page.</p></div><a class="text-link" href="https://www.drivendata.org/termsofuse/">Why no live leaderboard feed? ↗</a></div>
<p class="notice">DrivenData's terms prohibit automated monitoring. The status check uses only GitHub's public API. Peer mirrors are hash-pinned, not authenticated organizer originals; review their rights and the <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN source</a> before use. See the <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/research/preregistration.md">pre-registration</a> and <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/README.md">project README</a>.</p></section></div>'''
    # A concurrently developed lane is isolated; never replace its score with
    # this lane's result or compare unlike evaluators. The frozen study is negative.
    ssp1_path=ROOT/'studies/ssp1/evidence/run_card.json'
    if ssp1_path.exists():
        ssp1=json.loads(ssp1_path.read_text())
        if ssp1['decision']['ok_to_submit'] is not False:
            raise ValueError('Closed SSP1 study must not become an authorized submission')
        h=ssp1['holdout_dti'];ci=h['ci95_cluster_bootstrap']
        notice=f"""<section class="panel panel-pad" style="margin-top:18px"><div class="section-kicker">Parallel SSP1 study · research download, not a slot candidate</div><h2>New pixels. Still do not submit.</h2><p>A separate signed-scarp-profile experiment generated a new, locally format-valid TIFF. It fails the literal final-dot overlap and improvement gates. <strong>Download: yes · Submit: no.</strong></p><p>HOLDOUT-DTI {h['pooled_dti']:.5f} · 95% CI [{ci[0]:.5f}, {ci[1]:.5f}] · {e(h['evaluator_version'])} · {h['n_withheld_positives']:,} positive events. This evaluator differs from other lanes; results are not directly comparable.</p><p><a href="ssp1/executive-summary.html">New nine-site executive summary and TIFF downloads ↗</a> · <a href="ssp1/audit.html">Saved-byte and three-pass checks ↗</a></p></section>"""
        body=body.replace('<div class="wrap">','<div class="wrap">'+notice,1)

    guide=f'''<div class="wrap"><div class="page-title"><div class="section-kicker">Executive summary / submission guide</div><h1>From evidence to upload.</h1><p>What must be true before a file is considered — and why there is nothing to upload from this run.</p></div>
<div class="guide"><div><section class="panel" id="k3h1-upload"><h2>The K3-H1 file: what to do with it</h2><p><strong>Download: OK.</strong> <a href="downloads/{k3card['raster_file']}">{k3card['raster_file']}</a> (SHA-256 <code>{k3card['raster_sha256']}</code>) passes every format check and cannot trigger the “Predicted values must be in range [0, 1]” error: all pixels are finite and exactly 0 or 1, outside-footprint pixels are 0, and there is no nodata sentinel.</p><p><strong>Spend a slot: NO</strong>, if the goal is to beat 0.2778. Its PROJECTION is {k3card['projection']['value']:.3f} vs {k3card['projection']['champion_same_fit']:.3f} for the champion under the same model, and its HOLDOUT-DTI is not better than the best control. Under the literal duplicate rule it is also blocked, like every non-empty file (see below).</p><p>If you upload it anyway, for example to register a protocol-unique entry:</p><ol><li>Open the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">submissions page</a>; the limit is 3 per week (Official Rules §3.4).</li><li>Upload the .tif (or the .zip if your browser opens the TIF instead of saving it).</li><li>Paste the name <code>{k3card['submission_name']}</code> and the note <code>{k3card['submission_note']}</code>.</li><li>Save the receipt. Only that receipt makes the score ORGANIZER-CONFIRMED.</li><li>Keep the 0.2778 champion as your final selection unless something beats it on both gates (§3.5–3.6: one final submission for both rounds).</li></ol><p>Check any TIF before uploading: <code>python scripts/portal_check.py your.tif</code> prints <code>ok_to_upload</code> and the likely cause of a range error. Among 433 restored registry files, the only one with NaN inside the footprint is GEMSDOE31 <code>gemsdoe31-csdu-stepover-8cf9dc27-nan.tif</code> (2,610,312 NaN pixels). It is the one registry file that would plausibly trigger the error. <a href="k3h1.html">Details ↗</a></p></section><section class="panel warn"><h2>Current decision: <strong>DO NOT SUBMIT</strong></h2><p>No eligible candidate GeoTIFF exists. This run did not write a TIFF; a separate research TIFF already on main also failed the lattice gate at {parallel["candidate_overlap"]:.0%}. This run’s paired improvement was not established. A format-only file would not satisfy the science or selection gates.</p><a class="button" href="run-card.json">Open the run card ↗</a></section>
<section class="panel"><h2>The separate gates</h2><ol><li><strong>Science:</strong> establish the actual named lane; withhold whole segments and buffers; fit catalogue-derived features only from visible faults. Run feature canaries and a paired comparison against the current best on identical folds, with a defensible interval.</li><li><strong>Novelty:</strong> inventory current registries, test the surface before placement and the final dots afterward. A rank correlation above 0.90 or more than 70% of dots within 3 pixels of any one reference is a hard stop. The current 167-file snapshot is not complete.</li><li><strong>Format:</strong> only after clearing those gates, use the pinned shared writer. Save one <code>float32</code> band in the template CRS, shape and transform, then reopen the saved bytes and validate range, finite footprint and metadata.</li><li><strong>Selector:</strong> a format pass is not approval. Separately check the current account-specific submission cap, rights and organizer provenance; do not spend a slot automatically.</li></ol></section>
<section class="panel"><h2>Understanding the “[0, 1]” error</h2><p>The exact cause of the prior error is unknown: we do not have its rejected bytes or portal receipt. Typical causes include NaN or infinity, a nodata sentinel, scores outside [0,1], or writing the wrong band. A CRS, shape or transform mismatch is a separate format failure.</p><p>The official description calls for null/NaN outside the training-data bounds and probabilities in [0,1]. Treating the irregular mask of the unauthenticated sample mirror as the exact boundary is a <strong>conservative local policy</strong>, not a verified portal rule. One pinned writer defaults to zero outside while another defaults to NaN. Reopen the saved TIFF, inspect its mask, raw values, band count, <code>float32</code>, CRS, dimensions and transform; do not silently clip or assume either encoding guarantees acceptance. No local check proves what caused the prior portal error.</p></section>
<section class="panel"><h2>Only after explicit authorization</h2><p>Check the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official format</a>, current competition rules and account-specific cap. Select the exact validated filename and ≤140-character run-card note. Keep the file SHA-256 and the organizer's submission-page receipt together; only that receipt can support an organizer-confirmed result for that file.</p><p>No automatic upload, slot selection or expert geological review has taken place.</p></section></div>
<aside><section class="panel"><div class="section-kicker">Run summary</div><h3>Attempt</h3><p>Technical attempt 1 stopped on an orchestrator typo; fixed replay was attempt 2. Scientific settings did not change.</p><h3>Measured holdout</h3><p>{candidate['dti']:.4f} HOLDOUT-DTI · 95% CI [{candidate['ci95'][0]:.4f}, {candidate['ci95'][1]:.4f}] · {candidate['withheld_positive_pixels']:,} positives · {e(candidate['evaluator_version'])}.</p><h3>This run: file &amp; hash</h3><p>None. Its saved-byte validation is not applicable. The existing parallel research file is a duplicate, not an upload candidate.</p><h3>Current selector</h3><p>Not authorized. The submission cap was not checked for this account.</p></section>
<section class="panel"><div class="section-kicker">Next, not now</div><h3>Resolve the obstruction</h3><p>The 37,654-dot budget was recorded before candidate generation, not lowered to bypass the lattice. Any protocol change needs explicit authorization; do not secretly exempt the lattice or tune around its holes.</p></section></aside></div></div>'''
    outputs = {
        DOC/'index.html': layout('Research & evidence',body),
        DOC/'executive-summary.html': layout('Executive summary & submission guide',guide),
        DOC/'run-card.json': card_text,
        DOC/'k3h1.html': layout('K3-H1 lane report',render_markdown(ROOT/'research/k3h1-report.md')),
        DOC/'k3h1-run-card.json': k3_text,
        DOC/'data/k3h1-uniqueness-summary.json': k3_uniqueness,
        DOC/'data/focus9_family.json': (ROOT/'evidence/focus9_family.json').read_text(),
        DOC/'parallel-lattice-audit.json': parallel_text,
        ROOT/'run-card.json': card_text,
        DOC/'data/run_card.json': card_text,
        DOC/'data/run-card.json': card_text,
        DOC/'data/recovery-run-card.json': (ROOT/'evidence/recovery-run-card.json').read_text(),
        DOC/'data/registry_saturation.json': (ROOT/'evidence/registry_saturation_20261026.json').read_text(),
        DOC/'data/feature_cache_recovery.json': (ROOT/'evidence/feature_cache_recovery_20261026.json').read_text(),
        DOC/'data/shared_template_pins.json': (ROOT/'registry/shared_template_pins.json').read_text(),
        DOC/'research.html': layout('Scientific review',render_markdown(ROOT/'research/review.md')),
        DOC/'hypotheses.html': layout('Research hypotheses',render_markdown(ROOT/'research/hypotheses.md')),
        DOC/'sources.html': layout('Source register',render_markdown(DOC/'SOURCES.md')),
        DOC/'summary.html': layout('Executive summary',render_markdown(DOC/'EXECUTIVE_SUMMARY.md')),
        DOC/'submission.html': layout('Executive summary & submission guide',guide),
        DOC/'research.md': (ROOT/'research/review.md').read_text(),
        DOC/'submission.md': (DOC/'SUBMISSION_GUIDE.md').read_text(),
        **{DOC/f'{src}.md': (ROOT/f'research/{src}.md').read_text() for src in ['review','hypotheses']},
    }
    if check_only:
        stale = [str(path.relative_to(ROOT)) for path,text in outputs.items()
                 if not path.is_file() or path.read_text() != text]
        if stale:
            raise ValueError('Generated site is stale: ' + ', '.join(stale))
    else:
        for path,text in outputs.items():
            path.write_text(text)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='verify committed outputs without writing')
    build(check_only=parser.parse_args().check)
