# KANLERGEMSDOE3 — DOE GEMS research & submission readiness

> **Current decision: NOT READY TO SUBMIT. No competition GeoTIFF has been generated, validated, or approved in this checkout.** This repository currently has no competition data, model, cached feature stack, holdout evaluator, submission writer, or registered raster inventory. Do not upload a file from this repository.

**Start every project session here.** Read this charter before running an experiment. The goal is to discover previously unmapped faults that are useful to geothermal exploration, while maximizing the chance of a scientifically defensible competition result—not to optimize a misleading local proxy or relabel an old raster.

## North star and working rules

- **Maximize P(Win):** spend no weekly slot on an idea that has not beaten a same-evaluator spatial holdout baseline and passed format and cross-registry uniqueness gates.
- **Own the Outcome:** report negative results, data/access blockers, validation failures, and source disagreements. Never call a projection a score.
- **Discover faults, not catalogue pixels:** use whole-segment hide-and-recover evaluation; exclude withheld segments and buffers from every catalogue-derived feature; mask visible catalogue faults pixel-exactly.
- **Respect the experiment lane and budget:** the previous request specified a single method paragraph, but no method paragraph or lane definition was supplied in this checkout. Do not infer one. The previous protocol caps work at 3 experiments or 2 hours; this review ran **zero** experiments because required assets/tools are absent.
- **Uniqueness is a hard stop:** check the probability surface before placement and final dots against every available registry raster. Stop if absolute rank correlation exceeds 0.90 or if more than 70% of dots fall within 3 px of any one raster. The inventory is currently absent, so uniqueness is unverified.
- **Leakage canary:** evaluate each feature alone on the spatial holdout; AUC > 0.90 is leakage until investigated.
- **No fabricated evidence:** label metrics as `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` with a submission-page receipt. Historical site figures supplied by the requester are marked `OWNER-REPORTED / UNVERIFIED` in the review.
- **No data or tool substitution:** the requested cached stack, `evaluate_holdout.py`, and `submission_writer.py` are not present. Do not silently recreate them as a private fork. Restore the shared template/tools first.

## Read first

**Focus sites:** GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36. The supplied highest historical claim is GEMSDOE32 / `h33-h33-2-b2` at 0.2778; the separately supplied current-leader figure is 0.3195. Both remain unverified here. See the site-by-site evidence table, exact file IDs, source links, irregularities and “OK to submit” decision in the executive summary.

1. [Executive summary and nine-site historical comparison](docs/executive-summary.md) — clear file IDs, score evidence, uniqueness, and submit decision.
2. [Submission guide](docs/submission-guide.md) — official format, local preflight, and portal steps.
3. [Ranked hypothesis and validation plan](docs/research-plan.md) — five testable candidates and why none was run.
4. [Evidence and source register](docs/sources.md) — official references, what each supports, and limitations.
5. [Run card](evidence/current-run-card.json) — machine-readable state of this review.

A compact landing page is available at [`index.html`](index.html). GitHub API reports Pages enabled for the public repository from `main` / root at `https://kanlerxz87-cyber.github.io/KANLERGEMSDOE3/`; this branch’s new pages will publish after merge/build.

## Immediate blockers (verified against this checkout)

- `git ls-tree -r HEAD` contains only `README.md`; there is no `data/`, no feature stack, no template, and no analysis or validation scripts.
- The official DrivenData data tab redirected to its login page during this review. No authenticated session or input files are available in this checkout. Do not invent a bypass; access must be provided through an authorized environment.
- `rasterio` is not installed in the current Python environment. The preflight guide documents its install; no GeoTIFF can be locally checked without it and the official sample/template.
- The currently cited competition problem page defines a 100 m single-band `float32` raster in EPSG:32611, with values in `[0,1]`, matching bounds/grid, and null/NaN outside the bounds. It defines DTI with α=0.2, β=0.8 and a 300 m triangular distance kernel. See the official links in [sources](docs/sources.md).
- The user-provided value `0.3195` and the nine-site historical values are not independently verified leaderboard receipts in this checkout. The GEMSDOE32 page itself labels `0.2778` as owner-reported and says a receipt binding the score to the raster hash is absent.

## Required data/tool handoff before experiments

Restore the official authorized competition inputs into `data/` and the original shared template/evaluator/writer into their expected project location. Then record file hashes, CRS, shape, affine transform, bands and nodata before use. Confirm the following are actually present before running the plan:

- `training_features.tif`, `labels.tif`, and `sample_submission.tif` (or the official names currently supplied by DrivenData);
- official feature descriptions/band mapping, catalogue vectors/raster, and the data-license/terms record;
- the shared cached feature stack, `evaluate_holdout.py`, `submission_writer.py`, and the full registry of historical/parallel rasters;
- an explicitly selected lane/method paragraph, fixed split definition, and current same-evaluator baseline;
- an organizer receipt if an official score is to be cited as confirmed.

The task requester previously asserted that a download script exists, but it is **not in this checkout**. Do not claim it ran. Do not create a fake sample, a placeholder TIF, or a numeric “leaderboard estimate.”

## Session protocol

1. Read this README, then check `git status`, data inventory, evaluator version, registry manifest, and the current competition page/submission receipt.
2. Freeze a dated hypothesis and the ≤3 experiment/≤2 hour budget before analysis.
3. Run feature-alone leakage canaries; then the buffered whole-segment hide/recover holdout (visible-only catalogue features; exact visible-fault masking; pooled DTI α=.2/β=.8; triangular kernel 300 m). Record withheld-positive count and geographic-block 95% CI.
4. Run pre-placement surface uniqueness; stop and log a duplicate if `|Spearman| > .90` or >70% of candidate dots are within 3 px of one registry raster. Recheck final dots after placement.
5. Reuse the shared writer and preflight against the official sample grid. Save byte-bound SHA-256 and JSON receipt.
6. An independent selector may promote only after all gates pass. The experiment itself never spends/selects a weekly portal slot.
7. Report a one-line decision: `promote`, `negative`, or `blocked`. A negative/blocked result is a deliverable; never dress a projection up as an estimated score.

## Review/implementation passes completed

- **Pass 1 — inventory:** confirmed a one-file checkout with no data or runnable pipeline; checked the official task, metric, CRS, submission format, USGS GeoDAWN data-release information, and current target-site landing pages.
- **Pass 2 — evidence audit:** separated owner-reported historical scores from organizer-confirmed results; flagged conflicting current site claims and the absence of local files/evaluator/registry.
- **Pass 3 — safeguards and next work:** documented ranked testable ideas and validation gates, added an explicit no-submit guide and a fail-closed, machine-readable run card. No experiment or TIF was fabricated.

## Known limitations

No local data or authenticated competition download; no supplied cached stack, shared scripts, or registry; no confirmed live leaderboard receipt; no validated score estimate; no trained model; no candidate TIFF; no cross-site pixel-level uniqueness audit; updated Pages build is pending after merge. These are blockers, not assumptions to fill with guesses. Suggestions and authoritative source links are in the linked pages above.
