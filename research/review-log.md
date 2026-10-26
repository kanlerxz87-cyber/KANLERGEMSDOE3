# Three review-and-fix passes

Completed on 2026-10-26 UTC; this log distinguishes repeated checks from new experiments. **No geological experiment, candidate TIFF, or competition submission was made.**

## Pass 1 — sources, forensic claims, and stop order

- Reopened nine pinned historic TIFFs against the mirrored sample and checked actual hashes, binary masks, directed 3-px overlaps, and H33 lineage. Re-ran the full audit; all nine still fail overlap against a focus peer.
- Verified the shared saturation certificate against the immutable dense witness and reproduced the exact certificate with the expected exit 2. Corrected the invalid lattice-only “99.4% lower bound”: the rigorous lower bound at 37,654 dots is 82.34%.
- Recorded that score-to-file receipts and organizer-origin copies are unavailable; the mirrored sample's values match the label mask; `labels.tif` and `existing_faults.tif` are byte-identical. None is an independent hidden-label test.
- Checked current official rules, metric and leaderboard, and labeled peer and user-reported numbers honestly. Refreshed nine peer-head checks and documented newer narrower-scope or contradictory banners instead of treating them as approvals.

## Pass 2 — tools, math, and fail-closed behavior

- Tested synthetic tied-rank Spearman vs SciPy, 3-px boundary/direction, saturation/grid mismatch, and the pooled DTI against an independent brute-force formula. Tested visible-pixel exclusion and rejecting unpaired truth counts.
- Found an upstream **prose** error (`dT <= k` is false when a dot covers multiple truths); the shared implementation computes the metric correctly. Added a regression counterexample and documented it without a private template fork.
- Corrected the retrospective comparison to use the user's positive Spearman threshold, retain absolute correlation only as a diagnostic, and return **unknown** for missing comparison evidence. Hardened the one-witness preflight: exit 2 means blocked; exit 3 means inconclusive, never approved.
- Exercised saved-byte checks for NaN, infinity, range, nodata, outside mass, dtype, band count, shape, CRS, and transform. A format pass always remains `ok_to_submit: false`. Tested malicious archive paths/links and modified template files.
- Performed a clean independent rebuild of the shared 35-channel physical cache: its SHA-256 matched the original cache, `4f4b64aeabf32bd5717824e501c6766451525c322c1ea6f089d5d9ff20f6c5b7`. This is preprocessing reproducibility, not an experiment.

## Pass 3 — user interface, freshness, and operations

- Built deterministic static pages from the audited JSON. Checked local links, explicit NO decisions, nine research-only rows, disabled candidate download, and run-card nulls. Tested public-leader parsing with representative five-column HTML, ambiguous/login inputs, redirects/failures, and stale snapshot preservation; tested peer-head failure as **unknown**, not unchanged.
- Ran headless Chromium checks at 1440×900 and 390×844 on the homepage and submission guide; verified no JavaScript errors and no whole-page horizontal overflow. Fixed a mobile guide overflow; made the wide comparison table keyboard-focusable with a mobile scroll hint. No human inspection is part of raster validation.
- `python -m pytest -q` passed the local suite; `node --check assets/site.js`, Python compilation, link checks and `git diff --check` passed. GitHub Actions may require repository-level Pages configuration and permissions; the sandbox itself cannot access DrivenData directly, so the local feed updater's network failure was deliberately checked and remains visibly stale/error rather than presented as fresh.

The remaining hard stop, portal encoding ambiguity, complete-registry uncertainty, missing assigned lane, external-site changes and lack of authenticated score receipts are intentionally **not** hidden by these checks.
