# KANLERGEMSDOE3 — GEMS Prize Challenge research & submission workbench

> **Mission / working brief (read before every project change):** Build an auditable, reproducible workflow for discovering unmapped surface faults relevant to geothermal exploration in the DOE GEMS Prize Challenge. Maximize the probability of a scientifically defensible result, own the outcome end-to-end, and make it easy to inspect evidence and download a valid prediction raster. Do not claim a leaderboard score from a proxy; do not copy a prior raster; do not spend a competition slot on an idea that has not beaten a spatially blocked holdout baseline. Every fact, score, uniqueness claim, and validation result must have a traceable source or be explicitly marked unknown. Continue to maintain a current, source-linked research feed and preserve negative results.
>
> **Non-negotiable workflow:** stay within the experiment lane documented in the experiment card; use shared cached feature data and the shared holdout evaluator/writer when available; hold out whole fault segments with a buffer; derive catalogue features only from visible faults; mask those visible faults pixel-exactly; use the organizer's metric definition (DTI α=0.2, β=0.8, triangular distance kernel with 300 m support); test each feature alone as a leakage canary; compare candidates to registry rasters before and after placement. A rank correlation >0.90 or >70% of candidate dots within 3 px of one registry raster is a duplicate/drift signal. Label numerical results **HOLDOUT-DTI** (include evaluator version, withheld-positive count, and 95% CI) or **ORGANIZER-CONFIRMED** (receipt). Projection is never a score. Stop at 3 experiments or 2 hours. A promotion/slot decision belongs to the separate selector, not this research workflow.
>
> **Submission gate:** one-band float32 GeoTIFF; EPSG:32611; same dimensions, geotransform and extent as organizer template; in-footprint predictions finite and in [0,1]; outside-footprint null/NaN as required by the official format. Download/submission readiness must be explicit. Never label a file “OK to submit” unless all checks pass. If source data, official template, registry rasters, or a valid holdout are missing, report the blocker—do not fabricate a TIFF, score, or uniqueness result.

## Executive summary

**Current status: NOT READY TO SUBMIT.** Initial review found only the README; this pass added a project landing page and a fail-closed GeoTIFF format validator, but there are still no competition rasters, cached feature stack, holdout evaluator, writer, prior-site rasters, or validation results in the checkout. Therefore no honest holdout estimate, duplicate test, or valid competition GeoTIFF can be produced here. The supplied site scores below are user-provided historical claims, not independently verified receipts. The best reported reference is GEMSDOE32 at 0.2778; the stated current leaderboard high is inconsistent across the prompt (0.4413 and 0.3195), and neither is verified here. Do not interpret these as a prediction of a new submission's score.

| Site | Reported highest submission (from request) | Reported score | File to download | Unique vs listed sites? | Status |
|---|---|---:|---|---|---|
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan | 0.2477 | Not available in this checkout | Unknown; raster comparison unavailable | User-reported only |
| GEMSDOE25 | dotted-h19-5-d2-8-20261002-e56ea318af89-nan | 0.2600 | Not available in this checkout | Unknown | User-reported only |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan | 0.2449 | Not available in this checkout | Unknown | User-reported only |
| GEMSDOE28 | h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan | 0.2710 | Not available in this checkout | Unknown | User-reported only |
| GEMSDOE30 | d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca | 0.2600 | Not available in this checkout | Unknown | User-reported only |
| GEMSDOE31 | h27-4-solo-d28-20261004-8acb75e1-nan | 0.2708 | Not available in this checkout | Unknown | User-reported only |
| GEMSDOE32 | h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros | **0.2778** | [Published TIFF on site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) (already submitted; do not resubmit) | Unknown; not compared here | Site labels score OWNER-REPORT, not receipt-confirmed; site currently says NO new file authorized |
| GEMSDOE33 | h33d-analog-tip-stepover-r30-20261004-cb490425926e | 0.2632 | Not available in this checkout | Unknown | User-reported only |
| GEMSDOE36 | anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros | 0.2750 | Not available in this checkout | Unknown | User-reported only |
| **New candidate** | None generated | **No estimate** | **No file** | **Not tested** | **DO NOT DOWNLOAD/SUBMIT** |

Historical score is not evidence that a new file exceeds it. “Unique” can only be concluded after testing the actual candidate against every relevant registry raster; different filenames or methods do not establish raster uniqueness. The public site list and entries supplied in the request should be treated as an investigation index, not ground truth.

### What the 0.2778 report does—and does not—tell us

The live GEMSDOE32 public page was fetched for review. It displays the 0.2778 artifact and explicitly labels the score **OWNER-REPORT**, stating that no submission-page receipt linking that raster hash to the score is present in that repository. It identifies the artifact as a 37,654-dot “h33-h33-2-b2” file, says it was already submitted, and says not to resubmit. Thus the value is not an organizer-confirmed receipt. The current page banner says no new file is authorized; its stated gates require fold-local HOLDOUT-DTI improvement with paired 95% CI above the same-evaluator champion, no off-catalogue regression, unique surface/final-dot placement, exact format validation, and separate slot approval. It describes this artifact as Champion for its local evaluator, but does not prove why the entry scored 0.2778 on the competition leaderboard. The hypothesis that its 37,654-dot budget and B=2 “h33-h33-2” strategy explain the score is not causally demonstrated by one result; controlled ablations would be required. The page presents later negative experiments and explicitly says current raster options should not be submitted. We did not download or independently rerun those rasters, so their holdout numbers remain reports on that site, not results produced by this checkout. A higher competition score cannot be promised. See [GEMSDOE32 live evidence page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html).

## Candidate research hypotheses (proposals, not tested)

The repository has no feature inventory, so “not previously implemented here” means only that no implementation exists in this checkout; it is not a claim about all GEMSDOE sites. The prior methods/names listed in the request make overlap risks particularly important. Rank is a prioritization hypothesis, not a projected score.

| Rank | Hypothesis | Layer(s) and target signature | Why it might find uncatalogued faults | Difference from methods named in request | Cost / principal risk |
|---:|---|---|---|---|---|
| 1 | Multi-scale directional curvature discontinuity | DEM-derived profile/plan curvature and directional second derivatives at 100–300 m scales; seek persistent paired curvature breaks | A fault may create a geomorphic/structural break extending beyond existing mapped traces; multi-scale persistence can suppress isolated noise | Distinct from simple scarp, ridge, Euler, dotted-fault, gap-closure, and Poisson-distance ideas named; verify stack to avoid overlap | Medium; lithologic contacts, drainage edges and artificial surfaces mimic curvature breaks |
| 2 | Magnetic analytic-signal edge concordance | GeoDawn magnetic channels; analytic-signal amplitude and directional gradient ridges across scale | Basement structures can produce linear magnetic boundaries not yet mapped at surface; score only independent, spatially coherent anomalies | Different physical measurement than terrain-only methods and named radiometric/scarp approaches | Medium-high; requires checking actual bands/metadata and careful leveling/flight-line artifact controls |
| 3 | Drainage-network deflection/offset | DEM-derived channel centerlines, local channel azimuth and knickpoint/deflection metrics | Young or subtle structures may deflect channels outside catalogue traces | Distinct geomorphic process rather than fault-distance smoothing or ridge-tip placement | High; drainage extraction and lithology/erosion confounding; DEM quality is essential |
| 4 | Radiometric boundary plus magnetic/terrain conditional interaction | GeoDawn K/Th/U (if present) with magnetic gradients and terrain curvature; seek coincident, independently supported boundaries | Alteration or lithologic contrast may reveal structural corridors beyond known faults | Not a simple single-layer radiometric or terrain ranking; explicitly tests cross-sensor interaction | Medium-high; verify channels and flight/processing metadata; geology contacts can dominate |
| 5 | DEM-derived lineament intersection/termination network | Multi-scale slope/aspect lineaments; detect persistent intersections, terminations and aligned stepovers | Structural intersections may host permeability and unmapped fault segments | Topological network statistic rather than the named tip-stepover-only and Euler approaches | Medium; many false edges, and substantial overlap with prior “tip/stepover” families is likely |

**Top candidate for a first test:** #1, only if the cached DEM stack is present and the blocked holdout evaluator is available. No candidate is currently validated; none is approved for a submission slot. Feature-alone AUC >0.90 is a leakage alarm until independently explained. For every candidate, use buffered whole-segment holdouts, pixel-exact visible-fault masking, pooled DTI and a bootstrap CI over held-out segments. Include negative controls and compare with a simple baseline. Registry-raster correlation/overlap is a hard lane check before and after point placement.

### External data / sources to verify before use

Do not assume external-data access based on a URL. The official GeoDawn/USGS and GBC-INGENIOUS resources below are starting points for source and metadata review. The competition-provided features and DEM are preferable for the first controlled tests; external downloads require provenance, license, coordinate/resolution compatibility, and availability checks. A proposed layer that cannot be obtained and validated is not viable. No external layer was downloaded in this checkout.

## Getting to a valid submission

1. On an authorized environment, obtain the competition-provided feature stack, labels, and example/sample submission from the DrivenData data tab (login required, per the project notes). Keep raw data out of Git; place files under the repository's configured `data/` convention only after checking the download script and licenses.
2. Inspect the repository and retain one shared feature cache, evaluator, and submission writer. This checkout currently has none. Implement or restore them before claiming the protocol is operational; do not create a private fork of shared tooling.
3. Run the official-format validator against the sample/template and candidate. Record exact CRS, shape, transform, nodata/footprint, dtype, value range and NaN counts. A TIFF failing any check is not downloadable as a competition submission.
4. Run feature-alone leakage canaries and blocked holdouts; record evaluator version, withheld positives, fold/segment definitions, DTI and 95% CI. Compare each surface and final dots to all available registry rasters; keep duplicate diagnostics.
5. Only if a candidate beats the current holdout best under the same evaluation, passes uniqueness and file-format checks, and is clearly identified, mark it **OK TO DOWNLOAD**. Submission slot selection remains a separate user/selector action.
6. Archive source URLs, retrieval time, checksums, code revision, parameters, logs, validation JSON, raster SHA-256, and negative results. Never place private labels or credentials in Git.

## Official / primary references

| Topic | Source | What this repo uses it for |
|---|---|---|
| Competition problem, metric and submission format | [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Primary reference to confirm the 0–1 predictions, raster format, CRS/resolution and distance-weighted metric; login/access may be required for some pages |
| Rules and competition | [DrivenData competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/) | Rules and deadlines; verify live before any entry |
| About/resources | [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) | Challenge context |
| Competition data | [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Competition raster/template; authenticated access required according to project notes |
| Reference implementation | [DrivenData GEMS prize reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Public code reference; not itself a score guarantee |
| GeoDawn survey | [USGS GeoDawn data record](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Official survey context and metadata, subject to availability |
| INGENIOUS | [GBC-INGENIOUS current projects](https://gbcge.org/current-projects/ingenious/) | Project context; verify data access and terms before using layers |
| CRS definition | [EPSG:32611](https://epsg.io/32611) | CRS identifier reference; organizer template remains authoritative for exact grid |
| Prize challenge document | [NLR PDF, 96647](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Program requirements; verify the current revision |

## Limitations and required follow-up

- This repository is an empty scaffold: no scripts, tests, data, cached stack, validation tool, experiment history, or submission raster. The prompt's stated download/prepare pipeline cannot be confirmed to exist here.
- No DrivenData credentials or private labels/receipt are present. I cannot download authenticated competition files, read the private holdout, submit a file, inspect a receipt, or confirm an organizer score.
- No listed GEMSDOE site raster was retrieved or locally compared. Historical names/scores are reproduced from the request only; current pages and the inconsistent leaderboard figures require verification.
- A valid submission TIFF cannot be responsibly generated without the official template and required prediction inputs. Generating a zero/placeholder raster would risk another invalid or misleading submission.
- GPU is not the current blocker: no training pipeline or data exists in this checkout. Data/template/tooling access is the immediate blocker.

## Experiment card (current negative result)

```json
{
  "hypothesis": "No candidate tested; top research proposal is multi-scale DEM curvature discontinuity.",
  "mechanism": "Persistent directional curvature breaks may mark geomorphic expressions of faults not present in the visible catalogue; untested.",
  "named_non_fault_mimic": "Lithologic contacts, drainage edges, and anthropogenic terrain breaks.",
  "holdout_dti": null,
  "holdout_dti_label": "NOT RUN: evaluator, data and holdout unavailable; no estimate is reported",
  "confidence_interval_95": null,
  "withheld_positive_count": null,
  "evaluator_version": null,
  "correlation_overlap_vs_registry": "NOT TESTED: registry rasters unavailable",
  "raster_sha256": null,
  "validator_output": "NOT RUN: no candidate or official template; NaN/range/CRS/shape/transform not verified",
  "submission_name": null,
  "submission_note": "No candidate generated; not approved for download or submission.",
  "verdict": "negative"
}
```

**Next-session priority:** restore or add the shared, tested data-ingestion/feature-cache/blocked-holdout/writer pipeline; obtain the organizer template and permitted training assets; then run at most three pre-registered experiments with reproducible cards. Do not open a weekly submission slot until the candidate beats the holdout incumbent and passes all independent format and uniqueness gates.
