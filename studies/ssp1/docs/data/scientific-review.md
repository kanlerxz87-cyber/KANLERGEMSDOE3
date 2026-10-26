# Scientific review · 26 October 2026

## Executive conclusion

**There is no newly authorized submission in this run.** A genuinely new SSP1 raster was generated, checked from saved bytes, and made downloadable. Its pixel mask is not an exact duplicate within the comparable frozen registry. However, it fails the literal lane-overlap rule and does not beat the documented upstream holdout best. The automated verdict is **negative / DO NOT SUBMIT**. No competition upload or selector operation occurred.

**HOLDOUT-DTI — GEMSDOE32-HIDE-RECOVER-v3.0; 22,232 withheld positive-pixel events; spatial-block 95% CI:** SSP1 = **0.084644 [0.070384, 0.097041]**. There are 20,321 unique withheld positive pixels across the two draws; neither count is a count of independent faults. The upstream H38 card reports, on that evaluator and event count, **0.116958 [0.100533, 0.132040]**. Its OOF arrays were not reproduced here, so a paired improvement claim against it would be unsupported. The candidate's point estimate already fails the improvement requirement.

These are local validation results, **not** estimates of the hidden public or private leaderboard. No file-specific organizer receipt is available for the historical claim 0.2778. A public leaderboard observation on this date showed 0.4437, but it does not identify any peer artifact or its mechanism.

## 1. What the competition actually asks

[The official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) targets geological **faults**, structures that can be indicative of geothermal resources. It does not ask for a direct map of geothermal vents, measured temperatures or economically productive reservoirs. Newly expert-identified faults absent from the public catalogue form the initial test labels. The final round expands that test label set using expert review of predictions.

This distinction matters scientifically. A conductivity anomaly, warm spring or magnetic low can support a geothermal interpretation, but is neither a unique fault signature nor a fault label. Conversely, a well-imaged fault need not have the heat source, connected permeability and fluid supply needed for a useful geothermal system. This run reports candidate structural evidence, not a newly discovered productive vent.

The [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) explicitly integrates multiple exploration techniques for hidden systems. [GDR 1391](https://gdr.openei.org/submissions/1391) lists shallow temperature surveys, paleogeothermal deposits, strain, conductance, gravity, magnetic and well/spring data. Those are valuable physical context and potential independent tests; they do not change the competition's prediction target.

## 2. Why the reported 0.2778 file differs from its relatives

The actual byte-level results, not names, establish:

| Construction observation | Measured result |
|---|---|
| GEMSDOE25 D2.8 parent | 44,090 positive pixels |
| GEMSDOE30 versus GEMSDOE25 | Exactly the same positive-pixel mask |
| GEMSDOE28 solo = D2.8 outside 1 px of catalogue | Exact equality; 40,199 dots |
| GEMSDOE31 versus GEMSDOE28 solo | Exact positive-mask equality |
| GEMSDOE32 Champion = D2.8 outside 2 px of catalogue | Exact equality; 37,654 dots |
| Champion additions relative to D2.8 | Zero |
| D2.8 dots removed to obtain Champion | 6,436, all within 2 px of the catalogue |
| Champion versus the GEMSDOE36 Anderson-named map | Champion is a subset; Anderson adds 1,200 dots |

See [the independently executed nine-site audit](../evidence/nine_site_audit.json). Equal masks can have different file hashes because compression, missing-data representation or metadata differ. A name such as “PINN” or “analogue” is not proof of an independent geological mechanism.

### Metric mechanism, with the right caveat

Let `T` be distance-weighted true-positive credit, `F` false-positive mass and `G` the number of truth pixels. Since `FN = G − T`, the official denominator is

```
D = T + 0.2 F + 0.8 (G − T) = 0.2 (T + F) + 0.8 G.
```

When redundant dots are removed without reducing max-kernel truth credit, `T` remains fixed and `F` falls, so DTI rises. That provides a **plausible geometric explanation** for why thinning and removing a low-yield collar could help. It is not evidence that this happened on the hidden truth, nor does it prove a geothermal discovery mechanism. If a removed dot uniquely covers a nearby new fault, true-positive credit also falls and the change can hurt.

The [organizer's staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2) excludes the **exact known pixels**, not an official 200 m dead annulus. Neighboring pixels are still meaningful predictions. The 2 px exclusion is an empirical model heuristic. Receipt-linked controlled runs and hidden labels are unavailable, so the causal question “why did it score exactly that value?” is not identifiable from these files alone.

This also explains why blindly increasing dot count or unioning all high-claim maps is not a principled next step: the union can duplicate already delivered kernel coverage while adding false-positive mass. Nor should a new filename for D2.8 consume a slot.

## 3. Four hypotheses were ranked before fitting

The complete [preregistration](../registry/hypotheses.json) was frozen before the feature/model run; [its hash](../evidence/preregistration_sha256.txt) is retained. The starting repository had no implementations. Cross-site originality was not assumed: related physics exists in peers, and empirical uniqueness is separately tested.

| Priority | Hypothesis and concrete layers | Physical transform and missing-catalogue rationale | Non-fault mimic | Expected improvement / cost |
|---|---|---|---|---|
| 1 · SSP1 · executed | Detrended elevation, gravity, detrended slope; owner-derived LiDAR and encoded K/Th | Fit a normal-direction antisymmetric step after projecting out a smooth quadratic terrain null; persistence along the tangent; gravity alignment and radiometric nuisance contrasts. No catalogue extension or incumbent raster enters. | Alluvial-fan terrace, paleoshoreline, road embankment, lithologic contact | Highest qualitative priority, **not a numeric score projection**; medium cost |
| 2 · MCP2 · not run | RTP, gravity, basement-depth channels | Cross-profile lag between gravity and magnetic edges rather than coincidence; a possible covered boundary independent of mapped traces | Dipping intrusive contact, remanence, variable flight height | Second qualitative priority; medium–high cost; physics and cross-site uniqueness unproven |
| 3 · RBN3 · not run | Conductivity, basement depth, detrended elevation, gravity | Conductivity Hessian saddle plus a narrow-neck null test at an independent gravity step; focus on covered basin interiors | Saline groundwater channel, sedimentary facies boundary | Third priority; coarse resolution may defeat it; low–medium cost |
| 4 · RSC4 · not run | Elevation, encoded K/Th/U, LiDAR step/coherence | Persistent scarp step conditional on radiometric quietness, treating radiometrics as a nuisance-control rather than an alteration boost | Uniform-lithology terrace, grading, road cut | Fourth priority; quiet radiometrics alone is not fault evidence; low cost |

All four are computable from the restored layers and need no new external data to test. They are not four experiments: **only SSP1 was executed**, and there was no lane switch after rejection. Any future proposal needing new data must first verify a specific official resource, access, licensing, spatial coverage and reproducible ingestion. The GDR/USGS links in the source ledger verify available metadata and advertised resources, not a promise that an unperformed download has succeeded.

## 4. The SSP1 experiment, exactly

For nine elevations sampled along the local terrain-gradient normal at offsets `t = −4,…,+4` pixels, fit the smooth null basis `X = [1,t,t²]`. Define `Q = I − X X⁺`. For a proposed step width `w`, use `s = Q tanh(t/w)` and profile residual `r = Qz`. The residualized step's amplitude and fit improvement are

```
a = (r·s)/(s·s)
R²_step = (r·s)² / [(r·r)(s·s)].
```

The fixed widths are 0.7 and 1.4 pixels. This explicitly removes a smooth slope/curvature null; an odd-symmetric local step can fit, whereas an ideal symmetric ridge or valley cannot. Synthetic unit tests verify datum/smooth-trend invariance and the distinction. This is a **shape likelihood feature**, not a calibrated geological Bayes factor: actual terrain noise is not proven independent Gaussian noise, and the smooth null is deliberately limited.

Seventeen label-independent features combine those profile statistics, tangent persistence, gravity/topography gradient alignment, two encoded radiometric contrasts, documented decoded/clipped LiDAR aggregates and cached detrended slope. The radiometric encoding is not a concentration scale, so no fake physical K/Th ratio is calculated. The LiDAR inverse encoding recovers only a clipped approximation; it cannot recover lost fine-scale information or failed tiles.

Every feature alone is tested with a leakage-canary AUC on withheld positives versus sampled unlabeled background. The maximum either-direction AUC is **0.564622**, below the 0.90 canary threshold. This is a **LEAKAGE-CANARY diagnostic**, not DTI; passing it does not prove absence of leakage. Independent provenance and split checks remain necessary.

A fixed HistGradientBoosting ranking model is fit on visible faults **outside the test quadrant plus a 15 px collar**. Negative samples are unlabeled pixels more than 3 px from the fold-visible faults; they are not assumed geologically proven negatives. No catalogue-distance or coordinate feature enters. Each whole hidden connected segment is absent from fold-visible supervision. The held quadrant's visible pixels are masked exactly during emission and scoring. Two draws across four quadrants form one frozen experiment; the draws are not hyperparameter tuning.

The fixed emission rule is score-priority greedy 2.8 px disk exclusion, not a claimed globally DTI-optimal algorithm. It uses 37,654 full-footprint dots and area-scaled fold budgets. Production training can use all supplied labels; fold training cannot. The unmodified shared evaluator pools TP/FP/FN, applies the official 300 m triangular kernel, and reports a spatial-block bootstrap CI. No score inflation is obtained by averaging cell DTIs instead of pooling counts.

## 5. Results and falsification

**HOLDOUT-DTI — GEMSDOE32-HIDE-RECOVER-v3.0; 22,232 positive events; spatial 95% CI:** **0.084644 [0.070384, 0.097041]**. This is below the documented upstream best and does not meet the required improvement gate.

**HOLDOUT-DTI / external-catalogue diagnostic — GEMSDOE32-SGMC-CAL-v3.0; 62,703 external positive pixels; spatial 95% CI:** raw DTI **0.065148 [0.054210, 0.075889]**. This is an independent public-catalogue diagnostic, not newly withheld organizer truth. The template's SGMC collar is a three-iteration cross dilation, not a Euclidean disk. Its prevalence-rescaled result is intentionally not promoted into a leaderboard prediction.

SSP1's physical idea remains plausible in some terrain, but the tested implementation is a measured negative. At 100 m resolution an 800 m cross-profile may describe mountain flanks and erosional breaks better than a low-throw fault scarp. Encoded max-aggregates of 1 m terrain do not retain the original cross-section needed to resolve that ambiguity. Incomplete labels also make naive supervised background examples potentially positive. These are hypotheses about failure, not verified causal diagnoses; no additional tuning was performed after the duplicate stop.

## 6. Uniqueness is four different questions

1. **File SHA:** this TIFF's byte hash differs from the frozen registry.
2. **Pixel mask:** zero exact mask matches in the 2,711 comparable snapshot entries. This is not a claim about unpublished or later artifacts.
3. **Pre-placement surface correlation:** maximum full-footprint absolute Spearman **0.437207** among the comparable entries. Eighteen incompatible/malformed entries are explicitly quarantined; universal certification is therefore incomplete, not silently “all passed.”
4. **Final dots:** **99.875179%** of SSP1 dots lie within 3 px of the registered lattice, exceeding 70%. The final guard stops at the first violation, as requested; it does not pretend it evaluated all final overlaps after the stop.

The lattice proof is stronger than this one observed failure. It covers 5,160,724 of 5,167,373 footprint pixels within 3 px. With only `U = 6,649` uncovered cells and `N = 37,654` distinct dots, at most U dots can escape overlap, so the overlap is at least `max(0, 1 − U/N) = 82.341849%`. This is a counting argument, not a projection or a model score. The current constraints cannot authorize a map at this budget. Reducing the budget or moving dots into boundary gaps purely to satisfy the registry would replace geology with an anti-registry artefact.

## 7. Why no leaderboard point estimate is published

A withheld public-catalogue segment is not exchangeable with every new expert-mapped fault. Surface visibility, age, mapping effort, coverage and fault type can all differ. More importantly, many historical high-claim files are identical or nested masks, not independent calibration examples. Their frozen public-catalogue masks cannot be cleanly scored by simply pretending the full-catalogue masking never happened. A regression from those claims to a new hidden-test score would have pseudo-replication, label leakage and unknown covariate shift.

Two possible hidden label sets can be consistent with the same observed public inputs yet assign very different DTI to this candidate. Thus a precise hidden score is not identified by the available evidence. The honest automatic estimate is local HOLDOUT-DTI with its declared population and CI; **leaderboard estimate = unavailable**. Beating 0.2778, 0.3195 or the observed public leader cannot be promised.

## 8. Validation, limitations, and what is finished

Both generated TIFFs are independently re-read. The zero-filled version has no NaN or Inf anywhere, only values in [0,1], one float32 band, and exact CRS/shape/transform agreement with the pinned owner-mirrored sample. The NaN-outside twin follows the sample's missing-data convention. All 13 shared checks pass. SHA-256, the filename, a short unique name and a 98-character note are published with the file. This is **local saved-byte validation**, not an organizer acceptance receipt.

Core inputs were restored autonomously; no GPU or fresh password was needed. However, mirror integrity is not official-host authenticity. In particular, the mirrored sample contains catalogue ones although the public page describes an absence example. Only its finite footprint and geometry are used; its values are never a feature. Its validity mask differs slightly from the raw feature footprint, and the audit records both differences. No permissive license for the peer software is assumed merely because the data sources are official.

The website, tables, retained brief, source ledger, reproducible pipeline, new TIFF/ZIP, independent tests and negative JSON card are completed. The scientific requirement of a higher-scoring, protocol-unique, authorized competition submission is **not met** and is explicitly blocked. The project does not leave that judgment to a human inspector: it computes **NO**. A real weekly-slot selector and authenticated remaining capacity are separate requirements imposed by the prompt itself, not a missing raster-format inspection step.

## Official sources for manual review

- [DrivenData problem, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData known-pixel masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DOE/NLR September 2026 rules, especially 3.3–3.6](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN acquisition metadata and CC0 rights](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR INGENIOUS compilation and CC BY 4.0 resources](https://gdr.openei.org/submissions/1391)
- [GBCGE INGENIOUS project and publication index](https://gbcge.org/current-projects/ingenious/)
- [Official reference code](https://github.com/drivendataorg/gems-prize-reference-solution)

The structured [source ledger](../registry/sources.json) separates official facts, owner-mirror provenance, unverified historical claims, mathematical derivations, local measurements and untested hypotheses. A hyperlink is not blanket verification of everything a peer site claims.
