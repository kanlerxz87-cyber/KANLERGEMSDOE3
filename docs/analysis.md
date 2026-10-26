# What the high reported value can — and cannot — tell us

## The answer

GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` has the largest
**user-reported, unverified claim** among the nine historical values supplied in
the prompt. We found no organizer submission-page receipt tying that value to
this file; the repository's [audit manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/submissions_manifest.json)
sets the file's `receipt` to null. A null receipt does **not** prove the file
was never scored; it means we cannot establish the attribution. Other sibling
pages make conflicting claims. The public leaderboard lists team results, not
these file hashes. The observed public leader was 0.4437 on 2026-10-26; that
is an **organizer-published leaderboard observation**, not a file-specific
submission receipt or a prediction for us. [Live leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

We cannot establish that any new submission beats the reported value, much less
that it leads the leaderboard. No new candidate or holdout score was produced
because the literal pre-placement uniqueness gate is impossible for a nonempty
candidate with the current registry definition. That is a negative result, not
an invitation to relabel a file.

## What we independently measured

Using exact, SHA-verified *public mirror* files, the GEMSDOE32 B2 support has
37,654 positive cells. It is **exactly** the GEMSDOE25 D2.8 support (44,090
cells) with every dot at Euclidean distance ≤2 pixels from the mirrored known
fault mask removed: 6,436 removed, none added. This is reproducible with
`scripts/analyze_anchor_lineage.py`; [measurement](../evidence/anchor_lineage.json).
The two sites' files are not organizer-authenticated here. Equality is on the
mirrored grid, not proof of hidden-label performance.

D2.8 has exactly the same positive-pixel set as the GEMSDOE30 named reference;
the files have different TIFF bytes. All nine historical reference masks fail
at least one directional 3-pixel overlap comparison against the other eight.
This is a nine-anchor subset, **not** a complete registry audit. See the
[full pairwise audit](../evidence/focus_anchor_audit.json). Past submissions are
for historical research only, not the new unique file the user requested.

## Metric reasoning, without invented hidden truth

The [official metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)
uses a triangular 300 m kernel, α=0.2 and β=0.8. For weighted true positive
coverage T, weighted false positives F and hidden positive count G,
`FN = G − T` and `DTI = T / (0.2 T + 0.2 F + 0.8 G + ε)`. A sparse set of
well-placed dots can cover nearby truth while reducing redundant prediction
mass. Removing low-credit dots **can** improve the index, but it can also
remove useful coverage. Because the private truth and the candidate's organizer
receipt are absent, we cannot quantify the contribution of thinning, prove
that the catalogue buffer caused a result, assert true hidden-fault density, or
calibrate a holdout to a leaderboard value.

Organizer staff state that known USGS/INGENIOUS fault pixels are excluded
**pixel-exactly**, not by a 300 m halo; new corrections can lie near known
faults ([staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)).
Thus B2 is a historical empirical design, not an organizer rule or a proven
optimal radius. Public and private scores pool terms rather than averaging
chunk scores ([staff clarification](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550)).

## Why the run stopped

The hash-pinned shared `gems57.uniqueness` defines a “dot” as **every finite
positive pixel**, including pixels in a continuous prior raster. An indexed
17GEMSDOE probability raster is positive on every one of the 5,167,373 cells in
the mirrored footprint. Therefore every nonempty candidate inside it would
have 100% of its dots within 3 pixels of that one prior, exceeding the 70%
limit **before placement**, independently of its geology. The focused
GEMSDOE24 registry also includes a five-pixel calibration lattice covering
99.871% of that footprint within 3 pixels. For a 37,654-dot candidate it
forces at least 82.34% overlap even if every uncovered cell were used. See the
[executable preflight](../evidence/preflight.json).

The policy choice is consequential: continuous probability maps and calibration
lattices make a literal overlap rule effectively universal. A future session
needs an explicit authorized definition/scope for the uniqueness registry; it
must **not** silently exempt them or redefine thresholds. The prompt also refers
to a “single method paragraph below,” but no specific method lane was supplied.
No model, feature canary, holdout, final raster, or slot was run.

## Shared-template documentation irregularity

In the pinned `gems57/metric.py` binary-dot discussion, the claim that one
new dot's truth-side marginal credit `dT` is always at most its own dot-side
credit `k` is not true when that one dot covers several truth cells. For
example, placing a dot on the center of three adjacent truth cells gives
`dT = 1 + 2/3 + 2/3 = 7/3`, while `k = 1`. The actual `marginal_accept`
implementation compares the exact before/after DTI and does not enforce the
false documentation inequality; this observation does not establish an
implementation failure. We have not patched or forked the shared template.
The wording should be corrected upstream by its maintainer before relying on
the exposition. Our session is confined to this repository's fixed branch.

### Holdout construction needs an upstream correction/review before a run

The pinned `evaluate_holdout.py` scores the fold masks supplied by its caller;
it does **not** itself establish how faults were split or how features were
computed. The pinned `holdout.py` splits mapped branches into chunks of at
most 12 pixels, erodes the *quadrant boundary*, and in `mode="all"` sets the
visible catalogue to all mapped pixels except the selected hidden chunks. That
boundary erosion is **not** a buffer around each withheld geological segment,
and adjacent chunks of a longer trace may remain visible. Thus the current
shared default is not demonstrated to meet the user's stricter whole-segment
plus local-buffer requirement. Its arithmetic tests below are not a leakage
certification. Before any experiment, the shared template's fold generation
must be reviewed and corrected upstream as needed, with tests showing that
whole original segments and their required local buffers are excluded from
all catalogue-derived features while only visible fault pixels are masked in
the score. The scoring module may be reused unchanged only after the corrected
folds and visible-only feature rebuilds are verified. This repository did not
create a private fork, alter the pinned shared template, or run the holdout.

### A nodata-mask gap in the shared format check

The pinned shared gate checks raw pixel values but a TIFF tagged `nodata=0`
can have finite, in-range raw values while masking zero-valued cells *inside*
the footprint. `scripts/verify_submission.py` adds a separate fail-closed check
of the saved band's validity mask; it does not modify the shared tool. The
shared template's format gate should be corrected upstream as well, with an
in-footprint validity-mask regression test. This local supplemental check is
not an organizer receipt and is not a private copy of the shared gate.

### Exterior-policy conflict from the parallel-main review

The official problem says the GeoTIFF has the same bounds as the training data
and **data outside the bounds is null or NaN**. The phrase does not resolve
whether the sample's no-coverage cells *inside its rectangular bounds* must
also be null. The shared gate instead requires all values finite and zero
outside the sample-derived footprint. The parallel review's separate
`validate_submission.py` interprets the sample footprint exterior as null.
On historical B2, the shared all-finite check passes, while the stricter
reference-footprint-null check reports 7,111,787 finite exterior cells and
fails. Conversely, a TIFF with NaNs in that exterior can pass the latter and
fail the shared all-finite check. Neither result proves portal acceptance or
rejection. The combined wrapper reports both and fails closed if they do not
both pass; reconcile the shared template and obtain organizer clarification
before promoting any candidate.
