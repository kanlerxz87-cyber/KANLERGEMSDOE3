#!/usr/bin/env python3
"""Render the quarantined CADG archive from its original card and forensic audit.

The archive is research-only; a selector cannot waive a failed duplicate stop.
This builder never writes the root decision desk or generates a candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/cadg-submod"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_archive(report: dict, card: dict, root: Path = ROOT) -> list[dict]:
    """Bind the negative forensic receipt to the saved card, TIFFs and ZIPs.

    This is an integrity/consistency check, not a fresh scientific audit. It
    deliberately cannot authorize a positive decision, even with edited JSON.
    """
    archive = (root / "docs/cadg-submod/downloads").resolve()
    card_path = root / "evidence/cadg-submod-run-card.json"
    if (card.get("verdict") != "negative" or card.get("slot_authorized") is not False
            or report.get("verdict") != "negative" or report.get("slot_authorized") is not False
            or report.get("status") != "STOP_DUPLICATE" or report.get("all_files_exceed_70_percent") is not True
            or report.get("candidate_generated") is not False or report.get("full_registry_compared") is not False
            or report.get("source_card_sha256") != sha(card_path)):
        raise ValueError("CADG archive receipt is stale, positive or inconsistent")
    pinned_lattice = next(row for row in json.loads((root / "research/registry-lock.json").read_text())["entries"] if row["id"] == "registry-160")
    if report["lattice_source"] != pinned_lattice:
        raise ValueError("CADG audit does not use the pinned registered lattice")
    lattice_sha = pinned_lattice["sha256"]
    core = {row["id"]: row["sha256"] for row in json.loads((root / "data/core-manifest.json").read_text())["files"]}
    rows = []
    for version in report["versions"]:
        if version.get("same_in_footprint_dot_mask") is not True:
            raise ValueError("CADG encoding twins were not shown to match")
        receipt = root / version["receipt"]
        if receipt.is_symlink() or receipt.resolve().parent != archive or sha(receipt) != version["receipt_sha256"]:
            raise ValueError("CADG archive receipt bytes changed")
        if len(version["files"]) != 2:
            raise ValueError("Each CADG archive version needs both encodings")
        for item in version["files"]:
            file = root / item["file"]
            package = root / item["zip"]
            if (file.is_symlink() or package.is_symlink() or file.resolve().parent != archive
                    or package.resolve().parent != archive or sha(file) != item["sha256"]
                    or sha(package) != item["zip_sha256"] or item.get("zip_contains_exact_tiff_only") is not True):
                raise ValueError("CADG archive TIFF/ZIP bytes or paths changed")
            with zipfile.ZipFile(package) as z:
                if z.namelist() != [file.name] or z.read(file.name) != file.read_bytes():
                    raise ValueError("CADG ZIP does not contain the exact saved TIFF")
            measurement, validator = item["lattice"], item["validator"]
            count, near = measurement["candidate_dots"], measurement["candidate_dots_within_3px_of_lattice"]
            if (type(count) is not int or count <= 0 or type(near) is not int or not 0 <= near <= count
                    or measurement["candidate_sha256"] != item["sha256"] or measurement["lattice_sha256"] != lattice_sha
                    or measurement["sample_mirror_sha256"] != core["sample_submission"]
                    or measurement["label_mirror_sha256"] != core["labels"]
                    or measurement["candidate_dot_overlap_fraction"] != near / count
                    or near / count <= .70 or measurement["duplicate_over_70_percent"] is not True
                    or validator["candidate_sha256"] != item["sha256"] or type(validator.get("ok")) is not bool
                    or validator.get("portal_acceptance_verified") is not False
                    or validator.get("submission_authorized") is not False):
                raise ValueError("CADG measured duplicate or saved-byte binding is inconsistent")
            diagnostic = item["catalogue_filtered_lattice_diagnostic"]
            filtered_near = diagnostic["candidate_dots_within_3px"]
            if (type(filtered_near) is not int or not 0 <= filtered_near <= near
                    or diagnostic["overlap_fraction"] != filtered_near / count
                    or diagnostic["protocol_novelty_pass"] is not False):
                raise ValueError("CADG filtered-reference diagnostic is inconsistent")
            rows.append(item)
    if ({Path(item["file"]).name for item in rows} != {p.name for p in archive.glob("*.tif")}
            or len({item["file"] for item in rows}) != len(rows)
            or card.get("raster_sha256") not in {item["sha256"] for item in rows}):
        raise ValueError("CADG archive TIFF inventory is incomplete")
    return rows


def page(title: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · GEMS research archive</title><link rel="stylesheet" href="../assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="bar">
<a class="brand" href="../index.html"><span class="mark" aria-hidden="true">G</span><span>GEMS<small>Fault discovery / research desk</small></span></a>
<nav aria-label="Main navigation"><a href="../index.html">Executive summary</a><a href="../research.html">Research</a><a href="../sources.html">Evidence</a><a href="../executive-summary.html">How to submit</a></nav><span class="nav-status">Research blocked</span></div></header>
<main id="main">{body}</main><footer class="footer"><div>CADG archive · research only · no slot authorized</div><div><a href="../index.html">Return to the decision desk ↗</a></div></footer></body></html>\n'''


def render(root: Path = ROOT) -> dict[Path, str]:
    out = root / "docs/cadg-submod"
    card = json.loads((root / "evidence/cadg-submod-run-card.json").read_text())
    audit_bytes = (root / "evidence/session-91270cac-cadg-audit.json").read_bytes()
    report = json.loads(audit_bytes)
    rows = checked_archive(report, card, root)
    current = next(row for row in rows if row["sha256"] == card["raster_sha256"])
    measurement, diag = current["lattice"], current["catalogue_filtered_lattice_diagnostic"]
    hold = card["holdout"]
    table_rows = []
    for row in rows:
        data = row["lattice"]
        short = Path(row["file"]).name
        table_rows.append(f'''<tr><td><code>{esc(short)}</code><small>Preserved research artifact · no download is authorized</small></td>
<td><code>{esc(row['sha256'])}</code></td><td>{data['candidate_dots_within_3px_of_lattice']:,} / {data['candidate_dots']:,} ({data['candidate_dot_overlap_fraction']:.2%})</td>
<td>{'PASS' if row['validator']['ok'] else 'FAIL'} · {esc(row['validator']['encoding_profile'])}<small>Local mirror only; not a portal decision</small></td></tr>''')
    warning = '''<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — duplicate under the required all-registry rule.</strong><p>These are preserved research artifacts, not eligible competition files. A selector cannot waive a failed duplicate stop. No slot is authorized; no visual raster inspection is needed.</p></div></div>'''
    intro = f'''<div class="page-intro"><p class="eyebrow">Prior CADG-SUBMOD study / forensic archive</p><h1 class="subtitle-page">Research archive.<br>No eligible submission.</h1><p>The original experiment and files are preserved, but the current decision is negative.</p></div>{warning}'''
    body = intro + f'''<section class="section panel prose"><h2>Independent saved-byte result</h2><p>For the originally advertised TIFF, <strong>{measurement['candidate_dots_within_3px_of_lattice']:,} / {measurement['candidate_dots']:,} dots ({measurement['candidate_dot_overlap_fraction']:.2%})</strong> are within three pixels of a registered lattice. This is above the strict 70% duplicate stop. All archived encoding pairs independently fail that same single-reference test.</p><p>The original run card reported {card['final_dot_overlap_3px']:.2%} after removing catalogue pixels from the reference lattice. Our diagnostic reproduces that narrower calculation: {diag['candidate_dots_within_3px']:,} / {measurement['candidate_dots']:,} ({diag['overlap_fraction']:.2%}). The full registered reference, including its catalogue pixels, is the literal rule; both calculations stop the run. Surface correlation and the complete registry were not independently re-audited in this check.</p><p><a href="cadg-audit.json">Exact saved-byte, ZIP, lattice and format receipt ↗</a> · <a href="run-card.json">Unchanged original card ↗</a></p></section>
<section class="section panel prose"><h2>What the prior holdout does — and does not — say</h2><p>The prior participant card reports <strong>{hold['value']:.6f} HOLDOUT-DTI</strong> (95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]; evaluator <code>{esc(hold['evaluator_version'])}</code>; {hold['withheld_positives']:,} withheld positive pixels). This measurement was not independently rerun here, is not an organizer receipt or a leaderboard estimate, and cannot override a duplicate stop.</p><p>The previous page incorrectly described a selector sign-off as sufficient and claimed that zero padding prevents the reported portal error. The rejected upload was never provided; its error and the organizer's acceptance of these files remain unknown. The official format says null/NaN outside the bounds. Both local profiles are checks against an unauthenticated participant mirror.</p><p>Prior artifact identifier: <code>{esc(card['submission_name'])}</code><br>Original file SHA-256: <code>{esc(card['raster_sha256'])}</code><br>Historical note (do not paste for submission): <code>{esc(card['submission_note'])}</code></p></section>
<section class="section"><h2>Archived files · research only</h2><p>The existing bytes are retained in the repository for forensic reproducibility, without submission download links. <strong>DO NOT SUBMIT.</strong></p><div class="table-wrap"><table><thead><tr><th scope="col">Existing research file</th><th scope="col">SHA-256</th><th scope="col">Full lattice overlap</th><th scope="col">Local format profile</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table></div></section>
<section class="section panel prose"><h2>Next steps</h2><p>Use the <a href="../executive-summary.html">general submission guide</a> only after an independently validated new candidate clears every scientific and uniqueness gate. The historical <a href="hypotheses.md">hypotheses</a> and <a href="verification.md">verification report</a> are original author records; their claims are not independently reverified here.</p></section>'''
    guide = intro + f'''<section class="section panel prose"><h2>This is not an upload guide for the archived file</h2><p>The earlier page recommended uploading after human sign-off and asserted that one encoding prevented the range error. Neither assertion is established. The registered-lattice stop has failed, so the TIFF remains research-only regardless of sign-off.</p><p>Original TIFF <code>{esc(card['submission_name'])}</code><br>SHA-256 <code>{esc(card['raster_sha256'])}</code><br>Historical note, not for a new submission: <code>{esc(card['submission_note'])}</code></p><p><a href="index.html">View independent CADG archive audit ↗</a> · <a href="../executive-summary.html">General submission requirements ↗</a></p></section>'''
    md = f'''# CADG-SUBMOD research archive — DO NOT SUBMIT

The existing TIFF is a duplicate under the literal all-registry protocol; a selector cannot waive this stop. No slot is authorized.

The exact advertised TIFF has {measurement['candidate_dots_within_3px_of_lattice']:,} / {measurement['candidate_dots']:,} dots ({measurement['candidate_dot_overlap_fraction']:.2%}) within three pixels of the full registered lattice. The narrower catalogue-filtered comparison reproduces {diag['overlap_fraction']:.2%}; both exceed the 70% limit. This is a geometric audit, not a score.

Prior participant-reported HOLDOUT-DTI: {hold['value']:.6f}, evaluator `{hold['evaluator_version']}`, {hold['withheld_positives']:,} withheld positives, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]. Not rerun here or an organizer receipt.

The rejected upload is unavailable, and local format checks do not establish portal acceptance. See [the forensic receipt](cadg-audit.json) and [the general guide](../executive-summary.html).
'''
    return {out / "index.html": page("CADG prior study", body),
            out / "executive-summary.html": page("CADG archive limitations", guide),
            out / "EXECUTIVE_SUMMARY.md": md,
            out / "cadg-audit.json": audit_bytes.decode(),
            out / "hypotheses.md": '''# CADG-SUBMOD hypotheses — historical record, not validation

The preserved prior hypotheses include unverified causal claims and projected gains. They are not evidence that a candidate beat the leaderboard, and the archived CADG TIFFs fail the literal uniqueness stop. No selector can waive it.

Read the [original unmodified research record at the inherited commit](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/ee683eeff93ab9d5bbec802065963c6898a4190b/research/cadg-submod-hypotheses.md) as historical context, not as an approved upload or independently reproduced scientific result. For this review's conditional queue, see [current hypotheses](../hypotheses.md) and the [research page](../research.html).
''',
            out / "verification.md": '''# CADG-SUBMOD verification — superseded release interpretation

**DO NOT SUBMIT.** The original verification record claims an upload error was fixed and treats a narrower detector-only uniqueness comparison as relevant to selection. The previously rejected file was not supplied, so the cause of its error is unknown; a local encoding pass does not prove portal acceptance. The full registered lattice triggers the required duplicate stop, regardless of selector approval.

The [independent saved-byte audit](cadg-audit.json) binds the TIFFs, ZIPs, local profiles and overlap counts. The [original verification at the inherited commit](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/ee683eeff93ab9d5bbec802065963c6898a4190b/research/cadg-submod-verification.md) remains intact for historical research; it was not independently rerun as a model experiment here.
'''}


def build(check_only: bool = False) -> None:
    outputs = render()
    stale = [str(p.relative_to(ROOT)) for p, content in outputs.items() if not p.is_file() or p.read_text() != content]
    if check_only and stale:
        raise ValueError("Generated CADG archive is stale: " + ", ".join(stale))
    if not check_only:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(check_only=parser.parse_args().check)
