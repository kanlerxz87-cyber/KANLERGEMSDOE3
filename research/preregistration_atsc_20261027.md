# Preregistered Geological Hypotheses & Controlled 3-Experiment Plan (`L-K3-ATSC-SUBMOD`)

- **Repository / Branch:** `kanlerxz87-cyber/KANLERGEMSDOE3` (`arena/9cdeb62a-kanlergemsdoe3`)
- **Preregistration Timestamp:** `2026-10-27T00:00:00Z` (frozen prior to training or evaluating any `ATSC` experiment)
- **Assigned Single-Method Lane:** `L-K3-ATSC-SUBMOD` (*Anisotropic Tectonic-Strain Corridor & Listric Hanging-Wall Wedge Tomography with Non-Clumping 300 m Submodular Allocation*)
- **Shared Evaluator & Writer Reused Without Fork:** `vendor/gems24_template/holdout.py` (`SegmentHoldout`, `buffer_px=15`, `evaluator_version="gems-segment-pooled-v1"`, plus orthogonal `DiagonalSegmentHoldout`, `buffer_px=20`), `vendor/gems24_template/metric.py` ($\alpha=0.2, \beta=0.8$, $300\text{ m}$ kernel), and `vendor/gems24_template/submission.py` (`scripts/cadg_submission_writer.py`).
- **Hard Protocol Gates Enforced:**
  1. Single-feature two-polarity leakage canary $\max(\text{AUC}, 1-\text{AUC}) \le 0.90$ on every feature before modeling.
  2. Strict budget of $\le 3$ controlled within-lane experiments (`Exp-ATSC-1`, `Exp-ATSC-2`, `Exp-ATSC-3`) and $\le 2$ wall-clock hours.
  3. Uniqueness checked on **both** the continuous pre-placement score surface (`|Spearman rho| <= 0.90`) and final discrete dots (`|Spearman rho| <= 0.90` AND directional `3 px` overlap `<= 70%`) against the 36-raster core registry, all 6 prior `KANLERGEMSDOE3` lanes (including `f0565e6d10f9`), all 9 priority sites (`GEMSDOE24..36`), and all 58 Oct 26–27 peer/sibling GeoTIFFs (`KANLERGEMSDOE1..2`, `WBGGEMSDOE1..3`, `GEMSDOEkarage1..3`, `ApartGEMSDOE1..3`, `GEMSDOESASS1..3`, `GEMSDOE70/76/91/92`).
  4. Literal all-registry fail-closed gate (`scripts/promotion_gate.py`) preserved unmodified so `13GEMSDOE` `r13-lattice-s5` (`99.87%` footprint coverage) and `GEMSDOE48` full-footprint continuous surface remain transparently reported alongside genuine fault-detector uniqueness.

---

## Why Prior Repo & Peer Models Plateaued (Empirical Live-Leaderboard Synthesis)

Forensic synthesis of `H33-B2` (`GEMSDOE32`, `0.2778` owner-reported live), `GEMSDOE70` `P8` (`0.2478`), `GEMSDOE76` `PTCF` (`0.2343`), `GEMSDOE27` `H31-1` (`0.2250`), `GEMSDOE36` `KPL-36` (`0.1647` live / `0.1701` holdout), and `KANLERGEMSDOE3`'s prior `CADG-Submod Exp-K3-3` (`0.157080 HOLDOUT-DTI`) establishes four governing failure modes:

1. **Zero-Lag Dip Blindness on $45^\circ\text{–}65^\circ$ Basin-and-Range Normal Faults:** Every prior model in `KANLERGEMSDOE3` (`GPC-3`, `K3-H1 ASGT`, `DCAP-LHC`, `SSP1`, `CADG-Submod`) evaluated gravity, magnetic, MT conductance, and thermal fields at zero pixel offset $(r, c)$ relative to surface breaklines. On listric normal faults dipping $45^\circ\text{–}65^\circ$ basinward, the subsurface basement density/susceptibility step (`iso_grav_anom_hg`, `TMI_up150_hg`) and hanging-wall clay-cap / thermal upflow wedge (`cond_surf`, `F2mDAB`) are displaced $300\text{–}800\text{ m}$ ($3\text{–}8\text{ px}$) down the $\nabla\text{depth\_to\_base\_surf}$ vector from the surface scarp.
2. **Myopic 1-Stage Pixelwise Halo Bleed & 3-px Blob Crowding:** 1-stage pixelwise GBDTs (`CADG-Submod`, `KPL-36`) emit `1–2 km`-wide diffuse probability aprons along range fronts, causing `>=3`-neighbor 300 m dot crowding (`42.57%` in `KPL-36`) that wastes $FP_w$ denominator budget without covering new fault length.
3. **24.63% 1 m LiDAR Coverage Void:** `1,272,913 / 5,167,373` footprint cells lack 1 m 3DEP LiDAR (`NE_LidarGapHeavy` is $>60\%$ void), starving single-regime scarp detectors unless a dedicated seamless 10 m 3DEP + geophysical expert is calibrated and normalized in Stage-2.
4. **Three Live-Leaderboard Physical Laws:** Every non-`H19-5` submission scoring $>0.22$ live simultaneously satisfies: (i) **$>50\%$ far-field reach** ($d_{\text{cat}} > 1.5\text{ km}$), (ii) **$<4.3\%$ flat deep-basin spill** (`slope < 2°` & `depth > 300 m`), and (iii) **crisp single-strand 300 m spacing** (`Clump>=3 < 5%`) outside the uncredited $d_{\text{cat}} \le 2\text{ px}$ collar.

---

## Ranked Shortlist of 4 Untried Geological Hypotheses

| Rank | ID | Title | Specific Layers | Physical Transform | Expected `HOLDOUT-DTI` Gain | Cost | Sandbox Viable? |
|---:|---|---|---|---|---|---|---|
| **#1** | **`H-K3S2-1`** | **Anisotropic Tectonic-Strain Corridor & Listric Hanging-Wall Wedge Tomography (`ATSC-Submod`)** | Core 19-band stack + 1 m LiDAR + seamless 10 m 3DEP DEM/`chi` + GeoDAWN `TMI_up150` + TIGER roads + GDR #1391 2 m probes/springs/sinter | Basinward $\pm 300\text{–}700\text{ m}$ dip-offset scarp-to-basement/conductance/thermal coupling + nested inner-OOF Stage-2 8-azimuth (`1.0 km` / `2.6 km`) corridor tomography + `800 m` crest sharpening + `d=2.85` 300 m CELF | **`+0.025` to `+0.048`** over `CADG-Submod` (`0.1571`) | Medium (`~15 min` CPU, `<450 MB` RAM) | **YES — Selected Active Lane** |
| **#2** | **`H-K3S2-2`** | **GeoDAWN Survey-Seam Deconfounding & $^{214}\text{Bi}/^{208}\text{Tl}$ Radon-Transport Degassing Ridges** | GeoDAWN `U`, `Th`, `K`, `U/Th`, `U/K`, `Th/K` (`geodawn_rad_u8.tif`, `geodawn_extensions_u8.tif`) + compiled block geometry | High-pass DoG (`150 m - 1,000 m`) of `U/Th` ($^{222}\text{Rn}$ gas transport proxy normalized by immobile Th) & `K/Th` + survey-block seam suppression | **`+0.004` to `+0.012`** incremental (tested in `Exp-ATSC-2`) | Low (`~4 min` CPU) | **YES — Tested in `Exp-ATSC-2`** |
| **#3** | **`H-K3S2-3`** | **Fold-Visible Coulomb Tip-Propagation Lobe $\times$ Label-Free Corridor Bridge** | Fold-local `fold["visible"]` endpoints + Stage-1 geophysical/10 m-3DEP corridor field $P_1(x)$ | Forward $\pm 22^\circ$ endpoint tangent stress-lobe (`300–3,500 m`) gated multiplicatively by label-free 2.6 km Stage-1 corridor continuity in Stage-2 only | **`+0.002` to `+0.010`** on sparse splits (tested in `Exp-ATSC-3`) | Low (`~4 min` CPU) | **YES — Tested in `Exp-ATSC-3`** |
| **#4** | **`H-K3S2-4`** | **Raw 1-D GeoDAWN Flight-Line CWT Singularity Chains $\times$ NASA OPERA `DISP-S1` InSAR Phase-Step** | USGS ScienceBase GeoDAWN raw 1-D line data (`10.5066/P93LGLVQ`) + NASA ASF OPERA L3 `DISP-S1` (`30 m` Sentinel-1 LOS velocity) | 1-D Mallat-Hwang wavelet modulus-maxima depth inversion along flight tracks + across-strike InSAR aquifer-barrier velocity steps $\|\nabla_\perp v_{\text{LOS}}\|$ | High theoretical gain in flat playas (unprojected without data) | High (`~12 GB` raw ingest) | **NO — Blocked by sandbox egress allowlist** |

### Detailed Verification of Novelty, Non-Fault Mimics, and Official Free Data Sources
1. **`H-K3S2-1` (`ATSC-Submod`):**
   - *Why missing from USGS/INGENIOUS catalogue:* Captures $45^\circ\text{–}65^\circ$-dipping concealed piedmont and intrabasin normal/transtensional faults whose subtle 10 m-3DEP surface breakline is shifted `300–700 m` updip from its gravity/magnetic basement step, and multi-kilometer en-echelon fault corridors across the `24.63%` 1 m LiDAR void where single-pixel SNR is too weak for 1-stage detectors.
   - *Difference from all repo lanes:* `CADG-Submod` (`Exp-K3-3`), `DCAP-LHC`, `GPC-3`, `K3-H1 ASGT`, and `SSP1` are all 1-stage pixelwise or local-window detectors without $\pm 300\text{–}700\text{ m}$ $\nabla\text{depth\_to\_base\_surf}$ hanging-wall tomography and without nested inner-OOF Stage-2 8-azimuth (`1.0 km` / `2.6 km`) corridor continuity & cross-strike concentration.
   - *Named non-fault mimic:* Tilted Mio-Pliocene ash-flow tuff hogbacks or buried caldera ring margins dipping basinward above alluvial fans.
   - *Official free data sources (all verified & SHA-256-pinned in `.cache/gems_data/`):* USGS 3DEP 1 m & 10 m (`https://www.usgs.gov/3d-elevation-program`), USGS GeoDAWN (`https://doi.org/10.5066/P93LGLVQ`), US Census TIGER/Line 2024 (`https://www2.census.gov/geo/tiger/TIGER2024/ROADS/`), DOE GDR #1391 INGENIOUS (`https://doi.org/10.15121/1881483`).
2. **`H-K3S2-2` (GeoDAWN Seam + Radon `U/Th` DoG):**
   - *Named non-fault mimic:* Uraniferous rhyolitic tuffs or evaporite roll-front playa margins.
3. **`H-K3S2-3` (Fold-Visible Tip Lobe $\times$ Corridor Bridge):**
   - *Named non-fault mimic:* Alluvial-fan incised feeder channels radiating downslope along the strike projection of a range-front fault tip.
4. **`H-K3S2-4` (Raw 1-D Flight-Line CWT + OPERA `DISP-S1` InSAR):**
   - *Named non-fault mimic:* Agricultural groundwater pumping cones and geothermal reinjection subsidence bowls.
   - *Obtainability verification:* Official free open archives (`https://www.sciencebase.gov/catalog/item/61954f10d34eb622f6908c6c` and `https://asf.alaska.edu/datasets/daac/opera/`) verified by DOI/URL, but outbound hosts are blocked in this sandbox (`github.com`/`codeload.github.com`/`api.github.com`/`npmjs`/`pypi` only); explicitly marked non-viable in-sandbox per prompt instructions.

---

## Frozen 3-Experiment Within-Lane Protocol (`L-K3-ATSC-SUBMOD`)

- **`Exp-ATSC-1` (*1-Stage Dip-Offset Hanging-Wall Wedge Dual-Expert + Non-Clumping `d=2.85` 300 m CELF*):**
  Label-free 58-column `CADG` base + 12-column Group D listric dip-offset hanging-wall tomography (`70` label-free features total), dual LiDAR / 10 m-3DEP HGB ensemble, `800 m` local halo normalization, axial spine emphasis, fold-safe `d_visible > 2.05 px` collar, and `min_self_spacing_px = 2.85` 300 m submodular CELF (`N = 37,654` full-grid equivalent).
- **`Exp-ATSC-2` (*+ GeoDAWN Radon/Seam Group E + Nested Inner-OOF Stage-2 8-Azimuth Structural Corridor U-GBDT*):**
  Adds 10-column Group E (`80` label-free Stage-1 features total) + strictly nested 3-substrip buffered inner-OOF Stage-1 probabilities feeding a Stage-2 8-azimuth (`1.0 km` & `2.6 km`) structural corridor & geodetic-strain U-GBDT (`22` Stage-2 corridor/context features, 100% label-free inputs) + non-clumping `d=2.85` 300 m CELF.
- **`Exp-ATSC-3` (*+ Fold-Visible-Only Fault-Tip Stress-Lobe & Relay-Bridge $\times$ Stage-1 Corridor Interaction in Stage-2*):**
  Adds 4 strictly `fold["visible"]`-derived tip-lobe and band-passed (`>300 m`) relay-bridge $\times$ corridor features to Stage-2 (`26` Stage-2 features), testing head-to-head on identical `SegmentHoldout(buffer_px=15)` and `DiagonalSegmentHoldout(buffer_px=20)` splits whether pure label-free corridor tomography (`Exp-ATSC-2`) or tip-bridge corridor coupling (`Exp-ATSC-3`) achieves higher `HOLDOUT-DTI`.
