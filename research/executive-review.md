# Executive review — evidence and decisions

**Review completed:** 2026-10-26 UTC. **New competition-ready file:** none.
**Do not submit any file from this review.** The historical links are reference
material only. The best number in the owner's nine-site list is an unverified
claim, not an authenticated submission result. A leaderboard forecast for a
new file is not estimable from these correlated historical examples.

## What we independently checked

We downloaded the nine named historical TIFF encodings at immutable Git commits,
checked their published SHA-256 pins, opened their pixels against an owner-mirror
sample grid, and computed directed Euclidean three-pixel overlaps and full-footprint
binary Spearman correlations. The exact inputs and results are in
[`data/portfolio_audit.json`](../data/portfolio_audit.json). It is **not** a full
inventory of all past, private, or concurrent submissions. SHA checks establish
mirror identity, not origin, permission, or the association between a claimed
score and a submitted file. Original continuous pre-placement surfaces were not
available and were not inferred from final masks. The following historical
numbers are **USER-REPORTED / UNVERIFIED**, not organizer-confirmed scores.

| Site | Highest result in the supplied list | What the reopened file shows | Guidance |
| --- | --- | --- | --- |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5`, claim **0.2477** | 60,069 dots; 100% of them lie within 3 px of the GEMSDOE30 reference. | Historical research only. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8`, claim **0.2600** | 44,090 dots; decoded in-footprint values are identical to GEMSDOE30. | Historical research only; different encoding is not a new prediction. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5`, claim **0.2449** | 61,328 dots; 98.02% are within 3 px of GEMSDOE24. The site's newer approval banner does not establish compliance with this broader literal gate. | Historical research only; no selector approval here. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1`, claim **0.2710** | 37,660 dots; 100% are within 3 px of GEMSDOE30. Proximity does not mean these files have equal pixels. | Historical research only. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090`, claim **0.2600** | 44,090 dots; pixel-identical in the footprint to GEMSDOE25. | Historical research only. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28`, claim **0.2708** | 40,199 dots; all are within 3 px of GEMSDOE30. Other sites make additional unverified claims, and GEMSDOE31's own banners conflict. | Historical research only; don't interpret inconsistent site banners as approval. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2`, claim **0.2778** | 37,654 dots; exactly the GEMSDOE25/30 D2.8 set after removing 6,436 cells within 2 px of the mirrored catalogue. | Highest **claimed** number in the supplied nine-site list, not a new candidate; do not resubmit. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30`, claim **0.2632** | 41,865 dots; 99.71% lie within 3 px of GEMSDOE27. It is not proven to be a simple H33 superset. | Historical research only. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854`, claim **0.2750** | 38,854 dots: all H33 dots plus 1,200 others. | Historical research only. |

Each candidate's distance is measured in **its** direction: “A near B” is not
interchangeable with “B near A.” A 3 px overlap failure is a protocol flag, not
proof that another researcher copied a method.

## Concurrent site updates — observed around 22:06 UTC

The independent forensic table above remains pinned to the historical files,
not to moving page banners. By 22:06 UTC, eight of nine GitHub heads had changed
since this review began. The following page observations are **peer-reported,
not independently replayed**; newer sources can change again:

- [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) reports
  S3DEP1 **HOLDOUT-DTI 0.16606**, evaluator `gems-segment-pooled-v1`, 60,988
  withheld positives, 95% CI `[0.15186, 0.18034]`. Its paired difference vs
  DPRF1 is `+0.00227`, 95% CI `[-0.00699, 0.01144]`; it reports a 71.32%
  overlap with another local lane and says **do not submit**. This is not an
  organizer score or a proven improvement. The run was not reproduced here.
- [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) says its H31-1
  passes a **27-raster** evidence scope and simultaneously requires a separate
  selector; older text lower on the same page calls it a file to upload now.
  Those statements do not establish compliance with the full literal registry
  witness above or override this session's stop. The page also cites a different
  GEMSDOE31 owner-reported maximum (0.2710) and a GEMSDOE28 maximum of 0.2708,
  reversing the user's reported 0.2708/0.2710 ordering. No organizer receipt
  binds those alternate claims to their files; the quoted GEMSDOE31 alternate
  filename was not found in the checked current repository archive. We preserve
  the user's values in the table instead of silently substituting an unverified
  number.
- [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) describes a
  negative research run checked against 22 rasters; its new banner is dated
  2026-10-27 UTC even though the page was retrieved on 2026-10-26 UTC. Its
  limited comparator scope and future-dated banner cannot clear our gate.
- [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/),
  [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/) and
  [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) now show
  research-only negative decisions. Some narrow uniqueness counts omit the
  blocking witness; they are not a complete-registry clearance.

No newer TIFF, model fit, holdout result, or portal receipt from these sites was
replayed by this session. A head-change feed flags staleness rather than
pretending to audit or score new work.

## Why H33 might have improved — and what cannot be concluded

The official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
defines a 300 m triangular distance kernel and
`DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw)`. A prediction may contribute to multiple
truth cells, but each truth cell takes the **maximum** distance-weighted
prediction. Therefore closely spaced dots can buy little additional TP credit
while still increasing FP cost. Thinning a clustered field and removing a
low-yield catalogue-near annulus is a plausible explanation for the relative
owner-reported results. It is **not** proof: the hidden organizer labels and
per-pixel credit are unavailable and the score-to-raster mapping lacks receipts.

More precisely, write `T = TPw`, `F = FPw`, `G = number of positive truth cells`,
so `FNw = G - T`. If removing dots loses true-positive credit `L` and removes
false-positive cost `S`, the ratio improves, ignoring the tiny numerical epsilon,
only when `L * (0.2 F + 0.8 G) < 0.2 T S`. Neither side is known for the
organizer's hidden test set. The pruning fact supports a hypothesis about a
tradeoff; it cannot prove that pruning *caused* the claim or that another prune
will outperform it.

The leading official public leaderboard was **0.4437** when retrieved on
2026-10-26 around 21:38 UTC. This is an **organizer-published public-leaderboard
observation**, not a receipt for H33 or for any file here. It supersedes neither
the private evaluation nor a future leaderboard refresh. The prompt's 0.3195
and 0.4413 are inconsistent historical targets; the direct public page provides
the later observation. See the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## The hard stop: literal registry uniqueness

The shared template defines positive finite support as dots at **both** surface
and final phases. A registered [17GEMSDOE probability raster](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif)
(SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`)
was re-fetched and checked against the pinned sample. It is finite and strictly
positive on **all 5,167,373** footprint cells. Thus every nonempty candidate
support lies at zero distance from that raster and has **100%** directed
within-3-px overlap, exceeding the mandated 70% limit. The shared
`saturation_certificate` independently checks the CRS, shape, affine transform,
and coverage; see [`data/protocol_certificate.json`](../data/protocol_certificate.json).

A second independent witness is the registered five-pixel lattice: its three-pixel
halo covers **5,160,724 / 5,167,373 = 99.8713%** of footprint cells. It leaves
6,649 uncovered. For a 37,654-dot candidate, even the mathematically most
favorable choice has overlap at least `1 − 6649 / 37654 = 82.34%`. This bound is
not the often-quoted 99.4% lower bound; actual distributions may overlap more.
Lattice saturation alone does not prove impossibility for all smaller budgets;
the dense witness does under the shared positive-support interpretation.

We did not invent an exception for dense probability maps or calibration
probes. If an owner explicitly revises the protocol to compare **real submitted
binary masks** for dot overlap while measuring continuous surfaces by rank,
that is a different rule and must be preregistered, justified, and applied
consistently to the entire refreshed registry. It is not an authorization to
upload any existing file. Until then the required action is to stop **before**
placement, not to fabricate a unique raster or silently select a slot.

## Input and format irregularities

- The competition data page redirects to login. The inputs restored here are
  **owner-supplied mirrors** with matching SHA-256 pins, not independently
  authenticated organizer downloads. The mirrored feature stack has 19 bands;
  its shared, catalogue-free 35-channel feature cache was built once using the
  pinned upstream builder. It is large and intentionally ignored by Git.
- The mirrored `labels.tif` and `existing_faults.tif` are byte-for-byte
  identical (both SHA-256 `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`).
  The manifest discloses this, but separate label and catalogue provenance
  cannot be assumed. A hide-and-recover experiment on these bytes is a
  **catalogue-recovery proxy**, not an independent hidden-organizer-label test;
  the alias makes visible-only feature derivation especially important.
- The mirror named `sample_submission.tif` contains 60,988 positive pixels,
  exactly the mirrored label mask, while the official description calls the
  sample a total-fault-absence prediction. We used it **only** for grid and
  finite-footprint information. This provenance/meaning conflict needs an
  organizer-authenticated copy; do not use its values as prediction targets.
- The official specification asks for one float32 band, EPSG:32611, the same
  grid, predictions in `[0,1]`, and null/NaN outside bounds. The shared local
  validator additionally uses an all-finite export policy. The cause of the
  user's previous range error is unknown; neither NaN-outside nor zero-outside
  encoding has been independently shown to be accepted by the portal here.
- A proper leaderboard forecast needs a prospectively calibrated relationship
  between comparable holdouts and receipt-linked live submissions; it cannot be
  created by fitting the closely related H19-5 variants to their owner claims.
- The nine-file review is not proof of novelty against every public, private,
  or concurrently generated raster. A fresh complete inventory is required
  for any future uniqueness claim. Eight of nine public repository heads had
  already changed by the 22:06 UTC head check; those new commits have not been
  raster-audited here. See [`data/peer_feed.json`](../data/peer_feed.json).
- **Shared-template prose defect, not privately patched:** the docstring of
  [pinned `gems57/metric.py`](https://github.com/buffedlizard55-lab/57GEMSDOE/blob/822a0ce5546c7b6749cdd82eb145b6b3e616603d/src/gems57/metric.py)
  says a dot's total marginal true-positive credit `dT` is at most its best
  single-truth self-credit `k`. That is false when one dot covers multiple
  truths. With a unit prediction one pixel from each of two truth cells,
  `dT = 4/3` while `k = 2/3`. The shared exact scoring code sums the two
  credits correctly; a synthetic regression test checks it. We did not change
  the shared tool or depend on the incorrect bound. Its owning template should
  correct the documentation once; this checkout cannot push to that repository.

## Official research and audit links

- [DrivenData problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login required)
- [DOE/NLR rules, sections 3.2–3.5](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR INGENIOUS compilation and CC BY 4.0 license](https://gdr.openei.org/submissions/1391)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [USGS: Great Basin blind geothermal play fairways](https://pubs.usgs.gov/publication/70221765)
- [USGS: structural discontinuities and hydrothermal systems](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa)
- [USGS: geophysics, buried faults, and lithologic contacts](https://pubs.usgs.gov/of/2000/0189/pdf/of00-189.pdf)
- [USGS: fault terminations and geothermal springs](https://www.usgs.gov/publications/correlation-geothermal-springs-sub-surface-fault-terminations-revealed-high-resolution)
