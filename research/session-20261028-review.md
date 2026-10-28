# Repository review — 28 October 2026

## Decision: negative; do not submit

No new TIFF was generated, no model experiment was run, no competition slot was used, and no score or score projection is claimed. The repository already documents the required no-submit outcome and four ranked conditional hypotheses. The current checkout lacks a Python test environment and the competition rasters; this review did not bypass those constraints by inventing a lane, rebuilding an unauthenticated cache, or substituting a local metric.

The user's single-method lane paragraph is not present in the supplied project prompt. The repository correctly treats this as a hard stop: the lane cannot be selected from the hypothesis list, and a new submission cannot be justified until an authorized method is assigned and the evidence gates pass.

## Pass 1 — inventory and baseline

- Confirmed the active branch is `arena/2fbf8dca-kanlergemsdoe3`; the checkout was initially clean.
- Reviewed the README, project request/prompt, active and prior run cards, executive summary, readiness script, scientific review, and ranked hypothesis register.
- The README includes the full standing prompt and directs future work to the prior three-pass review and fixed session configuration. The executive summary prominently says **DO NOT SUBMIT**, lists all nine requested sites, identifies historical owner-reported results as unverified, and does not provide a speculative leaderboard estimate.
- The site retains four conditional, ranked geological hypotheses (Morse–Smale field topology; directional-fabric entropy break; signed edge-migration stability; hydrochemical residual corridors), each with inputs, proposed signal, rationale, distinction, confounder, cost, and source caveats. None has been represented as a coordinator-assigned lane or validated candidate.
- There are no competition input rasters in `data/` in this checkout; only manifests and documentation are present. This is a checkout observation, not proof that mirrors or files are unavailable elsewhere.

## Pass 2 — fail-closed preflight and hostile review

Ran:

```sh
python scripts/preflight.py --config config/research-session-e2903b2e.json --out /tmp/preflight.json
```

It exited **1**, as expected for the negative gate. `research_ready`, `submit_ready` and `slot_authorized` are all false; `holdout_dti` and `leaderboard_estimate` are null. The preflight found these unresolved requirements: assigned lane absent; core-data restoration receipt absent; shared evaluator operator audit failed/missing; canonical authenticated feature cache absent; complete raster/surface registry absent; registry's dot representation/saturation unresolved; same-evaluator/same-fold incumbent absent; and prior experiment/time budget malformed or exhausted. Submission additionally lacks organizer-template provenance, a paired holdout win, a saved unique TIFF plus validator receipt, and separate selector authorization. The pinned shared template identity check itself passed (13 files); that does not repair its known operator defects or certify organizer provenance.

A hostile review found no basis to override those blocks. In particular:

1. Historical focus-site numbers are participant/owner reports in the repository record, not organizer receipts and not comparable holdout results. The reported H33 value 0.2778 cannot be treated as causal proof that its pruning mechanism generalizes or as an estimated score for a new raster.
2. The current review's previously recorded lattice saturation/duplicate checks are reasons not to resubmit existing research artifacts. They do not establish uniqueness for a new artifact.
3. A local TIFF format check cannot establish that the competition portal accepts the bytes. The rejected upload and portal receipt associated with the `[0,1]` error are not available here.
4. Running an alternative/private evaluator or rebuilding the unavailable feature stack would violate the explicitly requested shared-tool protocol and would not produce an admissible HOLDOUT-DTI number.
5. The README describes earlier data restoration in historical session context. In this present checkout, `data/` has manifests but not the raster files; do not infer a current local restore from that older record.

## Pass 3 — test execution and reconciliation

The system interpreter initially lacked pytest and rejected a system-wide pip install under PEP 668. Following the repository's documented setup, created the ignored `.venv` and installed the project with its `dev` extra. Then ran:

```sh
.venv/bin/python -m pytest -q
```

Result: **257 passed, 9 skipped, 70 warnings** in 7.52 seconds. Warnings are inherited Rasterio/Affine matrix-multiplication pending deprecations. The skipped tests remain skipped; no claim is made that they passed. These are software tests, not scientific validation, HOLDOUT-DTI, TIFF validation, or submission authorization.

All original requirements were rechecked against the present evidence. There is no safe or supportable way to generate a unique, high-scoring TIFF now: the method lane is missing, evaluator/cache/registry/incumbent prerequisites fail, and the preflight explicitly denies research and submission readiness. Refusing to fabricate a deliverable is the required negative result, not a claim of success.

## Next actions, in order

1. Obtain the actual assigned method paragraph and record it verbatim; do not reset or extend the existing experiment/time budget by changing config.
2. Obtain a centrally released, content-addressed feature cache and corrected shared evaluator/writer; audit hashes and required empty-truth/soft-probability invariants before using them.
3. Restore and verify inputs from official competition data or a provenance-explicit mirror; retain source, byte-size, and SHA-256 receipts and label provenance honestly.
4. Resolve complete registry scope and dot-vs-surface semantics, including the binary lattice and continuous diagnostic; do not weaken the >70% or >0.90 rules by exception.
5. Establish a same-evaluator, same-fold baseline and run individual-feature leakage canaries, then no more than three preregistered whole-segment buffered experiments. Record pooled DTI, evaluator version, withheld positive count and spatial 95% CI.
6. Require pre-placement surface checks and final-dot checks, saved-byte format validation, and a separate selector's live weekly-cap authorization before any upload. Bind any eventual score to an organizer receipt.

Official-source pointers already curated in the repository include the [competition rules and overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), and [GDR resource 1391](https://gdr.openei.org/submissions/1391). Their presence is not a claim that gated files or supplemental chemistry have been downloaded or authenticated.

## Run card (review-only)

```json
{
  "hypothesis": "No experiment: no authorized single-method lane is supplied.",
  "mechanism": "Not tested; do not infer a geological mechanism or score from historical leaderboard reports.",
  "named_non_fault_mimic": "Not applicable to a no-experiment review; the existing hypothesis register names confounders per candidate.",
  "holdout_dti": null,
  "holdout_dti_label": "Not run; evaluator/version, withheld-positive count, and CI unavailable.",
  "correlation_overlap_vs_registry": "Not assessed for a new candidate; no candidate raster exists. Prior artifact audits are historical and remain disqualifying where noted.",
  "raster_sha256": null,
  "validator_output": "No candidate TIFF. No NaN/range/CRS/shape/transform validation performed.",
  "submission_name": null,
  "submission_note": "No artifact approved; do not download or submit existing research TIFFs.",
  "verdict": "negative"
}
```
