> **2026-10-26 update:** the GPC-3 research TIFF has 100% overlap within 3 pixels of a registered lattice and is a duplicate under the literal all-registry protocol. A pass against only nine champions is not sufficient. See `evidence/parallel-lattice-audit.json`. Do not submit. The original historical record follows.

# GPC-3 results — 2026-10-26 (Pass 1–3 review included)

All scores below are **HOLDOUT-DTI** (`gems-segment-pooled-v1`, whole-segment
hide-and-recover, 15 px buffer, 60,988 withheld positives, 95% spatial-block CI)
unless labelled OWNER-REPORTED. No leaderboard estimate is claimed.

## Arms (preregistered, budget = 3 experiments + matched control)

| Arm | Features | HOLDOUT-DTI | 95% CI | Paired Δ vs B0 [95% CI] | Fold wins |
|---|---|---|---|---|---|
| B0 control | 59 base | 0.132508 | [0.120689, 0.144628] | — | — |
| EXP-1 | B0 + 15 GPC | 0.137224 | [0.124884, 0.150399] | +0.004717 [0.000177, 0.009529] | 3/4 |
| **EXP-2** | B0 + 12 GPC concordance | **0.137681** | [0.125567, 0.150331] | **+0.005174 [0.000390, 0.010042]** | 3/4 |
| EXP-3 | EXP-1 + B2 collar | 0.137224 | identical to EXP-1 | +0.004717 | 3/4 |

Per-fold EXP-2 − B0: NW +0.014600, NE +0.010436, SW −0.001127, SE +0.002584.
The SW fold is the honest weak spot (all arms dip there); no fold was dropped.

**Replication check:** B0 here (0.132508) vs the recorded B0 for the same stack
in GEMSDOE36 (0.133749, seed/HGB-version differences only) — the control
reproduces, so the GPC delta is not a control artefact.

**EXP-3 null, explained:** in holdout, EXP-3 emitted *identical* dots to EXP-1
(0 differing pixels per fold; minimum dot→visible-catalogue distance ≥ 23 px).
Under whole-segment holdout the scored dots sit on withheld segments that are
structurally far from visible segments, so a 2 px visible-catalogue collar
cannot bind. The collar's known benefit (champion forensics, 0.2600→0.2778)
operates against the *full* catalogue at final-emission time, a different
geometry. We did not spend a 4th experiment on it (budget rule).

**Final-file anatomy (measured, post-hoc descriptive):** the EXP-2 full-data
fit emits 37,654 dots; 4,115 sit on catalogue pixels, 13,031 (34.6%) within
2 px of the catalogue, median catalogue distance 4.0 px (champion B2: 0 within
2 px, median 19.6 px). This is the single largest known inefficiency in the
file by the champion's own arithmetic, and the first thing a follow-up lane
should test — as its own preregistered experiment, not a silent tweak.

## Gates

| Gate | Result |
|---|---|
| Leakage canary (15 GPC features, two-polarity AUC ≤ 0.90) | **PASS** — worst 0.6749 (`evidence/leakage_canary.json`) |
| Paired CI vs B0 strictly positive (EXP-2) | **PASS** — [0.000390, 0.010042] |
| Beats recorded group best 0.16379 (GEMSDOE24 DPRF1, same evaluator) | **FAIL** — 0.137681 |
| Surface uniqueness vs 9 champions (|ρ| ≤ 0.90, pre-placement) | **PASS** — max 0.097 (GEMSDOE24) |
| Final-dot uniqueness vs 9 champions (≤70% within 3 px) | **PASS** — max 46.3% (GEMSDOE27); vs champion GEMSDOE32: ρ 0.065, overlap 30.2% |
| Format / portal range (whole array finite, [0,1], template grid, `-zeros`) | **PASS** — `evidence/validator_output.json` (`portal_range_ok: true`) |
| **Verdict** | **negative — DO NOT SUBMIT** (research download only) |

## Interpretation (PhD judgement, labelled inference)

Gradient phase is real fault information that magnitude-based lanes discard:
a +0.005 pooled gain with a paired CI excluding zero, from 12 label-free
features, replicated in 3 of 4 spatial quadrants, is not noise. But magnitude
still dominates this problem at 100 m: phase concordance adds ~4% relative,
where ~24% relative (0.1377→0.16379) is needed to clear the group holdout bar
and ~59% credit-per-dot to reach the live leaderboard top (0.4437, S2).
The most promising untested lever remains expert-scale 1 m DEM scarp-profile
reading (hypothesis #5), followed by STEP-THROW (#2) with a preregistered
full-catalogue annulus emission test.
