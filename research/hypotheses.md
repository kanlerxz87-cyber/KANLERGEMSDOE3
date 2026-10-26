# Conditional geological hypotheses — negative-session handoff

These are preregistered research directions, not implemented methods, proven novelty, scores or submission candidates. The assigned single-method lane is absent, so none was selected or run. The original availability state is retained in `2026-10-26-plan.md`; this document reflects the later source review recorded in `review.md`.

No defensible numerical improvement estimate is available. Benefit ranks are qualitative priorities conditional on a valid shared evaluator, identical folds, a complete registry, canonical cache and incumbent. Faults are the target; geothermal evidence is only a physical proxy.

## 1. Cross-scale edge phase disagreement

- **Layers:** Core TMI/RTP; upward-continued TMI at 150 m; GeoDAWN K/Th/U or ratio grids.
- **Physical signature / transform:** Persistent magnetic edges with signed edge-normal radiometric derivative reversal or termination, rather than coincident large gradient magnitudes.
- **Why an unmapped fault:** A buried discontinuity might remain visible at depth while shallow alteration changes across a concealed segment. Catalogue distance is not used as positive evidence.
- **Difference from implemented methods:** The specified signed cross-scale/radiometric termination interaction was not implemented or tested in this review session. Concurrent main now contains GPC phase-concordance features; direct code and registry comparison is required before calling the proposed disagreement mechanism distinct. It is not another H19/H33 dot-thinning claim.
- **Named non-fault mimic / confounder:** Intrusive lithologic contacts or flight-block levelling seams.
- **Availability now:** Conditional. Core mirror restored; derived bands and shared cache must be verified. Official GeoDAWN metadata obtained, original archive bytes not obtained.
- **Estimated cost (conditional):** Medium
- **Benefit rank:** Highest qualitative information-gain potential in this shortlist; no numeric DTI projection.
- **Official source:** https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and

## 2. Repeated drainage displacement graph

- **Layers:** Core detrended elevation (band 12), elevation slope (band 19), derived drainage graph; optional 3DEP high-resolution DEM.
- **Physical signature / transform:** Repeated signed lateral offsets across independent tributaries, with graph-level agreement across scales instead of a single scarp maximum.
- **Why an unmapped fault:** Displaced channels might reveal a transverse structure that has no continuous surface scarp and is absent from a trace catalogue.
- **Difference from implemented methods:** Not implemented locally; graph-level repeated displacement is not the earlier DEM ridge extractor. Hydro/conduit peer code still needs a direct novelty check.
- **Named non-fault mimic / confounder:** Stream capture, fan avulsion or abandoned lake shorelines.
- **Availability now:** Only a coarse core-data pilot is accessible. The 100 m grid may not resolve channel offsets. A new 1 m variant is not viable until official tile downloads/coverage are verified.
- **Estimated cost (conditional):** High
- **Benefit rank:** Second qualitative rank; more independent evidence, but resolution risk. No numeric DTI projection.
- **Official source:** https://apps.nationalmap.gov/downloader/

## 3. Alteration-front termination pairs

- **Layers:** GeoDAWN K/Th/U or Th/K and U/K; independent magnetic edge or analytic-signal axes.
- **Physical signature / transform:** Pair opposite-side along-strike terminations of alteration fronts across a magnetic edge; do not select merely high-ratio pixels.
- **Why an unmapped fault:** An unmapped transverse structure may compartmentalize alteration instead of lying on its strongest observed anomaly.
- **Difference from implemented methods:** Not implemented locally. Explicit pairing/topology differs from a pixelwise alteration conjunction, but global novelty has not been established.
- **Named non-fault mimic / confounder:** Erosional unconformities, lithologic boundaries or soil-moisture effects.
- **Availability now:** Conditional on exact band definitions, uint8 saturation and shared-cache provenance; no new official archive has been downloaded.
- **Estimated cost (conditional):** Medium
- **Benefit rank:** Third qualitative rank; physically motivated corroboration, not a calibrated probability or DTI forecast.
- **Official source:** https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and

## 4. Terrain-conditioned thermal sign asymmetry

- **Layers:** GDR #1391 well/spring temperature and sampling metadata; elevation, aspect and drainage position.
- **Physical signature / transform:** Robust terrain-corrected temperature residuals with repeated cross-line sign consistency, rather than nearest-hot-point distance.
- **Why an unmapped fault:** Focused upflow could corroborate concealed permeability away from mapped traces. It does not by itself establish a geothermal vent or a fault.
- **Difference from implemented methods:** Not implemented locally. Must be distinguished from the existing geothermal-conduit and PINN peer families before testing.
- **Named non-fault mimic / confounder:** Groundwater advection, seasonality, pumping or land-use effects.
- **Availability now:** Not viable yet. Official CC BY 4.0 index/resource links verified; attempted probe ZIP fetch failed, and date/depth/season coverage is not verified.
- **Estimated cost (conditional):** High
- **Benefit rank:** Fourth qualitative rank because sparse and seasonally biased sampling may dominate. No numeric DTI projection.
- **Official source:** https://gdr.openei.org/submissions/1391

## Evaluation and stopping contract

Test every feature alone first. Treat AUC >0.90 as leakage until disproved. Compare with the same-fold incumbent on a whole-segment, spatially blocked holdout and a segment buffer; derive every catalogue feature from visible faults only. Exclude visible fault pixels exactly. Use the centrally repaired pooled DTI operator with alpha 0.2, beta 0.8 and a 300 m triangular kernel, with withheld-positive counts, evaluator version and a 95% CI. Feature ablations and negative controls precede any combined candidate.

Before placement, compare the continuous surface with every registry entry. After emission, compare the final dot mask with every registry raster. Signed Spearman rho >0.90 OR >70% candidate dots within Euclidean 3 pixels of any entry means duplicate: log and stop. Distinct hashes are not semantic uniqueness.

The fixed session begins 2026-10-26 21:57 UTC and stops after three experiments or two hours (23:57 UTC), whichever first. This session executed zero geological experiments and spent zero competition submissions. There is no automatically authorized next experiment or slot.
