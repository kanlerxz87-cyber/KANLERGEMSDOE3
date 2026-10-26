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
