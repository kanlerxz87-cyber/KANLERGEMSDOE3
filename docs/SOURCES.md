# Source register and verification limits

Access checked on 2026-10-26 UTC. Official claims below were checked against the linked pages; their applicability is limited to the statements described. The nine project-site values are user-provided claims, not official sources.

| Source | Authority | Verified use here | Scope/limit |
|---|---|---|---|
| [DrivenData GEMS problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Competition organizer | Challenge target is fault presence; existing USGS/INGENIOUS fault ground truth is incomplete; challenge describes newly identified faults; supplied features include strain, gravity, magnetic, conductivity/depth, elevation, and earthquake-density layers; metric and submission contract. | The page is a description, not a score receipt or this checkout's actual data. |
| [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Competition organizer GitHub organization | Repository exists and README instructs users to download competition data and use the reference workflow. | Does not provide this checkout's shared cached stack, holdout tool, or a score for any site artifact. |
| [Official USGS GeoDAWN dataset](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | USGS | Identified by the competition page as GeoDAWN survey context/source. | No external raster downloaded or processed in this review. |
| [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) | Great Basin Center for Geothermal Energy | Identified by the official problem page as a source for challenge data/labels. | This review does not validate site score claims or independently download project datasets. |
| [EPSG:32611](https://epsg.io/32611) | EPSG registry mirror | Link for the UTM zone 11N CRS named in the organizer format requirements. | The competition's own format description is authoritative for this task. |
| [GEMSDOE30 nine-site review page](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE30/main/review-2026-10-26.html) | Participant repository, not organizer | Read-only cross-repository review text reports the nine values as owner-reported/unverified and describes a proposed H33 pruning lineage; it cautions that this is not hidden-label causal proof. | Participant-authored claims, not independently reproduced here; this repo contains no TIFF bytes or audit scripts. Useful as a source for diligence, not proof. |
| [GEMSDOE30 receipt-integrity review](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE30/main/receipt-integrity-review.html) | Participant repository, not organizer | Page explicitly distinguishes format validation from approval and says its audit lacks an official current leaderboard/receipt. | It concerns a different audit/artifact and must not be conflated with a verified audit of the nine historical files. |
| [Owner's nine site pages](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) (see [all nine site links](SITE_REVIEW.md)) | Participant repositories/sites | Locations from which to retrieve owner records. | Not an organizer receipt. This review does not call the reported numbers confirmed. |
| [User-provided run histories and leaderboard figures](SITE_REVIEW.md) | User prompt | Used to prioritize the sites and transcribe historical claim labels/filenames. | Unverified and internally conflicting. No score estimates are derived. |

## Official metric and format details checked

The official problem page describes a pixel-wise fault-confidence GeoTIFF, projected UTM zone 11N (EPSG:32611), 100 m resolution, same bounds as the training grid, a single float32 layer with predictions in [0,1], and null/NaN outside bounds. It defines a distance-weighted Tversky metric using a triangular kernel with 300 m support and α=0.2, β=0.8. See the [metric section](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) and [submission format section](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format).

## Blocked checks

- No login credentials or authorized competition-data download were available in this blank checkout; no login wall was bypassed.
- The live leaderboard and account-specific submission page/quota were not queried or verified for this review.
- The exact raster artifacts and registry files for all nine sites were not retrieved into this checkout; hence no byte checks, correlation, overlap, or SHA evidence is claimed.
- No current leaderboard score is inferred from old participant pages, user-entered lists, or repository text.
