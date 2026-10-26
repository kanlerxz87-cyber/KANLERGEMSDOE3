#!/usr/bin/env python3
"""Render the honest, fail-closed static Pages site from recorded evidence."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ESC = html.escape


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def wrapper(title, active, body, *, root=False):
    p = '' if root else '../'
    def nav(label, href, key):
        current = ' aria-current="page"' if active == key else ''
        return f'<a href="{p}{href}"{current}>{label}</a>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="An evidence-first research workspace for the DOE GEMS Prize. No candidate is currently cleared for submission.">
<title>{ESC(title)} · GEMS Signal</title><link rel="stylesheet" href="{p}assets/style.css"><script src="{p}assets/site.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="shell header-inner">
<a class="brand" href="{p}index.html" aria-label="GEMS Signal home"><span class="brand-mark" aria-hidden="true"><svg width="21" height="21" viewBox="0 0 24 24" fill="none"><path d="M4 17.5 9.2 8l3.2 5.3 2.5-3.8L20 17.5M5 20h14" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="15" cy="5" r="1.5" fill="currentColor"/></svg></span><span><span class="brand-name">GEMS SIGNAL</span><span class="brand-sub">Fault discovery workspace</span></span></a>
<nav aria-label="Main navigation">{nav('Overview','index.html','overview')}{nav('Executive summary','docs/executive-summary.html','summary')}{nav('Research & sources','docs/research.html','research')}<a class="nav-external" href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Challenge ↗</a></nav></div></header>
<main id="main">{body}</main><footer><div class="shell footer-inner"><div><strong>GEMS SIGNAL</strong> &nbsp;·&nbsp; Evidence before submissions.<br>Built for reproducible, responsible geothermal fault research.</div><div><a href="{p}docs/protocol.md">Standing protocol</a> &nbsp;·&nbsp; <a href="{p}docs/sources.md">Sources</a> &nbsp;·&nbsp; <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3">GitHub ↗</a></div></div></footer></body></html>'''


def benchmark(snapshot):
    value = ESC(snapshot['public_value'])
    participant = ESC(snapshot['participant'])
    stamp = ESC(snapshot['observed_utc'])
    return f'''<section class="benchmark" aria-label="Public leaderboard snapshot" data-public-feed data-snapshot-utc="{ESC(snapshot['observed_utc'], quote=True)}">
<div><p class="label">Public leaderboard · rank 1</p><div class="value"><span data-feed-score>{value}</span> <small>official page</small></div></div>
<div><p class="label">Participant</p><div class="value" style="font-size:17px" data-feed-participant>{participant}</div></div>
<div class="detail"><span data-feed-state>Dated snapshot · scheduled feed not yet verified</span><br>Page response received <span data-feed-date>{stamp}</span><br>Not a receipt for any project file.</div>
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">View leaderboard ↗</a></section>'''


def focus_table(anchors, audit, claim_link):
    rows = []
    for item in anchors:
        site = item['site']
        result = audit['references'][site]
        if result['sha256'] != item['sha256'] or result['claimed_value_not_score'] != item['claimed_value']:
            raise ValueError(f'Config/evidence mismatch for {site}')
        peer = result['max_overlap_other_site']
        overlap = result['max_forward_overlap_3px'] * 100
        exact = ', '.join(result['exact_support_matches'])
        exact_note = f'Identical support to {exact}' if exact else f'{overlap:.1f}% near {peer}'
        source = f"https://github.com/buffedlizard55-lab/{site}/blob/{item['reviewed_commit']}/{item['path']}"
        name = item['path'].split('/')[-1]
        conflict = '<span class="muted-line">Conflicting peer records</span>' if item.get('claim_conflict') else ''
        rows.append(f'''<tr><td><a class="site-name" href="https://buffedlizard55-lab.github.io/{ESC(site)}/">{ESC(site)} ↗</a><span class="muted-line" data-site-head="{ESC(site)}" data-reviewed-commit="{ESC(item['reviewed_commit'])}">Pinned source review</span></td>
<td><a class="file-link" href="{ESC(source, quote=True)}">{ESC(name)} ↗</a><span class="muted-line">Historical reference only</span></td>
<td><span class="claim">{item['claimed_value']:.4f}</span><span class="muted-line">USER/OWNER-REPORTED · UNVERIFIED</span>{conflict}</td>
<td>—<span class="muted-line">Not run · n — · CI —</span></td><td><span class="no">No</span><span class="muted-line">{ESC(exact_note)}</span></td><td><strong class="no">NOT OK</strong><span class="muted-line">Historical / duplicate</span></td></tr>''')
    return '''<div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Historical TIFF</th><th scope="col">Reported value</th><th scope="col">HOLDOUT-DTI</th><th scope="col">Unique vs 9 anchors?</th><th scope="col">Submit?</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table><div class="table-foot">Reported values appear in the user’s list and a community portfolio, not verified submission receipts; <a href="{CLAIM_LINK}">claim conflicts</a> remain unresolved; this is not an exhaustive search of every version. No holdout was run: evaluator version, withheld-positive count and 95% CI are unavailable. The prospective pinned evaluator is gems57-pooled-hide-v2. “No” applies the directional 3-pixel / 70% rule against these nine historical anchors only; it is not a complete fleet audit. Historical TIFFs are for research, not a new submission.</div></div>'''.replace('{CLAIM_LINK}', ESC(claim_link, quote=True))


def sources_cards():
    sources = [
      ('Official problem & metric', 'https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/', 'Task, DTI, grid and submission requirements.'),
      ('USGS GeoDAWN', 'https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and', 'Magnetic and radiometric survey data; CC0 record.'),
      ('GDR INGENIOUS', 'https://gdr.openei.org/submissions/1391', 'Geothermal datasets and public license information.'),
    ]
    return '<div class="source-list">' + ''.join(f'<div class="source-card"><a href="{ESC(url, quote=True)}">{ESC(name)} ↗</a><p>{ESC(desc)}</p></div>' for name,url,desc in sources) + '</div>'


def render():
    pins = load('config/focus_anchors.json')['anchors']
    audit = load('evidence/focus_anchor_audit.json')
    preflight = load('evidence/preflight.json')
    card = load('evidence/run_card.json')
    snapshot = load('evidence/leaderboard_snapshot.json')
    if len(pins) != 9 or len(audit['references']) != 9:
        raise ValueError('Expected the nine reviewed anchor references')
    # This build is explicitly a negative release. A new release needs a newly
    # implemented, reviewed selector rather than changing a label in JSON.
    if (card['verdict'] != 'negative' or card['raster_sha256'] is not None or
        preflight['preplacement_verdict'] != 'STOP' or
        not preflight['witnesses']['registry_dense']['universal_blocker']):
        raise ValueError('This negative-status site cannot render unverified promotion')
    if snapshot['rank'] != 1 or not 0 <= float(snapshot['public_value']) <= 1:
        raise ValueError('Invalid dated leaderboard snapshot')
    table_home = focus_table(pins, audit, 'docs/claims_audit.md')
    table_summary = focus_table(pins, audit, 'claims_audit.md')
    bench = benchmark(snapshot)
    ranks = snapshot['top_ten']
    if (len(ranks) != 10 or [x['rank'] for x in ranks] != list(range(1, 11)) or
        ranks[0]['public_value'] != snapshot['public_value'] or
        ranks[0]['participant'] != snapshot['participant'] or
        any(not 0 <= float(row['public_value']) <= 1 for row in ranks) or
        any(float(ranks[i]['public_value']) < float(ranks[i+1]['public_value']) for i in range(9))):
        raise ValueError('Invalid top-ten snapshot')
    rank_list = '<ol class="rank-list">' + ''.join(
        f'<li><span><span class="rank">{x["rank"]:02d}</span>{ESC(x["participant"])}</span><span class="score">{ESC(x["public_value"])}</span></li>'
        for x in ranks) + '</ol>'
    home = f'''<div class="shell"><div class="utility"><span><i class="dot"></i> DOE GEMS Prize · Research workspace</span><span class="hide-small">Evidence updated 26 Oct 2026</span></div>
<section class="hero"><div><p class="eyebrow">A more deliberate path to discovery</p><h1>Better evidence.<br><em>Smarter submissions.</em></h1>
<p class="hero-copy">A research workspace for finding geothermal fault signals—and knowing when a prediction is actually ready for the leaderboard.</p>
<div class="actions"><a class="button primary" href="docs/executive-summary.html">Read executive summary <span aria-hidden="true">↗</span></a><a class="button secondary" href="#focus-sites">Explore the nine sites <span aria-hidden="true">↓</span></a></div>
<p class="subtle-note">Independent analysis · No competition slot used in this session</p></div>
<aside class="readiness" aria-labelledby="readiness-title"><div class="card-heading"><div><p class="card-kicker">Submission readiness</p><h2 id="readiness-title">No file cleared yet</h2></div><span class="badge stop">Do not submit</span></div>
<div class="card-alert"><strong>Download is unavailable for now.</strong><p>The literal registry check stops every nonempty candidate before placement. No unique TIFF or holdout estimate has been generated.</p></div>
<ul class="gate-list"><li><span>Registry uniqueness</span><strong class="fail">STOP · duplicate blocker</strong></li><li><span>Holdout &amp; leakage canaries</span><strong>NOT RUN</strong></li><li><span>Saved TIFF validation</span><strong>NO CANDIDATE</strong></li><li><span>Weekly slot selection</span><strong>SEPARATE STEP</strong></li></ul>
<div class="card-foot"><button class="button disabled" type="button" disabled aria-describedby="download-reason">↓ &nbsp; Download submission TIFF</button><p id="download-reason" class="subtle-note">Disabled until every required gate is met. <a href="docs/analysis.html">See the proof ↗</a></p></div></aside></section>
{bench}
<section class="section compact"><div class="section-top"><div><p class="eyebrow">The state of the work</p><h2>Evidence at a glance</h2><p>What has actually been restored, verified and measured—without projecting a score.</p></div><a class="text-link" href="evidence/run_card.json">View run card ↗</a></div>
<div class="stats"><div class="stat"><div class="stat-label"><span class="stat-icon">↗</span> Data</div><div class="stat-value">19 bands restored</div><div class="stat-note">Hash-pinned mirror; origin not independently authenticated.</div></div>
<div class="stat"><div class="stat-label"><span class="stat-icon">◇</span> New candidate</div><div class="stat-value">None generated</div><div class="stat-note">Pre-placement uniqueness stop was observed.</div></div>
<div class="stat"><div class="stat-label"><span class="stat-icon">◫</span> Holdout estimate</div><div class="stat-value">Not available</div><div class="stat-note">No candidate, no canaries and no evaluation.</div></div>
<div class="stat"><div class="stat-label"><span class="stat-icon">✓</span> Slots used</div><div class="stat-value">0 this session</div><div class="stat-note">Selection remains a separate step.</div></div></div></section>
<div class="divider"></div><section class="section" id="focus-sites"><div class="section-top"><div><p class="eyebrow">Portfolio review · nine focus sites</p><h2>What the historical files show</h2><p>The requested high values are user-reported claims—not verified scores. None is a new, unique submission.</p></div><a class="text-link" href="docs/executive-summary.html#comparison">Open full summary ↗</a></div>{table_home}</section>
<section class="section compact" style="padding-top:0"><div class="insight-grid"><article class="insight tinted"><p class="eyebrow">The critical finding</p><h3>One prior covers the entire footprint.</h3><p>Under the shared rule that treats every positive probability as a dot, the registered dense surface puts any nonempty candidate inside its 3-pixel neighborhood. The stop is mathematical, not a lack of effort.</p><a class="text-link" href="docs/analysis.html#why-the-run-stopped">Read the uniqueness analysis ↗</a></article>
<article class="insight"><p class="eyebrow">A question worth testing</p><h3>Why did thinning appear to help?</h3><p>The B2 reference is exactly the D2.8 support after removing near-catalogue dots. That is a measurable lineage, not proof of its reported score or hidden-label causality.</p><a class="text-link" href="docs/analysis.html">Read the analysis ↗</a></article></div></section>
<section class="section compact" style="padding-top:0"><div class="section-top"><div><p class="eyebrow">Grounded in official sources</p><h2>Start from what can be verified.</h2></div><a class="text-link" href="docs/research.html">Explore the research ↗</a></div>{sources_cards()}</section></div>'''
    summary = f'''<div class="shell"><div class="page-intro"><p class="eyebrow">Executive summary / submission guide</p><h1>Make the next submission <em>count.</em></h1><p>Current decision: <strong>DO NOT SUBMIT.</strong> There is no newly generated, protocol-unique TIFF and no defensible holdout estimate.</p></div>
<div class="notice"><strong>Important:</strong> a local format pass is not a holdout win, a uniqueness clearance, an organizer receipt or permission to use a weekly slot. No file is approved in this session.</div>
<section class="section compact"><div class="section-top"><div><p class="eyebrow">At a glance</p><h2>What is ready today?</h2><p>The evidence is downloadable; the requested submission is not.</p></div></div>
<div class="detail-grid"><article class="detail-card"><h3>Submission TIFF</h3><p><strong>Not generated.</strong> The universal pre-placement duplicate witness requires a stop. An existing TIFF with a new name would not satisfy the protocol.</p><button class="button disabled" disabled>↓ &nbsp; Download submission TIFF</button></article>
<article class="detail-card"><h3>Run card &amp; verification</h3><p>Model, canaries, holdout and final-file validator are marked not run; no metrics have been invented.</p><a class="button secondary" href="../evidence/run_card.json">Download JSON run card ↗</a></article></div></section>
{bench}
<section class="section compact"><div class="section-top"><div><p class="eyebrow">Broader leaderboard / dated snapshot</p><h2>The public top ten</h2><p>Organizer-published page values received {ESC(snapshot['observed_utc'])}; the page may have been cached. This list does not refresh with the rank-one feed and does not identify submission files.</p></div><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Check current rankings ↗</a></div><div class="detail-card">{rank_list}</div></section>
<section class="section" id="comparison"><div class="section-top"><div><p class="eyebrow">Nine-site comparison</p><h2>Historical references, not recommendations</h2><p>Click a filename to inspect its pinned GitHub version. The user-supplied values are claims; a holdout estimate does not exist for a new file.</p></div><a class="text-link" href="../evidence/focus_anchor_audit.json">Download pairwise audit ↗</a></div>{table_summary}</section>
<div class="divider"></div><section class="section"><div class="section-top"><div><p class="eyebrow">When a file is actually approved</p><h2>How to submit</h2><p>These steps are for a future candidate after the automatic gates and separate selector have passed.</p></div></div>
<div class="detail-grid"><div class="detail-card"><ol class="steps"><li><strong>Check the decision banner.</strong> Proceed only if the site shows an approved unique file, a same-evaluator holdout win, leakage checks, a saved-byte validator and separate slot selection.</li><li><strong>Download the exact approved TIFF.</strong> Keep the filename and SHA-256 from the run card. A renamed old TIFF is not a unique submission.</li><li><strong>Open the competition submission page.</strong> Sign in to DrivenData, choose Submit → Make new submission, and upload the one TIFF or its single-TIFF ZIP.</li><li><strong>Use the provided short note.</strong> Copy the candidate’s name and note (≤140 characters) when available. Check the portal’s current submission allowance.</li><li><strong>Preserve the official receipt.</strong> Keep the portal result and local file hash together. A leaderboard position alone does not identify the file.</li></ol></div>
<div class="detail-card"><p class="eyebrow">Format safety</p><h3>Avoid the [0, 1] error</h3><p>The local inspection checks the actual TIFF bytes: one float32 band, grid match, finite values in [0,1], and no NaN or masked cells within the footprint. It rejects out-of-range sentinels instead of clipping them.</p><p>The shared writer’s all-finite exterior is a conservative local policy; the official problem description permits null/NaN outside the bounds. We cannot infer the cause of the earlier portal error without the failed file or guarantee how the portal handles exterior values.</p><p><span class="code">python scripts/verify_submission.py /path/to/file.tif</span></p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Read official format ↗</a></div></div></section>
<section class="section compact" style="padding-top:0"><div class="insight-grid"><article class="insight tinted"><p class="eyebrow">The reported B2 result</p><h3>What we know</h3><p>The 37,654-dot B2 support equals the 44,090-dot D2.8 support after removing pixels within 200 m of the mirrored fault catalogue. This is a measured relationship—not proof of score or causality.</p><a class="text-link" href="analysis.html">Read the full explanation ↗</a></article><article class="insight"><p class="eyebrow">The next blocker</p><h3>Resolve the literal registry rule.</h3><p>A dense prior makes the 70% threshold impossible for every nonempty file. The method lane also needs to be explicit. No exemptions have been silently applied.</p><a class="text-link" href="../evidence/preflight.json">Inspect the proof ↗</a></article></div></section></div>'''
    research = f'''<div class="shell"><div class="page-intro"><p class="eyebrow">Research &amp; provenance</p><h1>Questions first.<br><em>Claims second.</em></h1><p>Geology guides our hypotheses; spatially separated evidence and transparent uncertainty decide what proceeds.</p></div>
<div class="notice"><strong>No experiment run:</strong> the current prompt did not assign a specific method lane, and the literal registry preflight already requires a stop. These are proposals, not discoveries or scores.</div>
<section class="section compact"><div class="section-top"><div><p class="eyebrow">Preregistered ideas</p><h2>Four directions to investigate</h2><p>Ranked qualitatively by expected usefulness and cost; novelty is limited to this checkout.</p></div><a class="text-link" href="hypotheses.md">Full hypotheses &amp; caveats ↗</a></div>
<div class="detail-grid"><article class="detail-card"><p class="eyebrow">01 / Moderate CPU</p><h3>Magnetic–gravity interface under cover</h3><p>Test multi-scale edge persistence and axial alignment with cover-dependent gating. A lithologic contact or survey striping can mimic the signal.</p></article>
<article class="detail-card"><p class="eyebrow">02 / Moderate CPU</p><h3>Topographic step with gravity support</h3><p>Compare step profiles at multiple scales with an independent subsurface gradient. Terraces, shorelines and rock contacts are plausible mimics.</p></article>
<article class="detail-card"><p class="eyebrow">03 / Low–moderate CPU</p><h3>Strain transition at a magnetic contact</h3><p>Use coarse geodetic strain as a contextual prior, not a fault label. GPS interpolation and geological contacts can cause similar patterns.</p></article>
<article class="detail-card"><p class="eyebrow">04 / Deferred</p><h3>Shallow thermal-gradient corroboration</h3><p>GDR lists public probe data, but download, coverage and field suitability were not verified here. Soil moisture and seasonal heating are mimics.</p></article></div></section>
<section class="section compact"><div class="section-top"><div><p class="eyebrow">Trusted starting points</p><h2>Trace every claim to its source.</h2><p>Official references establish data and rules; they do not validate the proposed hypotheses.</p></div><a class="text-link" href="sources.md">Full source register ↗</a></div>{sources_cards()}</section>
<section class="section compact" style="padding-top:0"><div class="insight-grid"><article class="insight"><p class="eyebrow">Data provenance</p><h3>A mirror is not an official receipt.</h3><p>The 19-band stack and reference files were restored from immutable public GitHub mirrors with SHA-256 checks. A fresh authenticated download was not available. The mirrored sample contains fault labels despite the official description of an absence-only sample.</p><a class="text-link" href="../evidence/preflight.json">View preflight ↗</a></article><article class="insight"><p class="eyebrow">Reproducibility</p><h3>The shared tools stay shared.</h3><p>The scoring module, writer and uniqueness rule are fetched byte-for-byte. The fold builder still needs an upstream whole-segment buffer fix; the format wrapper adds a validity-mask check. No private metric fork is used.</p><a class="text-link" href="protocol.md">Read the protocol ↗</a></article></div></section></div>'''
    analysis = '''<div class="shell"><div class="page-intro"><p class="eyebrow">Evidence &amp; analysis</p><h1>What the pixels <em>actually say.</em></h1><p>A technical reading of the registry stop, the reported B2 value and the limits of the local evidence.</p></div>
<section class="section compact" id="why-the-run-stopped"><div class="prose"><p class="eyebrow">01 / Uniqueness preflight</p><h2>Why the run stopped</h2><p>The pinned shared rule treats each finite value greater than zero as a dot. A registered dense surface is positive at every one of the 5,167,373 cells in the mirrored footprint. Every nonempty in-footprint candidate is therefore within three pixels of that surface at <strong>100% of its dots</strong>, exceeding the &gt;70% cutoff.</p><p>A second lattice witness covers 5,160,724 footprint cells within three pixels. With 37,654 candidate dots, at most 6,649 can be outside that neighborhood, so overlap is at least 82.34%. The dense witness blocks every nonempty budget; the lattice is an independent illustrative bound at that specific budget. These are local measurements under the literal rule, not an organizer decision or a complete registry scan.</p><p><a href="../evidence/preflight.json">View the preflight evidence ↗</a> · <a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/822a0ce5546c7b6749cdd82eb145b6b3e616603d/src/gems57/uniqueness.py">Pinned shared rule ↗</a></p></div></section>
<div class="divider"></div><section class="section compact"><div class="prose"><p class="eyebrow">02 / GEMSDOE32 H33–H33-2–B2</p><h2>A plausible mechanism, not a receipt</h2><p>The B2 file has 37,654 positive cells. Its support is exactly the 44,090-cell D2.8 reference after removing 6,436 dots within two 100 m pixels of the mirrored known-fault catalogue; no pixels were added. The reported <strong>0.2778</strong> is an owner/user claim without a linked organizer receipt. The public leaderboard does not identify TIFF filenames.</p><p>The organizer masks known faults pixel-exactly, so removing nearby dots could improve the index if they are false positives or redundant, while distant edges may capture unmapped structure. It could also remove valid nearby extensions or splays. Both explanations are scientifically plausible; neither the hidden labels nor the counterfactual score are available here.</p><p>For binary dots, with weighted true-positive credit <em>T</em>, dot count <em>S</em>, dot-side credit <em>M</em>, and truth count <em>G</em>, the official denominator is <span class="code">0.2(T + S − M) + 0.8G</span>. It is not generally <span class="code">0.2S + 0.8G</span>: truth-side and dot-side credit need not be equal. No improvement has been demonstrated using a common, leakage-controlled evaluator.</p><p><a href="../evidence/anchor_lineage.json">View the lineage measurement ↗</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official metric ↗</a></p></div></section>
<div class="divider"></div><section class="section compact"><div class="prose"><p class="eyebrow">03 / Reproducibility caveats</p><h2>Know what each check proves.</h2><ul><li>Public-mirror SHA-256 checks prove byte identity, not organizer-authenticated origin. The mirrored sample contains positive cells matching known faults, unlike the official total-absence example description.</li><li>The format inspection tests saved bytes against that mirror and the unchanged shared local gates. It is not a portal receipt, uniqueness decision or promotion.</li><li>The shared fold builder needs an upstream whole-segment, local-buffer correction; its scoring function alone cannot verify leakage-safe folds. The shared metric module also has a documentation error: the incremental truth credit can exceed one dot’s self-credit when several truth cells are covered. Its exact two-sided implementation is not shown to be wrong by that comment; the upstream wording needs correction. No private fork was made.</li><li>Evidence is a dated snapshot. A source HEAD change calls for re-audit; a live public rank does not establish which file produced it.</li></ul><p><a href="analysis.md">Detailed technical notes ↗</a> · <a href="sources.md">Source register ↗</a></p></div></section></div>'''
    return {'index.html': wrapper('Overview','overview',home,root=True),
            'docs/executive-summary.html': wrapper('Executive summary','summary',summary),
            'docs/research.html': wrapper('Research & sources','research',research),
            'docs/analysis.html': wrapper('Evidence & analysis','research',analysis)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='Fail if generated pages are missing or stale')
    args = ap.parse_args()
    try:
        pages = render()
        mismatches = []
        for path, content in pages.items():
            target = ROOT / path
            content += '\n'
            if args.check:
                if not target.exists() or target.read_text(encoding='utf-8') != content:
                    mismatches.append(path)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
        if mismatches:
            raise ValueError('Generated pages stale: ' + ', '.join(mismatches))
        print(f'{"Checked" if args.check else "Built"} {len(pages)} fail-closed Pages documents')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'SITE BUILD FAILED: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
