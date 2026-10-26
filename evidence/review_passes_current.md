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
  paired physical-block intervals. In-memory final dots failed the first lattice overlap gate. No TIF
  or slot exists. The run card is the authority for the exact results and limitations.

## Pass 2: defect and assumption review

- Found the sample mirror contains the exact known positives. Restricted its use to footprint/grid.
- Found two registry rasters are nonbinary; preserved continuous values for Spearman comparisons.
- Verified the lattice bound separately and distinguished it from the observed final 100% overlap.
  Confirmed lower-density candidates are not universally ruled out and the budget was not reduced.
- Checked fold isolation and the OOF canary; compared the unchanged shared metric to a separate
  brute-force probability definition on synthetic masks. Smoke-tested the unchanged shared writer.
- Found a shared-writer conflict: official null-outside wording versus default zero exterior and an
  advisory-only outside check. The strict concurrent local validator rejects that default. A synthetic
  regression now captures both behaviors. The upstream template remains unchanged; no private fork
  or successful shared fix is claimed.
- Reconciled concurrent `main` changes, preserving earlier work in archives and integrating the
  template-mask-aware historical validator and safe Markdown link rendering. Kept the current
  experiment's authoritative run card and regenerated dashboard.

## Pass 3: full recheck

- Recomputed run-card pooled arithmetic, gate thresholds, reference counts and paired difference;
  verified the same negative result even with Python assertions disabled.
- Ran all **24** local tests after integration. The suite checks geometry, saved-byte format fixtures,
  feature support/offsets, leakage canary failure on a deliberately leaked label, independent metric
  parity, writer/mask conflict, source links and fail-closed gate behavior.
- Regenerated deterministic HTML/JSON, checked active pages' local links and fragment IDs, validated
  JavaScript syntax, and confirmed the standalone preview is served from `docs/` only. External
  images or manual data entry are not needed. The leaderboard is a dated observation, not an automated
  feed; the optional browser source-health check uses only GitHub's public API.
- Unresolved: assigned lane, authorized mirror/code rights, authenticated organizer data, full live
  registry, same-evaluator best-incumbent comparison, shared-template repair, account-specific cap,
  organizer receipt and geological expert review. The negative result does not satisfy the requested
  new high-scoring unique upload, and no numerical leaderboard forecast is justified.
