# Repository review and continuation — 31 October 2026

## Decision at a glance

**NEGATIVE — no TIFF is approved for competition download or upload.** No new geological experiment or HOLDOUT-DTI was run in this review. No leaderboard estimate or ORGANIZER-CONFIRMED score exists for a new candidate. No slot was used or authorized.

The root README and active Pages output previously disagreed: the README's first section called a TIFF ineligible, a later section advertised it as unique and pending selection, and `docs/index.html` still exposed a download. The TIFF's own receipt also contradicted itself. I moved that unchanged artifact out of the published `docs/downloads/` directory into [`archive/quarantined-submissions/20261029/`](../archive/quarantined-submissions/20261029/) and independently reopened its bytes. It has 7,111,787 NaN cells over the 12,279,160-cell grid; its finite cells are in `[0,1]`. The NaN count equals the prepared manifest's outside-footprint cell count, but the footprint mask is absent here, so the exact NaN locations cannot be confirmed from the current checkout. A portal/global range scan can reject the NaNs. The old validator's `format_valid=true` conflicts with its own `no_nan_inside_footprint=false`, `inside_range_0_1=false`, `no_infinite_pixels_anywhere=false`, and `selected_encoding=false` fields. **Do not download or submit this file.** See the [saved-byte quarantine audit](../evidence/kanler-geofault-propensity-quarantine-20261031.json).

The fixed experiment period recorded in [`config/research-session-e2903b2e.json`](../config/research-session-e2903b2e.json) began 27 October, has an expired two-hour gate, and has `assigned_method_paragraph: null`. This review did not reset it. Missing prerequisites also include authenticated inputs/canonical cache, a complete semantically defined raster registry, a corrected central shared evaluator, and a reproducible same-fold incumbent. Running a holdout with substitute tools or participant mirrors would not satisfy the requested protocol.

## Historical focus-site executive table

The names and values below are from the user's historical list and the saved-byte focus-nine audit [`docs/data/focus9_family.json`](../docs/data/focus9_family.json). Every numeric value is **OWNER-REPORTED / UNVERIFIED**, not a submission-page receipt. “Score estimate” is **not estimable**: none of these reported values is a validated prediction for a new file. The measured overlap values describe the pinned historical focus-nine rasters only, not the complete or current registry. All nine fail the stated >70% peer-dot uniqueness condition in that comparison.

| Site | Historical file (learning/reference only) | Owner-reported value (unverified) | Score estimate for a new submission | Unique vs the other eight historical focus files? | OK to download/submit? |
|---|---|---:|---|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Not estimable | No — maximum peer overlap 100% | No — historical reference only |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Not estimable | No — maximum peer overlap 100% | No — historical reference only |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Not estimable | No — maximum peer overlap 98.02% | No — historical reference only |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Not estimable | No — maximum peer overlap 100% | No — historical reference only |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Not estimable | No — maximum peer overlap 100% | No — historical reference only |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Not estimable | No — maximum peer overlap 100% | No — historical reference only |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Not estimable | No — maximum peer overlap 100% | No — historical reference only |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Not estimable | No — maximum peer overlap 99.71% | No — historical reference only |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Not estimable | No — maximum peer overlap 97.58% | No — historical reference only |

The submitted competition file is not identified by a reliable file-linked receipt in these inputs, so even historical values should not be interpreted as verified scores for the raster names. Current participant pages in `docs/data/focus-feed.json` are source-change observations, not a complete registry, live score feed, or approval. The public participant repositories are the supplied data sources for the file artifacts, not evidence of organizer validation.

## GEMSDOE32 H33-B2: defensible interpretation, not causal certainty

The supplied `0.2778` is an unverified owner-reported value. The archived owner note is itself described in project evidence as “UNSCORED” and reports a projection of 0.2747; that inconsistency needs a submission-page receipt to resolve. The historical H33 explanation should therefore be framed as a falsifiable mechanism, not “why it scored” as a known fact.

A plausible metric-level mechanism is **prediction-mass efficiency**. Removing predictions that are redundant or near areas excluded from scoring could reduce false-positive mass while preserving distance-weighted credit on hidden faults. The official target is fault mapping, not direct geothermal-vent detection; the score can reward geometric proximity without proving a vent or a physical fault mechanism. Conversely, removed dots could have been near hidden continuation segments and supplied useful recall. The benefit depends on hidden-label geometry, the evaluator's exact exclusion and aggregation rules, and the specific raster.

The historical lineage reports are inconsistent across snapshots: one pinned audit describes a 44,090-dot D2.8 parent with 6,436 dots removed near the catalogue and none added; another older pinned comparison describes B2 as a subset of a B1 mask with 2,545 dots removed. Different pinned source revisions and the absence of a receipt-bound common artifact mean these counts must not be combined or silently selected. Exact byte lineage needs re-audit against one immutable source set. The focus-nine overlap audit does establish that these are not unique alternatives under the stated historical peer rule. The exact causal contribution of thinning, geology, hidden labels, fold choice, and evaluator version remains unknown. It is not a basis for copying or lightly perturbing B2.

## Ranked untried hypotheses (qualitative, not score projections)

These candidates are transcribed from [`research/hypotheses.md`](hypotheses.md), whose latest addendum records them as unimplemented. Rank is qualitative expected value conditional on a valid protocol and data; it is not a predicted DTI lift. Novelty against the broad ecosystem is uncertain until the complete registry/code audit is repaired.

| Rank | Hypothesis / layers | Physical signature and missing-fault rationale | Difference from implementations documented here | Named non-fault mimic | Cost and data viability |
|---:|---|---|---|---|---|
| 1 | Cross-field Morse–Smale junction persistence: RTP/TMI (bands 2, 14), TMI gradients (3, 9), isostatic gravity and gradients (13, 18, 11) | Detect persistent ridge/saddle graph junctions across signed, multiscale magnetic and gravity fields. A concealed relay/intersection could perturb independent potential fields without a strong single ridge or surface trace. | Not a pixelwise ridge, Hessian, texture score, or pointwise classifier; topological matching is not implemented in this repository snapshot. | Intrusive/lithologic intersections, basin-fill contacts, survey levelling seams | Medium. No extra external layer in principle, but official core rasters and canonical cache are absent/unauthenticated in this checkout; **not runnable now**. |
| 2 | Two-sided directional-fabric entropy break: RTP/TMI/gravity (2, 14, 13), with elevation/slope (12, 19) as confounder controls | Compare structure-tensor orientation distributions on opposing sides of a candidate boundary using Jensen–Shannon divergence. A buried fault may juxtapose differently oriented fabrics even where amplitude and topographic scarps are weak. | Targets a two-sided distribution discontinuity, not local orientation/coherence alone. | Angular unconformity, intrusive contact, survey block, cultural alignment | Medium. No new external layer in principle; same missing input/cache and protocol blockers. |
| 3 | Signed edge-migration stability under continuation: TMI/RTP (14, 2), TMI gradients (3, 9), depth-to-base (15) | Track signed zero crossings through a fixed continuation/scale ladder; persistent edge locations may indicate deeper source contrasts beneath cover. | Tracks signed edge trajectories rather than magnitude-only ridge persistence. Peer continuation work exists, so broader novelty is uncertain. | Deep lithologic contacts, basin margins, boundary/padding effects | Low–medium. No new external layer in principle, but requires verified data and registry comparison. |
| 4 | Hydrochemical geothermometer residual corridors: GDR 1391 chemistry/temperature, elevation/slope, independent magnetic axes | Condition geothermometer residuals on lithology/elevation and test coherent corridors aligned with a separate structural axis; this may indicate fluid pathways away from mapped traces. | Chemistry-conditioned residual modeling is not documented in the local implementation set; related thermal/geothermal methods exist in peer projects. | Mixing, evaporation, groundwater advection, seasonality, pumping, lab-batch effects | High and **not viable yet**. GDR 1391 is the specific official source index; exact archive bytes, variables, spatial coverage and dates were not verified obtainable in the prior documented check. No external-data-dependent test is proposed as ready. |

### Why the top hypothesis was not validated

The top proposal cannot be tested under the actual requirements in this checkout: (1) no assigned single-method paragraph, (2) expired recorded experiment/time gate, (3) no authenticated competition rasters or content-addressed canonical cache, (4) the shared evaluator has known synthetic invariant/soft-input defects requiring a central repair, (5) the complete registry and continuous-surface dot semantics are unresolved, and (6) no same-evaluator/same-fold incumbent is available. The official DrivenData data page was reported to redirect to login in the existing 29 October review; the repository restore script uses participant mirrors, not organizer-authenticated bytes. A claimed validation based on substitutes would be fabricated. No slot was touched.

## Provenance and official references

The following are official-source links preserved in this repository's source ledger; they are provided for review, not represented as freshly fetched during this turn:

- [DrivenData competition overview/rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS/GDR 1391 resource index](https://gdr.openei.org/submissions/1391)
- [USGS 3DEP product information](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [USGS-indexed Great Basin structural-discontinuities paper](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa)

## Three-pass review record

1. **Implementation / containment:** inspected the current generated site, latest review receipts, saved artifact bytes, manifests, and exact file hashes. Moved the prior range-risk TIFF/ZIP/card outside Pages and recorded the audit. No new prediction was created.
2. **Adversarial review:** found conflicting top-level README claims, a still-live Pages download, a stale generator mismatch, and a contradictory validator receipt. No result or historical claim was promoted. Installed the pinned Python requirements in ignored `.venv`; software tests exposed a generator/audit inventory mismatch that this change will address and retest.
3. **Requirements recheck:** table labels each source claim and estimate status; score causality remains unproven; candidate status is explicitly no-download/no-submit; hypotheses include layers, signature, rationale, novelty caveat, mimic, cost and data access; top validation is correctly marked not run; the JSON run card leaves absent measurements `null`. Final verification passed: 331 Python tests passed, 9 were skipped; all five deterministic page-builder checks and `scripts/check_run.py` passed; Chromium UI smoke checks passed at desktop and mobile widths across the active pages; `git diff --check` passed. These are software/UI checks, not scientific validation, official-source refresh, or portal acceptance.

## Remaining work / access limitations

1. Coordinator must assign one method paragraph and issue a fresh capped experiment authorization; do not reuse or reset the expired session clock.
2. Obtain organizer-authenticated competition data, or centrally approve documented provenance for the pinned cache; the participant mirror is not the organizer.
3. Repair and pin the shared metric/writer centrally, with synthetic tests for empty-truth pooled false positives and soft-surface semantics.
4. Publish a complete immutable registry including continuous surfaces and explicit dot-mask semantics; preserve the literal >0.90 rank-correlation / >70% within-3-pixel stop.
5. Reproduce a clean same-fold incumbent, then run per-feature leakage canaries and a whole-segment buffered hide-and-recover with exact visible-fault masking. Report `HOLDOUT-DTI` with evaluator version, withheld positive count and 95% CI; no projections as scores.
6. Only a candidate beating that paired incumbent and clearing pre-placement and final-dot registry checks can proceed to a separate selector. Current account quota and portal acceptance are unknown.
7. Refresh source observations through the scheduled GitHub workflow; stale participant feeds are not a live score feed.

See the single machine-readable run card [`evidence/session-20261031-run-card.json`](../evidence/session-20261031-run-card.json). This review itself has no TIFF to download.
