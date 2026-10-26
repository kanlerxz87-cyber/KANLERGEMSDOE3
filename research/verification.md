# Three-pass verification record — 26 October 2026

## Pass 1 — implement/review the requested work

- Inspected the starting commit: it contained only the one-line README. Integrated the concurrent main review and its pinned site evidence before continuing.
- Reviewed pinned source trees for GEMSDOE24/25/27/28/30/31/32/33/36 and directly fetched current owner Pages to flag changing or contradictory selector statements.
- Fetched official DrivenData task/About pages, official data tab (redirected to login), USGS GeoDAWN page, EPSG:32611 record and reference-solution README. The official leaderboard, GDR page and NLR PDF were not verified.
- Restored nine exact historical TIFFs plus an owner-mirror sample and labels into ignored `data/` for forensic learning only. No historic file was treated as a candidate. Verified all 9 SHA-256 values against pinned manifests and recomputed 72 directed Euclidean ≤3 px overlap comparisons.
- Built a prioritized historical scorecard (owner-reported claims only), no-submit decision, research hypotheses, official source notes, submission instructions and JSON card. No TIF was generated.

## Pass 2 — adversarial review and bug fix

- Confirmed every historical winner exceeds the 70% overlap stop; minimum cross-winner directed overlap is 86.718954%. Continuous surfaces/full registry are not present; their correlation remains unknown.
- Compared all nine historical rasters to the pinned sample footprint. Found the old audit’s whole-array range/finiteness checks could call finite zeros outside the footprint a format pass even though the official description requires null/NaN outside.
- Fixed the shared local audit/report path to use `scripts/validate_submission.py` against the sample mask. Added a regression test for zero-outside rejection and nodata-outside acceptance.
- Strict sample-mask result: 2/9 historical files pass; 7/9 fail because finite zeros are stored outside the footprint. This owner-mirror check is not a portal result or organizer authentication.
- Installed rasterio/numpy/scipy in ignored `.venv`; no global environment or Git-tracked dataset was modified. All downloaded audit rasters and labels remain ignored under `data/`.

## Pass 3 — full requirement reconciliation

- Ran `scripts/audit_rasters.py`, `scripts/build_site.py`, JSON parses, HTML/local-link checks, and the full unit suite: **15 tests pass**.
- Ran `scripts/validate_submission.py` against all nine historic files and the pinned owner-mirror sample. The range error’s cause for the user’s previously uploaded file remains unknown because its bytes/receipt were not supplied.
- Historical 0.2778, the user’s 0.3195/0.4413 leaderboard targets, and every per-site score remain owner-reported/unverified; score estimate is not estimable.
- No assigned method lane, official training feature stack, cached features, integrated shared evaluator/writer, complete raster registry, paired holdout evidence, or current slot receipt/quota was available. Therefore no candidate experiment, new TIFF, portal submission or slot selection occurred. The requested high-scoring unique submission is **not yet fulfilled**; the negative readiness/duplicate findings are the honest deliverable.
- PR #5, containing the evidence review, was merged to `main`; the session branch was fast-forwarded to concurrent `main` reviews and retained.

## Remaining work

Obtain the missing method paragraph/lane. Restore or verify authorized data access and the canonical shared cache/evaluator/writer; do not treat owner mirrors as organizer-authenticated. Restore the complete current registry. Then pre-register one of the hypotheses, run feature-alone canaries and buffered whole-segment holdout, test surface and final-dot uniqueness, validate the exact output against the official sample, and let a separate selector decide whether a weekly slot is available. No leaderboard projection is a substitute for an organizer receipt.
