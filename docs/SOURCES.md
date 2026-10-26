# Sources, data rights and provenance — current review

Checked 2026-10-26. Links are for direct manual review. Public owner-site claims are not organizer
receipts and no authenticated DrivenData data were obtained.

| Source | What it establishes | Caveat |
|---|---|---|
| [GEMS problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Fault-mapping task, 100 m EPSG:32611 template, distance-weighted Tversky α=.2, β=.8, 300 m triangle, single float32 prediction and format rules. | Hidden labels are not available; confirm the latest format and rules before submission. |
| [GEMS overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) and [prize rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Scientific context, eligible data sharing and reproducibility requirements. | Fault evidence does not prove a geothermal resource; eligibility/account details are separate. |
| [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Public leader 0.4437 observed on 2026-10-26, with no exact observation time or response hash retained. | Dated observation, not live, not a receipt linking a file to a score. |
| [DrivenData terms](https://www.drivendata.org/termsofuse/) | Terms prohibit automatic access/monitoring of their website. | This project never runs a scheduled DrivenData scraper. |
| [Official reference code](https://github.com/drivendataorg/gems-prize-reference-solution) | Official baseline implementation and installation guidance. | Not the shared participant template used for this experiment. |
| [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), Glen and Earney (2024), DOI 10.5066/P93LGLVQ | Official magnetic/radiometric source, with CC0 1.0 designation and public data/metadata links. | We used a derived **owner cache**, not a newly acquired/verified official GeoTIFF. CC0 source rights do not automatically document rights/provenance of a derivative. |
| [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) and [LidarExplorer](https://www.usgs.gov/tools/lidarexplorer) | USGS states 3DEP products are free and without use restrictions; provides LiDAR/DEM search. | Specific source tiles, coverage and processing behind the owner cache were not reproduced. Follow USGS attribution requests and verify cache rights separately. |
| [USGS fault-scarp example](https://www.usgs.gov/media/images/emigrant-fault-scarp-lidarjpg) and [map showing non-fault scarps](https://pubs.usgs.gov/sim/2007/2961/pdf/SIM2961_508.pdf) | LiDAR can reveal scarps; anthropogenic/erosional features can mimic them. | Neither proves this regional K/Th texture hypothesis or geothermal productivity. |
| [Known-fault masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) and [fault continuations](https://community.drivendata.org/t/where-do-you-draw-the-line/11536) | Organizer forum describes masking exact known-fault pixels and allowing new continuations/splays. | A near-catalogue blanket exclusion can eliminate legitimate new faults. |
| [Owner historical nine-site summary](https://buffedlizard55-lab.github.io/GEMSDOE24/docs/portfolio-executive-summary.md) | Source of historical file associations and score claims. | Scores are unverified owner reports; exact file comparisons are in our local audit. |
| [Cached LiDAR strike code](https://github.com/buffedlizard55-lab/7GEMSDOE/blob/2e7bf080270493f77286fd62f2db958805053ba5/scripts/dem_merge.py#L88-L99) | Strike encoding used for the locked owner-cache features. | GitHub repositories checked have no recognized code license; do not assume permission to redistribute. |

`data/input-manifest.json`, `research/template-lock.json`, and `research/registry-lock.json` pin
third-party mirrors by SHA-256 or Git blob. The checks prove byte identity against those pins only.
The organizer's authenticated data page was not accessed, and hashes cannot certify its originals.
