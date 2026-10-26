# Evidence and source register

Research checked for this review on 2026-10-26. Statements are scoped to what each source actually says. The evolving GEMSDOE GitHub Pages are independent owner-maintained evidence pages, not competition organizers; their numbers are not treated as organizer-confirmed unless a submission receipt is present and checked.

## Official sources

| Source | Verified statement used here | Does not establish |
|---|---|---|
| [DrivenData — Problem description, task and features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | The task is fault mapping indicative of geothermal resources; test labels include expert-identified faults absent from current public USGS data; provided inputs include conductivity, elevation, strain, gravity, magnetic, source-depth, and earthquake-density layers; DEM links are provided. | The contents of this checkout, access to private competition files, or that a specific owner-submitted TIFF earned a particular leaderboard score. |
| [DrivenData — Performance metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | DTI uses α=.2, β=.8 and a 300 m triangular kernel; submission is a single-band float32 GeoTIFF, EPSG:32611, 100 m, same bounds/grid, values in [0,1], null/NaN outside. | Why an individual portal upload failed, or whether the portal accepts a particular file. The precise sample template still must be checked. |
| [DrivenData — About/data](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) | USGS/DOE GeoDAWN airborne magnetic/radiometric data and lidar context; links to USGS and INGENIOUS; describes task interpretation and fault mapping context. | A causal explanation for the reported 0.2778 score. |
| [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) | The official USGS page describes survey data products including magnetic/radiometric grids and GeoTIFFs; lists CC0 1.0. Supports candidate 5’s official source/rights lead. | Actual successful download in this session, a particular raster's spatial compatibility, or inclusion of radiometric bands in the DrivenData training stack. |
| [EPSG registry page — EPSG:32611](https://epsg.io/32611) | EPSG:32611 is WGS 84 / UTM zone 11N with metre units. | The specific template transform/shape/bounds, which must be read from official data. |
| [DrivenData reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) | The official reference repository README says to obtain challenge data from the competition website and place it in `data/`; describes its reference notebook and environment. | Any scripts, cached stack, or evaluator in this project checkout; those are absent. |
| [GBC Geothermal INGENIOUS project](https://gbcge.org/current-projects/ingenious/) | Official project context supplied by the requester. | The current availability/license/coverage of any particular layer without checking that layer’s own record. |
| [DrivenData competition data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | The competition is the source of official training/test/sample files. The official data-tab URL redirected to DrivenData’s login page when fetched during this review; the page is access-controlled. | That this workspace can access or has downloaded those files. No credentials or bypass were used. |

## Peer-site material inspected (nonofficial, mutable)

These pages were opened to compare their *published claims* with the supplied historical list. They are not authoritative competition receipts, and this checkout did not download or hash their TIFFs. Some pages explicitly distinguish research artifacts from slot-approved submissions; others have inconsistent or differing evaluator/registry scope. Treat every number from them as site-owner evidence until its exact receipt and raster hash are independently linked.

- [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/)
- [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/)
- [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/)
- [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/)
- [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/)
- [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)
- [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
- [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/)
- [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

## Evidence labels used in this repository

- **HOLDOUT-DTI** — local evaluator result on a named frozen spatial holdout; always give evaluator version, withheld-positive count, and 95% CI.
- **ORGANIZER-CONFIRMED** — copied from an official submission-page receipt and bound to a file hash.
- **OWNER-REPORTED / UNVERIFIED** — number copied from a user/site-owner-provided list or mutable peer page without verifying the corresponding official receipt and raster bytes.
- **PROJECTION** — prediction about a future organizer score; never report it as an achieved score.
- **Not estimable** — calibration is unsupported; not zero and not a negative result.
- **Blocked** — required data/tools were not present; no experiment/score was run.
