# GEMS Fieldnotes — evidence before submission

> **DO NOT SUBMIT.** No new candidate TIFF, calibrated score, or slot selection exists. Under the requested literal shared uniqueness rule, a registered probability raster is positive on **all 5,167,373 allowed cells** of the mirrored footprint. Any nonempty candidate therefore has 100% directed overlap with it, exceeding 70%, and must stop **before placement**. This finding is conditional on the hash-pinned owner mirrors and the shared rule; it is not an organizer ruling.

- [Open the GitHub Pages decision brief](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE3/) · [submission guide](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE3/executive-summary.html)
- [Executive review and nine-site table](research/executive-review.md) · [ranked hypotheses](research/hypotheses.md) · [machine-readable negative run card](data/run_card.json)
- [Measured stop certificate](data/protocol_certificate.json) · [nine-file forensic audit](data/portfolio_audit.json) · [immutable source and hash pins](data/focus_sources.json)

Historical TIFFs linked on the site are **research references only**, not approved downloads. The format-only validator cannot authorize a submission. No competition submission was made.

## Why this stop matters

The pinned `gems57.uniqueness` implementation defines support as `isfinite(x) & (x > 0)`. Its 3-pixel directed-overlap calculation counts a candidate cell as near a registry raster's support if it falls in that support's inclusive Euclidean disk. The [17GEMSDOE probability raster](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif) is positive on every mirrored sample-footprint cell; so even without the disk every nonempty support is a subset of the witness support. The measured blocker needs only **one** witness and does not depend on completing an inventory of all other rasters. It also doesn't grant permission to relax the scope.

An earlier calibration lattice alone covers 99.8713% of footprint cells within 3 pixels; for a 37,654-dot prediction it implies a theoretical overlap lower bound of 82.34%, **not** 99.4%. H33's measured relationships are stronger: it is exactly the 44,090-dot D2.8 mask after 6,436 dots within 200 m of the mirrored catalogue are removed. GEMSDOE36 contains all 37,654 H33 dots plus 1,200. The reported H33 score might reflect less redundant prediction mass, but its hidden-label cause is unproven.

The user-reported historic maxima for GEMSDOE24/25/27/28/30/31/32/33/36 are respectively **0.2477 / 0.2600 / 0.2449 / 0.2710 / 0.2600 / 0.2708 / 0.2778 / 0.2632 / 0.2750**. These are **USER-REPORTED**, not organizer-confirmed receipts or hash-bound scores. The audit finds that all nine fail the directed-overlap rule against at least one of the other eight. No new-file score estimate is defensible. The official public leader observed at approximately 22:01 UTC on 2026-10-26 was **0.4437**; this is a leaderboard observation, not a receipt for any of these files. It differs from the conflicting 0.3195 and 0.4413 figures in the user request, which should not be silently reconciled.

## Read this charter at the start of every session

The following is a **faithful working reconstruction of the owner's request and corrections**, not a claim to reproduce the original full chat verbatim; that full transcript is not present in this checkout. Re-read it before planning, modifying a shared tool, running an experiment, or recommending a slot. The guiding values are **“Maximize P(Win)”** and **“Own the Outcome.”**

1. Review **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36**. Provide an honest executive table with each historical best, precise file/link, score provenance, estimate only if calibrated, uniqueness against the others, and an unmistakable submission decision. Investigate why GEMSDOE32 `h33-h33-2-b2` was reported at 0.2778 and whether there is evidence for a better method.
2. Before running, rank **3–5 distinct, previously untried geological hypotheses** with named official data, transforms and signatures, a plausible uncatalogued-fault mechanism, prior-work distinctions, expected benefit/cost, and non-fault confounders. State when novelty or data availability is unverified. Work in **only the assigned method lane**; this request referred to a single lane but did not provide one.
3. Reuse the shared cached physical feature stack and shared `evaluate_holdout.py` / `submission_writer.py`. Do not privately fork the common tools; if they are wrong, correct them in their owning template once and report it. Hold out **whole fault segments with a buffer**, derive every catalogue feature from **visible faults only**, and mask visible faults pixel-exactly. Test every feature separately; AUC above 0.90 is leakage until proven otherwise.
4. Evaluate with the same pooled, distance-weighted Tversky implementation and strong same-evaluator baseline: α = 0.2, β = 0.8, 300 m triangular kernel. Give a spatial 95% confidence interval and paired control difference. Label any score **HOLDOUT-DTI** with evaluator version, withheld-positive count, and CI, or **ORGANIZER-CONFIRMED** only if supported by the submission-page receipt. Historical figures provided by the user remain **USER-REPORTED**. A projection is never a score.
5. Before placement **and** on final dots, check all accessible registry rasters. Surface Spearman > 0.90 or >70% of directed dots within 3 pixels is a duplicate and requires an immediate stop. Missing comparisons are **unknown**, never a pass. Do not copy, rename, or perturb a prior file and present it as a new submission.
6. Stop after **at most 3 experiments or 2 hours**; a negative result is a deliverable. Never select or spend an actual competition slot in the research lane. Only a later independent selector, subject to the real weekly quota, may recommend a file that beats the current comparable holdout best and satisfies every other gate.
7. If a candidate passes, produce a truly new single-band, correctly aligned [0,1] TIFF with an easy-to-find filename, link, and note ≤140 characters. Validate **the saved bytes**, automatically and without human inspection: dtype, band, finite values inside the footprint, range, CRS, shape, transform, and outside handling. Distinguish the official written null/NaN-outside spec from this repository's stricter all-finite local validator; do not promise organizer acceptance. Investigate the earlier portal “[0,1]” error without inventing a cause.
8. Provide a clean GitHub Pages site starting with an explicit **DOWNLOAD/SUBMIT** decision, a readable executive subpage and step-by-step future submission instructions, official links, a traceable table, and an automatic refresh strategy that exposes stale/error states. Put the request/goals in this README; verify claims line by line against trustworthy sources; do not hallucinate. Perform **three complete review/fix passes**. Create a PR, merge it to `main` if permitted, and explicitly report limitations and next steps.
9. End with **one JSON run card** containing hypothesis, mechanism, named non-fault mimic, holdout DTI/CI and context, registry correlation/overlap, raster SHA-256, validator output, submission name and note, and `promote` or `negative`. Nulls must stay null when the corresponding action was not done.

## Reproduce the audit

Python 3.11, GitHub CLI, and access to the public owner mirrors are required. Large inputs and derived caches are intentionally excluded from Git. Hashes prove the mirrors' byte identities, **not** their organizer origin. The official data and submission pages require authentication; this project has no organizer-authenticated copies or receipts.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# Restore and verify the pinned shared template and mirrored core data.
.venv/bin/python scripts/bootstrap.py --data

# Restore the exact witness and nine historic TIFFs by immutable commit and SHA-256.
.venv/bin/python scripts/fetch_audit_inputs.py

# Reproduce the nine-file direction-sensitive audit; rewrites its dated JSON receipt.
.venv/bin/python scripts/audit_portfolio.py

# Exit 2 is the expected hard stop; exit 3 would mean this witness is inconclusive.
# Neither outcome approves a candidate or authorizes an experiment.
.venv/bin/python scripts/preflight.py --out data/protocol_certificate.json

# Rebuild the static site after changing audit or feed data, then test it.
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q

# Local preview (no authentication or upload).
python3 -m http.server 4173 --bind 0.0.0.0
```

The optional `.venv/bin/python scripts/bootstrap.py --features` restores the same 35-channel physical cache. It can take several minutes and roughly 1.7 GB of storage. It does **not** run an experiment or create a candidate. Catalogue-derived channels from other caches must not be used across hide-and-recover folds unless rebuilt from visible faults only. The mirrored `labels.tif` and `existing_faults.tif` are byte-identical; these bytes support a catalogue-recovery proxy, not an independent hidden-organizer-label test. The mirrored sample's values also equal that label mask and are used only for the grid/footprint.

To check a future saved TIFF's **local format only**:

```bash
.venv/bin/python scripts/validate_raster.py path/to/file.tif
```

This reopens the exact file and compares it with the pinned owner-mirror grid. The local policy demands all finite grid values, including zero outside the footprint, whereas the [written organizer specification](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) calls for null/NaN outside bounds. Neither portal compatibility nor the cause of the past `[0,1]` error has been established. `format_ok` is never `ok_to_submit`.

## What is tracked

- `data/` holds auditable source pins, the executed blocker certificate, nine-file audit, timestamped public leader and peer-head freshness snapshots, and negative run card. It contains no competition TIFF or feature cache.
- `scripts/bootstrap.py`, `fetch_audit_inputs.py`, `preflight.py`, `audit_portfolio.py`, and `validate_raster.py` restore and examine pinned bytes. Missing or modified files fail closed.
- `research/` records method ranking, supporting official links, important counterexamples, and full limitations.
- `site/` and `assets/` are the source for the root static Pages site. `scripts/build_site.py` deterministically renders the nine-site table from the recorded audit.
- `scripts/update_feed.py` checks the public leaderboard; `scripts/update_peer_feed.py` checks the nine GitHub repo heads, not their science or scores. `.github/workflows/pages.yml` is designed to refresh both every six hours on GitHub Pages. It retains a dated snapshot and explicit error/stale states on failure; scheduling or deployment still depends on repository permissions and Pages configuration. A changed peer head means the static audit may need repeating, not that the new content is correct.
- `tests/` contains small synthetic and safety tests; the blocker and historical audit additionally rely on the pinned, much larger witnesses. `research/review-log.md` records the three review/fix passes and their scope.

## Official references

- [Problem, metric, grid and file requirements](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) · [DOE GDR INGENIOUS](https://gdr.openei.org/submissions/1391)

This is independent research, not an organizer site. Check the current official competition pages and rules before any future action.
