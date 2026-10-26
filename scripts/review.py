"""Build a reproducible, offline review from pinned upstream snapshots."""
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Owner claims supplied in the request, not organizer receipts or estimates.
CLAIMS = [
 (24, 'h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan', '0.2477', 'Dotted H19-5, spacing variant'),
 (25, 'dotted-h19-5-d2-8-20261002-e56ea318af89-nan', '0.2600', 'Dotted H19-5, wider spacing'),
 (27, 'topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan', '0.2449', 'Topological gap closure on D1.5'),
 (28, 'h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan', '0.2710', 'Rung30 variant; best of the supplied scored rows'),
 (30, 'd28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca', '0.2600', 'D2.8 off-catalogue Poisson placement'),
 (31, 'h27-4-solo-d28-20261004-8acb75e1-nan', '0.2708', 'Solo D2.8 family; independence not demonstrated'),
 (32, 'h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros', '0.2778', 'H33 B2 variant; highest supplied focus-site claim'),
 (33, 'h33d-analog-tip-stepover-r30-20261004-cb490425926e', '0.2632', 'Analog tip/stepover method'),
 (36, 'anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros', '0.2750', 'Anderson/geothermal PINN-named artifact; name alone is not physics verification'),
]

def build():
 rows=[]
 for site,name,score,summary in CLAIMS:
  folder=ROOT/'evidence/upstream'/f'GEMSDOE{site}'
  meta=json.loads((folder/'tree.json').read_text())
  matches=[e['path'] for e in meta['tree']['tree'] if e['path'].endswith('.tif') and name in e['path']]
  rows.append(dict(site=f'GEMSDOE{site}',historical_file=name,owner_reported_value=score,
   evidence_class='UNVERIFIED OWNER REPORT — not a score accepted by this review',
   estimate=None,unique='NOT ESTABLISHED locally',submit=False,summary=summary,
   source=f"{meta['repository']}/tree/{meta['sha']}", matching_paths=matches))
 (ROOT/'docs/data').mkdir(parents=True,exist_ok=True)
 (ROOT/'docs/data/sites.json').write_text(json.dumps(rows,indent=2)+'\n')
 manifest=[]
 for p in sorted((ROOT/'evidence/upstream').rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':manifest.append({'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (ROOT/'evidence/snapshot_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
 tr=''.join('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in [r['site'],r['historical_file'],r['owner_reported_value']+' (unverified owner report)','Unavailable',r['unique'],'NO'])+f'<td><a href="{r["source"]}">Pinned source</a></td></tr>' for r in rows)
 summaries=''.join(f'<h3>{r["site"]}</h3><p>{html.escape(r["summary"])}. Historical file: <code>{r["historical_file"]}</code>. Local format, holdout and all-registry uniqueness checks have not run. No new upload is recommended. <a href="{r["source"]}">Review evidence</a>.</p>' for r in rows)
 body=f'''<div class="stop"><strong>ARCHIVED PRE-EXPERIMENT REVIEW.</strong> This snapshot predates the current experiment. <a href="index.html">See the current dashboard</a>.</div><h1>Executive submission review</h1><section class="stop"><h2>DO NOT SUBMIT — no candidate authorized</h2><p>No new TIFF was generated. There is no compliant download to submit from this checkout. Format validity alone never authorizes a weekly slot.</p><p>Missing lane assignment, local cached stack, validated holdout and complete registry prevent generation under your protocol. No slot was used.</p></section>
 <p>Reviewed 26 October 2026. Offline snapshot, not a live leaderboard feed. Values below are retained as unverified owner claims, NOT ORGANIZER-CONFIRMED or HOLDOUT-DTI. No accepted numerical score or score estimate is available.</p>
 <nav><a href="research.html">Research &amp; limitations</a> · <a href="submission.html">How to submit</a> · <a href="data/sites.json">Machine-readable table</a> · <a href="data/run_card.json">Run card</a></nav>
 <h2>Best historical claims across nine focus sites</h2><p>Historical names identify artifacts for study, not fresh unique submissions. No historical download is offered as a new candidate.</p><div class="scroll"><table><thead><tr><th>Site</th><th>Historical file (not an approved download)</th><th>Reported value</th><th>Estimated score</th><th>Unique?</th><th>Submit?</th><th>Evidence</th></tr></thead><tbody>{tr}</tbody></table></div>
 <h2>Why GEMSDOE32?</h2><p>It has the highest owner-reported value in the supplied focus list. That does not establish causality or prove it is best on hidden labels. The pinned upstream page explicitly calls it an owner report without a submission-page receipt. It also calls it an already-submitted duplicate family. Sparse placement can reduce false-positive mass while retaining distance-tolerant coverage; attribution to B2 masking or geology requires controlled fold-local ablations, not filenames or leaderboard anecdotes.</p><p>The upstream review also flags full-catalogue masking in a historical holdout and excessive registry overlap. We do not import upstream “promote” flags as authorization. No evidence here supports a promise to exceed the stated targets.</p>
 <h2>Per-site executive summaries</h2>{summaries}
 <h2>Priority next steps</h2><ol><li>Record the missing single-method lane before running any candidate.</li><li>Restore a shared template and cached stack with pinned provenance; reuse, do not privately fork its evaluator/writer.</li><li>Rebuild whole-segment buffered holdout features from visible faults only, and mask visible faults pixel-exactly.</li><li>Run feature canaries, paired candidate/incumbent HOLDOUT-DTI with pooled counts and segment/block bootstrap intervals.</li><li>Stop at any registry surface or final-dot threshold breach; otherwise validate saved TIFF bytes, then use a separate weekly-cap selector.</li></ol>'''
 write_page('archived-dashboard.html',body)
 write_page('archived-summary.html',body)
 for name in ('research','submission'):
  raw=(ROOT/'docs'/f'{name}.md').read_text()
  text=render_markdown_links(raw)
  write_page(name+'.html','<p class="stop"><strong>ARCHIVED PRE-EXPERIMENT SNAPSHOT.</strong> <a href="index.html">See the current dashboard</a>.</p><nav><a href="index.html">Executive summary</a></nav><article style="white-space:pre-wrap;overflow-wrap:anywhere">'+text+'</article>')

def render_markdown_links(text):
 """Escape Markdown text while rendering inline and bare HTTPS links safely."""
 pattern=re.compile(r'\[([^]\n]+)\]\((https?://[^)\s]+)\)|(https?://[^\s<>]*[^\s<>.,;:!?])')
 parts=[]
 cursor=0
 for match in pattern.finditer(text):
  parts.append(html.escape(text[cursor:match.start()]))
  if match.group(1) is not None:
   label,url=match.group(1),match.group(2)
  else:
   label=url=match.group(3)
  parts.append(f'<a href="{html.escape(url,quote=True)}">{html.escape(label)}</a>')
  cursor=match.end()
 parts.append(html.escape(text[cursor:]))
 return ''.join(parts)


def write_page(name,body):
 (ROOT/'docs'/name).write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GEMS · Evidence &amp; submission review</title><link rel="stylesheet" href="style.css"><main>'''+body+'</main></html>')

if __name__=='__main__':build()
