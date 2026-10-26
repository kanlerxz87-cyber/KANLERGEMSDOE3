> **Historical pre-experiment snapshot:** superseded by the [current dashboard](index.html) and [run card](run-card.json). Descriptions of missing inputs or zero experiments are no longer current.

# Executive review — GEMSDOE24/25/27/28/30/31/32/33/36

**Reviewed:** 2026-10-26 (UTC) · **Repository:** `KANLERGEMSDOE3` · **Starting checkout:** initial commit `d795e4e`; current branch also integrates concurrent `origin/main` review assets · **Decision:** no submission file is available or approved from this checkout.

## Decision at a glance

- **Best historical score among the nine named sites, according to the supplied prompt:** GEMSDOE32’s `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, reported as **0.2778 (OWNER-REPORTED; not organizer-confirmed here)**. This is a historical claim, not an estimate or a validated current candidate. Do not copy/resubmit it.
- **Highest public score on the official leaderboard when checked:** **0.4437**, displayed for the top public entry [on the live leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) retrieved during this review on 2026-10-26. This is a point-in-time page value and public results can change; it is not a private/final prize result. The prompt's 0.3195 and 0.4413 figures are both below this point-in-time fetch and should not be presented as current.
- **Score estimate for any new file from this checkout:** **not estimable**. The merged repository includes pinned upstream pages/metadata, archived evaluator/writer copies, and this review restored nine historical winner rasters plus the sample/label mirrors for audit. It still has no organizer-authenticated competition feature stack, complete raster registry, canonical integrated prediction runner, or new candidate TIFF. No submission-page receipt was supplied.
- **Download / submit:** **No new TIFF to download; do not submit any file from this checkout.** The documentation/gate-schema tests do not evaluate raster bytes or scientific performance; no geospatial validator or scientific holdout was run, so claiming a passing submission would be false.

The official metric is distance-weighted Tversky with alpha 0.2, beta 0.8 and a 300 m triangular support. This weighs false negatives more heavily than false positives and gives partial credit to predictions near labeled faults. It explains why line coverage/recall and placement tolerance can matter, but **does not establish why the named GEMSDOE32 file received its reported score**. A causal explanation requires verified file-to-receipt linkage, a reproducible implementation, and controlled tests. The GEMSDOE32 site itself describes 0.2778 as owner-reported without a receipt linking the score to that raster hash. See the [official metric and submission specification](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [GEMSDOE32 snapshot](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html).

## Nine-site executive table

The score column transcribes the user's supplied values; all are **OWNER-REPORTED**, not receipt-confirmed. Estimated leaderboard score is `Not estimable`. For uniqueness, this branch restored the nine pinned historical winner TIFFs from owner-maintained GitHub mirrors, verified their SHA-256 hashes against the pinned manifest, then recomputed 72 directed dot-overlap comparisons on the common grid. The minimum peer overlap is 86.718954%, above the strict >70% stop; each winner therefore fails uniqueness against at least one of the other eight focus-site winners. This is a final-dot audit of those nine artifacts only: the full raster registry and continuous-surface rank correlations are still unavailable. Details and hashes are in [`docs/audit.json`](audit.json); mirror hashes prove consistency with those owner mirrors, not organizer provenance.

| Site | Highest-scoring file named in prompt | Prompt score evidence | Estimated leaderboard score | Unique vs. focus-site registry? | Download / submit decision |
|---|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | **0.2477 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 100.00%; format-only status is separate). | Historical reference only; do not copy/resubmit. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | **0.2600 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 100.00%). | Historical reference only; do not copy/resubmit. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | **0.2449 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 98.02%). | Historical reference only; do not copy/resubmit. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | **0.2710 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 100.00%). | Historical reference only; do not copy/resubmit. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | **0.2600 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 100.00%). | Historical reference only; do not copy/resubmit. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan.tif` | **0.2708 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 100.00%). | Historical reference only; do not copy/resubmit. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | **0.2778 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 100.00%). Its in-footprint dot mask is an exact subset of the 40,199-dot GEMSDOE31 winner: 37,654 retained, 2,545 removed. Score-to-receipt linkage remains unverified. | Historical reference only; do not copy/resubmit. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | **0.2632 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 99.71%). | Historical reference only; do not copy/resubmit. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | **0.2750 OWNER-REPORTED** | Not estimable | **NO — duplicate under the nine-winner audit** (max directed 3-px overlap 97.58%). | Historical reference only; do not copy/resubmit. |

**Best among these user-supplied claims is GEMSDOE32 0.2778; that is not a recommendation.** The exact mask comparison confirms the B2 positives are a subset of the audited GEMSDOE31 40,199-dot raster: 2,545 points were removed and none added. Its 100% within-3-px overlap with at least one other winner independently fails the literal duplicate gate. The score may plausibly have benefited from removing low-credit predictions under the asymmetric metric, but no receipt or holdout/ablation establishes that causal explanation.

## Why the 0.2778 result is not a reliable blueprint by itself

1. **Metric effect, not causal proof.** The official metric makes false negatives four times as heavily weighted as false positives in the Tversky denominator coefficients (beta 0.8 vs alpha 0.2), with distance credit out to 300 m. A fault-like, spatially distributed map may therefore score better than a sparse/high-confidence point map. The exact effect depends on the hidden labels and raster values.
2. **Potential catalogue overlap.** A map generated by pruning/spacing around existing catalogued faults can score well on a spatial holdout if the holdout shares the same spatial sampling bias. Whole-segment buffered hide-and-recover and feature-only leakage canaries are needed; random pixel splits are not adequate evidence.
3. **Score-to-file uncertainty.** GEMSDOE32’s current page labels 0.2778 owner-reported and explicitly notes the missing receipt/hash linkage. No submission receipt was provided in this checkout. Consequently the number cannot be used as ORGANIZER-CONFIRMED evidence here.
4. **Leaderboard context changed.** The official public leaderboard at review time showed 0.4437 at rank 1, not the prompt’s 0.3195. Public scores move over time and should be date-stamped; neither number establishes private-set or final-award performance.
5. **No valid estimate from a filename.** The prediction file, evaluator, threshold/dot-budget sweep and matching receipts are necessary to determine why that score occurred. The implementation in this checkout is absent.

## Ranked candidate hypotheses — preregistration proposals only

The current checkout has no implemented methods to compare against. The nine live Pages snapshots show many mechanisms already explored (examples include LiDAR scarps, geothermal/thermal signals, potential-field edges/curvature, geophysical ensembles, seismic/hydrothermal proxies and dot-placement variants). Therefore the proposals below are **new formulations to this empty checkout, not certified novel across all GEMSDOE repositories**. First pin and search the full registry and experiment history. No experiment was run, and no numerical score gain is projected.

| Rank | Hypothesis and layers | Physical signature / why it could reveal an unmapped fault | Difference and confounder | Expected DTI upside (qualitative) | Cost / gate |
|---:|---|---|---|---|---|
| 1 | **Strain-boundary orientation coherence** — provided dilatation, shear-strain rate, and second invariant of strain rate tensor | Detect narrow, spatially coherent boundaries where strain magnitude changes sharply and the local tensor orientation is consistent along a line. A mapped-fault-missing rupture may still localize present-day deformation; use orientation/gradient consistency rather than simply thresholding high strain. | Specific to a derivative/tensor-coherence feature from listed strain layers; not evidence it has never been tried elsewhere. Mimics: basin margins, model interpolation seams, anthropogenic subsidence, broad tectonic block boundaries. | Medium, because independent kinematic support could complement static mapped-fault features; high uncertainty about whether 100 m resampled strains resolve local faults. | Medium. First test each layer alone (AUC canary), then blinded whole-segment holdout; implement only through shared stack/evaluator. |
| 2 | **Seismicity gradient / quiet-core boundary** — provided earthquake-density layer plus strain-rate layers | Seek persistent line-like transitions between earthquake-rich and relatively quiet domains, conditioned on coherent strain. Faults may form seismicity boundaries or locked/creeping contrasts absent from fault catalogs. | Uses a paired boundary statistic rather than earthquake density as a simple positive predictor. Mimics: incomplete seismic detection, station/network coverage, volcanic/hydrothermal clustering, temporal sampling. | Low-to-medium; the provided layer’s temporal/spatial construction may dominate signal. | Low-to-medium. Confirm metadata and leakage first; same blocked holdout; require robustness across spatial blocks. |
| 3 | **Magnetic-source-depth break with cross-scale persistence** — top-of-crustal magnetic source-depth estimate, RTP/TMI, and listed horizontal/vertical TMI derivatives | Find persistent offsets/gradients in inferred source depth whose edges are supported at more than one scale by magnetic derivative orientation; fault juxtaposition can change magnetic source geometry even when amplitude is weak. | Focuses on source-depth discontinuity and scale persistence, not raw anomaly peaks. Potential-field edges and curvature/dipole ideas are already prominent in the published experiment pages, so novelty risk is high. Mimics: lithologic contacts, flight-line artifacts, remanent magnetization. | Low-to-medium; independent subsurface evidence but likely correlated with previously explored magnetic methods. | Medium. Must first check site histories and feature-only AUC; use spatial holdout and pre-placement registry correlation. |
| 4 | **Conductive-base structural gradient conditioned on gravity slope** — surface conductivity/depth-to-conductive-base and isostatic gravity anomaly/slope | Identify laterally persistent conductive-base boundaries corroborated by a gravity gradient, consistent with basin/fault-controlled alteration or basement offsets. It may expose unmapped buried structures where surface scarps are absent. | A coupled boundary/continuity test rather than a geothermal hotspot or generic multi-physics union. Mimics: lithology, basin fill, saline brines, alteration unrelated to faulting; substantial similarity risk to prior multi-domain fusion. | Low-to-medium; geological plausibility is real but spatial dependence and previous exploration reduce expected information gain. | Medium-high: scale/registration and confounding tests required; no added external data. |

**Top candidate to validate first (if/when prerequisites exist): Rank 1, strain-boundary orientation coherence.** This is a proposed next experiment, not a measured winner. It uses only feature families the official problem statement says are supplied, so it does not need new external data. The exact local band availability/names and provenance must be checked from the authenticated data package before implementation. Use at most three total experiments per run; do not proceed to a second candidate unless budget remains and the preregistered first candidate is completed.

## Holdout, uniqueness, and file gate status

| Gate | Required | This checkout |
|---|---|---|
| Canonical shared cached feature stack + visible-only feature construction | Available and inspected | **Missing; upstream evaluator/writer source copies exist only as pinned audit material, not a runnable integrated template** |
| Whole-segment buffered hide-and-recover, pooled DTI (0.2/0.8; 300 m triangular), evaluator version, n positives, 95% CI | Run for candidate and same-run baseline | **Not run; no authorized raster data or canonical evaluator integration** |
| Per-feature leakage canary; AUC > 0.90 investigated | Required | **Not run** |
| Candidate surface correlation and final-dot registry check | All relevant registry rasters; stop at >0.90 or >70% | **No candidate surface to test. Final-dot forensics on the nine historical winners ran: all 72 directed peer comparisons >70%; min 86.718954%. Full registry absent.** |
| Single-band GeoTIFF; float32; correct EPSG/shape/transform; no NaN inside footprint; values in [0,1]; exact saved-byte hash | Validate before download/submission | **Sample self-check passed. Historical-only format audit: 2/9 pinned files pass outside-footprint nodata check; 7/9 have zero-valued valid pixels outside footprint. No new candidate TIFF exists.** |
| Submission name/comment and weekly slot selector | Separate selector decision | **Not applicable; no candidate** |

## Irregularities and limitations to resolve

- **Repository gap:** the starting checkout contained only an initial README and `.git`. The merged current branch adds an offline review generator, schema gate, tests, pinned upstream metadata/pages and a static site; however, these are not an end-to-end model/training system. Several upstream evaluator/writer files are archived for audit only; there is no canonical cached feature stack, authorized competition raster package, full raster registry, or integrated holdout-to-TIFF pipeline.
- **Competition data access:** the official data URL redirects to DrivenData login in this environment. No login bypass or credential request is appropriate. Public USGS GeoDAWN data are useful source material, but do not replace the competition’s labels, sample submission, or packaged training stack.
- **Moving website claims:** GEMSDOE pages retrieved during this review show current 2026-10-26 content and sometimes conflicting or updated conclusions. Historical scores are not necessarily receipts; one page may contain multiple concurrent run cards and different evidence standards. Pin commit IDs, retrieve the linked exact files/JSON, and recompute comparisons before relying on them.
- **Uniqueness scope:** exact byte/hash difference is not enough. A dense sampling lattice or near-clone may violate the user’s literal overlap rule. The full registry must be frozen and each surface and final dots screened; absent that, say unknown/fail-closed.
- **Submission format nuance:** the official description asks for null/NaN outside bounds and float32 [0,1] inside. The user reports an organizer error “Predicted values must be in range [0, 1]”. Any future writer must test both the official nodata specification and the actual competition validator on the exact saved TIFF; do not silently replace outside nodata with zeros unless the official format or confirmed validator permits it.
- **Public leaderboard:** read from the official live page on 2026-10-26. The displayed 0.4437 is a point-in-time public score, not a forecast or a confirmed private/final score.

## Suggested next work

1. Populate `data/` using the competition’s authorized download and document the archive hashes, licenses, band names, CRS, masks, nodata, and footprint. Current official data page redirects to login.
2. Restore or build the shared template in this repository: cached feature stack, one canonical writer, one visible-only buffered whole-segment evaluator, per-feature canary, registry audit, and tests. Do not implement an alternate private evaluator.
3. Build a versioned, immutable registry for all nine sites (and all competition registry rasters required by the protocol), including exact TIFF hashes, source commit, arrays aligned to the sample grid, and receipts where available. Reconcile duplicate claims before describing any file as unique.
4. Pre-register the strain-boundary candidate, baselines, blocked folds, buffer, n withheld positives, bootstrap CI method, leakage gate, and stop criteria. Run no more than three experiments / two hours.
5. Generate a candidate TIFF only if a holdout win is established against a same-run baseline and all novelty/format gates pass. Then present the exact artifact and run card; otherwise report the negative result and preserve the slot.

## Sources checked

### Official competition / primary data

- [Problem description, data features, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — official page states the task is fault prediction; lists provided feature families; describes the distance-weighted Tversky parameters and GeoTIFF constraints.
- [Competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — fetched page redirected to [DrivenData login](https://www.drivendata.org/accounts/login/?next=/competitions/306/competition-doe-gems/data/). This verifies access restriction in this session, not inability of an authorized user to download.
- [Competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) · [about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Official live public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — retrieved 2026-10-26; top displayed public score 0.4437.
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [USGS DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) — USGS describes airborne magnetic/radiometric surveys and coordinated lidar; record lists CC0 1.0. This is free public source data, but no external data was downloaded or used in this review.
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) · [EPSG:32611](https://epsg.io/32611)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [GEMS prize PDF linked in prompt](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

### Site snapshots (owner-maintained project pages; not official competition records)

- [GEMSDOE24 review](https://buffedlizard55-lab.github.io/GEMSDOE24/)
- [GEMSDOE25 review](https://buffedlizard55-lab.github.io/GEMSDOE25/)
- [GEMSDOE27 review](https://buffedlizard55-lab.github.io/GEMSDOE27/)
- [GEMSDOE28 review](https://buffedlizard55-lab.github.io/GEMSDOE28/)
- [GEMSDOE30 review](https://buffedlizard55-lab.github.io/GEMSDOE30/)
- [GEMSDOE31 review](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)
- [GEMSDOE32 review](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
- [GEMSDOE33 review](https://buffedlizard55-lab.github.io/GEMSDOE33/)
- [GEMSDOE36 review](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

## Run card (final; no experiment performed)

```json
{
  "hypothesis": "Proposed, not tested: strain-boundary orientation coherence from dilatation, shear-strain rate, and strain-rate invariant",
  "mechanism": "Fault-localized strain gradients may trace uncatalogued structures; test line coherence and orientation, not only high strain magnitude",
  "named_non_fault_mimic": "Basin-margin strain, model interpolation seams, anthropogenic subsidence, or broad block boundaries",
  "holdout_dti": null,
  "holdout_dti_label": "NOT RUN: no data, cached stack, or shared evaluator in checkout; no estimate claimed",
  "withheld_positives": null,
  "95_percent_ci": null,
  "correlation_overlap_vs_registry": "NOT RUN: registry rasters absent; novelty not established",
  "raster_sha256": null,
  "validator_output": "NOT RUN: no output TIFF; CRS/shape/transform and [0,1]/NaN checks cannot be claimed",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```
