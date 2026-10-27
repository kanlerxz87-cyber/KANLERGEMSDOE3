# Arena branch review — 27 October 2026

## Decision

**DO NOT SUBMIT. No new TIFF, no leaderboard estimate, and no weekly slot used.** This was a repository/site correctness review, not a geological experiment. The fixed research session had already expired; its lane was unassigned. No scientific candidate was selected or evaluated.

## Pass 1 — implementation and repository review

- Read the standing README/full prompt, `AGENTS.md`, `PROJECT_REQUEST.md`, session configuration, research continuation and evidence cards before changes.
- Inspected the nine-site executive table, historical geometry receipts, four conditional hypotheses, generated site builder, validator/readiness gates, test suite and Pages workflows.
- `python scripts/build_site.py --check` found `docs/index.html` stale. The checked-in page still represented a legacy dashboard that advertised a downloadable candidate and repeated an unsupported `0.4413` score claim. Rebuilt the generated page from the current evidence-backed builder. The landing page now states that there is no eligible TIFF, no estimate, and **DO NOT SUBMIT**; historical rasters remain learning references only.
- Follow-up page-by-page review found that the archived CADG subpage and its “How to Submit” page still exposed a negative candidate as “DOWNLOAD READY” and recommended upload despite 99.73% overlap with the registered lattice. Replaced those generated pages and the lane README with a fail-closed archive decision, withheld actionable download links, and preserved the prior raster identity/results as non-submission research evidence.
- Added regression tests for both the root landing page and the archived candidate pages so stale, actionable download guidance cannot silently return.

## Pass 2 — adversarial checks

- Restored the pinned shared-template instruments in the ignored cache; 13 shared files matched their lock.
- Reproduced the known synthetic operator defect with `scripts/audit_shared_tools.py`: pooled evaluation omits false-positive mass in empty-truth cells and the shared tool binarizes soft inputs. This is a blocker; no local evaluator or writer fork was made.
- Re-ran the fail-closed preflight against the fixed session config. It reports research and submission not ready, no candidate/slot, and null holdout and leaderboard estimate. Current checkout lacks the core raster files and a current core-data restoration receipt; only small manifests/receipts are present.
- Verified the four ranked hypothesis write-up is explicit that all are proposals, not results, that ranking is qualitative (not numeric DTI), and that the required official-source data binaries are not verified as obtainable. The top proposal remains conditional and cannot be chosen as a lane.

## Pass 3 — full request and release verification

- Full Python suite: **191 passed** after adding the landing-page regression test.
- Deterministic site generation and `--check`: pass.
- Desktop/mobile browser smoke tests: pass; 9 priority-site pages, no approved download, no overflow/JavaScript errors, and source-feed failure/change never authorizes upload.
- `scripts/check_run.py`: consistency check passed with a negative verdict; it explicitly does not independently rerun science or establish global novelty.
- `git diff --check`: pass.
- No fresh official-site or organizer-page retrieval was performed in this review. Participant-source snapshots and inherited official-source evidence are not represented as live verification or submission receipts.

## Priority-site and score conclusion

The executive desk has a per-site summary for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36, with exact historical reference names, reported values, hashes and measured priority-peer dot overlaps. Historical reported values are unverified owner claims, **not** HOLDOUT-DTI or ORGANIZER-CONFIRMED. No new-file leaderboard score is estimable. All nine historical winners exceed the user's directed 3-pixel duplicate stop against another listed winner; none is a valid new submission recommendation.

For H33-B2, the saved geometry audit supports a sparse, catalogue-distance-thinned family relationship; the DTI emission/penalty trade-off makes reduced redundant prediction mass a plausible explanation. It does not identify a causal gain or establish a route to beating 0.2778. No score receipt ties the reported value to the exact bytes, and there is no paired hidden-label ablation. Do not infer a future leaderboard value from this analysis.

## Remaining blockers and next-session order

1. Obtain the explicitly assigned single-method paragraph; do not silently select one of the four hypotheses.
2. Resolve the upstream shared evaluator defect, pin a central correction, and rerun its operator tests.
3. Restore/authenticate the canonical feature cache and complete raster/surface registry; settle the unresolved registry representation without exempting the binary lattice or continuous diagnostics.
4. Obtain a same-evaluator, same-fold incumbent and official-template provenance; confirm actual weekly capacity in the selector.
5. Only after those gates, preregister and run at most three experiments / two hours, with per-feature leakage canaries, surface novelty before placement, final-dot novelty, paired spatial HOLDOUT-DTI and saved-byte validation.
6. A promotion decision and actual submission remain separate. No slot is authorized by this review.

The project values remain explicit: **Maximize P(Win)** by preserving scarce slots and rejecting unsupported forecasts; **Own the Outcome** by correcting the stale UI and keeping the failed readiness gates visible rather than disguising them.
