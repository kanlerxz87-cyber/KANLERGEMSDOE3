# Submission guide

**Current verdict: NOT OK TO SUBMIT. No new candidate or filename exists.**
The historical TIFF links in the executive summary are references only. A
renamed previous TIFF is not a new, genuinely unique candidate.

## Required automatic gates before any download is enabled

1. Assign exactly one method lane and resolve the literal pre-placement
   registry stop explicitly; do not exclude dense prior surfaces or change a
   threshold without authorization. Check **every accessible registry raster**
   for surface Spearman >0.90 or forward dot overlap >70% within 3 pixels.
2. Fix/review the shared fold builder upstream, hide whole original fault
   segments with local buffers, rebuild all catalogue-derived features from
   visible faults, and mask visible faults pixel-exactly in scoring. Every
   feature is a leakage canary; oriented AUC >0.90 stops the run pending audit.
3. Compare the candidate and same-evaluator best on identical folds using
   pooled 300 m triangular-kernel Tversky (`alpha=0.2`, `beta=0.8`). Report
   **HOLDOUT-DTI**, evaluator version, withheld positive count, and paired
   spatial 95% CI. A holdout score is not a leaderboard score.
4. Recheck the final dot raster against the full accessible registry, and run
   the saved-byte single-band float32/georeferencing/range/validity-mask gates
   against the official reference. Record SHA-256. Do not normalize sentinels,
   hide NaNs, or assume a local format pass means portal acceptance.
5. Run the separate promotion/weekly-slot selector. Only it can authorize a
   slot; this research workflow never auto-uploads.

## If a future file is promoted

- Give the *new* artifact a unique, descriptive filename such as
  `gems-<lane>-<UTC-date>-<hash-prefix>.tif`; derive the hash prefix from the
  actual saved bytes. This is a naming pattern, **not** a current filename.
- The run card must provide a truthful note of at most 140 characters, without
  representing a holdout or projection as an organizer score. No final note is
  assigned while the verdict is negative.
- Open the official [submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/),
  sign in, choose **Make new submission**, upload the exact approved TIFF (or
  ZIP containing only it), and enter the provided note. Confirm the current
  allowance on that page before using a slot.
- Preserve the exact local file hash and the organizer's submission-page
  receipt together. A public leaderboard ranking alone does not identify the
  file and cannot establish the attribution.

See the [official problem/format description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
and [source register](sources.md). The previous `[0, 1]` upload error is not
diagnosable without the rejected file or receipt.
