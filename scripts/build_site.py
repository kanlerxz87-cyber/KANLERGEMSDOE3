"""Render the evidence dashboard; never create, promote or submit a TIFF."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def page(title: str, content: str, *, hero: bool = False) -> str:
    title = escape(title)
    banner = '''<div class="hero shell"><div class="eyebrow">GEMS research · evidence snapshot · 26 October 2026</div>
<h1>Make the next submission count.</h1><p>A decision desk for missing-fault research, independent verification and careful use of limited competition submissions.</p>
<div class="actions"><a class="button" href="executive-summary.html">How to submit safely</a><a class="button secondary" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Open live leaderboard ↗</a></div></div>''' if hero else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | GEMS decision desk</title><link rel="stylesheet" href="style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header class="top"><div class="shell topbar"><div class="brand">GEMS<span> / </span>DECISION DESK</div><nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Submission guide</a><a href="research.html">Scientific review</a><a href="hypotheses.html">Hypotheses</a><a href="sources.html">Sources</a></nav></div>{banner}</header>
<main class="shell" id="main">{content}</main><footer><div class="shell">Evidence snapshot, not a live score feed. No file is automatically submitted. <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">View the official leaderboard</a>.</div></footer></body></html>'''


def render_markdown(source: Path) -> str:
    text = source.read_text(encoding='utf-8')
    # The published site can be served from docs/ alone; copy these small
    # evidence documents into docs/data rather than relying on parent paths.
    replacements = {
        '../evidence/registry_saturation_20261026.json': 'data/registry_saturation.json',
        '../evidence/feature_cache_recovery_20261026.json': 'data/feature_cache_recovery.json',
        '../registry/shared_template_pins.json': 'data/shared_template_pins.json',
        '../docs/audit.json': 'audit.json',
        'review.md': 'research.html',
        'hypotheses.md': 'hypotheses.html',
        'SOURCES.md': 'sources.html',
        'SUBMISSION_GUIDE.md': 'executive-summary.html',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    body = markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists'])
    # Tables are scrollable without forcing the rest of the page to overflow.
    body = body.replace('<table>', '<div class="scroll"><table>').replace('</table>', '</table></div>')
    return f'<article class="panel doc">{body}</article>'


def build():
    audit = json.loads((DOCS / 'audit.json').read_text(encoding='utf-8'))
    card = json.loads((ROOT / 'run-card.json').read_text(encoding='utf-8'))
    if card.get('verdict') != 'negative' or card.get('raster_sha256') is not None:
        raise ValueError('This evidence-only dashboard cannot publish a promoted candidate; use an independent selector and publisher.')
    rows = []
    for r in audit['rows']:
        url = f"https://github.com/buffedlizard55-lab/{r['repo']}/blob/{r['head']}/{r['file']}"
        site_path = {'GEMSDOE31': 'docs/', 'GEMSDOE32': 'docs/index.html', 'GEMSDOE36': 'docs/'}.get(r['repo'], '')
        site_url = f"https://buffedlizard55-lab.github.io/{r['repo']}/{site_path}"
        fmt = 'Meets local mask policy' if r['local_validation']['format_pass'] else 'Does not meet local mask policy'
        overlap = f"{r['max_overlap_3px']:.2%} max directed overlap"
        rows.append(f'''<tr><td><a href="{escape(site_url)}">{escape(r['repo'])}</a></td>
<td class="file"><a href="{escape(url)}">{escape(Path(r['file']).name)}</a><small>Historical reference variant; score is not bound to these bytes.</small></td>
<td>{r['owner_reported_leaderboard_score']:.4f}<small>Unverified user/owner report</small></td><td>Not estimable</td>
<td><strong>No</strong><small>{overlap}; exceeds stop</small></td><td><span class="pill stop-pill">NO</span></td>
<td>{escape(fmt)}<small>Not a portal verdict</small></td></tr>''')

    content = '''<section class="status" aria-labelledby="decision"><div class="label">Current decision</div><h2 id="decision">DO NOT SUBMIT — no eligible new TIFF</h2>
<p><strong>Approved download: none.</strong> No new candidate has passed the required holdout and uniqueness gates. Historical files below are for learning, not for upload.</p>
<p>The assigned method lane is missing. A continuous registry diagnostic also triggers the shared template’s literal overlap stop for every nonempty footprint candidate; its inclusion as a dot raster is unresolved. <a href="research.html">See the evidence and caveat</a>.</p></section>
<div class="cards"><div class="card"><span class="kicker">Candidate estimate</span><strong>Not estimable</strong><small>No compliant holdout or organizer receipt.</small></div><div class="card"><span class="kicker">Priority-site winners</span><strong>All fail overlap stop</strong><small>Measured against other historical winners.</small></div><div class="card"><span class="kicker">Shared inputs</span><strong>Cache recovered, not authenticated</strong><small>Participant mirror; sample identity and license unresolved.</small></div></div>
<section class="panel"><h2>Priority-site executive comparison</h2><p>These are the highest historical items in the supplied list, not approved submissions. Values are unverified user/owner reports; no receipt links them to the referenced TIFF bytes. A local sample-mask result is not an organizer rejection or acceptance.</p><div class="scroll"><table><thead><tr><th>Site</th><th>Historical file reference</th><th>Historical claim</th><th>Estimate</th><th>Unique vs peers?</th><th>OK to submit?</th><th>Local format check</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table></div>
<div class="note">All 72 directed winner-to-winner 3-pixel comparisons exceed the 70% stop; the minimum is 86.72%. Continuous-surface correlations and the complete current registry remain unchecked. <a href="audit.json">Inspect the measured audit</a>.</div></section>
<div class="columns"><section class="panel"><h2>Why did the H33 family stand out?</h2><p>Its reported historical value is the highest in the supplied nine-site list. Sparse thinning might reduce uncredited predictions, but can also reduce fault coverage. There is no receipt or controlled ablation to prove why it performed as reported.</p><p>DrivenData staff confirm the known-fault mask is pixel-exact, without a 300 m buffer. Nearby unmasked predictions can be penalized, but new-fault truth can also occur nearby. <a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">Read the clarification</a>.</p></section>
<section class="panel"><h2>What must happen next?</h2><ol><li>Resolve the missing lane and continuous-diagnostic registry scope without relaxing the stop locally.</li><li>Verify data/code licenses and the true organizer sample; the mirrored sample differs from the published description.</li><li>Refresh the complete registry, then run canaries and paired spatial holdout before a separate selector considers a slot.</li></ol><p><a href="hypotheses.html">See the ranked research hypotheses →</a></p></section></div>
<section class="panel"><h2>Rules, sources and confidence</h2><p>The organizer requires a single-band float32 GeoTIFF on the matching grid, with probabilities in [0,1] and null/NaN outside the bounds. The rules PDF describes three submissions per week; the current account quota is not known. The same selected submission is used in both prize rounds.</p><p>The shared cache is byte-matched to a participant template, not independently authenticated to the organizer. The previous portal range error cannot be diagnosed without its exact file. <a href="sources.html">Review official sources and limitations →</a></p><p><a href="run-card.json">Current run card</a> · <a href="data/registry_saturation.json">Registry certificate</a> · <a href="data/feature_cache_recovery.json">Cache recovery receipt</a></p></section>'''
    (DOCS / 'index.html').write_text(page('Executive summary', content, hero=True), encoding='utf-8')

    # Keep one authoritative run card; both site paths are deterministic copies.
    data_dir = DOCS / 'data'
    data_dir.mkdir(exist_ok=True)
    card_text = json.dumps(card, indent=2, allow_nan=False) + '\n'
    for p in (DOCS / 'run-card.json', data_dir / 'run_card.json'):
        p.write_text(card_text, encoding='utf-8')
    for src, dst in [
        ('evidence/registry_saturation_20261026.json', 'registry_saturation.json'),
        ('evidence/feature_cache_recovery_20261026.json', 'feature_cache_recovery.json'),
        ('registry/shared_template_pins.json', 'shared_template_pins.json'),
    ]:
        (data_dir / dst).write_text((ROOT / src).read_text(encoding='utf-8'), encoding='utf-8')
    # Keep markdown copies for auditable text; render accessible HTML subpages.
    for src, md_name, html_names, title in [
        (ROOT / 'research/review.md', 'review.md', ['research.html'], 'Scientific review'),
        (ROOT / 'research/hypotheses.md', 'hypotheses.md', ['hypotheses.html'], 'Research hypotheses'),
        (DOCS / 'SOURCES.md', None, ['sources.html'], 'Source register'),
        (DOCS / 'SUBMISSION_GUIDE.md', None, ['executive-summary.html', 'submission.html'], 'Submission guide'),
        (DOCS / 'EXECUTIVE_SUMMARY.md', None, ['summary.html'], 'Executive summary'),
    ]:
        if md_name:
            (DOCS / md_name).write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
        html = page(title, render_markdown(src))
        for name in html_names:
            (DOCS / name).write_text(html, encoding='utf-8')
    (DOCS / 'research.md').write_text((ROOT / 'research/review.md').read_text(encoding='utf-8'), encoding='utf-8')
    (DOCS / 'submission.md').write_text((DOCS / 'SUBMISSION_GUIDE.md').read_text(encoding='utf-8'), encoding='utf-8')


if __name__ == '__main__':
    build()
