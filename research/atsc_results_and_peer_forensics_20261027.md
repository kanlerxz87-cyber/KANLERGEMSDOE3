# ATSC research archive — corrected independent review, 28 October 2026

**DO NOT SUBMIT.** The original ATSC model, card and rasters are preserved; this
review did not rerun training or change the recorded scientific evidence. The
previous presentation is retained at
[`archive/atsc-cfcca804/research.md.snapshot`](../archive/atsc-cfcca804/research.md.snapshot)
for historical reference, but its claims of proven physical laws, confirmed
geological mechanisms, exact causal hidden scores and universal uniqueness are
withdrawn. The [corrected portal](../docs/atsc-submod/index.html) and
[byte-level receipt](../evidence/session-cfcca804-atsc-audit.json) take precedence.

## What the saved evidence actually establishes

| Question | Bounded observation | Consequence |
|---|---|---|
| Geometric novelty | Both saved encoding twins have 37,652 of 37,654 dots (99.99%) within 3 pixels of the pinned binary calibration lattice. | Exceeds the literal >70% stop; **DO NOT SUBMIT**. The check is against one reference, not a complete registry or a pre-placement surface. |
| Local format | Zero twin passes `finite-grid` but fails `template-mask` and `masked-finite`; NaN twin passes `template-mask` but fails the other two. Both are finite in [0,1] inside the participant-mirror footprint. | The mirror is not organizer-authenticated and the previously rejected upload is unavailable; neither profile proves portal acceptance or the cause of the error. |
| Leakage canary | The preserved inventory reports 103 tested names (maximum two-polarity AUC 0.630488); none of the 22 names in `STAGE2_CORRIDOR_NAMES` appears in that inventory. | The all-feature canary requirement is not established. A missing canary does **not** prove leakage or supply the missing AUCs. |
| Best-incumbent comparison | The prior card's positive paired interval belongs to `B0_regional_d28`, not the named `CADG_Exp_K3_3_prior_repo_best`. | A difference in point estimates is not a paired CI against the strongest incumbent. Do not use the B0 interval to claim that gate passed. |
| Provenance | The historical ATSC card asserts canonical cache, operator and complete-registry flags; it used a separate participant-mirror pipeline and its detector-only subset excludes the lattice. | Those self-declarations are not independent authentication of the current required cache, evaluator or complete registry. |

The prior card reports **HOLDOUT-DTI 0.163715** (95% CI `[0.153314, 0.174809]`,
`gems-segment-pooled-v1`, 60,988 withheld positive pixels) for ATSC-2. Its named
CADG incumbent is reported at **HOLDOUT-DTI 0.157080** (95% CI `[0.143057,
0.171030]`, same reported evaluator and positive count). These are historical
participant-run figures, not independently rerun in this review, not
organizer-confirmed, and not forecasts. A four-fold or block-bootstrap interval
also cannot eliminate geographic distribution shift between mapped and concealed
faults. The current review created **no** geological prediction or score.

Reproduce the saved-byte audit, using the three hash-pinned participant mirrors
sample, labels and lattice (not organizer-authenticated):

```sh
python scripts/audit_atsc_archive.py --restore
# Exit 1 = expected duplicate stop; exit 2 = audit failed/incomplete.
```

## What can be said about the reported GEMSDOE32 0.2778

The user supplied the historical 0.2778 value; no organizer submission-page
receipt binding it to the raster is available. The independently pinned
[H33 lineage audit](../evidence/h33-lineage-20261027.json) finds identical
44,090-dot GEMSDOE25/30 masks and a 37,654-dot GEMSDOE32 mask formed by
removing 6,436 dots within two grid pixels of the mirrored known-fault catalogue,
without additions. This is a geometrical observation, not proof of model ancestry
or of the cause of any leaderboard result.

The organizer's [metric definition](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)
uses a 300 m triangular kernel and weighted true-positive, false-positive and
false-negative terms. Sparse, non-redundant placement *could* improve the tradeoff,
but removing a dot can also lose unique truth coverage. Organizer staff state
that the known-fault mask is [pixel-exact, not a buffer](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4).
No matched hidden-truth ablation or file-bound score receipt establishes the
previously asserted causal gain or a 200 m dead zone.

## Correct marginal-coverage qualification

For a fixed truth set, let the current ratio be `S`, and let adding a prediction
change true-positive and false-positive mass by `t` and `f`, respectively. Because
`FN_w` decreases by `t`, the new ratio improves precisely when

```
t * (1 - (1 - beta) * S) > alpha * S * f
```

provided the denominators are positive. There is no universal exact threshold
based on `S` alone unless `f` is specified. A new dot can credit multiple truth
pixels, and its FP increment is a different quantity. The former ATSC prose
incorrectly treated a single threshold as necessary and sufficient.

A reproducible **synthetic fixture, not HOLDOUT-DTI**, is recorded in the audit:
a new dot raises the local metric even though its marginal truth credit is below
the claimed unconditional threshold. The related central report is
[upstream issue #50](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50).
A comment with this counterexample was attempted, but GitHub returned
`Resource not accessible by integration`; no upstream source was edited.

## Official science sources and limitations

- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), DOI `10.5066/P93LGLVQ`: describes magnetic and radiometric observations, flight geometry and processing. It does not establish that an individual anomaly is a fault or confirm this repository's derived mirror provenance.
- [USGS structural-discontinuity study](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa), DOI `10.1144/geoenergy2023-009`: identifies fault intersections, terminations and stepovers as important hydrothermal settings. It does not prove a candidate pixel is a vent.
- [USGS blind geothermal play-fairway report](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and), DOI `10.2172/1724080`: reports a blind Gabbs Valley system supported by multiple independent observations and drilling. Transfer to the challenge footprint remains a hypothesis.
- [DrivenData task and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) target fault predictions; external datasets require appropriate licenses. An indexed source, participant-mirror hash or source-refresh feed does not establish usable coverage, license, or organizer data identity.

The observed GEMSDOE32 source at commit
`e56a10a9d2f218c05ea66c5a5b7228bb780bb5a7` differs from the frozen pins. A
[synthetic operator replay](../evidence/session-cfcca804-upstream-operator.json)
found that it rejects soft inputs, but still drops empty-truth FP mass from pooled
blocks. This result concerns only the observed instrument, not the separate
`gems-segment-pooled-v1` used in the historical ATSC card. No central repair or
new source pin has been claimed.
