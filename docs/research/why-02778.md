# Why `h33-h33-2-b2` (GEMSDOE32) scored 0.2778 — PhD-level answer, verified in this repo

Score label: **0.2778 OWNER-REPORTED** (owner brief/site; no organizer receipt
linking this raster's hash to the score is published anywhere — IR-02).
Anatomy below: **MEASURED here** (`scripts/forensics_focus9.py` →
`evidence/forensics_focus9.json`, SHA-256-verified champion bytes).

## 1. The metric makes dot placement a mass-budget problem

From S1 (page 967) and `src/gems/metric.py`: DTI = TPw/(TPw + 0.2·FPw + 0.8·FNw),
300 m triangular kernel. With T = TPw, S = total emitted mass, M = kernel mass
landing on truth, N = truth pixels: **DTI = T / (0.2·(T + S − M) + 0.8·N)**.
A marginal dot with realised credit k raises DTI iff **k > 0.2·DTI**
(= 0.0556 at 0.2778). Binary {0,1} emission is optimal (linear-fractional).

## 2. Measured anatomy: 0.2778 is a deletion ladder on one field

| File (owner-reported) | Dots measured | Change vs previous |
|---|---|---|
| GEMSDOE25 d2.8 (0.2600) | 44,090 | H19-5 corroboration field thinned to ~3 px spacing |
| GEMSDOE31 solo (0.2708) | 40,199 | d2.8 minus **exactly** the 3,891 dots with d_catalogue ≤ 1 px (max removed d = 1.0 px; 0 dots added) |
| **GEMSDOE32 h33-2-b2 (0.2778)** | **37,654** | solo minus **exactly** the 2,545 dots with 1 < d ≤ 2 px (max removed d = 2.0 px; 0 added) |
| GEMSDOE36 Anderson (0.2750) | 38,854 | B2 **plus** 1,200 dots, 0 removed — score *fell* |

No new prediction coordinate was created after 0.2600. GEMSDOE36's forensic
inversion (same identity, N′ ≈ 12,541 effective truth px from the blind 5-px
lattice) prices the removed ≤1 px dots at ~0.002 credit/dot, the 1–2 px dots at
~0.006, the added Anderson dots at ~0.014 — all below the 0.0556 break-even —
vs 0.130 for an average kept B2 dot. This repo re-verified the subset chain and
distance bands exactly; the credit prices are inherited algebra (labelled
inference, assumptions stated in GEMSDOE36 `docs/research/why-02778.md`).

**Mechanism:** hidden truth is, by construction (S1), faults *not* in the USGS
database, and catalogue pixels are masked in scoring. Dots within ~200 m of a
mapped fault therefore earn almost nothing yet pay the 0.2 FP tax where
unmasked. Deleting the dead annulus shrank the denominator faster than the
numerator. 0.2778 = (best available field) × (~3 px dotted emission) ×
(annulus thrift). It is **not** evidence of new geology after 0.2600.

## 3. Can a submission beat 0.2778 / 0.3195 / 0.4437?

Arithmetic (same identity, 37,654 dots, N′ ≈ 12,541): reaching 0.30 needs
+8.0 % credit per dot, 0.3195 needs +15 %, and the current public top 0.4437
(S2, fetched 2026-10-26) needs ≈ +59 %. Further annulus deletion (2–3 px)
removes at most 2,171 more dots priced near zero — worth thousandths.
**Only a materially better detector surface can close the gap.** That is why
this lane (GPC phase concordance) is judged on the shared segment holdout
against both the matched B0 control and the recorded same-evaluator group best
(GEMSDOE24 DPRF1, HOLDOUT-DTI 0.16379), and why a holdout loss is published as
a negative result instead of being dressed up as a leaderboard estimate.
There is no defensible mapping from HOLDOUT-DTI to the hidden leaderboard
score; this repo never writes one as a score.
