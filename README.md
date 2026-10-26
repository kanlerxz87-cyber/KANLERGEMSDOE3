# KANLERGEMSDOE3 — DOE GEMS Prize fault discovery (lane **GPC-3**)

**Core Values — Maximize P(Win):** every weekly submission slot is an experiment,
not a lottery ticket; we weigh tradeoffs and choose the path that maximizes the
probability of winning. **Own the Outcome:** we own results end to end; every
claim carries an evidence label and failures are published, not dropped.

## 🚦 Submission status (automated, no human inspection)

<!-- STATUS:START -->
**🔴 DO NOT SUBMIT — verdict: negative (research download only).**

- **File (research):** `docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif`
  (SHA-256 `16ec0585a884224460f0e5d09e7448a54ab5a3348db92279452a9a4e0453b0f7`, 37,654 dots;
  ZIP alongside it). Also on the site: `docs/index.html`.
- **Unique submission name:** `kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be`
- **Note (82/140 chars):** `GPC-3 EXP-2 phase-concordance 37654d | HOLDOUT-DTI 0.1377 | NEGATIVE do not submit`
- **Evidence:** HOLDOUT-DTI 0.137681 [0.125567, 0.150331] (gems-segment-pooled-v1,
  60,988 withheld), paired Δ vs control +0.005174 [0.000390, 0.010042]; canary PASS;
  validator PASS (`portal_range_ok: true`); uniqueness vs the 9 focus champions
  PASS (max surface |ρ| 0.097 ≤ 0.90; max dots within 3 px 46.3% ≤ 70%).
- **Why withheld:** 0.137681 < recorded same-evaluator group best 0.16379
  (GEMSDOE24 DPRF1). The gate is fail-closed; a future lane may only reuse this
  name/note pattern after it *promotes*. Leaderboard estimate: **not estimable**
  from holdout evidence — no projection is written as a score.
<!-- STATUS:END -->

## Project brief (the prompt this repo is built from — read before every session)

> Review the repo. Focus on the highest-scoring submissions from GEMSDOE24,
> GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33,
> GEMSDOE36. Produce an executive summary per site making obvious which is the
> best submission to submit for a high leaderboard score. It must be unique —
> not an exact duplicate of any previous submission. Keep iterating and testing
> until we have the highest-scoring submission to download and submit. We must
> be able to estimate the score for a submission: a table in the executive
> summary listing what file to download, the estimated score, and whether it is
> unique unlike the other GEMSDOE sites. **Highest urgency: generate a UNIQUE
> TIF submission. Do not copy a previous submission except for learning. It
> must be obvious whether the generated TIF is OK to download and submit.**
> Many sites mention human inspection — inspection here is automated through
> the project and validated without human intervention.
>
> Parallel-run protocol: (1) stay in your lane; if rank-correlation vs any
> registry raster > 0.90 or > 70% of dots fall within 3 px of one registry
> raster, log it as a duplicate and stop — check the surface before placement
> and the final dots. (2) Reuse the template's cached feature stack,
> evaluate_holdout.py and submission_writer.py; holdout = hide-and-recover
> whole fault segments with a buffer, catalogue features only from visible
> faults, visible faults masked pixel-exactly, pooled DTI (α 0.2, β 0.8, 300 m
> triangular kernel). (3) Label every number HOLDOUT-DTI (evaluator version, n
> withheld, 95% CI) or ORGANIZER-CONFIRMED (submission-page receipt); a
> projection is never a score. (4) Leakage canary per feature: AUC > 0.90 means
> leakage until proven otherwise. (5) End with one JSON run card. (6) Budget:
> ≤ 3 experiments or 2 hours; promotion to a real slot is a separate selector
> step within the weekly cap.
>
> Study why GEMSDOE32's `h33-h33-2-b2` scored 0.2778 (the focus-site best) and
> whether we can beat it, with PhD-level judgement, no hallucinations, verified
> line by line from official sources. The competition is DrivenData #306
> (DOE GEMS); older prompt text citing 0.3195 / 0.4413 as the leaderboard top
> is stale — re-check the live leaderboard every session (0.4437 on
> 2026-10-26, IR-01).
>
> Before implementing, generate 3–5 new geological hypotheses naming layers,
> physical signature, why each catches faults missing from the USGS/INGENIOUS
> catalogue, and how it differs from anything already implemented; rank by
> expected DTI gain and cost; validate the top candidate on the spatially
> blocked holdout before spending a submission slot; if a candidate needs new
> external data, name the free official source and check obtainability first.
>
> The deliverable problem to solve: a site where the correct file is obvious
> at first glance, downloadable in one click, with an executive-summary subpage
> explaining exactly how to submit — solving manual checking and giving an
> up-to-date current feed. A previously downloaded file returned the portal
> error “Predicted values must be in range [0, 1]”: the submitted file must be
> whole-array [0, 1] (the `-zeros` encoding), with a unique name and a short
> (≤140-char) note for the submission form.

Full source list: `docs/research/sources.md`. Hypotheses: `docs/research/hypotheses.md`.

## What this repo did (2026-10-26 session)

1. **Reviewed all 9 focus sites** and re-measured their champions from
   SHA-256-verified bytes (`evidence/forensics_focus9.json`): GEMSDOE32
   0.2778 is the family best, and it is a *deletion ladder* — the 0.2600 field
   minus 3,891 dots ≤1 px (→0.2708) minus 2,545 dots 1–2 px (→0.2778) from the
   catalogue, zero new coordinates. Proof and beating arithmetic:
   `docs/research/why-02778.md`.
2. **New lane GPC-3** (not in any focus repo): amplitude-invariant
   gradient-*phase* concordance across RTP magnetics, isostatic gravity,
   depth-to-basement and detrended elevation (`src/kanler3/gpc.py`).
3. **Validated on the shared evaluator** (`gems-segment-pooled-v1`, 60,988
   withheld positives): see Results.
4. **Generated one unique TIF**, validated whole-array [0, 1] and against all
   9 champions, published on the site with an explicit verdict.

## Results (all HOLDOUT-DTI, gems-segment-pooled-v1, 60,988 withheld, 95% CI)

| Arm | HOLDOUT-DTI | 95% CI | Paired Δ vs B0 [95% CI] |
|---|---|---|---|
| B0 (59-feature control) | 0.132508 | [0.120689, 0.144628] | — |
| EXP-1 (B0 + 15 GPC) | 0.137224 | [0.124884, 0.150399] | +0.004717 [0.000177, 0.009529] |
| **EXP-2 (B0 + 12 GPC concordance)** | **0.137681** | [0.125567, 0.150331] | **+0.005174 [0.000390, 0.010042]** |
| EXP-3 (EXP-1 + B2 collar) | 0.137224 | identical dots to EXP-1 in holdout (0 differing px/fold; min dot→visible distance ≥23 px, so the collar is structurally inactive under segment holdout) | +0.004717 |

Leakage canary: **PASS**, worst two-polarity AUC 0.6749 (limit 0.90)
(`evidence/leakage_canary.json`). GPC is a real, statistically supported
signal (+0.005, CI excludes 0, 3/4 folds) — and still below the recorded
group best 0.16379 (GEMSDOE24 DPRF1, same evaluator). **Verdict: negative.**
No leaderboard estimate is claimed: HOLDOUT-DTI is not a leaderboard score.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
bash scripts/download_competition_data.sh        # pinned mirrors (IR-04)
.venv/bin/python scripts/prepare_data.py         # audit + prepared_manifest
.venv/bin/python scripts/forensics_focus9.py     # champion anatomy (learning)
.venv/bin/python scripts/fetch_registry.py       # 9 champions, hash-verified
.venv/bin/python scripts/evaluate_holdout.py --phase canary
.venv/bin/python scripts/evaluate_holdout.py --phase holdout
.venv/bin/python scripts/evaluate_holdout.py --phase final
.venv/bin/python scripts/validate_submission.py docs/downloads/<file>-zeros.tif
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest tests/ -q
```

## Limitations & next steps

- **No DrivenData auth in this sandbox**: data are owner-supplied GitHub
  mirrors, hash-pinned but not organizer-authenticated (IR-04).
  `scripts/download_competition_data.sh` documents the manual official route.
- **The gap to 0.16379 (holdout) and to 0.4437 (leaderboard) is a detector
  problem.** Next ranked candidate: STEP-THROW signed step profiles
  (`docs/research/hypotheses.md` #2), then the 1 m DEM scarp-profile lane (#5),
  which needs the official USGS 3DEP tiles via `1m_DEM_links.csv` — free, but
  outside this sandbox's network allowlist.
- Promotion to a real slot is a separate selector decision; this repo's gate
  is fail-closed and its current answer is **DO NOT SUBMIT**.


---

## Merged parallel-session record (from origin/main PR #4/#7 — forensic-only session, preserved on merge)

> The session merged into main before this lane produced a forensic-only
> negative (no new TIFF; archived site: `docs/parallel-forensic-index.html`,
> archived scripts: `archive/parallel-forensic/`). This GPC-3 lane supersedes
> its "no eligible TIFF exists" finding by generating and validating the
> unique TIF above, while keeping the same DO-NOT-SUBMIT verdict for a
> different reason (holdout bar, not eligibility). Its full README follows.

# KANLERGEMSDOE3 — evidence before submission

**Start every session by reading this README, [standing requirements](research/standing-requirements.md),
[review / continuation](research/review.md), and [run card](docs/run-card.json).**

## Current executive decision: DO NOT SUBMIT

[Executive summary](docs/index.html) · [How to submit](docs/executive-summary.html) ·
[Ranked hypotheses](research/hypotheses.md) · [Independent audit](docs/audit.json)

No new eligible TIFF or score estimate exists. Nine historical best masks were restored from pinned
GitHub mirrors and hash-checked for forensic learning. All 72 directed overlap comparisons exceed the
requested 70% stop. Strict validation against the owner-mirror sample mask passes for only 2/9 historical
rasters; the other 7 use valid zeros outside the footprint rather than null/nodata. No historical artifact
is being relabelled as a unique entry. No weekly slot was consumed.
This is a **negative research deliverable**, not a completed high-scoring model.

The initial checkout contained only this README's title. Claims in the project request about an existing
GPU pipeline, cached stack or a single remaining data-placement blocker were not true for this checkout.
A single method lane was not supplied. Full prompt requirements are **not yet fulfilled**; see continuation.

## Reproduce the three review passes

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python scripts/restore_audit_data.py   # gh authenticated; pinned hashes; ~8 MB, ignored by Git
.venv/bin/python scripts/audit_rasters.py
.venv/bin/python -m unittest discover -s tests -v
python scripts/build_site.py
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

Pass 1: source audit, pinned raster recovery, independent geometric comparisons and executive site.
Pass 2: tests for directional overlap, exact distance boundary, invalid values, grid mismatch and
fail-closed reporting; fix failures before proceeding.
Pass 3: reconcile original scientific requirements, identify unmet gates, verify source snapshot integrity,
rebuild docs and repeat tests. Details: [verification log](research/verification.md).

`scripts/refresh_sources.py` explicitly refreshes third-party source snapshots (not a verified live feed).
It needs GitHub `gh` access. Do not silently replace reviewed evidence with moving-branch claims.
`scripts/audit_rasters.py` is a read-only forensic validator, **not a private competition evaluator or writer**.
The snapshots of the canonical shared scripts import dependencies that have not been restored.

## Website and publication

The static site is in `docs/`. The existing legacy Pages configuration publishes main at the root; the root index redirects to docs/.
A verification workflow is retained; actual publication status must be checked rather than assumed.
The home page prominently separates file-format validity from scientific eligibility. There is deliberately
no approved-TIFF download link while validation is blocked.

## Core values

**Maximize P(Win):** prefer honest negative results and defensible spatial validation over speculative
leaderboard forecasts, duplicated raster tweaks or spending scarce submission slots.

**Own the Outcome:** preserve evidence, automate checks, expose blockers, and document the next concrete
experiment rather than claim unperformed training or verification.

## Concurrent-main integration

Main changed during this run. Its evidence archive, gate/schema tests, source reports and standing
`PROJECT_REQUEST.md` were merged without deleting them. The previous active dashboard is preserved at
[parallel review](docs/parallel-review-dashboard.html), with its README at
[parallel review README](docs/parallel-review-readme.md). `scripts/review.py` now rebuilds archived
dashboards rather than overwriting the active independent-raster-audit summary. The active run card
for this session is `docs/run-card.json`; other run cards remain historical evidence.
