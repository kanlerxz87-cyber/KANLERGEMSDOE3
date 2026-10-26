# Shared-template documentation defect — reported locally, no private fork

**Status:** confirmed by a synthetic counterexample; affects a docstring/premise, **not a demonstrated
failure of the exact evaluator**. An attempt to file an issue in
[`buffedlizard55-lab/57GEMSDOE`](https://github.com/buffedlizard55-lab/57GEMSDOE) returned
`Resource not accessible by integration (createIssue)`. This checkout has no push permission to that
repository and Arena's session branch cannot be changed. No upstream change or issue was claimed.

At 57GEMSDOE main commit `822a0ce5546c7b6749cdd82eb145b6b3e616603d`, and in the restored GEMSDOE31
shared-template pin `597b04cd1afb65d1ebbe3e9417fd952be48e3d74`, the `metric.py` docstring says a new
dot's marginal truth credit `dT <= k`, and that `dT == k` for a non-redundant dot. In general this is
false: `dT` sums new coverage across *all truth pixels*, whereas `k` is the largest credit that one dot
receives from its nearest truth pixel.

For an empty prediction, let truth pixels be `(3,3)` and `(3,4)`. Add one dot at `(3,3)` with the
3-pixel triangular kernel. The shared evaluator computes `TP_before = 0`, `TP_after = 1 + 2/3 = 5/3`,
so `dT = 5/3` while `k = 1`. Neither truth pixel was covered by an earlier dot. This does **not**
disprove the documented exact two-sided inequality or the implementation of `marginal_accept`.

Suggested upstream fix: remove the general `dT <= k` claim, qualify the simplified `dT == k` case to
situations where that equality actually holds, and add the two-truth-pixel counterexample as a regression
test. Do this once in the canonical shared template and propagate via its normal versioned release, not
by silently changing the vendored implementation here. Until then, rely on the exact metric equations,
not the erroneous prose. The local audit did not use the marginal shortcut. The synthetic unit check is
not a geological model experiment and used no competition slot.
