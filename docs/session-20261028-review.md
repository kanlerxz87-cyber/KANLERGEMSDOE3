# Three-pass review — 28 October 2026

## Executive decision

**NEGATIVE / DO NOT SUBMIT.** No method paragraph was assigned, the fixed experiment clock has expired, and multiple research and submission gates are false. No geological experiment ran, no candidate TIFF or fresh HOLDOUT-DTI value was generated, no leaderboard estimate is defensible, and no competition slot was spent or authorized. The requested validated TIFF and submission note are **not delivered** because there is no safe candidate to provide. This negative result is the correct deliverable; a renamed prior raster or privately rebuilt cache would violate the protocol.

Start each future session with the persistent task prompt in `README.md` and `PROJECT_PROMPT.md`, then inspect the current receipts linked below. Do not reset the fixed clock or infer a method lane.

- [Current run card](../evidence/session-20261028-run-card.json)
- [Nine-site source review](../evidence/session-20261028-focus-source-review.json)
- [Corrected upstream prerequisite audit](../evidence/session-20261028-upstream-prerequisites.json)
- [Negative preflight](../evidence/session-20261028-preflight.json)
- [Ranked hypotheses](hypotheses.md)
- [Submission guide](../docs/executive-summary.html)

## Pass 1 — repository, inputs, and recorded evidence

1. Re-read the standing prompt, fixed prior config, README, project instructions, registry/source feeds, historic run cards, and generated-site checks. The working session remains on `arena/b7809aa3-kanlergemsdoe3`; no branch switch, commit, push, PR, or merge was performed.
2. Restored five SHA-pinned inputs from participant mirrors and ran the shared raw-band preparation. Grid: EPSG:32611, 3,730 × 3,292; 5,167,373 footprint pixels; 60,988 catalogue-positive pixels in this mirror; sentinels affect 3,073 distinct footprint pixels. These are input/preparation measurements, not model performance. The hashes establish mirror consistency, not organizer authentication.
3. Confirmed the 19 prepared raw bands and that the canonical 35-channel cache bytes and digest are absent. Raw preparation is **not** the canonical feature-stack build. No cache was privately rebuilt.
4. Refreshed the nine-site focus feed and peer-head observations at `2026-10-28T16:23:32Z`; 9/9 head comparisons agree. Refreshed pinned participant source files: 33 retrieved, seven score-ledger paths absent at the pinned commits. Missing score ledgers are not score evidence.
5. The fixed config `config/research-session-e2903b2e.json` remains expired. Current preflight verifies all five configured input hashes but returns `research_ready=false`, `submit_ready=false`, `slot_authorized=false`, `experiments_used=0`, and `submission_slots_used=0`. No experiment or cache build followed.

## Pass 2 — hostile source, score, and novelty review

### Current shared source audit

The corrected audit is pinned to the participant repository `buffedlizard55-lab/GEMSDOE32` at HEAD [`109f364fb39030e40ef51b839b79cf694123b51b`](https://github.com/buffedlizard55-lab/GEMSDOE32/tree/109f364fb39030e40ef51b839b79cf694123b51b), observed at `2026-10-28T16:30:34Z`.

- Current evaluator/writer wrappers call a binary-mask validator; current source also has outside-footprint checks. This is **static source inspection only**—neither guard was dynamically retested at this HEAD. Open issue titles from an older source snapshot are not proof those current guards are absent.
- The current `src/gems32/holdout.py` still has an `n_t == 0` early-continue before adding prediction false-positive mass to pooled `fp_blk`. This is a source-visible operator concern, not evidence that any organizer score was affected.
- `scripts/arena8a_run_experiments.py` excludes a synthetic lattice from one 3-px overlap threshold. That conflicts with the user's strict all-registry rule; no exemption is accepted.
- `src/gems32/features.py` retains the smaller-magnitude Hessian eigenvalue in the ridge response. This observation is relevant to future shared-tool review, not a new experiment result.
- The earlier synthetic audit was pinned to vendor source commit `400b60d4a6d99f425ee90504e6c4552227556dd1`; do not describe its old soft-input behavior as a verified defect at current HEAD. The corrected receipt records scope and dynamic-test gaps.

The assigned method paragraph, canonical cache/digest, complete representation-resolved registry/saturation rule, same-fold incumbent, current-head operator repair/tests, and unexpired budget are all still missing. Thus **research is not ready** and no surface or final-dot novelty result exists for a new candidate.

### Current participant-page decisions

Each row below is a source-page statement pinned to its immutable participant commit, not organizer approval, a new raster audit, or a score receipt. The two refreshed feeds agree, but all nine heads differ from the prior 26 October registry snapshot, so those older TIFF comparisons do not clear current files.

| Site | Current participant-page statement | Pinned source |
|---|---|---|
| GEMSDOE24 | Research download only; `SUBMIT: NO`. | [1778da6](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/1778da6ae1f14f26b4bbc6c385f4a64ca6e9e4a6/docs/index.html) |
| GEMSDOE25 | No competition-ready TIFF, eligible download, or slot; `SUBMIT: NO`. | [a728c9f](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/a728c9f42e6298aaa5b65013806ac578f1b2a3ef/docs/index.html) |
| GEMSDOE27 | No candidate approved; page says not to upload historic/research TIFFs. | [0f9e3e4](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/0f9e3e4b06eeecdd584d32fb9dd7544a01d2f3f0/docs/index.html) |
| GEMSDOE28 | No new TIFF approved; duplicates and missing validation remain blocking. | [f6746e1](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/f6746e1ad4eb49a35902bb4fd5404b5e6edc9287/docs/index.html) |
| GEMSDOE30 | No new TIFF; published calibration-lattice overlap blocks the historical artifact. | [c3d6c81](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/c3d6c815ae5b6415b07a39d99058a10d4fda0789/index.html) |
| GEMSDOE31 | Newest H31-CC is negative and explicitly `DO NOT SUBMIT`. | [cd0b122](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/cd0b12260807732f3ddb339889984f066d12e870/docs/index.html) |
| GEMSDOE32 | No upload authorized; research artifacts remain `DO NOT SUBMIT`. | [109f364](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/109f364fb39030e40ef51b839b79cf694123b51b/docs/index.html) |
| GEMSDOE33 | Zero eligible candidates; research downloads only, `SUBMIT: NO`. | [1e08a7e](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/1e08a7e81ee4595e2f3770f5c4f7c071adc1a53e/docs/index.html) |
| GEMSDOE36 | Literal uniqueness gate failed; no candidate or slot approved. | [4b717aa](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/4b717aaff6eaf5de9b53030e637f8e1cf0d56e43/docs/index.html) |

A full current-head inventory of TIFF bytes, surfaces and final dots was **not** performed. The current source review binds each page’s exact Git blob and SHA-256 but explicitly leaves raster clearance false.

### Historical score provenance

- `docs/data/sites.json` stores these nine portfolio numbers as **UNVERIFIED OWNER REPORT**, with no estimate and no submission receipt linking a number to an exact uploaded TIFF hash: GEMSDOE24 `0.2477`; 25 `0.2600`; 27 `0.2449`; 28 `0.2710`; 30 `0.2600`; 31 `0.2708`; 32 `0.2778`; 33 `0.2632`; 36 `0.2750`. They are historical claims in this repository, not organizer-confirmed scores or predictions for a new file.
- The repeated `0.2778` GEMSDOE32 B2 claim has no retained organizer submission-page receipt. A hash-pinned geometry audit found the B2 dot mask is the GEMSDOE30 mask after deleting catalogue-near dots, with no additions; this is not causal proof of the claimed score.
- Some current participant pages report local `HOLDOUT-DTI` observations. They are participant claims and were not rerun in this session. A valid label must retain `HOLDOUT-DTI`, evaluator version, withheld-positive count and 95% CI; none is converted into an organizer score here.
- The latest stored public-leaderboard observation is stale/unavailable for current scoring and is not used as a leaderboard estimate. The official leaderboard is [here](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/); the official task page documents the [format and performance metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). No official page was re-observed as a current per-file receipt in this review.
- The pinned retrieval has seven `docs/score-ledger.csv` paths `not_found`; no ledger is invented from an older snapshot. Current participant pages are not independent score receipts.

Historical geometry is also not a leaderboard score: the earlier 9-site audit found the supplied winners over the literal 70% directed 3-px overlap threshold against other focus-site winners. That dated result is a duplicate stop for those archived files only; it cannot prove novelty or duplication of every newer file.

## Pass 3 — hypothesis ranking, site, and submission workflow

After comparing existing local ideas and the latest source/code scan, I did **not** relabel earlier Morse–Smale, directional-fabric, edge-migration, Fourier/phase, drainage, or geochemical families as new. The current qualitative order is:

1. **Windowed potential-field spectral-slope break** — medium cost; existing `rtp`, `tmi`, and `iso_grav_anom` layers. Test for co-located changes in long/short wavelength decay that could indicate a buried source-depth/domain boundary. Related Fourier continuation and Euler/local-wavenumber methods exist, but a focused local/source search found no exact windowed radial spectral-slope change point. Intrusive contacts, line levelling, basin mixing, and window leakage are strong mimics. Expected DTI improvement is unknown; no numeric estimate.
2. **Offset geometry of non-fault geologic contacts** — high cost and **not viable now**. It needs official bedrock map polygons, exact coverage/scale/metadata and verified downloadable bytes. The USGS [National Geologic Map Database](https://ngmdb.usgs.gov/) is only an index; footprint coverage was not checked, so this is deferred rather than presented as available data.
3. **Hydrothermal-alteration contrast across independent structure** — high cost and **not viable now**. It would need a pinned ASTER surface-reflectance product with usable coverage and cloud/vegetation treatment. The NASA/USGS [LP DAAC catalog](https://lpdaac.usgs.gov/products/) is an official portal, but product, AOI coverage, access, and bytes were not checked or obtained.

The ranking is planning-only and not a lane selection, global-novelty claim, score estimate, or authorization to build features. Full layers, mechanisms, mimics, source availability and limitations are in [the hypothesis record](hypotheses.md).

The website makes the download/submit decision explicit: **no candidate download, `DO NOT SUBMIT`, no slot**. A future candidate would require a single-band TIFF validated against the authenticated template for CRS, shape, transform, footprint and NaN/Inf handling, `[0,1]` values, and exact saved-byte SHA-256; surface and final-dot comparisons against the complete registry; a qualifying paired HOLDOUT-DTI record; a unique name and ≤140-character note; then a separate selector decision. A format pass alone cannot authorize a competition slot or prove portal acceptance. See the [automated submission guide](../docs/executive-summary.html).

## Limitations and next steps

1. Obtain the missing method paragraph and an explicit fresh selector/clock decision before research.
2. Centrally supply and digest the canonical cache; do not privately regenerate it. Repair and dynamically test the current shared evaluator/writer at a pinned HEAD, including zero-truth pooled false positives, binary/outside guards, and the all-registry synthetic lattice rule.
3. Resolve the complete raster/dot registry representation and current same-fold incumbent; recompare current source-tree TIFFs and pre-placement/final dots literally.
4. Only after those gates pass, re-rank the method lane, run its feature-only leakage canaries, and follow the hide-whole-segments/buffered pooled-DTI protocol. Stop at three experiments or two hours. Do not choose or spend a slot.
5. Refresh official-source observations and obtain score-to-file receipts before making any organizer-confirmed score statement. Do not project HOLDOUT-DTI to the public leaderboard.

**Final card:** `evidence/session-20261028-run-card.json`. `holdout_dti`, CI, registry comparisons, raster SHA, and validator values are null/not run because no candidate exists; promotion is false; the negative verdict is final for this expired fixed session.
