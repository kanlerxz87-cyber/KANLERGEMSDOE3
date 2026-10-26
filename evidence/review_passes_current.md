# Three-pass review — provisional K/Th–LiDAR research run

## Pass 1: implementation and observed result

- Ranked four hypotheses and fixed one provisional lane before feature implementation. Recovered six
  owner mirrors, validated their hashes and grid, and installed 19 unchanged, Git-blob-pinned shared
  modules. Restored and checked 167 frozen comparison rasters, including the calibration lattice.
- Attempt 1 stopped after canaries on a local uninitialized clock variable; preserved its error receipt.
  Fixed only that orchestrator bug; attempt 2 used identical features, seeds, budgets, thresholds and
  holdout. No further candidate was run after the duplicate stop.
- Used label-free physical features, fold-visible training, shared whole-component spatial holdout,
  single-feature/support canaries and OOF-model canary; two-surface rank checks preceded dot placement.
  Evaluated the fixed candidate and feature ablation using unchanged shared `gems57` pooled DTI and
  paired physical-block intervals. In-memory final dots failed the first lattice overlap gate. No TIFF
  was written from this lane and no slot was spent. The run card is the authority for the exact results and limitations.

## Pass 2: defect and assumption review

- Found the sample mirror contains the exact known positives. Restricted its use to footprint/grid.
- Found two registry rasters are nonbinary; preserved continuous values for Spearman comparisons.
- Verified the lattice bound separately and distinguished it from the observed final 100% overlap.
  Confirmed lower-density candidates are not universally ruled out and the budget was not reduced.
- Checked fold isolation and the OOF canary; compared the unchanged shared metric to a separate
  brute-force probability definition on synthetic masks. Smoke-tested the unchanged shared writer.
- Found a shared-writer conflict: official null-outside wording versus default zero exterior and an
  advisory-only outside check. The strict concurrent local validator rejects that default. A synthetic
  regression now captures both behaviors. A concurrent version pin defaults to NaN instead of zero;
  tests isolate the packages and verify both defaults. The upstream templates remain unchanged; no
  private fork or successful shared fix is claimed.
- Reconciled concurrent `main` changes, preserving earlier work in archives and integrating the
  template-mask-aware historical validator and safe Markdown link rendering. Kept the current
  experiment's authoritative run card and regenerated dashboard. A later main merge added a GPC-3
  research TIFF; its exact SHA-256 was independently audited and all 37,654 dots fall within 3 px of
  the registered lattice. A nine-champion-only uniqueness pass is insufficient. Its historical card
  is updated to record the duplicate, while the original is archived. A strict local footprint audit
  also rejects its exterior zeros; it is not a portal receipt.

## Pass 3: full recheck

- Recomputed run-card pooled arithmetic, gate thresholds, reference counts and paired difference;
  verified the same negative result even with Python assertions disabled.
- Ran all **34** local tests after integration. The suite checks geometry, saved-byte format fixtures,
  feature support/offsets, leakage canary failure on a deliberately leaked label, independent metric
  parity, writer/mask conflict, source links and fail-closed gate behavior.
- Regenerated deterministic HTML/JSON, checked active pages' local links and fragment IDs, validated
  JavaScript syntax, and confirmed the standalone preview is served from `docs/` only. Rendered both
  desktop (1440×900) and mobile (390×844) in headless Chromium: nine rows, no page errors, no body
  overflow, and the guide verdict was visible. The source-refresh success path used a mocked GitHub
  response; the restricted sandbox showed the truthful failure fallback. External images or manual
  data entry are not needed. The leaderboard is a dated observation, not an automated
  feed; the optional browser source-health check uses only GitHub's public API.
- Unresolved: assigned lane, authorized mirror/code rights, authenticated organizer data, full live
  registry, same-evaluator best-incumbent comparison, shared-template repair, account-specific cap,
  organizer receipt and geological expert review. The negative result does not satisfy the requested
  new high-scoring unique upload, and no numerical leaderboard forecast is justified.
