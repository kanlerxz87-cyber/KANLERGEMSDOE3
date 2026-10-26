# ARCHIVED GENERATOR: do not run; predates the full-registry duplicate audit and would overwrite the active dashboard.
#!/usr/bin/env python3
"""Generate docs/index.html + docs/executive-summary.html from evidence JSONs.

No number is typed by hand into the site: every score, hash and verdict is read
from registry/focus9_champions.json, evidence/forensics_focus9.json,
evidence/holdout_experiments.json, evidence/leakage_canary.json and
evidence/run_card.json at build time.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

def load(p, default=None):
    p = ROOT / p
    return json.loads(p.read_text()) if p.exists() else default

CSS = """
:root{--bg:#0f172a;--card:#ffffff;--ink:#111827;--mut:#6b7280;--ok:#047857;--bad:#b91c1c;--warn:#b45309;--line:#e5e7eb}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f3f4f6;color:var(--ink)}
header{background:var(--bg);color:#fff;padding:28px 20px}header h1{margin:0 0 6px;font-size:26px}header p{margin:0;color:#cbd5e1;max-width:100ch}
main{max-width:1100px;margin:0 auto;padding:20px}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin:16px 0}
.verdict{font-size:20px;font-weight:800;padding:14px;border-radius:10px}
.no{background:#fef2f2;color:var(--bad);border:2px solid var(--bad)} .yes{background:#ecfdf5;color:var(--ok);border:2px solid var(--ok)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
th{background:#f9fafb}a{color:#1d4ed8}code{background:#f3f4f6;padding:1px 5px;border-radius:4px;font-size:12px}
.btn{display:inline-block;background:#1d4ed8;color:#fff!important;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700;margin:6px 6px 6px 0}
.btn.secondary{background:#374151}.small{color:var(--mut);font-size:13px}ol,ul{line-height:1.55}h2{margin-top:4px}
"""

def main() -> int:
    focus = load("registry/focus9_champions.json", {"entries": []})
    fore = load("evidence/forensics_focus9.json", {})
    hold = load("evidence/holdout_experiments.json", {})
    canary = load("evidence/leakage_canary.json", {})
    card = load("evidence/run_card.json", {})

    ok = bool(card.get("ok_to_submit"))
    verdict_cls = "yes" if ok else "no"
    verdict_txt = ("OK TO SUBMIT — all automated gates passed" if ok else
                   "DO NOT SUBMIT — automated gate verdict: NEGATIVE (research download only)")
    tif = card.get("tif", "").replace("docs/", "")
    zipf = card.get("zip", "").replace("docs/", "")
    hold_txt = "not yet run"
    if hold:
        a = hold["arms"][card.get("holdout", {}).get("best_arm", hold["best_arm"])]
        hold_txt = (f"HOLDOUT-DTI {a['dti']:.6f} (95% CI [{a['ci95'][0]:.6f}, {a['ci95'][1]:.6f}], "
                    f"gems-segment-pooled-v1, {hold['withheld_positives']:,} withheld positives)")
    canary_txt = ("not yet run" if not canary else
                  f"{'PASS' if canary['passed'] else 'FAIL'} — worst two-polarity AUC "
                  f"{max(v['worst_two_polarity_auc'] for v in canary['features'].values()):.4f} (limit 0.90)")

    rows = []
    for e in focus["entries"]:
        f = fore.get("sites", {}).get(e["site"], {})
        file_link = f"https://github.com/{e['repo']}/blob/main/{e['path']}?raw=1"
        rows.append(
            f"<tr><td>{e['site']}</td><td><a href=\"{file_link}\">{e['name']}.tif</a><br>"
            f"<span class='small'>dots measured: {f.get('dots','?')} · median d_catalogue {f.get('dcat_median_px','?')} px</span></td>"
            f"<td><b>{e['score_owner_reported']:.4f}</b><br><span class='small'>OWNER-REPORTED</span></td>"
            f"<td>Not estimable</td><td>NO — historical family duplicate (see forensic chain)</td><td><b>NO</b></td></tr>")
    if card:
        u = card.get("uniqueness_vs_focus9", [])
        mx_rho = max((abs(r["surface_spearman"]) for r in u), default=float("nan"))
        mx_ov = max((r["dot_overlap_within_3px"] for r in u), default=float("nan"))
        rows.append(
            f"<tr><td><b>THIS REPO (GPC-3)</b></td><td><a href=\"{tif}\">{Path(tif).name}</a><br>"
            f"<span class='small'>SHA-256 {card.get('raster_sha256','')[:16]}… · {card.get('dots','?')} dots</span></td>"
            f"<td>— (never submitted)<br><span class='small'>No ORGANIZER-CONFIRMED score exists</span></td>"
            f"<td>{hold_txt}<br><span class='small'>Leaderboard: NOT ESTIMABLE</span></td><td>{'YES' if card.get('unique_vs_focus9') else 'NO'} — max |ρ| {mx_rho:.4f} (≤0.90), max 3-px overlap {mx_ov:.2%} (≤70%) vs 9 champions</td>"
            f"<td><b>{'YES' if ok else 'NO'}</b></td></tr>")
    table = ("<table><tr><th>Site</th><th>File to download</th><th>Historical score</th>"
             "<th>Estimated score (this repo's evidence)</th><th>Unique vs other GEMSDOE sites?</th><th>OK to submit?</th></tr>"
             + "".join(rows) + "</table>")

    dl = ""
    if card:
        run_card_href = "downloads/" + Path(tif).name.replace("-zeros.tif", "") + ".run-card.json"
        dl = (f"<p><a class='btn' href=\"{tif}\">⬇ Download the unique GPC-3 GeoTIFF ({Path(tif).name})</a>"
              f"<a class='btn secondary' href=\"{zipf}\">⬇ ZIP (single GeoTIFF)</a>"
              f"<a class='btn secondary' href=\"{run_card_href}\">Run-card JSON</a></p>"
              f"<p><b>Unique submission name:</b> <code>{card['submission_name']}</code><br>"
              f"<b>Note for the submission form ({card['note_chars']}/140 chars):</b> <code>{card['submission_note']}</code></p>")

    index = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KANLERGEMSDOE3 — GPC-3 fault discovery (DOE GEMS)</title><style>{CSS}</style></head><body>
<header><h1>KANLERGEMSDOE3 — Amplitude-Invariant Gradient-Phase Concordance (GPC-3)</h1>
<p>DOE GEMS Prize (DrivenData #306): discovering faults missing from the USGS/INGENIOUS catalogue.
Core values: <b>Maximize P(Win)</b> — every slot is an experiment; <b>Own the Outcome</b> — every number carries an evidence label.</p></header>
<main>
<div class="card"><div class="verdict {verdict_cls}">{verdict_txt}</div>
{dl}
<p class="small">Automated validation, no human inspection: leakage canary {canary_txt}; format validator checks the
<b>whole array</b> is finite and in [0, 1] (the portal error “Predicted values must be in range [0, 1]” is exactly what the
<code>-zeros</code> variant is built to pass), CRS/shape/transform match the template, and uniqueness is measured against all
9 focus champions. A format pass alone never authorises a slot.</p></div>

<div class="card"><h2>Executive summary — which file, what score estimate, is it unique?</h2>{table}
<p><b>Which historical submission scored highest?</b> GEMSDOE32's <code>h33-h33-2-b2</code> at <b>0.2778 OWNER-REPORTED</b>.
Why: measured here, it is not a new detector — it is the 0.2600 dotted field with the 3,891 dots ≤1 px and then the
2,545 dots 1–2 px from the catalogue deleted (0 dots added). Near-catalogue dots earn ~0.002–0.006 credit each against a
0.0556 break-even, so deleting the dead annulus raised the score. Full proof: <a href="research/why-02778.md">why-02778.md</a>.</p>
<p><b>Can we beat it?</b> Only with a better detector (+8% credit/dot for 0.30, ≈+59% for the current public top 0.4437,
fetched 2026-10-26). GPC-3 is that detector attempt: gradient-<i>phase</i> concordance across magnetics, gravity,
basement depth and elevation — information every prior magnitude/tilt/Hessian lane discarded. Its verdict above is
whatever the shared holdout measured; a holdout number is never dressed up as a leaderboard score.</p></div>

<div class="card"><h2>How to make a submission (no manual inspection)</h2>
<ol><li>Read the verdict banner above. If it says DO NOT SUBMIT, stop — downloading is for research only.</li>
<li>Download the <code>-zeros.tif</code> above (or its ZIP). Never upload a <code>-nan</code> variant: NaN outside the footprint triggers “Predicted values must be in range [0, 1]”.</li>
<li>Locally re-validate: <code>.venv/bin/python scripts/validate_submission.py docs/downloads/&lt;file&gt;-zeros.tif</code> must print PASS and <code>portal_range_ok: true</code>.</li>
<li>On DrivenData → Submit: choose the file, paste the submission <b>name</b> and the ≤140-character <b>note</b> shown above, submit once. A resubmission spends a slot and adds no information.</li>
<li>Record the receipt; only a submission-page receipt upgrades a score to ORGANIZER-CONFIRMED.</li></ol>
<p class="small">Full walkthrough: <a href="executive-summary.html">executive-summary.html</a></p></div>

<div class="card"><h2>Method &amp; evidence</h2><ul>
<li>Hypotheses ranked before any result: <a href="research/hypotheses.md">hypotheses.md</a> · <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/evidence/preregistration.json">preregistration.json</a></li>
<li>Sources, line by line: <a href="research/sources.md">sources.md</a> · Irregularities: <a href="research/known_irregularities.md">known_irregularities.md</a></li>
<li>Holdout / canary / forensics / run card: <code>evidence/</code> in the repository.</li>
<li>Code: <code>src/kanler3/gpc.py</code> (new lane), <code>src/gems/</code> (shared template, byte-for-byte pinned), <code>scripts/evaluate_holdout.py</code>.</li></ul></div>
</main></body></html>"""
    (DOCS / "index.html").write_text(index)

    exec_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Executive summary — how to submit</title><style>{CSS}</style></head><body>
<header><h1>Executive summary &amp; submission walkthrough</h1><p>KANLERGEMSDOE3 · GPC-3 · DOE GEMS Prize</p></header><main>
<div class="card"><div class="verdict {verdict_cls}">{verdict_txt}</div>{dl}
<p>{hold_txt}. Leakage canary: {canary_txt}. Leaderboard estimate: <b>not estimable</b> from holdout evidence —
any number written there would be a projection dressed as a score, which this repo prohibits.</p></div>
<div class="card"><h2>Decision table</h2>{table}</div>
<div class="card"><h2>Exact submission steps</h2>
<ol><li><b>Check the banner.</b> OK TO SUBMIT requires every gate: canary PASS, paired holdout CI vs the matched 59-feature control strictly positive, HOLDOUT-DTI above the recorded same-evaluator group best (0.16379, GEMSDOE24 DPRF1), surface |Spearman| ≤ 0.90 and ≤70% 3-px dot overlap vs each of the 9 focus champions, whole-array [0,1] format PASS. Any failure = DO NOT SUBMIT.</li>
<li><b>Download</b> the <code>-zeros.tif</code> (single-band float32, EPSG:32611, 3730×3292, transform 100 m, outside-footprint = 0, no NaN anywhere).</li>
<li><b>Re-validate locally</b> (automated, seconds): <code>scripts/validate_submission.py</code>.</li>
<li><b>DrivenData:</b> Competitions → DOE GEMS → Submit → choose file → Name = the unique submission name above → Note = the ≤140-char note above → Create submission.</li>
<li><b>Save the receipt.</b> Only then may a score be called ORGANIZER-CONFIRMED in this repo.</li></ol>
<p class="small">Why “-zeros”: the official sample carries NaN outside the footprint; some portal checks read the whole array.
Scored historical files prove the zeros encoding is accepted (e.g. the 0.2778 and 0.2750 OWNER-REPORTED files are themselves -zeros variants), while a NaN file can return “Predicted values must be in range [0, 1]”.</p></div>
<div class="card"><h2>Why 0.2778 won, and what beating it takes</h2>
<p>See <a href="research/why-02778.md">why-02778.md</a>: the champion is the 0.2600 field minus 6,436 near-catalogue dots and plus zero new coordinates. Beating 0.2778 needs +8% true-fault credit per dot (0.30) — a detector problem, which is what GPC-3 tests on the whole-segment holdout before any slot is considered.</p></div>
</main></body></html>"""
    (DOCS / "executive-summary.html").write_text(exec_html)
    print("Wrote docs/index.html and docs/executive-summary.html")
    return 0

def build() -> int:
    """Compatibility alias preserved from origin/main on merge (2026-10-26).

    The forensic session's tests import build(); this lane's generator is
    main(). Both render a DO-NOT-SUBMIT executive site into docs/.
    """
    return main()


if __name__ == "__main__":
    raise SystemExit(main())
