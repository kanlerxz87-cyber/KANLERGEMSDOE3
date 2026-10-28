#!/usr/bin/env python3
"""Deterministic static evidence desk built ONLY from checked-in audit receipts.

No training, scraping, score estimation, file promotion or raster download occurs
at build time. An unavailable candidate must never become a download button.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT))


def read(path: str):
    return json.loads((ROOT / path).read_text())


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, content: str, active: str = "summary", prefix: str = "") -> str:
    links = [("summary", "index.html", "Executive summary"), ("research", "research.html", "Research"), ("sources", "sources.html", "Evidence"), ("guide", "executive-summary.html", "How to submit")]
    nav = "".join(f'<a href="{prefix}{path}"' + (' aria-current="page"' if key == active else '') + f'>{text}</a>' for key, path, text in links)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Evidence-first DOE GEMS fault discovery. Exact historical files, automated validation and a clear submission decision.">
<title>{esc(title)} · GEMS research desk</title><link rel="stylesheet" href="{prefix}assets/site.css">
<script src="{prefix}assets/site.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="bar">
<a class="brand" href="{prefix}index.html"><span class="mark" aria-hidden="true">G</span><span>GEMS<small>Fault discovery / research desk</small></span></a>
<nav aria-label="Main navigation">{nav}</nav><span class="nav-status">Research blocked</span></div></header>
<main id="main">{content}</main>
<footer class="footer"><div><strong>KANLERGEMSDOE3</strong> · Evidence before promotion<br>Maximize P(Win). Own the outcome. No fabricated scores or renamed submissions.</div>
<div>Reviewed 27 Oct 2026 · <a href="{prefix}data/session-e2903b2e-run-card.json">Current negative JSON card</a><br>Source changes do not authorize an upload. No competition submission is automated.</div></footer></body></html>\n'''


def historical_url(row: dict) -> str:
    return f"https://github.com/buffedlizard55-lab/{row['repo']}/blob/{row['head']}/{row['file']}"


def source_cards(feed: dict) -> str:
    out = []
    for row in feed["rows"]:
        observed = row if row.get("commit") else row.get("last_successful_source", {})
        commit = observed.get("commit")
        if commit:
            out.append(f'''<article class="source-card" data-source-repo="{esc(row['repository'])}" data-reviewed-sha="{commit}">
<a href="{esc(observed['source_url'])}">{esc(row['site'])} ↗</a><code>Observed commit {commit[:10]}</code>
<span class="freshness" aria-live="polite">Live source check pending; snapshot retained.</span></article>''')
        else:
            out.append(f'<article class="source-card"><strong>{esc(row["site"])}</strong><span class="freshness unavailable">Refresh failed — source freshness unknown.</span></article>')
    return "".join(out)


def comparison_table(rows: list[dict]) -> str:
    out = []
    for index, row in enumerate(sorted(rows, key=lambda r: -r["owner_reported_leaderboard_score"])):
        top = index == 0
        name = Path(row["file"]).name
        profiles = row["local_validation"]["encoding_profiles"]
        encoding = "finite-grid" if profiles["finite-grid"] else "template-mask" if profiles["template-mask"] else "neither"
        out.append(f'''<tr{' class="history-top"' if top else ''}><td><a class="site-name" href="sites/{row['repo']}.html">{row['repo']} ↗</a>{'<span class="top-label">TOP HISTORICAL CLAIM</span>' if top else ''}</td>
<td><span class="not-approved">None approved</span><details><summary>Historical file · research reference only; score not bound to bytes</summary><a href="{esc(historical_url(row))}">{esc(name)}</a><code>SHA-256 {row['sha256']}</code><small>Not a new submission. Do not upload this reference.</small></details></td>
<td><span class="score">{row['owner_reported_leaderboard_score']:.4f}</span><small>Owner-reported / unverified<br>No score-to-file receipt.</small></td>
<td>Not estimable<small>No validated leaderboard forecast</small></td>
<td><span class="tag negative">Duplicate</span><small>{row['max_overlap_3px']:.2%} maximum directed dot overlap within 3 px</small></td>
<td><span class="tag unknown">{encoding}</span><small>Local mask policy; not a portal verdict<br>Named encoding profile, not approval.</small></td>
<td><span class="not-approved">NO</span><small>No slot selected</small></td></tr>''')
    return '''<div class="table-wrap"><table><caption class="skip">Nine priority-site historical reference comparison; none is a submission recommendation.</caption><thead><tr><th scope="col">Site</th><th scope="col">File to download / submit</th><th scope="col">Historical claim</th><th scope="col">Leaderboard estimate</th><th scope="col">Unique?</th><th scope="col">Encoding profile</th><th scope="col">Submit?</th></tr></thead><tbody>''' + "".join(out) + "</tbody></table></div>"



def check_h33_lineage(report: dict, winners: list[dict], manifest: dict) -> None:
    """Check the frozen geometry receipt before displaying its interpretation."""
    refs = {r["repo"]: r["sha256"] for r in winners}
    core = {r["id"]: r["sha256"] for r in manifest["files"]}
    hashes = report.get("input_hashes", {})
    if any(hashes.get(k) != refs.get(k) for k in ("GEMSDOE25", "GEMSDOE30", "GEMSDOE32")) or any(hashes.get(k) != core.get(k) for k in ("labels", "sample_submission")):
        raise ValueError("H33 lineage input hashes do not match the research pins")
    m = report.get("measurement", {})
    try:
        coherent = (m["gemsdoe25_and_30_exact_dot_mask_equal"] is True
                    and m["gemsdoe32_equals_30_after_two_pixel_exclusion"] is True
                    and m["gemsdoe25_dots"] == m["gemsdoe30_dots"]
                    and m["gemsdoe30_dots"] - m["gemsdoe32_dots"] == m["gemsdoe30_dots_removed_to_get_32"]
                    and m["gemsdoe30_dots_removed_to_get_32"] == m["removed_within_two_pixels_of_catalogue"]
                    and m["gemsdoe32_dots_added_to_30"] == m["removed_beyond_two_pixels_of_catalogue"] == m["gemsdoe32_retained_within_two_pixels"] == 0)
    except (KeyError, TypeError):
        coherent = False
    if not coherent or report.get("candidate_generated") is not False or report.get("slot_authorized") is not False:
        raise ValueError("H33 lineage receipt is inconsistent or claims authorization")


def check_kpl36_receipt(report: dict, card_bytes: bytes, registry: dict) -> None:
    """Keep a peer promotion claim separate from our measured literal stop."""
    expected_card = "9448983264018a95518f79da1f63ecfb0f981f740f11ceaeebf341abac8a8d04"
    try:
        card = json.loads(card_bytes)
        peer, measured, validation = report["peer_source"], report["final_dot_lattice_comparison"], report["validator"]
        lattice = next(r for r in registry["entries"] if r["id"] == "registry-160")
        count, nearby = measured["candidate_dots"], measured["candidate_dots_within_3px_of_lattice"]
        good = (hashlib.sha256(card_bytes).hexdigest() == peer["run_card_sha256"] == expected_card
                and peer["commit"] == "61783525af4aa6dcf8da0bc68b06fa38b89ed27a"
                and peer["peer_verdict"] == card["verdict"] == "promote"
                and peer["file_sha256"] == card["submission"]["sha256"] == measured["candidate_sha256"] == validation["candidate_sha256"]
                and peer["file"] == card["submission"]["file"]
                and measured["lattice_sha256"] == lattice["sha256"]
                and type(count) is int and type(nearby) is int and 0 <= nearby <= count and count == card["submission"]["dots"]
                and measured["candidate_dot_overlap_fraction"] == nearby / count > .70
                and measured["duplicate_over_70_percent"] is True
                and report["verdict"] == "negative" and report["slot_authorized"] is False
                and report["full_registry_compared"] is False and report["surface_registry_comparison"] is None
                and validation["portal_acceptance_verified"] is False and validation["submission_authorized"] is False
                and peer["peer_holdout"]["dti"] == card["holdout"]["arms"]["EXP-3"]["dti"]
                and peer["peer_holdout"]["ci95"] == card["holdout"]["arms"]["EXP-3"]["ci95"]
                and peer["peer_holdout"]["evaluator_version"] == card["holdout"]["evaluator_version"]
                and peer["peer_holdout"]["withheld_positive_pixels"] == card["holdout"]["n_withheld_positive_pixels"])
    except (KeyError, TypeError, StopIteration, ZeroDivisionError, json.JSONDecodeError):
        good = False
    if not good:
        raise ValueError("Peer-lattice receipt is inconsistent; refuse to display it")


def check_poisson_archive(report: dict, card_bytes: bytes, registry: dict) -> None:
    """Validate the archived random-control identity and negative lattice gate."""
    try:
        card = json.loads(card_bytes)
        lattice = next(r for r in registry["entries"] if r["id"] == "registry-160")
        good = (hashlib.sha256(card_bytes).hexdigest() == report["source_card_sha256"]
                and card["verdict"] == report["verdict"] == "negative"
                and card["ok_to_submit"] is False and card["slot_authorized"] is False
                and report["slot_authorized"] is False and report["full_registry_compared"] is False
                and report["surface_registry_comparison"] is None and report["same_in_footprint_dot_mask"] is True)
        for kind in ("zeros", "nan"):
            item, audit = report["files"][kind], report["measurements"][kind]
            path, zip_path = (ROOT / item["path"]).resolve(), (ROOT / item["zip"]).resolve()
            if not path.is_relative_to((DOCS / "candidate_downloads").resolve()) or zip_path != path.with_suffix(".zip"):
                good = False
                continue
            with zipfile.ZipFile(zip_path) as z:
                exact_zip = z.namelist() == [path.name] and z.read(path.name) == path.read_bytes()
            m, v = audit["lattice"], audit["validator"]
            count, nearby = m["candidate_dots"], m["candidate_dots_within_3px_of_lattice"]
            good = (good and item["sha256"] == card["raster_sha256"][kind] == hashlib.sha256(path.read_bytes()).hexdigest()
                    and item["zip_sha256"] == hashlib.sha256(zip_path.read_bytes()).hexdigest()
                    and item["zip_contains_exact_tiff_only"] is True and exact_zip
                    and v["candidate_sha256"] == m["candidate_sha256"] == item["sha256"]
                    and m["lattice_sha256"] == lattice["sha256"]
                    and type(count) is int and type(nearby) is int and 0 <= nearby <= count == 37654
                    and m["candidate_dot_overlap_fraction"] == nearby / count > .70
                    and m["duplicate_over_70_percent"] is True
                    and v["ok"] is True and v["portal_acceptance_verified"] is False and v["submission_authorized"] is False)
    except (KeyError, TypeError, StopIteration, ZeroDivisionError, OSError, json.JSONDecodeError, zipfile.BadZipFile):
        good = False
    if not good:
        raise ValueError("Parallel control audit or artifact integrity is inconsistent")


def check_s2d36_receipt(report: dict, card_bytes: bytes, audit: dict, registry: dict) -> None:
    """Bind a bounded peer audit to its exact card and pinned reference identities.

    This is receipt consistency, not a fresh numerical evaluation or organizer
    authentication. A missing surface/full-registry audit can never become a pass.
    """
    try:
        card = json.loads(card_bytes)
        peer, lattice, validator = report["peer"], report["lattice"], report["validator"]
        hold, source_hold = card["holdout"], peer["source_holdout"]
        expected = {r["repo"]: r for r in audit["rows"]}
        comparisons = report["nine_historical_final_dot_comparisons"]
        lattice_lock = next(r for r in registry["entries"] if r["id"] == "registry-160")
        count, nearby = lattice["candidate_dots"], lattice["candidate_dots_within_3px_of_lattice"]
        valid = (hashlib.sha256(card_bytes).hexdigest() == peer["card_sha256"]
                 == "5df79bfe5d1da5c04bac8e57d78333385105a31f5777eabfe452441ba2f2114c"
                 and peer["commit"] == "21eec80b50f0daa34e2c06536ab7ffafdfc1095e"
                 and card["verdict"] == peer["peer_verdict"] == report["verdict"] == "negative"
                 and card["slot_approved"] is report["slot_authorized"] is report["ok_to_submit"] is False
                 and report["candidate_generated"] is False and report["geological_experiments"] == report["slots_used"] == 0
                 and report["surface_compared"] is report["complete_registry_compared"] is False
                 and peer["file"] == card["submission"]["file"]
                 and peer["sha256"] == card["submission"]["sha256"] == lattice["candidate_sha256"] == validator["candidate_sha256"]
                 and lattice["lattice_sha256"] == lattice_lock["sha256"]
                 and lattice["sample_mirror_sha256"] == validator["sample_mirror_sha256"] == "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
                 and lattice["organizer_template_authenticated"] is False
                 and lattice["geometry"]["bands"] == 1 and lattice["geometry"]["dtype"] == "float32"
                 and lattice["geometry"]["crs"] == "EPSG:32611" and lattice["geometry"]["shape"] == [3730, 3292]
                 and lattice["geometry"]["transform"] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
                 and lattice["in_footprint_nan"] == lattice["in_footprint_inf"] == 0
                 and (lattice["in_footprint_min"], lattice["in_footprint_max"]) == (0.0, 1.0)
                 and lattice["strict_nan_outside"] is False and lattice["outside_nan_count"] == 0
                 and lattice["outside_unmasked_finite_count"] == lattice["outside_pixel_count"] == 7111787
                 and type(count) is int and count > 0 and type(nearby) is int and 0 <= nearby <= count
                 and count == card["submission"]["dots"]
                 and math.isclose(lattice["candidate_dot_overlap_fraction"], nearby / count, rel_tol=0, abs_tol=1e-12)
                 and lattice["duplicate_over_70_percent"] is (nearby / count > .70)
                 and lattice["duplicate_over_70_percent"] is True
                 and source_hold["evidence_class"] == hold["label"] == "HOLDOUT-DTI"
                 and source_hold["value"] == hold["arms"]["EXP-2"]["dti"]
                 and source_hold["ci95"] == hold["arms"]["EXP-2"]["ci95"]
                 and source_hold["evaluator_version"] == hold["evaluator_version"]
                 and source_hold["withheld_positives"] == hold["n_withheld_positive_pixels"]
                 and validator["portal_acceptance_verified"] is validator["organizer_template_authenticated"] is False
                 and validator["profiles"] == {"template-mask": False, "finite-grid": True, "masked-finite": False}
                 and validator["in_footprint_finite_range"] == [0.0, 1.0]
                 and all(validator["checks"].get(k) is True for k in
                         ("single_band", "shape_match", "crs_match", "transform_match", "dtype_float32",
                          "no_nan_inside_footprint", "no_masked_inside_footprint", "inside_range_0_1",
                          "no_infinite_pixels_anywhere", "selected_encoding", "expected_positive_pixels_match"))
                 and len(comparisons) == len(expected) == 9
                 and {r["site"] for r in comparisons} == set(expected))
        for row in comparisons:
            n, hits, rho = row["candidate_dots"], row["candidate_dots_within_3px"], row["binary_spearman"]
            valid = (valid and row["reference_sha256"] == expected[row["site"]]["sha256"]
                     and row["reference_dots"] == expected[row["site"]]["dots"]
                     and type(n) is int and n == count and type(hits) is int and 0 <= hits <= n
                     and type(rho) in (int, float) and math.isfinite(rho) and -1 <= rho <= 1
                     and math.isclose(row["directed_overlap_3px"], hits / n, rel_tol=0, abs_tol=1e-12)
                     and row["duplicate"] is (hits / n > .70 or rho > .90))
    except (KeyError, TypeError, ValueError, StopIteration, ZeroDivisionError):
        valid = False
    if not valid:
        raise ValueError("S2D-36 peer audit is inconsistent; refuse to display it")


def check_changed_peer_receipt(changes: dict, report: dict, snapshot_bytes: bytes, registry: dict, manifest: dict, before_feed: dict, after_feed: dict) -> None:
    """Bind a dated, non-authorizing peer audit to its immutable-tree inventory."""
    import math
    import re
    from scripts.snapshot_raster_changes import rows_by_site
    before, after = rows_by_site(before_feed), rows_by_site(after_feed)
    pinned = next(row for row in registry["entries"] if row["id"] == "registry-160")
    core = {row["id"]: row["sha256"] for row in manifest["files"]}
    if (report.get("change_snapshot_sha256") != hashlib.sha256(snapshot_bytes).hexdigest()
            or report.get("lattice_source") != pinned or report.get("sample_mirror_sha256") != core["sample_submission"]
            or report.get("full_registry_compared") is not False or report.get("slot_authorized") is not False
            or report.get("new_candidate_generated") is not False or report.get("verdict") != "negative"
            or changes.get("all_compared") is not True or changes.get("registry_complete") is not False
            or changes.get("baseline_checked_utc") != before_feed.get("checked_utc")
            or changes.get("current_checked_utc") != after_feed.get("checked_utc")
            or report.get("snapshot_checked_utc") != after_feed.get("checked_utc")
            or len(changes.get("rows", [])) != len(before)
            or {row.get("site") for row in changes.get("rows", [])} != set(before)):
        raise ValueError("Changed-peer audit source binding or negative status is inconsistent")
    expected = {}
    for row in changes["rows"]:
        site = row["site"]
        if (row.get("status") != "PINNED_TREE_COMPARISON_ONLY"
                or row.get("repository") != after[site]["repository"]
                or row.get("before_commit") != before[site]["commit"]
                or row.get("after_commit") != after[site]["commit"]):
            raise ValueError("Changed-peer source tree not compared to the pinned feeds")
        for category in ("added", "changed"):
            for item in row[category]:
                key = (row["site"], item["path"])
                if key in expected:
                    raise ValueError("Duplicate changed-peer path")
                expected[key] = (row["repository"], row["after_commit"], item["after"]["git_blob"], item["after"]["mode"], category)
    findings = report["findings"]
    if len(findings) != len(expected) or report.get("files_seen") != len(findings):
        raise ValueError("Changed-peer file inventory incomplete")
    seen = set()
    for finding in findings:
        key = (finding["site"], finding["path"])
        identity = (finding["repository"], finding["commit"], finding["git_blob"], finding["mode"], finding["category"])
        if key in seen or expected.get(key) != identity or finding.get("slot_authorized") is not False:
            raise ValueError("Changed-peer finding does not match the source tree")
        seen.add(key)
        status = finding["status"]
        if status == "UNKNOWN":
            if finding.get("sha256") is not None:
                raise ValueError("Unknown changed-peer result claims a verified hash")
            continue
        count = finding["candidate_dots"]
        near = finding["candidate_dots_within_3px_of_full_lattice"]
        fraction = finding["directed_overlap_fraction"]
        if (not isinstance(finding.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", finding["sha256"])
                or type(count) is not int or count <= 0 or type(near) is not int or not 0 <= near <= count
                or not isinstance(fraction, (int, float)) or not math.isfinite(fraction) or fraction != near / count
                or status != ("STOP_DUPLICATE" if fraction > .70 else "BLOCKED_INCOMPLETE_REGISTRY")
                or finding.get("surface_correlation") is not None or finding.get("surface_before_placement") is not None):
            raise ValueError("Changed-peer geometry or status is inconsistent")
    for field, status in (("duplicate_stops", "STOP_DUPLICATE"), ("unknown", "UNKNOWN"), ("incomplete_registry", "BLOCKED_INCOMPLETE_REGISTRY")):
        if report.get(field) != sum(row["status"] == status for row in findings):
            raise ValueError("Changed-peer status counts are inconsistent")


def method_note(repo: str) -> str:
    """Interpret the supplied historical labels; do not invent model causality."""
    notes = {
        "GEMSDOE24": "The supplied winner is the D1.5-labelled dotted H19-5 variant. Spacing/thinning can trade redundant prediction mass for coverage, but the filename does not establish a new physical feature or a paired improvement. Its measured overlap places it in the shared historical geometry family.",
        "GEMSDOE25": "The D2.8-labelled H19-5 emission variant has a higher supplied historical claim than D1.5. That is not a causal spacing experiment: no same-fold ablation or score-to-file receipt is available. Greater sparsity can help false positives or hurt missed faults; the measured duplicate stop still applies.",
        "GEMSDOE27": "The supplied winner is labelled topological gap closure on D1.5. Gap completion could connect a concealed segment, but could also join unrelated landforms or contacts. Neither that mechanism nor a fold-local gain is established by the label. Later unscored artifacts are not ranked above this supplied claim.",
        "GEMSDOE28": "The Rung30 blind-R1-labelled file is the highest supplied scored entry for this site. Nearby Euler/tip-labelled variants do not isolate the cause of that claim. The exact raster still overlaps the other high-claim historical entries beyond the stop; a new label is not independent geology.",
        "GEMSDOE30": "The off-catalogue Poisson/D2.8-labelled file is an emission/placement reference, not proof of a new fault detector. Catalogue exclusion must be fold-local during holdout, not applied with hidden labels. Its high geometric overlap prevents treating it as a distinct submission here.",
        "GEMSDOE31": "The solo-D28-labelled winner continues the D2.8 reference family. Neither the solo label nor a different file hash proves a new physical mechanism. Without matched validation and a bound organizer receipt, its supplied historical claim cannot be translated into an estimate for another raster.",
        "GEMSDOE32": "H33 B2 is the highest supplied nine-site historical claim. Its dot mask equals the pinned GEMSDOE30 mask after excluding the dots within two pixels of the mirrored known catalogue, without additions. This suggests a testable emission-efficiency explanation, not a demonstrated geological breakthrough or causal score gain. Paired out-of-fold deletion/coverage ablations and a score-to-file receipt are absent; the shared-tool defect is not evidence that any official result was affected.",
        "GEMSDOE33": "The analog tip/stepover label suggests a structural-geometry hypothesis, but catalogue-derived analog features would need visible-only reconstruction after withholding. Lithologic contacts or landforms can mimic the pattern. The measured historical overlap triggers the stop independently of that unvalidated interpretation.",
        "GEMSDOE36": "Anderson/geothermal/PINN is a method label, not evidence that physical constraints, geothermal causality or a leakage-safe improvement were demonstrated. The high measured overlap with other winners prevents claiming independent geometry. Fault prediction and geothermal-vent discovery are different targets.",
    }
    return notes[repo]



def check_inherited(report: dict) -> None:
    """Bind the saved geometry receipt to every inherited TIFF, without repinning."""
    files = {str(path.relative_to(ROOT)) for path in (DOCS / "downloads").glob("*.tif")}
    if len(report["rows"]) != len(files) or {row["file"] for row in report["rows"]} != files or report.get("slot_authorized") is not False:
        raise ValueError("Inherited TIFF inventory/authorization receipt changed")
    lattice = next(row for row in read("research/registry-lock.json")["entries"] if row["id"] == "registry-160")
    for row in report["rows"]:
        path = (ROOT / row["file"]).resolve()
        if not path.is_relative_to((DOCS / "downloads").resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != row["candidate_sha256"]:
            raise ValueError("Inherited TIFF bytes differ from the audit: " + row["file"])
        count, near = row["candidate_dots"], row["candidate_dots_within_3px_of_lattice"]
        if type(count) is not int or type(near) is not int or not 0 <= near <= count or count == 0:
            raise ValueError("Inherited dot counts are invalid")
        ratio = near / count
        if (row.get("lattice_sha256") != lattice["sha256"] or abs(ratio - row["candidate_dot_overlap_fraction"]) > 1e-12
                or ratio <= .70 or row["duplicate_over_70_percent"] is not True):
            raise ValueError("Inherited lattice or duplicate arithmetic changed")
        if (row["validator"].get("sha256") != row["candidate_sha256"]
                or row["validator"].get("portal_acceptance_verified") is not False
                or row["validator"].get("submission_authorized") is not False):
            raise ValueError("Inherited format receipt is not bound to the same bytes and negative decision")


def inherited_section(report: dict, downloads: bool = False) -> str:
    rows = []
    for row in report["rows"]:
        filename = Path(row["file"]).name
        short = "GPC-3" if "gpc3" in filename else "K3-H1 ASGT hybrid" if "k3h1" in filename else "KANLER-H1 DCAP-LHC / NaN padding" if filename.endswith("-nan.tif") else "KANLER-H1 DCAP-LHC / zero padding"
        label = f'<strong title="{esc(filename)}">{esc(short)}</strong><br><small>SHA-256 <code>{row["candidate_sha256"][:12]}…</code></small>'
        if downloads:
            label = f'<a href="downloads/{esc(filename)}" title="{esc(filename)}" download>{label} ↘</a><br><small>Research-only TIFF; not an eligible upload.</small>'
        rows.append(f'<tr><th scope="row">{label}</th><td>{row["candidate_dots"]:,}</td><td>{row["candidate_dot_overlap_fraction"]:.3%}</td><td>{row["catalogue_positive_pixels"]:,}</td><td>{"PASS local profile only" if row["validator"]["ok"] else "FAIL"}</td><td class="status-stop">{"STOP DUPLICATE" if row["duplicate_over_70_percent"] else "BLOCKED / incomplete registry"}</td></tr>')
    return f'<section class="section panel" id="kanler-h1"><p class="eyebrow">Concurrent main preserved · not this session’s experiments</p><h2>Four root-archive TIFFs. Still no eligible upload.</h2><p>An independent saved-byte check includes the binary calibration lattice, with no “like-for-like” exemption. All four root-archive TIFFs exceed the literal 70% overlap stop. The separately preserved SSP1 study is not included in this four-file count. This is geometry forensics, not a model score or a complete registry audit.</p><div class="table-wrap" role="region" aria-label="Inherited research artifact literal-rule audit" tabindex="0"><table class="comparison"><thead><tr><th scope="col">Inherited research artifact</th><th scope="col">Dots</th><th scope="col">Within 3 px of lattice</th><th scope="col">On mirrored catalogue</th><th scope="col">Saved bytes</th><th scope="col">Eligibility</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div><p>The GPC file also contains 4,115 positives on mirrored catalogue pixels; its final-file visible-mask claim must not be inferred from a holdout flag. Local padding checks are not organizer authentication.</p><p><a href="inherited-literal-audit.json">Bound geometric + format receipts ↗</a> · <a href="parallel-research.html">Scoped parallel cards / research-only downloads ↗</a></p></section>'


def gpc_archive_pages(report: dict, card: dict) -> dict[Path, str]:
    """Replace unsafe GPC presentation, not its scientific artifacts or card."""
    rows = [row for row in report["rows"] if "gpc3" in Path(row["file"]).name]
    if (len(rows) != 1 or card.get("verdict") != "negative" or card.get("ok_to_submit") is not False
            or card.get("raster_sha256") != rows[0]["candidate_sha256"] or card.get("tif") != rows[0]["file"]):
        raise ValueError("GPC archive card does not identify its independently audited negative TIFF")
    row = rows[0]
    hold = card["holdout"]
    filename = Path(row["file"]).name
    intro = f'''<div class="page-intro"><p class="eyebrow">Preserved GPC-3 study / research archive</p><h1 class="subtitle-page">Prior experiment.<br>No eligible submission.</h1></div>
<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — registered-lattice duplicate.</strong><p>The earlier nine-champion comparison is not the all-registry test. A selector cannot waive a failed duplicate stop. No slot is authorized.</p></div></div>'''
    body = intro + f'''<section class="section panel prose"><h2>Independent saved-byte result</h2><p>The archived TIFF has <strong>{row['candidate_dots_within_3px_of_lattice']:,} / {row['candidate_dots']:,} dots ({row['candidate_dot_overlap_fraction']:.2%})</strong> within three pixels of the registered lattice. The saved raster also has {row['catalogue_positive_pixels']:,} positive pixels on the mirrored catalogue. This is a geometric stop, not a new model score.</p><p><a href="inherited-literal-audit.json">Independent geometry and local-format receipt ↗</a> · <a href="data/gpc-run-card.json">Original amended run card ↗</a></p><p><a href="downloads/{esc(filename)}" download>Research-only TIFF ↘</a><br>SHA-256 <code>{esc(row['candidate_sha256'])}</code>. No portal acceptance is claimed.</p></section>
<section class="section panel prose"><h2>Prior holdout, bounded interpretation</h2><p>The original card reports <strong>{hold['dti']:.6f} HOLDOUT-DTI</strong>, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], evaluator <code>{esc(hold['evaluator_version'])}</code>, {hold['withheld_positives']:,} withheld positive pixels. It was not rerun here, is not an organizer receipt or forecast, and cannot override a duplicate stop.</p><p>Earlier presentation incorrectly called this TIFF unique, gave upload steps for it, asserted a cause for the prior range error and attributed the historical 0.2778 score to deleted dots as proof. None of those claims follows from the evidence. The rejected upload was not supplied; local [0,1] compatibility is not proof of portal acceptance or the cause of its error.</p><p>The source presentation snapshots remain under <code>evidence/archived-pages/</code>; the actual TIFF and scientific run card are unchanged. <a href="research.html#h33">Measured H33 geometry and uncertainty →</a> · <a href="executive-summary.html">General future submission requirements →</a></p></section>'''
    markdown = f'''# GPC-3 prior study — DO NOT SUBMIT

The existing TIFF has {row['candidate_dots_within_3px_of_lattice']:,} / {row['candidate_dots']:,} dots ({row['candidate_dot_overlap_fraction']:.2%}) within three pixels of a registered lattice. This exceeds the user's literal duplicate stop. No slot is authorized, and a selector cannot waive the stop.

Prior reported HOLDOUT-DTI {hold['dti']:.6f}, 95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}], evaluator `{hold['evaluator_version']}`, {hold['withheld_positives']:,} withheld positives; not rerun here or an organizer score.

The original presentations are retained under `evidence/archived-pages/` for history, including superseded claims. The rejected upload was unavailable, so its error cause and portal acceptance remain unknown. See [the current desk](index.html) and [the independent receipt](inherited-literal-audit.json).
'''
    return {DOCS / "parallel-gpc-dashboard.html": page("GPC-3 research archive", body),
            DOCS / "parallel-gpc-submission-guide.html": page("GPC-3 archive limitations", body, "guide"),
            DOCS / "parallel-gpc-readme.md": markdown}


def changed_peer_section(changes: dict, report: dict) -> str:
    """Render scoped changed-path findings without treating them as new scores."""
    findings = report["findings"]
    rows = []
    for row in changes["rows"]:
        site_findings = [f for f in findings if f["site"] == row["site"]]
        stops = sum(f["status"] == "STOP_DUPLICATE" for f in site_findings)
        unknown = sum(f["status"] == "UNKNOWN" for f in site_findings)
        blocked = sum(f["status"] == "BLOCKED_INCOMPLETE_REGISTRY" for f in site_findings)
        rows.append(f'<tr><th scope="row"><a href="sites/{esc(row["site"])}.html">{esc(row["site"])}</a></th>'
                    f'<td>{len(row["added"])}</td><td>{len(row["changed"])}</td><td>{len(row["removed"])}</td>'
                    f'<td>{stops}</td><td>{unknown + blocked}</td></tr>')
    return f'''<section class="section panel" id="changed-peer-audit"><p class="eyebrow">Frozen peer source delta / literal lattice stop</p>
<h2>{report['duplicate_stops']} changed raster files fail one reference. None are approved.</h2>
<p>Comparing pinned Git trees from {esc(changes['baseline_checked_utc'])} to {esc(changes['current_checked_utc'])} found {report['files_seen']} added or modified TIFF paths. Exact Git-blob bytes were checked against one full registered lattice; the count includes NaN/zero twins and is <strong>not</strong> a count of independent models. All {report['duplicate_stops']} exceed 70% directed dot overlap. This is not a score, a full-registry review, or an audit of files added after that snapshot.</p>
<div class="table-wrap"><table><caption class="skip">Changed peer raster paths and saved-byte lattice stops, by site</caption><thead><tr><th>Site</th><th>Added paths</th><th>Modified paths</th><th>Removed paths</th><th>Duplicate stops</th><th>Unknown or incomplete</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>Zero changed paths does not mean that site's existing files are unique. Surface correlations, holdout scores and portal acceptance were not measured. The files remain participant research artifacts, not downloads selected by this desk.</p><p><a href="data/changed-peer-audit-91270cac.json">Saved-byte findings and hashes ↗</a> · <a href="data/raster-changes-91270cac.json">Pinned source-path inventory ↗</a></p></section>'''


def heatmap(audit: dict) -> str:
    names = [row["repo"] for row in audit["rows"]]
    pairs = {(row["candidate"], row["reference"]): row["overlap_3px"] for row in audit["pairs"]}
    pieces = ['<svg class="heatmap" viewBox="0 0 590 540" role="img" aria-labelledby="heat-title heat-desc"><title id="heat-title">Historical directed dot overlap</title><desc id="heat-desc">Rows are candidate sites, columns are reference sites. All 72 cross-site comparisons exceed the 70 percent duplicate stop. Values are geometric measurements, not scores.</desc>']
    for i, name in enumerate(names):
        short = name.replace("GEMSDOE", "")
        pieces.append(f'<text x="{112+i*50}" y="44" text-anchor="middle">{short}</text><text x="74" y="{81+i*50}" text-anchor="end">{short}</text>')
        for j, reference in enumerate(names):
            value = pairs.get((name, reference))
            fill = "#f0f3ef" if value is None else "#d8e9db" if value < .95 else "#b8d4c0"
            label = "—" if value is None else f"{value:.0%}"
            pieces.append(f'<rect x="{89+j*50}" y="{56+i*50}" width="46" height="46" rx="5" fill="{fill}"/><text class="tiny" x="{112+j*50}" y="{83+i*50}" text-anchor="middle">{label}</text>')
    pieces.append('<text x="310" y="525" text-anchor="middle">Reference site → · candidate rows · ≤3 px, directed</text></svg>')
    return "".join(pieces)


def hypothesis_cards(hypotheses: list[dict], detailed: bool = False) -> str:
    pieces = []
    for row in hypotheses:
        details = f'''<dl><dt>Physical signature</dt><dd>{esc(row['signature'])}</dd><dt>Why missing from the catalogue?</dt><dd>{esc(row['missing_fault_rationale'])}</dd><dt>Difference from prior work</dt><dd>{esc(row['difference'])}</dd><dt>Non-fault mimic</dt><dd>{esc(row['non_fault_mimic'])}</dd><dt>Availability / viability</dt><dd>{esc(row['viability'])} <a href="{esc(row['source'])}">Source ↗</a></dd><dt>Expected DTI improvement</dt><dd>{esc(row['expected_improvement'])}</dd></dl>''' if detailed else f'<p>{esc(row["signature"])}</p><p><strong>Confounder:</strong> {esc(row["non_fault_mimic"])}</p>'
        pieces.append(f'''<article class="hypothesis"><span class="rank" aria-hidden="true">0{row['rank']}</span><h3>{esc(row['name'])}</h3><span class="tag unknown">Untested</span><span class="tag">{esc(row['cost'])} cost</span><p>{esc(row['layers'])}</p>{details}</article>''')
    return '<div class="hypothesis-grid">' + "".join(pieces) + '</div>'


def guide() -> str:
    return '''<div class="page-intro"><p class="eyebrow">Submission guide / automated checks first</p><h1 class="subtitle-page">From an idea to an eligible GeoTIFF.</h1><p>Validation is executed by code, not a human raster inspector. A scientific promotion and permission to spend a weekly slot are separate decisions.</p></div>
<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>Current state: DO NOT SUBMIT</strong><p>No eligible file, unique submission name or competition note exists yet. No download is authorized. The examples below are instructions, not generated submissions.</p></div></div>
<ol class="rule-list">
<li><strong>Restore and audit the pinned inputs.</strong>Run the commands below. This public participant mirror is hash-verified, not organizer-authenticated. Preparation delegates to the shared template and sanitizes raw-band sentinels; it does not generate predictions or privately rebuild the canonical feature stack.<pre>python -m venv .venv
.venv/bin/pip install -r requirements.txt
bash scripts/download_competition_data.sh
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/audit_shared_tools.py
.venv/bin/python scripts/preflight.py</pre>A negative audit/preflight exits nonzero intentionally. Do not override it with a success label.</li>
<li><strong>Establish the assigned lane and trustworthy instruments.</strong>The method paragraph is absent. The shared cache bytes/digest and same-fold incumbent are absent. The shared evaluator has an open <a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41">operator defect</a>. Repair the shared template centrally, pin its corrected commit, and rerun operator tests. Never patch a private scoring fork.</li>
<li><strong>Validate one preregistered geological candidate.</strong>Hide whole fault segments with a buffer. Recompute distance, tip, density, orientation and every other catalogue-derived feature using only visible faults. Mask visible faults pixel-exactly. Run every feature alone as a leakage canary; AUC above 0.90 blocks trust until explained. Canonical hide-and-recover currently takes binary masks; it must not silently evaluate soft probabilities as their nonzero support.</li>
<li><strong>Beat the recorded holdout best before any slot decision.</strong>Use pooled HOLDOUT-DTI, alpha 0.2, beta 0.8 and a 300 m triangular kernel. Save evaluator version, withheld-positive count, 95% spatial-block CI and paired improvement CI on identical folds. Require the lower bound of paired improvement to be positive. A holdout number is not a public leaderboard estimate. Stop after three experiments or two hours.</li>
<li><strong>Check semantic uniqueness twice.</strong>Before writing: compare the continuous surface and explicit preview dots against every registry raster. After writing: repeat on the exact final dots, and bind the report to their hash. Rank correlation above 0.90 or directed dot overlap above 70% within Euclidean 3 px means duplicate: log and stop. A partial registry, a constant/empty comparison or a new filename is not a uniqueness pass.<pre>.venv/bin/python scripts/check_uniqueness.py --help</pre>The current nine historical winners already fail this stop; copying any of them is not an experiment.</li>
<li><strong>Write through the canonical writer, then validate the saved bytes automatically.</strong>Use the unmodified shared <code>vendor/shared-template/scripts/submission_writer.py</code> only after the research gates pass. Write to ignored <code>data/research/</code>, not the website. Do not pass invalid, NaN or arbitrary soft values and rely on binarization/clipping to repair them. A write receipt is not scientific approval.<pre>.venv/bin/python scripts/validate_submission.py data/core/sample_submission.tif data/research/CANDIDATE.tif --profile masked-finite
.venv/bin/python scripts/validate_submission.py data/core/sample_submission.tif data/research/CANDIDATE.tif --profile template-mask
.venv/bin/python scripts/validate_submission.py data/core/sample_submission.tif data/research/CANDIDATE.tif --profile finite-grid</pre><code>masked-finite</code> additionally requires a standalone masked exterior and finite raw [0,1] values everywhere, guarding against a portal-wide scan of a hidden negative sentinel. The report counts raw below-zero, above-one and nonfinite cells, including masked/outside pixels. It cannot identify the cause of your earlier range error because the rejected file was not provided. The official page requires float32, matching grid/bounds and null/NaN outside bounds; all three profiles are local checks against an unauthenticated mirror, not proof of portal acceptance. The validator never repairs a file.</li>
<li><strong>Bind name, note, hash and quality evidence.</strong>The exact output must be single-band float32 on the template's CRS/shape/transform, with no NaN/Inf/nodata inside and values in [0,1]. Record SHA-256 and all automated receipts. A future name may encode project, lane, UTC and content digest; it is not uniqueness evidence. A short note must be at most 140 characters. No real filename or note is offered while no candidate exists.</li>
<li><strong>Let the separate selector authorize a slot.</strong>The <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules, section 3.4</a>, specify up to three submissions per week. The logged-in submission page determines the account's actual remaining cap; it has not been verified here. No slot is selected automatically by this research session.</li>
<li><strong>Only then download and upload the exact approved file.</strong>After evidence-bound promotion, an approved TIFF link must appear at the beginning of the executive summary with its exact hash/name and note. On DrivenData choose Submit → Make new submission, select the single-band TIFF (or the portal-supported single-TIFF ZIP), and paste the saved note. Preserve the resulting submission-page receipt and submitted hash. Only that receipt establishes ORGANIZER-CONFIRMED per-file performance. The site cannot submit under an unauthenticated account.</li>
<li><strong>Preserve reproducibility and required disclosures.</strong>Retain complete code, input provenance, licenses and the winning-model documentation. Official rules section 3.2 requires disclosure of generative-AI assistance. AI was used here for research synthesis, code, tests and documentation; no claim is made of field-confirmed geological discovery.</li></ol>
<section class="panel"><h2>About the range error</h2><p>The prior error is unknown: the rejected upload's bytes were not supplied. Possible mechanisms include NaN/Inf, raw feature nodata sentinels, incorrect bands, values below zero or above one, or a padding contract mismatch. Automated validation must inspect the exact saved TIFF, not just the in-memory array. Do not change the file after hashing; a ZIP must contain only the approved TIFF.</p></section>'''



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


def build(check_only: bool = False) -> None:
    audit = read("docs/audit.json")
    card = read("evidence/run-card.json")
    session = read("evidence/session-7d1e577d-run-card.json")
    previous_session = read("evidence/session-52a91352-run-card.json")
    concurrent_session = read("evidence/session-12817d00-run-card.json")
    second_concurrent_session = read("evidence/session-5c1613da-run-card.json")
    current_session = read("evidence/session-91270cac-run-card.json")
    for scoped in (previous_session, concurrent_session, second_concurrent_session, current_session):
        if scoped.get("verdict") != "negative" or scoped.get("ok_to_submit") is not False or scoped.get("slot_authorized") is not False or scoped.get("raster_sha256") is not None:
            raise ValueError("A review-session card cannot authorize an unimplemented publisher")
    our_session = read("evidence/session-30454eca-run-card.json")
    if (our_session.get("verdict") != "negative" or our_session.get("promote") is not False
            or our_session.get("slot_authorized") is not False or our_session.get("raster_sha256") is not None
            or our_session.get("geological_experiments") != 0 or our_session.get("weekly_slots_used") != 0):
        raise ValueError("This review card cannot authorize an unimplemented publisher")
    final_session = read("evidence/session-e2903b2e-run-card.json")
    if (final_session.get("verdict") != "negative" or final_session.get("ok_to_submit") is not False
            or final_session.get("slot_authorized") is not False
            or final_session.get("weekly_slots_used_this_session") != 0
            or final_session.get("raster_sha256") is not None
            or final_session.get("candidate_generated") is not False):
        raise ValueError("Final review card cannot authorize an unimplemented publisher")
    upstream = read("evidence/session-e2903b2e-upstream-prerequisites.json")
    latest_upstream = read("evidence/session-20261028-upstream-prerequisites.json")
    from scripts.audit_upstream_prerequisites import validate_receipt
    for snapshot in (upstream, latest_upstream):
        upstream_errors = validate_receipt(snapshot)
        if upstream_errors:
            raise ValueError("Shared-prerequisite receipt is malformed: " + ", ".join(upstream_errors))
    inherited = read("evidence/inherited_literal_audit.json")
    check_inherited(inherited)
    saturation = read("evidence/session-30454eca-saturation.json")
    check_saturation(saturation, (ROOT / "evidence/upstream/GEMSDOE31/registry/raster_registry.json").read_bytes())
    from scripts.check_run import check
    check(card, read("research/registry-lock.json"))
    outputs = {}
    def emit(path, content):
        outputs[path] = content
    for path, content in gpc_archive_pages(inherited, read("evidence/run_card.json")).items():
        emit(path, content)
    readiness = read("evidence/session-e2903b2e-preflight.json")
    emit(DOCS / "data/readiness.json", json.dumps(readiness, indent=2) + "\n")
    # The root desk and the isolated archive are one checked publication unit;
    # neither builder can leave a stale optimistic archive guide behind.
    from scripts.build_cadg_site import checked_archive, render as render_cadg
    cadg_card = read("evidence/cadg-submod-run-card.json")
    cadg_report = read("evidence/session-91270cac-cadg-audit.json")
    cadg_rows = checked_archive(cadg_report, cadg_card)
    cadg_current = next(row for row in cadg_rows if row["sha256"] == cadg_card["raster_sha256"])
    for path, content in render_cadg().items():
        emit(path, content)
    feed = read("docs/data/focus-feed.json")
    change_path = ROOT / "evidence/session-91270cac-raster-changes.json"
    changes = json.loads(change_path.read_bytes())
    peer_audit = read("evidence/session-91270cac-changed-peer-audit.json")
    check_changed_peer_receipt(changes, peer_audit, change_path.read_bytes(), read("research/registry-lock.json"),
                               read("data/core-manifest.json"), read("evidence/session-20261027-focus-feed.json"),
                               read("evidence/session-91270cac-focus-feed.json"))
    emit(DOCS / "data/raster-changes-91270cac.json", change_path.read_text())
    emit(DOCS / "data/changed-peer-audit-91270cac.json", (ROOT / "evidence/session-91270cac-changed-peer-audit.json").read_text())
    hypotheses = read("research/hypotheses.json")
    official = read("evidence/official-claims-20261026.json")
    observation = read("evidence/official-observation-20261027.json")
    lineage = read("evidence/session-30454eca-h33.json")
    check_h33_lineage(lineage, read("sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json")["historical_winners"], read("data/core-manifest.json"))
    h33 = lineage["measurement"]
    emit(DOCS / "research/why-02778.md", f'''# What the reported 0.2778 H33 B2 result can and cannot tell us

**OWNER-REPORTED, not ORGANIZER-CONFIRMED:** no submission-page receipt binds 0.2778 to the pinned TIFF. The score is not a forecast for a new file.

The independently checked GEMSDOE25 and GEMSDOE30 masks are identical (44,090 dots). The GEMSDOE32 H33 B2 mask is the GEMSDOE30 mask with {h33['gemsdoe30_dots_removed_to_get_32']:,} dots within two pixels of the mirrored known-fault catalogue removed, and no additions. See [the hash-pinned geometry receipt](../h33-lineage-20261027.json).

The official 300 m triangular distance-weighted Tversky rewards nearby coverage but penalizes false-positive mass. Thinning redundant dots could reduce the denominator without losing coverage, but deleting a dot that uniquely covers a hidden fault could hurt. [Organizer staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) say *only exact known-fault pixels* are masked; nearby new truth remains possible. There is no established 200 m dead annulus.

Hidden truth, receipt-bound scores and a matched causal ablation are unavailable. Therefore the reason for the reported score is not identifiable from geometry alone. Earlier numerical credit and leaderboard projections, zero/NaN portal claims, and categorical causal explanations in the preserved [original source at the inherited commit](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/ee683eeff93ab9d5bbec802065963c6898a4190b/docs/research/why-02778.md) are superseded, not verified results. No claim of improved future leaderboard performance is supported.
''')
    emit(DOCS / "research/hypotheses.md", '''# Hypotheses: current review and historical GPC record

See the [current ranked hypotheses](../hypotheses.md) and [scientific explanation](../research.html). All are conditional and untested in the current review; no assigned lane is inferred.

The [original GPC hypotheses at the inherited commit](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/ee683eeff93ab9d5bbec802065963c6898a4190b/docs/research/hypotheses.md) remain a historical record. Their causal premises and uniqueness claims are not established by this review.
''')
    emit(DOCS / "research.md", '''# Scientific research — current decision

**DO NOT SUBMIT.** No new candidate, holdout score, leaderboard estimate or authorized slot was produced in this review. See the [current research page](research.html), [ranked hypotheses](hypotheses.md), [H33 geometry and limitations](research/why-02778.md), and [independent inherited-file audit](inherited-literal-audit.json).

The [superseded parallel research at the inherited commit](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/ee683eeff93ab9d5bbec802065963c6898a4190b/docs/research.md) contains claims of causal scores, predicted gains and suggested final selections. It is retained for history, not accepted as a score, novelty result or submission recommendation.
''')
    kpl = read("evidence/kpl36-lattice-audit-20261027.json")
    check_kpl36_receipt(kpl, (ROOT / "evidence/upstream/GEMSDOE36/kpl36-run-card-61783525.json").read_bytes(), read("research/registry-lock.json"))
    kpl_dots, kpl_holdout = kpl["final_dot_lattice_comparison"], kpl["peer_source"]["peer_holdout"]
    poisson = read("evidence/parallel-poisson-audit-20261027.json")
    check_poisson_archive(poisson, (ROOT / "evidence/candidate_poisson_20261027.json").read_bytes(), read("research/registry-lock.json"))
    poisson_dots = poisson["measurements"]["zeros"]["lattice"]
    s2d = read("evidence/session-30454eca-s2d36-audit.json")
    check_s2d36_receipt(s2d, (ROOT / "evidence/peer-s2d36-card-21eec80b.json").read_bytes(), audit, read("research/registry-lock.json"))
    s2d_lattice, s2d_holdout = s2d["lattice"], s2d["peer"]["source_holdout"]
    s2d_nine = {r["site"]: r for r in s2d["nine_historical_final_dot_comparisons"]}
    # This desk has no release/publisher implementation or eligible artifact.
    # Fail rather than render an optimistic state if somebody edits a card alone.
    if card.get("verdict") != "negative" or card.get("raster_sha256") is not None or readiness.get("submit_ready") is not False:
        raise ValueError("No evidence-bound publisher exists for a positive decision; do not manufacture a download link")
    resolved = "".join(f'<div class="progress-item"><span aria-hidden="true">✓</span><div><strong>{esc(text)}</strong><small>Automated integrity checks; not scientific approval.</small></div></div>' for text in readiness["resolved"])
    blockers = "".join(f'<div class="progress-item"><span aria-hidden="true">—</span><div><strong>{esc(text)}</strong></div></div>' for text in readiness["failures"])
    prior = card["holdout_dti"]["scores"]["candidate"]
    delta = card["holdout_dti"]["paired_differences"]["ablation"]
    open_issues = [row for row in upstream["upstream_issues"] if row["state"] == "OPEN"]
    issue_numbers = ", ".join(f"#{row['number']}" for row in open_issues)
    shared_panel = f'''<section class="section panel prose" id="shared-prerequisites"><p class="eyebrow">Dated shared-template audit / participant source</p><h2>Source changed. Research remains blocked.</h2><p>On 28 October the participant head was <code>{esc(latest_upstream['participant_source']['head_commit'][:12])}</code>. {sum(not row['byte_identical_to_pinned'] for row in latest_upstream['shared_files'])} of {len(latest_upstream['shared_files'])} checked files changed since our local pin; the upstream binary-input guard changed, but the current head has not been independently operator-tested. The pinned evaluator still fails the synthetic empty-truth false-positive test. Issue state alone does not establish the behavior of new bytes.</p><p>The latest checked feature receipt has no SHA-256 and its cache path is absent from that repository tree. <a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/53">Issue #53</a> requests a content-addressed artifact and lineage. No private cache was substituted.</p><p><a href="upstream-prerequisites-20261028.json">28 October prerequisite receipt ↗</a> · <a href="session-0f36badb-review.md">28 October review ↗</a> · <a href="data/session-20261028-run-card.json">Negative run card ↗</a> · <a href="upstream-prerequisites-20261027.json">Earlier snapshot ↗</a> · <a href="session-e2903b2e-review.md">Earlier integrated review ↗</a></p></section>'''
    parallel_panel = f'''<section class="section panel prose" id="results"><p class="eyebrow">Concurrent main / prior experiments, not this review session</p><h2>Preserved evidence. Still a negative decision.</h2><p>The prior bilateral-texture session recorded <strong>{prior['dti']:.4f} HOLDOUT-DTI</strong>, 95% CI [{prior['ci95'][0]:.4f}, {prior['ci95'][1]:.4f}], evaluator <code>{esc(prior['evaluator_version'])}</code>, {prior['withheld_positive_pixels']:,} withheld positive pixels. The matched ablation difference is {delta['delta']:.6f}, 95% CI [{delta['ci95'][0]:.6f}, {delta['ci95'][1]:.6f}]: it does not establish improvement. These are archived participant-run measurements, consistency-checked here, not independently rerun or organizer-confirmed.</p><p>Its final dots had 100% forward overlap within 3 px of a registered binary calibration lattice: a literal duplicate stop. Four inherited research TIFF files under the root downloads archive, including two encodings of DCAP-LHC, have independent literal-rule checks below. The separate random control is also preserved. None is an eligible submission. This review session ran zero geological experiments and generated no new TIFF; it does not overwrite or claim those prior runs.</p><h3>A registry representation obstruction</h3><p>A <strong>full-footprint witness</strong> in the pinned registry is a continuous diagnostic, not an established submitted dot field. The prior shared tool counts every finite positive cell as a dot; under that convention it covers all 5,167,373 footprint pixels and forces 100% overlap for any nonempty candidate. Our new geometry CLI instead refuses to invent dots from a soft surface and requires its explicit companion dot mask. That is an unresolved registry definition, not an exemption or a uniqueness pass. The binary lattice remains a separate verified obstruction for the recorded 37,654-dot runs.</p><p><a href="run-card.json">Canonical prior bilateral card ↗</a> · <a href="data/session-7d1e577d-run-card.json">Prior review’s negative card ↗</a> · <a href="data/session-91270cac-run-card.json">Changed-peer audit card ↗</a> · <a href="data/session-30454eca-run-card.json">Peer-forensic audit card ↗</a> · <a href="data/session-e2903b2e-run-card.json">Final review’s negative card ↗</a> · <a href="data/registry_saturation.json">Conditional saturation receipt ↗</a> · <a href="parallel-lattice-audit.json">Archived binary-lattice audit ↗</a></p></section>'''
    main = f'''<section class="hero"><div><p class="eyebrow">Executive summary / DOE GEMS</p><h1>Better fault predictions.<br><em>Evidence before a slot.</em></h1><p class="lede">An honest decision desk for the nine priority sites. See exactly what can be downloaded, what has been tested, and what still blocks a genuinely new submission.</p><p class="date">Evidence snapshots: 27–28 October 2026 · not a score projection</p></div>
<aside class="download-card" aria-label="Submission file status"><p class="eyebrow">Your competition file</p><h2>No eligible TIFF yet.</h2><p>The required scientific and uniqueness gates have not passed. No historical file is being relabelled as new.</p><div class="file-unavailable"><svg width="27" height="32" viewBox="0 0 27 32" fill="none" aria-hidden="true"><path d="M4 1h12l7 7v22H4zM16 1v8h7M9 16h9M9 21h9" stroke="currentColor" stroke-width="1.4"/></svg><div><strong>Download unavailable · DO NOT SUBMIT</strong><small>No placeholder file. No authorized slot.</small></div></div><div class="download-meta"><div><span>Score estimate</span><strong>Not estimable</strong></div><div><span>Unique candidate</span><strong>Not generated</strong></div><div><span>Weekly slots used</span><strong>None this session</strong></div></div></aside></section>
<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — historical winners duplicate; no new candidate qualifies.</strong><p>The historical family fails your literal overlap stop. Core data were restored locally for this review from participant mirrors; ignored inputs must be restored in a fresh checkout. The assigned lane/cache/incumbent are missing and the shared evaluator needs a central repair. This is a negative research deliverable, not a completed high-scoring model.</p><p><a href="session-e2903b2e-review.md">Final integrated three-pass review →</a> · <a href="session-30454eca-review.md">Peer-forensic review →</a> · <a href="session-91270cac-review.md">Changed-peer audit →</a> · <a href="session-5c1613da-review.md">Parallel CADG audit →</a></p></div></div>
<div class="stats"><article class="stat"><span class="label">Historical uniqueness</span><strong>9 / 9 stopped</strong><small>Geometric audit · not DTI scores</small></article><article class="stat"><span class="label">Data placement</span><strong>Locally restored</strong><small>19-band input · participant mirror, not organizer-authenticated</small></article><article class="stat"><span class="label">Shared instruments</span><strong>Blocked</strong><small>Source-locked · operator defect reproduced</small></article><article class="stat"><span class="label">Geological experiments / final review</span><strong>0 / 3</strong><small>No lane silently assigned · no slot spent</small></article></div>
{shared_panel}
<section class="section" id="comparison"><div class="section-heading"><div><p class="eyebrow">Priority portfolio</p><h2>One clear decision for every site.</h2><p>Sorted by historical owner-reported claims, not by a validated score forecast or a recommendation.</p></div><a href="audit.json">Exact hashes &amp; all comparisons ↗</a></div>
{comparison_table(audit['rows'])}<div class="table-note"><span><strong>Claims are quarantined:</strong> no organizer submission-page receipt binds any historical score to a file. No new HOLDOUT-DTI was run by this review session; prior parallel results are separately identified below.</span><span>Local encoding compatibility ≠ portal acceptance ≠ scientific promotion.</span></div></section>
{changed_peer_section(changes, peer_audit)}
<section class="section panel prose" id="s2d36-audit"><p class="eyebrow">Newer GEMSDOE36 research / independent saved-byte audit</p><h2>S2D-36 EXP-2: <span class="not-approved">DO NOT SUBMIT.</span></h2><p>At pinned peer commit <code>{esc(s2d['peer']['commit'][:12])}</code>, the peer itself reports a negative verdict. Our fresh independent check found <strong>{s2d_lattice['candidate_dots_within_3px_of_lattice']:,} / {s2d_lattice['candidate_dots']:,} dots ({s2d_lattice['candidate_dot_overlap_fraction']:.2%})</strong> within three pixels of the registered binary lattice. It also exceeds 70% against the pinned historic GEMSDOE24 ({s2d_nine['GEMSDOE24']['directed_overlap_3px']:.2%}) and GEMSDOE27 ({s2d_nine['GEMSDOE27']['directed_overlap_3px']:.2%}) winners. Any one is a literal duplicate stop.</p><p>The peer reports <strong>{s2d_holdout['value']:.4f} HOLDOUT-DTI</strong>, 95% CI [{s2d_holdout['ci95'][0]:.4f}, {s2d_holdout['ci95'][1]:.4f}], <code>{esc(s2d_holdout['evaluator_version'])}</code>, {s2d_holdout['withheld_positives']:,} withheld positives. This is participant-reported, was not rerun here, and is not an organizer-confirmed or projected score. We did not compare the pre-placement surface or complete registry.</p><p>The exact peer TIFF locally matches the mirror grid and has finite in-footprint values in [0,1], but its unmasked zero exterior fails the local <code>template-mask</code> profile even as it passes <code>finite-grid</code>. Neither check proves portal acceptance, and the earlier rejected file was unavailable. No new TIFF or slot was produced.</p><p><a href="data/session-30454eca-s2d36-audit.json">Nine comparisons &amp; validator receipt →</a> · <a href="data/peer-s2d36-card-21eec80b.json">Pinned original peer card ↗</a> · <a href="https://github.com/{esc('buffedlizard55-lab/GEMSDOE36')}/blob/{esc(s2d['peer']['commit'])}/docs/downloads/s2d36-run-card.json">Peer source ↗</a></p></section>
<section class="section panel prose" id="kpl36-conflict"><p class="eyebrow">Previously pinned peer recommendation / independent literal check</p><h2>GEMSDOE36 KPL-36: <span class="not-approved">DO NOT SUBMIT.</span></h2><p>The previously pinned peer page promoted KPL-36 EXP-3 after comparing against competing detectors but not counting the calibration lattice as a blocking reference; later source changes have not been scientifically audited here. We re-opened its exact pinned TIFF: <strong>{kpl_dots['candidate_dots_within_3px_of_lattice']:,} / {kpl_dots['candidate_dots']:,} dots ({kpl_dots['candidate_dot_overlap_fraction']:.2%})</strong> are within three pixels of that registered lattice. Your literal stop is over 70%, so this file is a duplicate under your protocol, regardless of the peer’s recommendation.</p><p>The peer reports <strong>{kpl_holdout['dti']:.4f} HOLDOUT-DTI</strong>, 95% CI [{kpl_holdout['ci95'][0]:.4f}, {kpl_holdout['ci95'][1]:.4f}], <code>{esc(kpl_holdout['evaluator_version'])}</code>, {kpl_holdout['withheld_positive_pixels']:,} withheld positives. That participant result was not independently rerun here and is not a leaderboard estimate. Its saved bytes pass the local <code>finite-grid</code> profile, not organizer acceptance; surface and full-registry comparisons were not performed in this audit.</p><p><a href="kpl36-lattice-audit-20261027.json">Measured bytes, hashes and conflict →</a> · <a href="{esc(kpl['peer_source']['repository'])}/blob/{esc(kpl['peer_source']['commit'])}/{esc(kpl['peer_source']['file'])}">Pinned peer TIFF · research reference only ↗</a></p></section>
<section class="section panel prose" id="cadg-submod-study-link"><p class="eyebrow">Prior CADG study / independent saved-byte audits</p><h2>CADG archive: <span class="not-approved">DO NOT SUBMIT.</span></h2><p>The advertised TIFF has <strong>{cadg_current['lattice']['candidate_dots_within_3px_of_lattice']:,} / {cadg_current['lattice']['candidate_dots']:,} dots ({cadg_current['lattice']['candidate_dot_overlap_fraction']:.2%})</strong> within three pixels of the full registered lattice. The older, distinct field also fails: <strong>37,635 / 37,654 (99.95%)</strong>. The earlier 99.73% figure used catalogue-excluded lattice cells and also fails. A selector cannot waive the stop.</p><p>Local format checks are not portal acceptance. The previously rejected upload was not provided, so its range-error cause remains unknown.</p><a href="cadg-submod/index.html">Prior study and forensic audit →</a> · <a href="cadg-submod/cadg-audit.json">Four saved-byte and ZIP checks →</a> · <a href="data/session-30454eca-cadg-lattice.json">Independent full/subset audit →</a></section>
<section class="section panel prose" id="parallel-control"><p class="eyebrow">Parallel session / research-only control</p><h2>A random control exists. It is not a submission.</h2><p>Another session generated a random off-catalogue TIFF and a matching encoding. Our independent audit finds <strong>{poisson_dots['candidate_dots_within_3px_of_lattice']:,} / {poisson_dots['candidate_dots']:,} dots ({poisson_dots['candidate_dot_overlap_fraction']:.2%})</strong> within three pixels of the registered lattice, so both encodings fail the literal uniqueness stop. No holdout score or complete surface comparison is available.</p><p>The rejected upload was not supplied, so the local [0,1] checks cannot prove the old portal error was fixed. The earlier run card lists only a subset of per-site overlaps and does not establish all-nine uniqueness.</p><a href="candidate.html">Research archive and corrected limits →</a> · <a href="parallel-poisson-audit-20261027.json">Saved-byte audit →</a></section>
{parallel_panel}
{inherited_section(inherited)}
<section class="section panel prose" id="ssp1-study-link"><p class="eyebrow">Separate preserved study / not directly comparable</p><h2>SSP1 research download: yes.<br>Competition upload: no.</h2><p>The isolated SSP1 portal preserves another session’s methods, negative run card and TIFF encodings. Its reported 99.8752% registered-lattice overlap fails the literal rule. Detector-only uniqueness is not all-registry clearance; its evaluator is not directly comparable to the prior bilateral card.</p><p><a href="ssp1/executive-summary.html">Open the scoped SSP1 executive review ↗</a></p></section>
<script src="source-status.js" defer></script>
<section class="section grid-two"><article class="panel"><p class="eyebrow">Understanding the reported 0.2778</p><h2>A leaner emission budget,<br>not proven new geology.</h2><p>H33 B2 on GEMSDOE32 is the highest supplied historical claim. In our independent, hash-pinned mirror audit, the GEMSDOE25 and GEMSDOE30 reference dot masks are equal. GEMSDOE32 is pixel-equivalent to the GEMSDOE30 mask after removing <strong>{h33['gemsdoe30_dots_removed_to_get_32']:,} dots at most two pixels from known catalogue faults</strong>; it adds none.</p><p>The official metric makes a lower false-positive burden plausible, but deleting dots can also increase missed faults. Hidden truth and a score-to-file receipt are unavailable, so this geometry does not prove causation or a higher future leaderboard result.</p><a class="link-button" href="h33-lineage-20261027.json">Exact historical geometry audit →</a> · <a href="research.html#h33">Scientific analysis →</a></article><article class="panel"><p class="eyebrow">Why a renamed file is not new</p><h2>The historical family trips the stop.</h2><p>The smallest of all 72 directed cross-winner overlaps is <strong>{min(p['overlap_3px'] for p in audit['pairs']):.2%}</strong>, above the 70% threshold. Compression, filenames and nodata encodings can change the hash while retaining the same predictions.</p><details><summary>View the nine-site geometric overlap matrix</summary>{heatmap(audit)}</details><p class="subtext">Continuous historical surfaces are not available. Their rank correlations are unknown; dot overlap alone is sufficient to reject these references.</p></article></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">This session / actual progress</p><h2>Resolve prerequisites. Don’t invent results.</h2></div><a href="data/readiness.json">Dated preflight snapshot ↗</a></div><div class="grid-two"><article class="panel"><h3>Recovered and verified</h3>{resolved}<p><a href="sources.html#data">Core grid, raw-band and sentinel audit →</a></p></article><article class="panel"><h3>Still blocking research</h3>{blockers}<p><a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41">Shared-template defect: existing upstream issue #41 ↗</a></p></article></div></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">Scientific queue / before implementation</p><h2>Four hypotheses. No performance claims.</h2><p>Qualitative improvement potential and cost; none is an assigned lane or a validated discovery.</p></div><a href="research.html">Mechanisms, layers &amp; viability →</a></div>{hypothesis_cards(hypotheses)}</section>
<section class="section" id="feed"><div class="section-heading"><div><p class="eyebrow">Source-change feed</p><h2>Current sources, separate from approval.</h2><p>Participant source refresh attempted {esc(feed['checked_utc'])}. A pinned commit is an observation, not an audit of its new files. Browser checks detect later source commits—not scores, reviews or permission.</p></div><button class="refresh-button" type="button" id="refresh-sources">Check source changes</button></div>{'<div class="source-grid">'+source_cards(feed)+'</div>'}<p class="subtext" id="feed-summary" aria-live="polite">Automatic source checks are read-only. Failed API access is shown as unknown; this observed snapshot is retained.</p></section>
<section class="evidence-strip"><div><h3>A valid raster is necessary. It is not enough.</h3><p>The published format, three explicit local encoding profiles, holdout evidence, semantic novelty and slot authorization are separate checks. The earlier blanket rejection of zero-outside files is withdrawn; no portal acceptance is claimed.</p></div><a class="link-button" href="executive-summary.html">How to make a submission →</a></section>'''
    emit(DOCS / "index.html", page("Executive summary", main))
    emit(DOCS / "summary.html", page("Executive summary", main))
    for path in ("executive-summary.html", "submission.html"):
        emit(DOCS / path, page("How to submit", guide() + shared_panel + parallel_panel, "guide"))
    research = f'''<div class="page-intro"><p class="eyebrow">Scientific research / preregistered proposals</p><h1 class="subtitle-page">Contrarian mechanisms.<br>Conservative evidence.</h1><p>The competition predicts previously unmapped faults, not directly geothermal vents. Geological plausibility is a hypothesis; only a leakage-safe, paired experiment can establish holdout improvement.</p></div><div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>No method lane was supplied. No geological experiment was run in this review session.</strong><p>These proposals were recorded before method implementation. “Untested” does not mean globally novel. New-data variants are not viable until the official bytes and required coverage are obtainable.</p></div></div>
{hypothesis_cards(hypotheses, detailed=True)}
<section class="section panel prose"><h2>Separate scoped hypothesis queue</h2><p>Another review independently ranked four conditional proposals: cross-scale magnetic/radiometric edge disagreement, repeated drainage-displacement graphs, paired alteration-front terminations and terrain-conditioned thermal asymmetry. They are not interchangeable with the concurrent queue above and neither review assigned a lane or ran a geological experiment.</p><p><a href="session-91270cac-hypotheses.md">Session 91270cac ranked mechanisms, mimics, sources and costs →</a> · <a href="session-12817d00-review.md">Concurrent review and prerequisites →</a> · <a href="session-91270cac-review.md">Changed-peer forensic review →</a> · <a href="session-e2903b2e-review.md">Final integrated review →</a></p></section>
<section class="section panel prose" id="h33"><p class="eyebrow">H33 B2 / mechanism vs inference</p><h2>Why thinning can help—and why that is not a forecast.</h2><p>The official DTI credits a ground-truth pixel with its best nearby prediction, not the sum of every nearby dot. Redundant dots can add false-positive mass without improving coverage. Removing those dots can improve emission efficiency; removing the wrong dots loses recall. The pinned B2 mask is exactly the GEMSDOE30 mask after removing 6,436 dots within two pixels of the mirrored catalogue; none were added. This observed geometry does not isolate a new geological signal or prove why its reported result differed.</p><p>The triangular kernel has zero credit exactly at 300 m. At alpha 0.2 and beta 0.8, missed faults are penalized more heavily than false positives. It is therefore wrong to infer that sparser is always better, or that one fixed dot count should be copied across geological settings.</p><p>Staff clarify that existing catalogue pixels are excluded in both rounds. A fold-local catalogue mask must exclude only visible faults, not withheld positives. A final submission already zeroed with the complete catalogue cannot stand in for an honest hide-and-recover prediction.</p><div class="score-disclaimer">Historical 0.2778 is an unverified owner report. No organizer receipt binds it to a hash, and no paired causal ablation is available. No leaderboard estimate is emitted.</div><a href="review.md">Full scientific review, uncertainty and next steps →</a></section>
<section class="section panel prose"><h2>What could mimic the signal?</h2><p>USGS describe GeoDAWN radiometrics as surface geology/soil information and magnetics as subsurface structure/geology information. Variable terrain clearance, flight geometry and levelling can create persistent line-like signatures. Lithologic contacts may explain cross-layer edges without a fault; stream capture can explain apparent drainage offsets; groundwater transport and seasonal sampling can explain thermal residuals.</p><p>Even a correct mapped-fault holdout has population shift: mapped/exposed faults are not necessarily representative of concealed expert-labeled faults. AUC below the canary threshold does not prove that feature lineage is leak-free. A passing format validator says nothing about those scientific issues.</p><p><a href="sources.html">Verified source excerpts and what they actually establish →</a> · <a href="geothermal-science-2026-10-27.md">Updated geological source and confounder notes →</a></p></section>'''
    pz, pn = poisson["files"]["zeros"], poisson["files"]["nan"]
    pm = poisson["measurements"]["zeros"]["lattice"]
    candidate_archive = f'''<div class="page-intro"><p class="eyebrow">Parallel session / retained research-only control</p><h1 class="subtitle-page">An archived random control.<br>Not a competition submission.</h1><p>This is an existing parallel-session artifact, not a geological hypothesis run by this review. No hidden leaderboard score or paired holdout is available.</p></div>
<div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — fails the literal registry stop.</strong><p>{pm['candidate_dots_within_3px_of_lattice']:,} of {pm['candidate_dots']:,} dots ({pm['candidate_dot_overlap_fraction']:.2%}) are within three pixels of the registered calibration lattice. The surface and complete registry were not independently compared.</p></div></div>
<section class="section panel prose"><h2>Original files · research only</h2><p>The zero and NaN encodings have the same in-footprint dot mask. Both saved TIFF/ZIP pairs are retained unchanged for research; these links do not imply scientific or portal approval.</p><div class="table-wrap"><table><thead><tr><th>Encoding</th><th>Research TIFF</th><th>SHA-256</th><th>Local profile</th><th>Submit?</th></tr></thead><tbody><tr><td>Zeros outside</td><td><a download href="{esc(pz['path'][5:])}">{esc(Path(pz['path']).name)}</a><br><a download href="{esc(pz['zip'][5:])}">Single-TIFF ZIP</a></td><td><code>{esc(pz['sha256'])}</code></td><td>finite-grid pass</td><td><strong>NO</strong></td></tr><tr><td>NaN outside</td><td><a download href="{esc(pn['path'][5:])}">{esc(Path(pn['path']).name)}</a><br><a download href="{esc(pn['zip'][5:])}">Single-TIFF ZIP</a></td><td><code>{esc(pn['sha256'])}</code></td><td>template-mask pass</td><td><strong>NO</strong></td></tr></tbody></table></div><p>Both comparisons use the participant-mirror grid, not an authenticated organizer template. Neither profile guarantees portal acceptance, and the earlier rejected file was not provided; no one can establish that its range error was fixed.</p></section>
<section class="section panel prose"><h2>Corrections to the earlier card</h2><p>The preserved original card claimed uniqueness against all nine focus sites, but listed only a subset of per-site overlap results. That broader claim is not established by the card. In any case, the independently reproduced lattice overlap already fails the user's required rule.</p><p>It also claimed that this random file resolved the prior upload error. There is no rejected-file evidence or portal receipt to support that statement. Earlier causal explanations or numerical leaderboard scenarios for H33 are not validated scores. The original JSON is retained as a historical record, not a decision source.</p><p><a href="parallel-poisson-audit-20261027.json">Independent saved-byte audit ↗</a> · <a href="evidence/candidate_poisson_20261027.json">Original card · contains superseded claims ↗</a> · <a href="h33-lineage-20261027.json">Verified H33 geometry ↗</a></p></section>'''
    emit(DOCS / "candidate.html", page("Parallel random control", candidate_archive))
    emit(DOCS / "research.html", page("Research queue", research, "research"))
    emit(DOCS / "hypotheses.html", page("Research queue", research, "research"))
    source_rows = []
    for claim in official["claims"]:
        quotes = claim.get("quotes", [claim["quote"]] if "quote" in claim else [])
        quotation = "".join(f'<blockquote>{esc(quote)}</blockquote>' for quote in quotes)
        source_rows.append(f'<tr><td><strong>{esc(claim["id"])}</strong></td><td>{esc(claim["claim"])}{quotation}</td><td><a href="{esc(claim["source"])}">Official source ↗</a><small>{esc(claim.get("verified_scope", claim.get("binary_obtainability", "See source record for limits.")))}</small></td></tr>')
    data = read("evidence/input-integrity.json")
    sources = f'''<div class="page-intro"><p class="eyebrow">Evidence / provenance and limitations</p><h1 class="subtitle-page">Know what each source proves.</h1><p>Official task pages define rules and physics context. Participant mirrors prove only hash consistency. A public leaderboard observation is not a submission-page receipt tied to our raster. Hypotheses and operator tests are separate from measured geological performance.</p></div>
<section class="panel prose"><h2>Dated official observations</h2><p>On {esc(observation['observed_utc_day'])} a single research fetch of the official public leaderboard displayed {esc(observation['public_leaderboard']['participant'])} first with <strong>{observation['public_leaderboard']['displayed_value']:.4f}</strong>. This is a dated public-page observation, not a per-file score receipt or a forecast. Automated DrivenData monitoring is disabled under the published terms; this snapshot is not live.</p><p>The official rules specify up to three submissions per week. The account’s actual remaining allowance is unknown; no slot is authorized. The official data page redirects unauthenticated requests to login.</p><p><a href="official-observation-20261027.json">Observation and limits ↗</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official leaderboard ↗</a></p></section>
<section class="section" id="data"><div class="section-heading"><div><p class="eyebrow">Data placement / local mirror</p><h2>Core bytes restored locally. Provenance kept explicit.</h2><p>Large mirrored inputs are ignored and must be restored again in a fresh checkout.</p></div></div><div class="grid-two"><article class="panel"><dl class="key-value"><dt>Grid</dt><dd>EPSG:{data['grid']['epsg']} · {data['grid']['height']} × {data['grid']['width']} · 100 m</dd><dt>Raw features</dt><dd>19 bands, restored from immutable participant mirrors</dd><dt>Footprint pixels</dt><dd>{data['counts']['footprint_valid_pixels']:,}</dd><dt>Catalogue positives</dt><dd>{data['counts']['positive_catalogue_label_pixels']:,}</dd><dt>Sentinel-affected pixels</dt><dd>{data['counts']['unique_footprint_pixels_with_any_sentinel']:,} unique footprint pixels; {data['counts']['total_sentinel_band_pixels_inside_footprint']:,} summed across bands</dd><dt>Derived cache</dt><dd>Not obtained; not privately regenerated</dd><dt>Organizer authentication</dt><dd>Not established by the mirror hashes. The mirror sample contains 60,988 catalogue positives, unlike the official all-absence sample description; <a href="sample-provenance-check.json">provenance audit ↗</a>.</dd></dl></article><article class="panel"><h3>Shared tool audit</h3><p>The source-locked evaluator drops pooled false-positive mass from an empty-truth cell. A synthetic operator test reproduces the defect, without evaluating a geological candidate. This does not show that any historical competition score was affected.</p><p>The tool also binarizes nonzero soft inputs. It cannot be trusted as a probability evaluator merely because it accepts a float array.</p><p><a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41">Existing central repair issue ↗</a> · <a href="tool-audit.json">Synthetic operator receipt ↗</a></p></article></div></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">Claim-by-claim source ledger</p><h2>Verified excerpts. Bounded conclusions.</h2><p>Transcribed excerpts from fetched pages; not hashes of the original HTML/PDF bytes. Full source retrieval or a resource index is not proof that every linked dataset was downloaded.</p></div><a href="official-claims.json">Machine-readable ledger ↗</a></div><div class="table-wrap"><table class="source-table"><thead><tr><th>Claim</th><th>Observation / exact excerpt</th><th>Source and verification scope</th></tr></thead><tbody>{''.join(source_rows)}</tbody></table></div></section>'''
    emit(DOCS / "sources.html", page("Evidence ledger", sources, "sources"))
    parallel = f'<div class="page-intro"><p class="eyebrow">Preserved research archive · do not submit</p><h1 class="subtitle-page">Different methods.<br>Unmet release gates.</h1><p>These TIFFs were generated by other sessions already merged into main. This review did not train or regenerate them. Their original negative cards are unchanged; the literal binary-lattice audit is independently reproduced here.</p></div>{inherited_section(inherited, True)}<section class="section panel prose"><h2>Original scoped run cards</h2><p><a href="data/gpc-run-card.json">GPC-3 ↗</a> · <a href="k3h1-run-card.json">K3-H1 ASGT hybrid ↗</a> · <a href="kanler-h1-run-card.json">KANLER-H1 DCAP-LHC ↗</a> · <a href="run-card.json">Bilateral radiometric/scarp ↗</a></p><p>Their HOLDOUT-DTI measurements use their stated versions, positives and CIs. They were not rerun or ranked against each other here. Detector-only/like-for-like novelty excludes a required lattice and is not literal all-registry clearance. No slot is authorized.</p></section>'
    emit(DOCS / "parallel-research.html", page("Parallel research archive", parallel))
    k3 = read("evidence/k3h1-run-card.json")
    h = k3["holdout"]
    k3_row = next(row for row in inherited["rows"] if "k3h1" in Path(row["file"]).name)
    emit(DOCS / "k3h1-report.md", f'''# K3-H1 archive — DO NOT SUBMIT

The existing TIFF has {k3_row['candidate_dots_within_3px_of_lattice']:,} / {k3_row['candidate_dots']:,} dots ({k3_row['candidate_dot_overlap_fraction']:.2%}) within three pixels of the registered lattice; the literal duplicate stop cannot be waived. See the [independent saved-byte audit](inherited-literal-audit.json).

The prior card reports {h['value']:.4f} HOLDOUT-DTI, 95% CI [{h['ci95'][0]:.4f}, {h['ci95'][1]:.4f}], evaluator `{h['evaluator_version']}`, {h['withheld_positives']:,} withheld positives. That result was not rerun here, is not an organizer score, and is not a leaderboard estimate. Local format compatibility does not establish portal acceptance; the rejected bytes were not provided.

The [original scoped report at the inherited commit](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/ee683eeff93ab9d5bbec802065963c6898a4190b/research/k3h1-report.md) is preserved, including superseded uniqueness, portal-error, causal-score and selection claims. It is not an upload guide or a basis for slot selection. The [original card](k3h1-run-card.json) is unchanged.
''')
    k3_body = f'<div class="page-intro"><p class="eyebrow">Prior K3-H1 research · negative</p><h1 class="subtitle-page">ASGT hybrid.<br>Not a promoted result.</h1><p>This prior scoped experiment has a negative card. It is not a new experiment from the current review, an organizer-confirmed result or a qualified weekly upload.</p></div><section class="section panel prose"><h2>Archived HOLDOUT-DTI observation</h2><p>Evaluator <code>{esc(h["evaluator_version"])}</code>; {h["withheld_positives"]:,} withheld positives; value {h["value"]:.4f}; 95% CI [{h["ci95"][0]:.4f}, {h["ci95"][1]:.4f}]. This archived measurement was not rerun here and does not establish an improving paired gain.</p><p><a href="k3h1-run-card.json">Unchanged scoped card ↗</a> · <a href="k3h1-report.md">Corrected archive context and original record ↗</a></p></section>{inherited_section(inherited)}'
    emit(DOCS / "k3h1.html", page("K3-H1 prior negative research", k3_body))
    current = {row["site"]: row for row in feed["rows"]}
    for row in audit["rows"]:
        other = sorted((pair for pair in audit["pairs"] if pair["candidate"] == row["repo"]), key=lambda x: -x["overlap_3px"])
        profiles = row["local_validation"]["encoding_profiles"]
        peer_list = "".join(f'<li>{pair["reference"]}: {pair["overlap_3px"]:.4%} directed overlap within 3 px</li>' for pair in other)
        source_row = current[row["repo"]]
        now = source_row if source_row.get("commit") else source_row.get("last_successful_source", {})
        site_findings = [f for f in peer_audit["findings"] if f["site"] == row["repo"]]
        site_stops = sum(f["status"] == "STOP_DUPLICATE" for f in site_findings)
        text = f'''<p class="breadcrumb"><a href="../index.html#comparison">← Priority-site comparison</a></p><div class="page-intro"><p class="eyebrow">Individual executive summary / {row['repo']}</p><h1 class="subtitle-page">Historical evidence.<br>No eligible new download.</h1><p>Best supplied historical claim: <strong>{row['owner_reported_leaderboard_score']:.4f}</strong>, owner-reported without a submission-page receipt. It is not an approved recommendation or an estimate for a new file.</p></div><div class="notice"><span class="icon" aria-hidden="true">!</span><div><strong>DO NOT SUBMIT — duplicate under your protocol.</strong><p>No new unique TIFF is available for this site. The historical reference exceeds the 70% directed overlap stop against priority peers. Estimated leaderboard score: not estimable. No slot selected.</p></div></div>
<div class="grid-two"><section class="panel"><h2>Exact historical file</h2><p><a href="{esc(historical_url(row))}">{esc(Path(row['file']).name)}</a></p><p>Forensic reference only; not a new competition download.</p><dl class="key-value"><dt>File SHA-256</dt><dd><code>{row['sha256']}</code></dd><dt>Source commit</dt><dd><code>{row['head']}</code></dd><dt>Positive dots</dt><dd>{row['dots']:,} · geometric audit</dd><dt>Template-mask profile</dt><dd>{'PASS' if profiles['template-mask'] else 'FAIL'} · local contract only</dd><dt>Finite-grid profile</dt><dd>{'PASS' if profiles['finite-grid'] else 'FAIL'} · local contract only</dd><dt>Portal acceptance</dt><dd>Unknown; local checks are not a receipt</dd><dt>New file / estimate</dt><dd>None / not estimable</dd></dl></section><section class="panel"><h2>Semantic-uniqueness result</h2><span class="tag negative">Stop duplicate</span><p>Comparison is candidate-to-reference, not a symmetric similarity. Dot hashes alone cannot establish novelty. Historical continuous-surface correlation is not measured.</p><ul>{peer_list}</ul></section></div>
<section class="section panel prose"><h2>What the best supplied historical file tells us</h2><p>{esc(method_note(row["repo"]))}</p><p>These are bounded interpretations of the supplied labels and the measured raster geometry, not verified model implementations or causal explanations. No defensible new-file score estimate is available.</p></section>
<section class="section panel"><h2>Current source snapshot</h2><p>The historical file above is pinned independently from the newer homepage. Homepage statements are participant claims, not this project’s selector decision.</p><p>At the frozen {esc(changes['current_checked_utc'])} tree snapshot, {len(site_findings)} added or modified TIFF files were checked against the registered lattice; {site_stops} exceeded the literal duplicate threshold. This count includes encoding twins. Zero changed files is not a uniqueness pass, and later changes are not covered.</p><p><a href="{esc(now.get('source_url','../sources.html'))}">Observed participant page at {esc(str(now.get('commit') or 'unknown')[:10])} ↗</a> · <a href="../data/changed-peer-audit-91270cac.json">Changed-file forensic receipt ↗</a></p><p><a href="../research.html">Shared-family performance interpretation and conditional research queue →</a></p></section>'''
        if row["repo"] == "GEMSDOE36":
            text += f'''<section class="section notice"><span class="icon" aria-hidden="true">!</span><div><strong>Newer S2D-36 and earlier KPL-36 both fail the literal uniqueness rule.</strong><p>The newer S2D peer card is negative; our independent saved-dot check found {s2d_lattice['candidate_dot_overlap_fraction']:.2%} overlap with the required lattice. Its participant-reported {s2d_holdout['value']:.4f} HOLDOUT-DTI, 95% CI [{s2d_holdout['ci95'][0]:.4f}, {s2d_holdout['ci95'][1]:.4f}], <code>{esc(s2d_holdout['evaluator_version'])}</code>, {s2d_holdout['withheld_positives']:,} withheld positives, was not rerun here or organizer-confirmed.</p><p>The earlier KPL-36 peer promotion also conflicts with the rule: {kpl_dots['candidate_dot_overlap_fraction']:.2%} lattice overlap. Neither file is approved here.</p><p><a href="../data/session-30454eca-s2d36-audit.json">Newer forensic receipt →</a> · <a href="../kpl36-lattice-audit-20261027.json">Earlier forensic receipt →</a></p></div></section>'''
        emit(DOCS / "sites" / f"{row['repo']}.html", page(row["repo"] + " executive summary", text, prefix="../"))
    emit(DOCS / "upstream-prerequisites-20261028.json", (ROOT / "evidence/session-20261028-upstream-prerequisites.json").read_text())
    for source, dest in [("evidence/parallel-poisson-audit-20261027.json", "parallel-poisson-audit-20261027.json"), ("evidence/kpl36-lattice-audit-20261027.json", "kpl36-lattice-audit-20261027.json"), ("evidence/h33-lineage-20261027.json", "h33-lineage-20261027.json"), ("evidence/official-observation-20261027.json", "official-observation-20261027.json"), ("evidence/official-claims-20261026.json", "official-claims.json"), ("evidence/shared_tool_audit.json", "tool-audit.json"), ("evidence/input-integrity.json", "input-integrity.json"), ("evidence/session-7d1e577d-verification.json", "verification.json"), ("evidence/inherited_literal_audit.json", "inherited-literal-audit.json"), ("evidence/sample-provenance-check.json", "sample-provenance-check.json"), ("evidence/session-e2903b2e-upstream-prerequisites.json", "upstream-prerequisites-20261027.json"), ("knowledge/geothermal-science-2026-10-27.md", "geothermal-science-2026-10-27.md")]:
        emit(DOCS / dest, (ROOT / source).read_text())
    for name in ("review", "hypotheses", "verification", "session-12817d00-review", "session-5c1613da-review", "session-91270cac-review", "session-91270cac-hypotheses", "session-30454eca-review", "session-30454eca-hypotheses", "session-e2903b2e-review", "session-0f36badb-review"):
        emit(DOCS / f"{name}.md", (ROOT / "research" / f"{name}.md").read_text())

    for src, destinations in [
        ("evidence/run-card.json", [ROOT / "run-card.json", DOCS / "run-card.json", DOCS / "data/run-card.json", DOCS / "data/run_card.json"]),
        ("evidence/run_card.json", [DOCS / "data/gpc-run-card.json"]),
        ("evidence/session-7d1e577d-run-card.json", [DOCS / "data/session-7d1e577d-run-card.json"]),
        ("evidence/session-52a91352-run-card.json", [DOCS / "data/session-52a91352-run-card.json"]),
        ("evidence/session-12817d00-run-card.json", [DOCS / "data/session-12817d00-run-card.json"]),
        ("evidence/session-5c1613da-run-card.json", [DOCS / "data/session-5c1613da-run-card.json"]),
        ("evidence/session-5c1613da-cadg-audit.json", [DOCS / "data/session-5c1613da-cadg-audit.json"]),
        ("evidence/session-91270cac-run-card.json", [DOCS / "data/session-91270cac-run-card.json"]),
        ("evidence/session-30454eca-run-card.json", [DOCS / "data/session-30454eca-run-card.json"]),
        ("evidence/session-e2903b2e-run-card.json", [DOCS / "data/session-e2903b2e-run-card.json"]),
        ("evidence/session-20261028-run-card.json", [DOCS / "data/session-20261028-run-card.json"]),
        ("evidence/session-e2903b2e-verification.json", [DOCS / "data/session-e2903b2e-verification.json"]),
        ("evidence/session-30454eca-saturation.json", [DOCS / "data/session-30454eca-saturation.json"]),
        ("evidence/session-30454eca-s2d36-audit.json", [DOCS / "data/session-30454eca-s2d36-audit.json"]),
        ("evidence/session-30454eca-cadg-lattice.json", [DOCS / "data/session-30454eca-cadg-lattice.json"]),
        ("evidence/peer-s2d36-card-21eec80b.json", [DOCS / "data/peer-s2d36-card-21eec80b.json"]),
        ("evidence/registry_saturation_20261026.json", [DOCS / "data/registry_saturation.json"]),
        ("evidence/feature_cache_recovery_20261026.json", [DOCS / "data/feature_cache_recovery.json"]),
        ("evidence/recovery-run-card.json", [DOCS / "data/recovery-run-card.json"]),
        ("registry/shared_template_pins.json", [DOCS / "data/shared_template_pins.json"]),
    ]:
        for destination in destinations:
            emit(destination, (ROOT / src).read_text())
    if check_only:
        stale = [str(path.relative_to(ROOT)) for path, content in outputs.items() if not path.is_file() or path.read_text() != content]
        if stale:
            raise ValueError("Generated site is stale: " + ", ".join(stale))
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(check_only=parser.parse_args().check)
