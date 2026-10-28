# 28 October 2026 peer-forensics continuation

## Decision

**Negative / do not submit.** This continuation performed a read-only source-tree and saved-byte audit. It did not train a model, spend a DrivenData slot, claim a leaderboard score, or promote a TIFF. The existing `L-K3-ATSC-SUBMOD` research raster remains format-valid and stronger than the previous repository holdout incumbent, but it is blocked by the project's literal all-registry uniqueness rule.

The exact negative receipts are:

- [`evidence/nine_site_and_peer_forensics_20261028.json`](../evidence/nine_site_and_peer_forensics_20261028.json): 35 GitHub repositories, current commit observations, bounded peer-raster selection and the GEMSDOE30 border irregularity.
- [`evidence/atsc-current-peer-audit-20261028.json`](../evidence/atsc-current-peer-audit-20261028.json): exact saved-byte comparison of the ATSC research TIFF against the selected current peer cache.
- [`evidence/atsc-submod-run-card.json`](../evidence/atsc-submod-run-card.json): the original ATSC holdout, leakage, format and literal full-registry decision.

## What was checked

The nine requested focus repositories were refreshed at current GitHub `main` heads on 28 October 2026: `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33` and `GEMSDOE36`. Twenty-six extended/sibling repositories were also queried. The tree fetcher excludes competition input/template files, groups obvious NaN/zero encoding twins by stem, and selects at most 12 unique stems per repository. It downloaded 249 full-grid raster byte streams after SHA-256 de-duplication; 244 were treated as discrete detector candidates and 5 as calibration/continuous probes under the documented rule.

This is **not a complete registry**. It is a reproducible bounded observation of public participant trees. A source commit is not an organizer receipt, a score, or permission to upload. The full registry and pre-placement surface requirement remain separate gates.

## Focus-site table

| Site | 28 Oct observed head | TIFF paths in tree | Unique filename stems | Selected for bounded byte audit | Status here |
|---|---|---:|---:|---:|---|
| GEMSDOE24 | `5a7f227d6f38219e5e0e5fa428ef0f9854967ac4` | 63 | 37 | 12 | Source observation only |
| GEMSDOE25 | `a728c9f42e6298aaa5b65013806ac578f1b2a3ef` | 60 | 32 | 12 | Source observation only |
| GEMSDOE27 | `0f9e3e4b06eeecdd584d32fb9dd7544a01d2f3f0` | 42 | 22 | 12 | Source observation only |
| GEMSDOE28 | `f6746e1ad4eb49a35902bb4fd5404b5e6edc9287` | 52 | 28 | 12 | Source observation only |
| GEMSDOE30 | `c3d6c815ae5b6415b07a39d99058a10d4fda0789` | 34 | 27 | 12 | Source observation only |
| GEMSDOE31 | `cd0b12260807732f3ddb339889984f066d12e870` | 61 | 32 | 12 | Source observation only |
| GEMSDOE32 | `109f364fb39030e40ef51b839b79cf694123b51b` | 79 | 44 | 12 | Source observation only |
| GEMSDOE33 | `1e08a7e81ee4595e2f3770f5c4f7c071adc1a53e` | 44 | 23 | 12 | Source observation only |
| GEMSDOE36 | `4b717aaff6eaf5de9b53030e637f8e1cf0d56e43` | 21 | 17 | 12 | Source observation only |

The live source page may contain its own internal holdout claims or “download” links. Those claims remain quarantined unless they satisfy this repository's evaluator, lineage, leakage, full-registry and selector gates. They are not copied into the score table as organizer-confirmed results.

## GEMSDOE30 off-lattice irregularity

The current GEMSDOE30 source includes `gems30-unique-offlattice-structural-20261028-s8.tif`. Its saved-byte geometry has 6,649 positive in-footprint cells and 0.0% 3-pixel overlap with the pinned 5-pixel calibration lattice. However, 6,493 / 6,649 dots (97.6538%) lie within five pixels, or 500 m, of the outer survey boundary. The uncovered zone contains only 135 / 60,988 mirrored catalogue pixels. This is evidence of a calibration-probe boundary loophole, not evidence of geological quality. It has no qualifying same-evaluator buffered holdout in this checkout and is not a submission recommendation.

The finding does not weaken the literal rule. A complete registry, a policy decision about calibration probes and a scientifically validated prediction surface would be required before any off-lattice placement could be considered.

## Exact ATSC candidate recheck

The ATSC research TIFF is:

`docs/atsc-submod/downloads/kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros.tif`

Its SHA-256 is `bf21ac69a0e5e6325d9725e7188be210a24b2e68b68060574db56af0d5972566`. The saved byte has 37,654 in-footprint dots. The bounded current-peer comparison found:

- 249 selected current peer rasters compared, of which 244 were discrete detectors and 5 were calibration/continuous probes.
- Maximum final-dot overlap against the selected discrete detectors: **57.143995%**, below the 70% stop.
- Maximum final-dot overlap against the selected calibration/continuous probes: **100%**, above the 70% stop.
- No pre-placement surface was available to this read-only recheck; this is not a surface-gate pass.
- No new holdout was run and no leaderboard estimate was produced.

The ATSC run card independently records the stronger, full-lattice stop: the 206,895-dot `r13-lattice-s5` probe covers 99.8713% of the footprint within three pixels and forces a minimum overlap above the 70% threshold for a 37,654-dot candidate. The exact candidate therefore remains **research-only / DO NOT SUBMIT**.

## Scientific result carried forward

The original ATSC campaign remains the only selected lane result in this checkout:

- `HOLDOUT-DTI` `0.1637154060975635`, 95% CI `[0.15331407692303034, 0.1748086574042234]`.
- Evaluator `gems-segment-pooled-v1`; 60,988 withheld positives; pooled alpha `0.2`, beta `0.8`, 300 m triangular kernel.
- It exceeded the recorded same-evaluator CADG incumbent `0.15707951145733381` by approximately `0.006636`, with the recorded paired improvement CI positive against the B0 baseline.
- The local format checks pass, but local format validity is not organizer acceptance.

This is a `HOLDOUT-DTI` measurement, not a projected public leaderboard score. The official competition description states that hidden expert labels are distinct from the public catalogue and that the submission is a single-band float32 GeoTIFF with EPSG:32611, matching bounds/resolution and values in `[0,1]`; see the official sources below.

## Official sources for manual review

- DrivenData problem description and submission format: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- DrivenData public leaderboard (dated public observation, not an artifact receipt): <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
- Official rules PDF: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
- USGS GeoDAWN metadata: <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
- USGS 3DEP: <https://www.usgs.gov/3d-elevation-program>
- GDR INGENIOUS index: <https://gdr.openei.org/submissions/1391>
- Shared-template defect ledger: <https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41>
- Shared feature-cache provenance request: <https://github.com/buffedlizard55-lab/GEMSDOE32/issues/53>

## Next authorized action

Do not create a fourth ATSC experiment or spend a weekly slot in this continuation. The prior lane's three-experiment budget is already exhausted. A future session needs a newly assigned method paragraph, a centrally repaired and pinned evaluator/writer, a content-addressed canonical feature cache, an authenticated organizer template, a complete registry with explicit calibration-probe semantics, and a separate selector authorization. Until then, the negative result is the scientifically correct deliverable.
