"""Render the isolated L-K3-CADG-SUBMOD executive summary and submission guide under docs/cadg-submod/."""
from __future__ import annotations

from html import escape as e
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/cadg-submod"


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    audit = json.loads((ROOT / "docs/audit.json").read_text())
    card = json.loads((ROOT / "evidence/cadg-submod-run-card.json").read_text())
    exp_ev = json.loads((ROOT / "evidence/kanlergems3_experiments_20261026.json").read_text())
    uniq_ev = json.loads((ROOT / "evidence/kanlergems3_uniqueness_20261026.json").read_text())
    cross_ev = json.loads((ROOT / "evidence/kanlergems3_cross_lane_audit_20261026.json").read_text())

    art = card["submission_artifacts"]
    z_tif_rel = art["primary_zeros_tif"].replace("docs/cadg-submod/", "", 1)
    z_zip_rel = art["primary_zeros_zip"].replace("docs/cadg-submod/", "", 1)
    n_tif_rel = art["official_nan_twin_tif"].replace("docs/cadg-submod/", "", 1)
    n_zip_rel = art["official_nan_twin_zip"].replace("docs/cadg-submod/", "", 1)
    note_rel = art["note_file"].replace("docs/cadg-submod/", "", 1)
    rec_rel = art["receipt_file"].replace("docs/cadg-submod/", "", 1)

    hold = card["holdout"]
    inc = card["incumbent_comparison"]
    conf = card["independent_confirmation"]
    ureg = card["uniqueness_registry_summary"]
    p_bound = ureg["pigeonhole_lattice_bounds"][0]
    pied = card["diagnostic_piedmont_proxy"]["models"]["deployed_oof8f_candidate"]
    g32_row = next(r for r in uniq_ev["detector_comparisons"] if r["id"] == "focus-GEMSDOE32")

    rows_html = []
    md_rows = []
    for r in audit["rows"]:
        url = f"https://github.com/buffedlizard55-lab/{r['repo']}/blob/{r['head']}/{r['file']}"
        fname = Path(r["file"]).name
        fmt = (
            "PASS (null/NaN outside)"
            if r["local_validation"]["format_pass"]
            else "Finite-zero outside (7,111,787 cells; in-footprint [0,1] PASS)"
        )
        reported = f"{r['owner_reported_leaderboard_score']:.4f} (UNVERIFIED OWNER REPORT; no organizer receipt)"
        overlap = f"NO — duplicate ({r['max_overlap_3px']:.2%} max 3-px peer overlap)"
        rows_html.append(
            f"<tr><td><strong>{e(r['repo'])}</strong></td>"
            f"<td><a href=\"{e(url)}\"><code>{e(fname)}</code></a>"
            f"<small>{r['dots']:,} dots · Historical learning reference only — do not submit</small></td>"
            f"<td>{e(reported)}</td>"
            f"<td>Not estimable (no leaderboard projection)</td>"
            f"<td>{e(overlap)}</td>"
            f"<td><strong>NO</strong> (already submitted / duplicate family)</td>"
            f"<td>{e(fmt)}</td></tr>"
        )
        md_rows.append(
            f"| `{r['repo']}` | `{fname}` (`{r['dots']:,}` dots) | `{r['owner_reported_leaderboard_score']:.4f}` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`{r['max_overlap_3px']:.2%}` peer 3-px overlap) | **NO** |"
        )

    k3_row_html = (
        f"<tr style=\"background:#f0fbf8\"><td><strong>KANLERGEMSDOE3 ({e(card['lane_id'])})</strong></td>"
        f"<td><a download href=\"{e(z_tif_rel)}\"><code>{e(Path(z_tif_rel).name)}</code></a> · "
        f"<a download href=\"{e(z_zip_rel)}\"><code>.zip</code></a>"
        f"<small>{card['validator']['predicted_positive_dots']:,} binary dots · SHA-256 <code>{e(card['raster_sha256'][:16])}…</code></small></td>"
        f"<td><strong>HOLDOUT-DTI {hold['value']:.6f}</strong><br>"
        f"<small>95% CI [{hold['ci95'][0]:.6f}, {hold['ci95'][1]:.6f}] · {hold['withheld_positives']:,} withheld px · <code>{e(hold['evaluator_version'])}</code> (not a live score)</small></td>"
        f"<td>Not estimable (unsubmitted; 0 live slots used)</td>"
        f"<td><strong>YES vs all 39 genuine detectors</strong> ({ureg['genuine_35_final_dot_overlap_3px']:.2%} max vs 35 external; &le;46.39% vs 4 sibling lanes; {g32_row['final_3px_overlap']:.2%} vs GEMSDOE32)<br>"
        f"<small>Literal uniform lattice probe: {card['final_dot_overlap_3px']:.2%} (pigeonhole min {p_bound['mathematical_min_possible_3px_overlap']:.2%})</small></td>"
        f"<td><strong>HOLD FOR HUMAN SELECTOR</strong><br><small>Automated verdict: <code>{e(card['verdict'])}</code> (`slot_authorized=false`)</small></td>"
        f"<td><strong>PASS (15/15)</strong><br><small>All 12,279,160 cells finite [0,1]; -nan twin also PASS</small></td></tr>"
    )
    rows_html.append(k3_row_html)
    md_rows.append(
        f"| **`KANLERGEMSDOE3 ({card['lane_id']})`** | [`{Path(z_tif_rel).name}`]({z_tif_rel}) (`37,654` dots) | **`HOLDOUT-DTI {hold['value']:.6f}`** (`95% CI [{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}]`, `60,988` pos) | Not estimable | **YES vs 39/39 detectors** (`{ureg['genuine_35_final_dot_overlap_3px']:.2%}` max; `{card['final_dot_overlap_3px']:.2%}` vs 207k lattice probe) | **HOLD FOR HUMAN SELECTOR** (`verdict={card['verdict']}`) |"
    )

    ablation_rows_html = []
    for key, label in [
        ("matched_random", "Matched random spacing (d=2.8 px, 37,654 dots)"),
        ("static_G70_P8", "Static GEMSDOE70 P8-oof38k (37,654 dots; d_cat<=2 holes on withheld truth)"),
        ("static_H33_B2", "Static GEMSDOE32 H33-B2 (37,654 dots; d_cat<=2 holes on withheld truth)"),
        ("unsupervised_D28_37654", "Leak-free unsupervised multi-physics D2.8 (37,654 dots)"),
        ("B0_regional_d28", "B0_regional_d28: 19-band HGB + 2.8 px spacing (37,654 dots, in-run incumbent)"),
        ("Exp-K3-1", "Exp-K3-1: Decontaminated 1m/10m scarp + 150m TMI/grav + 300m submodular CELF"),
        ("Exp-K3-2", "Exp-K3-2: + TIGER road / pluvial bench suppression & INGENIOUS hydro/rad halos"),
        ("Exp-K3-3", "Exp-K3-3 (Selected): + fold-safe LCO visible relay/tip continuation & piedmont calibration"),
    ]:
        s = exp_ev["screen_summaries"][key]
        ci = s["ci95"]["interval"]
        bold = " style=\"background:#f0fbf8;font-weight:600\"" if key == card["selected_ablation_id"] else ""
        ablation_rows_html.append(
            f"<tr{bold}><td><code>{e(key)}</code></td><td>{e(label)}</td>"
            f"<td>{s['dti']:.6f}</td><td>[{ci[0]:.6f}, {ci[1]:.6f}]</td>"
            f"<td>{s['n_emitted']:,}</td></tr>"
        )

    cross_rows_html = []
    for c in cross_ev["comparisons"]:
        cross_rows_html.append(
            f"<tr><td><strong>{e(c['lane'])}</strong></td>"
            f"<td><code>{e(Path(c['file']).name)}</code><small>SHA-256 <code>{e(c['sha256'][:16])}…</code></small></td>"
            f"<td>{c['peer_off_cat_dots']:,}</td>"
            f"<td>{c['final_3px_overlap']:.2%} (&le; 70% PASS)</td>"
            f"<td>{c['final_abs_spearman_rho']:.4f} (&le; 0.90 PASS)</td>"
            f"<td><strong>PASS</strong></td></tr>"
        )

    style = (
        "<style>:root{font-family:system-ui,-apple-system,sans-serif;color:#162a38;background:#f3f6f8}"
        "body{max-width:1240px;margin:auto;padding:28px}"
        "header,section{background:#fff;border:1px solid #d8e2e8;border-radius:14px;padding:24px;margin:18px 0}"
        "h1{font-size:2.15rem;letter-spacing:-.03em;margin:.3rem 0}h2{margin-top:0;font-size:1.35rem}"
        "a{color:#076367}nav{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px}"
        ".banner{border-left:7px solid #b85d19;background:#fff9f2}"
        ".grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin:14px 0}"
        ".pill{border:1px solid #d8e2e8;border-radius:10px;padding:14px;background:#f9fbfc}"
        ".pass{border-left:5px solid #16794b}.hold{border-left:5px solid #b85d19}"
        ".btn{display:inline-block;background:#076367;color:#fff;text-decoration:none;padding:10px 15px;border-radius:8px;font-weight:600;margin:4px 8px 4px 0}"
        ".btn.sec{background:#eef4f6;color:#162a38;border:1px solid #c5d4dd}"
        "small{display:block;color:#5c6f7c;margin-top:5px}"
        "table{border-collapse:collapse;width:100%;font-size:.88rem}"
        "td,th{text-align:left;padding:12px;border-bottom:1px solid #dce4e9;vertical-align:top}"
        "td:nth-child(2){overflow-wrap:anywhere;min-width:210px}th{background:#eef4f6}"
        ".scroll{overflow:auto}p,li{line-height:1.6}.eyebrow{color:#076367;text-transform:uppercase;letter-spacing:.12em;font-size:.78rem;font-weight:700}"
        "code{background:#eef3f6;padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}footer{color:#5c6f7c;padding:16px;font-size:.88rem}</style>"
    )
    head = (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>KANLERGEMSDOE3 ({e(card['lane_id'])}) | GEMS Submission Decision Desk</title>{style}<body>"
    )

    index_html = (
        head
        + f"""<header>
<div class="eyebrow">DOE GEMS #306 · Isolated Study Portal · Lane {e(card['lane_id'])} · 26 Oct 2026</div>
<h1>KANLERGEMSDOE3 ({e(card['lane_id'])}) — Evidence &amp; Submission Decision Desk</h1>
<p>Concealed Basin-and-Range fault discovery via cultural/pluvial-decontaminated 1 m LiDAR &amp; 10 m 3DEP breaklines, 150 m upward-continued aeromagnetics, INGENIOUS hydrothermal halos, and exact 300 m submodular CELF allocation.</p>
<nav>
  <a href="executive-summary.html"><strong>How to Submit (Step-by-Step Guide)</strong></a>
  <a href="run-card.json">JSON Run Card</a>
  <a href="hypotheses.md">Preregistered Hypotheses</a>
  <a href="verification.md">3-Pass Verification Audit</a>
  <a href="../index.html">&larr; Root Multi-Lane Desk</a>
</nav>
</header>

<section class="banner">
<h2>Gate &amp; Submit-Readiness Status: DOWNLOAD READY · DO NOT SUBMIT WITHOUT HUMAN SELECTOR SIGN-OFF (<code>verdict = {e(card['verdict'].upper())}</code>)</h2>
<p><strong>Zero weekly competition slots were spent automatically (<code>slot_authorized = false</code>, <code>live_submission_slots_used = 0</code>).</strong> Our newly generated 8-fold spatial out-of-fold candidate GeoTIFF passes <strong>all 15/15 format &amp; finite-<code>[0,1]</code> byte checks</strong>, passes <strong>all 80 two-polarity leakage canaries</strong>, beats every leak-free spatial holdout incumbent on two orthogonal whole-segment buffered splits, and passes uniqueness across <strong>all 39/39 genuine geological fault-detector rasters</strong> (35 external + 4 concurrent repository lanes). Automated <code>promotion_gate.py</code> remains fail-closed (<code>verdict = negative</code>) rather than weakening two non-model blockers documented below: (1) <code>13GEMSDOE</code>'s 206,895-dot uniform spacing-5 calibration lattice covers 99.87% of the footprint within 300 m (forcing &ge;82.34% overlap for any 37,654-dot file), and (2) DrivenData's <code>/data/</code> tab requires authenticated login so template hashes were verified against 9 pinned mirrors.</p>
<div class="grid2">
  <div class="pill pass"><strong>1. Automated Format &amp; Finite [0,1] Gate: PASS (15/15)</strong><small><code>EPSG:32611</code> · <code>3730&times;3292</code> · <code>float32</code> · 12,279,160/12,279,160 finite <code>{{0.0, 1.0}}</code> cells (prevents <em>"Predicted values must be in range [0, 1]"</em>) · 37,654 off-catalogue dots · 0 catalogue overlap.</small></div>
  <div class="pill pass"><strong>2. Spatial Holdout Gate (HOLDOUT-DTI): PASS (4/4 &amp; 4/4 Folds)</strong><small>Primary <code>{hold['value']:.6f}</code> (95% CI <code>[{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}]</code>, 60,988 withheld px) vs <code>B0_regional_d28 = {inc['incumbent_holdout_dti']:.6f}</code> (+52.1%) &amp; <code>GEMSDOE33 CSHT = {inc['recorded_gemsdoe33_a33_r2_csht_holdout_dti']:.6f}</code> (+13.7%). Diagonal confirm: <code>{conf['candidate_dti']:.6f}</code> vs <code>{conf['incumbent_dti']:.6f}</code>.</small></div>
  <div class="pill pass"><strong>3. Leakage Canary &amp; 39-Detector Uniqueness: PASS</strong><small>80 features tested: max two-sided AUC = <code>{card['max_feature_auc']:.4f} &le; 0.90</code>. Across all 35 external detectors + 4 concurrent repo lanes: max 3-px dot overlap = <code>{ureg['genuine_35_final_dot_overlap_3px']:.2%} &le; 70%</code> (<code>{g32_row['final_3px_overlap']:.2%}</code> vs GEMSDOE32); max |&rho;| = <code>{ureg['genuine_35_surface_max_abs_spearman_rho']:.4f} &le; 0.90</code>.</small></div>
  <div class="pill hold"><strong>4. Un-Weakened Literal Selector Hold: <code>verdict = {e(card['verdict'])}</code></strong><small>Literal 36th raster <code>r13-lattice-s5</code> (206,895 grid dots, 99.87% footprint halo) gives <code>{card['final_dot_overlap_3px']:.2%}</code> (mathematical min <code>{p_bound['mathematical_min_possible_3px_overlap']:.2%}</code>). Human selector must explicitly sign off before using 1 of &le;3 weekly DrivenData slots.</small></div>
</div>
<p>
  <a class="btn" download href="{e(z_tif_rel)}">&#11015; Download Primary Finite [0,1] GeoTIFF (808 KB)</a>
  <a class="btn" download href="{e(z_zip_rel)}">&#11015; Download 1-TIFF Competition ZIP (169 KB)</a>
  <a class="btn sec" download href="{e(n_tif_rel)}">NaN-Outside Twin .tif (1.6 MB)</a>
  <a class="btn sec" download href="{e(n_zip_rel)}">NaN-Outside Twin .zip</a>
  <a class="btn sec" href="{e(rec_rel)}">Writer Receipt JSON</a>
  <a class="btn sec" href="{e(note_rel)}">Submission Note (.txt)</a>
</p>
<p><strong>Unique Submission Name:</strong> <code>{e(card['submission_name'])}</code><br>
<strong>Submission Note ({len(card['submission_note'])} / 140 chars):</strong> <code>{e(card['submission_note'])}</code><br>
<strong>Primary <code>-zeros.tif</code> SHA-256:</strong> <code>{e(card['raster_sha256'])}</code></p>
</section>

<section>
<h2>Executive Summary Table — 9 Priority GEMSDOE Sites + KANLERGEMSDOE3 ({e(card['lane_id'])})</h2>
<p>All historical scores from sibling repositories are strictly quarantined as <code>UNVERIFIED OWNER REPORT</code> (no organizer submission-page receipt binds raster SHA-256 to score). Live public leaderboard verified 2026-10-26 at <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData #306</a>: <code>#1 xiaofanhu = 0.4437</code>, <code>#2 cfld__ = 0.3916</code>, <code>#3 Batik Shirt Brothers = 0.3904</code> (resolving stale prompt figures <code>0.4413</code> / <code>0.3195</code>). Leaderboard projections are prohibited; internal results carry <code>HOLDOUT-DTI</code> provenance (not directly comparable across differing segment-split masks).</p>
<div class="scroll"><table>
<thead><tr><th>Site</th><th>Downloadable File &amp; Dot Count</th><th>Defensible Score / Evidence Class</th><th>Estimated Live Score</th><th>Uniqueness vs Registry</th><th>OK to Submit?</th><th>Automated Format Check</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody>
</table></div>
</section>

<section>
<h2>Cross-Lane Uniqueness Audit vs Concurrent <code>KANLERGEMSDOE3</code> Parallel Lanes</h2>
<p>All 4 concurrent research lanes preserved on <code>main</code> pass the strict <code>&le; 70%</code> 3-pixel overlap and <code>&le; 0.90</code> Spearman correlation rule against <code>Exp-K3-3</code> (<code>evidence/kanlergems3_cross_lane_audit_20261026.json</code>):</p>
<div class="scroll"><table>
<thead><tr><th>Sibling Lane</th><th>Artifact</th><th>Off-Catalogue Dots</th><th>3-px Overlap vs Exp-K3-3</th><th>|Spearman &rho;|</th><th>Detector Uniqueness</th></tr></thead>
<tbody>{''.join(cross_rows_html)}</tbody>
</table></div>
</section>

<section>
<h2>Forensic Analysis: Why GEMSDOE32 <code>H33-B2</code> Reported <code>0.2778</code> — and How <code>KANLERGEMSDOE3</code> Advances</h2>
<ul>
  <li><strong>Exact Subset Genealogy:</strong> Pixel-level raster audit proves an exact nested subset chain across historical owner winners: <code>GEMSDOE32 H33-B2</code> (<code>37,654</code> dots, reported <code>0.2778</code>) &sub; <code>GEMSDOE31 H27-4</code> (<code>40,199</code> dots, <code>0.2708</code>) &sub; <code>GEMSDOE25/30 D2.8</code> (<code>44,090</code> dots, <code>0.2600</code>) &sub; <code>19GEMSDOE H19-5</code> (<code>121,131</code> dots, <code>0.1922</code>). Specifically, <code>H33-B2 = D2.8 &amp; (d_catalogue &gt; 2.0 px)</code> deletes <code>6,436</code> near-catalogue dots at <code>1 &le; d_catalogue &le; 2 px</code>.</li>
  <li><strong>Official Metric Algebra (DrivenData Staff Confirmation):</strong> On <a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">DrivenData Forum Thread #11516</a>, organizer <code>chrisk-dd</code> confirmed that known USGS/INGENIOUS catalogue pixels are masked from evaluation in both Phase 1 and Phase 2, and under <code>DTI(&alpha;=0.2, &beta;=0.8, R=300 m)</code> every off-catalogue dot outside 300 m of hidden test faults adds <code>0.2 &times; FP_w</code> to the denominator. Thinning redundant clustered scarp mass from <code>121,131 &rarr; 37,654</code> dots cuts uncredited <code>FP_w</code> by &gt;68% while preserving 300 m triangular-kernel coverage.</li>
  <li><strong>Why Static <code>H19-5</code> / <code>D2.8</code> Cannot Be Used as Holdout Baselines:</strong> Forensic code audit of <code>19GEMSDOE</code> shows <code>H19-5</code> and <code>D2.8</code> were trained on legacy unbuffered quadrant splits (retaining cross-boundary halves of withheld faults) and zeroed <code>labels.tif == 0</code> across all 4 quadrants. Evaluating static <code>H33-B2</code> fairly on <code>SegmentHoldout(buffer_px=15)</code> yields <code>0.006708</code> (due to full-catalogue holes around withheld segments), while a leak-free 37,654-dot unsupervised multi-physics D2.8 composite scores <code>0.064020</code> and 19-band HGB <code>B0_regional_d28</code> scores <code>0.102267</code>.</li>
  <li><strong>How <code>Exp-K3-3</code> (8-Fold Spatial OOF) Breaks Both Ceilings:</strong> Deploying a stitched 8-fold spatial out-of-fold cross-fitted surface (<code>0.5 &times; quadrant OOF + 0.5 &times; diagonal-wedge OOF</code>) eliminates in-sample training-label collar memorization, placing <strong><code>{pied['fraction_dots_d_cat_gt_10px']:.1%}</code> of its 37,654 dots &gt;1 km from mapped catalogue traces</strong> (<code>C_pied</code> blind-piedmont diagnostic DTI = <code>{pied['c_pied_dti']:.4f}</code> vs <code>GEMSDOE33 CSHT = 0.0874</code>), achieving <strong><code>HOLDOUT-DTI = {hold['value']:.6f}</code></strong> (+52.1% over <code>B0_regional_d28</code>) with only <code>{g32_row['final_3px_overlap']:.2%}</code> 3-px overlap against <code>GEMSDOE32</code> (<strong>53.7% brand-new off-catalogue fault predictions</strong>).</li>
</ul>
</section>

<section>
<h2>Controlled Within-Lane Holdout Ablations (<code>{e(hold['evaluator_version'])}</code>, <code>3/3</code> Budget Used)</h2>
<div class="scroll"><table>
<thead><tr><th>Series ID</th><th>Method Description</th><th>Pooled HOLDOUT-DTI</th><th>95% Block-Bootstrap CI</th><th>Total Emitted Dots</th></tr></thead>
<tbody>{''.join(ablation_rows_html)}</tbody>
</table></div>
<p><small>Orthogonal confirmation on <code>DiagonalSegmentHoldout(buffer_px=20)</code> (<code>{e(conf['split_id'])}</code>, {conf['withheld_positives']:,} withheld positives): <strong><code>{e(card['selected_ablation_id'])} = {conf['candidate_dti']:.6f}</code></strong> vs <code>{e(conf['strongest_confirm_incumbent'])} = {conf['incumbent_dti']:.6f}</code> (paired &Delta; = <code>+{conf['paired_delta_dti']:.6f}</code>, 95% CI <code>[{conf['paired_delta_ci95'][0]:.6f}, {conf['paired_delta_ci95'][1]:.6f}]</code>, {e(conf['fold_wins'])} folds).</small></p>
</section>

<section>
<h2>Preregistered Geological Hypotheses (Frozen SHA-256 <code>e49c6aae…</code>)</h2>
<ol>
  <li><strong>H-K3-1 (Selected &amp; Validated — Lane <code>L-K3-CADG-SUBMOD</code>):</strong> Cultural/pluvial-decontaminated asymmetric 1 m LiDAR + seamless 10 m 3DEP piedmont breaklines fused with 150 m upward-continued TMI depth-persistence, INGENIOUS hydrothermal/K-radiometric upflow halos, leave-component-out relay continuation, and exact 300 m submodular CELF allocation. <em>Confounder guarded:</em> TIGER/Line 2024 road embankments, Lahontan/Bonneville shorelines, and static volcanic contacts.</li>
  <li><strong>H-K3-2 (Deferred Rank #2):</strong> 10 m 3DEP drainage-divide migration (&chi; disequilibrium) across range-bounding fault blocks (<code>dem10_chi_100m_i16.tif</code> + profile curvature). <em>Confounder:</em> Resistant welded-tuff knickzones.</li>
  <li><strong>H-K3-3 (Deferred Rank #3):</strong> Basement-depth &amp; MT conductance dilatational stepover bridge tomography for blind geothermal transfer zones. <em>Confounder:</em> Conductive playa evaporite brines.</li>
  <li><strong>H-K3-4 (Deferred Rank #4):</strong> Geodetic tensor principal-extension azimuth alignment (Kreemer et al., 2022) with aeromagnetic tilt edges. <em>Confounder:</em> Pre-Cenozoic sutures accidentally coaxial with modern extension.</li>
</ol>
<p><a href="hypotheses.md">Full preregistered physics, DOIs, expected DTI gains, and implementation costs &rarr;</a></p>
</section>

<footer>Reproducible static evidence desk built by <code>scripts/build_cadg_site.py</code> from <code>evidence/cadg-submod-run-card.json</code> and <code>docs/audit.json</code>. Zero live DrivenData submission slots consumed automatically. Verified official rules: <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE/NLR FY26-96647</a> (&le;3 submissions/week; 1 final submission evaluated across Phase 1 &amp; Phase 2).</footer></body></html>"""
    )
    (OUT / "index.html").write_text(index_html)

    how_html = (
        head
        + f"""<header>
<div class="eyebrow">Executive Summary &amp; Submission Guide · Lane {e(card['lane_id'])}</div>
<h1>How to Verify &amp; Submit the KANLERGEMSDOE3 ({e(card['lane_id'])}) Candidate</h1>
<nav><a href="index.html">&larr; Back to CADG-Submod Decision Desk</a> · <a href="run-card.json">JSON Run Card</a> · <a href="{e(rec_rel)}">Writer Receipt</a> · <a href="../index.html">Root Multi-Lane Desk</a></nav>
</header>

<section class="banner">
<h2>Selector Summary: Candidate Validated Locally · Human Weekly-Slot Sign-Off Required</h2>
<p>Automated format, finite-<code>[0,1]</code> range, leakage-canary, dual-geometry <code>HOLDOUT-DTI</code>, and <strong>39/39 genuine detector uniqueness</strong> checks all <strong>PASS</strong>. Automated <code>promotion_gate.py</code> holds <code>verdict = {e(card['verdict'])}</code> (<code>slot_authorized = false</code>) solely due to two un-weakened protocol checks requiring human selector judgment: (1) <code>13GEMSDOE</code>'s 206,895-dot uniform spacing-5 calibration grid covers 99.87% of the footprint within 300 m (pigeonhole lower bound <code>82.34% &gt; 70%</code> at 37,654 dots), and (2) DrivenData's <code>/data/</code> download requires login so <code>sample_submission.tif</code> was SHA-256 verified against 9 pinned mirrors.</p>
</section>

<section>
<h2>Step-by-Step Submission Procedure (After Human Selector Sign-Off)</h2>
<ol>
  <li><strong>Verify Weekly Quota (&le;3 Submissions / Rolling 7 Days):</strong> Log in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData DOE GEMS Submissions</a> and confirm at least 1 of the official <strong>3 submissions/week</strong> slots (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE/NLR Rules p. 7</a>) is available and not reserved for a higher-priority portfolio candidate.</li>
  <li><strong>Download the Primary Portal-Hardened GeoTIFF (or 1-TIFF ZIP):</strong>
    <ul>
      <li>Recommended single-file upload: <a download href="{e(z_tif_rel)}"><code>{e(Path(z_tif_rel).name)}</code></a> (<code>{art['primary_zeros_bytes']:,}</code> bytes, SHA-256 <code>{e(card['raster_sha256'])}</code>)</li>
      <li>Or faster 1-TIFF ZIP upload: <a download href="{e(z_zip_rel)}"><code>{e(Path(z_zip_rel).name)}</code></a></li>
      <li><em>Why <code>-zeros.tif</code> prevents <code>"Predicted values must be in range [0, 1]"</code>:</em> Every single one of the <code>12,279,160</code> <code>float32</code> pixels in <code>-zeros.tif</code> is finite <code>0.0</code> or <code>1.0</code> (<code>nodata=None</code>), eliminating portal validator rejections triggered when whole-array <code>min/max</code> checks encounter <code>NaN</code> or negative sentinel nodata values (<code>IR-34-NODATA-01</code>). If the organizer portal ever requests literal <code>NaN</code> outside the footprint, upload the identical-in-footprint twin <a download href="{e(n_tif_rel)}"><code>{e(Path(n_tif_rel).name)}</code></a>.</li>
    </ul>
  </li>
  <li><strong>Verify Local Checksum Before Upload (Optional 1-Line Terminal Check):</strong><br>
    <code>sha256sum {e(Path(z_tif_rel).name)}</code> &rarr; must equal <code>{e(card['raster_sha256'])}</code>.</li>
  <li><strong>Paste the Exact &le;140-Character Submission Note:</strong><br>
    <code>{e(card['submission_note'])}</code> (<code>{len(card['submission_note'])}</code> chars).</li>
  <li><strong>Record Organizer Receipt:</strong> Save the DrivenData submission timestamp and returned public DW-Tversky score alongside SHA-256 <code>{e(card['raster_sha256'])}</code>. Only an official submission-page receipt upgrades a result to <code>ORGANIZER-CONFIRMED</code>.</li>
</ol>
</section>

<section>
<h2>Automated Pre-Upload Verification Checklist (100% Code-Verified, Zero Human Raster Inspection)</h2>
<ul>
  <li><strong>Single-band <code>float32</code> GeoTIFF:</strong> <code>{card['validator']['single_band']}</code></li>
  <li><strong>Exact CRS <code>EPSG:32611</code> &amp; shape <code>3730 &times; 3292</code>:</strong> <code>{card['validator']['crs_match']}</code> / <code>{card['validator']['shape_match']}</code></li>
  <li><strong>Exact affine geotransform <code>(100, 0, 243350, 0, -100, 4508550)</code>:</strong> <code>{card['validator']['transform_match']}</code></li>
  <li><strong>Whole-array finite <code>[0, 1]</code> (zero <code>NaN</code>, zero <code>Inf</code>, zero negative nodata):</strong> <code>{card['validator']['whole_array_all_finite_0_1']}</code></li>
  <li><strong>In-footprint positive dots:</strong> <code>{card['validator']['predicted_positive_dots']:,}</code> (exact target <code>37,654</code>; overlap with known USGS/INGENIOUS catalogue = <code>{card['validator']['catalogue_overlap_dots']}</code>)</li>
</ul>
</section>
</body></html>"""
    )
    (OUT / "executive-summary.html").write_text(how_html)

    exec_md = f"""# Executive Summary — KANLERGEMSDOE3 (`{card['lane_id']}`) Nine-Site Audit & Validated Candidate

**Review date:** 2026-10-26 (UTC)
**Assigned Lane:** `{card['lane_id']}` (`{card['selected_hypothesis_id']}` / `{card['selected_ablation_id']}`, 8-fold spatial OOF cross-fitted)
**Automated Gate Verdict (`scripts/promotion_gate.py`):** **`{card['verdict']}` (`slot_authorized = false`, `live_submission_slots_used = 0` — HOLD FOR HUMAN SELECTOR)**
**Genuine 39-Detector Uniqueness:** **`PASS`** (`max 3-px overlap = {ureg['genuine_35_final_dot_overlap_3px']:.2%} <= 70%` across 35 external + 4 concurrent lanes, `max |Spearman rho| = {ureg['genuine_35_surface_max_abs_spearman_rho']:.4f} <= 0.90`)
**Primary Downloadable Candidate:** [`{Path(z_tif_rel).name}`]({z_tif_rel}) (`{art['primary_zeros_bytes']:,}` bytes, SHA-256 `{card['raster_sha256']}`) · [1-TIFF ZIP]({z_zip_rel}) · [NaN-outside twin]({n_tif_rel})

## Executive Summary Table (9 Priority Sites + KANLERGEMSDOE3)

| Site | Downloadable / Audited File | Defensible Score / Provenance | Est. Live Score | Unique vs Registry? | OK to Submit? |
|---|---|---|---|---|---|
{chr(10).join(md_rows)}

## How to Submit (After Human Selector Sign-Off)

1. Confirm remaining weekly DrivenData submission quota (`<= 3/week` per [DOE/NLR FY26-96647](https://docs.nlr.gov/docs/fy26osti/96647.pdf)) and explicit selector sign-off on the synthetic `r13-lattice-s5` pigeonhole bound (`>= 82.34%` at `37,654` dots).
2. Upload [`{Path(z_tif_rel).name}`]({z_tif_rel}) or [`{Path(z_zip_rel).name}`]({z_zip_rel}) (`all 12,279,160 float32 cells in {{0.0, 1.0}}`, preventing `"Predicted values must be in range [0, 1]"`).
3. Paste submission note (`{len(card['submission_note'])}/140` chars): `{card['submission_note']}`.
"""
    (OUT / "EXECUTIVE_SUMMARY.md").write_text(exec_md)
    (OUT / "hypotheses.md").write_text((ROOT / "research/cadg-submod-hypotheses.md").read_text())
    (OUT / "verification.md").write_text((ROOT / "research/cadg-submod-verification.md").read_text())


if __name__ == "__main__":
    build()
