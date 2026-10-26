# K3-H1 session — three review passes (26 Oct 2026)

## Pass 1 — implementation

- Pre-registered 5 hypotheses and the decision rules: `research/preregistration-20261026.md`, written 22:18:36Z, before E1 started at 22:20:13Z, and never edited afterwards. Its SHA-256 is in `evidence/experiment_log.json`.
- Restored 435 registry rasters by git transport, SHA-256 verified, and built packed 3-px buffers.
- Ran E1 (mechanism), E2 (unique pure-ASGT projections) and E3 (hybrid). That used the 3-experiment cap, about 6 minutes wall-clock.
- Wrote the file with the **shared** writer (`vendor/gems57/submission_writer.py`, byte-identical to the pinned 57GEMSDOE template), which re-validated it on disk (15/15 checks).
- Ran the final uniqueness gate from registry bytes (433 comparable rasters), plus a leakage canary for E3's added features.
- Run card `evidence/k3h1-run-card.json`: the verdict is computed by the pre-registered rules and by `scripts/promotion_gate.py`, and both say **negative**.
- Merged `origin/main`, which contained 5 PRs from parallel sessions. There were no conflicts because every lane file is namespaced (`k3h1`, `k3_`, `kgems/`).

## Pass 2 — bug review (each finding fixed and re-verified)

1. **Wrong timestamp in a filename.** The first package used a hand-typed `T2245Z` when the real time was 22:26Z. It was regenerated from the system clock; the TIF bytes are unchanged (SHA `4a5b0b48…`).
2. **Glob collision with a parallel lane.** `uniqueness_gate.py` and `build_run_card.py` globbed `kanler3-*`, which would also match main's GPC-3 files and abort on re-run. Both now glob `kanler3-k3h1-*`.
3. **Physics wording.** "FP dominates the denominator" was true for the solid network but false for the champion (0.2·35.1k ≈ 7.0k < 0.8·18.0k ≈ 14.4k). This is corrected in the report.
4. **Arithmetic.** The truth gain needed to reach 0.4437 is +66%, not "roughly 60%", using T₂/T₁ = [D₂/(1−0.2D₂)]/[D₁/(1−0.2D₁)].
5. **Transcription.** GEMSDOE28's catalogue-proximal share is exactly 6.25%, not 6.3%; this was caught by the new report-vs-evidence test.
6. **Reproducibility.** `load_grid()` needed hand-made `data/bridge` symlinks. `kgems.common.ensure_bridge()` now creates them, and the shared loader still SHA-checks them.
7. **Validator conflict surfaced, not hidden.** The older local checker expects NaN outside the footprint, while the shared writer requires zeros. The portal scored both encodings. This is documented in the README and in report §5.
8. **Unverifiable licence claim removed.** The 3DEP licence page was not re-read, so the knowledge base now says so.
9. **Monitoring mistake.** `wait_for: log` cannot see output redirected to a file; long jobs were then polled through their log files instead. No result was affected.

## Pass 3 — requirements re-check (against the full prompt in README)

| Requirement | Status | Where |
|---|---|---|
| Unique TIF generated (not a copy/relabel) | Done; unique vs 427 non-space-filling rasters. Literal rule blocks every file (policy conflict surfaced) | `docs/downloads/kanler3-k3h1-…tif`, report §4 |
| Obvious OK / not-OK to download and submit | Top of dashboard: download OK · upload format OK · slot NO | `docs/index.html#k3h1` |
| Validation automated, no human inspector | Shared writer + `portal_check.py` + uniqueness gate + promotion gate; CI tests | `tests/test_k3h1.py` |
| Unique name + note ≤140 | `kanler3-k3h1-asgt-hybrid-48559-7ecb7b69` / 103 chars | run card |
| Executive summary per site, best file per site | Done | report §1 |
| Table: file, estimated score, unique vs sites | Done (PROJECTION labelled, never a score) | dashboard table + report |
| PhD-level "why 0.2778" | Break-even rule k > 0.2·DTI, thinning and depletion, nine-site ordering by catalogue-proximal share | report §1 |
| Beat 0.2778 | **Not achieved.** E3 projects 0.252 vs 0.284; negative result delivered | report §3 |
| Fix "[0, 1]" portal error | Diagnosis + checker + fix; the K3-H1 file is immune | report §5, submission guide |
| Submission-instructions subpage | Done | `docs/executive-summary.html#k3h1-upload` |
| Parallel-run protocol (lane, reuse, labels, canary, run card, budget) | Done; lane self-assigned (IR-K3-LANE-01) | run card |
| 3–5 hypotheses ranked before implementing | Done | pre-registration |
| Official sources, no hallucinations | Facts with links; unverifiable items flagged | `knowledge/official-sources-k3h1-20261026.md` |
| Prompt in README, read every session | Full prompt in README `<details>`; reading list updated | README |
| PR + merge to main | See the PR | — |

Not done / limitations: the space-filling-raster policy decision (yours); no unique design beats the champion under the same model; the registry is limited to the user's sites; the sample is a participant mirror; and no organizer receipt exists for any number here.
