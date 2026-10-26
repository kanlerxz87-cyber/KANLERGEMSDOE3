# Executive portfolio review

**Decision:** no newly generated file in this checkout is cleared for upload. The
project did **not** spend a weekly slot. A file with a different hash, a valid TIFF,
or a favorable forecast alone is not evidence of a better or protocol-unique
submission. The nine files below are prior submissions linked **for research only**.

The highest claim in the user's nine-site list is GEMSDOE32's H33-B2, **0.2778
USER-REPORTED / UNVERIFIED**, not an organizer-confirmed submission-page receipt.
The [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
showed **0.4437** at its top when our research tool retrieved it on 2026-10-26 UTC;
that is a **PUBLIC-LEADERBOARD OBSERVATION**, not a receipt for any of our files. It
may change. The conflicting 0.3195 and 0.4413 values in the prompt are historical
claims, not current observations. There is no calibrated prediction of any future
leaderboard result in this review.

## Exact-byte results

The [machine-readable audit](../evidence/portfolio-audit.json) reopens nine pinned
historical TIFFs against the SHA-verified owner-mirror template and labels. It checks
finite binary values in the footprint, grid identity, exact pixel-mask aliases,
full-footprint binary rank correlation, and the **directional** fraction of each
file's dots within three pixels of each of the other eight files. The audit does not
reconstruct the pre-placement surfaces or check every current registry file; the
user-requested all-registry rule therefore remains stricter. Downloads and exact
pinned source hashes are in the [site's table](../docs/index.html#portfolio).

| Site | Historical claim, not a verified score | Final-dot uniqueness within the audited nine | Conclusion |
| --- | --- | --- | --- |
| GEMSDOE24 | 0.2477 USER-REPORTED | No; 100% near GEMSDOE25 | Do not resubmit |
| GEMSDOE25 | 0.2600 USER-REPORTED | No; identical in-footprint mask to GEMSDOE30 | Do not resubmit |
| GEMSDOE27 | 0.2449 USER-REPORTED | No; 98.02% near GEMSDOE24 | Do not resubmit |
| GEMSDOE28 | 0.2710 USER-REPORTED | No; 100% near GEMSDOE25 | Do not resubmit |
| GEMSDOE30 | 0.2600 USER-REPORTED | No; identical in-footprint mask to GEMSDOE25 | Do not resubmit |
| GEMSDOE31 | 0.2708 USER-REPORTED | No; 100% near GEMSDOE25 | Do not resubmit |
| GEMSDOE32 | 0.2778 USER-REPORTED | No; 100% near GEMSDOE36 | Do not resubmit |
| GEMSDOE33 | 0.2632 USER-REPORTED | No; 99.71% near GEMSDOE27 | Do not resubmit |
| GEMSDOE36 | 0.2750 USER-REPORTED | No; 97.58% near GEMSDOE27 | Do not resubmit |

These numbers are a comparison of historical *claims*, not estimates and not
organizer-confirmed. “No” above means the stated nine-file **final-dot** comparison
failed; it does not say the archived files have the same SHA. Within-3-pixel overlap
is asymmetric: the denominator is the dots in the row's file.

## Why H33-B2 plausibly did better

We independently verified these relationships on the pinned bytes and mirror labels:

* The GEMSDOE25/30 D2.8 raster contains 44,090 positive cells. GEMSDOE31's R1 has
  40,199 and equals D2.8 after retaining pixels more than one pixel from the
  catalogue. H33-B2 has 37,654 and equals D2.8 after retaining pixels more than two
  pixels from the catalogue. GEMSDOE36's file contains every H33 dot plus 1,200.
* The [organizer's metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)
  uses a 300 m triangular kernel and DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw).
  Spacing predictions and removing low-yield dots **can** lower weighted false
  positives while preserving much of the useful coverage. This is a plausible
  explanation, not a causal proof. Hidden labels and byte-bound organizer receipts
  are unavailable, so the actual marginal TP/FP/FN effects and cause of the score
  differences cannot be identified.
* [DrivenData staff state](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2)
  that pixels corresponding to existing known faults are excluded from scoring in
  both rounds. This does **not** establish that a 200 m exclusion around them is
  automatically optimal; nearby undiscovered faults may still matter.

A method can in principle exceed the reported 0.2778; this review has **not**
demonstrated one or established its probability of beating the public leader.

## The literal registry obstruction

The pinned spacing-five calibration lattice has 206,895 positive cells. Its
three-pixel disk covers **5,160,724 of 5,167,373** footprint cells (99.8713%); only
6,649 footprint cells are outside that disk. If each candidate dot occupies a
unique cell, any candidate with 37,654 dots would need at least 11,297 dots outside
that disk to keep overlap at or below 70%, but only 6,649 such cells exist. The
necessary maximum is 22,163 dots; other registry rasters and geological constraints
can only make the feasible set smaller. This is a mathematical necessary bound,
**not** a proof that a lower-budget detector will pass or score well. We did not
silently exempt the lattice. See the [exact audit](../evidence/portfolio-audit.json).

Several sibling pages advertise approval after checking a narrower/discrete-only
registry (for example [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/)
and sections of [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)).
Those claims conflict with the literal all-registry instruction here. Do not
inherit a sibling's approval without the full current snapshot and the separate
selector. Sibling repositories are changing concurrently; a pinned audit is not a
live full-registry scan.

## Data and tool irregularities

* Four core files were restored using the [shared manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/07806249f4ed3efe70b4fbf866183c32392b7853/registry/data_manifest.json)
  and their SHA-256 hashes checked. The shared prepare script ran successfully and
  generated [this receipt](../evidence/mirror-preparation.json). Hashes prove the
  mirrors are internally consistent, **not** that DrivenData authenticated them.
* The mirror sample has exactly the same positive-pixel mask as the mirror labels,
  whereas the [official description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format)
  describes the sample as predicting total absence. Treat that as a provenance
  discrepancy; use it as a grid/footprint reference only, not as a prediction.
* The published template does not include its precomputed `feature_stack.npy`.
  The prompt also refers to an assigned single method paragraph that is absent.
  These are blockers to a new conforming lane run; we did not rebuild the stack,
  perform a geological experiment, or fabricate canary/holdout evidence.
* The shared CLI evaluator and writer silently turn any positive probability into
  1. This was reproduced and [reported upstream](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37).
  Until fixed, use them only for confirmed binary arrays; do not privately fork
  them or claim a probabilistic score from them. The separate `check_submission.py`
  also fails to check outside-footprint values; we reproduced that on a small
  synthetic grid and [reported it upstream](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/39).
  Our readiness wrapper delegates to the shared `gems32.submission.audit_geotiff`,
  which does check that condition, rather than relying on the incomplete CLI.
* The user's portal range error is real, but its cause is unverified. Check every
  in-footprint value, finite state, nodata and sentinel. The written rules ask for
  null/NaN outside the bounds; some sibling all-finite files claim portal safety,
  but this does not establish acceptance. No candidate was created or validated in
  this session.

## Next steps

1. Obtain a declared lane and a hash-pinned published copy of the shared stack (or
   an explicit revision to the reuse rule). Confirm the template tool defect is
   fixed upstream or limit the candidate to binary masks.
2. Freeze the full current registry, including calibration/dense references, then
   run the preregistered primary hypothesis within the 3-experiment / 2-hour cap.
   Check individual canaries, fold-local features and exact pre/final uniqueness.
3. Compare the new candidate to the **same evaluator and folds** with a paired
   spatial-block confidence interval. A mapped-fault holdout is a proxy, not a
   leaderboard score or a calibrated forecast.
4. If all evidence and byte-level format gates pass, pass the file to a **separate**
   selector. This session cannot verify remaining account quota and has not picked a
   slot. The [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) state
   three submissions per week, but check the current submission page before use.
