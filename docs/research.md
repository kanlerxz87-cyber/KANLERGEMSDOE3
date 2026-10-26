# Scientific review and preregistration — 26 October 2026

## Audit scope and limits

The base checkout was only a 16-byte README. No previous-session pipeline or next-step log exists locally. We retrieved immutable GitHub tree snapshots, README and landing-page content, available shared evaluator/writer files, and selected registries from all nine focus repositories. `evidence/snapshot_hashes.json` records the downloaded bytes. These are owner-maintained research repositories, not official competition receipts. This is a targeted audit, not verification of every line in those repositories.

The prompt says “single method paragraph below” but contains no assigned method paragraph. Running an invented lane would risk colliding with simultaneous sessions. Experiments run: none. New rasters generated: none. No competition slot used. This is a negative readiness result, not evidence that any geological hypothesis is false.

GitHub mirrors of the input data are discoverable: see the pinned GEMSDOE32 `registry/data_manifest.json`. Their own warning states that hashes prove mirror consistency, not organizer authentication. Data absence is therefore not proof that public mirrors are unobtainable. We did not download a large stack or start training with an unspecified lane and unverified provenance. The historical claim that a GPU is mandatory is not supported: the official reference README explicitly supports CPU-only execution (slower).

## What the evidence says about the historical best

GEMSDOE32's pinned landing page labels the historical H33 B2 result as an owner report, explicitly says no submission-page receipt links its hash to that claim, and says not to resubmit it. Its name suggests a B2 exclusion/placement variant, but the name does not establish its implementation or causal performance gain.

Sparse predictions can trade false-positive mass against distance-tolerant recovery. This is a plausible explanation for dotted families performing differently from continuous fields, not proof about hidden organizer labels. A smaller false-positive penalty does not make arbitrary extra dots free. Placement, coverage, and proximity to actual withheld faults still matter. We cannot infer a better leaderboard result by extrapolating these claims or tune directly against a handful of public results without selection bias.

A separate upstream “winning variant” card reports high overlap with D2.8 yet says promote. That contradicts the literal current uniqueness protocol. Another upstream review flags full-catalogue masking in a historical holdout. Both are reasons to re-evaluate, not to trust historical promotion flags.

The request contains incompatible “current best” claims (recorded in the request brief); none is treated as a verified current leaderboard. Competition submission receipts and the weekly remaining cap are unavailable in this checkout. No numerical leaderboard estimate is published.

## Candidate geological hypotheses — proposed, not tested

Ranking below is a qualitative expected-value judgment, NOT a projected score or proven novelty. No candidate is approved for implementation until a lane is assigned. The local repository had no methods, so all differ from its base; the nine upstream hypothesis registries contain extensive overlapping work. A full semantic novelty check is still outstanding. Layer names and availability must be checked against the actual cached stack before viability is claimed.

| Rank | Candidate / layers | Physical signature and missing-fault rationale | Difference and confounder | Cost / viability |
|---|---|---|---|---|
| 1 | Magnetic–radiometric displacement consistency; magnetic field and K/Th/U channels | Estimate opposing-side multichannel texture displacement across a candidate boundary; require consistent offset direction across scales. A buried shear discontinuity may have little surface expression and therefore be absent from mapped surface faults. | Test lateral offset consistency, not simple edge magnitude, curvature concurrence, or radiometric fusion. Lithologic contacts and survey seams mimic offsets. Broad fusion exists upstream; exact displacement method novelty unproven. | Medium–high; conditional on channel coverage and acquisition-seam masks. |
| 2 | Elevation–magnetic vertical separation; elevation and potential-field channels | Compare multi-scale upward-continuation edge positions with terrain scarps; stable subsurface edges displaced from surface gradients could indicate blind dipping structures. | Model scale-dependent lateral edge migration, rather than merely detecting Euler depth clusters or pre-existing tip projection. Remanent magnetization and contact dip can mimic it. Related depth/dip methods already exist upstream. | High; requires justified field conventions, depth resolution, and holdout stability. |
| 3 | Radiometric transport asymmetry; K/Th/U and elevation | Test whether cross-slope radiometric asymmetry persists after conditioning on downslope sediment transport; an alteration corridor cutting drainage could indicate a permeable structure missing from surface catalogues. | Residualize drainage transport before detection, not just rank anomalies. Parent lithology, soil moisture and alluvial mixing mimic alteration. Generic radiometric/terrain fusion is not novel. | Medium–high; conditional on stable coverage; extra official lithology may be necessary. |
| 4 | Geophysical phase discontinuity without amplitude edges; magnetic field | Detect persistent local phase jumps in normalized multiscale bandpass responses while controlling amplitude; weak covered discontinuities may escape amplitude detectors and mapping. | Phase-residual hypothesis, not another thresholded ridge ensemble. Gridding seams and flight-line leveling errors mimic it. Must check upstream phase/tilt methods first. | Medium; conditional on seam metadata and adequate signal/noise. |

No new external source is claimed obtainable here. If lithology is necessary, USGS National Geologic Map Database / State Geologic Map Compilation is the official source to investigate; its data endpoint, license, scale and actual download must be verified before declaring that candidate viable. None of these hypotheses claims direct identification of geothermal vents: the task is fault prediction, with geothermal relevance as a downstream interpretation.

## Required experiment protocol

1. Reuse an identified, hash-pinned shared template cache, `evaluate_holdout.py`, and `submission_writer.py`. Retrieved upstream source files are evidence only; no private evaluator fork was created. An upstream defect must be fixed in its shared template before adoption.
2. Freeze whole fault segments and spatial blocks with buffers. For each fold, discard all hidden-fault-derived features, rebuild every catalogue feature from visible segments, and mask only visible faults pixel-exactly. Audit all inputs including exclusion masks for hidden-label leakage.
3. Test every feature individually. An AUC above the specified canary threshold blocks trust until leakage is disproved; a lower AUC does not prove absence of leakage. Report background sampling and spatial confidence intervals.
4. Compare candidate and incumbent on exactly the same folds, domain and evaluator. Report pooled HOLDOUT-DTI with evaluator version, withheld-positive count and segment/block bootstrap confidence intervals, plus a paired improvement interval. Do not average fold ratios as a substitute for pooled counts. Use the requested triangular distance kernel and weighting, verified against the official implementation before release.
5. Check every registry raster on the continuous surface before placement, then final dots. Stop as duplicate if the literal correlation or proximity threshold is breached. Do not exempt dense calibration lattices silently; flag if these make the protocol infeasible. SHA difference alone is never geological uniqueness.
6. Validate the saved GeoTIFF bytes against the actual template: one band, exact CRS, dimensions and transform, finite values inside footprint, range compliance. Our proposed release gate conservatively requires all-grid finiteness as well to avoid sentinel/range failures outside the mask.
7. Maximum three experiments or two hours; stop on duplicate. Promotion requires a same-evaluator holdout win, not an owner score or projection. A separate selector checks the authenticated submission page and weekly cap; the gate script never allocates a slot.

## Sources and verification status

- Official reference solution: https://github.com/drivendataorg/gems-prize-reference-solution — README retrieved at commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`; supports CPU and requires obtaining competition data separately.
- Official task description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ — supplied link; not fetched in this network-restricted run.
- Official leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ — not fetched; current standings unknown.
- Official submission/data access: https://www.drivendata.org/competitions/306/competition-doe-gems/data/ — not fetched; no authenticated access used.
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and — research lead supplied by user, not verified here.
- GDR: https://gdr.openei.org/submissions/1391 — research lead supplied by user, not verified here.
- Competition report: https://docs.nlr.gov/docs/fy26osti/96647.pdf — not retrieved; no rules attributed to unread PDF.
- INGEnIOUS: https://gbcge.org/current-projects/ingenious/ — research lead, not verified here.

Outbound network access is restricted to GitHub and package registries. We cannot independently fetch the organizer pages, Dropbox, USGS or the report in this environment. This is not a verified login redirect, and does not establish that the public resources are globally unavailable. Do not ask for or store credentials. Authenticated receipt, cap and rules verification must use an approved future access path.
