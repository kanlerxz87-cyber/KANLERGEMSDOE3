> **Historical snapshot — superseded.** This earlier review predates the restored shared template, feature stack, and decisive positive-everywhere witness. Some data/uniqueness statements below are now stale. See the [current executive desk](index.html), [scientific review](review.html), and [current run card](data/current-run-card.json). The stop/no-submit decision remains in force.

# Competition submission guide

## Current answer: do not upload from this repository

There is no validated prediction TIFF in this checkout, so there is no file to download or submit. The fact that the competition accepts GeoTIFFs does not make historical files in other repositories approved or unique. Do not substitute a zero raster, rename an old file, or treat a format check as scientific validation.

## When a candidate clears all gates

### 1. Before opening the submission form

1. Obtain the official `sample_submission.tif` and required inputs through the enrolled team's authorized DrivenData data page. Do not bypass account authentication.
2. Run the shared whole-segment buffered hide-and-recover holdout and feature-alone leakage canaries. Record evaluator version, number of withheld positives, pooled `HOLDOUT-DTI`, and 95% CI. Compare against the predeclared control using the same splits.
3. Run both novelty checks against the complete named raster registry before placement and on final dots. Stop on any rank-correlation >0.90 or >70% candidate dots within 3 pixels of one registry raster. The current literal rule is blocked by the positive-everywhere witness; do not proceed without clarification.
4. Use the shared writer to generate a *new* candidate; validate the saved bytes, not just in-memory arrays. Require one band, float32, exact sample CRS/shape/transform, and finite values in [0,1] within the study footprint. The official wording says null/NaN outside bounds; the shared writer's all-finite project policy is a separate assumption. Record SHA-256 and validator output.
5. Only if every required gate is documented and the independent selector approves a weekly slot, mark `OK TO SUBMIT`. Experiments do not select a file or use a weekly submission slot.

### 2. Form steps (portal wording from the user-provided form text)

The user quoted the form as “New submission,” with a **File to submit** selector accepting a single-band GeoTIFF (`.tif`) or a `.zip` containing a single GeoTIFF, plus an optional short **Note** field. This field text is treated as user-provided UI evidence; the live account form was not accessed in this review.

After the file is approved:

1. Sign in to DrivenData and open the GEMS Prize Challenge.
2. Choose **Submit** → **Make new submission** (the public competition page's general how-to-compete instructions describe this sequence).
3. Select the exact SHA-verified approved `.tif` (or a ZIP containing exactly one GeoTIFF if the form requires ZIP), not an earlier or similarly named artifact.
4. Enter the exact unique submission name recorded in the run card and a concise note (at most 140 characters per the project protocol). Suggested note structure: hypothesis tag, dot count, holdout DTI + CI, and run identifier. Do not write an unverified projection as a score.
5. Confirm the displayed filename, submit, and preserve the resulting organizer receipt alongside a documented hash of the exact uploaded bytes. Do not assume the portal receipt itself includes a SHA-256.

### 3. Error: “Predicted values must be in range [0, 1]”

The exact cause of the previously reported error is unverified. Before any retry, inspect the saved TIFF for NaN/Inf, negative values, values above 1, and nodata/mask interpretation, and compare its CRS and grid with the official sample. Do not hide invalid outputs by clamping; repair the writer/inputs, rerun validation, and regenerate the SHA. Consult the current official format wording and portal behavior.

### 4. Current status

No file, name, note, estimated score, organizer receipt, or weekly-slot status is available. The appropriate action is to stop before the form. Refer to the [executive decision](EXECUTIVE_SUMMARY.md) and [machine-readable run card](../run-card.json).

Official references: [competition how-to-compete and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description, metric, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
