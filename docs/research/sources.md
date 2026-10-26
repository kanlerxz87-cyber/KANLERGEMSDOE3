# Verified sources (checked 2026-10-26, line by line)

Every external claim in this repo traces to one of these. Anything not listed
here and not measured in `evidence/` is labelled inference.

| # | Source | URL | What it verifies | Status |
|---|---|---|---|---|
| S1 | DrivenData GEMS problem description (page 967) | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | Task (faults indicative of geothermal resources); hidden test = expert-identified faults **not** in the USGS database; features at EPSG:32611, 100 m; labels from USGS Quaternary faults + INGENIOUS; distance-weighted Tversky metric (alpha/beta, 300 m) | Fetched 2026-10-26 |
| S2 | DrivenData leaderboard | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ | Public best at fetch time: **0.4437 (xiaofanhu)** — the prompt's "0.4413" and "0.3195" are both stale (IR-01) | Fetched 2026-10-26; dynamic page, re-check before acting |
| S3 | GEMS Prize official rules (NLR 96647) | https://docs.nlr.gov/docs/fy26osti/96647.pdf | Prize structure, submission and scoring rules; initial round scored on a private expert set, final round rescored on an expert-expanded label set | Fetched 2026-10-26 |
| S4 | Reference solution (DrivenData) | https://github.com/drivendataorg/gems-prize-reference-solution | Organizer-endorsed baseline approach (U-Net MC-CV notebook); data must be placed in `data/` after login download | Fetched 2026-10-26 |
| S5 | USGS GeoDAWN data release | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI https://doi.org/10.5066/P93LGLVQ, CC0) | Origin/coverage/processing of the magnetic + radiometric surveys; lidar collected via USGS 3DEP over a similar extent | Fetched 2026-10-26 |
| S6 | INGENIOUS project (GBCGE) | https://gbcge.org/current-projects/ingenious/ | INGENIOUS label provenance named on page 967 | Named by S1; not independently re-fetched this session |
| S7 | EPSG:32611 | https://epsg.io/32611 | WGS 84 / UTM zone 11N, metres, central meridian −117° — matches the raster CRS/transform measured in `data/prepared_manifest.json` | Fetched 2026-10-26 |
| S8 | Tversky index (reference) | https://en.wikipedia.org/wiki/Tversky_index | Metric family definition; the authoritative alpha=0.2/beta=0.8/300 m form is S1 + `src/gems/metric.py` (organizer worked example passes in tests) | Secondary reference only |
| S9 | GDR OpenEI submission 1391 (geothermal data) | https://gdr.openei.org/submissions/1391 | Source of the well/spring geothermal tables mirrored in GEMSDOE24's external bundle (provenance in `registry/data_manifest.json`) | Named in prompt; files used here arrive via the pinned mirror, not a fresh GDR download |
| S10 | Focus-site pages (owner-reported scores) | https://buffedlizard55-lab.github.io/GEMSDOE24/ · /GEMSDOE25/ · /GEMSDOE27/ · /GEMSDOE28/ · /GEMSDOE30/ · /GEMSDOE31/docs/ · /GEMSDOE32/docs/index.html · /GEMSDOE33/ · /GEMSDOE36/docs/ | Historical submission names + OWNER-REPORTED scores in the executive table. No score-to-receipt linkage is published, so none is ORGANIZER-CONFIRMED | GEMSDOE24/32/36 fetched in full 2026-10-26; other scores as listed in the owner brief and cross-checked against `registry/scored_registry.json` hashes in GEMSDOE36 |

## Data-access limitation (verified, not assumed)

DrivenData data download requires login; this sandbox has no DrivenData auth.
Competition rasters were therefore restored from the owner's GitHub mirrors
with SHA-256 pins (`registry/data_manifest.json`, `scripts/restore_data.py`):
integrity-verified byte copies, **not organizer-authenticated**. Hashes match
the pins recorded independently in GEMSDOE36 (`data/prepared_manifest.json`):
training_features `4371c82e…`, labels `7ba308cc…`, sample_submission `2176d08e…`.

## Official source that would be needed for hypothesis #5 (not run)

USGS 3DEP 1 m DEM tiles listed in the competition's `1m_DEM_links.csv`
(DrivenData data tab, login required) — obtainable free from USGS 3DEP, but
not inside this sandbox's network allowlist; named as the blocker, per protocol.
