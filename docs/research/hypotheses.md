# Candidate geological hypotheses not previously tried in this repo family — ranked

Date locked: 2026-10-26 (before any holdout number in this repo).
Evaluator for all gates: HOLDOUT-DTI, `gems-segment-pooled-v1`
(whole-segment hide-and-recover, 15 px / 1,500 m buffer, visible faults masked
pixel-exactly, pooled TPw/FPw/FNw, alpha 0.2, beta 0.8, 300 m triangular kernel).
Scores copied from sites are OWNER-REPORTED, never ORGANIZER-CONFIRMED, and are
never written as HOLDOUT-DTI. A leaderboard projection is never written as a score.

Why the incumbent is hard to beat (measured in GEMSDOE36
`docs/research/why-02778.md`, re-checked in this repo's README): the 0.2778 file
is the H19-5 corroboration field thinned to 44,090 dots (0.2600), then with the
3,891 dots ≤1 px and 2,545 dots 1–2 px from the catalogue deleted (0.2708 →
0.2778). No new coordinate was added after 0.2600; the removed near-catalogue
dots carried ~0.002–0.006 credit/dot vs 0.130 average and a 0.0556 break-even.
Beating it needs a *better detector surface*, not another emission trick.

| Rank | ID | Layers (competition band / external) | Physical signature targeted | Why it should catch a fault missing from USGS/INGENIOUS catalogue | Difference from anything in the 9 focus repos | Named non-fault mimic | Expected HOLDOUT-DTI gain vs cost |
|---|---|---|---|---|---|---|---|
| 1 | **GPC (this lane)** | 02_rtp, 13_iso_grav_anom, 15_depth_to_base_surf, 12_det_elev (all in training_features.tif) | Amplitude-invariant gradient-*phase* concordance: unit-gradient direction agreement (mean/min pairwise \|cos\|), double-angle consensus resultant R, ≥3-field consensus count, 100 m vs 300 m cross-scale orientation persistence, Laplacian zero-crossing concordance | A hidden normal fault juxtaposes basement/sediments, so magnetics, gravity, basement depth and elevation all turn across the *same* line even where each contrast is weak (deep/buried piedmont faults whose gradient magnitude is swamped by range-front lithology). Phase survives where magnitude ranking fails. | Focus repos used gradient *magnitude*, tilt, Hessian ridges, worms, Radon, Euler and scarp amplitude — never unit-gradient direction concordance across independent fields, and never a minimum-pairwise (weakest-field) term. Implemented in `src/kanler3/gpc.py`. | Lithologic contact, playa shoreline, volcanic flow edge, flight-line seam (align ≤2 fields; must fool all 4 + zero-crossings to score) | +0.003…+0.015 hoped; cost LOW (label-free transforms, no new data) |
| 2 | STEP-THROW | 12_det_elev, 15_depth_to_base_surf, 19_det_elev_slope | Signed asymmetric step profile across a candidate line: footwall-high/hanging-wall-low offset amplitude 100–600 m each side, sign-consistent between elevation and basement depth | Surface trace sits at the step midpoint; deep-field lineaments are displaced down-dip, so a *step* (not ridge) matched filter re-centres evidence on the trace of buried range-front faults | Prior scarp lanes used step *magnitude* maxima (LiDAR step_max, basement-step h61a scored 0.0009) — not a two-sided signed offset with cross-field sign consistency at 100 m grid | Erosional escarpment / terrace riser (single-field, sign-inconsistent with basement) | +0.002…+0.010; cost LOW–MED (directional sampling) |
| 3 | STRAIN-AXIS | 04_geod_2ndinv, 07_geod_shearrate, 08_geod_dilaterate, 10_deq_n100a15, 16_ieq_n100a15 | Rotation of geodetic principal strain axes + earthquake-density lineation anisotropy (structure tensor of ieq) co-located with dilatation gradient | Actively extending, unmapped faults localise present-day strain and microseismicity before a scarp is mapped; catalogue faults are largely Quaternary traces, not necessarily the active strand | H36C used a scalar "seismic-strain corridor" level; nobody used strain-axis *rotation* or seismicity *anisotropy orientation* vs Anderson extension | Volcanic inflation, groundwater-withdrawal strain bowls (equant, no lineation) | +0.000…+0.008, uncertain; cost LOW |
| 4 | MT-PHASE | 17_cond_surf, 15_depth_to_base_surf, 02_rtp | Conductivity lateral *phase* step (unit gradient of cond_surf) discordant with basement depth step: fault-zone clay/graphite conduit vs stratigraphic conductor | Fault conduits/barriers offset pore-fluid pathways, producing a resistivity boundary that need not coincide with a mapped trace in basin fill where scarps are buried | MTO-36 used magnetic-gravity contact crosscutting; HVG used cond_surf *residual level* after playa regression — neither used MT gradient direction vs basement discordance | Playa evaporite margin, palaeochannel clay (follows topography, concordant with elevation) | +0.000…+0.008; cost LOW |
| 5 | DEM1M-SCARP-AGE | USGS 3DEP 1 m DEM tiles via competition `1m_DEM_links.csv` (official source, see sources.md) | Expert-scale scarp morphology at 1 m: scarp height / slope-age (diffusion) profile classification on the raw DEM, not the 100 m aggregated u8 product | Human experts found the hidden faults largely by 1 m scarp reading; the aggregated 100 m LiDAR product discards scarp-face shape that separates fault scarps from terrace/channel risers | All focus lanes used the 100 m-aggregated lidar_scarp_features_u8 or 10 m DEM derivatives; none classified 1 m scarp profiles. **Not viable in this sandbox** (716 tile downloads + GPU-class compute) — named here with its source, not claimed as run | Terrace riser, channel bank, road cut (morphology differs in profile curvature) | Potentially largest (+0.01…+0.05 by the 0.4413 arithmetic) but cost HIGH / external-data blocked here |

Ranking rationale (Maximize P(Win)): GPC is the only candidate that is
(i) mechanistically orthogonal to every scored lane in the registry,
(ii) computable from already-pinned data on CPU, and (iii) testable on the
shared holdout within budget. STEP-THROW is a close second and is the
pre-registered fallback if GPC's canary or holdout fails.

## Pre-registered experiments (max 3, plus matched control)

- **B0 control**: 59-feature base stack, HGB, ridge-NMS spaced emission, 37,654 dots.
- **EXP-1 (GPC-full)**: B0 + all 15 GPC features.
- **EXP-2 (GPC-concordance)**: B0 + 12 GPC features (excludes consensus cos2/sin2
  orientation and the signed RTP-gravity polarity — tests whether pure
  concordance, not strike learning, carries any gain).
- **EXP-3 (GPC-full + B2)**: EXP-1 surface, emission restricted to pixels
  >2 px from the *visible* catalogue (fold-local in holdout; full catalogue in
  the final fit) — tests the dead-annulus deletion on a new surface.

Gates (fail-closed, automated, no human inspection): leakage canary
two-polarity AUC ≤ 0.90 for every GPC feature; promote an arm only if its
paired 95% CI vs B0 excludes 0 in the positive direction AND it beats the
recorded same-evaluator group best point estimate; final file must pass the
whole-array [0,1] validator and the focus-9 uniqueness check
(surface |Spearman| ≤ 0.90 and ≤70% of dots within 3 px of each champion).
Otherwise verdict = negative, file labelled DO NOT SUBMIT.
