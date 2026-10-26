# Pre-registration — KANLERGEMSDOE3 session 2026-10-26 (written before any experiment ran)

**Lane-paragraph irregularity.** The protocol says "Your lane is the single method paragraph below", but no
method paragraph was included in the prompt (also noted by the previous session, which stopped and produced
nothing). The user's standing instruction is that a unique TIF **must** be generated, so this session defines
its own lane as the top-ranked hypothesis below and records that choice here. This is logged as `IR-K3-LANE-01`.

**Budget.** At most 3 experiments or 2 hours wall-clock from the first experiment (started ≈22:20 UTC), whichever
comes first. Negative results are deliverables.

## Evidence this plan starts from (all verified this session)

* Official metric (page 967): DTI = TP/(TP + 0.2·FP + 0.8·FN), triangular 300 m kernel; known faults are masked
  pixel-exactly (forum 11516); public score is one pooled index over undisclosed chunks (forum 11550).
* 433 comparable registry rasters restored by git and SHA-256-verified (`registry/registry_index.json`).
* The 0.2778 champion (GEMSDOE32 `h33-h33-2-b2`, OWNER-REPORT) has 37,654 dots, **all** of them on pixels of the
  H19-5 ridge network (121,131 px; its 3-px buffer covers 19.6% of the footprint), none within 2 px of the
  catalogue. A protocol-unique file therefore needs ≥30% of its scored dots outside that buffer.
* GEMSDOE32's H47 already ran the "LLI-optimal unique allocation" lane: champion core + novel dots ranked by a
  weak score (feature AUC ≈0.54) confined to 16% of the footprint → PROJECTION 0.240–0.248, HOLDOUT-DTI 0.0784
  vs 0.0992 for its champion proxy. **That lane is not repeated here.**
* LiDAR-scarp layer (GEMSDOE24 product from USGS 3DEP 1 m DEM, sha256 `d580bb8b…`): single-band AUC against
  the catalogue is weak (0.48–0.59); the strongest band is `upface_max` (0.587).

## Hypotheses (untried in the registry; ranked by expected DTI gain ÷ cost)

| rank | id | layers | physical signature | why it catches *uncatalogued* faults | novelty vs registry | cost |
|---|---|---|---|---|---|---|
| 1 | **K3-H1 Antislope-scarp grain traces (ASGT)** | LiDAR `upface_max`, `downface_max`, `cross_max`, `coh100`, `strike`; visible catalogue (orientation only) | a 10–50 m-scale step that faces **uphill** (against the 100 m regional slope), coherent over ≥300 m and parallel to the local fault grain | uphill-facing scarps are almost uniquely tectonic: erosion, deposition, terraces and shorelines make downhill-facing risers. Small antithetic/synthetic hanging-wall and piedmont scarps visible only in lidar are exactly what pre-lidar Qfault compilations miss and what expert lidar mapping adds | H19-5 used facing-agnostic openness/LRM; GEMSDOE32 tested halo *side* via LLI and generic "LiDAR step" strata, never facing polarity × grain | low |
| 2 | K3-H2 Hanging-wall antithetic belt | ASGT + visible catalogue dip-side geometry | antislope scarps 0.5–3 km on the hanging-wall side of mapped range-front faults (graben geometry) | antithetic faults are rarely compiled at 1:250k | not tried | medium (dip side must be inferred from DEM) |
| 3 | K3-H3 Facing persistence | LiDAR facing bands + strike | the facing side stays constant along strike for km (fault) vs flips (channels, terraces) | removes channel-bank mimics that dominate generic scarp detectors | not tried | medium |
| 4 | K3-H4 Strain-gated piedmont scarps | geodetic shear/dilatation rate, `det_elev_slope` | scarps in low-slope piedmont belts inside high geodetic strain-rate zones | active deformation is where young scarps survive | strain used only as a raw ML feature elsewhere | low |
| 5 | K3-H5 Radiometric offset edges | GeoDAWN K/Th/U edges | sharp, linear K/Th contrasts that cut lithology | bedrock faults without scarps | radiometrics used only as raw features | medium |

**Selected lane: K3-H1 (ASGT).** Non-fault mimics and their handling: landslide/sackung headscarps (ridge-top,
high relief → `relief` veto), channel banks (across-slope gradient → `cross_max` dominance veto), roads/berms
(short, straight, any orientation → grain-compatibility and coherence down-weight), lake shorelines (downhill-facing
→ excluded by the facing test). LiDAR is missing on ~25% of the footprint; ASGT emits nothing there.

## Experiments (≤3) and pre-declared decision rules

* **E1 — mechanism on the shared hide-and-recover holdout** (`vendor/gems57`, `buffered_component_draw`, seed 20,
  20% whole components withheld per label-blind quadrant, 3-px context collar, pixel-exact known mask, pooled DTI
  α=0.2 β=0.8, 300 m kernel, paired 20 km-block bootstrap 1,000 draws). Arms at matched dot count:
  ASGT; ablation A (upface only, no grain/coherence); ablation B (generic `step_max`); control C1 = H19-5 dotted
  at 2.8 px with fold-local B2 (champion recipe; leak-advantaged because H19-5 used the full catalogue);
  control C2 = champion bytes (leak-handicapped). **Leakage canary:** any single feature with AUC > 0.90 for
  withheld positives → stop. **Mechanism supported** iff ASGT − ablation A paired 95% CI > 0.
* **E2 — protocol-unique allocation + projection.** Core = ASGT dots inside the H19-5 3-px buffer (≤69.5% of
  scored dots); novel = ASGT dots outside it (≥30.5%), all at >3 px from the catalogue (catalogue-proximal
  depletion is ledger-supported). Dots are counted only where they are scored (inside the footprint, off the
  catalogue), so masked pixels cannot be used to pad uniqueness. Report LLI PROJECTION (shared GEMSDOE32 S3 fit,
  ±0.022 LOO MAE) and HOLDOUT-DTI.
* **E3 — one budget/share variant** chosen from E2 diagnostics (not a free sweep).

**Verdicts.** `promote` (hand to the separate selector) only if: format-valid AND unique (no non-space-filling
registry raster with >70% forward overlap; Spearman ≤0.90 with every raster) AND HOLDOUT-DTI ≥ the best control in
the same run AND LLI PROJECTION ≥ the champion's projection under the same fit. Otherwise `negative` — the file may
still be published as a valid, unique research artefact, clearly marked **not expected to beat 0.2778**.
