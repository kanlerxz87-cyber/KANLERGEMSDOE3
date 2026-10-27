#!/usr/bin/env python3
"""Render the preserved CADG study as a strictly negative research archive.

The historical card and TIFF bytes remain unchanged. A human selector cannot
waive a duplicate STOP under the standing protocol; this generator has no
positive publisher or competition-upload implementation.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape as esc
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/cadg-submod"
LATTICE_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
CARD_SHA = "3a2627d8b6175e20e280b0c42ee3ea47a654614b2f407fe1766e2bed790be5e2"
SAMPLE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_receipt(card: dict, report: dict) -> None:
    """Check identity and arithmetic, not independent scientific provenance."""
    try:
        full, subset = report["full_registered_lattice"], report["catalogue_excluded_lattice"]
        n, hits = full["candidate_dots"], full["candidate_dots_within_3px_of_lattice"]
        sn, shits = subset["candidate_dots"], subset["candidate_dots_within_3px"]
        artifact = ROOT / card["submission_artifacts"]["primary_zeros_tif"]
        card_path = ROOT / "evidence/cadg-submod-run-card.json"
        valid = (sha(card_path) == CARD_SHA and json.loads(card_path.read_bytes()) == card
                 and card["verdict"] == report["verdict"] == "negative"
                 and card["slot_authorized"] is report["slot_authorized"] is report["ok_to_submit"] is False
                 and report["candidate_generated"] is False and report["geological_experiments"] == report["slots_used"] == 0
                 and full["candidate_sha256"] == card["raster_sha256"] == sha(artifact)
                 and full["lattice_sha256"] == LATTICE_SHA and full["sample_mirror_sha256"] == SAMPLE_SHA
                 and full["organizer_template_authenticated"] is False
                 and full["geometry"]["bands"] == 1 and full["geometry"]["dtype"] == "float32"
                 and full["geometry"]["crs"] == "EPSG:32611" and full["geometry"]["shape"] == [3730, 3292]
                 and full["geometry"]["transform"] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
                 and full["in_footprint_nan"] == full["in_footprint_inf"] == 0
                 and (full["in_footprint_min"], full["in_footprint_max"]) == (0.0, 1.0)
                 and full["strict_nan_outside"] is False and full["outside_nan_count"] == 0
                 and full["outside_unmasked_finite_count"] == full["outside_pixel_count"] == 7111787
                 and type(n) is int and type(hits) is int and n > 0 and 0 <= hits <= n
                 and type(sn) is int and type(shits) is int and sn == n and 0 <= shits <= sn
                 and math.isclose(full["candidate_dot_overlap_fraction"], hits / n, abs_tol=1e-12, rel_tol=0)
                 and math.isclose(subset["directed_overlap_3px"], shits / sn, abs_tol=1e-12, rel_tol=0)
                 and math.isclose(subset["directed_overlap_3px"], card["final_dot_overlap_3px"], abs_tol=5e-7, rel_tol=0)
                 and subset["matches_card"] is True
                 and full["duplicate_over_70_percent"] is (hits / n > .70)
                 and full["duplicate_over_70_percent"] is True)
    except (KeyError, OSError, TypeError, ValueError, ZeroDivisionError):
        valid = False
    if not valid:
        raise ValueError("CADG card, saved bytes and lattice audit disagree; refuse to build")


def build(check_only: bool = False) -> None:
    audit = json.loads((ROOT / "docs/audit.json").read_text())
    card_bytes = (ROOT / "evidence/cadg-submod-run-card.json").read_bytes()
    card = json.loads(card_bytes)
    report = json.loads((ROOT / "evidence/session-30454eca-cadg-lattice.json").read_text())
    check_receipt(card, report)
    if not (OUT / "run-card.json").is_file() or (OUT / "run-card.json").read_bytes() != card_bytes:
        raise ValueError("Preserved CADG run card does not match original evidence")
    hold, art = card["holdout"], card["submission_artifacts"]
    full, subset = report["full_registered_lattice"], report["catalogue_excluded_lattice"]
    zero = Path(art["primary_zeros_tif"]).relative_to("docs/cadg-submod").as_posix()
    nan = Path(art["official_nan_twin_tif"]).relative_to("docs/cadg-submod").as_posix()
    note = esc(card["submission_note"])
    name = esc(card["submission_name"])
    digest = esc(card["raster_sha256"])
    rows = []
    for row in audit["rows"]:
        source = f"https://github.com/buffedlizard55-lab/{row['repo']}/blob/{row['head']}/{row['file']}"
        rows.append(f'''<tr><th scope="row">{esc(row['repo'])}</th><td><a href="{esc(source)}">{esc(Path(row['file']).name)}</a><small>Historical reference only</small></td><td>{row['owner_reported_leaderboard_score']:.4f}<small>Unverified owner report; no score-to-file receipt</small></td><td>Duplicate: {row['max_overlap_3px']:.2%} maximum directed 3-px peer overlap</td><td><strong>DO NOT SUBMIT</strong></td></tr>''')
    style = '''<style>:root{font-family:system-ui,sans-serif;color:#172f38;background:#f3f6f6}body{max-width:1100px;margin:auto;padding:24px}header,section{background:white;border:1px solid #d7e2e2;border-radius:14px;padding:24px;margin:18px 0}h1{font-size:clamp(1.8rem,4vw,2.7rem)}h1,h2{letter-spacing:-.025em}p,li{line-height:1.65}a{color:#075d61}nav{display:flex;gap:1rem;flex-wrap:wrap}.banner{border-left:7px solid #a93529;background:#fff5f1}.archive{border-left:5px solid #bb831d}small{display:block;color:#536b6e}code{overflow-wrap:anywhere;background:#edf4f3;padding:1px 4px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:.9rem}td,th{text-align:left;padding:12px;border-bottom:1px solid #d7e2e2;vertical-align:top}th:nth-child(2),td:nth-child(2){min-width:180px;overflow-wrap:anywhere}footer{padding:15px;color:#536b6e}.eyebrow{text-transform:uppercase;font-size:.78rem;letter-spacing:.1em;color:#45666a}</style>'''
    def page(title: str, body: str) -> str:
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} · CADG research archive</title>{style}</head><body>{body}<footer>Prior research, not a competition receipt. No slot was selected by this review.</footer></body></html>'''
    banner = f'''<section class="banner"><h2>DO NOT SUBMIT · literal duplicate STOP</h2><p>The preserved CADG research TIFF is not an eligible competition file. The independent full-lattice audit found <strong>{full['candidate_dots_within_3px_of_lattice']:,} / {full['candidate_dots']:,} dots ({full['candidate_dot_overlap_fraction']:.2%})</strong> within three pixels of a registered lattice, exceeding the 70% stop. A separate selector cannot override a failed uniqueness gate. No slot is authorized.</p><p>Its original card reports {subset['directed_overlap_3px']:.2%} after excluding lattice dots on the mirrored catalogue. We reproduced both definitions; neither passes. Excluding those dots is not an approved exemption.</p><p><a href="../data/session-30454eca-cadg-lattice.json">Independent full and catalogue-excluded audit →</a> · <a href="run-card.json">Unchanged historical card →</a></p></section>'''
    uncertainty = '''<p>The rejected upload and portal receipt were not supplied. The cause of the earlier <code>Predicted values must be in range [0, 1]</code> message is unknown. Locally finite values do not prove a fix or guarantee acceptance. The official task specifies null/NaN outside bounds; the zero-outside research file does not meet the local strict mirror-mask profile. The mirrored sample is not organizer-authenticated.</p>'''
    score = f'''<p>The archived card reports <strong>{hold['value']:.6f} HOLDOUT-DTI</strong>, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], evaluator <code>{esc(hold['evaluator_version'])}</code>, {hold['withheld_positives']:,} withheld positives. This is a prior participant-run result, not rerun in this review and not a leaderboard estimate. A separately reproduced <a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41">shared evaluator defect</a> blocks relying on new experiments until fixed centrally; this synthetic finding does not establish that the archived score was affected.</p>'''
    archive = f'''<section class="archive"><h2>Preserved artifacts · research only</h2><p>These prior files are retained for reproducibility, not submission, and no TIFF download is offered here. The two encodings have the same in-footprint dots; changing exterior encoding does not make a new prediction or overcome the duplicate stop.</p><p>Archived zero-TIFF path: <code>{esc(zero)}</code><br>NaN-outside twin path: <code>{esc(nan)}</code><br><a href="run-card.json">Original card</a></p><p>Archived zero-TIFF SHA-256: <code>{digest}</code><br>Historical name, not approved: <code>{name}</code><br>Historical note, do not paste for upload: <code>{note}</code></p></section>'''
    index = page("CADG decision", f'''<header><p class="eyebrow">Prior isolated study · {esc(card['lane_id'])}</p><h1>CADG-SUBMOD research archive</h1><p>A preserved parallel study with an explicitly negative submission decision.</p><nav><a href="executive-summary.html">Decision and future submission gates</a><a href="../index.html">Root nine-site desk</a><a href="hypotheses.md">Original hypotheses</a><a href="verification.md">Original verification</a></nav></header>{banner}<section><h2>What the prior study reported</h2>{score}<p><strong>Hypothesis:</strong> {esc(card['hypothesis'])}</p><p><strong>Non-fault mimic:</strong> {esc(card['non_fault_mimic'])}</p><p>The card's selected 35-detector comparison and four sibling-lane comparisons are limited scopes, not all-registry uniqueness. The full registered lattice independently fails; its result supersedes any impression of a uniqueness pass.</p></section><section><h2>Saved-byte format limits</h2><p>The original local validator reports a single float32 band on the participant-mirror EPSG:32611 grid, with no in-footprint NaN and values in [0,1]. This is local format evidence only; it is not organizer acceptance or a scientific promotion.</p>{uncertainty}</section>{archive}<section><h2>Nine historical priority sites</h2><p>Reported scores are unverified owner claims, not organizer receipts; no new score is estimated. File links are historical references only.</p><div class="scroll"><table><thead><tr><th>Site</th><th>Historical file</th><th>Reported value</th><th>Uniqueness</th><th>Submit?</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>''')
    guide = page("CADG gates", f'''<header><p class="eyebrow">Prior study · decision and future gates</p><h1>No approved CADG submission</h1><nav><a href="index.html">← CADG research archive</a><a href="../executive-summary.html">Root submission guide</a></nav></header>{banner}<section><h2>What is required before any future upload</h2><ol><li>Obtain an assigned method lane, authenticated organizer template and complete registry; centrally repair and repin the shared evaluator. Do not start a new geological run while the prerequisites or time budget are blocked.</li><li>Run leakage-safe whole-segment holdouts, feature canaries and a same-fold paired comparison. Record the evaluator, 95% confidence interval and withheld positives.</li><li>Check the full registry before placement and again on exact final saved dots. A surface correlation above 0.90 or directed 3-pixel overlap above 70% is a mandatory duplicate stop. A selector cannot waive it.</li><li>Validate the saved single-band float32 TIFF against the authenticated organizer grid, including CRS, shape, transform, in-footprint finite [0,1] and outside contract. Bind a new unique filename, SHA-256 and note of at most 140 characters to receipts.</li><li>Only after all scientific, uniqueness and format gates pass may a separate selector decide whether to spend an available weekly slot. Retain the organizer's actual receipt. No upload is automated.</li></ol>{uncertainty}</section><section><h2>Historical identity, not an upload instruction</h2><p>SHA-256 <code>{digest}</code><br>Historical name <code>{name}</code><br>Historical note <code>{note}</code></p>{score}</section>{archive}''')
    md = f'''# CADG-SUBMOD: negative research archive\n\n**DO NOT SUBMIT.** The independent full-lattice audit found {full['candidate_dots_within_3px_of_lattice']:,}/{full['candidate_dots']:,} dots ({full['candidate_dot_overlap_fraction']:.2%}) within 3 px, exceeding the literal 70% stop. A selector cannot waive that gate. The older {subset['directed_overlap_3px']:.2%} figure excludes lattice cells on the mirrored catalogue; it also fails and is not an exemption.\n\nThe prior card reports HOLDOUT-DTI {hold['value']:.6f}, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], evaluator `{hold['evaluator_version']}`, {hold['withheld_positives']:,} withheld positives. This participant result was not rerun or organizer-confirmed.\n\nThe original zero-outside TIFF's SHA-256 is `{card['raster_sha256']}`. Its locally finite [0,1] values do not establish the cause of the prior portal error or guarantee acceptance; the rejected file is unavailable. The official task describes null/NaN outside bounds. Both encodings are preserved only as research artifacts.\n\n[Current CADG decision](index.html) · [Gate guide](executive-summary.html) · [Full root desk](../index.html) · [Forensic receipt](../data/session-30454eca-cadg-lattice.json) · [Original card](run-card.json)\n'''
    outputs = {
        OUT / "index.html": index,
        OUT / "executive-summary.html": guide,
        OUT / "EXECUTIVE_SUMMARY.md": md,
        OUT / "README.md": md,
        OUT / "hypotheses.md": (ROOT / "research/cadg-submod-hypotheses.md").read_text(),
        OUT / "verification.md": (ROOT / "research/cadg-submod-verification.md").read_text(),
    }
    if check_only:
        stale = [str(p.relative_to(ROOT)) for p, text in outputs.items() if not p.is_file() or p.read_text() != text]
        if stale:
            raise ValueError("Generated CADG site is stale: " + ", ".join(stale))
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for path, text in outputs.items():
            path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on stale output without changing any file")
    args = parser.parse_args()
    build(check_only=args.check)


if __name__ == "__main__":
    main()
