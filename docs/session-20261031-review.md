# Repository review — 31 October 2026

## Decision at a glance

**DO NOT DOWNLOAD OR SUBMIT any TIFF from this repository. No candidate passed all scientific, novelty, format, provenance, and selector gates. No competition slot was used.** The public Pages root previously exposed an inherited geofault TIFF as a download even though its archived run/validator records were contradictory and its release status was negative. This review fixes the generator so the exact TIFF is now hash-bound in quarantine and no TIFF/ZIP download link is rendered on the active executive summary, guide, or submission page. The TIFF remains preserved for audit; it is not a recommendation.

Current machine-readable card: [evidence/session-20261031-run-card.json](../evidence/session-20261031-run-card.json). The updated public summary is generated from pinned evidence by `scripts/build_site.py`.

## Pass 1 — inspect and implement

- Read `README.md`, the verbatim request in `PROJECT_PROMPT.md`, `PROJECT_REQUEST.md`, `AGENTS.md`, the latest prior reviews/cards, current site builder, data manifests, evidence, tests, and the five preregistered hypotheses.
- Confirmed there is no assigned single-method lane. The preserved session clock started 27 October and is expired; it was not reset. No geological experiment or TIFF was produced during this review.
- Confirmed core rasters and the canonical feature cache are absent in this checkout (`data/` contains manifests only); do not rebuild the cache privately.
- Ran the fail-closed readiness/preflight checks. Research and submission readiness are false; no leaderboard estimate is available.
- Found a concrete site integrity defect: `docs/downloads/kanler-geofault-propensity-20261029T031629Z-f705bdebde7e-nan.tif` was neither in the historical audit inventory nor the active quarantine inventory. The source card marks upload false, and its archived validation metadata contains inconsistent booleans; the active root HTML nevertheless advertised “Unique TIFF ready to download.”
- Extended the active builder to hash-bind this exact artifact and verify its ZIP's single-member byte identity, include it in the quarantine inventory, and present it only as blocked history. Added regression tests and rebuilt the checked-in Pages output. No historical file was deleted or altered.

## Pass 2 — adverse checks

- The shared-template lock passes integrity verification for all 13 pinned files. Separately, the synthetic operator audit fails as expected: the pinned shared evaluator drops false-positive mass in an empty-truth cell; soft-input behavior is also unsuitable. This is a software/evaluator defect, **not** evidence that any prior official competition score is wrong.
- Before the site fix, `build_site.py --check` and the suite exposed the missing quarantine inventory. After adding hash binding, site generation/check passes.
- Re-ran the full tests. Result: **331 passed, 9 skipped**. Earlier test failures from the artifact inventory were fixed; the pre-fix failure count is not the final status.
- Desktop/mobile Playwright smoke passed across the root desk, all nine site pages, and the research archives. GitHub freshness states were mocked for regression coverage; this was not live leaderboard verification. The new check confirms the legacy geofault row has no download link.
- Checked the generated homepage for the inherited file link and stale “download ready” wording; it now states no eligible TIFF, no download, and no submission. The legacy artifact is named in the quarantine table without an action link.
- No ranking metric was produced by software tests. No synthetic test or historical peer claim is reported as HOLDOUT-DTI or ORGANIZER-CONFIRMED.

## Pass 3 — request reconciliation and scientific guardrails

- The nine-site executive table remains in `docs/index.html`, sourced from pinned participant-repository artifacts. Per-site leader values are explicitly owner-reported/unverified; candidate leaderboard estimate is “not estimable”; historical files are not submission recommendations. The site summary does not convert a participant holdout into a leaderboard forecast.
- The bounded H33 explanation remains in `research/cpx_why_02778_20261028.md` and `docs/HYPOTHESES.md`: GEMSDOE25/30 share one 44,090-dot geometry; the supplied H33 mask has 37,654 dots and removes 6,436 points within two pixels of the mirrored catalogue, without additions. This geometry is consistent with an emission-efficiency/thinning hypothesis, but does not establish model ancestry, hidden-fault coverage, causal score gain, or the receipt-to-file identity of the owner-reported 0.2778.
- Five candidate hypotheses are already ranked, with layers, physical signatures, rationale for missed catalogue faults, distinctions from named peer ideas, likely non-fault mimics, cost and validation protocol in `docs/HYPOTHESES.md`. The top-ranked strain-tensor orientation-discontinuity idea needs no new data if the canonical feature cache is restored. It remains untested; the absence of a lane means it cannot be activated now.
- No candidate estimate can be computed defensibly from historical competition claims. The requested 0.2778, 0.3195, and 0.4413 figures have different scopes and lack organizer receipts in this checkout. The focus-site values in the executive table are historical owner claims, not confirmed scores.

## Current blockers, in priority order

1. **Method lane:** obtain the explicit assigned single-method paragraph; do not infer one from the list of ideas.
2. **Canonical shared cache:** obtain its bytes, digest, lineage, and invalidation method from the shared template; do not privately regenerate it.
3. **Shared evaluator repair:** central owner must fix the empty-truth pooled-FP invariant, publish a pinned commit, and pass synthetic fixtures. Keep upstream source pristine until then.
4. **Inputs/provenance:** official competition data page requires participant authentication; mirror byte hashes establish mirror integrity only, not organizer identity. Establish organizer-template identity and legal/provenance clearance before model use.
5. **Registry completeness/semantics:** acquire a complete current raster and continuous-surface registry and define companion dots for soft fields. Current public-repository scans omit private/organizer-only submissions; the observed full-footprint diagnostic also saturates an older positive-cell-as-dot rule.
6. **Comparable incumbent:** preserve fold IDs/digest and evaluator version for a same-fold, same-evaluator baseline. Existing participant holdout reports are not an incumbent receipt unless reproduced.
7. **Then run one lane only:** test every feature individually for leakage (AUC > 0.90 is stop-until-explained), then the preregistered top candidate under whole-segment buffered hide-and-recover, pixel-exact visible-fault masking, and pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). Compare its paired 95% interval against the same-fold incumbent; enforce correlation and >70% overlap stops before placement and on final dots.
8. **Release only after gates:** saved-byte validator must certify single-band float32, range [0,1] inside footprint, no NaN/Inf inside, and exact organizer CRS/shape/transform. A distinct selector must verify the weekly cap. A local validator or a public download page never authorizes upload.

## Trusted review links

- [DrivenData competition overview / metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData official data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [NREL/DOE GEMS report](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN official data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [Shared evaluator repair issue #41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41) and [canonical cache issue #53](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/53)

These are source links for manual review, not proof that every linked page or data file was freshly retrieved in this session. No DrivenData authentication or official upload receipt is available here.

## Final result

This is a negative, end-to-end repository/site review. It fixes a dangerous stale-download presentation and adds test coverage, but does **not** meet the scientific submission target. The correct next step is resolving the prerequisite blockers, not downloading a preserved raster or spending a competition slot.
