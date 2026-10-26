# Scientific review: completed fixed experiment (2026-10-26 UTC)

## Decision and actual evidence

**Negative; do not submit.** After the whole-segment, buffered spatial experiment, the frozen
37,654-dot candidate was generated only in memory and checked against the registered calibration
lattice. All **37,654 / 37,654 = 100%** lay within 3 pixels; the 70% rule triggers an immediate stop.
This lane produced no TIFF, SHA or saved-byte validator result; no slot selection, receipt or
expert-reviewed discovery exists. The [run card](../evidence/run-card.json) is the single authoritative current record.

The candidate achieved **HOLDOUT-DTI 0.1133855**, 95% CI **[0.1006053, 0.1262007]**;
`gems57-pooled-hide-v2`, **60,988 withheld positive pixels**, 1,999 paired bootstrap draws over
553 physical 10 km clusters. Its fixed feature ablation achieved **HOLDOUT-DTI 0.1124083**, 95% CI
**[0.0994455, 0.1252295]**, same evaluator and positives. The paired difference is **+0.0009773**,
95% CI **[−0.0005962, +0.0026773]**. This interval does not establish improvement. The ablation
is a controlled comparator, not the best available prior incumbent; the requirement to beat a
same-evaluator best has not been demonstrated. Intervals condition on fixed fitted folds and catalogue
labels, and are not forecasts or calibrated probabilities of a hidden leaderboard score.

Four centroid-assigned whole-component folds used a 1.5 km training buffer, label-free physical features,
visible-only training labels/background exclusion, and pixel-exact visible-fault masks. Single-feature
and support-mask AUC leakage canaries and a genuinely out-of-fold model canary did not exceed 0.90 in
either polarity; passing does not prove absence of leakage. No full-data predictions were used as a
withheld-label canary. The model used K/Th and LiDAR cached layers, not sample values or prior predictions.

Both out-of-fold and full-fit continuous surfaces were compared with all 167 hash-verified registry
rasters before dot placement, preserving actual nonbinary values for two references. Maximum absolute
rank correlations were **0.0859** and **0.0975**, respectively. This is only a frozen-snapshot
surface pass. Final-dot comparisons stopped immediately after the first lattice duplicate, and the
snapshot cannot establish completeness across concurrent/unregistered projects.

## Concurrent GPC-3 artifact, independently checked

A separate session had already committed a GPC-3 research TIFF to main, with a negative verdict based
on its reported holdout. Its record reports **HOLDOUT-DTI 0.1376815**, 95% CI **[0.1255670,
0.1503305]**, `gems-segment-pooled-v1`, **60,988 withheld positives**. Its reported paired delta
against its own B0 is **+0.0051737**, 95% CI **[+0.0003899, +0.0100424]**, same evaluator and
positives. We did not replay that experiment, and its evaluator should not be directly compared with
our `gems57` result without parity validation.

We independently checked its saved TIFF SHA-256 and found all **37,654 / 37,654 = 100%** of its
final dots within 3 pixels of the same registered lattice ([receipt](../evidence/parallel-lattice-audit.json)).
Its pass against only nine focus champions does not satisfy the user’s all-registry stop; this research
file is a **duplicate and must not be submitted**. The strict local null-outside validator also finds
7,111,787 valid exterior pixels in this zero-outside TIFF ([format receipt](../evidence/parallel-format-audit.json));
this is not evidence of portal behavior. The historical output remains for provenance, with
its run card updated to reflect the new audit; it is not a promoted deliverable. This check inspected
existing bytes and did not fit or generate another candidate.

## Geometry and protocol tension

The lattice covers **5,160,724 / 5,167,373** footprint cells within 3 pixels, leaving **6,649**.
For `N` distinct candidate dots, the overlap fraction is at least `max(0, N − 6649) / N`.
It therefore exceeds 0.70 at `N >= 22,164`. For the preregistered 37,654-dot budget, the guaranteed
lower bound is 82.34%; the actual run showed 100%. This proof does not say that every smaller candidate
is a duplicate. The budget was recorded after the obstruction was discovered, but not reduced to evade
it. The project does not change the rule without explicit authorization.

## Historical sites and the 0.2778 claim

Nine exact owner-mirrored historical files are hash- and Git-blob-verified; details and scores are in
[evidence/portfolio-audit.json](../evidence/portfolio-audit.json). Their reported figures are **owner
reports, not organizer-confirmed**; no submission receipt binds score and file. Each fails the 70%
directed overlap criterion against another of the nine. GEMSDOE25 and GEMSDOE30 have identical
footprint masks despite different bytes. In pinned mirrors GEMSDOE32's H33-B2 is exactly the 44,090
D2.8 dots minus 6,436 dots at or within two pixels of the known catalogue, leaving 37,654.

Removing predictions without losing weighted true-positive coverage can reduce the false-positive term
and increase DTI. Removing dots near known faults may also remove real, newly mapped continuations or
splays. Hidden truth, causal ablation, and verified receipts are missing, so no causal explanation or
future improvement is established. A prior GEMSDOE24 report of HOLDOUT-DTI 0.16379 (95% CI
[0.15045, 0.17739], `gems-segment-pooled-v1`, 60,988 positives) was not replayed against our model;
its reported value is not a directly comparable victory threshold. Do not treat its holdout as an
organizer result or claim our lane exceeded it.

## Shared writer versus the official footprint mask

The published format describes null/NaN outside the footprint. The two unchanged GEMSDOE24 shared
writer pins differ: `fc2bc6f` defaults to NaN outside, while `7ab1c8f` defaults to zero. Their
`format_valid` checks treat the official outside-NaN condition as advisory. A separately integrated strict local validator requires outside
pixels to be nodata and rejects a zero-outside file. A synthetic regression demonstrates both
behaviors; neither establishes what the portal accepted or why an earlier file failed. The shared
upstream template has **not** been modified here: the session is restricted to this repository branch,
so no private writer fork or upstream fix is claimed. The inconsistency must be fixed once in the
shared template, or clarified by the organizer, before any submission is contemplated.

## Data, licenses and access

The six files were restored from pinned owner mirrors. SHA-256 and expected grids/bands were verified;
this is mirror integrity, not organizer authentication. The sample mirror contains exactly the known
labels as positives; it supplied only the finite footprint and spatial grid. Cached LiDAR/scarp and
radiometric layers are derived, quantized proxies; the full 19-band training raster was validated but
not used as a predictor. The underlying USGS GeoDAWN release is CC0 and 3DEP products are generally
free/public-domain, but this does not establish the provenance, code license or shareability of the
owner's derived caches. Direct authenticated organizer data and account-specific cap were unavailable.
See [source register](../docs/SOURCES.md).

The user refers to a single named method paragraph that cannot be identified in the supplied request;
this lane was explicitly provisional and cannot be promoted as though assigned. The feature idea may
be mimicked by channels, deposits, contacts, roads, processing seams and inconsistent flight sampling.
The candidate is not a geothermal-vent detector and no newly discovered feature has been confirmed.

## Attempts and continuation

Attempt 1 terminated on an uninitialized clock variable after feature/canary calculation; its receipt
is preserved. Attempt 2 corrected only the runner bug and produced the results above. Under the duplicate
stop no further candidate is run. First resolve the actual lane, mirror authentication and sharing rights,
registry completeness, and the impossible high-density requirement. Any new, authorized run needs a
fresh preregistration and paired best-incumbent evaluation. Promotion, format validity and the weekly
slot selector remain separate.
