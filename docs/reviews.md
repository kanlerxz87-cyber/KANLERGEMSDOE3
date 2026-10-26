# Three review passes — 2026-10-26

## 1. Implementation and evidence

Restored the pinned shared template and public-mirror core/feature inputs,
recorded pre-implementation hypotheses, reproduced the universal duplicate
witness, audited nine historical anchors and B2 lineage, and built a negative
run card, saved-byte format wrapper, source register, Pages dashboard and
public-feed workflow. No training, candidate placement, holdout evaluation or
competition submission occurred.

## 2. Bugs, edge cases and fixes

- Added fail-closed checks for empty/mismatched witness grids, impossible dot
  budgets, empty/constant correlations, the strict 70% boundary, failed or
  corrupted downloads, malformed/ambiguous public tables, stale/invalid feeds,
  broken local links and a run-card promotion attempt.
- Found that an in-range `nodata=0` TIFF can mask valid pixels while the shared
  raw-value gate passes. The wrapper now rejects in-footprint masked cells and
  safely JSON-serializes NaN/inf diagnostics; the shared template still needs
  that regression/fix upstream. Also stopped calling a known-fault positive a
  *format* failure: it is informational, since those pixels are score-masked.
- Reconciled the parallel main review: its sample-footprint-null validator and
  the shared all-finite gate disagree for the mirrored sample exterior. The
  wrapper reports both and fails closed instead of choosing one interpretation;
  official wording says outside the bounds is null/NaN, and the exact meaning
  of the no-coverage footprint needs organizer clarification.
- Tested official-formula shared DTI arithmetic against brute force and found an
  upstream prose inequality that fails when one dot covers several truth
  cells. The exact two-sided implementation is not shown to fail by this.
- Inspected and tested the shared default fold builder: its 12-pixel chunks can
  leave an adjacent piece of the same trace visible. Fold-boundary erosion is
  not a segment-local buffer. It needs upstream correction/review before use;
  passing an arithmetic test is not a leakage-safe holdout certification.
- Browser feed behavior was tested with seven dependency-free simulated
  scenarios. A headless Chromium visual check could not run in the sandbox
  because system NSS/NSPR libraries were unavailable; do not claim otherwise.

## 3. Original-request coverage and limitations

- Executive comparison contains nine pinned historical filenames, user/owner-
  reported unverified values, absent HOLDOUT-DTI/n/CI, uniqueness outcomes and
  explicit NOT OK decisions. A dated top-ten public leaderboard snapshot is
  separate. A pinned peer portfolio repeats all nine reports; other peer
  records conflict on the 25, 28 and 31 attributions, as documented in
  [the claim audit](claims_audit.md). None is a file-specific organizer receipt.
- Ranked geological proposals, non-fault mimics, public source/license caveats,
  submission guidance, README, JSON run card and a no-candidate UI are present.
- The requested unique TIFF, score estimate, same-evaluator win, complete
  current registry scan and file-specific organizer receipts remain unavailable.
  The full original prompt was not available verbatim in this condensed
  session; the protocol is transparently labeled a summary.
- The live raw-page parser and scheduled GitHub Release publication need a
  successful run in the target repository. Until then, the dashboard shows a
  dated fallback, not a fabricated live feed.
