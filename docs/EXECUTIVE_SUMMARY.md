# Executive Summary — KANLERGEMSDOE3 Nine-Site Audit & Validated Candidate

**Review date:** 2026-10-26 (UTC)
**Assigned Lane:** `L-K3-CADG-SUBMOD` (`H-K3-1` / `Exp-K3-3`, 8-fold spatial OOF cross-fitted)
**Automated Gate Verdict (`scripts/promotion_gate.py`):** **`negative` (`slot_authorized = false`, `live_submission_slots_used = 0` — HOLD FOR HUMAN SELECTOR)**
**Genuine 35-Detector Uniqueness:** **`PASS`** (`max 3-px overlap = 57.11% <= 70%`, `max |Spearman rho| = 0.1598 <= 0.90`)
**Primary Downloadable Candidate:** [`kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif`](downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif) (`826,834` bytes, SHA-256 `9f4b590d0bd887632c54ec34c114136d4de52d452de052ba105e35ebfeffe8b5`) · [1-TIFF ZIP](downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.zip) · [NaN-outside twin](downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-nan.tif)

## Executive Summary Table (9 Priority Sites + KANLERGEMSDOE3)

| Site | Downloadable / Audited File | Defensible Score / Provenance | Est. Live Score | Unique vs Registry? | OK to Submit? |
|---|---|---|---|---|---|
| `GEMSDOE24` | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` (`60,069` dots) | `0.2477` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** |
| `GEMSDOE25` | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` (`44,090` dots) | `0.2600` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** |
| `GEMSDOE27` | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` (`61,328` dots) | `0.2449` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`98.02%` peer 3-px overlap) | **NO** |
| `GEMSDOE28` | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` (`37,660` dots) | `0.2710` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** |
| `GEMSDOE30` | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif` (`44,090` dots) | `0.2600` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** |
| `GEMSDOE31` | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` (`40,199` dots) | `0.2708` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** |
| `GEMSDOE32` | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`37,654` dots) | `0.2778` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`100.00%` peer 3-px overlap) | **NO** |
| `GEMSDOE33` | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif` (`41,865` dots) | `0.2632` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`99.71%` peer 3-px overlap) | **NO** |
| `GEMSDOE36` | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`38,854` dots) | `0.2750` (`UNVERIFIED OWNER REPORT`) | Not estimable | **NO** (`97.58%` peer 3-px overlap) | **NO** |
| **`KANLERGEMSDOE3`** | [`kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif`](downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif) (`37,654` dots) | **`HOLDOUT-DTI 0.155510`** (`95% CI [0.1415, 0.1698]`, `60,988` pos) | Not estimable | **YES vs 35/35 detectors** (`57.11%` max; `99.75%` vs 207k lattice probe) | **HOLD FOR HUMAN SELECTOR** (`verdict=negative`) |

## Why `GEMSDOE32` (`H33-B2`, Owner-Reported `0.2778`) Performed Well — and How `KANLERGEMSDOE3` Advances

1. **Exact Subset Chain:** Byte-verified pixel comparison establishes `H33-B2` (`37,654` dots, reported `0.2778`) `⊂ H27-4` (`40,199`, `0.2708`) `⊂ D2.8` (`44,090`, `0.2600`) `⊂ H19-5` (`121,131`, `0.1922`), where `H33-B2 = D2.8 & (d_catalogue > 2.0 px)` removes `6,436` near-catalogue dots.
2. **DTI Metric Mechanism:** Per official DrivenData confirmation ([Thread #11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)), existing USGS/INGENIOUS catalogue pixels are masked from evaluation in both Phase 1 and Phase 2, and every uncredited off-catalogue dot incurs `0.2 * FP_w` penalty outside the 300 m (`3 px`) triangular kernel.
3. **8-Fold Cross-Fitted `CADG-Submod` (`Exp-K3-3`):** Achieves **`HOLDOUT-DTI = 0.155510`** (`95% CI [0.141542, 0.169790]`, `+52.1%` over matched `B0_regional_d28 = 0.102267`, `4/4` folds) and **`0.151134`** on orthogonal `DiagonalSegmentHoldout(buffer_px=20)` (`4/4` folds), places **`62.9%`** of its `37,654` dots `> 1 km` from mapped faults, and overlaps `GEMSDOE32` on only **`46.32%`** within `3 px` (`53.7%` newly discovered fault traces).

## How to Submit (After Human Selector Sign-Off)

1. Confirm remaining weekly DrivenData submission quota (`<= 3/week` per [DOE/NLR FY26-96647](https://docs.nlr.gov/docs/fy26osti/96647.pdf)) and explicit selector sign-off on the synthetic `r13-lattice-s5` pigeonhole bound (`>= 82.34%` at `37,654` dots).
2. Upload [`kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif`](downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif) or [`kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.zip`](downloads/kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.zip) (`all 12,279,160 float32 cells in {0.0, 1.0}`, preventing `"Predicted values must be in range [0, 1]"`).
3. Paste submission note (`90/140` chars): `K3 Exp-K3-3 8f-OOF: decontam scarp+TMI150+hydro 300m CELF 37654d | HOLD-SEL | 9a4ecfd71d00`.
