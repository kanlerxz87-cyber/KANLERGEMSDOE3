# Three-pass repository review — 31 October 2026

## Decision

**NEGATIVE — do not download or submit any TIFF from this checkout.** No experiment, holdout measurement, candidate raster, or organizer receipt was produced in this review. The assigned single-method paragraph is absent and the inherited fixed two-hour window expired on 27 October; this review does not reset it or choose a lane. The downloadable-looking historical TIFFs are research artifacts, not approved submissions. No defensible score estimate exists for a new candidate.

## Priority-site executive snapshot

The nine-site historical leaderboard table remains at [`docs/EXECUTIVE_SUMMARY.md`](../docs/EXECUTIVE_SUMMARY.md). Its historical numeric entries are explicitly owner-reported, not organizer receipts. For the cited GEMSDOE32 B2 artifact, the claimed 0.2778 is **UNVERIFIED-OWNER-REPORTED**, not HOLDOUT-DTI and not ORGANIZER-CONFIRMED. Plausible explanations for a higher reported score include sparse emission changing the precision/recall trade-off and reduction of penalties near the exact known-fault mask; neither establishes causation or a reproducible score. The old geometry audit records near-total overlap with peer masks, so it is not a unique strategy under the user's literal rule. A score above it cannot be asserted without a candidate run and receipt.

| Priority site | Historical best listed in user-provided snapshot | Estimate for a new candidate | Unique new artifact | Download / submit |
|---|---:|---|---|---|
| GEMSDOE24 | 0.2477 (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE25 | 0.2600 (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE27 | 0.2449 (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE28 | 0.2710 (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE30 | 0.2600 (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE31 | 0.2708 (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE32 | **0.2778** (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE33 | 0.2632 (owner report; unverified) | Not estimable | No candidate | No / No |
| GEMSDOE36 | 0.2750 (owner report; unverified) | Not estimable | No candidate | No / No |

The “historical best” column repeats the user-supplied snapshot only; values are not refreshed competition receipts. No TIFF from these peers is recommended for download or reuse as a submission.

## Candidate scientific hypotheses — ranked, conditional, not run

These proposals are carried from the repository's prior research review [`research/session-30454eca-hypotheses.md`](session-30454eca-hypotheses.md); they are not new implementations or validated discoveries. Ranking is qualitative information potential/cost, not a numerical DTI estimate.

| Rank | Hypothesis; layers and physical signature | Why it might identify an unmapped fault | Difference from known implementation | Cost / expected benefit | Named non-fault mimic; availability |
|---|---|---|---|---|---|
| 1 | **Cross-scale edge phase disagreement:** TMI/RTP, 150 m upward continuation, GeoDAWN K/Th/U; signed radiometric derivative reversal or termination at persistent magnetic edge | Concealed structure may preserve a deeper magnetic discontinuity while shallow alteration changes across its trace, rather than merely ranking catalog-near pixels | The signed cross-scale/radiometric termination interaction is not evidenced as implemented here; current GPC phase-concordance means direct feature-level comparison is required before claiming novelty | Medium cost; highest qualitative information potential, no numerical improvement forecast | Intrusive contact or flight-line levelling seam; official context: [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). Required authenticated inputs/cache are absent, so not presently testable |
| 2 | **Repeated drainage displacement graph:** detrended elevation, slope and derived channel graph; signed lateral offsets recur across independent tributaries | A buried transverse fault could offset channels without a continuous surface scarp or mapped trace | Graph-level repeated displacement differs from pixelwise DEM ridge extraction; peer hydro/conduit overlap still needs review | High cost; second qualitative rank, 100 m resolution is a serious limitation | Stream capture, fan avulsion or abandoned shoreline; potential official source [USGS National Map Downloader](https://apps.nationalmap.gov/downloader/). Required high-resolution tiles/coverage not verified obtainable |
| 3 | **Alteration-front termination pairs:** GeoDAWN K/Th/U ratios with independent magnetic edge axes; paired along-strike front terminations | An unmapped transverse structure may compartmentalize alteration away from the strongest anomaly | Pairing/topology differs from pixelwise alteration conjunction; global novelty not established | Medium cost; third qualitative rank, no calibrated forecast | Erosional unconformity, lithologic boundary or soil moisture; USGS GeoDAWN original archive and canonical cache absent/authentication unresolved |
| 4 | **Terrain-conditioned thermal sign asymmetry:** GDR well/spring temperatures and metadata, elevation/aspect/drainage; terrain-adjusted residual sign consistency across a line | Focused upflow may corroborate permeability away from mapped traces, but is not itself proof of a fault or vent | Not implemented locally; must distinguish from existing geothermal-conduit/PINN peer families | High cost; lower actionability due sparse and seasonally biased sampling | Groundwater advection, seasonality, pumping; [OpenEI GDR submission 1391](https://gdr.openei.org/submissions/1391) index was reachable in prior review, but direct archive fetch failed and coverage/fields remain unverified; not viable for this run |

No hypothesis is selected or validated. The existing review reports lack of authenticated raster inputs/canonical feature stack and an upstream shared-evaluator defect; no private evaluator/writer fork is appropriate. The official competition description and requirements are available at [DrivenData overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (authentication required per prior repository checks), and [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).

## Pass 1 — inspect and reproduce

- Read `README.md`, `PROJECT_PROMPT.md`, `PROJECT_REQUEST.md`, `AGENTS.md`, the standing rules, prior continuation review/cards and current source inventory.
- Created an ignored local `.venv` and installed the pinned `requirements.txt` dependencies; no tracked environment files were created.
- Ran `.venv/bin/python scripts/build_site.py --check`: **failed closed** with `Inherited/quarantined TIFF inventory or authorization receipt changed`.
- Ran `.venv/bin/python -m pytest -q`: **312 passed, 9 skipped, 14 failed, 4 errors**. Failures were primarily the same inventory mismatch in the site builder; one link test also failed. Do not represent this as a passing suite.
- The checkout contains eight TIFFs in `docs/downloads/`; `evidence/inherited_literal_audit.json` covers four inherited rasters, while current quarantine metadata separately covers other entries. The inventory check detects unclassified TIFFs and must not be bypassed. No full raster audit was possible here because pinned core template/labels/lattice are absent locally.

## Pass 2 — adversarial review and blockers

- The build check deliberately does not repair pages/evidence; running a write-mode builder or changing the expected file inventory without exact-byte audit could publish unsupported authorization.
- The user's lane protocol has no assigned method paragraph. Existing session configuration has a fixed expired start/budget and cannot be reset. Therefore no geological experiment or holdout is permitted by the preserved protocol.
- The full registry is not certified complete, the canonical cache bytes/digest are absent, organizer data provenance is unresolved, and prior shared evaluator issues are documented. A score copied from a participant site cannot substitute for the prescribed HOLDOUT-DTI tuple or an organizer receipt.
- Historical generated artifacts must remain quarantined. File format acceptance, scientific improvement, uniqueness, portal acceptance and selector/weekly-slot authorization are separate checks.

## Pass 3 — request reconciliation and next steps

This review did not generate the requested new unique TIFF: doing so would violate the unassigned-lane, expired-budget, shared-cache/evaluator, registry and no-promote gates. The project cannot currently estimate a new submission score; report **not estimable**, not a numeric projection. The recorded focus-site 0.2778 is a user/participant claim and cannot be treated as a score estimate for another file. There is no “OK to download and submit” TIFF in this review.

Next session actions, in order: obtain a fresh explicit single-method assignment and authorized budget; restore approved organizer-authenticated inputs and canonical cache provenance; centrally repair/pin the shared evaluator and writer; produce a content-addressed complete registry with explicit continuous-surface dot semantics; bind a same-fold incumbent; refresh current peer source artifacts and independently audit every newly found TIFF before site generation; only then run the top-ranked preregistered candidate with per-feature leakage canaries, whole-segment buffered holdout and paired CI. Keep the separate selector/weekly quota decision outside model promotion.

**Core values:** Maximize P(Win) by preserving slots until evidence is valid; Own the Outcome by recording these failed checks and not disguising the negative result.
