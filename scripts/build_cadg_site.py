#!/usr/bin/env python3
"""Render the prior CADG study as a quarantined, reproducible research archive.

This publisher never promotes a TIFF or selects a competition slot. It refuses
contradictory cards, stale measurements, or altered saved bytes rather than
restoring the old misleading "download-ready" page.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/cadg-submod"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def check_receipt(card: dict, receipt: dict) -> None:
    """Check identities and negative-result invariants, not scientific validity."""
    artifacts = card["submission_artifacts"]
    if (card.get("verdict") != "negative" or card.get("slot_authorized") is not False
            or receipt.get("verdict") != "negative" or receipt.get("ok_to_submit") is not False
            or receipt.get("complete_registry_audited_in_this_replay") is not False
            or receipt.get("surface_audited_in_this_replay") is not False
            or receipt.get("portal_acceptance_verified") is not False
            or receipt.get("sample_mirror_organizer_authenticated") is not False
            or receipt.get("equal_prediction_values_inside_mirrored_footprint") is not True):
        raise ValueError("Quarantine cannot publish an optimistic or contradictory decision")
    lattice_sha = receipt["lattice_source"]["sha256"]
    pinned = next(row for row in json.loads((ROOT / "research/registry-lock.json").read_text())["entries"]
                  if row["id"] == "registry-160")
    source = receipt["lattice_source"]
    if (lattice_sha != pinned["sha256"] or source["repo"] != pinned["repo"]
            or source["commit"] != pinned["ref"] or source["path"] != pinned["file"]
            or receipt.get("sample_positive_equals_label_positive") is not True):
        raise ValueError("Lattice or participant-mirror identity is inconsistent")
    core = {row["id"]: row["sha256"] for row in json.loads((ROOT / "data/core-manifest.json").read_text())["files"]}
    for key, prefix, profile in (("zeros", "primary_zeros", "finite-grid"),
                                  ("nan", "official_nan_twin", "template-mask")):
        row = receipt["measurements"][key]
        geom, validation = row["geometry"], row["validator"]
        relative = artifacts[prefix + "_tif"]
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(OUT.resolve()) or not path.is_file():
            raise ValueError("Missing archived TIFF or unsafe artifact path")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        count, within = geom["candidate_dots"], geom["candidate_dots_within_3px_of_lattice"]
        if (row["file"] != relative or digest != artifacts[prefix + "_sha256"]
                or digest != geom["candidate_sha256"] or digest != validation["candidate_sha256"]
                or validation["template_sha256"] != geom["sample_mirror_sha256"]
                or geom["sample_mirror_sha256"] != core["sample_submission"]
                or geom["label_mirror_sha256"] != core["labels"]
                or geom["lattice_sha256"] != lattice_sha or geom["duplicate_over_70_percent"] is not True
                or type(count) is not int or type(within) is not int or count <= 0 or not 0 <= within <= count
                or geom["candidate_dot_overlap_fraction"] != within / count or within / count <= .70
                or geom["in_footprint_nan"] != 0 or geom["in_footprint_inf"] != 0
                or validation["encoding_profile"] != profile or validation["ok"] is not True
                or not all(validation["checks"].get(name) is True for name in
                           ("single_band", "shape_match", "crs_match", "transform_match", "dtype_float32",
                            "no_nan_inside_footprint", "inside_range_0_1"))
                or validation["portal_acceptance_verified"] is not False
                or validation["submission_authorized"] is not False):
            raise ValueError("Archived TIFF, geometry or local validation receipt disagrees")
    z, n = (receipt["measurements"][k]["geometry"] for k in ("zeros", "nan"))
    if (z["candidate_dots"] != n["candidate_dots"]
            or z["candidate_dots_within_3px_of_lattice"] != n["candidate_dots_within_3px_of_lattice"]):
        raise ValueError("Archived encodings disagree on their in-footprint dot set")
    old = receipt["older_9a_pair"]
    old_path = (ROOT / old["writer_receipt"]).resolve()
    if (not old_path.is_relative_to((OUT / "downloads").resolve()) or not old_path.is_file()
            or hashlib.sha256(old_path.read_bytes()).hexdigest() != old["writer_receipt_sha256"]
            or old["equal_prediction_values_inside_mirrored_footprint"] is not True
            or old["not_a_new_candidate"] is not True or type(old["pixels_different_from_f056_pair"]) is not int
            or old["pixels_different_from_f056_pair"] <= 0):
        raise ValueError("Older CADG writer receipt or field identity is inconsistent")
    writer = json.loads(old_path.read_text())
    for key, section, profile in (("zeros", "primary_zero_outside", "finite-grid"),
                                  ("nan", "official_text_nan_outside_twin", "template-mask")):
        row = old["measurements"][key]
        geom, val = row["geometry"], row["validator"]
        path = (ROOT / row["file"]).resolve()
        count, near = geom["candidate_dots"], geom["candidate_dots_within_3px_of_lattice"]
        if (not path.is_relative_to(old_path.parent) or not path.is_file()
                or path.name != writer[section]["file"]
                or hashlib.sha256(path.read_bytes()).hexdigest() != writer[section]["sha256"]
                or geom["candidate_sha256"] != writer[section]["sha256"]
                or geom["lattice_sha256"] != lattice_sha or geom["sample_mirror_sha256"] != core["sample_submission"]
                or type(count) is not int or type(near) is not int or count <= 0 or not 0 <= near <= count
                or geom["candidate_dot_overlap_fraction"] != near / count or near / count <= .70
                or geom["duplicate_over_70_percent"] is not True or val["encoding_profile"] != profile
                or val["candidate_sha256"] != writer[section]["sha256"] or val["portal_acceptance_verified"] is not False):
            raise ValueError("Older archived TIFF or local geometry receipt disagrees")
    older_z, older_n = (old["measurements"][k]["geometry"] for k in ("zeros", "nan"))
    if (older_z["candidate_dots"] != older_n["candidate_dots"]
            or older_z["candidate_dots_within_3px_of_lattice"] != older_n["candidate_dots_within_3px_of_lattice"]):
        raise ValueError("Older archived encodings disagree")
    ref = receipt["reference_mask_sensitivity"]
    total, oncat, offcat = (ref[k] for k in
                            ("full_reference_dots", "reference_dots_on_catalogue", "off_catalogue_reference_dots"))
    near = ref["candidate_dots_near_off_catalogue_reference"]
    if (any(type(x) is not int or x < 0 for x in (total, oncat, offcat, near))
            or total != pinned["positive_pixels"] or oncat + offcat != total
            or near > z["candidate_dots_within_3px_of_lattice"]
            or ref["candidate_fraction_near_off_catalogue_reference"] != near / z["candidate_dots"]
            or not math.isclose(ref["candidate_fraction_near_off_catalogue_reference"],
                                card["final_dot_overlap_3px"], abs_tol=0.0000005)):
        raise ValueError("Reference-mask sensitivity receipt disagrees with the archived result")


def frame(title: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · GEMS research archive</title><link rel="stylesheet" href="../assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="bar">
<a class="brand" href="../index.html"><span class="mark" aria-hidden="true">G</span><span>GEMS<small>Research archive</small></span></a>
<nav aria-label="Main navigation"><a href="../index.html">Executive summary</a><a href="../research.html">Research</a><a href="../sources.html">Evidence</a><a href="../executive-summary.html">How to submit</a></nav><span class="nav-status">Research blocked</span></div></header>
<main id="main">{body}</main><footer class="footer"><div>Archived evidence · no submission authorized</div><div><a href="../index.html">Return to the decision desk</a></div></footer></body></html>\n'''


def build(check_only: bool = False) -> None:
    card = json.loads((ROOT / "evidence/cadg-submod-run-card.json").read_text())
    receipt = json.loads((ROOT / "evidence/session-5c1613da-cadg-audit.json").read_text())
    check_receipt(card, receipt)
    zero = receipt["measurements"]["zeros"]
    nan = receipt["measurements"]["nan"]
    geom, ref = zero["geometry"], receipt["reference_mask_sensitivity"]
    older = receipt["older_9a_pair"]
    older_geom = older["measurements"]["zeros"]["geometry"]
    hold = card["holdout"]
    rows = "".join(
        f'<tr><td>{esc(label)}</td><td><code>{esc(Path(row["file"]).name)}</code>'
        f'<small>Research only — DO NOT SUBMIT</small></td>'
        f'<td><code>{esc(row["geometry"]["candidate_sha256"])}</code></td>'
        f'<td>{esc(row["validator"]["encoding_profile"])} local check; portal unverified</td><td><strong>NO</strong></td></tr>'
        for label, row in (("f056 · finite zeros outside", zero), ("f056 · NaN outside", nan),
                           ("9a4e · finite zeros outside", older["measurements"]["zeros"]),
                           ("9a4e · NaN outside", older["measurements"]["nan"]))
    )
    warning = f'''<div class="notice"><span class="icon" aria-hidden="true">!</span><div>
<strong>DO NOT SUBMIT — duplicate under the requested registry rule.</strong>
<p>Reopened saved bytes: {geom['candidate_dots_within_3px_of_lattice']:,} / {geom['candidate_dots']:,} dots
({geom['candidate_dot_overlap_fraction']:.2%}) are within 3 pixels of the registered binary lattice.
This exceeds the 70% stop. A selector signature cannot change a failed scientific gate.</p></div></div>'''
    intro = '''<div class="page-intro"><p class="eyebrow">Archived study / not a new submission</p>
<h1 class="subtitle-page">CADG research archive.<br>No eligible upload.</h1>
<p>The original artifacts and participant-run results are retained for learning, not recommended for competition submission.</p></div>'''
    content = intro + warning + f'''
<section class="section panel prose"><h2>Why the earlier page was wrong</h2>
<p>The earlier page called the file download-ready, implied human sign-off could resolve a failed literal gate, and asserted that a finite grid prevents the prior portal error. Those claims are withdrawn. The rejected upload was not supplied; the portal and authentic organizer sample have not been tested.</p>
<p>The old lattice figure used only {ref['off_catalogue_reference_dots']:,} reference dots after removing {ref['reference_dots_on_catalogue']:,} dots on the mirrored catalogue. That limited reference gives {ref['candidate_dots_near_off_catalogue_reference']:,} / {geom['candidate_dots']:,} ({ref['candidate_fraction_near_off_catalogue_reference']:.2%}); the required full registered raster gives {geom['candidate_dots_within_3px_of_lattice']:,} / {geom['candidate_dots']:,} ({geom['candidate_dot_overlap_fraction']:.2%}). Both fail. This is a geometry measurement, not a model score.</p>
<p>An older, distinct 9a4e prediction differs from f056 at {older['pixels_different_from_f056_pair']:,} in-footprint pixels; it also fails: {older_geom['candidate_dots_within_3px_of_lattice']:,} / {older_geom['candidate_dots']:,} ({older_geom['candidate_dot_overlap_fraction']:.2%}) against the full lattice. Neither pair can be submitted under the protocol.</p>
<p><a href="../data/session-5c1613da-cadg-audit.json">Independent saved-byte forensic receipt →</a> · <a href="run-card.json">Original card · historical claims →</a></p></section>
<section class="section panel"><h2>Original files · research use only</h2><p>Exact names and hashes are retained for reproducibility, but the failed files are not linked for download. Within each pair, the outside encodings have identical in-footprint predictions; the two pairs differ. The mirror is not authenticated by the organizer. A local encoding pass does not establish portal acceptance or novelty.</p>
<div class="table-wrap"><table><thead><tr><th>Encoding</th><th>Archived TIFF</th><th>SHA-256</th><th>Local format profile</th><th>Submit?</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="section panel prose"><h2>Original participant-run holdout</h2>
<p><strong>HOLDOUT-DTI {hold['value']:.6f}</strong> — evaluator <code>{esc(hold['evaluator_version'])}</code>, {hold['withheld_positives']:,} withheld positives, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]. This is a prior participant-reported result, not independently rerun here, not organizer-confirmed, not a forecast, and not directly comparable to a different split or evaluator.</p>
<p>Original submission name: <code>{esc(card['submission_name'])}</code><br>Original note, for identification only: <code>{esc(card['submission_note'])}</code></p></section>
<section class="section panel prose"><h2>Next steps before any eligible download</h2><p>Resolve the assigned lane, centrally repair and repin the shared evaluator, obtain the canonical cached features and complete registry, and establish a valid paired holdout incumbent. Then perform canaries, pre-placement and final-dot comparisons, and saved-byte validation. A separate selector can consider a slot only after all gates pass.</p><p><a href="../executive-summary.html">Read the step-by-step submission guide →</a></p></section>'''
    md = f'''# CADG archive — DO NOT SUBMIT

This is a prior research artifact, not an eligible new competition submission.
The saved TIFF has {geom['candidate_dots_within_3px_of_lattice']:,} / {geom['candidate_dots']:,}
({geom['candidate_dot_overlap_fraction']:.2%}) dots within 3 pixels of the full pinned binary lattice,
above the mandatory 70% duplicate stop; the failed artifacts are not linked for download. The prior off-catalogue-only reference produced
{ref['candidate_fraction_near_off_catalogue_reference']:.2%}; both fail.
The distinct older 9a4e field also fails: {older_geom['candidate_dots_within_3px_of_lattice']:,} /
{older_geom['candidate_dots']:,} ({older_geom['candidate_dot_overlap_fraction']:.2%}).

The local format profiles do not prove organizer acceptance. The rejected upload was not supplied.
The original participant-run HOLDOUT-DTI is {hold['value']:.6f}, evaluator
`{hold['evaluator_version']}`, {hold['withheld_positives']:,} positives, 95% CI
[{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]; it was not independently rerun and is not a leaderboard forecast.

[Research-only archive](index.html) · [Forensic receipt](../data/session-5c1613da-cadg-audit.json) · [Current decision desk](../index.html)
'''
    outputs = {OUT / "index.html": frame("CADG research archive", content),
               OUT / "executive-summary.html": frame("CADG research archive and guide", content),
               OUT / "EXECUTIVE_SUMMARY.md": md}
    if check_only:
        stale = [str(path.relative_to(ROOT)) for path, text in outputs.items()
                 if not path.is_file() or path.read_text() != text]
        if stale:
            raise ValueError("CADG quarantine pages are stale: " + ", ".join(stale))
    else:
        for path, text in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(check_only=parser.parse_args().check)
