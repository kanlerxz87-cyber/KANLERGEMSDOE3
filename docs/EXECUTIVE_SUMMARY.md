> **Historical snapshot — superseded.** This earlier review predates the restored shared template, feature stack, and decisive positive-everywhere witness. Some data/uniqueness statements below are now stale. See the [current executive desk](index.html), [scientific review](review.html), and [current run card](data/current-run-card.json). The stop/no-submit decision remains in force.

# Executive summary — repository review and nine-site submission audit

**Review date:** 2026-10-26 (UTC)
**Decision:** 🔴 **DO NOT SUBMIT — no submission TIFF is available or authorized.**
**Scope:** This checkout plus the nine site claims explicitly supplied by the project owner.
**Experiments run:** 0. **HOLDOUT-DTI measurements:** none. **Organizer receipts inspected:** none.

## Decision in brief

The highest figure in the supplied nine-site list is the GEMSDOE32 claim, **0.2778** for `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`. That number is **owner-provided and unverified here**, not an `ORGANIZER-CONFIRMED` receipt and not a holdout result from this checkout. The number does not establish why the artifact scored as it did, and it cannot be used as a training label or forecast.

The [GEMSDOE32 public page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) was fetched on 2026-10-26. It labels 0.2778 **OWNER-REPORT**, says no submission-page receipt linking raster hash to score is present in that repository, identifies the 37,654-dot H33 file as already submitted, and says not to resubmit. The same page's status banner says no new file is authorized and lists holdout, off-catalogue regression, uniqueness, format, and separate selector gates. The public page provides meaningful documentation, but does not prove the competition score's cause. It describes subsequent research artifacts as negative; we did not retrieve or rerun their TIFFs or local evaluator. A related audit on that page discusses H33 as pruning relative to a prior dot set, while cautioning that reconstruction does not identify which dropped/retained points were true/false positives. That is a plausible hypothesis for why thinning could help under a false-positive-penalizing metric, not causal evidence. See [Sources](SOURCES.md).

**No score estimate is defensible.** There is no template, data, cached feature stack, holdout evaluator, writer, registry, or submission receipt in this repository. The user-provided leaderboard figures (including 0.3195 and 0.4413) conflict with each other and were not freshly verified. Treat them as unverified claims; do not extrapolate them into estimates.

**No unique TIFF can responsibly be generated here.** The strict requirements call for exact sample-grid matching, [0,1] validation and registry-wide duplicate checks before and after placement. Inputs to perform those checks are absent. Creating a synthetic or empty GeoTIFF would falsely imply competition readiness. Consequently there is no download link and no `OK TO SUBMIT` status.

## Nine-site comparison

Every result below is transcribed from the user's supplied site history. **All scores are `OWNER-REPORTED / UNVERIFIED` in this review**—none is `HOLDOUT-DTI` or `ORGANIZER-CONFIRMED`. “Unique?” means verified pixel-level uniqueness against the listed sites' registries, not distinct filename. Since this checkout contains no raster artifacts/registry, every uniqueness answer is **unknown**.

| Site | Highest supplied claim (unverified) | Named artifact | Est. score | Unique vs other eight? | Action |
|---|---:|---|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | 0.2477 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | **Not estimable** | Unknown; not audited | Treat as historical baseline only |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | 0.2600 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | **Not estimable** | Unknown; not audited | Treat as historical baseline only |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | 0.2449 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | **Not estimable** | Unknown; not audited | Treat as historical baseline only |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | 0.2710 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | **Not estimable** | Unknown; not audited | Highest supplied claim for this site; no selection implied |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | 0.2600 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | **Not estimable** | Unknown; not audited | Treat as historical baseline only |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | 0.2708 | `h27-4-solo-d28-20261004-8acb75e1-nan` | **Not estimable** | Unknown; not audited | Closely related naming/lineage needs byte comparison |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | **0.2778** | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **Not estimable** | Unknown; not audited | Highest supplied nine-site claim; not approved |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | 0.2632 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | **Not estimable** | Unknown; not audited | Tip/stepover idea is already represented in the supplied history |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | 0.2750 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | **Not estimable** | Unknown; not audited | Second-highest supplied claim; PINN label alone is not validation |

**Best to investigate first, not to submit:** H33-B2 from site 32 is the highest *reported* claim among these nine. It cannot be called the best verified submission, estimated as a predicted score, or declared unique until its exact bytes, receipt, and registry comparisons are obtained and run through an identical spatial holdout protocol.

## Why 0.2778 might be higher (carefully bounded explanation)

The official metric weights distance with a 300 m triangular kernel and uses α=0.2, β=0.8. That makes false negatives costlier than false positives in the specified denominator, but false-positive mass still matters. If two prediction sets cover similar recoverable fault length, removing redundant/off-target predictions can improve the ratio by lowering the false-positive term more than it lowers weighted true positives. This provides a plausible *mechanistic explanation* for why a thinner map could outperform a denser ancestor.

The supplied owner history labels H33 as “zeros” and site 32 reports 37,654 dots; naming and point counts alone do not establish its actual pixel values, geospatial alignment, lineage, or score provenance. Even if a file is an exact subset of a prior map, aggregate leaderboard performance cannot tell whether removed points were false alarms or missed real faults. Only organizer scoring receipts or a valid spatial hide-and-recover holdout can answer predictive-performance questions. There is no evidence here to claim it beat 0.2778 or that a new candidate can beat the claimed 0.3195/0.4413.

## Why work stops before the first experiment

The checkout consists only of a one-line README at the starting commit. There are no model scripts or tests and no files under `data/`. The shared template/cached feature stack, `evaluate_holdout.py`, `submission_writer.py`, sample grid, fault-label raster/vectors, and registry surfaces are not available here. The provided project brief also says DrivenData authentication is required for the competition download page; we cannot authenticate or fetch login-only files from this blank checkout. Those are blocking prerequisites for the mandated experiment and TIF validation. No external substitute was downloaded or silently treated as equivalent.

This is not a reason to relax the protocol. It is the result: **negative / blocked; no DTI measured, no projection, no TIF, zero submission slots used.** See [`run-card.json`](../run-card.json) and the next-step list in the [project charter](../README.md).

## Three-pass completion review

1. **Pass 1 — inventory and implement:** inspected the checkout and branch, checked the official problem/metric/formats page, and created the standing charter, nine-site score-provenance table, ranked hypotheses, source register, submission procedure, static overview, and negative JSON run card.
2. **Pass 2 — challenge assumptions:** distinguished organizer facts from user/site claims, avoided inferring scores from unrelated leaderboard figures, checked that H33's proposed pruning explanation is presented as a possible mechanism rather than proven causality, and confirmed that no dataset/evaluator/registry exists here. Did not fabricate a TIFF to satisfy a file request.
3. **Pass 3 — verify outputs:** parsed the JSON; parsed the HTML; checked all relative Markdown links, checked whitespace with `git diff --check`, and re-read the required protocol against the README, hypotheses, submission guide, and run card. These are documentation integrity checks, not raster validation, model tests, or holdout experiments.
