# Submission guide — fail-closed

## Current decision

**There is no GeoTIFF in this checkout. Do not upload a file from this repository.** The current branch lacks the official sample grid, prediction writer, validation tooling, registry and competition data. This guide explains the required future workflow; it is not evidence that a file passes.

## When a candidate has passed all gates

1. **Select the exact artifact** named in the run card. Download the `.tif` (or a ZIP containing exactly one `.tif`) from the project's generated-artifact page. Do not use a report, preview, NaN/zeros alternate, stale version, or similarly named file unless the selector explicitly approves that exact SHA-256.
2. **Verify the local file.** Compare its SHA-256 to the signed/recorded run card and validator receipt. A different hash means stop. Confirm it is single-band float32 GeoTIFF and matches the official sample's CRS (UTM 11N / EPSG:32611), dimensions, bounds, resolution and affine transform. Confirm no NaN/Inf inside the footprint and all submitted prediction values are in `[0,1]`; verify outside-footprint nodata against the current official format and actual validator. Never “fix” a rejected file by blindly replacing nodata with 0, because that can change predictions and metric behavior.
3. **Confirm scientific permission.** Require a positive, same-evaluator buffered whole-segment `HOLDOUT-DTI` result with evaluator version, withheld-positive count and 95% CI; all leakage canaries addressed; and literal pre-placement and final-dot uniqueness below the 0.90 rank-correlation and 70% within-3-px stop thresholds. A format pass alone is not approval.
4. **Read the separate selector decision.** It must explicitly authorize this exact hash for a slot, after checking the current weekly cap. Do not infer authorization from “download”, “unique”, a score estimate, a historical page, or a successful local validator. This project must not silently upload or spend a slot.
5. **Use the competition page.** Sign in to the authorized DrivenData account; open DOE GEMS competition → **New submission**; choose the approved `.tif` (or single-TIFF ZIP); enter the unique portal name and a note of no more than 140 characters; review the selected filename and quota; then submit. The official submission form is the authority for acceptance.
6. **Archive the receipt.** Save the organizer's submission-page receipt and score. Label that result `ORGANIZER-CONFIRMED` only when the receipt records it. Archive the exact uploaded hash, name, note, UTC time, and selector/run-card IDs. A portal acceptance is not proof of high leaderboard performance.

## The reported `[0, 1]` error

The competition problem page specifies one prediction layer, float32, values between zero and one, and null/NaN outside the footprint. Check the exact saved bytes rather than the design surface: nodata, NaNs, infinity, scaling, dtype conversion, and accidental out-of-range values can be introduced by the writer or GeoTIFF library. Validate the entire in-footprint array after reopening the TIFF. The format requirements and portal's actual acceptance must both be satisfied; this repository has not tested either because it has no TIFF or competition data.

## Official references

- [Official problem, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
- [Official data page (login required in this environment)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official live public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
