# Source register and verification limits

Checked on 2026-10-26 UTC. Official claims below were fetched during this session unless explicitly marked otherwise. The GEMSDOE websites are participant-maintained research pages, not organizer score receipts.

| Source | Authority / verified use | Limit |
|---|---|---|
| [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Official task states target is fault mapping, describes provided layer families and new expert-identified faults, defines distance-weighted Tversky with α=0.2, β=0.8 and 300 m triangular support, and specifies submission GeoTIFF schema. Page fetched on 2026-10-26. | Does not authenticate site-owner scores or verify files in this checkout. |
| [DrivenData About page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) | Official context about DOE/USGS GeoDAWN, INGENIOUS and the geological fault task. Fetched 2026-10-26. | Scientific context is not evidence that a prediction indicates a geothermal vent. |
| [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Official data URL fetched 2026-10-26; it redirected to the DrivenData login page. | No credentials used; no official competition file downloaded. This is a verified access blocker for this environment. |
| [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Official organization repository page/README fetched. README says competition data must be downloaded separately and supports CPU-only as well as GPU environments. | Not the missing integrated template/cache for this checkout. Archived copies under `evidence/upstream/` are review evidence, not a runnable pipeline. |
| [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) | Official page fetched. It describes magnetic and radiometric survey deliverables, including grids/GeoTIFFs, and lists CC0 1.0. | Individual raster download, coverage, resolution, processing, and compatibility with the competition grid were not checked. |
| [EPSG:32611](https://epsg.io/32611) | Fetched CRS record identifies WGS 84 / UTM zone 11N with metre units. | The actual competition sample's grid dimensions and affine transform must be read from the sample file. |
| [GBC INGENIOUS](https://gbcge.org/current-projects/ingenious/) | Research lead supplied by the user. | Not fetched in this review; per-layer license/coverage not verified. |
| [GDR submission 1391](https://gdr.openei.org/submissions/1391) | Research lead supplied by the user. | Not fetched in this review. |
| [Competition report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Link supplied by the user. | Not retrieved; no claim is attributed to unread text. |
| [Competition leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Official leaderboard link. | Not checked in this review; current value is unknown. The user-provided 0.4413/0.3195 and historical site figures remain unverified. |
| [Nine focus-site Pages](SITE_REVIEW.md) | Source locations for the supplied historical list and mutable participant research updates. | Not organizer receipts. Exact TIF bytes were not retrieved into this checkout; score-to-hash binding and literal all-registry uniqueness were not independently re-run. |

## Format and metric, as stated by DrivenData

The official problem page describes one float32 prediction band in EPSG:32611 at 100 m, matching sample-grid bounds, values between 0 and 1, and null/NaN outside the bounds. The metric is distance-weighted Tversky: α=.2, β=.8, triangular kernel with 300 m support. A portal range error must be debugged against the **saved output** and the official sample/validator. Participant pages disagree on zero-outside versus null/NaN-outside practice; follow the official sample/schema and never claim a local check guarantees portal acceptance.

## Provenance boundaries

The immutable site snapshots and `evidence/snapshot_hashes.json` support reproducible text/tree review. They are owner-authored evidence. `registry/data_manifest.json` files in those snapshots describe owner-supplied input mirrors and themselves warn that hash pins establish mirror consistency, not organizer authentication. No actual input rasters, peer-submission TIFFs, or official receipt images were opened here. `HOLDOUT-DTI`, `ORGANIZER-CONFIRMED`, owner-reported claim, and any projection must remain separate labels.
