# Implementation and review log

Date: 2026-10-26 UTC. This is a record of work, not a candidate scoring receipt.

## Pass 1 — evidence, scientific protocol and reproduction

* Reviewed the competition problem, metric, official known-fault masking
  clarification, rules and source catalog. Separated user-reported historical
  claims from public leaderboard observations and actual candidate metrics.
* Restored four owner-mirror core files by pinned SHA and delegated preparation
  to the shared template. Preparation produced 19 bands, not the required cached
  feature stack. The sample mirror contains the existing-label positive mask;
  this discrepancy and lack of organizer authentication are recorded.
* Reopened nine pinned historical TIFFs; checked grid, binary masks, pairwise
  directional three-pixel overlap, common lineage and the spacing-five lattice.
  Results: [`portfolio-audit.json`](portfolio-audit.json). These are not a full
  live-registry or new-candidate pre-placement audit.
* Ranked four physical hypotheses and alternatives before modeling. No assigned
  lane or cache existed, so zero modeling experiments or canary/holdout claims
  were made.

## Pass 2 — implementation and adversarial review

* Implemented a fail-closed run-card gate, byte-bound local validation wrapper,
  reproducible data setup, static site builder, source feed and automated tests.
* Reproduced shared probability binarization and outside-footprint validator
  defects, filed [issue 37](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37)
  and [issue 39](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/39), and
  used the separate shared `gems32.submission.audit_geotiff` function for
  outside-footprint checks. No evaluator/writer fork was introduced.
* Verified on a historical H33 NaN raster that the pinned shared auditor reopens
  and checks actual saved bytes; that research-only file was not approved. Added
  tests for incomplete registry evidence, absent canaries, NaNs and out-of-range
  values, unauthenticated templates, score/evaluator mismatches, exact thresholds,
  stale feed parsing, local links, and missing/corrupted cache and mirror files.
* Actual preflight against `/tmp/gems-data` and `/tmp/gems-work`: all four owner
  SHA pins matched, `feature_stack.npy` absent, no assigned lane, exit 2 as
  intended. The `/tmp` paths are ephemeral.

## Pass 3 — site, usability and end-to-end checks

* Rebuilt generated pages; verified the builder's `--check` reports no drift.
  Ran the test suite: **28 passed**; 18 upstream Rasterio/Affine pending-
  deprecation warnings are present in synthetic tests. The seven shared-auditor
  integration cases use its hash-pinned source with grid-count constants adjusted
  for small synthetic fixtures; they test valid bytes, NaN, infinity, sentinel,
  out-of-range, outside-footprint and wrong-transform failures.
* Loaded the home page and all three secondary pages with headless Chromium at
  1440×1000 and 390×844. Both layouts showed nine rows and the no-upload verdict;
  no JavaScript/page errors, failed local responses or document-level horizontal
  overflow were observed. Added a mobile table-swipe hint and keyboard-focusable
  scroll region after reviewing the rendered page. The tests check internal links;
  they are not an availability guarantee for external sites.
* Exercised the live feed in the sandbox: all nine GitHub peer HEAD calls succeeded
  and showed changed commits relative to the immutable audit pins; DrivenData is
  outside sandbox shell egress and was marked stale/unavailable. A new peer HEAD
  does not mean that its TIFFs have been re-audited. The scheduled Pages workflow
  will attempt public refreshes, but subsequent deployment and network access must
  be verified from GitHub Actions rather than assumed.
* At this point, before merging the later parallel model run, the saved run card
  was **negative** with no candidate, SHA, candidate HOLDOUT-DTI, name or slot spent.

## Concurrent-main integration

While the PR was prepared, `main` advanced through several independent review
merges. Their source snapshots, project request, scripts, evidence, run cards and
15-test `unittest` suite were preserved. The previous active dashboard, README,
research and static generator were archived and linked rather than silently
replaced. The older review builder was redirected away from the active research
page and taught not to include ignored `__pycache__` bytes in its source manifest.
Their strict owner-mirror format audit found seven of nine selected historical
file variants had finite outside-footprint values; this is not a portal result.

After integration, **43 pytest tests passed** including the prior review's tests;
its standalone `unittest` suite also passed **15 tests**. The site builder passed
`--check`, and Chromium desktop/mobile checks were repeated. The scientific
verdict, zero experiments and no-upload decision did not change.

## Later parallel GPC-3 integration and byte-level stop

Another branch merged three reported experiments and a research TIFF while this
PR was in progress. Its source, run cards, model code, TIFF and earlier dashboard
are retained; its method was self-selected, not a lane explicitly assigned in the
user request, and its rebuilt stack was not the requested precomputed cache.
Canary evidence for the 59 baseline features was not documented in the parallel
receipt. We did not rerun its training or its reported HOLDOUT-DTI.

We independently reopened its SHA-bound saved TIFF and the pinned lattice.
All 37,654 candidate dots lie within 3 px of the lattice, violating the literal
70% stop; see `parallel-candidate-audit.json`. Against the owner mirrors, the
pinned shared auditor rejected outside-footprint compliance and nonzero
catalogue pixels. The outside-format conflict is not a claim of actual portal
behavior. The parallel report's nine-site pass is only a partial novelty check.
The old runner is archived and its CLI/final emission are blocked after its
three-experiment budget. The research file remains downloadable but is not
approved for submission; the active run card records the combined negative result.

Post-integration verification: **52 pytest tests passed** (including the
parallel session's original tests and synthetic lattice/runner regressions), and
**15 unittest tests passed**. There were 31 Rasterio/Affine pending-deprecation
warnings in synthetic fixtures. Browser checks again passed at 1440×1000 and
390×844, with no document overflow or local JS errors. The range-check CLI now
labels numeric checks as local, checks strict template-mask compliance separately
and does not claim a portal result: the research TIFF passed the all-finite
numeric range check but failed the strict mask check, as expected.
