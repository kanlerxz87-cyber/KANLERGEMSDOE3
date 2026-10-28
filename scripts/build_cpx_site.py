#!/usr/bin/env python3
"""Render the preserved CPX study as a fail-closed research archive."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_cpx_archive import check_receipt  # noqa: E402
from scripts.build_site import page  # noqa: E402

OUT = ROOT / "docs/cpx-edti"
RECEIPT = ROOT / "evidence/session-cfcca804-cpx-audit.json"
CARD = ROOT / "evidence/cpx-run-card.json"
WHY = ROOT / "research/cpx_why_02778_20261028.md"


def build(check_only: bool = False) -> None:
    raw_receipt = RECEIPT.read_text()
    receipt = json.loads(raw_receipt)
    check_receipt(receipt)
    raw_card = CARD.read_text()
    card = json.loads(raw_card)
    if card.get("verdict") != "negative" or card.get("slot_authorized") is not False:
        raise ValueError("CPX historical card must remain negative")
    geom, hold = receipt["geometry"], card["holdout"]
    name = escape(Path(receipt["candidate_file"]).name)
    sha = escape(receipt["candidate_sha256"])
    warning = f'''<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT · literal all-registry stop</strong>
<p>The saved TIFF has {geom['candidate_dots_within_3px_of_lattice']:,} / {geom['candidate_dots']:,} dots ({geom['candidate_dot_overlap_fraction']:.2%}) within 3 pixels of the registered binary lattice. Detector-only comparisons do not override this stop; a selector cannot waive it. The earlier recommendation to treat another study as a slot candidate is withdrawn.</p></div></div>'''
    identity = f'''<section class="section panel prose"><h2>Historical file and local format</h2>
<p><code>{name}</code><br>SHA-256 <code>{sha}</code>. This zero-outside TIFF passes only the local <code>finite-grid</code> profile against the participant mirror, not <code>template-mask</code> or <code>masked-finite</code>. Values inside the mirrored footprint are finite and in [0,1]. The rejected upload was not supplied; its error cause and portal acceptance are unknown.</p>
<p><a href="cpx-audit.json">Independent saved-byte audit →</a> · <a href="run-card.json">Unchanged historical card →</a> · <a href="../index.html#comparison">Nine-site executive desk →</a></p></section>'''
    holdout = f'''<section class="section panel prose"><h2>Historical holdout is not a leaderboard estimate</h2>
<p>The prior card reports <strong>HOLDOUT-DTI {hold['value']:.6f}</strong>, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], <code>{escape(hold['evaluator_version'])}</code>, {hold['withheld_positives']:,} withheld positives. This is a participant-run result, not independently rerun here or an organizer receipt. Its paired interval versus B0 includes zero. It does not establish that this file will beat 0.2778.</p></section>'''
    intro = '''<p class="breadcrumb"><a href="../index.html">← Repository executive desk</a></p><div class="page-intro"><p class="eyebrow">CPX concurrent research archive · 28 October 2026</p><h1 class="subtitle-page">No CPX submission is authorized.</h1><p>This earlier research lane is preserved, not a new experiment from the current review.</p></div>'''
    overview = intro + warning + identity + holdout + '''<section class="section panel prose"><h2>How to submit later</h2><p>No eligible TIFF exists today. A future candidate needs a named method lane, whole-segment buffered validation, feature canaries, a matched incumbent, pre-placement and final all-registry uniqueness checks, and saved-byte format verification. A separate selector checks the actual weekly quota only after those gates pass.</p><p><a href="../executive-summary.html">Conditional competition guide →</a> · <a href="why-02778.md">Bounded H33 analysis →</a></p></section>'''
    guide = '''<p class="breadcrumb"><a href="index.html">← CPX archive</a></p><div class="page-intro"><p class="eyebrow">Conditional future submission guide</p><h1 class="subtitle-page">Do not upload this TIFF.</h1><p>The literal duplicate stop prevents submission; this page cannot authorize a slot.</p></div>''' + warning + identity + '''<section class="section panel prose"><h2>When a future candidate is eligible</h2><p>Use the <a href="../executive-summary.html">repository submission guide</a> only after an independently authenticated template, paired same-fold improvement, complete registry checks and a separate selector decision. Local format checks cannot guarantee a portal result.</p></section>'''
    hypotheses = '''<p class="breadcrumb"><a href="index.html">← CPX archive</a></p><div class="page-intro"><p class="eyebrow">Historical hypotheses</p><h1 class="subtitle-page">Geological ideas remain provisional.</h1><p>No new assigned method lane or geological experiment was inferred during this review.</p></div>''' + warning + '''<section class="section panel prose"><h2>Concealed fault discovery</h2><p>Gravity, magnetic, basement and strain edges can coincide near faults, but lithologic contacts, volcanic structures and survey seams can mimic them. Prior model recovery on a mapped-fault holdout does not prove discovery of a hidden fault or geothermal vent.</p><p>Review the <a href="../hypotheses.html">ranked research queue</a>, the <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">official USGS GeoDAWN release</a>, and the <a href="https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa">USGS structural discontinuity study</a>.</p></section>''' + holdout
    md = f'''# CPX research archive — DO NOT SUBMIT

The prior TIFF `{name}` (SHA-256 `{sha}`) has {geom['candidate_dots_within_3px_of_lattice']:,} / {geom['candidate_dots']:,} dots ({geom['candidate_dot_overlap_fraction']:.2%}) within 3 px of the registered binary lattice. The literal stop cannot be waived. See [the saved-byte audit](cpx-audit.json).

The historical card reports HOLDOUT-DTI {hold['value']:.6f}, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], `{hold['evaluator_version']}`, {hold['withheld_positives']:,} withheld positives. This was not rerun here, is not an organizer score and cannot forecast the leaderboard.

The zero-outside file passes only `finite-grid` locally against the participant mirror. Portal acceptance and the cause of the previous range error are unknown. [H33 explanation](why-02778.md) · [Conditional submission guide](../executive-summary.html).
'''
    outputs = {
        OUT / "index.html": page("CPX archive", overview, prefix="../"),
        OUT / "executive-summary.html": page("CPX executive summary", overview, prefix="../"),
        OUT / "submission-guide.html": page("CPX submission guide", guide, prefix="../"),
        OUT / "hypotheses.html": page("CPX hypotheses", hypotheses, prefix="../"),
        OUT / "README.md": md,
        OUT / "EXECUTIVE_SUMMARY.md": md,
        OUT / "why-02778.md": WHY.read_text(),
        OUT / "cpx-audit.json": raw_receipt,
        OUT / "run-card.json": raw_card,
    }
    if check_only:
        stale = [str(path.relative_to(ROOT)) for path, content in outputs.items() if not path.is_file() or path.read_text() != content]
        if stale:
            raise ValueError("Stale CPX archive files: " + ", ".join(stale))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content)
    print("Built the fail-closed CPX research archive; no TIFF was generated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(check_only=parser.parse_args().check)
