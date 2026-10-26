# GEMS Signal — evidence-first fault-discovery workspace

> **NOT OK TO SUBMIT.** No new candidate TIFF, HOLDOUT-DTI, confidence interval,
> or organizer submission receipt was produced. The download is deliberately
> disabled. No competition slot was used in this session.

[Open the Pages dashboard](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE3/) ·
[Executive summary](docs/executive-summary.html) ·
[Run card](evidence/run_card.json) · [Three reviews](docs/reviews.md)

## Read at the beginning of every session

The user's priorities include **Maximize P(Win)** and **Own the Outcome**.
Read [the standing protocol](docs/protocol.md), [PROJECT_REQUEST.md](PROJECT_REQUEST.md),
then this README, the run card, and the latest evidence before doing work.
Follow all current user instructions.

The full, verbatim original request was not available in this session's
compacted context. `PROJECT_REQUEST.md` and `docs/protocol.md` are **non-verbatim
operational summaries**, not a substitute transcript; we will not invent or
label a reconstruction as verbatim. If the original is later supplied,
preserve it exactly with its date.

## What was established

- The shared uniqueness rule treats any finite value greater than zero as a
  dot. A previously indexed, hash-verified dense probability raster is positive
  at **all 5,167,373 cells of the mirrored footprint**. Every nonempty candidate
  therefore overlaps it at 100%, exceeding the user-mandated 70% threshold.
  This is a **pre-placement STOP** under the literal rule, not a full-registry
  clearance or an organizer decision. See [preflight](evidence/preflight.json)
  and [analysis](docs/analysis.html).
- Nine historical anchors were checked pairwise; all fail uniqueness against
  at least one other of those nine. GEMSDOE25 and GEMSDOE30 have identical
  positive support *inside the mirrored footprint*. The nine-file audit is a
  subset, not the complete registry. Prior TIFFs are learning references, not
  newly authorized submissions. See [audit](evidence/focus_anchor_audit.json).
- GEMSDOE32 B2 has 37,654 dots and is exactly the D2.8 support after 6,436
  dots within two 100 m pixels of the mirrored catalogue are removed. Its
  **0.2778 is owner/user-reported and unverified**, not a file-specific
  organizer receipt; geometry alone does not prove score causation. See
  [lineage](evidence/anchor_lineage.json) and [technical notes](docs/analysis.md).
- The separately observed public leaderboard value is **organizer-published
  page data**, not a receipt identifying a TIFF. Its [dated snapshot](evidence/leaderboard_snapshot.json)
  is explicitly distinguished from any refreshed feed and from HOLDOUT-DTI.
- Public mirror SHA-256 pins show byte identity, **not authenticated organizer
  origin**. The mirrored sample's positive labels conflict with the official
  description of an absence-only example. Do not treat that mirror as an
  independently authenticated reference.
- The pinned fold builder uses 12-pixel chunks and quadrant-boundary erosion,
  not a demonstrated local buffer around whole original fault segments.
  The shared template needs an upstream correction/review before a valid
  experiment. Its format gate also needs an in-footprint validity-mask fix and
  clarification of the all-finite exterior against the reference-null policy;
  this repo reports both without forking the shared gate. Details: [analysis](docs/analysis.md).

**No model experiment ran.** A missing assigned method lane, the literal
uniqueness STOP, and unverified buffered-fold construction prevent progression.
No source permits us to invent a score, estimate, filename or submission note.

## Reproduce the audits

Requirements: Python 3.11, GitHub CLI `gh` with access to public repositories,
and the pinned Python packages. No competition credentials are used. All large
inputs and caches are ignored by Git.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt

# Core rasters + unchanged shared template + nine historical reference TIFFs.
python scripts/restore_workspace.py --fetch --anchors

# Optional: also reassemble the 418,912,844-byte, 19-band feature stack.
# Allow several hundred MB of additional disk space. This does not train a model.
python scripts/restore_workspace.py --fetch --all

# Rerun measurements into the ignored cache without rewriting recorded evidence.
python scripts/preflight.py --output .cache/rechecks/preflight.json
python scripts/audit_focus.py --output .cache/rechecks/focus.json
python scripts/analyze_anchor_lineage.py --output .cache/rechecks/lineage.json

# Inspect a saved TIFF. A local pass is NOT a uniqueness/slot/organizer approval.
python scripts/verify_submission.py /path/to/file.tif --sample /path/to/official_sample.tif
```

If `--sample` is omitted, the inspector uses the **unauthenticated public
mirror**, clearly identified in its report. It compares the saved bytes with
the reference and pinned grid, checks one float32 band, CRS, shape, transform,
finite values in `[0,1]`, no in-footprint masked cells, and the shared more
all-finite/zero-exterior policy and, separately, the parallel review's
reference-footprint-null policy. The organizer says data **outside the bounds**
must be null or NaN, but it is not established whether that wording refers to
the sample's interior no-coverage footprint as well as its rectangular bounds.
The two local policies disagree for the mirrored sample; the wrapper fails
closed when they do. Neither policy proves portal acceptance or the cause of
the past error, and no pixels are clipped or repaired.

## Site, data and tests

The root `index.html` is a static, accessible GitHub Pages site configured for
`main` root `/`; `scripts/build_site.py` renders five fail-closed pages from the
recorded evidence. It refuses to turn a negative run card into a positive
banner. The independent parallel-main evidence, tests and review remain
preserved, with conflicting snapshots in [the archive](docs/concurrent-main/README.md).
The single current run card is `evidence/run_card.json`; other run cards are
historical. See [submission instructions](docs/submission.md),
[ranked hypotheses](docs/hypotheses.md), the parallel [research shortlist](research/hypotheses.md)
and the [source register](docs/sources.md).

```bash
python scripts/build_site.py          # regenerate pages
python scripts/build_site.py --check  # verify tracked pages are current
python -m pytest -q                    # includes restored-byte integration tests
node tests/test_browser.js             # offline feed/frontend behavior tests
python -m http.server 4173 --bind 0.0.0.0
```

The feed workflow fetches only the **public** organizer leaderboard and public
GitHub repository HEADs twice daily, then writes a JSON GitHub Release body; it
does not commit to a branch or use a submission slot. Its raw live-page parser,
GitHub Actions permissions and first scheduled publication must be verified in
the destination repository. On failure or a feed older than the snapshot, the
site keeps the dated static observation and says the feed is unavailable/stale.
The top-ten list is a dated snapshot, not dynamically refreshed. Public rank
never establishes which file generated a score.

## Next gated step

The literal rule needs an explicit authorized resolution and one explicit
method lane; it cannot be silently relaxed. Correct/review the shared
whole-segment buffered fold and in-footprint mask gates upstream. Then, within
three experiments or two hours, rebuild **all** catalogue features from
visible faults only, run single-feature leakage canaries, compare pooled
hide-and-recover DTI on identical folds to a same-evaluator baseline with a
paired spatial 95% CI, and check the complete accessible registry both before
placement and on the final file. Only after the saved-byte validator and a
separate promotion/slot selector pass should a new unique filename and ≤140
character note be created. No leaderboard slot is spent automatically here.
