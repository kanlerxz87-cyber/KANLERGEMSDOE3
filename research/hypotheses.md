# Ranked geological hypotheses — preregistration, not discoveries

**Status:** research proposals only; none implemented or evaluated. Ranking is qualitative expected
information gain and possible HOLDOUT-DTI upside, **not a numerical prediction**. The request refers to
a single-method paragraph but does not identify one. A shortlist is not an assigned lane. The literal
registry witness described in the [review](review.md) blocks **every nonempty candidate** before
placement, so no model experiment, output TIFF or slot selection was performed.

| Rank | Layers and proposed physical signature | Missing-fault rationale; non-fault mimic | Difference, expected upside and approximate cost |
|---|---|---|---|
| **1** | **Cross-line radiometric texture displacement**: use independent magnetic RTP/gradient axes, then correlate windows of K, Th and U texture on opposite sides of each axis to infer coherent along-strike offsets and their uncertainty; condition on detrended relief. | A fault concealed beneath cover can displace a continuous geochemical pattern even if its trace is not mapped. Alluvial-fan/lithologic boundaries, alteration unrelated to faulting, airborne seams and terrain clearance can create similar breaks. | Unlike a pointwise magnetic+radiometric edge or simple ratio fusion, score a **paired displacement** of textures, never distance to known traces. This distinction is conceptual, not a proven literature-wide invention. Highest qualitative expected benefit/information among this shortlist; moderate CPU/memory cost. |
| 2 | **Cross-scale magnetic-pattern offset coherence**: compare magnetic RTP, TMI and gradients across multiple smoothing scales; test whether opposite-side patterns have a consistent lateral shift along a line, rather than simply selecting gradient peaks. | A buried fault can offset magnetic stratigraphy; intrusive contacts, remanent magnetization and flight-line noise also generate lineaments. | Cross-line *matched offset* rather than magnetic-worm magnitude or a named Euler derivative. High-to-medium expected information; medium CPU cost. Might correlate with hypothesis 1; full-registry comparison remains essential. |
| 3 | **Repeated relief/lineament termination pairs**: pair changes in detrended elevation/slope and owner-mirrored LiDAR scarp features across an independently oriented geophysical line. Seek a repeated, consistent termination pattern, not proximity to a mapped fault. | Concealed faulting can juxtapose or terminate buried/eroded geomorphic signatures. Drainage capture, erosion, fan boundaries and roads are non-fault alternatives. | Pairwise termination and coherence differs from raw scarp or knickpoint scores, but sibling implementation overlap must be checked. Medium expected information; moderate-to-high cost. Missing LiDAR coverage must be recorded, not imputed as geology. |
| 4 | **Terrain-adjusted shallow-temperature asymmetry**: relate independently modeled topographic/cover context and GDR 2 m probe temperatures across candidate geophysical lineaments, with geographic and seasonal uncertainty. | A permeable fault can focus warm fluid away from mapped traces; groundwater transport, season, weather, land use and measurement campaigns can mimic it. It is **not** proof of a vent or of geothermal resource. | Test local cross-line contrast, not nearest-hot-spring distance or a renamed PINN. Lower confidence due to sparse biased sampling and overlap with geothermal-conduit work; high feature-engineering cost. |

## Availability and limitations

- USGS [GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
  lists magnetic and radiometric data under CC0 1.0; its overview was fetched. The 4-band K/Th/U/total-count
  `geodawn_rad_u8.tif` derivative was **actually restored from an owner GitHub mirror** and verified against
  its pinned hash and grid; it is quantized, and its full processing lineage, licensed use and raw official
  download have not been independently authenticated. Official webpage availability is not equivalent to
  verification of every raw raster's download/coverage. Our priority concept uses this derivative only as a
  proposed input and is not cleared to train.
- The same owner mirror restored a 19-band core feature stack (including RTP, TMI, detrended elevation
  and slope) and a 12-band LiDAR-derived product. The core image is hash-pinned, **not an organizer-authenticated
  competition download**. The LiDAR product's `valid` band and missing tiles need explicit handling.
  The official organizer [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
  redirected to login; no credentials were requested or used.
- [GDR / INGENIOUS #1391](https://gdr.openei.org/submissions/1391) was checked and lists CC BY 4.0.
  A 2 m temperature-probe archive was retrieved and hash-verified from the owner mirror; raw-site download,
  individual observation licensing, temporal corrections and utility inside the scoring footprint remain
  unverified. The related mirrored wells/springs CSV contains a `dist_known_fault_px` column: **never use it**
  as a predictor or canary shortcut. Any fault-catalogue-derived or fault-proxy information must be rebuilt
  fold-locally from visible faults, or excluded.
- USGS research supports the general plausibility of [concealed fault signatures in aeromagnetics](https://www.usgs.gov/publications/high-resolution-aeromagnetic-data-a-new-tool-mapping-intrabasinal-faults-example)
  and [blind geothermal systems](https://www.usgs.gov/publications/discovery-a-blind-geothermal-system-southern-gabbs-valley-western-nevada-through),
  not the claimed novelty or predictive performance of these proposals. No method can be called genuinely
  novel across all sibling work without a full search and independent replication.

## Prespecified experiment, if the protocol conflict is resolved

For rank 1, first document the assigned lane and perform the surface uniqueness gate with the **complete
applicable registry**, without changing the literal rule. Then hide whole fault segments with spatial
buffers, rebuild every catalogue-derived feature solely from the visible catalogue, and mask visible
faults pixel-exactly. Use the unchanged pinned shared `evaluate_holdout.py` and `submission_writer.py`;
any shared defect belongs in the upstream template, not a private fork. Run every feature singly as an
AUC leakage canary; >0.90 requires investigation and blocks trust. Compare candidate and best baseline
on the same folds and pooled DTI (α=.2, β=.8, triangular 300 m kernel), recording evaluator version,
withheld-positive count and spatial-block bootstrap 95% CIs including the **paired** improvement CI.
Repeat the complete literal uniqueness check on final dots and validate the exact saved bytes. Require
an improvement over the current same-evaluator holdout best and a separate selector; no weekly slot is
spent by research. Maximum three experiments or two hours. The reference supplies CPU as well as GPU
options; no GPU was detected in this environment, but GPU is not a prerequisite for every experiment.
