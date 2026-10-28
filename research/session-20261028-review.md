# Repository review and research decision — 2026-10-28

## Executive decision: negative / **DO NOT SUBMIT**

This is a fresh source-and-tool audit, not a geological experiment. **No candidate TIFF, holdout result, leaderboard estimate, organizer receipt, or upload authorization was produced.** The correct download choice is **none** for every priority site. Historical files remain forensic references only.

The current preflight at `2026-10-28T16:22:13Z` is fail-closed: `research_ready=false`, `submit_ready=false`, `slot_authorized=false`, zero experiments, and zero slots. See the [preflight receipt](../docs/data/session-20261028-preflight.json) and [negative run card](../docs/data/session-20261028-run-card.json). It records the fixed session clock as exhausted. I did not reset that clock or privately assign the missing lane. The working checkout does not contain the core competition rasters or a core-data receipt; restoring pinned template/instrument files into ignored `.cache` paths is not data readiness.

### Decision in brief

| Item | Current result |
|---|---|
| File to download for submission | **None** |
| New unique single-band TIFF | Not generated |
| New leaderboard estimate | Not estimable; no projection emitted |
| HOLDOUT-DTI | Not run; no evaluator version, withheld-positive count, or CI to report |
| Historical score `0.2778` | User/participant-reported claim; no submission-page receipt binding it to a file |
| Historical uniqueness | All nine supplied winner rasters fail the within-family 70% directed 3 px overlap stop; this is geometry, not model performance |
| Current research readiness | False; assigned method paragraph, raw inputs/receipt, authenticated cache/digest, complete representation-resolved registry, repaired/pinned evaluator, and same-fold incumbent are missing |
| Experiments / weekly slots | 0 / 0; fixed two-hour clock expired and was not reset |
| Final recommendation | **DO NOT SUBMIT** |

## Three-pass review

### Pass 1 — establish repository, files, and source freshness

- Read `README.md`, `AGENTS.md`, the full project prompt, existing review/run cards, site generator, test suite, data manifests, registry notes, and both competing hypothesis files. The standing instructions still prohibit assigning a lane, resetting the inherited fixed clock, privately rebuilding the canonical feature stack, or promoting another session's quarantined result.
- Recreated the local environment and installed the locked requirements. Pinned template recovery and the optional `saturation57` instrument completed under ignored `.cache` paths. No raw core TIFF or digest-bound `data/input_receipt.json` was present in this checkout. No prediction, TIFF, or geology experiment was created.
- Refreshed the nine priority-site participant-source pins at **2026-10-28T16:13:43Z**. The registry remains explicitly incomplete. I read and SHA-256-bound each pinned participant homepage; those statements are not official score receipts or independent audits of the newer TIFF bytes.
- Re-audited the current GEMSDOE32 `main` source at **`109f364fb39030e40ef51b839b79cf694123b51b`**, observed at **2026-10-28T16:16:54Z**. Four of five checked evaluator/feature/writer files differ from the local pin; `features.py` is unchanged. The changed evaluator/writer path adds explicit mask/grid checks and rejects a synthetic 0.5 mask, but the hide-and-recover empty-truth false-positive aggregation defect remains. Issues #37, #41, #51, and cache-provenance issue #53 were still open at the observation; an open/closed state is not proof of organizer impact. No source change was copied into the pinned vendor template.
- Fresh preflight at **2026-10-28T16:22:13Z** confirmed the same hard blockers and the inherited clock expiry. Its exit code 1 is the expected fail-closed outcome, not a software-test failure.

#### Executive table — GEMSDOE24/25/27/28/30/31/32/33/36

The `historical claim` column is the owner-supplied/participant-reported value captured in `docs/audit.json`; it is **not** labelled HOLDOUT-DTI or ORGANIZER-CONFIRMED. The overlap is the maximum directed dot overlap against another supplied focus-site historical raster within 3 px. It is a geometric measurement only; continuous historical-surface rank correlations were not available in this audit. Every historical row is research-reference-only.

| Site | Historical file (reference only; not a download) | Historical claim | New leaderboard estimate | Max within-family 3 px overlap | Unique under the stated stop? | Download / submit? | Latest pinned participant-page statement |
|---|---|---:|---|---:|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` | 0.2477 · owner-reported | Not estimable | 100.00% | **No** | **None / NO** | Current page says its local point-best remains research-only; no submission-authorized TIFF. |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` | 0.2600 · owner-reported | Not estimable | 100.00% | **No** | **None / NO** | H79-CTHM is inspection/testing-only; no competition-ready TIFF or slot. |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` | 0.2449 · owner-reported | Not estimable | 98.02% | **No** | **None / NO** | H33-1 is research-only after a failed holdout comparison; later run stopped before publication. |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` | 0.2710 · owner-reported | Not estimable | 100.00% | **No** | **None / NO** | S23 stopped before producing a new model/TIFF; no file is approved. |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif` | 0.2600 · owner-reported | Not estimable | 100.00% | **No** | **None / NO** | POOL-1 holdout claims are blocked by final-dot overlap; no new TIFF or slot is approved. |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` | 0.2708 · owner-reported | Not estimable | 100.00% | **No** | **None / NO** | H31-CC is research-only; its page says the matched chance-control and calibration-lattice gates fail. |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 · owner-reported | Not estimable | 100.00% | **No** | **None / NO** | H51-1-EWSP is a research/audit artifact; page reports internal holdout work but withholds upload on lattice/calibration gates. |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif` | 0.2632 · owner-reported | Not estimable | 99.71% | **No** | **None / NO** | A33-R7-PCSUP is research-only; participant page says its same-operator matched-random holdout gate failed. |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 · owner-reported | Not estimable | 97.58% | **No** | **None / NO** | No candidate is authorized; S2D/KPL artifacts are references and fail literal-lattice uniqueness. |

The exact hashes, dot counts, validation profiles, and all pairwise comparisons remain in [`audit.json`](../docs/audit.json). The nine site pages and current participant-source observations are available from the [executive desk](../docs/index.html#current-participant-pages) and [hash-bound source receipt](../docs/data/session-20261028-peer-source-observations.json). The newly observed participant pages are not organizer pages. The conflicting undated leaderboard figures `0.4413` and `0.3195` were not treated as current standings or candidate estimates.

### Pass 2 — hostile review of scores, uniqueness, geology, and shared instruments

#### What the reported GEMSDOE32 `0.2778` can—and cannot—mean

The reported `0.2778` is not bound by a submission-page receipt to a saved TIFF hash, so it remains an owner-reported historical claim. The defensible evidence is geometric: in the pinned mirror audit, GEMSDOE25 and GEMSDOE30 have identical 44,090-dot masks. GEMSDOE32 H33 B2 has 37,654 dots and is exactly the GEMSDOE30 mask after removing 6,436 dots that lie within two pixels of the mirrored known-fault catalogue; it adds no dots. This lineage is independently hash-bound in the [geometry receipt](../docs/h33-lineage-20261027.json).

A mechanism is plausible but not identified. The official score rewards nearby coverage of each hidden truth pixel while penalizing emission mass that receives no credit; with alpha 0.2 and beta 0.8, false negatives are more costly than false positives. Removing redundant predictions that add little hidden-truth coverage can reduce false-positive cost, while removing a dot that uniquely covers hidden truth can reduce score. The measured deletions were near the known catalogue, but hidden truth, a receipt-bound score, and a paired causal ablation are unavailable. **The geometry does not establish that thinning caused 0.2778, that H33 is a new geological signal, or that any future model can exceed it.**

#### Current shared-tool operator diagnostic — synthetic, not a score

At current upstream commit `109f364f…`, an eight-cell synthetic fixture had seven matching truth/prediction cells and one prediction in a zero-truth cell. The fold records contained FP mass **1.0**, while pooled spatial blocks contained **0.0**. The evaluator's synthetic pooled diagnostic was `0.9999999999998571`; conservation-recomputing the same synthetic TP/FN with FP mass included gives `0.9722222222220872`. These values test aggregation behavior only; they are **not HOLDOUT-DTI**, geological measurements, or evidence that a historical score was affected.

The current source also rejected a prediction value of `0.5` with `ValueError` (“no implicit thresholding”). That is a real input-contract improvement in the inspected path, but does not repair the omitted pooled FP mass. The audit exercised current `holdout.py` and `submission.py`; `metric.py`, `paths.py`, and `__init__.py` were copied from the pinned local template only to satisfy imports. Current upstream `metric.py` was not fetched or audited. Issues #41 and #53 were open at the recorded source observation. No private evaluator fork or vendor patch was made. See the [synthetic current-source audit](../docs/data/session-20261028-upstream-operator-audit.json) and [upstream prerequisite receipt](../docs/data/session-20261028-upstream-prerequisites.json).

#### Ranked hypotheses, not an experiment plan authorization

The single active conditional shortlist is in the [machine-readable hypothesis record](../docs/data/current-hypotheses.json) and the detailed [hypothesis review](session-20261028-hypotheses.md): (1) cross-field Morse–Smale junction persistence, (2) two-sided directional-fabric entropy break, (3) signed edge-migration stability under continuation, and (4) hydrochemical geothermometer residual corridors. Each names layers, a physical signature, why it could reveal unmapped faults, differences from active local code, a non-fault mimic, qualitative benefit/cost, and data viability. The top three use challenge-core bands and require no separate public dataset; the raw core data and valid input receipt are absent here. The fourth is not viable until the actual official GDR chemistry files/coverage/license are confirmed obtainable. No official host refresh or new external data download was performed today. The ranking is a research priority, **not** an assigned lane, performance prediction, proof of global novelty, or probability of winning.

No experiment was attempted because the missing lane, raw data/receipt, cached feature digest/bytes, complete registry/dot semantics, sound shared evaluator, and same-fold incumbent all fail the preflight; the fixed two-hour session budget also expired. Running a hypothesis under those conditions would violate the stated protocol.

### Pass 3 — reconcile the active decision surface and test the negative result

- Refreshed and saved current source receipts, current participant-page summaries, the source-dependent audit wording, current preflight, current upstream synthetic test, this review, the canonical ranked shortlist, and a negative run card.
- Made the generated executive table explicit for all nine sites: historical claim labels, no new estimate, file reference only, geometric overlap, and **NO** submission. Added a separate pinned participant-page table; the homepage does not infer organizer approval or score status from those pages.
- The generated submission guide remains **DO NOT SUBMIT**. It explains the required feature-canary, whole-segment buffered hide-and-recover, exact visible mask, same-fold paired incumbent, surface and final-dot uniqueness, saved-TIFF validator, note/name/hash, and separate slot-selection gates.
- Preserved the prior review cards and raster archives as history; did not re-label any peer/quarantined TIFF as this session's result.
- Final verification: `pytest -q` **275 passed, 0 failed, 0 skipped**; `scripts/build_site.py --check`, `scripts/build_cadg_site.py --check`, and `scripts/check_run.py` passed. `check_run.py` only consistency-checks the preserved negative card; it is not a new run.
- Desktop/mobile Playwright smoke test **passed 51 checks** across the current pages, all nine site pages, quarantined archives, source-feed outcomes, and local-storage failure modes. The source API is mocked in this test; it is not a live score check. `npm ci --prefix tools/browser` installed 19 packages and reported 0 vulnerabilities.
- The pinned `scripts/audit_shared_tools.py` and current `scripts/preflight.py` exit nonzero intentionally: the former reproduces the local empty-truth FP and soft-mask issues; the latter says research/submit readiness and slot authorization are false. Current-upstream synthetic diagnostics are stored separately and must not be called HOLDOUT-DTI.
- `git diff --check` and the final clean/reviewed patch checks are reported in the handoff. A passing test suite proves software consistency only, not geological performance or competition acceptance.

## Official-source limits

`docs/SOURCES.md` and `knowledge/geothermal-science-2026-10-27.md` preserve earlier dated observations from the official competition, staff clarification, rules, USGS GeoDAWN, DrivenData reference, and GDR source index. This continuation did **not** fetch official DrivenData, USGS, or GDR pages or binaries; those hosts were outside this sandbox's allowed outbound set. Therefore no new official deadline, leaderboard, downloadable-data availability, license, or portal behavior is claimed as freshly verified here. The newest source refresh in this review is GitHub participant material only. Account-specific remaining slots and organizer acceptance remain unknown.

## Required next steps before any future experiment

1. A coordinator must provide the explicit method paragraph and authorize a new fixed-clock session; do not infer the lane or reset this expired clock.
2. Obtain and bind the required core-data input receipt and authenticated feature-cache bytes/digest without privately rebuilding the stack.
3. Resolve the shared empty-truth FP aggregation defect centrally, review the full current upstream diff, pin the corrected source, and rerun operator tests. Preserve the strict binary input contract.
4. Complete the registry and decide, with evidence, how continuous diagnostics and explicit dot masks are represented; do not silently exempt the lattice or reinterpret candidates.
5. Establish the same-evaluator, same-fold incumbent. Only then preregister and run rank 1; test each feature alone, use whole-segment buffered hide-and-recover with visible-only features and exact visible masking, and report paired improvement CI.
6. Compare both continuous pre-placement surfaces and final saved dots against every registry raster. Stop on absolute rank correlation above 0.90 or more than 70% of dots within Euclidean 3 px of any entry.
7. Do not spend a weekly slot without a positive paired holdout improvement, verified remaining cap, successful hash-bound single-band float32 TIFF validation (grid/CRS/shape/transform and `[0,1]`), unique filename, note of at most 140 characters, and separate selector authorization. Only an organizer submission-page receipt can support **ORGANIZER-CONFIRMED**.

**Maximize P(Win):** keep the submission file unavailable while the edge-case evaluator, data, registry and improvement evidence remain unresolved. **Own the Outcome:** report the exact negative result, the improvement in input validation, and the remaining reproducible defect without inventing a winner.
