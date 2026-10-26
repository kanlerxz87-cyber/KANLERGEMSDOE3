# Evidence and sources

| Source | Verified relevance | Limit / use |
|---|---|---|
| [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Fault mapping task, input bands, DTI, EPSG:32611, 100 m and GeoTIFF requirements. | Does not reveal private test truth. |
| [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Public team results. | No mapping to the nine named file hashes; changes over time. |
| [DrivenData rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) and [NLR prize rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Official rules, eligibility and data use. | Full PDF was not downloaded in this sandbox. |
| [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Official baseline and CPU/GPU setup; it requests the competition data. | Not a guarantee of competitive performance. |
| [Organizer known-fault mask clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) | Known fault pixels are masked; nearby pixels can still count. | Not evidence of any historical file's score. |
| [Organizer pooled-aggregation clarification](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550) | Public and private indices pool over their subsets. | Does not disclose subset geometry. |
| [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Magnetic/radiometric survey and acquisition details; record marked CC0. | Public catalog checked; no official binary downloaded here. |
| [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) | DEM and lidar products free without use restrictions. | Area-of-interest coverage still must be verified per product. |
| [GDR INGENIOUS compilation](https://gdr.openei.org/submissions/1391) | Lists faults, wells, springs, thermal probes and other datasets; page states CC BY 4.0. | Verify individual files, coverage, attribution and license before use. |
| [Shared gems57 template](https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d/src/gems57) | Evaluator, writer and literal uniqueness implementation used unchanged. | Community code, not official organizer code. |
| [GEMSDOE32 audit manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/submissions_manifest.json) | Named anchor has `receipt: null`. | Absence of a receipt does not prove no score exists. |
| [17GEMSDOE dense registry raster](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/main/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif) and [57GEMSDOE preflight](https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/preflight_anatomy.json) | Public indexed registry witness, independently hash/grid checked here. | A witness proves a stop, not full-registry completeness. |

All competition rasters in this run came from third-party GitHub mirrors, not a
fresh authenticated DrivenData download. Their SHA-256 values verify transport
identity only. The mirrored sample contains positive labels matching the known
fault raster, while the official task page describes an absence-only example;
this discrepancy blocks a claim that the sample bytes are official. The private
competition labels, user-specific submission receipt, authenticated data tab
and remaining weekly slots were not accessible. No source establishes the cause
of the user's prior range error. Sentinel values or unhandled NaNs are plausible
failure modes, but the failed file must be inspected to identify its cause.

## Claim conflicts found in peer records

The pinned [GEMSDOE32 portfolio](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/07806249f4ed3efe70b4fbf866183c32392b7853/docs/index.html)
repeats all nine user-provided values as owner reports, without associating
organizer receipts. The [GEMSDOE31 irregularity register](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/776bf4668a8c10631908c9bba9443a8f11ce5036/registry/irregularities.json)
records unresolved `0.2600` D2.8 and `0.2708` H27-4 attribution conflicts; it
does not prove that differently named TIFFs or all claims are identical. The
[GEMSDOE28 irregularity register](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/2c839d10f57ec9b074829e93c84bc39935f52896/registry/irregularities.json)
records an initial H36-1 note as unscored and not slot-approved. These are
community claims and historical statuses, not official adjudications. See
[claim audit](claims_audit.md) for the nine-site trace.
