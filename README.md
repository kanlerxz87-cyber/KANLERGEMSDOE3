# GEMS Observatory

> **Current decision: NO FILE IS APPROVED FOR SUBMISSION.** A parallel session
> produced a [research-only TIFF](docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif),
> but it fails the literal registry novelty rule and local footprint checks. Its
> holdout was not independently rerun. [Open the executive summary and submission
> guide](docs/executive-summary.html) or [read the portfolio review](knowledge/portfolio-review.md).
> Do not upload this research file or rename a historical TIFF as new work.

An evidence-first workspace for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/).
The aim is a scientifically grounded fault-discovery system that could compete
for a top leaderboard position, **not** a fabricated leaderboard prediction. The
organizer asks for faults indicative of geothermal resources, not a direct map of
geothermal vents. The system must make it obvious which TIFF, if any, is permitted
to submit, generate and validate it automatically, show reliable evidence, and
maintain an accessible, current feed. There is no permitted TIFF at present.

The static GitHub Pages site lives in [`docs/`](docs/index.html). The original
checkout contained only this README; the shared tools and data referred to in the
request were not in the checkout. This audit session restored and prepared core
inputs from owner mirrors but did not perform a scientific experiment. A separate
parallel session later contributed a research TIFF and reported holdout results;
its evidence is preserved and independently checked below.

## Standing project request — read before every session

This is a reconstructed brief of the user's standing objectives and constraints,
not a verbatim transcript of the original prompt. Read it as the starting brief
for future work:

* Focus on the strongest submissions from **GEMSDOE24, 25, 27, 28, 30, 31, 32,
  33 and 36**. Provide a clear executive summary, exact filename, estimated score
  only when defensible, and whether each file is unique against the other sites.
* Study why the reported GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`
  claim of **0.2778** was the highest in the supplied focus list and whether a
  unique candidate can do better. Do not assert a causal explanation, a private
  result or an organizer receipt that has not been observed.
* **A genuinely new, unique, competition-format TIFF is required for a future
  submission. Do not copy a previous submission except for learning or audit.**
  Its download, unique name, <=140-character note and explicit submit/no-submit
  decision must be prominent. A negative result is still a deliverable, and a
  blocked run must never be represented as a valid submission.
* Automatically inspect and validate the saved file without relying on a human
  geological inspector. Prevent the reported `Predicted values must be in range
  [0, 1]` error by checking values, NaNs, infinities, sentinels, footprint, band
  count, CRS, shape and transform. Do not claim an actual portal acceptance until
  it is observed. Respect the official outside-bounds null/NaN guidance and flag
  the apparent conflict with all-finite variants.
* Before new modeling, rank 3–5 geological hypotheses, specifying layers,
  physical signatures, off-catalogue rationale, alternatives and novelty relative
  to existing work. Test the leading assigned hypothesis against a comparable
  spatial holdout before using a weekly slot. Find and cite free, official and
  appropriately licensed data; distinguish metadata access from a verified raw
  download and mark missing coverage. Provide a clean source catalog and a GitHub
  Pages site with a submission guide and an up-to-date, timestamped feed.
* Review the work in multiple passes, test edge cases, correct mistakes, preserve
  negative findings and record remaining limitations. Link to verified official
  sources for manual review while keeping validation autonomous. Maximize P(Win)
  and own the outcome end to end.

### Parallel-run protocol from the request

1. **LANE.** The lane is the single method paragraph assigned to the session. Stay
   inside it. If raster rank-correlation with any registry raster exceeds 0.90,
   or more than 70% of dots fall within 3 pixels of a registry raster's dots, log
   a duplicate and stop. Check the surface before placement and final dots. The
   current request refers to such a paragraph but does **not** actually include an
   assigned method; do not invent an assignment.
2. **REUSE, DON'T REBUILD.** Reuse the template's cached feature stack,
   `evaluate_holdout.py` and `submission_writer.py`. Hide whole fault segments with
   a buffer, derive all catalogue-based features from visible faults only, mask
   visible faults pixel-exactly and score **pooled DTI** (alpha 0.2, beta 0.8,
   300 m triangular kernel). If a shared tool is wrong, fix it in the shared
   template and report it; never maintain a private fork.
3. **LABEL EVERY NUMBER.** A result is HOLDOUT-DTI with evaluator version, number
   of withheld positives and 95% CI, or ORGANIZER-CONFIRMED from a submission-page
   receipt. A projection is never a score. User-provided historical claims without
   receipts must be identified as **unverified claims**, not mislabelled as either.
   A public leaderboard observation is also not a submission-page receipt.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout before relying on a
   result. AUC above 0.90 means leakage until proved otherwise.
5. **RUN CARD.** End each run with one JSON card recording hypothesis, mechanism,
   named non-fault mimic, HOLDOUT-DTI and CI, correlation/overlap versus the
   registry, raster SHA-256, validator output, name and <=140-character note,
   and verdict `promote` or `negative`. Negative results are deliverables.
6. **BUDGET.** Stop after three experiments or two hours, whichever comes first.
   Do not pick submissions: promotion to a real slot is a separate selector step
   and must respect the weekly cap shown on the submission page.

### Historical focus claims supplied by the user

These are **USER-REPORTED / UNVERIFIED claims**, not organizer-confirmed results or
predictions. File names and comparative byte evidence are in
[`data/historical-manifest.json`](data/historical-manifest.json) and the
[portfolio audit](evidence/portfolio-audit.json). All nine fail the specified
final-dot threshold against at least one other member of the audited nine; the
full current registry and pre-placement surfaces were not audited for them.

| Site | Highest claim in the supplied list | Status |
| --- | --- | --- |
| GEMSDOE24 | 0.2477 | Historical; do not submit |
| GEMSDOE25 | 0.2600 | Historical; same in-footprint mask as GEMSDOE30 |
| GEMSDOE27 | 0.2449 | Historical; do not submit |
| GEMSDOE28 | 0.2710 | Historical; do not submit |
| GEMSDOE30 | 0.2600 | Historical; same in-footprint mask as GEMSDOE25 |
| GEMSDOE31 | 0.2708 | Historical; do not submit |
| GEMSDOE32 | 0.2778 | Historical; highest supplied focus claim, not a receipt |
| GEMSDOE33 | 0.2632 | Historical; do not submit |
| GEMSDOE36 | 0.2750 | Historical; do not submit |

The official public leaderboard showed **0.4437** when retrieved by our research
instrument on 2026-10-26 UTC. This is a **public leaderboard observation**, not a
submission-page receipt or a forecast. The prompt's 0.3195 and 0.4413 figures are
not treated as current. The published site displays the most recent successful
observation and marks failures or stale data instead of silently using old values.

## Verified work in this checkout

* [Nine-file forensic audit](evidence/portfolio-audit.json): historical files were
  fetched at immutable refs, SHA checked, reopened and compared on the owner-mirror
  grid. The GEMSDOE32 file equals the GEMSDOE25 D2.8 mask after retaining cells
  >2 pixels from the mirror catalogue; GEMSDOE36 contains every H33 dot plus
  1,200. These geometric facts do not establish why a hidden score changed.
* The pinned 13GEMSDOE spacing-five lattice is within 3 pixels of 99.8713% of the
  footprint. Against this reference alone, a 37,654-dot candidate cannot satisfy
  the literal 70% threshold; at most 22,163 distinct dots is a necessary (not
  sufficient) upper bound. No lattice exception has been granted.
* [Core mirror preparation receipt](evidence/mirror-preparation.json): all four
  core SHA pins were restored and shared `prepare_data.py` ran. The sample mirror's
  positive mask equals the labels, conflicting with the organizer's description
  of a zero-prediction sample. Mirrors are **not organizer-authenticated**.
* The requested precomputed `feature_stack.npy` is absent from the pinned shared
  tree and published artifacts. This audit session had no assigned lane and built
  no candidate. A parallel session self-selected a lane and rebuilt a stack rather
  than using the missing cached stack; its reported tests are preserved separately.
  No slot was spent.
* The shared CLI silently binarizes positive probabilities; this was reproduced and
  [reported upstream](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37).
  A second shared CLI validator does not inspect outside-footprint values; also
  [reported upstream](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/39).
  This checkout does not fork or silently patch those tools. Our release wrapper
  invokes the shared `gems32.submission.audit_geotiff` instead of the incomplete
  check CLI, and still requires an authenticated template and separate selector.
* [Pre-registration](knowledge/preregistration-2026-10-26.md) provides four ranked
  hypotheses and named non-fault mimics. The [run card](evidence/run-card.json)
  explicitly records the negative blocked result.

## Reproduce the audit and data placement

Prerequisites: Python 3.11+, GitHub CLI (`gh`, for this restricted environment),
`curl`, and sufficient disk space. Large inputs and caches stay out of Git.
The scripts fetch the immutable shared template by commit, verify pinned tool
hashes, and delegate to it; they do not vendor private evaluator/writer copies.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
bash scripts/download_competition_data.sh core   # or external, scored, all
python scripts/prepare_data.py                  # shared data preparation
python scripts/preflight.py                     # exit 2 while the lane/cache are missing
python scripts/audit_history.py \
  --sample .cache/gems_data/sample_submission.tif \
  --labels .cache/gems_data/labels.tif
python scripts/readiness.py                     # fail-closed; never selects a slot
python scripts/build_site.py
python -m pytest -q
python -m unittest discover -s tests -v         # concurrent review suite
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

`download_competition_data.sh` uses pinned **owner mirrors**. It does not establish
that the files came from the competition organizer. The canonical cache is not
published, so these commands do not create it or claim that training is ready.
`GEMS_DATA_DIR`, `GEMS_WORK_DIR` and `GEMS_TEMPLATE_DIR` can override paths.
The optional scheduled Pages workflow checks public leaderboard and peer-head
freshness; it cannot authenticate a submission, access the account's quota,
re-audit all current rasters, or upload anything.

## Official references

* [DrivenData problem, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
* [Competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
* [DrivenData staff clarification of known-fault masking](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2)
* [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
* [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
* [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) · [USGS fault database](https://www.usgs.gov/programs/earthquake-hazards/faults)
* [DOE GDR INGENIOUS compilation](https://gdr.openei.org/submissions/1391) · [EPSG:32611](https://epsg.io/32611)

## Parallel GPC-3 research candidate — DO NOT SUBMIT

A separate session produced
[`kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif`](docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif)
(SHA-256 `16ec0585a884224460f0e5d09e7448a54ab5a3348db92279452a9a4e0453b0f7`).
Its session reports **HOLDOUT-DTI 0.137681 [0.125567, 0.150331]**,
`gems-segment-pooled-v1`, 60,988 withheld positives. We did not independently
rerun that evaluation, and its folds have not been authenticated as matching the
site-reported same-evaluator best of 0.16379. It is not a leaderboard prediction.

The earlier report checked novelty against only nine champions. Our independent
[`parallel-candidate-audit.json`](evidence/parallel-candidate-audit.json) finds
**37,654/37,654 dots within 3 pixels of the registered spacing-five lattice**:
100% exceeds the literal 70% stop, so this raster is a duplicate. The pinned
shared auditor also rejects its finite values outside the footprint and 4,115
positive catalogue cells. The owner-mirror sample is not organizer-authenticated.
The parallel runner at `scripts/evaluate_holdout.py` is a prior session's custom
experiment driver, not the shared evaluator; its CLI and final-emission path are
blocked because its three-experiment budget was used and its narrower novelty gate
must not promote another file. The pinned GEMSDOE32 shared tools are bootstrapped
separately for audit and future properly assigned work.
The exact original runner and prior site are archived for reproducibility; the
TIFF and ZIP are **research downloads only**. No slot was selected or spent.

To reproduce our lattice audit after restoring the core mirror and running
`scripts/audit_history.py` (which caches the pinned lattice), run:

```bash
python scripts/audit_parallel_candidate.py \\
  --candidate docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif \\
  --lattice .cache/history/13GEMSDOE/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif \\
  --sample .cache/gems_data/sample_submission.tif --labels .cache/gems_data/labels.tif
```

## Concurrent-main review preserved

Other reviews reached `main` while this work was in progress. Their
[standing project request](PROJECT_REQUEST.md), [independent audit](docs/audit.json),
[review dashboard](docs/concurrent-main-dashboard.html), [research](docs/archived-research.html),
[source snapshots](evidence/upstream/), [prior README](docs/concurrent-main-readme.md),
[parallel GPC-3 dashboard](docs/parallel-gpc-dashboard.html) and
[parallel GPC-3 README](docs/parallel-gpc-readme.md) are preserved. The independent audit compared historical representation variants
against the owner-mirror footprint and found that some zeros-outside files do not
meet the strict null-outside interpretation; this is not an organizer portal
receipt. The active run card for **this** session is
[`evidence/run-card.json`](evidence/run-card.json); other cards record earlier
reviews and must not be interpreted as new candidate approvals. The other review
builder now writes archived research rather than overwriting the active site.

See the [source catalog](docs/sources.html), [next steps and irregularities](knowledge/portfolio-review.md),
and the [user-facing submission guide](docs/executive-summary.html). The official
reference solution has CPU and GPU environments; a GPU is useful but not proven
necessary. Competition data and private submission receipts remain behind account
access, while the sandbox shell has outbound access only to approved GitHub and
package hosts. No credentials are requested or stored here.
