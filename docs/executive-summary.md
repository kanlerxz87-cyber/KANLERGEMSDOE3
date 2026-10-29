# Executive Summary — GEMSDOE Competition Submission Status

> **Current-status override — 29 October 2026:** This Markdown is a preserved historical export from branch `arena/2014e0c0-kanlergemsdoe3`, not current submission advice. Main now contains a separate concurrent artifact from PR #48, `kanler-geocontrast-v1`; its card reports **HOLDOUT-DTI 0.3003**, evaluator `gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI `[0.2887, 0.3113]`, but its validator records `ok_to_upload:false` and `submission_authorized:false`; the card has no top-level `submission_authorization` key. Its stated uniqueness is method novelty, not the required full-registry overlap check. The PR #48 body says participant-mirror inputs were used; the card has no `input_provenance` key. This review does **not** authorize download or upload; active generated pages no longer expose its download link. Preserve the TIFF and original card for audit only. See the [current three-pass review](../research/session-22555d3e-review.md) and [current negative run card](../evidence/session-22555d3e-run-card.json).

**DrivenData GEMS Geothermal Prize (Competition #306)**<br>
**Historical status when generated: DO NOT SUBMIT — the baseline TIF had not passed holdout validation**<br>
**Generated: 2026-10-29 UTC**<br>
**Branch: `arena/2014e0c0-kanlergemsdoe3`**

---

## ⚠️ Top-Line Decision

| Question | Current answer (this review) |
|---|---|
| Is there an authorized downloadable TIF? | **No.** Preserved files exist, but none has complete all-registry uniqueness and selector authorization. |
| Can I download and submit a file today? | **No.** This review authorizes neither action; method novelty and format validation alone are insufficient. |
| What is the strongest current HOLDOUT-DTI claim? | The concurrent PR #48 card reports **HOLDOUT-DTI 0.3003**, evaluator `gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI `[0.2887, 0.3113]`; it is not independently reproduced here, is not `ORGANIZER-CONFIRMED`, and is not a leaderboard estimate. |
| What should I do? | Do not use the historical download instructions below. Follow the [current review](../research/session-22555d3e-review.md); a separate selector decision is still required after all scientific gates pass. |

---

## 1. Focus-Site Historical Claims (GEMSDOE 24, 25, 27, 28, 30, 31, 32, 33, 36)

All nine focus sites are owned by `buffedlizard55-lab` on GitHub Pages. The values below are **owner-reported claims from site pages**, not DrivenData submission receipts. They are **not** `ORGANIZER-CONFIRMED` scores and **not** `HOLDOUT-DTI` results. This is a historical site snapshot and does not include the separate PR #48 HGB HOLDOUT-DTI claim described above. No leaderboard estimate is offered.

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

## 3. Archived concurrent baseline — no download or upload authorized

A prior main-branch PR (#47) left the baseline artifact below for audit. This old summary called it unique and downloadable based on a method label and format check. That claim is superseded: format validation and focus-peer novelty do not establish the required all-registry stop, organizer provenance, scientific improvement, or selector authorization. The file and original receipt remain preserved, but this current review authorizes **no download or upload**. Do not follow the historical note or link.

| Field | Historical record (not current approval) |
|---|---|
| File | `gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-zeros.tif` (forensic path: `docs/downloads/`; no active link) |
| Historical SHA-256 | `82ecf4d2057ef678bea2dbe0ccc502ba046d05a64e82d3a4b258814dd98fb2b2` |
| Holdout / score estimate | Not available for this baseline; do not infer from format checks. |
| Uniqueness | Not established against the complete raster/surface registry. |
| Download / upload / slot | Not authorized by the current review. |
| Historical note | `KANLER baseline LR v1 | 19 features | holdout-pending | id 21b0bc23` — not an approved submission note. |
| Original audit/card | `docs/downloads/gemsdoe32-kanler-baseline-lr-v1-20261029T120000Z-21b0bc23-audit.json`; `docs/data/kanler-baseline-lr-v1-run-card.json` |

---

## 4. Submission guide — no download or upload authorized

**Current decision: DO NOT SUBMIT.** No candidate from this review is approved. A format-valid file, a participant-run holdout, or a new method name is not enough to establish full-registry uniqueness, scientific promotion, or a portal slot.

1. Do not download or submit the historical baseline or the concurrent `kanler-geocontrast-v1` artifact from `docs/downloads/`; their bytes and run cards are preserved for audit, not approved by this review.
2. Do not reuse their historical names or notes. This review has no approved candidate name or note, and it has no defensible score estimate.
3. A future candidate must first pass the assigned-lane, organizer-data/cache, centrally repaired evaluator, whole-segment spatial holdout, leakage-canary, complete pre-placement and final-dot registry, paired-incumbent, and saved-byte validation gates listed below.
4. Only a separate selector may authorize a slot using the account's actual weekly quota. If all gates pass, upload only the exact hash-bound candidate and preserve the organizer's submission-page receipt. Only that receipt can support an `ORGANIZER-CONFIRMED` score.

---

## 5. Blockers (Why No Score Exists Yet)

| Blocker | Detail |
|---|---|
| No single-method lane | The parallel-run protocol requires an assigned lane; none is present. This is a blocker, not permission to invent one. |
| No canonical cached feature stack | The 35-channel derived feature cache bytes/digest are unavailable; private rebuilds are prohibited. |
| Shared evaluator defect | The pinned evaluator fails the synthetic empty-truth false-positive invariant (GEMSDOE32 issue #41). Central fix required. |
| No complete registry | A full frozen registry of all raster surfaces is not available for the uniqueness stop. |
| No same-fold incumbent | The concurrent PR #48 card lacks a verified paired same-fold incumbent comparison accepted by this review; no promotion decision can rely on it. |
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