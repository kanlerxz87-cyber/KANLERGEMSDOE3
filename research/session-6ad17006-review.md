# Three-pass review — session 6ad17006

**Decision: DO NOT SUBMIT.** This session began at `2026-10-27T23:40:41Z`
([fixed config](../config/research-session-6ad17006.json)). It did not generate a
geological candidate, run a geological experiment, spend a weekly competition slot,
or create a leaderboard estimate. The requested winning GeoTIFF and its name/note
are not deliverable from the available evidence. This is a negative result, not a
claim that none of the proposed mechanisms can work.

## Pass 1 — source and historical-evidence review

The nine participant repositories were repinned at
[23:42:22 UTC](../evidence/session-6ad17006-focus-feed.json); the homepage feed had
been older. Nine commits changed relative to that older deployed feed; three changed
relative to the preceding scoped review. After integrating concurrent main, a second
[9/9 refresh at 00:05:57 UTC on 28 October](../evidence/session-6ad17006-focus-feed-post-merge.json)
found GEMSDOE33 changed since the newer main feed. These are source-head observations
only, not a complete registry, scientific review, updated score receipt, or permission
to upload.
The pages contain per-site source file links, SHA-256s, local-format profiles and
geometric uniqueness against the prior priority references:

| Priority executive page | Historical participant-reported claim, **unverified**, not a new score |
|---|---:|
| [GEMSDOE24](../docs/sites/GEMSDOE24.html) | 0.2477 |
| [GEMSDOE25](../docs/sites/GEMSDOE25.html) | 0.2600 |
| [GEMSDOE27](../docs/sites/GEMSDOE27.html) | 0.2449 |
| [GEMSDOE28](../docs/sites/GEMSDOE28.html) | 0.2710 |
| [GEMSDOE30](../docs/sites/GEMSDOE30.html) | 0.2600 |
| [GEMSDOE31](../docs/sites/GEMSDOE31.html) | 0.2708 |
| [GEMSDOE32](../docs/sites/GEMSDOE32.html) | 0.2778 |
| [GEMSDOE33](../docs/sites/GEMSDOE33.html) | 0.2632 |
| [GEMSDOE36](../docs/sites/GEMSDOE36.html) | 0.2750 |

None is bound to an actual organizer submission-page receipt. They are neither
ORGANIZER-CONFIRMED nor comparable new HOLDOUT-DTI measurements. The claimed
0.2778 for GEMSDOE32/H33 B2 has no justified causal explanation. An independently
repeated [saved-raster geometry audit](../evidence/session-6ad17006-h33-lineage.json)
reproduced the previous receipt exactly: GEMSDOE25 and 30 masks both contain 44,090
identical dots; GEMSDOE32 equals that mask after removal of 6,436 dots within two
pixels of the mirrored catalogue, with no additions. Less redundant emission might
reduce false-positive cost, but could also miss true faults; absent hidden labels and a
paired ablation, this observation does not explain the score or prove authorship.

The pre-existing all-nine audit found every historical winner above the literal 70%
overlap rule against another priority reference; historical continuous surfaces were
not available for correlation. The existing 37,654-dot GEMSDOE36 KPL-36 peer file
has 37,341 dots (99.17%) within 3 pixels of the registered lattice. The existing
parallel-session random control has 37,611 / 37,654 (99.89%) overlap. Neither is this
session's candidate, and both fail the user's rule regardless of their prior promotion
claims. At 37,654 dots, the independent coverage bound gives at least 82.34% lattice
overlap; lower-density candidates are not ruled out by this bound alone. A separate
soft diagnostic lacks an authenticated dot definition; its saturation is not an
exemption. See [lattice evidence](../evidence/lattice-coverage.json),
[KPL audit](../evidence/kpl36-lattice-audit-20261027.json) and
[random-control audit](../evidence/parallel-poisson-audit-20261027.json).

## Pass 2 — implementation and scientific review

### Gates and format

- [Uniqueness](../scripts/check_uniqueness.py) reopens co-registered TIFFs, verifies
  registry hashes, stops on the first literal duplicate, atomically replaces old
  receipts with an in-progress/failure state, refuses output/input aliasing, rehashes
  inputs and refuses unhashed sidecars. It binds the final rank correlation to the
  exact final dot raster. Signed correlation **greater than** 0.90 or directed
  candidate-to-reference dot overlap **greater than** 70% within 3 pixels blocks.
- [Readiness](../scripts/readiness.py) runs the locked shared operator audit live,
  checks canary direction/counts/intervals and independently replays both saved
  uniqueness stages. Receipts alone are not trusted. Registry completeness and
  chronology remain external assertions; no cryptographic proof of an inventory's
  completeness, assignment or check-before-placement order is claimed. Passing this
  gate only makes a candidate eligible for consideration by a separate selector.
- [Saved-byte validation](../scripts/validate_submission.py) checks single band,
  CRS, shape, transform, float32, finite in-footprint values, [0,1] range, mask,
  sidecars and before/after input hashes. To reduce whole-grid range-scan risk,
  the readiness gate calls the pinned shared auditor's existing **zeros** mode plus
  the independent **masked-finite** profile; the latter requires a standalone
  internal exterior mask and finite raw [0,1] values. The shared check also requires
  raw exterior zeros and no visible-catalogue predictions. The wrapper also rejects
  multiband, sidecar-altered or missing/nonbinary in-footprint catalogue labels, so a
  label mask cannot silently hide known faults. These are stricter local checks, not
  organizer acceptance. Changes after the check are still possible.
- The pinned shared writer emits an unmasked zeros file and a raw-NaN file, neither
  of which meets that combined requirement. Central writer/validator repair and a
  repinned shared release are still needed; this session did not alter the shared
  writer or privately rewrite a candidate. The exact rejected portal TIFF was not
  provided, so no cause of the earlier [0,1] error is established. The archived
  random-control zeros file passes only the [local finite-grid profile](../evidence/session-6ad17006-archived-format.json)
  against the participant mirror; it is not accepted or eligible.

The [live synthetic audit](../evidence/session-6ad17006-operator.json) again found
that the pinned shared evaluator fails to accumulate false-positive mass from
empty-truth cells. This is an operator defect, **not** a claim that historical
competition scores were affected. [Issue #41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41)
was open when checked; the [upstream observation](../evidence/session-6ad17006-upstream.json)
shows the current public shared `holdout.py` Git blob still matched the locked
failing version, and the authenticated account lacked push permission. No private
numerical evaluator was introduced.

### Sources and science

The [primary-source audit and conditional ranking](../knowledge/session-6ad17006-geothermal-research.md)
records DOE/NLR rules, USGS GeoDAWN/3DEP, USGS Surprise Valley and GDR. The four
untried ideas in the **earlier alternative queue** are, in qualitative priority order:
cross-scale magnetic edge with signed radiometric termination; repeated drainage
offsets; paired alteration-front terminations; and terrain/season-conditioned thermal
asymmetry. Their refined machine-readable record is
[`hypotheses-session-6ad17006.json`](hypotheses-session-6ad17006.json). The concurrently
merged [newer queue](hypotheses.md) is preserved unchanged as the site's main four
proposals. Each has named non-fault mimics, missing-fault rationale, cost and provenance
limits; neither queue is the missing assigned lane or a global novelty claim. GeoDAWN Area 2 nominal flight-line
spacing is 400 m, so a 100 m grid is not independent 100 m acquisition. Official DEM
tile metadata is available within the template's bounding rectangle, not proven
footprint coverage. The attempted official 2 m probe archive retrieval returned HTTP
500. No new external binary was acquired. The public official reference also supports
CPU-only execution; a GPU is not universally required.

## Pass 3 — reproducibility, site and adversarial review

- Full Python suite with restored optional pinned instruments:
  `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` →
  **231 passed** after integrating concurrent main ([verification receipt](../evidence/session-6ad17006-verification.json)).
  These are software/synthetic and historical consistency tests, not new geological experiments.
- `python scripts/review.py && python scripts/build_site.py --check` passed; the
  deterministic generator retains other sessions' isolated study artifacts. The
  blocked homepage, historical site pages and source snapshots were refreshed.
  `git diff --check` passed.
- `node tests/browser_smoke.mjs --serve` passed desktop/mobile, all priority pages,
  no-approved-download, overflow, and changed/unavailable/rate-limited feed tests.
  GitHub API responses in browser scenarios were mocked; this is not a live score
  or organizer check. The production page's read-only source feed is not a score feed.
- The preserved SSP1 study's separate suite passed **61 tests**, its 15-page browser
  check passed, and its offline saved-byte verifier passed 38 checks; the original
  study receipts were restored unchanged ([scoped receipt](../evidence/session-6ad17006-ssp1-technical.json)).
  This did not rerun its real-data OOF experiment or change its negative verdict.
- The [dated preflight](../evidence/session-6ad17006-preflight.json) verifies pinned
  participant-mirror input bytes and shared-tool lock locally, but those hashes do not
  establish organizer provenance. The mirror sample includes catalogue positives,
  inconsistent with the documented all-absence sample description. Ignored bulk
  inputs, virtual environment and restored optional instruments may not persist.

### Required next steps

1. Obtain the actual single-method assignment; preserve the fixed clock/budget and
   do not silently choose a lane. Repair the shared evaluator **and** writer centrally,
   pin the corrected source, and rerun conservation/encoding tests.
2. Restore and authenticate the canonical derived feature cache/digest; establish a
   complete, current registry and explicit reference dot masks, plus a same-fold,
   same-evaluator incumbent. Do not exempt the lattice or full-support diagnostic.
3. Authenticate the official template/footprint and resolve the participant sample
   discrepancy. Verify data rights, provenance, coverage and AI-use disclosure.
4. Only then run at most three lane experiments / two hours, with buffered whole
   fault-segment folds, visible-only catalogue-derived features, exact visible-fault
   masks, feature-alone AUC leakage canaries and the required pooled metric/CI.
   Uniqueness must be checked before placement and on final saved dots. Any result is
   a HOLDOUT-DTI, not an organizer score or calibrated leaderboard estimate.
5. If a future candidate actually clears every scientific, format and uniqueness
   gate, build an evidence-authenticating publisher, record the name/note and exact
   bytes, and let a **separate** selector check the actual account cap and decide on a
   slot. The current publisher cannot promote positive results.
