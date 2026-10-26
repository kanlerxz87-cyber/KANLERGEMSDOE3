# Executive scientific review — 26 October 2026 UTC

## Decision

**Negative. No new TIFF exists; nothing is authorized to download for submission or upload. No weekly
slot was used and no model/holdout experiment was run.** This is not a high-scoring-model claim.
The user’s literal parallel-run rule requires a stop for any registry raster with >70% of candidate dots
within 3 pixels. A locally restored and SHA-verified prior is positive in **all 5,167,373 footprint cells**.
Under the unchanged shared template’s `finite & (value > 0)` support definition, every nonempty candidate
inside the footprint is within zero pixels of that raster. Its directed overlap is 100%, including after
masking the catalogue (5,106,385 eligible cells). One witness is enough to prove rejection; we have **not**
claimed to complete the registry. See the reproducible [audit](../evidence/audit.json) and
[run card](../evidence/run-card.json).

An independent spacing-5 lattice covers 5,160,724 of 5,167,373 cells within 3 pixels. At least 30% of a
candidate's dots would have to occupy the 6,649 uncovered cells; more than 22,163 distinct dots must
therefore fail against this prior alone. This remains a blocker for many historical-size candidates even
if a future authorized protocol explicitly revises the dense-surface rule. No exemption, rethresholding,
or unapproved reinterpretation was silently introduced.

## Historical comparison, not a leaderboard receipt

The previous reviews recovered nine historical TIFFs. This session re-verified their hashes and computed
72 directed pairwise overlaps and exact binary Spearman correlations on the valid footprint. Every directed
overlap between the nine is above 70%. These are **geometric registry measurements, not HOLDOUT-DTI scores**.
The main [executive summary](../docs/index.html) reports the nine owner-provided historical highs with
explicit unverified labels and links to exact pinned files for research only. No identified organizer
submission-page receipt ties any of these scores to a TIFF hash; lack of such a receipt is not proof a
submission was never scored. The latest checked public leaderboard snapshot was 0.4437 on 26 October 2026;
it is context, not an accepted file-bound result under the project receipt rule, and it may change. No new leaderboard score can be estimated
reliably from this audit.

The exact decoded masks establish: GEMSDOE25 = GEMSDOE30 on the footprint; GEMSDOE31 = GEMSDOE25 after
removing its 1-pixel mapped-catalogue collar; GEMSDOE32 = GEMSDOE25 after removing its 2-pixel collar.
That removes 3,891 dots from 25 to 31 and a further 2,545 from 31 to 32. GEMSDOE36 contains all 37,654
GEMSDOE32 dots plus 1,200 others. Mask identity is not byte identity or proof of method causality. Sparse
thinning plausibly reduces uncredited prediction mass but could remove true positives; without paired,
leakage-free ablation and private labels, the reported 0.2778 cannot be causally attributed or forecast.

## Inputs, provenance and trustworthy classes

The original base commit contained only a README title; the claim that this checkout already had a fully
integrated GPU pipeline was not true at that point. Concurrent review work on main was integrated without
deleting its evidence archive. This continuation recovered, verified and cached an owner-mirrored sample,
catalogue, 19-band feature raster, selected geological inputs and an unchanged shared template pinned to
`buffedlizard55-lab/GEMSDOE31@597b04cd1afb65d1ebbe3e9417fd952be48e3d74`. The cache is gitignored and
reconstructible with `scripts/restore_assets.py`. SHA-256 pin checks establish **mirror integrity**, not
organizer authorization, raw-data provenance, license clearance, leakage safety, or fitness for training.
The mirror sample has 60,988 positive pixels and reproduces the provided catalogue; use its grid and
footprint only, never its positives as a prediction or a feature.

The official [data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirected
to login. Official problem, leaderboard and geological overview pages were read through the web tool, while
the sandbox command network is limited to GitHub and package registries. A public page fetch is not an
authenticated download. No participant was asked for credentials. A GPU is not available here (`nvidia-smi`
not found), but the [official reference](https://github.com/drivendataorg/gems-prize-reference-solution)
also supports CPU execution.

- **REGISTRY-MEASUREMENT:** reproducible raster support/overlap/lineage counts; not predictive performance.
- **HOLDOUT-DTI:** only a pooled, spatially withheld result with evaluator version, withheld count and CI;
  none produced in this session.
- **ORGANIZER-CONFIRMED:** only a number copied from a submission receipt tied to exact bytes; none found.
- **Owner report / projection:** useful lead, not a score established by this review; never silently relabel.

The [official metric and grid rules](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
require float32 single-band probabilities [0,1], EPSG:32611 on the supplied 100 m grid, with a 300 m
triangular distance kernel and Tversky α=.2, β=.8. The organizer requires data outside the bounds to be null or NaN; the pinned shared project
writer instead enforces an **all-finite** local export policy. Their treatment of the irregular internal
footprint is not automatically equivalent, and these are not the same guarantee. Local format validation does not prove acceptance by the portal; check its
current documentation and exact output bytes. Never clip invalid predictions to hide an error.
See the [exact metric guardrails](../docs/METRIC.md). A synthetic counterexample also revealed a
[shared-template docstring defect](../docs/SHARED_TEMPLATE_ISSUE.md), not a demonstrated evaluator defect;
upstream issue creation was denied by the GitHub integration. No private fork was introduced.

## Remaining steps, without overriding the stop

1. Preserve the literal witness and request an **explicit protocol clarification** if research should
   proceed despite it. The method-lane paragraph is missing, and no lane was assigned in this run.
2. Obtain and document the authorized official inputs, actual source licensing, full applicable registry,
   same-evaluator incumbent and any training permissions. Hash pins alone do not establish these.
3. Only if the protocol permits: validate the [ranked hypotheses](hypotheses.md) using whole-segment,
   buffered, visible-only feature reconstruction; test individual-feature AUC; run matched pooled DTI
   with 95% block-bootstrap CI and paired improvement; repeat surface and final uniqueness; use the
   unchanged shared writer and validate its saved output. Maximum three experiments/two hours.
4. A separate selector checks weekly cap and slot authorization. It—not this research run—may choose an
   eligible file. Preserve the exact uploaded SHA and organizer receipt. No automatic upload exists here.

Core sources: [official problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[competition](https://www.drivendata.org/competitions/306/competition-doe-gems/),
[leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/),
[reference solution](https://github.com/drivendataorg/gems-prize-reference-solution),
[owner's prior review](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/research/arena9-results-and-nine-site-executive-summary.md),
[USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
and [GDR INGENIOUS](https://gdr.openei.org/submissions/1391). Original archived reviews are snapshots and
may describe an earlier state; this page and the current run card supersede their status statements.
