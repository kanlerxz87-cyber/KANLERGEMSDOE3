#!/usr/bin/env python3
"""Build the archived CADG study pages without exposing a failed candidate as a download."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/cadg-submod"
CARD_PATH = ROOT / "evidence/cadg-submod-run-card.json"


def build() -> None:
    card = json.loads(CARD_PATH.read_text())
    hold = card["holdout"]
    overlap = float(card["final_dot_overlap_3px"])
    authorized = (
        card.get("verdict") == "promote"
        and card.get("slot_authorized") is True
        and card.get("template_provenance_verified") is True
        and card.get("registry_complete") is True
        and overlap <= 0.70
    )
    status = "ELIGIBLE FOR SEPARATE SELECTION" if authorized else "DO NOT SUBMIT"
    artifact = escape(str(card.get("submission_name") or "No candidate"))
    digest = escape(str(card.get("raster_sha256") or "not available"))
    note = escape(str(card.get("submission_note") or "No submission note"))
    why = []
    if card.get("verdict") != "promote":
        why.append("The recorded automated verdict is negative.")
    if card.get("slot_authorized") is not True:
        why.append("No separate selector authorized a competition slot.")
    if card.get("template_provenance_verified") is not True:
        why.append("Organizer-template provenance is not verified.")
    if card.get("registry_complete") is not True:
        why.append("The registry is not complete.")
    if overlap > 0.70:
        why.append(f"The recorded candidate-to-lattice dot overlap is {overlap:.2%}, above the strict 70% duplicate stop.")
    if not why:
        why.append("No blocking release check was recorded.")
    why_html = "".join(f"<li>{escape(item)}</li>" for item in why)
    holdout = (
        f"HOLDOUT-DTI {hold['value']:.6f} (95% CI "
        f"[{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], "
        f"{hold['withheld_positives']:,} withheld positives, "
        f"{escape(hold['evaluator_version'])})"
    )
    download_state = (
        f'<p><a download href="downloads/{artifact}.tif">Download candidate GeoTIFF</a></p>'
        if authorized
        else '<p class="blocked"><strong>Download unavailable — DO NOT SUBMIT.</strong> '
             'The preserved raster is a research artifact, not a qualified competition file.</p>'
    )
    OUT.mkdir(parents=True, exist_ok=True)
    index = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archived CADG experiment · KANLERGEMSDOE3</title>
<style>body{{max-width:960px;margin:2rem auto;padding:0 1rem;font:16px/1.6 system-ui;color:#172b3a;background:#f4f7f9}}main,header,section{{background:white;border:1px solid #d9e2e8;border-radius:12px;padding:1.2rem;margin:1rem 0}}.blocked{{border-left:6px solid #a43b32;background:#fff3f1;padding:1rem}}code{{overflow-wrap:anywhere;background:#eef3f6;padding:.12rem .3rem}}a{{color:#075f65}}</style></head>
<body><header><p><a href="../index.html">← Current executive desk</a> · <a href="../executive-summary.html">Submission instructions</a> · <a href="run-card.json">Archived run card</a></p>
<h1>Archived CADG experiment — {status}</h1>
<p>This page records an earlier research lane; it is not the current project approval screen. Format validation and a positive holdout result do not override the literal registry duplicate rule or authorize a submission slot.</p></header>
<main><section><h2>Decision</h2><p class="blocked"><strong>{status}.</strong> The saved candidate fails release requirements. No competition upload is authorized.</p><ul>{why_html}</ul>{download_state}</section>
<section><h2>Archived evidence (not a leaderboard score)</h2><p>{holdout}</p><p>Candidate identifier: <code>{artifact}</code></p><p>Saved-raster SHA-256 in the archived card: <code>{digest}</code></p><p>Archived submission note: <code>{note}</code></p><p>These historical research measurements are not current validation, an organizer-confirmed score, or an estimate of leaderboard performance.</p></section>
<section><h2>What would be required before any future upload</h2><ol><li>Resolve the complete registry and the literal duplicate test; do not waive the registered lattice.</li><li>Use the centrally corrected shared evaluator and authenticated canonical data/cache.</li><li>Run the assigned-lane holdout against a same-evaluator incumbent, including feature canaries and surface/final-dot checks.</li><li>Obtain independent selector authorization and verify the current account cap. A local TIFF validator alone is not permission to upload.</li></ol></section></main></body></html>'''
    guide = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Submission status · CADG archive</title>
<style>body{{max-width:900px;margin:2rem auto;padding:0 1rem;font:16px/1.6 system-ui;color:#172b3a}}section{{border:1px solid #d9e2e8;border-radius:12px;padding:1.2rem;margin:1rem 0}}.blocked{{border-left:6px solid #a43b32;background:#fff3f1;padding:1rem}}a{{color:#075f65}}</style></head><body>
<p><a href="index.html">← Archived experiment</a> · <a href="../index.html">Current executive desk</a></p><h1>Competition submission instructions</h1>
<section class="blocked"><h2>{status}</h2><p>No TIFF from this archived lane is approved for download or upload. Its recorded overlap exceeds the strict duplicate stop, and the other release gates are not satisfied. Do not upload the preserved research raster.</p></section>
<section><h2>For a future approved candidate</h2><p>The current project executive page will provide the exact file and instructions only after automated evidence gates and a separate selector have authorized it. At that point, use the competition's single-band GeoTIFF/one-TIFF ZIP form, preserve the generated filename and short note, and save the organizer receipt. Do not infer approval from a passing format check.</p><p><a href="../executive-summary.html">Current project submission guide →</a></p></section></body></html>'''
    (OUT / "index.html").write_text(index)
    (OUT / "executive-summary.html").write_text(guide)

    md = f'''# Archived CADG experiment — {status}

**Not a current candidate. Do not upload.** This archived card reports `{card.get('verdict')}` and `slot_authorized={card.get('slot_authorized')}`. The strict candidate-to-lattice 3-pixel overlap is `{overlap:.2%}`; the duplicate stop is greater than 70%. The historical TIFF remains for audit/learning only and is not linked as a download.

- Archived holdout: **{hold['value']:.6f} HOLDOUT-DTI**, evaluator `{hold['evaluator_version']}`, {hold['withheld_positives']:,} withheld positives, 95% CI `[{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]`.
- Candidate identifier: `{card.get('submission_name')}`.
- SHA-256 recorded in archived card: `{card.get('raster_sha256')}`.
- Leaderboard estimate: **not estimable**. No organizer receipt binds a score to this raster.
- Final verdict: **{status}**. No slot authorization.

See the [current executive desk](../index.html), [current submission guide](../executive-summary.html), and [archived JSON card](run-card.json). Formatting, holdout performance and semantic novelty are separate gates.
'''
    (OUT / "EXECUTIVE_SUMMARY.md").write_text(md)
    for name, source in (("hypotheses.md", "research/cadg-submod-hypotheses.md"),
                         ("verification.md", "research/cadg-submod-verification.md")):
        (OUT / name).write_text((ROOT / source).read_text())


if __name__ == "__main__":
    build()
