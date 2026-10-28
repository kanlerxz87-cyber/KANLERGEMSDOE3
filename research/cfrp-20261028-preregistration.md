# Preregistration — 2026-10-28 session (written before any experiment in this session)

## Lane (single method, declared for this session)
**CFRP — Cross-Field Ridge Persistence.** Label-free Hessian ridge/saddle fields
computed independently on RTP/TMI, isostatic gravity and detrended elevation at
Gaussian scales σ ∈ {1.5, 3, 6} px, combined as cross-field min/product and
scale-persistence features, fed (with raw-band + context base features) to a
HistGradientBoosting classifier trained only on *visible* catalogue faults in
each holdout fold. Emission: ridge-NMS ≥3 px-spaced dotted emission
(`src/kanler3/emission.py`, shared `gems.metric.ridge_nms`), budget and
catalogue-collar rule selected in Experiment 2 only. No registry raster, no
prior submission raster, no catalogue-distance feature is read by any feature.

Named non-fault mimic: intersecting intrusive/lithologic contacts, flight-line
levelling seams, basin-fill boundaries, alluvial terrace breaks.

## Why 0.2778 (verified geometry, `docs/h33-lineage-20261027.json`)
GEMSDOE25 and GEMSDOE30 champion masks are byte-different files with identical
44,090-dot masks (owner-reported 0.2600). GEMSDOE32 H33-B2 (0.2778) is exactly
that mask minus the 6,436 dots within 2 px of the mirrored catalogue, zero
additions (37,654 dots). Hypothesis tested here: sparse near-catalogue thinning
removes FP mass (α=0.2) at little TP cost (β=0.8, 300 m triangular kernel), and a
*different, better-ranked* surface under the same thinning beats it.

## Five candidate hypotheses (ranked before results)
| Rank | Hypothesis | Layers (training_features.tif bands) | Signature | Why uncatalogued | Differs from repo | Cost |
|---|---|---|---|---|---|---|
| 1 | **CFRP cross-field ridge persistence** (SELECTED) | rtp(2), tmi(14), iso_grav_anom(13), det_elev(12); gradients 3,9,11,18 | Hessian ridge strength per field/scale; cross-field min/product; scale persistence (min/mean across σ); saddle √(λ⁺·−λ⁻) | Concealed faults perturb ≥2 independent potential fields co-locatedly even with weak single-field amplitude; no catalogue position used | Repo has pointwise/context HGB, single-field worms/Euler/tilt, one-scale 150 m continuation ratio; no cross-field Hessian ridge persistence product | Medium, core-only |
| 2 | Signed edge-migration stability under continuation | tmi(14), rtp(2), tmi_hg(3), tmi_vg(9), depth_to_base(15) | Track signed zero-crossings through σ ladder; reward positional stability | Deep source edges stay put as shallow noise decays | Repo tracks no signed edge trajectories (single-ratio continuation exists in CADG) | Low, core-only |
| 3 | Two-sided directional-fabric entropy break | rtp(2), tmi(14), iso_grav(13), controls det_elev(12), slope(19) | Jensen–Shannon divergence of opposing-side structure-tensor orientation histograms | Buried juxtaposition rotates grain at moderate amplitude | Repo has pixel coherence, not two-sided distribution divergence | Medium, core-only |
| 4 | Magnetic–gravity edge centreline lag | rtp(2), iso_grav(13), depth_to_base(15) | Normal-direction cross-correlation peak lag of bandpassed gradients | Dipping covered boundaries offset magnetic vs gravity edges | Repo detects coincident edges only | Medium-high, core-only |
| 5 | Hydrochemical geothermometer residual corridors | GDR 1391 chemistry + core bands | Lithology/elevation-conditioned residual corridors | Fluid ascent reveals permeable concealed structures | No chemistry model in repo | **Not viable now**: exact official chemistry bytes/fields/coverage unverified in sandbox; named source needed: GDR submission 1391 https://gdr.openei.org/submissions/1391 (free, official DOE Geothermal Data Repository) — obtainability of the required table not confirmed, so not proposed as viable |

## Experiments (max 3, stop rules fixed now)
- **E1**: Holdout (`gems.holdout.SegmentHoldout`, buffer 15 px, pooled DTI
  α=0.2 β=0.8 300 m triangular, evaluator `gems-segment-pooled-v1`): arm BASE
  (raw+context) vs arm CFRP (BASE+CFRP features), emission V1 (budget 37,654
  total-equivalent per-fold proportional, eligible = valid fold & >2 px from
  *visible* catalogue). Leakage canary first: every CFRP feature alone,
  two-polarity AUC > 0.90 ⇒ leakage, feature dropped and logged.
  Promote CFRP only if paired ΔDTI 95% CI > 0 vs BASE.
- **E2**: Emission selection on the E1-winning surface (no retraining):
  V1 (37,654, collar>2px), V2 (44,090, collar>2px), V3 (37,654, no collar),
  V4 (30,000, collar>2px). Pick highest pooled HOLDOUT-DTI; ties → smaller budget.
- **E3** (only if E1 fails): rank-average ensemble BASE+CFRP surfaces, V1 emission.
  If E1 passes, E3 is the final-model uniqueness/validator audit (not a model change).

## Uniqueness gates (protocol)
Surface before placement AND final dots vs every focus-9 champion raster
(+13GEMSDOE spacing-5 lattice reported separately as space-filling calibration
control per `gems.novelty.classify_space_filling_control`): Spearman |ρ| ≤ 0.90
and candidate dots within 3 px ≤ 70% for competing methods. Exceed ⇒ duplicate, stop.

## Score labelling
Every number is HOLDOUT-DTI (evaluator, withheld positives, 95% CI) or
ORGANIZER-CONFIRMED (none in this session) or PROJECTION (calibration method
stated inline, never written as a score).
