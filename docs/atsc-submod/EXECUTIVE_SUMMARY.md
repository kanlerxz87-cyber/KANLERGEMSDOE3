# L-K3-ATSC-SUBMOD Executive Summary & Encoding Reference (Research Only · DO NOT SUBMIT)

- **Selected Candidate**: `kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros` (`Exp-ATSC-2`, 8-fold spatial OOF)
- **Primary `HOLDOUT-DTI`**: **`0.163715`** (`95% CI [0.153314, 0.174809]`, `60,988` withheld positives, `gems-segment-pooled-v1`, **`+0.006635` above prior repo best `CADG Exp-K3-3`**)
- **Orthogonal Confirmation `HOLDOUT-DTI`**: **`0.152844`** (`+0.005181` above `CADG Exp-K3-3` `0.147663`)
- **Research-Only Finite-Grid File**: [`kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros.tif`](downloads/kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros.tif) (`SHA-256: bf21ac69a0e5e6325d9725e7188be210a24b2e68b68060574db56af0d5972566`, `37,654` binary `{0,1}` dots, `0` NaN whole-array locally; portal acceptance unverified)
- **Recorded Note (`104` chars)**: `H-K3S2-1 Exp-ATSC-2: ATSC dip-wedge+8-az corridor+d2.85 300m CELF 37654d HOLDOUT-DTI=0.1637 3108468e86b9`
- **Uniqueness & Fail-Closed Gate**: **PASS across `87/87` genuine fault detectors** (`57.14% <= 70%`, `|rho| = 0.0712 <= 0.90`); **DO NOT SUBMIT** (`verdict = "negative"`, `slot_authorized = false`) under the literal all-registry rule (`99.99%` unfiltered / `99.77%` off-catalogue 3-px overlap vs `206,895`-dot `13GEMSDOE r13-lattice-s5`; selector cannot waive).

## Nine-Site & KANLERGEMSDOE3 Summary Table

| Site / Lane | Artifact | Metric | Uniqueness | Safe to Submit? |
| --- | --- | --- | --- | --- |
| `GEMSDOE24` | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` (`60,069` dots) | `0.2477` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`100.00%` overlap) | **NO** (historical) |
| `GEMSDOE25` | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` (`44,090` dots) | `0.2600` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`100.00%` overlap) | **NO** (historical) |
| `GEMSDOE27` | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` (`61,328` dots) | `0.2449` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`98.02%` overlap) | **NO** (historical) |
| `GEMSDOE28` | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` (`37,660` dots) | `0.2710` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`100.00%` overlap) | **NO** (historical) |
| `GEMSDOE30` | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif` (`44,090` dots) | `0.2600` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`100.00%` overlap) | **NO** (historical) |
| `GEMSDOE31` | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` (`40,199` dots) | `0.2708` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`100.00%` overlap) | **NO** (historical) |
| `GEMSDOE32` | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`37,654` dots) | `0.2778` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`100.00%` overlap) | **NO** (historical) |
| `GEMSDOE33` | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif` (`41,865` dots) | `0.2632` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`99.71%` overlap) | **NO** (historical) |
| `GEMSDOE36` | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`38,854` dots) | `0.2750` (`OWNER-REPORTED-UNVERIFIED`) | **NO** (`97.58%` overlap) | **NO** (historical) |
| **`KANLERGEMSDOE3 (L-K3-ATSC-SUBMOD)`** | [`kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros.tif`](downloads/kanlergemsdoe3-h-k3s2-1-atsc-submod-exp-atsc-2-oof8f-37654-20261027-3108468e86b9-zeros.tif) (`37,654` dots, research-only) | **`HOLDOUT-DTI 0.163715`** (`95% CI [0.153314, 0.174809]`; Diag `HOLDOUT-DTI 0.152844`) | **87/87 genuine detectors &le;57.14%**; **FAILS literal 207k lattice (`99.99%` unfiltered / `99.77%` off-catalogue)** | **DO NOT SUBMIT** (`verdict=negative`, `slot_authorized=false`) |
