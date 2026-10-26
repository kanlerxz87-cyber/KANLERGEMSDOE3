# Executive summary — nine focus sites

**Decision: no file in this checkout is currently approved to download and submit.** There is no GeoTIFF, no local competition data, no shared evaluator/writer, and no registry in this repository. The values below are reproduced from the requester’s supplied list. They are **OWNER-REPORTED / UNVERIFIED historical score claims**, not `HOLDOUT-DTI`, not `ORGANIZER-CONFIRMED`, and not score forecasts. The current site pages are mutable and several report newer, conflicting claims; inspect the linked pages and their receipts before relying on them.

## Highest historical score named per focus site

“File ID” is the submission identifier/name as supplied in the request; it is not an audited local file or a verified download URL. The exact TIFF bytes and score-to-file linkage are not available here. Therefore novelty cannot be certified. **Do not rename, copy, or upload these historical artifacts as a new unique prediction.**

| Site | Historical file/submission ID from request | Score claim from request | Evidence class here | Uniqueness vs all nine | Decision in this checkout |
|---|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | OWNER-REPORTED / UNVERIFIED | Unknown here; current site review reports historical near/exact duplicate relationships, not independently re-audited here | No submission file; do not resubmit historical ID |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | OWNER-REPORTED / UNVERIFIED | Unknown here; pages report H19-5 family overlaps/aliases | No submission file; do not resubmit historical ID |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | OWNER-REPORTED / UNVERIFIED | Unknown here; site pages contain differing registry scopes and newer status | No submission file; do not resubmit historical ID |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | OWNER-REPORTED / UNVERIFIED | Unknown here; current page reports broader registry conflicts and multiple negative/contradictory dispositions | No submission file; do not resubmit historical ID |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | OWNER-REPORTED / UNVERIFIED | Unknown here; site claims an H19-5 family duplicate among older artifacts | No submission file; do not resubmit historical ID |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | OWNER-REPORTED / UNVERIFIED | Unknown here; current site presents newer candidate claims and also records broad-lattice uniqueness conflicts | No submission file; do not resubmit historical ID |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | OWNER-REPORTED / UNVERIFIED; the site says no submission-page receipt binds this score to this raster hash | Unknown from this checkout. Current site reports an exact/subset relationship with D2.8 historical files, but literal registry audit is unavailable here | Highest historical claim in the supplied list, not a valid new candidate; no submission file |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | OWNER-REPORTED / UNVERIFIED | Unknown here; current site has many newer research rasters and conflicting registry counts | No submission file; do not resubmit historical ID |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | OWNER-REPORTED / UNVERIFIED | Unknown here; current site reports this historical family overlaps strongly with GEMSDOE32 | No submission file; do not resubmit historical ID |

### What explains the 0.2778 result—and can we beat it?

The only defensible explanation available in this review is a **hypothesis**, not an audited causal finding: the reported prediction appears to use a fixed, sparse set of 37,654 spatial dots and likely combines a geologic prior with probability mass placed near plausible fault structures. On this task, the official metric gives a triangular distance credit out to 300 m and weights false negatives more heavily than false positives (`α=0.2`, `β=0.8`). A spatially broad, strategically placed map can therefore outperform a visually precise but sparse trace map on the public hidden-fault sample. That mechanism is plausible, but we cannot attribute the score to it without the exact raster, method, fold-local ablations, and the organizer receipt.

There is no reliable evidence here that `0.2778` is a leaderboard high, that it is organizer-confirmed, or that a new candidate would score higher. The requester separately supplied `0.3195` as a current high score, also unverified in this checkout. Do not project either number onto a holdout score. A score estimate for a future artifact is **not estimable** until the same frozen evaluator is run on leakage-controlled spatial holdouts and calibrated against receipt-bound organizer scores.

### Irregularities requiring review

1. **Score provenance:** GEMSDOE32’s current page labels 0.2778 owner-reported and says the repository lacks a submission-page receipt connecting the score to the TIFF hash. Therefore this review does not call it `ORGANIZER-CONFIRMED`.
2. **Changing site state:** site pages fetched for this review contain later 2026-10-26 experiment claims than the historic list in the request. Their numbers use different evaluators, withheld-positive counts, folds, and registry scopes. They cannot be pooled/ranked as one scorecard.
3. **Conflicting upload decisions:** GEMSDOE27 and GEMSDOE31 pages contain “approved” selector sections while other current pages and site sections apply literal lattice/registry uniqueness rules that block uploads. These are source-owner claims, not a shared audited decision. This repository does not inherit their approval.
4. **Duplicate risk:** GEMSDOE24/25/30/31/32/33 site pages report H19-5/D2.8 family duplication or subset relationships. Those claims need independent byte/pixel checks against all registry rasters; they are sufficient reason not to assume the historical list is unique.
5. **Submission schema:** the official task page says outside-bounds values should be null/NaN. Several site pages advocate all-finite zero-outside rasters to avoid a reported portal range error. These claims are in tension; test the chosen encoding against the official sample and authorized validator. A local format pass is not proof of portal acceptance.
6. **No local source files:** only README exists at the base commit. Neither website binaries nor the authenticated competition data are present locally, so all source-site artifact comparisons are explicitly **not reproduced** here.

## Candidate download table — current state

| File to download | Score estimate | Unique vs listed sites? | OK to submit? |
|---|---|---|---|
| **None. No new TIF exists in this repository.** | **Not estimable.** User-supplied historical values above are unverified claims, not estimates. | **Unverified:** this checkout has no rasters or complete registry. | **NO.** No local artifact, no holdout result, no hash, no format receipt, no selector decision. |

When a candidate eventually exists, name it with a new descriptive ID; submit only if the frozen holdout wins with a paired 95% CI over the same-evaluator baseline, every single-feature canary is ≤0.90 AUC or explained, surface and final-dot novelty pass literally, its exact GeoTIFF passes format validation, and an independent selector approves it. Weekly-slot selection remains separate.
