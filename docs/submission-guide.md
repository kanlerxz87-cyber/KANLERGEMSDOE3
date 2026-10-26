# Executive submission guide

## Current decision: no TIF to upload

There is **no downloadable candidate in this repository**. Do not upload a historical site raster under a new name. The required competition rasters/tools are not present, so there is no way to certify strict `[0,1]` values, template grid, scientific holdout, hash, or uniqueness here. This page is ready to guide the workflow once an eligible artifact exists; it does not itself authorize an upload.

## What the official format requires

The official [GEMS problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) states the submission must be a single-layer GeoTIFF, 32-bit floating point, same projected coordinate system (EPSG:32611), resolution (100 m), bounds/grid as the training data, values from 0 to 1, and null/NaN outside bounds. Use the official `sample_submission.tif` as the ground-truth grid/template once downloaded through the authorized data page. Do not hard-code a shape or transform before inspecting that file.

The same page defines DTI with α=0.2 and β=0.8, using a triangular distance kernel supported to 300 m. A local holdout number is **not** an organizer score; only a score copied from a submission-page receipt can be labelled `ORGANIZER-CONFIRMED`.

### Fixing “Predicted values must be in range [0, 1]”

That error means the portal rejected at least one submitted prediction value. Before upload, inspect the **saved output** (not an in-memory precursor):

- one raster band, `float32`;
- every finite prediction **inside the competition footprint** is between 0 and 1, inclusive;
- no NaN/Inf in footprint cells;
- outside the competition bounds, follow the official null/NaN requirement and match the sample template's mask/nodata convention;
- exact CRS, bounds, dimensions, pixel resolution, and affine transform match the sample template;
- no unintended second band, integer conversion, scaling offset, or invalid numeric values.

Some site pages report that a portal error was avoided by setting outside pixels to zero. This is not equivalent to the official page’s stated null/NaN outside-bounds requirement. Do not change the mask encoding on anecdotal evidence alone; compare with the official sample and test an authorized validation route. A local preflight cannot guarantee portal acceptance.

## Local validation when the data and script are available

A fail-closed validator has **not** been included because there is no raster library, official sample, or candidate to validate in this checkout. Restore the shared competition template/tooling and run the shared validator/writer. At minimum, a byte-bound JSON receipt should record:

- candidate SHA-256 and filename;
- reference and candidate CRS, dimensions, transform, pixel size, band count and dtype;
- count of masked/outside cells and finite/NaN/Inf values inside/outside;
- finite min/max and out-of-range count inside the footprint;
- exact-grid and mask results;
- independent holdout + CI reference, uniqueness evidence, and final decision.

Do not call a file “OK to submit” merely because it opens in GIS or passes the range check. All preregistered scientific and uniqueness gates must also pass, and the selector must separately authorize it.

## Portal steps after a future candidate is approved

1. Open the official [DrivenData GEMS competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) and sign in.
2. Open **New submission**. Choose the exact approved `.tif` (or a `.zip` containing one GeoTIFF if the portal accepts that format).
3. Enter the unique submission name and a short provenance note of at most 140 characters. Do not claim a holdout score is an organizer score.
4. Review the weekly submission cap and selected filename before using a slot. The selector—not the experiment runner—chooses whether to spend it.
5. After the portal reports a score, save the submission-page receipt and bind it to the exact TIFF SHA-256. Only then label the number `ORGANIZER-CONFIRMED`.

## Future name/note example (not assigned to a candidate)

- Name pattern: `gemsdoe3-<lane>-<mechanism>-<date>-<short-hash>`.
- Note pattern: `Lane <ID>; <mechanism>; holdout <version>; research gate passed; <short hash>`.
- Current exact file/name/note: **none**. A future note must not be used for a historical raster or to imply a promotion that did not occur.
