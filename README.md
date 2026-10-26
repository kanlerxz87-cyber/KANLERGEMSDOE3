# KANLERGEMSDOE3 — DOE GEMS fault-discovery workbench

> **Read this standing brief before every project change.** The goal is reliable, auditable scientific work that improves the probability of a strong DOE GEMS competition result—not the production of a TIFF merely to have one.

## Persistent work order

1. **Competition target.** Develop predictions of faults in the DOE GEMS / GeoDAWN region. Treat the official competition description, data specification, metric and rules as the source of truth. Keep a clean, auditable inventory of scientific claims and link primary sources.
2. **Research before code.** Before implementing a candidate, describe 3–5 geological hypotheses. For each, name the existing layer(s), physical signature/transform, why it may reveal a catalog-missing fault, and what is materially different from work already recorded. Rank by expected value (qualitative unless supported by evidence) and implementation cost. If “new” cannot be established from the complete registry/history, say so.
3. **Stay in the assigned lane.** Compare the candidate surface before placement and final dots against the pinned registry. Stop and record a duplicate if absolute rank correlation exceeds 0.90 or more than 70% of candidate dots are within 3 pixels of any one registry raster. Do not rename, perturb, or re-encode another submission to claim novelty.
4. **Reuse shared tooling.** Use the template’s cached feature stack, shared `evaluate_holdout.py` and `submission_writer.py` when available. Holdout is hide-and-recover: withhold whole fault segments with a buffer; build every catalogue-derived feature only from visible faults; mask visible faults pixel-exactly; evaluate pooled distance-weighted Tversky (alpha 0.2, beta 0.8, 300 m triangular kernel). Fix a shared-tool defect in the shared template, never in a private fork. Do not invent substitute results when these files or data are absent.
5. **Leakage checks.** Test each feature alone on the same holdout before trusting a model. AUC > 0.90 is a leakage warning until disproven.
6. **Evidence labels.** Label every score as `HOLDOUT-DTI` (evaluator version, withheld-positive count, 95% CI) or `ORGANIZER-CONFIRMED` (copied from the submission-page receipt). Label owner-provided historical numbers `OWNER-REPORTED`. A projection is never a score. Do not claim a leaderboard estimate unless it is calibrated and validated; otherwise say `not estimable`.
7. **Fail closed on files.** A download is not permission to submit. Before saying a TIFF is safe to upload, validate the exact saved bytes, single-band GeoTIFF, float32, required CRS/shape/transform, footprint/nodata behavior, no NaN inside the footprint, and predictions in [0, 1]. Record SHA-256 and a short unique portal name/note (≤140 characters). The scientific holdout gate and literal uniqueness gate must also pass. Slot selection is separate and subject to the competition’s current cap.
8. **Budget and honesty.** Stop after at most 3 experiments or 2 hours per run card. Negative results are valid deliverables. Do not spend or claim a weekly slot without the separate selector decision. Do not fabricate a TIFF, score, receipt, data access, validation, or scientific conclusion.
9. **Autonomy and values.** Automate checks where data and tooling permit; do not require human geological inspection for a machine gate. Flag blockers that genuinely require account access. Apply **Maximize P(Win)** by protecting scarce slots and **Own the Outcome** by reporting failures, uncertainty, and next actions directly.
10. **Research archive.** Preserve official, free/public data sources and their license/provenance. Do not fetch/login-bypass competition data. Keep large datasets and artifacts out of Git unless the project’s storage policy requires them.

## Current checkout status (2026-10-26)

At the start of this review, the checkout contained only the original README and `.git`; this update adds documentation and a static landing page, but no feature stack, labels, training data, `evaluate_holdout.py`, `submission_writer.py`, tests, interactive application, cached registry, or TIFF. Therefore **no candidate was tested, no holdout score was measured, and no submission TIFF can honestly be generated or approved here**. The competition data endpoint redirects to DrivenData login in this environment. See the [project landing page](index.html), [review and evidence report](docs/executive-summary.md), and [submission guide](docs/submission-guide.md) for the nine-site audit, source links, hypotheses, limitations, and next steps. GitHub Pages publishing is not configured or verified by this checkout.

## Primary sources

- [DrivenData problem description, metric, and GeoTIFF format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
- [DrivenData data download page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login required from this environment
- [Official live public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- [INGENIOUS project, Great Basin Center for Geothermal Energy](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)

## How to continue

1. Obtain competition data through an authorized DrivenData account and place it under the agreed `data/` path; preserve the original sample submission and metadata.
2. Bring in or implement the shared template’s cached features, segment-buffered evaluator, writer, and registry audit in the shared project (not a fork), with tests.
3. Pin the nine-site registry rasters and their metadata/hashes; reconcile conflicting site statements before any uniqueness claim.
4. Preregister no more than three experiments, run leakage canaries, evaluate candidate and same-run controls, and publish the complete run card whether the outcome is positive or negative.
5. Only after holdout, strict uniqueness, and byte-level format gates all pass, let the separate slot selector decide whether an upload is worth the weekly cap.
