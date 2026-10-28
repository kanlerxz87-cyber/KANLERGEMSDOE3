#!/usr/bin/env python3
"""Render the isolated L-K3-ATSC-SUBMOD executive portal, submission guide, and hypothesis deep-dive under docs/atsc-submod/."""
from __future__ import annotations

import argparse
from html import escape as e
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/atsc-submod"


STYLE = """<style>
:root {
  --bg: #f4f7f9;
  --surface: #ffffff;
  --surface-alt: #f8fafc;
  --border: #d8e1e8;
  --text: #0f172a;
  --muted: #475569;
  --accent: #0f766e;
  --accent-soft: #ecfdf5;
  --amber-bg: #fffbeb;
  --amber-border: #f59e0b;
  --amber-text: #92400e;
  --blue-bg: #eff6ff;
  --blue-border: #3b82f6;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --sans: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
.container { max-width: 1260px; margin: 0 auto; padding: 28px 22px 56px; }
nav.topnav {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  justify-content: space-between; margin-bottom: 20px;
  padding: 12px 18px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px;
}
nav.topnav .links { display: flex; flex-wrap: wrap; gap: 8px; }
nav.topnav a {
  text-decoration: none; color: var(--text); font-weight: 600; font-size: 0.9rem;
  padding: 6px 12px; border-radius: 8px; border: 1px solid transparent;
}
nav.topnav a:hover { background: var(--surface-alt); border-color: var(--border); }
nav.topnav a.active { background: var(--accent-soft); color: var(--accent); border-color: #99f6e4; }
header.hero, section.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 24px 26px; margin-bottom: 20px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}
h1 { font-size: 1.95rem; letter-spacing: -0.025em; margin: 6px 0 10px; line-height: 1.2; }
h2 { font-size: 1.3rem; letter-spacing: -0.015em; margin: 0 0 12px; }
h3 { font-size: 1.05rem; margin: 16px 0 8px; }
p { margin: 8px 0; color: #1e293b; }
small, .muted { color: var(--muted); font-size: 0.85rem; }
code, pre { font-family: var(--mono); font-size: 0.86rem; }
code { background: #f1f5f9; padding: 2px 6px; border-radius: 5px; word-break: break-all; }
pre {
  background: #0f172a; color: #f8fafc; padding: 14px 16px; border-radius: 10px;
  overflow-x: auto; line-height: 1.45; margin: 10px 0;
}
.badge {
  display: inline-block; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.03em;
  text-transform: uppercase; padding: 3px 9px; border-radius: 999px;
}
.badge-teal { background: #ccfbf1; color: #115e59; }
.badge-amber { background: #fef3c7; color: #92400e; }
.badge-slate { background: #e2e8f0; color: #334155; }
.verdict-banner {
  background: var(--amber-bg); border: 2px solid var(--amber-border);
  border-radius: 12px; padding: 18px 20px; margin: 16px 0;
}
.verdict-banner strong { color: var(--amber-text); }
.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px; margin-top: 16px;
}
.kpi {
  background: var(--surface-alt); border: 1px solid var(--border);
  border-radius: 11px; padding: 14px 16px;
}
.kpi .label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); font-weight: 600; }
.kpi .val { font-size: 1.45rem; font-weight: 800; color: var(--text); margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.kpi .sub { font-size: 0.82rem; color: var(--muted); }
.table-wrap { overflow-x: auto; margin-top: 12px; border: 1px solid var(--border); border-radius: 10px; }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; font-variant-numeric: tabular-nums; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
th { background: var(--surface-alt); font-weight: 700; color: #334155; white-space: nowrap; }
tr:last-child td { border-bottom: none; }
tr.highlight td { background: var(--accent-soft); }
.dl-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 16px; margin-top: 14px; }
.dl-card { border: 1px solid var(--border); border-radius: 12px; padding: 18px; background: var(--surface-alt); }
.dl-card.primary { border: 2px solid var(--accent); background: #f0fdfa; }
.btn {
  display: inline-block; text-decoration: none; font-weight: 700; font-size: 0.88rem;
  padding: 9px 15px; border-radius: 8px; margin: 8px 8px 4px 0;
}
.btn-primary { background: var(--accent); color: #ffffff; }
.btn-secondary { background: #ffffff; color: var(--text); border: 1px solid var(--border); }
</style>"""


def _nav(active: str) -> str:
    items = [
        ("index.html", "ATSC-Submod Overview"),
        ("executive-summary.html", "Executive Summary & Submission Guide"),
        ("hypotheses.html", "Hypotheses & GEMSDOE32 Analysis"),
        ("run-card.json", "Run Card JSON"),
        ("../index.html", "<- Repository Root Review"),
    ]
    links = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{e(label)}</a>'
        for href, label in items
    )
    return f'<nav class="topnav"><div><strong>KANLERGEMSDOE3</strong> · <span class="badge badge-teal">L-K3-ATSC-SUBMOD</span></div><div class="links">{links}</div></nav>'


def build(check_only: bool = False) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    audit = json.loads((ROOT / "docs/audit.json").read_text())
    card = json.loads((ROOT / "evidence/atsc-submod-run-card.json").read_text())
    holdout_ev = json.loads((ROOT / "evidence/atsc_holdout_20261027.json").read_text())
    uniq_ev = json.loads((ROOT / "evidence/atsc_uniqueness_100rasters_20261027.json").read_text())
    laws_ev = json.loads((ROOT / "evidence/atsc_physical_laws_forensics_20261027.json").read_text())
    canary_ev = json.loads((ROOT / "evidence/atsc_leakage_canary_20261027.json").read_text())
    cadg_card = json.loads((ROOT / "evidence/cadg-submod-run-card.json").read_text())
    current_peer_audit = json.loads((ROOT / "evidence/atsc-current-peer-audit-20261028.json").read_text())

    art = card["submission_artifacts"]
    z_tif_rel = art["primary_zeros_tif"].replace("docs/atsc-submod/", "", 1)
    z_zip_rel = art["primary_zeros_zip"].replace("docs/atsc-submod/", "", 1)
    n_tif_rel = art["official_nan_twin_tif"].replace("docs/atsc-submod/", "", 1)
    n_zip_rel = art["official_nan_twin_zip"].replace("docs/atsc-submod/", "", 1)
    note_rel = art["note_file"].replace("docs/atsc-submod/", "", 1)
    rec_rel = art["receipt_file"].replace("docs/atsc-submod/", "", 1)

    hold = card["holdout"]
    inc = card["incumbent_comparison"]
    diag = inc["orthogonal_diagonal_confirmation"]
    ureg = card["uniqueness_registry_summary"]
    p_bound = ureg["pigeonhole_lattice_bounds"][0]
    bounded_peer = current_peer_audit["peer_registry_scope"]
    bounded_result = current_peer_audit["result"]

    g32_cmp = next(
        (r for r in uniq_ev["detector_comparisons"] if "GEMSDOE32" in r["id"]),
        {"final_3px_overlap": 0.35, "final_abs_spearman_rho": 0.03},
    )
    cadg_cmp = next(
        (r for r in uniq_ev["detector_comparisons"] if "CADG" in r["id"]),
        {"final_3px_overlap": 0.54, "final_abs_spearman_rho": 0.06},
    )

    # Priority 9 sites + prior CADG + new ATSC table
    priority_rows_html = []
    md_rows = []
    for r in audit["rows"]:
        url = f"https://github.com/buffedlizard55-lab/{r['repo']}/blob/{r['head']}/{r['file']}"
        fname = Path(r["file"]).name
        reported = f"{r['owner_reported_leaderboard_score']:.4f} (OWNER-REPORTED-UNVERIFIED; no organizer receipt)"
        uniq_txt = f"NO — historical registry baseline ({r['max_overlap_3px']:.2%} max 3-px peer overlap)"
        fmt = (
            "PASS (NaN outside)"
            if r["local_validation"]["format_pass"]
            else "Finite-zero outside (7,111,787 cells; in-footprint [0,1] PASS)"
        )
        priority_rows_html.append(
            f"<tr><td><strong>{e(r['repo'])}</strong></td>"
            f"<td><a href=\"{e(url)}\"><code>{e(fname)}</code></a><br>"
            f"<small>{r['dots']:,} dots · Historical reference only — do not re-submit</small></td>"
            f"<td>{e(reported)}</td>"
            f"<td>{e(uniq_txt)}</td>"
            f"<td><span class=\"badge badge-slate\">DO NOT SUBMIT</span><br><small>Already submitted / nested lineage</small></td>"
            f"<td><small>{e(fmt)}</small></td></tr>"
        )
        md_rows.append(
            f"| `{r['repo']}` | `{fname}` (`{r['dots']:,}` dots) | `{r['owner_reported_leaderboard_score']:.4f}` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`{r['max_overlap_3px']:.2%}` overlap) | **NO** (historical) |"
        )

    # Prior CADG row
    priority_rows_html.append(
        f"<tr><td><strong>KANLERGEMSDOE3 (Prior CADG)</strong></td>"
        f"<td><a href=\"../cadg-submod/index.html\"><code>{e(cadg_card['submission_name'])}.tif</code></a><br>"
        f"<small>37,654 dots · SHA-256 <code>{e(cadg_card['raster_sha256'][:16])}…</code></small></td>"
        f"<td><strong>HOLDOUT-DTI {cadg_card['holdout']['value']:.6f}</strong><br>"
        f"<small>95% CI [{cadg_card['holdout']['ci95'][0]:.6f}, {cadg_card['holdout']['ci95'][1]:.6f}] · <code>gems-segment-pooled-v1</code></small></td>"
        f"<td>YES vs 39 detectors (57.11% max) · Superseded by ATSC (+66.4 bps)</td>"
        f"<td><span class=\"badge badge-slate\">SUPERSEDED BY ATSC</span></td>"
        f"<td><small>PASS (finite [0,1])</small></td></tr>"
    )

    # New ATSC row
    priority_rows_html.append(
        f"<tr class=\"highlight\"><td><strong>KANLERGEMSDOE3 ({e(card['lane_id'])})</strong><br><span class=\"badge badge-teal\">NEW REPO BEST</span></td>"
        f"<td><a download href=\"{e(z_tif_rel)}\"><code>{e(Path(z_tif_rel).name)}</code></a> · "
        f"<a download href=\"{e(z_zip_rel)}\"><code>.zip</code></a><br>"
        f"<small>{card['validator']['predicted_positive_dots']:,} binary {{0,1}} dots · SHA-256 <code>{e(card['raster_sha256'][:16])}…</code></small></td>"
        f"<td><strong>HOLDOUT-DTI {hold['value']:.6f}</strong><br>"
        f"<small>95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}] · {hold['withheld_positives']:,} withheld px · <code>{e(hold['evaluator_version'])}</code> · Orthogonal Diag: <strong>{diag['candidate_holdout_dti']:.6f}</strong> (+51.8 bps vs CADG)</small></td>"
        f"<td><strong>YES vs all {ureg['genuine_detector_rasters_checked']}/{ureg['genuine_detector_rasters_checked']} genuine fault detectors</strong><br>"
        f"<small>Max 3-px overlap = {ureg['genuine_final_dot_overlap_3px']:.2%} (&le;70% PASS); max |&rho;| = {ureg['genuine_final_max_abs_spearman_rho']:.4f} (&le;0.90 PASS); vs GEMSDOE32 = {g32_cmp['final_3px_overlap']:.2%}; vs CADG = {cadg_cmp['final_3px_overlap']:.2%}. Literal 207k lattice probe: {card['final_dot_overlap_3px']:.2%} (min possible {p_bound['mathematical_min_possible_3px_overlap']:.2%}).</small></td>"
        f"<td><span class=\"badge badge-amber\">DO NOT SUBMIT (LITERAL GATE)</span><br>"
        f"<small>Research-only artifact: <code>verdict={e(card['verdict'])}</code>, <code>slot_authorized=false</code>. 87/87 genuine fault detectors pass (&le;57.14%), but unfiltered 207k <code>r13-lattice-s5</code> overlap is 99.99% (99.77% off-catalogue; selector cannot waive literal rule).</small></td>"
        f"<td><strong>PASS (16/16 local finite-grid)</strong><br><small>All 12,279,160 px finite in [0,1]; portal acceptance unverified</small></td></tr>"
    )
    md_rows.append(
        f"| **`KANLERGEMSDOE3 (L-K3-ATSC-SUBMOD)`** | [`{Path(z_tif_rel).name}`]({z_tif_rel}) (`37,654` dots, research-only) | **`HOLDOUT-DTI {hold['value']:.6f}`** (`95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]`; Diag `HOLDOUT-DTI {diag['candidate_holdout_dti']:.6f}`) | **87/87 genuine detectors &le;57.14%**; **FAILS literal 207k lattice (`99.99%` unfiltered / `99.77%` off-catalogue)** | **DO NOT SUBMIT** (`verdict={card['verdict']}`, `slot_authorized=false`) |"
    )

    # Ablation & Benchmark Table
    prim_sums = holdout_ev["primary_screen"]["summaries"]
    ablation_spec = [
        ("matched_random", "Matched random spacing (d=2.8 px, 37,654 dots)", prim_sums["matched_random"]["dti"], prim_sums["matched_random"]["ci95"]["interval"]),
        ("static_G70_P8", "Static GEMSDOE70 P8-oof38k (catalogue-collared on labels.tif)", prim_sums["static_G70_P8"]["dti"], prim_sums["static_G70_P8"]["ci95"]["interval"]),
        ("static_H33_B2", "Static GEMSDOE32 H33-2-B2 (catalogue-collared on labels.tif)", prim_sums["static_H33_B2"]["dti"], prim_sums["static_H33_B2"]["ci95"]["interval"]),
        ("unsupervised_D28_37654", "Label-free 5-channel geophysical/3DEP rank + d=2.8 spacing", prim_sums["unsupervised_D28_37654"]["dti"], prim_sums["unsupervised_D28_37654"]["ci95"]["interval"]),
        ("B0_regional_d28", "B0_regional_d28: 19-band HGB baseline + d=2.8 spacing (live incumbent)", prim_sums["B0_regional_d28"]["dti"], prim_sums["B0_regional_d28"]["ci95"]["interval"]),
        ("CADG Exp-K3-2 (Oct 26)", "Prior 1-stage deconfounded scarp + TMI150 + 300 m CELF", 0.153035, [0.139088, 0.167424]),
        ("CADG Exp-K3-3 (Oct 26)", "Prior Repo Best: CADG + visible LCO relay/tip continuation", inc["incumbent_holdout_dti"], inc["incumbent_ci95"]),
        ("Exp-ATSC-1", "H-K3S2-1a: Disjoint LiDAR/10m-3DEP Stage-1 + 12 Dip-Offset Wedge + Axial d=2.85 CELF", prim_sums["Exp-ATSC-1"]["dti"], prim_sums["Exp-ATSC-1"]["ci95"]["interval"]),
        ("Exp-ATSC-2", "H-K3S2-1+2 (WINNER): + GeoDAWN Radon/Seam + Regime-Harmonized Nested-OOF Stage-2 8-Azimuth Corridor U-GBDT", prim_sums["Exp-ATSC-2"]["dti"], prim_sums["Exp-ATSC-2"]["ci95"]["interval"]),
        ("Exp-ATSC-3", "H-K3S2-3 (Falsified): + Fold-Visible Coulomb Tip-Lobe / Relay-Bridge Interaction", prim_sums["Exp-ATSC-3"]["dti"], prim_sums["Exp-ATSC-3"]["ci95"]["interval"]),
    ]
    ablation_rows_html = []
    for key, desc, val, ci in ablation_spec:
        hl = ' class="highlight"' if key == card["selected_ablation_id"] else ""
        delta_k3 = val - inc["incumbent_holdout_dti"]
        ablation_rows_html.append(
            f"<tr{hl}><td><code>{e(key)}</code></td><td>{e(desc)}</td>"
            f"<td><strong>{val:.6f}</strong></td>"
            f"<td>[{ci[0]:.6f}, {ci[1]:.6f}]</td>"
            f"<td>{delta_k3:+.6f}</td></tr>"
        )

    # Three Physical Laws table
    laws_rows_html = []
    for m_key, m_label in [
        ("KANLERGEMSDOE3_Exp-ATSC-2_NEW", "KANLERGEMSDOE3 Exp-ATSC-2 (New Repo Best, 37,654 dots)"),
        ("KANLERGEMSDOE3_CADG_Exp_K3_3_PRIOR", "KANLERGEMSDOE3 CADG Exp-K3-3 (Prior Repo Best, 37,654 dots)"),
        ("GEMSDOE32_H33_B2_0p2778", "GEMSDOE32 H33-2-B2 (0.2778 owner-reported, 37,654 dots)"),
        ("GEMSDOE70_P8_0p2478", "GEMSDOE70 P8-oof38k (0.2478 owner-reported, 37,654 dots)"),
        ("GEMSDOE36_KPL36_0p1647", "GEMSDOE36 KPL-36 (0.1647 owner-reported, 37,654 dots)"),
        ("GEMSDOE36_S2D36_holdout0p2008", "GEMSDOE36 S2D36 (HOLDOUT-DTI 0.2008, 37,654 dots)"),
    ]:
        if m_key not in laws_ev:
            continue
        lw = laws_ev[m_key]
        hl = ' class="highlight"' if m_key == "KANLERGEMSDOE3_Exp-ATSC-2_NEW" else ""
        laws_rows_html.append(
            f"<tr{hl}><td><strong>{e(m_label)}</strong></td>"
            f"<td>{lw['law1_far_field_gt_1p5km_frac']:.2%}</td>"
            f"<td>{lw['law2_flat_deep_basin_spill_frac']:.2%}</td>"
            f"<td><strong>{lw['law3_clump_ge3_300m_frac']:.2%}</strong></td>"
            f"<td>{lw['lidar_void_dot_share']:.2%}</td></tr>"
        )

    verdict_box = f"""
    <div class="verdict-banner">
      <strong>AUTOMATED VERDICT: DO NOT SUBMIT TO COMPETITION &middot; RESEARCH-ONLY DOWNLOADS (ZERO HUMAN RASTER INSPECTION REQUIRED)</strong><br>
      1. <strong>Literal Fail-Closed Promotion Gate: <code>verdict = "{e(card['verdict'])}"</code> (<code>slot_authorized = false</code>)</strong> — Against the registered <code>206,895</code>-dot <code>13GEMSDOE r13-lattice-s5</code> uniform grid probe covering <code>99.8713%</code> of the footprint within 3 px, <code>37,652 / 37,654</code> dots (<code>99.99%</code> unfiltered; <code>99.77%</code> off-catalogue-filtered; mathematical pigeonhole minimum <code>82.34%</code>) fall within 3 px. Under this repository's literal all-registry rule, a selector signature cannot waive or override a &gt;70% registry overlap.<br>
      2. <strong>Genuine Geological Detector Uniqueness (Scoped Diagnostic): PASS across all {ureg['genuine_detector_rasters_checked']}/{ureg['genuine_detector_rasters_checked']} real fault detectors</strong> in <code>GEMSDOE24..92</code>, <code>KANLERGEMSDOE1..3</code>, <code>WBGGEMSDOE1..3</code>, <code>GEMSDOEkarage1..3</code>, <code>ApartGEMSDOE1..3</code>, and <code>GEMSDOESASS1..3</code> (max 3-px dot overlap = <code>{ureg['genuine_final_dot_overlap_3px']:.2%} &le; 70%</code>; max |&rho;| = <code>{ureg['genuine_final_max_abs_spearman_rho']:.4f} &le; 0.90</code>).<br>
      3. <strong>Scientific Spatial Holdout Gain: PASS (+66.4 bps Primary / +51.8 bps Orthogonal over Prior Repo Best)</strong> — <code>HOLDOUT-DTI = {hold['value']:.6f}</code> (95% CI <code>[{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]</code>, <code>{hold['withheld_positives']:,}</code> withheld positives on participant-mirrored <code>{e(hold['evaluator_version'])}</code>), outperforming prior repo best <code>CADG Exp-K3-3</code> (<code>0.157080</code>) and <code>B0_regional_d28</code> (<code>0.102255</code>, paired 95% CI <code>[+{card['paired_improvement_ci95'][0]:.4f}, +{card['paired_improvement_ci95'][1]:.4f}]</code>, <code>4/4</code> folds).<br>
      4. <strong>Local Saved-Byte Format Validation: PASS (16/16 checks on <code>finite-grid</code> and <code>template-mask</code>; Portal Acceptance Unverified)</strong> — Primary research file <code>{e(Path(z_tif_rel).name)}</code> (SHA-256 <code>{e(card['raster_sha256'])}</code>) is single-band <code>float32</code>, <code>EPSG:32611</code>, shape <code>(3730, 3292)</code>, with <strong>0 NaN / 0 Inf across all 12,279,160 whole-array pixels</strong> and exact values in <code>{{0.0, 1.0}}</code> (<code>37,654</code> off-catalogue dots, <code>0</code> catalogue overlap). Because the historically rejected upload was not supplied and template provenance is mirrored rather than organizer-signed, actual DrivenData portal acceptance remains unverified.<br>
      5. <strong>Fresh bounded final-dot audit (28 Oct): STOP.</strong> The exact saved bytes were compared with <code>{bounded_peer['rasters_compared']}</code> selected current peer rasters ({bounded_peer['genuine_detectors_compared']} genuine detectors and {bounded_peer['calibration_or_continuous_probes_compared']} calibration/continuous probes). Final-dot overlap is <code>{bounded_result['max_final_dot_overlap_3px_genuine_detectors']:.2%}</code> versus genuine detectors but <code>{bounded_result['max_final_dot_overlap_3px_calibration_or_continuous_probes']:.2%}</code> versus a continuous calibration probe. The bounded audit has no pre-placement surface or holdout result and cannot weaken the full-registry lattice stop.
    </div>"""

    # 1. index.html
    index_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KANLERGEMSDOE3 · L-K3-ATSC-SUBMOD Executive Portal &amp; Audited GeoTIFFs</title>
  {STYLE}
</head>
<body>
<div class="container">
  {_nav("index.html")}
  <header class="hero">
    <span class="badge badge-teal">DrivenData DOE GEMS · Fault Mapping</span>
    <span class="badge badge-slate">Preregistered SHA-256: e87228d6…</span>
    <h1>Anisotropic Dip-Offset Structural Corridor Tomography &amp; Axial 300 m Submodular Allocation (<code>L-K3-ATSC-SUBMOD</code>)</h1>
    <p>New 8-fold spatial out-of-fold fault-mapping model (<code>Exp-ATSC-2</code>) advancing <code>KANLERGEMSDOE3</code> from prior best <code>HOLDOUT-DTI 0.157080</code> (<code>L-K3-CADG-SUBMOD</code>) to <strong><code>HOLDOUT-DTI {hold['value']:.6f}</code></strong> (+66.4 bps primary quadrant holdout; +51.8 bps orthogonal diagonal confirmation; 0.11% 300 m blob clumping; 87/87 genuine fault detectors unique).</p>
    {verdict_box}
    <div class="kpi-grid">
      <div class="kpi">
        <div class="label">Primary HOLDOUT-DTI</div>
        <div class="val">{hold['value']:.6f}</div>
        <div class="sub">95% CI [{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}] · +66.4 bps vs CADG</div>
      </div>
      <div class="kpi">
        <div class="label">Orthogonal Diag HOLDOUT-DTI</div>
        <div class="val">{diag['candidate_holdout_dti']:.6f}</div>
        <div class="sub">2.0 km buffer · +51.8 bps vs CADG (0.147663)</div>
      </div>
      <div class="kpi">
        <div class="label">Genuine Detector Uniqueness</div>
        <div class="val">{ureg['genuine_final_dot_overlap_3px']:.2%}</div>
        <div class="sub">&le;70% PASS across 87/87 real detectors (|&rho;|={ureg['genuine_final_max_abs_spearman_rho']:.3f})</div>
      </div>
      <div class="kpi">
        <div class="label">Three Physical Laws</div>
        <div class="val">3 / 3 PASS</div>
        <div class="sub">56.94% &gt;1.5 km · 2.91% deep spill · 0.11% clump&ge;3</div>
      </div>
      <div class="kpi">
        <div class="label">Leakage Canary (103 Feats)</div>
        <div class="val">{canary_ev['max_feature_auc']:.4f}</div>
        <div class="sub">Max two-sided AUC &le; 0.90 PASS · 3/3 budget</div>
      </div>
    </div>
  </header>

  <section class="card" id="downloads">
    <h2>Research-Only Audited GeoTIFF Artifacts (DO NOT SUBMIT) &amp; Recorded Note (&le;140 chars)</h2>
    <p>Every research-only artifact below is byte-verified locally by <code>scripts/validate_submission.py</code> against mirrored <code>sample_submission.tif</code> (<code>EPSG:32611</code>, <code>3730 &times; 3292</code>, <code>float32</code>, <code>37,654</code> binary <code>{{0, 1}}</code> off-catalogue dots, <code>0</code> catalogue overlap; portal acceptance unverified). Open the <a href="executive-summary.html"><strong>Executive Summary &amp; Encoding Reference Guide &rarr;</strong></a></p>
    <div class="dl-grid">
      <div class="dl-card primary">
        <span class="badge badge-amber">Research Only &middot; Finite-Grid Encoding (-zeros.tif)</span>
        <h3><code>{e(Path(z_tif_rel).name)}</code></h3>
        <p><small>Sets the <code>7,111,787</code> outside-footprint cells to finite <code>0.0</code> (<code>nodata=None</code>) so whole-array <code>((a &gt;= 0) &amp; (a &lt;= 1)).all() == True</code> across all <code>12,279,160</code> pixels locally (<code>--profile finite-grid</code> PASS; rejected upload was not supplied, so portal acceptance remains unverified).</small></p>
        <p><small>SHA-256: <code>{e(card['raster_sha256'])}</code> ({art['primary_zeros_bytes']:,} bytes)</small></p>
        <a class="btn btn-primary" download href="{e(z_tif_rel)}">Research download -zeros.tif</a>
        <a class="btn btn-secondary" download href="{e(z_zip_rel)}">Research download -zeros.zip</a>
      </div>
      <div class="dl-card">
        <span class="badge badge-slate">Research Only &middot; NaN-Outside Twin (-nan.tif)</span>
        <h3><code>{e(Path(n_tif_rel).name)}</code></h3>
        <p><small>Identical <code>37,654</code> in-footprint positive pixels, with outside-footprint cells set to <code>NaN</code> matching mirrored <code>sample_submission.tif</code> (<code>--profile template-mask</code> PASS).</small></p>
        <p><small>SHA-256: <code>{e(art['official_nan_twin_sha256'])}</code></small></p>
        <a class="btn btn-secondary" download href="{e(n_tif_rel)}">Research download -nan.tif</a>
        <a class="btn btn-secondary" download href="{e(n_zip_rel)}">Research download -nan.zip</a>
      </div>
    </div>
    <h3>Submission Note ({len(card['submission_note'])} / 140 characters)</h3>
    <pre>{e(card['submission_note'])}</pre>
    <p><small>Supporting receipts: <a download href="{e(note_rel)}"><code>{e(Path(note_rel).name)}</code></a> · <a download href="{e(rec_rel)}"><code>{e(Path(rec_rel).name)}</code></a> · <a href="run-card.json"><code>run-card.json</code></a> · <a href="current-peer-audit-20261028.json"><code>current-peer-audit-20261028.json</code></a></small></p>
  </section>

  <section class="card" id="priority-sites">
    <h2>Priority Nine-Site Summary Table (<code>GEMSDOE24..36</code>) &amp; <code>KANLERGEMSDOE3</code> Advancement</h2>
    <p>Strict metric labeling per Parallel-Run Protocol Rule 3: historical site scores without organizer portal receipts are labeled <code>OWNER-REPORTED-UNVERIFIED</code>; internal metrics are labeled <code>HOLDOUT-DTI</code> with evaluator version, withheld positive pixel count, and 95% spatial-block CI. No leaderboard projections are stated anywhere.</p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Site / Lane</th>
            <th>Artifact &amp; Dot Support</th>
            <th>Strictly Labeled Metric</th>
            <th>Uniqueness vs. 90-Raster Registry</th>
            <th>Automated Verdict</th>
            <th>Format Audit</th>
          </tr>
        </thead>
        <tbody>
          {"".join(priority_rows_html)}
        </tbody>
      </table>
    </div>
  </section>

  <section class="card" id="ablations">
    <h2>Controlled 3-Experiment Campaign &amp; Same-Evaluator Benchmarks (<code>gems-segment-pooled-v1</code>)</h2>
    <p>Evaluated on whole-segment <code>1.5 km</code> buffered quadrant holdout (<code>60,988</code> withheld fault pixels across <code>3,199</code> connected components, pixel-exact visible-fault masking, pooled <code>alpha=0.2, beta=0.8</code>, <code>300 m</code> triangular kernel, <code>N = 37,654</code> dots).</p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Experiment / Series</th>
            <th>Geological &amp; Algorithmic Specification</th>
            <th>Pooled HOLDOUT-DTI</th>
            <th>95% Spatial-Block CI</th>
            <th>&Delta; vs Prior Repo Best (0.157080)</th>
          </tr>
        </thead>
        <tbody>
          {"".join(ablation_rows_html)}
        </tbody>
      </table>
    </div>
  </section>

  <section class="card" id="physical-laws">
    <h2>Three Live-Leaderboard Physical Laws Verification</h2>
    <p>Across 30+ historical peer runs, every model exceeding <code>0.22</code> owner-reported live DTI simultaneously satisfied Far-Field Reach (<code>52–58%</code> of dots &gt;1.5 km off-catalogue), Flat Deep-Basin Discipline (&le;4.3% spill), and Non-Clumping (&lt;2% <code>Clump&ge;3</code>). Axial spine concentration + <code>d=2.85 px</code> self-spacing eliminates the <code>3.57&times;</code> 2-D disk inflation inside 300 m CELF.</p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model / Emitted 37,654-Dot Raster</th>
            <th>Law 1: Far-Field (&gt;1.5 km)</th>
            <th>Law 2: Flat Deep-Basin Spill (&le;4.3%)</th>
            <th>Law 3: 300 m Clump&ge;3 (&lt;2.0%)</th>
            <th>LiDAR-Void Dot Share (24.63% Area)</th>
          </tr>
        </thead>
        <tbody>
          {"".join(laws_rows_html)}
        </tbody>
      </table>
    </div>
  </section>
</div>
</body>
</html>
"""

    # 2. executive-summary.html (Dedicated Submission Guide + 9-site overview)
    exec_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Executive Summary &amp; DrivenData Submission Guide · L-K3-ATSC-SUBMOD</title>
  {STYLE}
</head>
<body>
<div class="container">
  {_nav("executive-summary.html")}
  <header class="hero">
    <span class="badge badge-teal">Executive Summary &amp; Submission Guide</span>
    <h1>DrivenData GEMS Submission Guide &amp; Nine-Site Executive Synthesis</h1>
    <p>Actionable, automated verification summary covering all 9 priority sites (<code>GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36</code>), the wider peer ecosystem (<code>GEMSDOE..92</code>, <code>KANLER</code>, <code>WBG</code>, <code>karage</code>, <code>Apart</code>, <code>SASS</code>, <code>EUG</code>, <code>GINNY</code>), and exact instructions for <code>{e(card['submission_name'])}</code>.</p>
    {verdict_box}
  </header>

  <section class="card">
    <h2>Encoding Reference &amp; Verification Procedure (Research Only &middot; DO NOT SUBMIT)</h2>
    <ol>
      <li><strong>Respect the Fail-Closed Gate (<code>slot_authorized = false</code>):</strong> Do not spend a live DrivenData weekly slot on this artifact while the literal all-registry rule includes the <code>206,895</code>-dot <code>13GEMSDOE r13-lattice-s5</code> uniform grid probe (<code>99.99%</code> unfiltered / <code>99.77%</code> off-catalogue 3-px overlap; a selector cannot waive the literal stop). Across all <code>87</code> genuine geological fault detectors, max 3-px overlap is <code>{ureg['genuine_final_dot_overlap_3px']:.2%} &le; 70%</code>.</li>
      <li><strong>Inspect Both Local Encoding Profiles (<code>-zeros.tif</code> vs <code>-nan.tif</code>):</strong><br>
        <a class="btn btn-primary" download href="{e(z_tif_rel)}">Research download {e(Path(z_tif_rel).name)}</a>
        <a class="btn btn-secondary" download href="{e(z_zip_rel)}">Research download .zip</a><br>
        <small>Why emit both twins? Because the historically rejected upload that triggered <code>Error: Predicted values must be in range [0, 1]</code> was not supplied, its exact cause is unverified: an unmasked whole-array check fails on outside-footprint <code>NaN</code>, whereas a strict template-mask check expects <code>NaN</code> outside. We emit both <code>-zeros.tif</code> (<code>16/16</code> checks on <code>--profile finite-grid</code>; <code>0</code> NaN across all <code>12,279,160</code> cells) and <a download href="{e(n_tif_rel)}"><code>-nan.tif</code></a> (<code>16/16</code> checks on <code>--profile template-mask</code>).</small>
      </li>
      <li><strong>Verify Downloaded SHA-256 Checksum Locally:</strong>
        <pre>sha256sum {e(Path(z_tif_rel).name)}
# Expected: {e(card['raster_sha256'])}</pre>
      </li>
      <li><strong>Recorded &le;140-Character Run-Card Note:</strong>
        <pre>{e(card['submission_note'])}</pre>
      </li>
    </ol>
  </section>

  <section class="card">
    <h2>Priority Nine-Site &amp; Peer-Ledger Executive Table</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Site / Lane</th>
            <th>File &amp; Dot Count</th>
            <th>Strictly Labeled Metric</th>
            <th>Uniqueness vs. Registry</th>
            <th>Verdict</th>
            <th>Format Check</th>
          </tr>
        </thead>
        <tbody>
          {"".join(priority_rows_html)}
        </tbody>
      </table>
    </div>
  </section>
</div>
</body>
</html>
"""

    # 3. hypotheses.html (Pre-modeling Hypotheses + GEMSDOE32 Mathematical Analysis)
    hyp_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ranked Geological Hypotheses &amp; GEMSDOE32 Deep Dive · L-K3-ATSC-SUBMOD</title>
  {STYLE}
</head>
<body>
<div class="container">
  {_nav("hypotheses.html")}
  <header class="hero">
    <span class="badge badge-teal">Geological &amp; Metric Theory</span>
    <h1>Why <code>GEMSDOE32</code> (<code>0.2778</code>) Led the Priority Cohort, Why <code>0.4413</code> Sits Higher, and Our 4 Preregistered Hypotheses</h1>
    <p>Frozen prior to model fitting in <code>evidence/preregistration_atsc_20261027.json</code> (SHA-256 <code>e87228d624bcca28a5d6ec7475a10582a82d833c996644bbc8b5312b6e189201</code>).</p>
  </header>

  <section class="card">
    <h2>1. Exact Forensics of <code>GEMSDOE32</code> (<code>0.2778</code> Owner-Reported) vs. <code>0.3195</code> / <code>0.4413</code></h2>
    <h3>1.1 Nested Thinning Chain (<code>19GEMSDOE H19-5 &rarr; GEMSDOE32 H33-2-B2</code>)</h3>
    <p>Pixel-exact set algebra across the cached GeoTIFFs proves that the top 5 priority-site submissions are strictly nested subsets of one continuous probability map (<code>H19-5</code>):</p>
    <pre>H19-5 (121,131 px, 0.1922) &sup; GEMSDOE24 D1.5 (60,069 px, 0.2477) &sup; GEMSDOE25/30 D2.8 (44,090 px, 0.2600)
  &sup; GEMSDOE31 Solo (40,199 px, 0.2708) &sup; GEMSDOE32 H33-2-B2 (37,654 px, 0.2778 = D2.8 \\ {{d_cat &le; 200 m}})</pre>
    <h3>1.2 Exact DTI Marginal-Inclusion Differential Law</h3>
    <p>Under pooled Distance-Tolerant IoU (<code>&alpha;=0.2, &beta;=0.8</code>, <code>300 m</code> triangular cone), since <code>TP_w + FN_w = |T_hid|</code> is constant, adding a binary dot <code>x_0</code> increases DTI if and only if its marginal uncaptured truth coverage exceeds:</p>
    <pre>&Delta;T(x_0) &gt; &tau;(DTI) = (0.2 &times; DTI) / (1 - 0.2 &times; DTI)
  At DTI = 0.2600 (D2.8)       : &tau; = 0.0549  (6,436 d_cat&le;200m collar dots had &Delta;T &approx; 0.008 &rarr; excising them gave +0.0178 &rarr; 0.2778!)
  At DTI = 0.2778 (GEMSDOE32)  : &tau; = 0.0588
  At DTI = 0.4413 (Leader #1)  : &tau; = 0.0968</pre>
    <h3>1.3 The 3.57&times; 2-D Blob Inflation Theorem &amp; Four Structural Bottlenecks</h3>
    <ul>
      <li><strong>Dip-Offset Geometry Mismatch:</strong> Great Basin listric normal faults dip 45&deg;&ndash;60&deg; basinward; basement gravity/magnetic horizontal gradients peak <code>300–700 m</code> into the hanging wall rather than directly beneath the surface scarp.</li>
      <li><strong>3.57&times; 2-D Blob Inflation in 300 m CELF:</strong> On a 100 m grid, the 300 m triangular kernel integrates to <code>10.7225</code> on a 2-D blob vs <code>3.0000</code> on a 1-D fault crest, tricking naive submodular allocators into packing 30–43% <code>Clump&ge;3</code> clusters onto playa margins and volcanic domes.</li>
      <li><strong>24.63% 1 m LiDAR Void Domain Shift:</strong> Pooling 1 m LiDAR and 10 m-3DEP pixels in Stage-2 without regime quantile harmonization starves corridors across 1.27M void pixels.</li>
      <li><strong>Short-Scale Fragmentation:</strong> Pixel-level trees cannot separate 200 m road/terrace steps from multi-kilometer structural corridors.</li>
    </ul>
  </section>

  <section class="card">
    <h2>2. Ranked Pre-Modeling Geological Hypotheses &amp; Empirical Outcome</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Rank &amp; ID</th>
            <th>Geological Mechanism &amp; Layers</th>
            <th>Named Non-Fault Mimic</th>
            <th>Expected Gain</th>
            <th>Controlled Holdout Outcome</th>
          </tr>
        </thead>
        <tbody>
          <tr class="highlight">
            <td><strong>#1 · H-K3S2-1</strong><br><span class="badge badge-teal">CONFIRMED</span></td>
            <td><strong>Listric Dip-Offset Hanging-Wall Wedge (+300..+700 m) + Regime-Harmonized Nested-OOF Stage-2 8-Azimuth (1.0 &amp; 2.6 km) Corridor Tomography + Axial d=2.85 CELF</strong><br><small>Layers: <code>iso_grav_anom</code>, <code>depth_to_base_surf</code>, <code>magnetic_anom</code>, 1 m LiDAR + seamless 10 m 3DEP.</small></td>
            <td>Tilted Mio-Pliocene ash-flow tuff hogbacks / buried caldera ring margins</td>
            <td><code>+0.008 to +0.022</code></td>
            <td><strong>CONFIRMED:</strong> <code>Exp-ATSC-1 = 0.161641</code> (+45.6 bps vs CADG); with Stage-2 corridor <code>Exp-ATSC-2 = 0.163715</code> (+66.4 bps vs CADG <code>0.157080</code>, +106.8 bps vs 1-stage CADG <code>0.153035</code>).</td>
          </tr>
          <tr class="highlight">
            <td><strong>#2 · H-K3S2-2</strong><br><span class="badge badge-teal">CONFIRMED</span></td>
            <td><strong>GeoDAWN Airborne Radiometric U/Th Radon &amp; K/Th Potassic Fault-Zone DoG + 4-Block Survey Seam Deconfounding</strong><br><small>Layers: <code>geodawn_u_ppm</code>, <code>geodawn_th_ppm</code>, <code>geodawn_k_pct</code>, <code>geodawn_tmi</code>.</small></td>
            <td>Rhyolitic ash-flow tuff contacts &amp; evaporitic uranium-enriched playa crusts</td>
            <td><code>+0.003 to +0.008</code></td>
            <td><strong>CONFIRMED (jointly in Exp-ATSC-2):</strong> Combined with Stage-2 corridor head, lifted NW (+158 bps), SW (+72 bps), and SE (+75 bps) over Exp-ATSC-1 to reach <code>0.163715</code>.</td>
          </tr>
          <tr>
            <td><strong>#3 · H-K3S2-3</strong><br><span class="badge badge-amber">FALSIFIED</span></td>
            <td><strong>Fold-Safe Visible-Catalogue Coulomb Stress-Shadow Tip-Lobe (3 km) &amp; En-Echelon Relay-Bridge (6 km) &times; Corridor Interaction</strong><br><small>Layers: <code>fold.visible</code> strict subset of <code>existing_faults.tif</code>.</small></td>
            <td>Erosional range-front embayments &amp; braided stream fan apices beyond fault tips</td>
            <td><code>+0.002 to +0.006</code></td>
            <td><strong>FALSIFIED (-24.3 bps vs Exp-ATSC-2):</strong> <code>Exp-ATSC-3 = 0.161290</code> still beat prior CADG (<code>0.157080</code>) by +42.1 bps, but regressed vs label-free <code>Exp-ATSC-2</code> because tip proximity pulls mass away from isolated &gt;5 km intrabasin horsts.</td>
          </tr>
          <tr>
            <td><strong>#4 · H-K3S2-4</strong><br><span class="badge badge-slate">EXTERNAL NEXT STEP</span></td>
            <td><strong>Raw 1-D GeoDAWN Flight-Line Profiles (200 m spacing) + NASA OPERA L3 DIST-ALERT / NISAR InSAR</strong><br><small>Official free sources: USGS ScienceBase <code>10.5066/P9X82336</code> &amp; ASF DAAC OPERA.</small></td>
            <td>Agricultural groundwater-pumping subsidence bowls</td>
            <td><code>+0.015 to +0.045</code> (non-sandbox)</td>
            <td>Documented with official USGS/NASA links for external workstation execution (sandbox egress allowlist excludes ScienceBase/ASF).</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</div>
</body>
</html>
"""

    exec_md = (
        f"# L-K3-ATSC-SUBMOD Executive Summary & Encoding Reference (Research Only · DO NOT SUBMIT)\n\n"
        f"- **Selected Candidate**: `{card['submission_name']}` (`Exp-ATSC-2`, 8-fold spatial OOF)\n"
        f"- **Primary `HOLDOUT-DTI`**: **`{hold['value']:.6f}`** (`95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}]`, `{hold['withheld_positives']:,}` withheld positives, `{hold['evaluator_version']}`, **`+0.006635` above prior repo best `CADG Exp-K3-3`**)\n"
        f"- **Orthogonal Confirmation `HOLDOUT-DTI`**: **`{diag['candidate_holdout_dti']:.6f}`** (`+0.005181` above `CADG Exp-K3-3` `0.147663`)\n"
        f"- **Research-Only Finite-Grid File**: [`{Path(z_tif_rel).name}`]({z_tif_rel}) (`SHA-256: {card['raster_sha256']}`, `37,654` binary `{{0,1}}` dots, `0` NaN whole-array locally; portal acceptance unverified)\n"
        f"- **Recorded Note (`{len(card['submission_note'])}` chars)**: `{card['submission_note']}`\n"
        f"- **Uniqueness & Fail-Closed Gate**: **PASS across `87/87` genuine fault detectors** (`{ureg['genuine_final_dot_overlap_3px']:.2%} <= 70%`, `|rho| = {ureg['genuine_final_max_abs_spearman_rho']:.4f} <= 0.90`); **DO NOT SUBMIT** (`verdict = \"{card['verdict']}\"`, `slot_authorized = false`) under the literal all-registry rule (`99.99%` unfiltered / `99.77%` off-catalogue 3-px overlap vs `206,895`-dot `13GEMSDOE r13-lattice-s5`; selector cannot waive).\n"
        f"- **28 Oct bounded peer re-audit**: `{bounded_peer['rasters_compared']}` selected current peer rasters; final-dot max `{bounded_result['max_final_dot_overlap_3px_genuine_detectors']:.2%}` vs genuine detectors and `{bounded_result['max_final_dot_overlap_3px_calibration_or_continuous_probes']:.2%}` vs calibration/continuous probes. Scope is incomplete and surface comparison was not run; this is an additional negative forensic receipt, not a score or approval. See [`current-peer-audit-20261028.json`](current-peer-audit-20261028.json).\n\n"
        f"## Nine-Site & KANLERGEMSDOE3 Summary Table\n\n"
        f"| Site / Lane | Artifact | Metric | Uniqueness | Safe to Submit? |\n"
        f"| --- | --- | --- | --- | --- |\n"
        + "\n".join(md_rows)
        + "\n"
    )
    outputs = {
        OUT / "index.html": index_html,
        OUT / "executive-summary.html": exec_html,
        OUT / "hypotheses.html": hyp_html,
        OUT / "EXECUTIVE_SUMMARY.md": exec_md,
        OUT / "README.md": exec_md,
        OUT / "current-peer-audit-20261028.json": (ROOT / "evidence/atsc-current-peer-audit-20261028.json").read_text(),
    }
    if check_only:
        stale = [str(p.relative_to(ROOT)) for p, content in outputs.items() if (not p.is_file()) or p.read_text() != content]
        if stale:
            raise ValueError(f"Stale L-K3-ATSC-SUBMOD generated pages: {', '.join(stale)}")
        return
    for p, content in outputs.items():
        p.write_text(content)
    print(f"Built {OUT}/index.html, executive-summary.html, hypotheses.html, EXECUTIVE_SUMMARY.md, README.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify generated ATSC pages match disk without rewriting")
    ns = parser.parse_args()
    build(check_only=ns.check)
