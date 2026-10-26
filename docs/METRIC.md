# Metric and evaluation guardrails

Source: [official GEMS problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
This is a clarification, not a new evaluator. Use the pinned, unchanged shared implementation and record
its version and hashes when a genuine holdout is eventually run.

For prediction confidence `p(x)` and true fault cells `G`, the triangular distance kernel is
`k(d) = max(1 − d/300 m, 0)`. The official weighted counts are:

- `TPw = Σ[g∈G] max[x] p(x) k(distance(x,g))`;
- `FPw = Σ[x:p(x)>0] p(x) (1 − max[g∈G] k(distance(x,g)))`;
- `FNw = |G| − TPw`;
- `DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw + ε)`.

For binary dots, **`FPw` is not generally the number of dots minus `TPw`**: the true-positive term sums
per-truth credit, while false-positive credit sums per-prediction contribution. A dot can credit several
nearby truth cells; several dots can compete to credit the same truth. The local audit uses neither a
fictional hidden ground-truth reconstruction nor a derived score ceiling.

The shared template contains an [incorrect docstring claim about a marginal-credit bound](SHARED_TEMPLATE_ISSUE.md);
its exact evaluator was not shown to be defective. No shared implementation was privately modified.
Before any future result, hold out whole fault segments with a buffer, recompute catalogue-derived
features from visible faults only, mask visible faults pixel-exactly, and test each feature alone for
AUC >0.90. Pool held-out counts across the same spatial folds for candidate and baseline. Record the
evaluator version, withheld-positive count, 95% spatial-block bootstrap CI and paired improvement CI.
A conditional spatial holdout CI is **not** a leaderboard prediction. The current run has no holdout.
