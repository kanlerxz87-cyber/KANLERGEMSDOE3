# KANLERGEMSDOE3 — evidence before submission

**Starting point for every session:** read this README, the faithful standing project request in
[PROJECT_REQUEST.md](PROJECT_REQUEST.md), [pre-registration](research/preregistration.md),
[scientific review](research/review.md), and the [canonical JSON run card](evidence/run-card.json).

## Decision: DO NOT SUBMIT

The one fixed research experiment ended in a **duplicate stop**. Its 37,654 in-memory final dots
were all within 3 pixels of a registered calibration lattice, above the user's 70% threshold. No
candidate TIFF or submission name exists, no slot was spent, and there is no organizer receipt.
Changing the dot budget or quietly exempting the lattice to evade the rule is not authorized.

- [GitHub Pages research dashboard](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE3/) ·
  [Executive summary / submission guide](docs/executive-summary.html) ·
  [Nine-site audit](evidence/portfolio-audit.json) · [Run card](evidence/run-card.json)
- The provisional bilateral K/Th–LiDAR lane achieved **HOLDOUT-DTI 0.1134**
  (95% CI **[0.1006, 0.1262]**; `gems57-pooled-hide-v2`; 60,988 withheld positives).
  Against its same-fold feature ablation, the paired difference was **+0.0010**
  (95% CI **[−0.0006, +0.0027]**, same evaluator and positives), so improvement was not
  established. The ablation is *not* the prior best incumbent; that comparable test remains undone.
- Both continuous surfaces passed rank screening against all 167 files in a frozen, SHA-verified
  snapshot (maximum |ρ| **0.0975** for the final fitted surface). This is not a global novelty pass:
  unregistered/concurrent rasters may be missing, and the final-dot gate actually failed.
- The mathematical lattice bound would force more than 70% overlap for **any** ≥22,164 distinct
  footprint dots; it does not rule out all smaller budgets. The observed experiment's overlap was
  100%; the separate bound alone is not an observation. See [coverage evidence](evidence/lattice-coverage.json).
- GEMSDOE32's **0.2778** is an **unverified owner report**, not a confirmed receipt. In pinned
  mirrors, H33-B2 is exactly D2.8's 44,090 dots minus 6,436 within two pixels of mapped faults.
  Removing uncredited mass may help, but may lose recall; hidden labels do not establish causality.
- The public organizer leaderboard's leader was **0.4437 on 2026-10-26** (dated page observation,
  no archived response hash or link to this project). It may have changed; it is not a candidate score.

## Provenance and limits

The six required data files, including the ~419 MB 19-band competition-stack mirror, were restored
and SHA-verified. Actual model inputs were the owner-cached radiometric and LiDAR channels; the
19-band stack was validated, not used as a model feature. **Mirrors are not authenticated organizer
originals.** The sample mirror's positive pixels exactly match the known labels, despite the official
sample description; use it only for grid/footprint, never as a prediction feature. Derived caches and
shared-template code lack an established redistribution license; verify provenance/rights before
any competition use. The official null-outside format and the shared writer's zero-outside default
conflict; the shared template remains unchanged and needs a central fix or organizer clarification
before use. No physical fault or geothermal resource was independently confirmed.

The prompt refers to a named single-method paragraph that was not identifiable. Our research lane
was explicitly provisional, never claimed to be assigned. The frozen registry includes the nine focus
sites but cannot prove coverage of all current registries. The best same-evaluator prior incumbent,
a selector, account cap, organizer receipt and expert review remain unavailable.

## Reproduce checks without spending a slot

Prerequisites: Python 3.11, `gh` access to public pinned mirrors, network to GitHub. Data are ignored
by Git. Downloading the full data bundle is approximately 464 MiB and the registry adds more.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python scripts/install_template.py                    # 19 pinned unchanged shared modules
bash scripts/download_bilateral_data.sh            # six hash-pinned owner mirrors
python scripts/fetch_bilateral_registry.py                      # 167 frozen comparison rasters
OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/prepare_bilateral_data.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/check_lattice.py
.venv/bin/python scripts/check_run.py                 # receipt consistency, not a model rerun
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q
python scripts/build_site.py
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

The code for the frozen experiment is `scripts/run_experiment.py`; it refuses to overwrite an
existing run card. **Do not rerun or modify a candidate after the duplicate stop to seek a pass.**
Attempt 1 stopped on a local clock-variable bug; corrected replay was attempt 2 of at most three,
with no scientific settings changed. The record preserves the failure. `check_run.py` checks arithmetic
and gate consistency; synthetic tests compare unchanged shared evaluation code to an independent
small-grid definition and smoke-test the shared writer. No new prediction is produced by the checks.

The site automatically checks GitHub source freshness in the visitor's browser, not DrivenData. Its
[terms of use](https://www.drivendata.org/termsofuse/) prohibit automated website monitoring, so no
scheduled live leaderboard scraper is supplied. The leaderboard snapshot is explicitly dated.
Static Pages publication uses the repository's existing main-branch Pages configuration.

## Next authorized work

1. Obtain the actual assigned method lane and authenticate organizer inputs/derived-cache rights.
2. Resolve or amend the contradictory all-registry novelty requirement **explicitly**; refresh the
   live registry including concurrent work. A smaller budget is not automatically unique or better.
3. Only under an authorized new run, preregister a truly different hypothesis and evaluate it against
   the best comparable incumbent on the same folds, including leakage, novelty, provenance and CIs.
4. If everything passes, use the unchanged shared writer, reopen/validate exact bytes, and let a
   separate selector check the account-specific cap. Keep the submission-page receipt with the hash.

## Core values

**Maximize P(Win):** prefer defensible evidence, recall, novelty, and a truly comparable holdout over
unverified forecasts or spending a scarce slot on a duplicate.

**Own the Outcome:** make the stop obvious, preserve failures, automate independent checks, and make
uncertainty and exact next steps visible rather than presenting a placebo raster as a submission.

Prior concurrent-agent reports are retained under `docs/archive/`, `research/archive/`, and
`docs/legacy-*`; they are historical snapshots and must not override this run card.
