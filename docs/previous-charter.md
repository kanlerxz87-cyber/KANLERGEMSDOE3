# GEMS fault-discovery research — project charter

> **Start here at the beginning of every project session.** This README is the standing brief and decision policy for this repository. It condenses the project instructions into durable, auditable requirements; it is not a verbatim transcript of the original chat prompt.

## Mission

Develop a scientifically defensible, reproducible, and competitive method to identify **previously unmapped geological faults** in the DOE/NLR GEMS Prize Challenge region. The competition target is fault presence, not proof of geothermal vents. Geothermal interpretation is a downstream scientific question and needs independent evidence.

Maximize the probability of a valid, scientifically useful result (Arena's “Maximize P(Win)”) while owning the complete outcome: inspect inputs, test assumptions, validate outputs, report failures, and never label a projection or an owner-reported number as an official score.

## Non-negotiable operating rules

1. **Use the shared template and shared tooling.** Reuse its cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Do not create a private fork of shared evaluators or writers. Fix a shared-tool defect in the template and document the fix.
2. **Spatial holdout before submission.** Hide whole fault segments with a spatial buffer. Derive every catalogue-dependent feature from visible faults only; mask visible fault pixels exactly. Score pooled DTI with α=0.2, β=0.8 and a 300 m triangular kernel. Use a 95% confidence interval and report evaluator version and withheld-positive count.
3. **Leakage canary.** Evaluate each feature alone on the same holdout before trusting it. AUC >0.90 is leakage until demonstrated otherwise.
4. **Unique-lane guard.** Check candidate surface rank-correlation with every registry raster before placement and final-dot overlap after placement. If absolute correlation exceeds 0.90, or >70% of candidate dots lie within 3 pixels of any one registry raster's dots, mark duplicate and stop. Do not copy a prior submission. A unique filename or hash alone is not novelty.
5. **Every number has provenance.** Label measured validation results `HOLDOUT-DTI` (evaluator, withheld positives, 95% CI) or copied receipts `ORGANIZER-CONFIRMED`. Label user/site reports as **unverified claims**. A projection is never a score.
6. **Bounded work.** Stop after three experiments or two hours, whichever comes first. Do not select a competition submission or spend a weekly slot. Promotion to a real submission slot is a separate selector decision.
7. **Fail closed.** No TIF is approved unless saved bytes pass an automated validator: one-band float32 GeoTIFF, exact sample-template CRS/shape/transform, finite values in [0,1] inside the footprint, and null/NaN only outside. Record SHA-256. Clearly distinguish “download for audit” from “OK to submit.” Never emit a fabricated or placeholder submission.
8. **Research discipline.** Propose 3–5 hypotheses before experimentation, name the physical signature and confounder, compare against documented prior approaches, and cite official sources. If external data is necessary, name an official free source and verify availability before treating the idea as viable.

## Submission contract (official problem page)

The official challenge describes fault prediction as pixel-wise confidence/probability values in a GeoTIFF, in EPSG:32611 at 100 m, on the training grid, with a single float32 layer and values in [0,1]; outside-bounds values are null/NaN. Its public metric is distance-weighted Tversky with α=0.2, β=0.8 and a triangular 300 m support kernel. See the [official problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and the [organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution). These are format/method facts, not evidence that any particular candidate scores well.

## Current repository state and decision

The initial checkout contained no model code or data. The current branch now includes tests, offline audit/validation scripts, archived upstream evaluator/writer source copies, sample/template/label mirrors, and nine historical winner TIFFs in ignored `data/` for forensic analysis. It still lacks an organizer-authenticated feature stack, complete registry, integrated candidate pipeline, candidate TIFF, and valid spatial holdout. The historical files are not approved for reuse; their audit does not authorize submission. Therefore no valid candidate experiment or downloadable submission can be produced here yet. **Current decision: DO NOT SUBMIT; no new TIFF is offered for download.** Do not infer a score from historical website claims.

The initial review and all blockers are recorded in [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md), the nine-site comparison in [`docs/SITE_REVIEW.md`](docs/SITE_REVIEW.md), ranked preregistered hypotheses in [`docs/HYPOTHESES.md`](docs/HYPOTHESES.md), and the step-by-step portal workflow in [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md). The official-source register is [`docs/SOURCES.md`](docs/SOURCES.md). The machine-readable end-of-run card is [`run-card.json`](run-card.json).

### Minimum prerequisites for the next valid experiment

- Restore/locate the shared template and its cached feature stack, holdout evaluator, writer, and tests **in this branch/workspace**, or identify the approved shared remote/template to extend.
- Obtain the competition-provided training features and fault labels, plus an authorized sample-submission/template and provenance. The competition data page redirected to login during this review. Existing label/template mirrors are third-party forensic copies, not an authorized competition package.
- Supply the full registry rasters for the uniqueness checks, plus any manifest mapping registry name to raster/hash. Do not treat a list of scores or repository pages as pixel-level duplicate evidence.
- Run the canaries, spatial holdout, candidate/final-surface novelty checks, and exact saved-byte validator; only then report a measured result.

## Session checklist

- [ ] Read this charter and the status in the executive summary.
- [ ] Confirm branch, worktree, data provenance, and tool versions.
- [ ] Check the current official competition rules, leaderboard, and slot quota where accessible; timestamp any changing values.
- [ ] Register 3–5 hypotheses and intended experiment budget before execution.
- [ ] Run only the pre-registered holdout/canary/uniqueness workflow.
- [ ] Produce one JSON run card, including negative results. Do not select or upload a submission in the experiment step.
