# Submission guide

## Current decision: DO NOT SUBMIT

There is **no approved competition TIFF** to download from this project. A previously committed GPC-3 research TIFF and the historical references fail the requested uniqueness threshold; the prior bilateral experiment did not write a TIFF. Do not rename, perturb or upload any of them as a fresh entry. No current candidate leaderboard estimate exists.

## Required automated evidence before a future selector can approve a file

1. Resolve the missing parallel method lane and the full-footprint registry diagnostic described in the [scientific review](review.md). Restore the intended shared template and authorized organizer sample; confirm all data/code licenses.
2. Use the shared evaluator on buffered, whole-segment spatial hide-and-recover folds. Build catalogue features using visible faults only and mask visible pixels exactly. Run each feature's AUC canary; a value above 0.90 is a leakage stop unless disproved.
3. Compare against the current holdout incumbent on identical folds. Record pooled `HOLDOUT-DTI`, evaluator version, withheld positives and 95% CI, including paired improvement uncertainty. A leaderboard projection is not a score.
4. Before placement and after final dots, compare against the complete, frozen registry. Stop if **positive** rank correlation exceeds 0.90 or more than 70% of candidate dots are within 3 pixels of a registry dot set. Missing bytes or undefined comparisons do not prove uniqueness. The current shared interpretation treats every finite positive registry pixel as a dot, producing the documented saturation blocker.
5. Use the shared submission writer, then validate the **saved** TIFF against the verified sample: one float32 band; exact CRS, shape and transform; no NaN or invalid probabilities inside the footprint. The conservative local check also requires null/masked/NaN outside the sample mask and flags whole-grid raw non-finite or out-of-range values. Its result is not a portal acceptance.
6. Bind measured evidence to the exact TIFF SHA-256, unique filename and note of at most 140 characters. A complete schema alone is not scientific validation. Independently select a weekly slot only after verifying the account's actual remaining allowance. The [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), §§3.2–3.5, describes three submissions per week, but the live account quota has not been checked.

## Only after a file and slot are approved

1. Download the exact approved `.tif` from the project executive summary and compare its SHA-256 with the published run card. No such download exists today.
2. Enroll/sign in to [DrivenData](https://www.drivendata.org/competitions/306/competition-doe-gems/), select **Submit**, then **Make new submission**. The user-provided form text says it accepts one single-band GeoTIFF or a ZIP containing one GeoTIFF; the authenticated form was not accessed here.
3. Choose that exact unique filename. Put the run-card's short note in the optional **Note** field; the quoted form did not establish a separate name field.
4. Submit only after the separate selector authorizes the slot. Preserve the organizer response and bind the receipt to the uploaded filename and independently recorded hash. Only an actual submission-page receipt can support an `ORGANIZER-CONFIRMED` team score. Select one final submission for both rounds before the official deadline. The rules also require disclosing generative-AI use in the narrative and reproducible code/documentation for finalists.

## “Predicted values must be in range [0, 1]”

The cause is unknown because the failed upload's exact bytes and receipt were not supplied. Run `python scripts/validate_submission.py <verified-sample.tif> <candidate.tif>` on the exact saved file. Check raw NaN, infinity, sentinel values, negative values and values above one, along with the mask and geometry. Null/NaN outside the official bounds is described by the organizer; how the portal handles the mirrored irregular footprint mask is unverified. Do not blindly clamp or assume that either zero-outside or NaN-outside guarantees acceptance. The synthetic internal-mask regression test is a format experiment, not an approved candidate or portal test.
