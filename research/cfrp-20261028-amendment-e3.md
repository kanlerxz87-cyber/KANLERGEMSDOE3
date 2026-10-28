# Amendment E3 — logged before running E3 (2026-10-28)

Trigger (measured, not assumed): the final CFRP dots are all ≥10 px from the
catalogue (min 10.0, median 20.4) although 79.8% of the raw top-44,090 surface
pixels are within 3 px of it. Cause identified line-by-line:
`gems.metric.ridge_nms` erodes its `valid` mask by a 4σ+3 halo (≈7 px); with
the >2 px catalogue collar the effective no-emission corridor is ≈9–10 px.
The archived live-ledger inversion (vendor/gems32lli S3, reused unchanged;
LOO MAE 0.0219) projects the resulting raster at 0.1110 vs 0.2843 same-fit for
the H33 champion — i.e. this emission, not the CFRP surface ranking, is the
dominant known weakness.

E3 (final experiment, 3/3): on the *existing* E1 CFRP holdout surfaces, no
retraining, compare V2 ridge emission (0.13882) against direct ≥3 px-spaced
greedy top-k surface emission, budget 44,090, collar >2 px from *visible*
catalogue (fold-proper). Paired pooled HOLDOUT-DTI decides. If direct emission
wins with paired 95% CI > 0, the final model is re-emitted with it; otherwise
the V2 final raster stands. Deviation from the original E3 clause is logged
here; experiment count remains 3.
