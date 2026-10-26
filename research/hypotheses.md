# Preregistered geological ideas — 2026-10-26

**Decision:** design proposals only. No experiment is authorized until the literal
registry stop and the missing assigned-lane ambiguity are resolved. Their ordering
is a qualitative judgment, not a measured or forecast competition score. The
checkout was empty apart from its README; therefore none was implemented in this
repository before this record. A comprehensive claim that no other team has ever
used any component would be unverified. The proposed combinations must be checked
against the refreshed parallel registry before any experiment.

The prompt refers to “the single method paragraph below” but does not identify a
single assigned method. The first proposal is the preferred *future* lane, not a
claim that the user assigned it. The literal uniqueness rule includes controls;
we will not silently exempt the calibration lattice.

| Rank | Hypothesis and data | Target and missing-fault mechanism | Difference / confounder | Expected benefit and cost |
| --- | --- | --- | --- | --- |
| 1 | **Cross-boundary magnetic texture displacement.** GeoDAWN total or reduced-to-pole magnetic intensity, competition isostatic gravity and detrended elevation. | Search for a coherent, nonzero along-strike translation between paired magnetic textures on opposite sides of a prospective gravity-gradient line, with displacement consistent along neighboring windows. Displaced magnetic units can expose a buried fault beneath alluvium even without a mapped surface scarp. | Unlike a pixel-wise magnetic edge or generic scarp fusion, this tests a *matched pattern offset* on both sides of a line. **Non-fault mimic:** a volcanic flow edge or an intrusion, along with survey-line artifacts. Template features alone do not implement the proposed paired-window displacement; unseen work elsewhere is not ruled out. | Highest qualitative scientific promise; **high** implementation cost and resolution sensitivity. Magnetic sampling/flight-line geometry and the aperture problem may make the offset unreliable; any comparisons must include unshifted and contact controls. Data: official [GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [competition features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/); the owner mirror's authenticity is unconfirmed. |
| 2 | **Fan-channel offset consistency.** USGS 3DEP 1 m DEM, aggregated onto the competition grid, and magnetic lineaments. | Correlate multiple channel cross-sections across a candidate trace, looking for repeated signed lateral displacement and/or a common vertical step, then test corroborating magnetics. Such displacement may survive where catalogue mapping is incomplete. | More than a single terrain edge: seek a *consistent offset of several neighboring channels*. **Mimic:** depositional avulsion, terrace erosion, roads. The DEM coverage and resolution must be validated before testing. | Medium–high, but **high** cost: downloading, mosaicking, hydrological extraction and missing-tile handling. [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) is official; the competition supplies a tile list after login. Metadata/page access confirmed, actual DEM tiles not fetched here. Not yet viable for a reproducible run in this restricted sandbox. |
| 3 | **Blind transfer-zone thermal residual.** GDR 2 m temperature probes and well/spring chemistry plus GeoDAWN gravity and magnetics. | After deduplicating sites and modeling the sampled background by location and elevation, test whether an anomalous geothermal residual lies near a gravity/magnetic line-intersection or termination that is not merely a visible fault trace. | Residualize *survey effort* and site duplication rather than treating dense sampling as heat. **Mimic:** seasonal groundwater, environmental conditions and selective sampling. A thermal prospect is not automatically an actual fault or a vent. Other sites already tried hydrothermal and geothermal priors; distinctness of this precise residual approach is not established. | Medium, **high** cost and sparse coverage. The official [GDR 1391](https://gdr.openei.org/submissions/1391) metadata and public download links are available under CC BY 4.0; actual files were not fetched here. Not yet viable in this sandbox. |
| 4 | **Multi-scale edge polarity reversal.** Gravity anomaly and magnetic intensity from the competition feature stack. | At several scales, test whether paired gradient profiles show a consistent displacement/contact shape with a localized along-strike polarity reversal, suggestive of a faulted or juxtaposed magnetic unit. | Unlike multiplying gradient magnitudes, this examines *signed profiles and persistence*. **Mimic:** non-fault lithologic contacts or cultural/survey artifacts. Similar contact and curvature lanes exist on peer sites, so novelty there is unproven. | Lower expected incremental benefit, **medium** cost; no external layer needed once the competition stack is restored and authenticated. |

## Falsification protocol if an explicitly scoped lane becomes available

1. Freeze the mechanism, feature inventory, emission budget, spatial splits,
   buffer, controls, canary, and stopping rules before running. Reuse the pinned
   shared template's feature cache, `evaluate_holdout.py`, and
   `submission_writer.py` without creating a private fork.
2. On each withheld whole-segment spatial fold, derive **all** catalogue-based
   features from visible faults only, mask visible faults pixel-exactly, and run
   a two-sided single-feature leakage canary. AUC > 0.90 is a stop pending proof.
3. Before placing dots, compare the actual continuous surface and its defined
   preview support against every available registry raster. Stop immediately at
   Spearman > 0.90 or directed 3-pixel overlap > 70%. Recheck final
   dots only if the first stage passed; missing raster or missing surface is
   UNKNOWN, never PASS.
4. Report pooled HOLDOUT-DTI with evaluator version, withheld-positive count,
   spatial-block 95% CI and paired delta to the strongest **same-protocol**
   control. A catalogue recovery proxy is not the organizer score and must not
   be converted to a leaderboard forecast without validated calibration.
5. Format validation, scientific gates, complete registry coverage, and slot
   selection are separate checks. A locally valid TIFF is not portal approval.

Scientific basis: USGS discusses fault-offset magnetic lithologies and buried
structures in [Blakely et al.](https://pubs.usgs.gov/of/2000/0189/pdf/of00-189.pdf),
and reports multi-physics evidence for blind geothermal settings in
[Faulds et al.](https://pubs.usgs.gov/publication/70221765). These sources motivate
hypotheses; they do not validate our specific proposed algorithm or DTI improvement.
