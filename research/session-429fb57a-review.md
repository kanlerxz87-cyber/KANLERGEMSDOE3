# Repository review — 29 October 2026

## Outcome

**NEGATIVE / DO NOT SUBMIT.** This was a repository and reproducibility review, not a new geological experiment. No new TIFF, leaderboard estimate, organizer-confirmed result, or competition-slot action was produced. This session did not run a model experiment: the prompt does not provide the required explicit single-method paragraph, and the SSP1 study's own all-registry lattice feasibility result blocks the 70% final-dot rule for its fixed dot budget. Do not treat the historical candidate or its historical HOLDOUT-DTI as an eligible download.

The full standing request remains preserved in `PROJECT_PROMPT.md` and the README. Root README, AGENTS.md, project request, the previous continuation, SSP1 lane documentation and evidence were reviewed before assessment. The repository already has an extensive executive site, source ledger, nine-site registry, experiments and a separately isolated SSP1 study; extending the UI to claim a higher leaderboard score would exceed the evidence.

## Three review passes

### Pass 1 — repository and evidence inventory

- Working branch: `arena/429fb57a-kanlergemsdoe3`; initial tree clean at `295efea`.
- The tracked competition inputs `sample_submission.tif`, `training_features.tif`, and `labels.tif` are absent from `data/`. Thus this checkout cannot freshly regenerate the real-data feature stack or repeat a holdout fit from those input files.
- Existing `studies/ssp1/registry/hypotheses.json` holds four ranked geological candidates. SSP1 is the residualized signed normal-direction scarp-profile likelihood method; MCP2 the displaced magnetic/gravity edge-centreline method; RBN3 the conductivity-neck method; RSC4 the radiometrically quiet, multi-scale scarp method. These are existing preregistrations, not new claims or numerical performance predictions.
- The prior SSP1 run card reports **HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 withheld positives, 95% cluster-bootstrap CI 0.07038–0.09704)** for SSP1-E1. This is a historical local holdout result, not an organizer score and not a new rerun in this review. It is not a public leaderboard projection.
- `studies/ssp1/registry/irregularities.json` records the decisive issue: only 6,649 footprint pixels outside the 3-pixel dilation of the dense calibration lattice, versus a 37,654-dot output budget. Any map of that budget must overlap at least 82.3418% by the recorded feasibility bound, exceeding the protocol's 70% stop. SSP1's recorded final dots themselves overlap 99.8752%. This is a protocol/registry conflict, not a reason to jitter dots or redefine the registry.
- No artifact-specific organizer receipt, authenticated competition submission template, live account slot count, or DrivenData authentication is present. The owner's mirrored files and historic peer-site claims are not equivalent to organizer-authenticated truth.

### Pass 2 — reproducibility and safety checks

- Installed the pinned root requirements into ignored `.venv/` and ran `.venv/bin/python -m pytest -q`: **329 passed, 9 skipped**.
- `.venv/bin/python scripts/build_site.py --check`: **exit 0**, no stale generated site reported.
- The SSP1 release verifier completed its deterministic technical checks and reported a technical/reproducibility PASS, explicitly **not scientific promotion**; it also reported `ok_to_submit: false`, negative verdict, no fresh real-data reevaluation, and no organizer authentication. The verifier rewrote two committed verification JSON snapshots using offline/absent-input scope. Those incidental rewrites were reverted; no evidence was silently updated. Its stdout was preserved in the review-session record only as summarized here; rerunning the verifier in a data-absent checkout can rewrite published evidence and should be treated as a mutating command.
- `git diff --check` passed; the final tracked tree is clean apart from this review record/card.

### Pass 3 — request reconciliation and blockers

- The request to create a new high-scoring, unique TIFF cannot be truthfully completed from this state. No numeric estimate may be inferred from the peer sites' scores, and the existing SSP1 TIFF fails the explicit uniqueness condition. There is no evidence to label any suggested download as OK to submit.
- The request's instruction to run 3–5 candidate tests conflicts with the lane protocol and the standing fail-closed lane rules: lane assignment is absent, only one method can be tested per lane, stop immediately on >70% registry overlap, and no model should be started without the canonical cache and evaluator prerequisites. The repository already contains four ranked proposals; do not run the other three under SSP1.
- The existing submission guide and executive summary already explain format, download and upload steps; retain the clearly visible no-upload warnings. A valid GeoTIFF format is not evidence that its values meet [0,1], its grid matches the authenticated organizer template, it is unique, scientifically predictive, or accepted by DrivenData.
- No PR or merge is appropriate for this read-only review: there is no implementation diff to propose, and the fixed session branch must not be merged to `main` without a substantive reviewed change. The generated review note/card document findings without asserting a software change.

## Candidate hypothesis shortlist (existing preregistration; no fresh validation here)

Qualitative ordering below is the study's prior ordering, not a predicted leaderboard uplift. Cost is the existing preregistration estimate. All use cached layers, so no new external source is required *if* the canonical cache is authenticated and available. None is authorized to execute in this review.

| Rank | Hypothesis / specific layers and signature | Why potentially finds uncatalogued faults; difference from recorded repo approaches | Non-fault mimic | Cost / disposition |
|---|---|---|---|---|
| 1 | SSP1: elevation (band 12), isostatic gravity (13), detrended slope (19), LiDAR scarp aggregates, encoded K/Th. Residualize nine-point normal profiles against a quadratic smooth null; score signed tanh steps at 0.7/1.4 px and tangent persistence. | Catalog-independent cross-section shape rather than generic ridge strength, catalogue collars, or analogue tips; may nominate a subtle/buried scarp away from mapped traces. Already tested once; negative, duplicate stop applies. | Terrace/paleoshoreline, road embankment, lithologic contact. | Medium; historical HOLDOUT-DTI is recorded above but no promotion. |
| 2 | MCP2: RTP magnetic band 2, isostatic gravity 13, basement depth 15. Cross-correlate bandpassed normal gradients and use peak lag/confidence. | Targets displaced geophysical edges and covered structures rather than coincident edge/ridge detectors; existing proposal is untested. | Dipping intrusive contact, remanent magnetization, survey-height seam. | Medium-high; deferred/outside SSP1 lane. |
| 3 | RBN3: conductivity 17, basement depth 15, elevation 12, gravity 13. Scale-normalized conductivity Hessian saddle plus a narrow neck at a gravity step. | Tests a covered-basin neck against a broad-basin null; differs from simple clay-cap/favorability multiplication, but overlap with peer saddle approaches is unresolved. | Saline groundwater channel or sedimentary facies boundary. | Low-medium; deferred/outside SSP1 lane. |
| 4 | RSC4: elevation 12, encoded K/Th/U, LiDAR step/coherence. Multi-scale persistent step conditional on low radiometric rank contrast. | Uses radiometric quietness as a nuisance control, not positive alteration fusion; catalogue-independent, but scarp methods exist in peers. | Fluvial terrace, agricultural grading, road cut. | Low; deferred/outside SSP1 lane. |

### Next actions (required before a future experiment)

1. Obtain an explicit coordinator-assigned single method paragraph and centrally resolve whether the dense calibration lattice is a registry item under the literal final-dot overlap stop. Do not self-exempt it.
2. Recover and authenticate the exact organizer template and all competition inputs; document provenance, hashes, license, and grid. Obtain the canonical content-addressed feature cache and invalidate it on any source change.
3. Repair/pin the shared evaluator centrally, with synthetic empty-truth false-positive tests; do not privately fork it. Use the shared evaluator, buffered whole-segment hide-and-recover folds, alpha 0.2 / beta 0.8 / 300 m triangular kernel, and visible-fault-only derived features.
4. Reconstruct the exact clean same-fold incumbent and canary every feature alone; prove no feature AUC >0.90 absent leakage explanation. Compare paired spatial-block intervals to that incumbent and stop on any registry breach.
5. Only a candidate that beats the incumbent on valid holdout and passes complete surface, final-dot, and exact-grid validator gates can go to a separate selector for the current authenticated weekly quota. No quota or upload is authorized by this review.

Official/manual references already maintained in `docs/SOURCES.md`: [DrivenData task and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition data page (login gated)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [USGS GeoDAWN dataset](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR submission 1391](https://gdr.openei.org/submissions/1391), [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [competition PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Official references establish context, not validation of the participant-mirrored data or model.

**Maximize P(Win):** conserve scarce slots and don't claim a speculative score. **Own the Outcome:** preserve negative evidence, identify the blockers, and don't present a duplicate as submission-ready.
