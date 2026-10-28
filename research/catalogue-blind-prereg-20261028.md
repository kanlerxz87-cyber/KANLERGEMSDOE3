# Pre-registration: catalogue-blind dot candidates (28 Oct 2026)

Scope: one lane for this session. Budget: 3 experiments (E1-E3), stop after 3.
Evaluators (unmodified, source-locked): `vendor/shared-template` via `scripts/shared_tools.load_tool`:
`GEMSDOE32-HIDE-RECOVER-v3.0` (hide-and-recover pooled DTI, alpha 0.2, beta 0.8, 300 m triangular kernel,
spatial cluster bootstrap) and `GEMSDOE32-SGMC-CAL-v3.0` (off-catalogue USGS SGMC diagnostic).
Feature stack: shared `features.build` run unmodified on `data/core/training_features.tif`
(35 channels; the canonical cache bytes/digest are NOT available, so this is a rebuild by the upstream code,
not the canonical cache. Labelled accordingly).

## Hypotheses (ranked before scoring)
- H1 (E1): dots at local maxima of the 2-scale Hessian ridge response (`ridge_s2`) with 3-px non-maximum
  suppression separate fault-like linear features from blobs. Mechanism: a line-shaped response matches
  the 1-px fault trace the metric rewards. Non-fault mimic: topographic relief and drainage ridges
  (`relief5` alone has SGMC-AUC 0.77 in our canary, so relief confounding is plausible).
- H2 (E2): multiplying the ridge response by structure-tensor coherence (`coherence_s2`) favours linear,
  orientation-coherent features over isotropic ridges. Mimic: linear anthropogenic/DEM artefacts (roads,
  canals, lidar striping).
- H3 (E3): half ridge-NMS and half blue-noise coverage. Tests whether pure coverage (the non-fault mimic
  for this metric) is needed to recover distant faults.

## Protocol rules applied
- Selection is LABEL-FREE: the ranking uses only the 35-channel stack. The evaluator masks visible catalogue
  pixels itself.
- Canary: every channel alone vs SGMC off-catalogue positives (AUC > 0.90 = leakage until disproved).
- Decision rule (fixed here): promote only if the FINAL file beats the best same-evaluator incumbent on BOTH
  proxies: hide-and-recover > 0.0967 (GEMSDOE25/30) AND SGMC raw > 0.1024 (GEMSDOE27); AND uniqueness passes
  the literal gate; AND format validation passes.
- Uniqueness: `scripts/check_uniqueness.compare` (exact full-footprint 3-px directed overlap + rank correlation)
  against every restored registry raster, on the surface before the writer and on the final dots.

## Deviation log (kept, not hidden)
1. First run (`evidence/superseded` receipt, not in the main evidence) excluded all catalogue pixels DURING
   SELECTION. That uses hidden-fault information in the hide-and-recover evaluation and was a bug. It was
   corrected to label-free selection before any final number was taken. The superseded numbers are NOT used.
2. The final file removes catalogue pixels after selection (the shared writer's rule). This is a post-selection
   step consistent with the official-format intent (new faults only), not a selection leak.
3. The 37,654-dot budget is the participant convention seen in GEMSDOE32/36 outputs; no organizer rule
   specifying it was found (see the official rules PDF and problem page).
4. Uniqueness gate: the literal test was run against 30 of the 36 registry rasters that could be restored
   by hash (6 are unavailable: 2 GEMSDOE70, 3 KANLERGEMSDOE1, 1 GEMSDOE27). The registry is not a complete
   GEMSDOE inventory.
5. Saturation finding (added after the first uniqueness run, which is why it is recorded here): the calibration
   probe `13gems_r13-lattice-s5` covers 99.87% of the footprint within 3 px; uniform random dots also trip the
   literal test (99.9%). The literal test therefore cannot discriminate. The verdict reports this as a blocked rule
   defect, not a pass. The rule itself was NOT changed.
