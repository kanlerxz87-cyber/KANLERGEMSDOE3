# KANLERGEMSDOE3 — GEMS research evidence desk

**Read this README at the start of each session.** Values: **Maximize P(Win)** and **Own the Outcome**.
The full operational request available to this session is embedded below and also maintained in
[`PROJECT_REQUEST.md`](PROJECT_REQUEST.md). The original long prompt's exact wording is unavailable in
the surviving context, so this reconstruction is not represented as verbatim.

## Executive decision — DO NOT SUBMIT

**No new TIFF, score estimate or approved download exists. No model experiment or competition slot was
used.** A hash-verified registry raster is positive in all 5,167,373 footprint cells. With the unchanged
shared template's literal `finite > 0` support and the required >70% 3-pixel overlap stop, **every
nonempty candidate has 100% overlap with that witness**. No silent exemption, private evaluator fork,
or fabricated TIFF is justified. One witness proves rejection; it is not a complete registry scan.

- [Executive site](docs/index.html) · [Submission guide](docs/executive-summary.html) ·
  [Scientific review](research/review.md) · [Four ranked hypotheses](research/hypotheses.md)
- [Machine-readable registry/lineage audit](evidence/audit.json) ·
  **[Current negative run card](evidence/run-card.json)** · [Review passes](research/verification.md)
- [Official metric guardrails](docs/METRIC.md) · [Shared-template documentation defect and failed upstream report](docs/SHARED_TEMPLATE_ISSUE.md)
- The previous reviews and independent nine-file audit remain available under `docs/`, `sources/` and
  `evidence/upstream/`; their status statements describe earlier snapshots and do not replace the
  current audit. Reported historical values are owner claims without a file-bound organizer receipt.

The user asked for a unique TIFF and training; the protocol's universal stop prevents producing either
honestly. The missing method-lane paragraph and organizer data authentication are additional unresolved
conditions. An explicit protocol clarification is needed before any model placement/selection. A separate
selector controls real weekly slots. No promise is made that a future method beats any leaderboard score.

## Reproduce the local audit

Requires Python 3.11+, GitHub CLI `gh`, and public repository access. No competition credentials are
requested. Downloads are cached under ignored `.cache/`; do not commit competition data or the 419 MB stack.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_assets.py --focus
.venv/bin/python scripts/audit_evidence.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_site.py
python -m http.server 8000 --bind 0.0.0.0
```

`--focus` restores nine prior artifacts. Optional `--features --external` also restore the pinned 19-band
feature image and selected owner-mirrored derivatives (roughly 0.5 GB total). Every file is hash-verified
before use. Hashes prove consistency with public mirrors—not an official data download, permission to
train, absence of leakage, or registry completeness. The official competition data tab required login.
Re-running the forensic audit refreshes its timestamp; it does not run a geological experiment.

A future file can be examined without changing it:

```sh
.venv/bin/python scripts/check_submission.py candidate.tif --surface surface.tif --out evidence/preflight.json
```

This checks saved bytes with the unchanged shared local format/uniqueness helpers against one decisive
witness. It exits nonzero and returns `ok_to_submit: false`, because one witness and local format checks
cannot establish a complete registry, valid holdout or selector approval. It never uploads. The shared
project's conservative all-finite export rule and the organizer's null/NaN-outside-bounds wording
are not the same guarantee; local validity is not organizer acceptance. The historical `scripts/validate_submission.py` uses a
separate outside-nodata interpretation and is not the canonical shared writer; neither interpretation
establishes portal acceptance without an actual receipt.

GitHub Pages is configured from `main` at the root; `index.html` links into the maintained `docs/` desk.
The site is an offline evidence snapshot, not a live scoreboard. Rebuild using `scripts/build_site.py`;
older parallel reports are preserved and may contain stale "not restored" status statements.

## Standing request (available operational transcription)

# Standing project request — operational transcription

Read this before every session. This is an operational transcription of the available user requirements, not a verbatim archive. The exact original long prompt is not present in the surviving session context; its full wording cannot be honestly reconstructed here. Do not treat this condensation as permission to ignore any original constraint. If a verbatim archive is required, it must be supplied again.

## Outcome and urgency

Review the repository and prior next steps. Build a clean GitHub Pages site with an executive summary and a submission-instructions subpage. The first screen must state whether download AND competition upload are permitted. Ultimately produce an easy-to-download, genuinely new single-band GeoTIFF matching the competition template, finite inside its footprint and with values in [0,1]. Avoid the previously reported range error. Provide a unique name and a short note (at most 140 characters). Do not relabel, copy, or trivially perturb a previous submission as new. Format validity is not scientific validity.

## Focus sites and score provenance

Review GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36 under https://github.com/buffedlizard55-lab. Their Pages sites use the same repository names, sometimes with `/docs/` paths. Table must clearly identify the historical best file per site, available evidence, any justified estimate, uniqueness, and submission permission. Study the reported H33 B2 result from GEMSDOE32, explain plausible performance mechanisms without invented causal certainty, and pursue an improvement.

The request gives multiple conflicting claimed current highs: 0.4413, 0.3195, and the focus-site historical 0.2778. These are unverified owner statements, NOT accepted scores. The supplied historical names/values for the nine sites are preserved in `scripts/review.py` and `docs/data/sites.json`. No organizer receipt was supplied. An estimate is not a score; do not present a projection as HOLDOUT-DTI or ORGANIZER-CONFIRMED.

## Parallel-run protocol (takes precedence over pressure to generate)

- Stay inside the assigned single-method lane. No lane paragraph is actually present in the received request; this is a blocker, not permission to invent one.
- Before placement AND on final dots, compare against every registry raster. Rank-correlation greater than 0.90 or more than 70% of dots within 3 pixels of any registry raster means duplicate: log and stop. Hash-only uniqueness is insufficient.
- Reuse canonical cached features, `evaluate_holdout.py`, and `submission_writer.py`. Fix shared defects once in the template, never maintain a private evaluator fork.
- Hide and recover whole fault segments with a buffer; all catalogue-derived features must use only visible faults. Mask visible faults pixel-exactly. Evaluate pooled DTI with alpha 0.2, beta 0.8, triangular 300 m kernel.
- Test every feature alone. AUC above 0.90 is leakage until disproved.
- Accepted result numbers must be HOLDOUT-DTI (evaluator version, withheld-positive count, 95% CI) or ORGANIZER-CONFIRMED (submission receipt). Unverified historical claims must stay quarantined and never be promoted into either class.
- End with one JSON run card: hypothesis, mechanism, named non-fault mimic, holdout and CI, registry correlation/overlap, raster hash, validator output, name, short note, and promote/negative verdict. Missing results remain null, not fabricated.
- Stop at three experiments or two hours. Negative results are deliverables. Promotion is separate from the weekly-slot selector; do not spend a slot without beating the same-evaluator holdout best and verifying the remaining cap.

## Research and implementation

Before implementation propose three to five geological hypotheses, naming layers, physical signature, rationale for missing mapped faults, difference from existing methods, cost and qualitative expected benefit. Validate the top candidate spatially before any slot. If external data is required, name a free official source and verify actual obtainability before declaring viability. Research geothermal relevance critically without confusing fault predictions with proven vent discovery. Preserve sources, uncertainty, irregularities, limitations and reusable knowledge. Use official sources for rules and data, not fabricated citations.

Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/
Description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
About: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
Data: https://www.drivendata.org/competitions/306/competition-doe-gems/data/
Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
Reference: https://github.com/drivendataorg/gems-prize-reference-solution
Report: https://docs.nlr.gov/docs/fy26osti/96647.pdf
USGS, INGEnIOUS and GDR research links are preserved in docs/research.md. User also supplied Dropbox mirrors; their existence does not establish official provenance or successful retrieval. No credentials may be requested or stored.

Aim for autonomous reproducible work, verified claims and no hallucinated results. Explicitly report network/data/auth limitations rather than asserting success. Carry out implementation, bug-review, and full-requirements-review passes. Open a PR, merge it onto main, and record unfinished work for the next session. Keep the fixed Arena branch. Core values: Maximize P(Win) and Own the Outcome.
