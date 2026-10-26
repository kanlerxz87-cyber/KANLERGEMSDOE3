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
