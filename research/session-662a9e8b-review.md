# Session 662a9e8b — three-pass review, 28 October 2026

**Decision: DO NOT SUBMIT. No new candidate TIFF or score estimate.** The
[run card](../evidence/session-662a9e8b-run-card.json) is a negative deliverable;
no geological experiment or competition slot was used. The previous H33 result
is an unverified owner report, not an organizer receipt. The existing
[focus-site table](../docs/index.html) and [H33 geometry audit](../evidence/h33-lineage-20261027.json)
remain dated, bounded evidence: thinning near known faults plausibly changes the
false-positive/coverage trade-off but does not establish causality or predict hidden-score improvement.

## Pass 1 — restore and audit

- Read the standing request, prior reviews, cards and repository instructions. The
  prompt refers to a single assigned method but does not contain one. The existing
  [four ranked hypotheses](hypotheses.md) are conditional proposals, not an assigned
  lane or evidence of novelty across all peers.
- Restored all five pinned core inputs and ran shared raw-band preparation. Hashes
  authenticate the participant-mirror bytes against the manifest, **not** organizer
  provenance. These large files and the virtual environment are ignored/ephemeral,
  so restore again in a fresh workspace using the commands in the README. The derived
  35-channel cache was neither recovered nor privately rebuilt. The sample-provenance
  discrepancy remains documented in [the check](../evidence/sample-provenance-check.json).
- Reproduced the pinned shared evaluator's synthetic empty-truth false-positive
  bookkeeping defect and its soft-input binarization. This is an operator test,
  not a geological result or proof of any historic score being affected.
- Refreshed all nine public participant sources at immutable heads:
  [focus snapshot](../evidence/session-662a9e8b-focus-feed.json). This is a source
  snapshot, not a current official leaderboard, exhaustive current registry, or score receipt.

## Pass 2 — hostile review and fixes

- Found that the older `scripts/uniqueness_gate.py` computes its `unique` flag while
  exempting space-filling overlaps and allowing incomplete comparisons. Its CLI
  and its associated historical positive-support cache CLI are now archive-blocked,
  like the frozen experiment/card CLIs. Their old functions are not an approved gate.
  The active `scripts/check_uniqueness.py` now also rejects malformed rows missing an
  explicit boolean duplicate result. It still requires a complete registry and
  cannot authenticate an inventory just because the manifest says it is complete.
- The prior shared prerequisite refresher would overwrite its historical evidence
  by default, and its prose implicitly generalized a pinned test to any newer head.
  It now writes to ignored local data, marks a failed refresh unknown, distinguishes
  the tested pin from a changed head, and never treats a declared cache path and hash
  as verification of its bytes or fold-safe lineage.
- On 28 October, the [upstream snapshot](../evidence/session-662a9e8b-upstream-prerequisites.json)
  found four of five tracked files differ at [the participant head](https://github.com/buffedlizard55-lab/GEMSDOE32/tree/109f364fb39030e40ef51b839b79cf694123b51b).
  The new versions were **not** operator-tested here and must not be described as
  repaired or defective based solely on the earlier pin. Issues [41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41)
  and [53](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/53) remained open
  at observation. The 35-channel receipt still lacked a digest and tree bytes; this
  does not prove that no external copy exists. The homepage includes the update.

## Pass 3 — reconciliation and verification

- `pytest`: 272 passed. Generated root, CADG, and ATSC site checks, card consistency,
  `review.py`, and `git diff --check` passed. Desktop/mobile browser smoke passed;
  network freshness failure scenarios were mocked, not a live leaderboard verification.
- The [preflight](../evidence/session-662a9e8b-preflight.json) remains negative:
  no assigned lane, valid shared cache/operator, complete representation-resolved
  registry, or matched incumbent; the preserved previous research clock is expired.
  A format-only check, byte-unique filename, new SHA, or peer “promote” cannot clear these gates.
- The source ref already in the README preserves the standing prompt. Do not treat
  the user's conflicting leaderboard numbers as independently verified current scores.
  [Official problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
  [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
  [official reference code](https://github.com/drivendataorg/gems-prize-reference-solution),
  [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
  and [GDR 1391](https://gdr.openei.org/submissions/1391) are sources for later checks,
  not proof that a candidate works.

## Next work

1. Obtain an explicit method lane and a new authorized budget/ledger; don't reset a prior session clock.
2. Review the changed central source, pin and synthetic-test a repaired shared release, and obtain its content-addressed canonical feature cache with visible-only lineage. Do not fork the evaluator.
3. Resolve complete registry and companion-dot definitions, obtain a matched same-fold incumbent, and establish organizer data/template provenance. Enforce canaries and surface/preview/final novelty stops.
4. Only after a qualified paired holdout improvement, independently validate exact saved TIFF bytes and have a separate selector check the live account quota. The exact file that triggered the reported range error and the portal receipt are unavailable; no local profile is a guarantee of acceptance.

**Maximize P(Win):** do not spend a limited slot without trustworthy evidence.
**Own the Outcome:** close the misleading legacy CLI, restore available inputs, record the changed upstream source and leave unresolved work explicit.
