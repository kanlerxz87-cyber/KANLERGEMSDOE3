# KANLERGEMSDOE3 — DOE GEMS (#306) Concealed-Fault Discovery & Submission Decision Desk

> **GATE & SUBMIT-READINESS BANNER (`2026-10-26 UTC`)**
> - **1. Candidate GeoTIFF & 1-TIFF ZIP Download (`download_ready`):** **`YES — VALIDATED (15/15 BYTE CHECKS PASS)`**
>   - **Primary Portal-Hardened Finite `[0, 1]` GeoTIFF (`-zeros.tif`):** [`docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif`](docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif) (`826,642` bytes · SHA-256 `9f4b590d0bd887632c54ec34c114136d4de52d452de052ba105e35ebfeffe8b5`)
>   - **Primary 1-TIFF Competition ZIP (`-zeros.zip`):** [`docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.zip`](docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.zip) (`172,533` bytes)
>   - **Official-Text `NaN`-Outside Twin (`-nan.tif` / `.zip`):** [`-nan.tif`](docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-nan.tif) · [`-nan.zip`](docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-nan.zip) · [Writer Receipt JSON](docs/downloads/receipt-kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00.json) · [JSON Run Card](run-card.json)
> - **2. Scientific Holdout & Genuine Detector Uniqueness:** **`PASS`**
>   - **Primary `HOLDOUT-DTI` (`gems-segment-pooled-v1`, `60,988` withheld positives, `1.5 km` whole-segment buffer):** **`0.155510`** (`95% CI: [0.141542, 0.169790]`) — **`+52.1%`** over matched `B0_regional_d28` (`0.102267`, paired `Δ = +0.053242`, `95% CI: [+0.042450, +0.064542]`, `4/4` folds), **`+37.3%`** over `GEMSDOE33 B1_regional` (`0.113244`), and **`+13.7%`** over `GEMSDOE33 A33-R2-CSHT` (`0.136716`).
>   - **Orthogonal Confirmation (`diagonal-wedge-buffered-20px-confirm-v1`):** **`0.151134`** vs `B0_regional_d28 = 0.100111` (paired `Δ = +0.051023`, `95% CI: [+0.038173, +0.064083]`, `4/4` folds).
>   - **Two-Polarity Leakage Canary (`80` features):** **`PASS`** (`max two-sided AUC = 0.6296 <= 0.90`).
>   - **Uniqueness vs All `35/35` Genuine Geological Fault-Detector Rasters (12 repos):** **`PASS`** — pre-placement surface `|ρ| = 0.1598 <= 0.90`, `3-px = 0.6236 <= 0.70`; final binary dots `|ρ| = 0.0509 <= 0.90`, **`max 3-px overlap = 0.5711 <= 0.70`** (**`0.4632`** vs `GEMSDOE32` `0.2778` — `53.7%` newly discovered off-catalogue fault predictions).
> - **3. Automated Promotion Gate (`scripts/promotion_gate.py`):** **`verdict = "negative"` · `slot_authorized = false` · `0` Weekly Slots Used (HOLD FOR HUMAN SELECTOR)**
>   - Per [`research/review.md`](research/review.md) (*"report that conflict rather than weakening the gate"*), two non-model protocol blocks remain fail-closed until explicit human selector sign-off: (1) `13GEMSDOE` uniform `5×5` spacing calibration lattice `calib_r13lattice_00904.tif` (`206,895` grid dots covering `99.8713%` of all footprint cells within `3 px`) forces mathematical minimum forward overlap `1 - 6,649 / 37,654 = 82.34% > 70%` (`99.75%` measured) for any `37,654`-dot raster (`IR-42-UNIQ-01`), and (2) `template_provenance_verified = false` because DrivenData's `/data/` tab requires authenticated login (`sample_submission.tif` verified via SHA-256 `2176d08e...` across 9 pinned sibling mirrors).
> - **Unique Submission Name:** `kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00`
> - **Submission Note (`90 / 140` chars):** `K3 Exp-K3-3 8f-OOF: decontam scarp+TMI150+hydro 300m CELF 37654d | HOLD-SEL | 9a4ecfd71d00`

**Quick Navigation:** [Static Homepage (`docs/index.html`)](docs/index.html) · [How to Submit Subpage (`docs/executive-summary.html`)](docs/executive-summary.html) · [Executive Summary Markdown](docs/EXECUTIVE_SUMMARY.md) · [Preregistered Hypotheses](research/hypotheses.md) · [Frozen Preregistration JSON](evidence/preregistration_20261026.json) · [JSON Run Card](run-card.json) · [3-Pass Verification Log](research/verification.md) · [Standing Requirements](research/standing-requirements.md)

---

## 1. Executive Summary Table — 9 Priority GEMSDOE Sites + `KANLERGEMSDOE3`

All historical sibling scores are preserved strictly as `UNVERIFIED OWNER REPORT` (no organizer submission-page receipt binds raster SHA-256 to score). On `2026-10-26 UTC`, the live public leaderboard at [DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed **`#1 xiaofanhu = 0.4437`** (`31` submissions), **`#2 cfld__ = 0.3916`** (`18`), **`#3 Batik Shirt Brothers = 0.3904`** (`53`), **`#4 BrandenKMurray = 0.3724`** (`32`), **`#5 No Fault of Our Own = 0.3561`** (`44`) — resolving the stale/conflicting `0.4413` and `0.3195` figures in earlier notes. Per Protocol Rule 3, projections are never reported as scores.

| Site | Downloadable / Audited File | Defensible Score / Provenance | Est. Live Score | Unique vs Registry? | OK to Submit? |
|---|---|---|---|---|---|
| `GEMSDOE24` | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` (`60,069` dots) | `0.2477` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** (historical duplicate) |
| `GEMSDOE25` | `gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-allfinite.tif` (`44,090` dots) | `0.2600` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** (historical duplicate) |
| `GEMSDOE27` | `gems27-tgc-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` (`61,328` dots) | `0.2449` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`97.97%` peer 3-px overlap) | **NO** (historical duplicate) |
| `GEMSDOE28` | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` (`37,660` dots) | `0.2710` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`99.87%` peer 3-px overlap) | **NO** (historical duplicate) |
| `GEMSDOE30` | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` (`44,090` dots) | `0.2600` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** (historical duplicate) |
| `GEMSDOE31` | `gems31-h27-4-solo-d28-20261004-8acb75e1-zeros.tif` (`40,199` dots) | `0.2708` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** (historical duplicate) |
| `GEMSDOE32` | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`37,654` dots) | `0.2778` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** (already submitted) |
| `GEMSDOE33` | `gems33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` (`41,865` dots) | `0.2632` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`89.94%` peer 3-px overlap) | **NO** (historical duplicate) |
| `GEMSDOE36` | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`38,854` dots) | `0.2750` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`96.91%` peer 3-px overlap) | **NO** (historical duplicate) |
| **`KANLERGEMSDOE3`** | [`kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif`](docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif) (`37,654` dots) | **`HOLDOUT-DTI 0.155510`** (`95% CI [0.1415, 0.1698]`, `60,988` pos, `gems-segment-pooled-v1`) | Not estimable | **YES vs all 35 real detectors** (`57.11%` max 3-px; `46.32%` vs `GEMSDOE32`; `99.75%` vs 207k lattice probe) | **HOLD FOR HUMAN SELECTOR** (`slot_authorized=false`) |

---

## 2. Forensic Analysis of `GEMSDOE32` (`0.2778`) & How `KANLERGEMSDOE3` Advances

1. **Exact Pixel-Subset Genealogy (`121k -> 44k -> 40k -> 37.6k`):**
   Byte-verified raster comparison proves every historical focus-site winner derives from `19GEMSDOE`'s `H19-5` (`121,131` dots, owner-reported `0.1922`):
   $$\text{H33-B2 }(37{,}654,\;0.2778) \subset \text{H27-4 }(40{,}199,\;0.2708) \subset \text{D2.8 }(44{,}090,\;0.2600) \subset \text{H19-5 }(121{,}131,\;0.1922)$$
   Specifically, `H33-B2 = D2.8 & (d_catalogue > 2.0 px)` deletes `6,436` near-catalogue dots in `(0, 2] px` (`200 m`) of existing USGS/INGENIOUS traces (`GEMSDOE36` `0.2750` simply adds `1,200` dots back to `H33-B2`).
2. **Official DTI Scoring Algebra & DrivenData Staff Confirmation:**
   On the official [DrivenData Task Description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [DrivenData Forum Thread #11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) (`chrisk-dd`, Sep 16), known USGS/INGENIOUS fault pixels are **masked/excluded from evaluation in both Phase 1 and Final Round**. Under $\text{DTI}(\alpha=0.2, \beta=0.8, R=300\text{ m})$, true-positive credit saturates via $\max_{x: d(x,g)\le 3\text{ px}} p(x)(1 - d/3)$, whereas every off-catalogue pixel sums linearly into $0.2\,\text{FP}_w$. Spacing dots at $\ge 2.5\text{–}2.8\text{ px}$ and applying a `2.05 px` catalogue collar eliminates redundant overlapping kernel mass and wall-rock halo false alarms.
3. **Why Static `H19-5` / `D2.8` Are Contaminated on `SegmentHoldout`:**
   Inspecting `19GEMSDOE/scripts/run_spatial_holdout_and_build.py` and `evaluate_h19_and_build_submissions.py` proves `H19-5` and `D2.8` were trained on legacy unbuffered quadrant splits (retaining cross-boundary halves of withheld faults and computing tip/stepover stress at `0 m` across fold borders) and post-masked on full `labels.tif == 0` across all 4 quadrants. Evaluating static `H33-B2` fairly on `SegmentHoldout(buffer_px=15)` scores `0.006708` (due to `d_labels <= 2` holes around withheld truth), whereas leak-free `37,654`-dot baselines score `0.064020` (`unsupervised_D28_37654`) and `0.102267` (`B0_regional_d28`).
4. **Why 8-Fold Spatial OOF Cross-Fitting (`Exp-K3-3`) Breaks Both Prior Ceilings:**
   In Pass 2 we discovered and fixed a major ML deployment failure mode (`IR-K3-INSAMPLE-COLLAR-01`): fitting boosted trees in-sample on the full footprint memorizes leaf neighborhoods around `labels.tif`, dumping `60.6%` of emitted dots into the `205–500 m` wall-rock collar (`d_cat <= 5 px`) and starving concealed basin faults (`d_cat > 1 km` = `9.7%`). Replacing in-sample refitting with **stitched 8-fold spatial out-of-fold cross-fitting** (`0.5 × 4-quadrant OOF + 0.5 × 4-diagonal-wedge OOF`) shifts **`62.9%` (`23,684` dots) into `d_catalogue > 1 km`**, raises blind-piedmont diagnostic `C_pied` (`ρ = +0.8667` across 22 live-scored owner entries) to `0.1124` (`+28.6%` over `GEMSDOE33 A33-R2-CSHT = 0.0874`), achieves **`HOLDOUT-DTI = 0.155510`**, and passes uniqueness across **all `35/35` genuine detector rasters** (`max 3-px = 0.5711 <= 0.70`).

---

## 3. Preregistered Geological Hypotheses & Controlled 3-Experiment Results

Locked prior to training in [`evidence/preregistration_20261026.json`](evidence/preregistration_20261026.json) (`SHA-256: e49c6aae3afafdcb60306ac79ff439d48fdfde2342b4fb9c0ba611fb23f54278`; full physics & DOIs in [`research/hypotheses.md`](research/hypotheses.md)):

| Rank & ID | Hypothesis & Exact Layers | Physical Signature & Transform | Named Non-Fault Confounder | Status & Measured `HOLDOUT-DTI` |
|---|---|---|---|---|
| **#1 `H-K3-1`** (`L-K3-CADG-SUBMOD`) | Cultural/pluvial-decontaminated 1 m LiDAR (`lidar_scarp_features_u8.tif` valid-eroded) + seamless 10 m 3DEP (`topo_10m_derived_100m_u8.tif`) + 150 m upward-continued TMI (`tmi` FFT $e^{-2\pi k \Delta z}$), gravity HGM, GeoDAWN K/Th/U (`10.5066/P93LGLVQ`), INGENIOUS 2 m probe/spring/sinter (`10.15121/1881483`) + 300 m CELF | Tectonic scarps exhibit mono-vergent step asymmetry (`\|down-up\|/(down+up+4)`), deep-persisting TMI/gravity tilt across basement steps, and K-metasomatism/thermal leakage away from roads & paleo-shorelines | US Census TIGER/Line 2024 road cuts (`tiger_road_distance_m.tif`), Pleistocene Lake Lahontan (`1332 m`) / Bonneville (`1463, 1552 m`) benches, and static volcanic contacts | **Selected & Validated (`3/3` budget):** `Exp-K3-1 = 0.148514` → `Exp-K3-2 = 0.152410` → **`Exp-K3-3 = 0.155510`** (`95% CI [0.1415, 0.1698]`); diagonal confirm **`0.151134`** |
| **#2 `H-K3-2`** | 10 m 3DEP stream-power $\chi$ disequilibrium (`dem10_chi_100m_i16.tif`) + profile curvature & `det_elev` | Active footwall tilt drives cross-divide $\Delta\chi$ jumps paired with range-front piedmont breaklines | Differential lithologic erosion across resistant welded-tuff hogbacks | Deferred for next session (`3/3` experiment budget respected) |
| **#3 `H-K3-3`** | `depth_to_base_surf`, `iso_grav_anom`, MT `cond_surf`..`cond_4000`, `geod_dilaterate` (`10.5066/P9TWT2LU`, `10.5066/P9Z6SA1Z`) | Dilatational stepover bridges combine localized basement-depth gradients with mid-crustal conductive fluid plumes | Conductive clay/evaporite playa brines (`cond_surf >> cond_2000`) | Deferred |
| **#4 `H-K3-4`** | `geod_maxext`, `geod_shearrate`, `geod_dilaterate` (`10.1785/0220220153`) + oriented TMI/gravity tilt | Concealed faults strike orthogonal ($\pm 25^\circ$) to principal GPS extension (`N60°W–N75°W`) or conjugate Riedel shear | Pre-Cenozoic sutures accidentally coaxial with modern extension | Deferred |

---

## 4. Preventing `"Predicted values must be in range [0, 1]"` (100% Automated Validation)

Every emitted GeoTIFF is verified directly from saved disk bytes by [`scripts/validate_submission.py`](scripts/validate_submission.py) (`audit(..., strict_zero_outside=True)` and `validate(...)`) with **zero human raster inspection**:
- **Root Cause (`IR-34-NODATA-01`):** DrivenData's portal validator rejects uploads with `"Predicted values must be in range [0, 1]"` when an array contains `NaN`, `±Inf`, float overshoots (`< 0` or `> 1`), or negative sentinel nodata values (`-9999.0`) evaluated before `nodata` masking.
- **Automated Prevention:** [`submission_writer.py`](submission_writer.py) clips and rounds binary predictions cleanly inside the footprint, zeroes known USGS/INGENIOUS catalogue pixels (`0` overlap), writes `0.0` outside the footprint with `nodata=None` in primary `-zeros.tif` (**all `12,279,160` `float32` pixels strictly in `{0.0, 1.0}`**), emits the official-text `-nan.tif` twin (`validate(...) -> ok: True`), packages single-GeoTIFF `.zip` archives, and re-opens saved disk bytes to assert `1` band, `EPSG:32611`, `3730 × 3292`, transform `(100, 0, 243350, 0, -100, 4508550)`, and SHA-256 parity.

---

## 5. Reproducible Commands

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1. Restore SHA-256-pinned data & 36-raster uniqueness registry into gitignored .cache/gems_data/
./scripts/download_competition_data.sh

# 2. Re-run full preregistered 80-canary + 3-experiment holdout + 8f-OOF emission (~17.5 min on 2 vCPUs)
.venv/bin/python scripts/run_kanlergems3_experiments.py

# 3. Fast byte-level verification of saved GeoTIFFs, Run Card, promotion gate, site & unit tests (<10 sec)
.venv/bin/python scripts/run_kanlergems3_experiments.py --verify-only
.venv/bin/python scripts/review.py && .venv/bin/python scripts/build_site.py
.venv/bin/python -m unittest discover -s tests -v
```

---

## 6. Verified Official Sources, Limitations & Next-Session Continuation

### Verified Official Links (Fetched 2026-10-26 UTC)
- **Competition Overview, Metric & Format Spec:** [DrivenData #306 Problem Description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [About Page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) · [Live Public Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) (`#1 = 0.4437`) · [Reference Solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- **Official DOE / NLR Prize Rules ($300k, `<= 3 submissions/week`, 1 final submission across Phase 1 & Phase 2):** [NLR Report FY26-96647 PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- **Official DrivenData Catalogue-Masking Clarification (`chrisk-dd`):** [Community Forum Thread #11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)
- **Official Public Geoscience Data Releases:** [DOE GDR #1391 INGENIOUS Regional Dataset (`10.15121/1881483`, CC-BY-4.0)](https://gdr.openei.org/submissions/1391) · [GBCGE INGENIOUS Project](https://gbcge.org/current-projects/ingenious/) · [USGS GeoDAWN (`10.5066/P93LGLVQ`, CC0)](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [EPSG:32611](https://epsg.io/32611)

### Remaining Work & Limitations
1. **Human Weekly-Slot Selector Step:** Because `13GEMSDOE`'s uniform `5×5` lattice probe (`calib_r13lattice_00904.tif`) covers `99.8713%` of all footprint cells within `3 px` (forcing `>= 82.34%` overlap for any `37,654`-dot raster) and DrivenData's `/data/` tab requires login authentication, `promotion_gate.py` holds `verdict = "negative"` (`slot_authorized = false`). A human selector should inspect [`docs/executive-summary.html`](docs/executive-summary.html), confirm weekly slot availability (`<= 3/week`), verify whether `calib_r13lattice_00904.tif` is treated as a non-detector density probe, and upload [`-zeros.tif`](docs/downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif) (or `.zip`) only if authorized.
2. **Next Scientific Lane (`H-K3-2`):** Evaluate drainage-divide $\chi$ disequilibrium (`dem10_chi_100m_i16.tif`) in a fresh preregistered 3-experiment budget on `SegmentHoldout(buffer_px=15)` to test whether geomorphic footwall-tilt signals further improve blind range-front recovery beyond `0.155510`.

---

## 7. Stored Core Task & Standing Parallel-Run Charter

Per standing project instructions ([`PROJECT_REQUEST.md`](PROJECT_REQUEST.md) & [`research/standing-requirements.md`](research/standing-requirements.md)), every session in `KANLERGEMSDOE3` adheres to **Arena Core Values (`Maximize P(Win)`, `Own the Outcome`)** and the 6-point Parallel-Run Protocol:
1. **Single-Method Lane & Uniqueness Stop:** Stay in one preregistered lane (`L-K3-CADG-SUBMOD`); screen both pre-placement surface and final dots (`|Spearman ρ| <= 0.90` and `<= 70%` dots within `3 px` of registry rasters); never copy or relabel a historical `.tif`.
2. **Shared Template & Hide-and-Recover Holdout:** Reuse SHA-256-pinned `vendor/gems24_template`, `evaluate_holdout.py`, and `submission_writer.py`; withhold whole fault segments with a spatial buffer (`1.5 km` / `2.0 km`); derive all catalogue features from `visible` faults only; mask `visible` faults pixel-exactly; score pooled DTI (`α = 0.2`, `β = 0.8`, `300 m` triangular kernel).
3. **Metric Provenance:** Report only `HOLDOUT-DTI` (with evaluator version, withheld-positive count, and 95% CI) or `ORGANIZER-CONFIRMED` (with submission-page receipt). Never report projections as scores.
4. **Leakage Canary:** Screen every feature alone first; halt if two-polarity `AUC > 0.90`.
5. **Run Card & Automated Byte Validation:** Emit one JSON Run Card (`run-card.json`) with hypothesis, mechanism, named non-fault mimic, holdout DTI + CI, registry overlap, SHA-256, 100% automated GeoTIFF validator checks (`[0, 1]` finite range, single band, `EPSG:32611`, exact shape/transform), unique submission name, `<= 140`-character note, and `promote` / `negative` verdict.
6. **Experiment & Slot Discipline:** At most `3` experiments per lane; promotion to a live weekly DrivenData slot (`<= 3/week`) is a separate human selector step.
