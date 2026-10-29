# Executive Summary — GEMSDOE Competition Submission Status

**DrivenData GEMS Geothermal Prize (Competition #306)**  
**Status: DO NOT SUBMIT — no holdout-validated candidate exists**  
**Generated: 2026-10-29 UTC**  
**Branch: `arena/2014e0c0-kanlergemsdoe3`**

---

## ⚠️ Top-Line Decision

| Question | Answer |
|---|---|
| Is there a downloadable TIF ready to submit? | **No.** A format-valid baseline TIF exists but has **not** passed holdout validation. |
| Can I download and submit a file today? | **No.** No candidate has beaten the holdout incumbent, and no single-method lane is assigned. |
| What is the highest verified score? | **None available.** All historical values are unverified owner reports, not organizer receipts. |
| What should I do? | Read the blockers below, validate a candidate on the holdout, then a separate selector authorizes a slot. |

---

## 1. Focus-Site Historical Claims (GEMSDOE 24, 25, 27, 28, 30, 31, 32, 33, 36)

All nine focus sites are owned by `buffedlizard55-lab` on GitHub Pages. The values below are **owner-reported claims from site pages**, not DrivenData submission receipts. They are **not** `ORGANIZER-CONFIRMED` scores and **not** `HOLDOUT-DTI` results. No estimate is offered because no holdout evaluation has been run for any candidate.

| # | Site | Best historical file (owner claim) | Owner-reported value | Evidence class | Unique vs focus peers? | OK to download & submit? |
|---|------|-----------------------------------|---------------------|----------------|----------------------|-------------------------|
| 1 | [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 2 | [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 3 | [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 4 | [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 5 | [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 6 | [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 7 | [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 8 | [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |
| 9 | [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Unverified owner report | **No** — exceeds 3-px overlap stop | **No** |

**Highest owner-reported claim:** GEMSDOE32 at 0.2778 (`h33-h33-2-b2-...-zeros`). This is the highest value in the supplied focus list, but it is **not** an organizer-confirmed score and **cannot** be submitted because it fails the literal duplicate stop (>70% of dots within 3 px of a registry raster).

---

## 2. Why GEMSDOE32's 0.2778 Is the Highest Claim — and Why We Cannot Copy It

GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (reported 0.2778) is the highest owner-reported value among the nine focus sites.

**Plausible mechanism (not proven causality):** The submission is a sparse dotted field (`-zeros` suffix, 44,090 dots reduced by near-catalogue thinning). Sparse placement reduces false-positive mass while retaining distance-tolerant coverage under the DTI metric (α=0.2 FP penalty, β=0.8 FN penalty, 300 m triangular kernel). Removing dots near the known USGS/INGENIOUS catalogue can reduce penalties on untruthful nearby predictions, but it can also remove credit for real nearby truth. Attributing the score to B2 masking or any specific geological mechanism requires controlled fold-local ablations — none are available from the site page.

**Why we cannot submit it:**
1. It fails the literal duplicate stop: GEMSDOE25 and GEMSDOE30 share identical 44,090-dot masks; GEMSDOE32 equals that mask after removing 6,436 dots within 2 px of the mirrored catalogue, with no additions.
2. It is not unique — it overlaps another focus-site raster.
3. No organizer receipt exists; the value is an unverified owner claim.
4. Submitting it would be copying a previous submission, which the project rules prohibit.

---

## 3. New Candidate: KANLER Baseline LR v1 (Format-Valid, Holdout-Pending)

A new, **unique** TIF has been generated using a logistic regression baseline on the 19 GEMSDOE training features. It is **format-valid** (all 13 audit checks pass) but has **not** been validated on the holdout. It must **not** be submitted until holdout DTI is measured and beats the incumbent.

| Field | Value |
|---|---|
| **File to download** | `gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-zeros.tif` |
| **ZIP bundle** | `gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-zeros.tif.zip` |
| **Estimated score** | **Not estimable** — holdout DTI not yet run (no lane assigned, no canonical cache) |
| **Unique submission?** | **Yes** — new baseline, not a copy of any focus-site file |
| **OK to download?** | **Yes** — format-valid GeoTIFF |
| **OK to submit?** | **No** — requires holdout validation and selector authorization |
| **SHA-256** | `82ecf4d2057ef678bea2dbe0ccc502ba046d05a64e82d3a4b258814dd98fb2b2` |
| **Submission note** | `KANLER baseline LR v1 | 19 features | holdout-pending | id 21b0bc23` (67 chars, ≤140) |
| **Positive pixels** | 3,245 (sparse, within budget) |
| **Value range** | [0.0, 1.0] everywhere, no NaN/Inf inside footprint |
| **Outside footprint** | 0.0 (zeros variant), avoiding the `[0,1]` portal range error |
| **CRS / shape / transform** | EPSG:32611 / 3730×3292 / 100 m, origin (243350, 4508550) — matches template |
| **Audit file** | `gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-audit.json` |

**Download link:** [docs/downloads/gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-zeros.tif](downloads/gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-zeros.tif)

---

## 4. Submission Instructions

### Step 1: Verify the file

Before downloading, confirm the SHA-256 matches the run card:

```bash
sha256sum gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-zeros.tif
# Expected: 82ecf4d2057ef678bea2dbe0ccc502ba046d05a64e82d3a4b258814dd98fb2b2
```

### Step 2: Format validation (already passed)

The file passed all 13 hard format checks:
- Single-band float32 GeoTIFF
- CRS: EPSG:32611, shape: 3730×3292, transform: 100 m origin (243350, 4508550)
- Values in [0, 1] inside the 5,167,373-pixel footprint
- No NaN or Inf inside the footprint
- 0.0 outside the footprint (zeros variant) — avoids the "Predicted values must be in range [0, 1]" error
- No positive pixels on known catalogue traces

### Step 3: Submit to DrivenData

1. Sign in to [DrivenData](https://www.drivendata.org/competitions/306/competition-doe-gems/)
2. Go to **Submit → Make new submission**
3. Upload the `.tif` (or `.zip` containing it)
4. In the **Note** field, enter: `KANLER baseline LR v1 | 19 features | holdout-pending | id 21b0bc23` (≤140 characters)
5. Submit only after a separate selector authorizes the weekly slot

### Step 4: Preserve the receipt

After submission, save the organizer's submission-page receipt. Only an actual receipt can support an `ORGANIZER-CONFIRMED` score.

---

## 5. Blockers (Why No Score Exists Yet)

| Blocker | Detail |
|---|---|
| No single-method lane | The parallel-run protocol requires an assigned lane; none is present. This is a blocker, not permission to invent one. |
| No canonical cached feature stack | The 35-channel derived feature cache bytes/digest are unavailable; private rebuilds are prohibited. |
| Shared evaluator defect | The pinned evaluator fails the synthetic empty-truth false-positive invariant (GEMSDOE32 issue #41). Central fix required. |
| No complete registry | A full frozen registry of all raster surfaces is not available for the uniqueness stop. |
| No same-fold incumbent | No baseline holdout result exists to compare against. |
| No weekly slot | Account remaining cap and slot authorization have not been verified. |
| Data provenance | Training data restored from participant-mirrored GitHub repos (SHA-256 verified) but not organizer-authenticated. DrivenData data download requires login. |

---

## 6. Required Next Steps (Before Any Submission)

1. **Resolve the lane** — obtain the assigned single-method paragraph before running experiments.
2. **Fix the shared evaluator** — pin a repaired central source for the empty-truth FP defect (GEMSDOE32 issue #41).
3. **Recover the canonical cache** — obtain the 35-channel feature bytes and digest (issue #53).
4. **Build the registry** — assemble the complete frozen registry of all raster surfaces.
5. **Run holdout validation** — buffered whole-segment hide-and-recover, pooled DTI (α=0.2, β=0.8, 300 m triangular kernel), withheld positives, 95% CI, paired vs incumbent.
6. **Run leakage canaries** — each feature alone; AUC > 0.90 is a leakage stop.
7. **Check uniqueness** — rank correlation ≤ 0.90 and ≤ 70% of dots within 3 px of any registry raster.
8. **Selector authorizes slot** — verify weekly cap before uploading.

---

## 7. Scientific Context

The competition target is fault detection using the Distance-Weighted Tversky Index (DTI):
- **α = 0.2** (false-positive penalty)
- **β = 0.8** (false-negative penalty)
- **R = 300 m** triangular kernel (3 pixels at 100 m resolution)
- **Format:** single-band float32 GeoTIFF, EPSG:32611, 100 m grid, 3730×3292, NaN or 0 outside the footprint

Official references:
- [Competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [GDR INGENIOUS #1391](https://gdr.openei.org/submissions/1391)

---

*This executive summary is a project artifact, not an organizer endorsement. No score is claimed, and no submission is authorized.*