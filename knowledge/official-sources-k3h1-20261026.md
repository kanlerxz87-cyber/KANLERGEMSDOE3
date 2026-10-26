# Verified official facts — fetched 26 Oct 2026 (K3-H1 session)

Every line below was read from the linked page during this session. Participant (GEMSDOE*) material is *not* included here; it lives in `research/k3h1-report.md` with SHA pins.

## Rules — [GEMS Prize Official Rules, NLR, September 2026](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

- $300,000 total prize pool. Phase 1: $50,000, split equally among the top five on the **private** test set. Phase 2: $250,000 (100k/70k/40k/25k/15k), rescored against the **full, revised new-fault dataset** that experts update *using submitted predictions* (§1, §1.1).
- Submission: **a single GeoTIFF**, one raster layer at **100 m**, covering the entire GeoDAWN study area, in the format on the competition website (§3.2).
- **Three submissions per week** (§3.2, §3.4).
- **One final submission** must be selected for evaluation across **both** prize rounds, without knowledge of private scores (§3.4–§3.6.2). Public leaderboard scores may differ from final private scores (§3.2).
- Metric: distance-weighted Tversky index, which penalises false negatives more than false positives (§3.6.1).
- Labels: the USGS Quaternary Fault and Fold Database plus a set of **newly identified faults labelled by geology experts at NLR and USGS**. Training labels come from the INGENIOUS Great Basin Regional Dataset Compilation (§2, §3.3).
- Features: GeoDAWN high-resolution lidar, magnetic and radiometric data, plus a USGS DEM at 1 m (§2, §3.3).
- Generative-AI use is allowed but **must be disclosed in the narrative**; competitors remain responsible for accuracy and authorship (§3.2).
- Finalists must deliver **complete code and documentation** that reproduce the winning results and run on new data (§3.2, §3.5).
- Deadline: 5:00 p.m. ET on the submission deadline date (App. A.1). See gems.drivendata.org for current dates (§1.2).

## Task and metric — [problem description (page 967)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

- With p(x) the prediction at pixel x, k(d) = max(1 − d/300 m, 0) the triangular kernel, and g a truth pixel:
  - TP_w = Σ_g max_x p(x)·k(d);
  - FP_w = Σ_x p(x)·[1 − max_g k(d)];
  - FN_w = Σ_g [1 − max_x p(x)·k(d)];
  - α = 0.2, β = 0.8.
- Worked example: TP 3.00, FP 1.89, FN 2.00 → 0.60 (tested in `tests/test_metric_and_format.py`).
- Format: EPSG:32611, 100 m, same bounds as the sample, a single float32 band with values in [0, 1], and null/NaN outside the bounds.

## Context — [About (page 968)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)

- GeoDAWN (USGS + DOE, under EarthMRI) acquired high-resolution airborne magnetic and radiometric data over northern/western Nevada and eastern California (Walker Lane, western Great Basin). It was coordinated with USGS 3DEP airborne lidar.
- "Geothermal resources are often found in regions with active or recent faulting, where fractures in the Earth's crust provide pathways for hot fluids to reach the surface." Most GeoDAWN-region faults are subtle, and many are hidden below the surface.

## Organizer clarifications ([DrivenData community forum](https://community.drivendata.org/), staff answers)

- [11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4): known-fault pixels are masked **pixel-exactly**, identical to the training labels, with no buffer. Predictions near known faults but far from new truth are fully penalised, and new truth can lie within 300 m of known faults. The same applies in Phase 2.
- 11550: the public leaderboard is **one pooled index** over all public-subset pixels; the chunking is undisclosed. The final round uses the whole GeoDAWN area.
- 11556: Phase-2 labels may be added, removed or changed; the same exclusion mask and metric apply, with no extra weighting.
- 11536: a "new fault" is any fault pixel not captured by USGS/INGENIOUS, including new geometry of existing systems.
- 11527: organizers will not disclose test-fault data sources, types or coverage.

## Data sources (free, official)

- [INGENIOUS Great Basin Regional Dataset Compilation, GDR 1391](https://gdr.openei.org/submissions/1391), DOI [10.15121/1881483](https://doi.org/10.15121/1881483), **CC-BY-4.0**. Contents: 2 m temperature probes, earthquake density, MT conductance (USGS [10.5066/P9TWT2LU](https://doi.org/10.5066/P9TWT2LU)), elevation trend/detrended elevation ([10.5066/P9MQRCBY](https://doi.org/10.5066/P9MQRCBY)), geodetic shear and dilation models, gravity/magnetics ([10.5066/P9Z6SA1Z](https://doi.org/10.5066/P9Z6SA1Z)), heat flow ([10.5066/P9BZPVUC](https://doi.org/10.5066/P9BZPVUC)), paleo-geothermal features (sinter/tufa), Quaternary fault slip/dilation tendency ([10.5066/P9YL58W6](https://doi.org/10.5066/P9YL58W6)), Quaternary faults v1/v2 (v2 supersedes v1; 2023-06-27), Quaternary volcanics, study-area boundary, and well/spring temperature and chemistry.
- [INGENIOUS project (GBCGE, UNR)](https://gbcge.org/current-projects/ingenious/): DOE GTO award DE-EE0009254, 1 Feb 2021 – 30 Jun 2025, $10M. It builds on geothermal play-fairway efforts in central Nevada, NE California/NW Nevada and western Utah, with the goal of discovering **hidden (blind)** geothermal systems. Collaborators include USGS, NREL and LBNL.
- [USGS GeoDAWN data release, DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ): airborne magnetic and radiometric surveys (Glen & Earney, 2024), cited by the Official Rules.
- [Reference solution (DrivenData)](https://github.com/drivendataorg/gems-prize-reference-solution): U-Net with Monte-Carlo cross-validation; supports CPU.

## Implications used by this lane (inferences, labelled as such)

- The scored truth is *new* faults (the known ones are masked). Pixels adjacent to mapped faults therefore carry little truth: the live-ledger inversion fits 1.2% of the far-field density at 1–2 px, peaking at 5–10 px (1.10×).
- Phase 2 relabels using submitted predictions, so a selected file should be geologically plausible rather than tuned to the public chunk.
- External data must carry a suitable licence. INGENIOUS is CC-BY-4.0 (GDR 1391, read this session). GeoDAWN is listed as CC0 1.0 on its USGS release page (read by the previous session; see `docs/SOURCES.md`). The 1 m lidar scarp product is derived from USGS 3DEP elevation data according to its GEMSDOE24 metadata; the 3DEP licence page was not re-read this session.
