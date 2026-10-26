# KANLERGEMSDOE3 — DOE GEMS Geothermal Fault Discovery Desk & Autonomous `KANLER-H1` Engine

**Quick Navigation:** [Live UI / Executive Summary (`docs/index.html`)](docs/index.html) · [Contest Submission & `[0, 1]` Fix Guide (`docs/executive-summary.html`)](docs/executive-summary.html) · [PhD Analysis & Cross-Site Review (`research/review.md`)](research/review.md) · [5 Ranked Hypotheses & Results (`research/hypotheses.md`)](research/hypotheses.md) · [Frozen Pre-Registration (`research/preregistration_kanler_h1.md`)](research/preregistration_kanler_h1.md) · [Official Verification & Irregularities (`research/verification.md`)](research/verification.md) · [JSON Run Card (`docs/run-card.json`)](docs/run-card.json)

---

## 1. Executive Decision & Generated Unique GeoTIFF Status (`2026-10-26`)

| Item | Verified Status |
|---|---|
| **Generated Unique `.tif` (All-Finite Primary)** | [`docs/downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.tif`](docs/downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.tif) (`139,196 B`, `37,654` dots, SHA-256 `5e5a7b2925876a86473a50d523ee2d31b18da8b17809dcb00fa075cf817ea386`) + [`.zip` (`102,165 B`)](docs/downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.zip) |
| **Companion Template-Mask Twin (`NaN` Outside)** | [`docs/downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-nan.tif`](docs/downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-nan.tif) (`351,761 B`, identical `37,654` in-footprint dots, SHA-256 `97279cabe47a7e81eb47dc4caa1cbf0fd3143b451beb3a3440032e504f8a8db5`) + [`.zip` (`217,482 B`)](docs/downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-nan.zip) |
| **Unique Submission Name** | `kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.tif` |
| **DrivenData Tracking Note (`84 / 140` chars)** | `KANLER-H1 DCAP-LHC 37654d: dip-coupled piedmont+1mLiDAR+mag/hydro; holdoutDTI 0.1253` |
| **Gate `G1` — Format & `[0, 1]` Range** | **PASS** — `float32`, single band, `EPSG:32611`, `3730 × 3292`, transform `(100, 0, 243350, 0, -100, 4508550)`, `0` `NaN`/`Inf` inside footprint, strictly `[0.0, 1.0]`, `0` positive pixels on `labels.tif`. |
| **Gate `G2` — Single-Feature Leakage Canary** | **PASS** — All 10 input lines & composite surfaces `max(AUC, 1 - AUC) <= 0.7577 <= 0.90` (`H1_MULTI AUC = 0.6528`). |
| **Gate `G5` — Cross-Site Uniqueness (`415` Detector Rasters)** | **PASS** — Max final-dot 3-px overlap **`58.47% <= 70%`** (`39.74%` vs `GEMSDOE32` `0.2778`; `36.24%` vs `GEMSDOE31 H31-X`; `43.45%` vs `GEMSDOE24 D1.5`); surface `max |Spearman| = 0.1599 <= 0.90`; final-dot `max |Spearman| = 0.0408 <= 0.90`. *(Synthetic `5×5` calibration grid `13gems_r13-lattice-s5` covers `99.8713%` of Nevada within 3 px — Pigeonhole lower bound `82.16%` for `37,654` dots — disclosed transparently.)* |
| **Gate `G3` — Shared Holdout Incumbent (`gems57-pooled-hide-v2`)** | **FAIL (`0.1253` vs `0.1674` global holdout best)** — `HOLDOUT-DTI = 0.1253 [0.1080, 0.1414]` ($N=60,988$) decisively beat `CTRL` (`0.0671`, paired `+0.0582`) and `SLOPE` (`0.0486`, paired `+0.0767`), **beat `REF_H31X` in Walker Lane Quadrant 3 (`0.1726 vs 0.1602`)**, and lifted `<= 6°` piedmont off-catalogue `SGMC` discovery **`+28.1%` (`0.0569 vs 0.0444`)**, but trailed `REF_H31X` (`0.1674`) globally because `47.4%` of Quadrant 1 lacks 1 m 3DEP LiDAR coverage (`IR-KANLER-LIDAR-COVERAGE-STARVATION`). |
| **FINAL AUTOMATED SUBMISSION DECISION** | **`VERDICT: NEGATIVE` — OK TO DOWNLOAD FOR RESEARCH & FORMAT/UNIQUENESS VERIFICATION; DO NOT SPEND A WEEKLY LIVE DRIVENDATA SUBMISSION SLOT.** |

---

## 2. Executive Comparison Table: `KANLERGEMSDOE3` + All 9 Focus Sites + Portfolio Benchmarks

All score numbers obey Protocol Rule 3 (`HOLDOUT-DTI` with evaluator version, withheld $N$, and 95% CI; `OWNER-REPORTED` for sibling leaderboard reports lacking archived portal receipts; zero projections presented as scores).

| Site / Repo | Primary File to Inspect / Download | Dots | Leaderboard Score (Strictly Labeled) | Shared `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, $N=60,988$) | Uniqueness Status (`<=70%` 3-px & `|rho|<=0.90`) | Approved to Submit Live? |
|---|---|---:|---|---|---|---|
| **`KANLERGEMSDOE3` (This Run — `KANLER-H1`)** | `docs/downloads/kanlergems3-h1-dcap-lhc-37654-20261026-431237cf-zeros.tif` (+ `-nan.tif`) | `37,654` | Unsubmitted (`0` slots used) | **`0.1253 [0.1080, 0.1414]`** (`Q3 = 0.1726`; confirm `0.1107` on $N=29,965$) | **UNIQUE vs all 415 detectors** (`max 58.47%` 3-px; `39.74%` vs `H33`; `|rho|=0.1599`) | **NO (`verdict: negative` — research download only; Q1 LiDAR starvation)** |
| **`GEMSDOE32` (Historical Best)** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | `37,654` | **`0.2778` (`OWNER-REPORTED` — Highest Focus Score)** | `H50 = 0.0126` (2026-10-26 lane) | **DUPLICATE** (`98.49%` vs `28/36`, `100%` subset of `D2.8`) | **NO** (already submitted; family duplicate) |
| **`GEMSDOE36`** | `gemsdoe36-atbe-b2-h33-plus1200-20261005-872264e3-zeros.tif` | `38,854` | `0.2750` (`OWNER-REPORTED`) | `H36-R3` negative | **DUPLICATE** (`96.91%` vs `GEMSDOE32`) | **NO** |
| **`GEMSDOE28`** | `gemsdoe28-h28c-edgerelief-37660-20261004-f8ba1dc8-zeros.tif` | `37,660` | `0.2710` (`OWNER-REPORTED`) | `CSPD = 0.0369 [0.0258, 0.0493]` | **DUPLICATE** (`98.49%` vs `GEMSDOE32`) | **NO** |
| **`GEMSDOE31` (Holdout Best)** | Historic: `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif`; **2026-10-26:** `gemsdoe31-h31x-piedmont-junction-37654-20261026-5a956da9-zeros.tif` | `40,199` / `37,654` | Historic `h27-4`: `0.2708` (`OWNER-REPORTED`); `H31-X`: unsubmitted | **`H31-X = 0.1661 [0.1499, 0.1821]`** (`0.1674` local repro; confirm `0.1462`) | Historic: `100%` subset of `D2.8`. `H31-X`: `63.05%` final dots (`86.31%` pre-placement `top-K`) | **NO** (`H31-X` failed pre-placement `top-K` & 5-px lattice gate) |
| **`GEMSDOE33`** | `gemsdoe33-stepover-b1-20261004-d9777b8d-nan.tif` | `41,865` | `0.2632` (`OWNER-REPORTED`) | `DPPS = 0.0954` | **DUPLICATE** (`96.26%` vs `GEMSDOE31`) | **NO** |
| **`GEMSDOE25`** | `gems25-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-allfinite.tif` | `44,090` | `0.2600` (`OWNER-REPORTED`) | Legacy `B1` only | **DUPLICATE** (`100.00%` identical to `GEMSDOE30`) | **NO** |
| **`GEMSDOE30`** | `gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | `44,090` | `0.2600` (`OWNER-REPORTED`) | Not run (`0` new exps) | **DUPLICATE** (`100.00%` identical to `GEMSDOE25`) | **NO** |
| **`GEMSDOE24`** | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` | `60,069` | `0.2477` (`OWNER-REPORTED`) | `H24-R5 = 0.0593` ($n=29,880$) | **DUPLICATE** (`96.59%` vs `GEMSDOE27`) | **NO** |
| **`GEMSDOE27`** | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` | `61,328` | `0.2449` (`OWNER-REPORTED`); `H29-S = 0.2190` | `H31-1 = 0.0473` (40-cell CV) | **DUPLICATE** (`94.67%` vs `GEMSDOE24`) | **NO** |
| *Context: `GEMSDOE70`* | `gems70-p5-dual-submod300-oof38k` / `P9` | `37,654` | **`0.2478` (`OWNER-REPORTED` — Best Non-`H19-5` Live)** | `P9 = 0.1100` (`gems57-pooled-hide-v2`) | Genuine non-`H19-5` (`45.39%` vs `KANLER-H1`) | Historical benchmark |
| *Context: `19GEMSDOE`* | `gems19-h19-5-powerlaw-budget-multiline-corroborated` | `121,131` | `0.1922` (`OWNER-REPORTED`) | Ancestor ridge surface | Parent of all 9 focus winners | Superseded |

---

## 3. PhD Summary: Why `0.2778` Won & How to Beat `0.2778` Toward `0.33–0.4437`

1. **Why `GEMSDOE32` (`0.2778`) Won Within the `H19-5` Family:**
   - **MAX-vs-SUM DTI Asymmetry (`0.1922 -> 0.2600`):** Under pooled DTI ($\alpha=0.2, \beta=0.8, R=300\text{ m}$), $\text{TP}_w$ takes $\max_x p(x)k(d(x,g))$ while $\text{FP}_w$ sums $\sum_x p(x)(1-q(x))$. Thinning `19GEMSDOE H19-5` (`121,131` solid ridge pixels) to `d = 2.8 px` binary dots (`44,090` dots) cut $\text{FP}_w$ by $63.6\%$ while retaining $1 - 2.8/12 = 76.7\%$ line coverage on true traces.
   - **Pixel-Exact Catalogue Collar Pruning (`0.2600 -> 0.2708 -> 0.2778`):** Per DrivenData Staff Ruling `#11516`, mapped `labels.tif` faults are masked pixel-exactly (`0 m` buffer). Deleting `6,436` scarp-flank dots in $0 < d_{\text{cat}} \le 2\text{ px}$ (where new-fault truth is $93\text{–}99\%$ depleted) stripped $\approx 1,280$ denominator penalty units at negligible $\text{TP}_w$ loss (`+0.0178`).
2. **Why `0.2778` Can Be Surpassed (Live Leaderboard `#1 = 0.4437`, `#5 = 0.3561` on `2026-10-26`) & Exact `KANLER-H1.1` Next Steps:**
   - In **Quadrant 3 (Walker Lane / Hawthorne-Tonopah, `92.9%` 1 m LiDAR coverage)**, `KANLER-H1` (`H1_MULTI`) **already beat `REF_H31X` (`0.1726 vs 0.1602`)** at only `39.74%` overlap with `GEMSDOE32` (`0.2778`).
   - **Next Session Priority 1 (`KANLER-H1.1` Coverage-Invariant Quantile Fusion):** Apply conditional rank normalization separately inside `lidar_valid == 1` (`75.4%` of footprint) and `lidar_valid == 0` (`24.6%`, concentrated `47.4%` in Quadrant 1) so missing 3DEP tiles never starve northern Basin-and-Range quadrants (`3,296 -> ~9,500` Q1 dots).
   - **Next Session Priority 2 (Pure Non-Negative Slope-Asymmetry Gate):** Remove `det_elev(0) > det_elev(+3u)` trough clipping (`Band 12 det_elev` is high-pass detrended residual elevation with negative piedmont-toe troughs) and gate strictly on `Band 19 det_elev_slope` asymmetry $s(-3\hat{u}) > s(+3\hat{u})$.
   - **Next Session Priority 3 (Multi-Scale Spatial Convolutional / Gabor Encoder Under SAR-PU Loss):** Train a lightweight 4-fold spatially blocked U-Net / Gabor receptive-field encoder (`3–8 km` aperture) with observability-weighted Positive-Unlabeled loss so en-echelon fault continuity across alluvial wash gaps is learned before 300 m submodular dot allocation.

---

## 4. Autonomous Reproduction & Test Suite

```bash
# 1. Create virtualenv & install pinned scientific stack
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Autonomously restore & SHA-256-verify competition stack, external USGS/DOE layers & 417 registry rasters
#    (Streams via blobless git / codeload into gitignored .cache/ — zero DrivenData login or REST quota required)
bash scripts/download_competition_data.sh

# 3. Execute frozen 3-experiment KANLER-H1 pipeline, 417-raster uniqueness audit & dual GeoTIFF packaging
.venv/bin/python scripts/run_kanler_h1.py

# 4. Generate canonical JSON Run Cards, rebuild GitHub Pages UI, and run full automated test suite
.venv/bin/python scripts/write_run_card.py
.venv/bin/python scripts/build_site.py
.venv/bin/pytest -q
```

---

## 5. Standing Project Guidance (Stored Prompt & Governance)

<details>
<summary><strong>Click to expand complete stored user prompt &amp; Parallel-Run Protocol guidance</strong></summary>

1. **First Action:** Review the repo and complete next steps from previous sessions first; store this guidance in `README.md`.
2. **Focus-Site Review (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36` + `GEMSDOE..GEMSDOE92`):** Build a clean GitHub Pages UI (`docs/index.html`) with an executive summary at the top and a contest-submission subpage (`docs/executive-summary.html`). Clearly tabulate file to download, strictly labeled score (`HOLDOUT-DTI` or `ORGANIZER-CONFIRMED`, or quarantined `OWNER-REPORTED`), uniqueness across GEMSDOE sites, and unmistakable `OK to download / submit` status.
3. **PhD Analysis of `0.2778`:** Explain why and how `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778`) achieved the highest focus-site score and whether/how a submission can beat `0.2778` (toward `0.3195` / `0.4413+` live highs; verified `2026-10-26` live `#1 = 0.4437`).
4. **Unique GeoTIFF Generation & Automated Validation:** Must generate a genuinely unique `.tif` submission (never copy a prior submission except for learning/comparison) validated automatically without human raster inspection: single-band `float32`, `EPSG:32611`, `3730 × 3292`, exact geotransform matching `example_submission.tif`, no `NaN` inside footprint, values strictly in `[0, 1]` (preventing `"Predicted values must be in range [0, 1]"`), zero positive mass on known `labels.tif` catalogue, unique name + `<= 140`-character note, directly clickable for laptop download.
5. **Parallel-Run Protocol:**
   - **Lane & Uniqueness:** Stay inside one pre-registered method lane per session. Check BOTH on the continuous surface before placement AND on final dots against the full registry: stop/flag if `|Spearman| > 0.90` OR `> 70%` of dots fall within `3 px` of any registry raster's dots.
   - **Reuse, Don't Rebuild:** Use shared `vendor/gems57` cached features, `evaluate_holdout.py`, and `submission_writer.py`. Fix shared bugs in the template and report them — no private forks. Hide-and-recover whole fault segments with buffer; derive catalogue features from visible faults only; mask visible faults pixel-exactly; score pooled DTI (`alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel).
   - **Score Labeling:** Every score must be labeled `HOLDOUT-DTI` (evaluator version, withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (portal receipt). Never write a projection as a score.
   - **Leakage Canary:** Test each feature alone first; single-feature `AUC > 0.90` means leakage until proven otherwise.
   - **Run Card & Budget:** Stop after at most `3` experiments or `2` hours. Emit one JSON Run Card (`hypothesis`, `mechanism`, `non_fault_mimic`, `holdout_dti` + 95% CI, registry correlation/overlap, `raster_sha256`, validator output, submission name + `<= 140`-char note, and `verdict`: `promote` or `negative`). Do not spend a live slot on an idea that has not beaten holdout best.
6. **Multi-Pass Engineering & Git Workflow:** Execute Pass 1 (implement & verify), Pass 2 (find & fix bugs/assumptions/edge cases), and Pass 3 (line-by-line prompt re-check), verify all claims against official sources (`drivendata.org`, `docs.nlr.gov/docs/fy26osti/96647.pdf`, `usgs.gov`, `gdr.openei.org/submissions/1391`), open a PR from the session branch, and merge onto `main`.

</details>
