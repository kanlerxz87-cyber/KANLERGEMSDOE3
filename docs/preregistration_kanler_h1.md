# Pre-Registration: Five Untried Geological Hypotheses & Frozen Lane `KANLER-H1` (`DCAP-LHC`)

- **Frozen UTC Date:** `2026-10-26` (written and frozen **before** restoring competition rasters or computing any holdout / canary numbers in this session)
- **Session Branch:** `arena/925864ac-kanlergemsdoe3`
- **Shared Evaluator:** `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`, `label-blind-quadrants-v2`, `buffer_px = 80`, pooled DTI `alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel, `60,988` withheld catalogue positives) + untouched `50%` random-component confirmation split (`seed = 3103`, `29,965` withheld positives).
- **Lane Governance Disclosure (`IR-KANLER-LANE-01`):** The standing prompt text invokes `PARALLEL-RUN PROTOCOL §1` (*"Your lane is the single method paragraph below"*) without an appended method paragraph, while simultaneously requiring (`HIGHEST URGENCY`) generation of 3–5 untried geological hypotheses ranked by expected DTI improvement and implementation cost, holdout validation of the top candidate, and automated generation/validation of a genuinely unique `.tif` submission. We therefore pre-register five untried hypotheses below, lock **Rank #1 (`KANLER-H1: DCAP-LHC`)** as the **single frozen lane** for this session, and enforce `<= 3` experiments and zero post-holdout retuning.

---

## 1. Five Untried Candidate Geological Hypotheses

| Rank | ID | Hypothesis Name | Primary Layers | Target Missing-Fault Regime | Expected `HOLDOUT-DTI` | Impl. Cost | Status |
|---:|---|---|---|---|---|---|---|
| **1** | **`KANLER-H1`** | **Dip-Coupled Asymmetric Piedmont-Scarp, Road-Vetoed 1m LiDAR & Hydrothermal-Magnetic Conduit (`DCAP-LHC`)** | `B12 det_elev`, `B19 det_elev_slope`, `B05 iso_grav_anom_slope`, `B15 depth_to_base_surf`, `B02 rtp`, `B03 tmi_hg`, `B09 tmi_vg`, `B17 cond_surf`, `B04/B07` strain, `ext_lidar_scarp_features_u8`, GeoDAWN `TMI_up150` + `K/Th`, GDR `#1391` paleo/probes, Census `tiger_road_distance_m` | Unmapped range-front piedmont breaks (`>6°`), `<1.5 m` Holocene 1m-LiDAR alluvial-fan scarplets (`1°–8°`), and dipping/blind hydrothermal-magnetic basin faults (`<4°`) | **`0.175 – 0.215`** (target `> 0.1661` cross-site best) | Low–Medium (~4 min CPU, `<600 MB` RAM) | **SELECTED FROZEN LANE** |
| 2 | `KANLER-H2` | Upward-Continued Aeromagnetic Euler-Tilt & Magnetite-Destruction Trough (`ETD-MDT`) | `B02 rtp`, `B03 tmi_hg`, `B09 tmi_vg`, `B14 tmi`, GeoDAWN `TMI_up150`, `K`, `Th`, `U`, `B05` | Zero-relief intrabasin faults under playal/eolian cover leached by oxidizing hydrothermal fluids | `0.085 – 0.120` | Low | Blind conduit physics folded into `H1` Line 4 |
| 3 | `KANLER-H3` | Multi-Catchment Wineglass-Facet & Knickpoint Alignment (`WF-KPA`) | `B12 det_elev`, `B19 det_elev_slope`, 1m LiDAR `relief`, `ex_max`, `cross_max` | Pre-Holocene Quaternary range fronts where alluvial aggradation buried toe scarps | `0.130 – 0.150` | Medium | Deferred |
| 4 | `KANLER-H4` | Transtensional Riedel-Relay Coulomb Shear-Dilatation Azimuthal Steered Detector (`RCSD-BRIDGE`) | `B04 geod_2ndinv`, `B07 geod_shearrate`, `B08 geod_dilaterate`, `B10/B16` seismicity, `B05`, `B12` | En-echelon oblique Walker Lane stepover splays (`R` and normal-relay azimuths) | `0.110 – 0.140` | Low | Deferred |
| 5 | `KANLER-H5` | Upslope-Backprojected Paleo-Sinter/Tufa & 2m Thermal Feeder Inversion (`PHT-SPI`) | GDR `#1391` `paleo_geothermal_regional` (`281` sinter/tufa mounds), `2m_temperature_probe`, `gdr_wellspring`, `B17 cond_surf`, `U/Th` | Blind geothermal upflow feeder faults upstream of lateral shallow outflow plumes | `0.050 – 0.080` standalone | Low | Hydrothermal boost folded into `H1` Line 4 |

### Detailed Physical Specifications of Each Hypothesis

#### `KANLER-H1` (`DCAP-LHC`) — Selected Frozen Lane
1. **Specific Layers Used:**
   - Official competition stack (`training_features.tif`): `B12 det_elev`, `B19 det_elev_slope`, `B05 iso_grav_anom_slope`, `B13 iso_grav_anom`, `B15 depth_to_base_surf`, `B02 rtp`, `B03 tmi_hg`, `B09 tmi_vg`, `B17 cond_surf`, `B04 geod_2ndinv`, `B07 geod_shearrate`, `B10 deq_n100a15`.
   - Public official external datasets (all `CC0` / US Gov Public Domain or `CC-BY-4.0`, verified obtainable without login):
     - USGS 3DEP 1 m LiDAR scarp stack (`ext_lidar_scarp_features_u8.tif`: `step_max`, `upface_max`, `downface_max`, `coh100`, `valid`),
     - US Census TIGER/Line road distance (`tiger_road_distance_m.tif`, `CC0`),
     - USGS GeoDAWN airborne radiometric & upward-continued aeromagnetic grids (`doi:10.5066/P93LGLVQ`, `CC0`: `K`, `Th`, `TMI_up150`),
     - OpenEI GDR `#1391` INGENIOUS paleo-geothermal sinter/tufa & 2 m temperature probe / thermal spring compilations (`doi:10.15121/1881483`, `CC-BY-4.0`).
2. **Physical Signature & Mathematical Transforms:**
   - **Line L1 — Asymmetric Scale-Normalized Piedmont-Scarp Break (`J_ASYM`)**:
     - Downslope unit vector $\hat{u}_{\text{down}} = -\nabla z_\sigma / (|\nabla z_\sigma| + \epsilon)$ and strike unit vector $\hat{t} = (-\hat{u}_x, \hat{u}_y)$ at $\sigma = 1.5\text{ px}$ ($150\text{ m}$).
     - Relative break-in-slope $J_{\text{rel}} = \max(0, -\nabla\ln(s_\sigma + s_0)\cdot \hat{u}_{\text{down}})$ ($s_0 = 2.0^\circ$) blended equally with raw $J_{\text{raw}} = \max(0, -\nabla s_\sigma \cdot \hat{u}_{\text{down}})$ over gentle-inclusive piedmont window $(0.8^\circ, 2.2^\circ, 16.0^\circ, 26.0^\circ)$, curing `H31-X`'s $8\times$ suppression of $2^\circ\text{–}5^\circ$ piedmont scarps.
     - **Step-vs-Thalweg Asymmetry Gate (`A_step`)**: Compare elevation & slope at upslope offset $-L\hat{u}_{\text{down}}$ vs downslope offset $+L\hat{u}_{\text{down}}$ ($L = 3\text{ px} = 300\text{ m}$). Require monotonic step drop $z(-L\hat{u}) > z(0) > z(+L\hat{u})$ and positive upslope-minus-downslope slope contrast $\text{clip}((s(-L\hat{u}) - s(+L\hat{u})) / (s(-L\hat{u}) + s(+L\hat{u}) + s_0), 0, 1)$, zeroing symmetric canyon floors / stream thalwegs where both banks rise.
     - **Along-Strike Axial Persistence**: Integrate along strike $\pm k\hat{t}$ ($k \in \{-3\dots+3\}\text{ px}$) to suppress arcuate talus cones and fan lobes while sharpening linear fault traces.
   - **Line L2 — Dip-Projected Hanging-Wall Subsurface Corroboration (`SUB_DIP`)**:
     - By Andersonian normal-fault mechanics ($\delta \approx 50^\circ\text{–}60^\circ$ basinward dip; Grauch & Hudson, 2007, *Geophysics*), a dipping normal fault with $0.6\text{–}1.6\text{ km}$ Cenozoic basin fill places its gravity horizontal-gradient peak $|\nabla_h g_{\text{iso}}|$ and basement-depth drop $|\nabla Z_{\text{base}}|$ **down-dip in the hanging wall** at $x + d\hat{u}_{\text{down}}$ ($d \in \{5, 10, 14\}\text{ px} = 500\text{–}1,400\text{ m}$ basinward), *not* on the surface trace pixel $d = 0$.
     - Sample $G_{\text{dip}}(x) = \max_{d \in \{0, 5, 10, 14\}} R_{\text{grav\_base}}(x + d\hat{u}_{\text{down}})$, turning subsurface physics into a true corroborator instead of a same-pixel killer (`IR-H31X-SAMEPIXEL-OFFSET`).
   - **Line L3 — Road-Vetoed Single-Facing 1 m 3DEP LiDAR Piedmont Scarplet (`LIDAR_SCARP`)**:
     - `step_max` $\times$ single-facing scarp polarity $|\text{upface\_max} - \text{downface\_max}| / (\text{upface\_max} + \text{downface\_max} + 1)$ $\times$ `coh100` across piedmont/fan slopes ($0.4^\circ \le s \le 12^\circ$), multiplied by US Census road-embankment veto $w_{\text{road}} = \text{clip}((d_{\text{road}} - 80\text{ m})/170\text{ m}, 0.10, 1.0)$.
   - **Line L4 — Blind Intrabasin Upward-Continued Magnetic Tilt-Zero + Hydrothermal Conduit (`BLIND_CONDUIT`)**:
     - Magnetic 3D tilt-angle zero-crossing sharpness $\exp(-|\arctan(\text{tmi\_vg}/(\text{tmi\_hg}+\epsilon))| / 0.35)$ weighted by upward-continued $|\nabla_h \text{TMI}_{\text{up150}}|$ persistence, corroborated by potassic/clay hydrothermal alteration (`K/Th` residual + elevation-debiased $|\nabla\text{cond\_surf}|$ + GDR `#1391` paleo-sinter/tufa/2m-probe corridor weight).
3. **Why It Catches Catalogue-Missing Faults:** Pre-2023 QFFD compilations missed (i) degraded piedmont junctions without fresh scarps (caught by `J_ASYM + SUB_DIP`), (ii) sub-meter Holocene alluvial-fan scarplets only resolved in 2020–2022 1 m GeoDAWN/3DEP LiDAR (`LIDAR_SCARP`), and (iii) buried intrabasin hydrothermal/magnetic basement faults (`BLIND_CONDUIT`).
4. **Named Non-Fault Mimics:** (a) Symmetric stream thalwegs / two-bank desert arroyos (`A_step` + 1m upface/downface polarity veto), (b) US/NV highway/railroad cut-and-fill berms (`tiger_road_distance_m` veto), (c) inactive erosional pediments & Lake Lahontan wave-cut shorelines (`SUB_DIP` down-dip gravity step), (d) flat saline playa clay pans (elevation-residualized $|\nabla\text{cond\_surf}|$).
5. **How It Differs From All Prior Implementations:** Zero use of `H19-5` or catalogue-distance power-law fields; cures `H31-X`'s canyon-floor mimic, `>6°` slope bias, and $d=0$ gravity-offset bug; adds road-vetoed 1 m LiDAR single-facing scarplets + blind GeoDAWN magnetic/hydrothermal conduits + OOF PU calibration + 300 m kernel submodular emission.

---

## 2. Pre-Registered 3-Experiment Budget & Automated Promotion Gates

### Experiments (Strictly `<= 3`)
1. **`EXP-1` (Unsupervised Multi-Regime Crest Concordance vs Single-Line & Null Controls):**
   Evaluate `H1_JASYM` (asymmetric scale-normalized piedmont scarp + down-dip gravity corroboration) and `H1_MULTI` (all 4 physical regimes `L1..L4` crest-thinned) against `CTRL` (isotropic topographic gradient ridge), `SLOPE` (`det_elev_slope`), and `REF_H31X_REPRO` (`H31-X` baseline formula) on `gems57-pooled-hide-v2` (`60,988` withheld positives).
2. **`EXP-2` (Fold-Local Observability-Debiased PU Out-of-Fold Crest Calibration):**
   Inside each `label-blind-quadrants-v2` fold (`buffer_px = 80`, fit strictly on visible non-buffered training quadrants), fit a monotonic L2-regularized Positive-Unlabeled (`SAR-PU` slope/lidar observability-reweighted) logistic model over the frozen `KANLER-H1` physical features on candidate crest pixels (`H1_PU_OOF`). Select between `EXP-1` best and `H1_PU_OOF` by paired `gems57-pooled-hide-v2` `HOLDOUT-DTI`.
3. **`EXP-3` (Exact 300 m Triangular-Kernel Submodular `CELF` Allocation vs Greedy `2.8 px` Poisson Disk + Random-Component Confirmation):**
   On the winning surface from `EXP-1`/`EXP-2`, compare exact 300 m triangular-kernel submodular (`CELF`) marginal-gain allocation (`H1_CELF`) against `2.8 px` greedy Poisson-disk thinning (`H1_POISSON`) at locked `37,654` dot budget (`d_vis > 2 px` inside holdout; `d_cat > 2 px` on full export), and verify on the untouched `50%` random-component confirmation split (`seed = 3103`, `29,965` withheld positives).

### Automated Validation & Promotion Gates (No Human Inspector)
- **`G1_FORMAT`:** `float32`, single band, `EPSG:32611`, `3730 x 3292`, exact transform `(100, 0, 243350, 0, -100, 4508550)`, zero `NaN`/`Inf` inside footprint (`all_finite` in `[0.0, 1.0]` for `-zeros.tif`; template-mask `NaN` outside for `-nan.tif`), zero positive mass on known `labels.tif` catalogue.
- **`G2_CANARY`:** Every single input feature/line tested alone on `gems57-pooled-hide-v2` has `max(AUC, 1 - AUC) <= 0.90`.
- **`G3_HOLDOUT_BEST`:** Candidate beats `CTRL`, `SLOPE`, **and** the cross-site `gems57-pooled-hide-v2` benchmark `H31-X` (`0.16613`) with paired 20 km spatial-block bootstrap `95% CI` lower bound `> 0`, AND confirms positive paired gain on the untouched `50%` random-component split (`seed = 3103`).
- **`G4_OFFCAT_DISCOVERY`:** Candidate beats `H33` (`0.0940`) on off-catalogue `USGS SGMC` (`d_cat > 300 m`, `61,664` pixels) AND specifically improves low-slope piedmont discovery (`slope <= 6°`) over `H31-X` (`0.0433`).
- **`G5_UNIQUENESS`:**
  - Pre-placement continuous surface: full-footprint `|Spearman| <= 0.90` (and crest `top-K` 3-px overlap `<= 0.70`) against all genuine detector submissions across all 9 focus sites (`GEMSDOE24..36`).
  - Final placed dots: `|Spearman| <= 0.90` AND directional within-3-px dot overlap `<= 0.70` against **all genuine detector submissions** across all 9 focus sites (`GEMSDOE24..36`, 360+ rasters).
  - Transparent disclosure of the synthetic space-filling `(5i, 5j)` calibration grid `13gems_r13-lattice-s5` (`99.871%` footprint coverage within 3 px, making literal `<= 70%` mathematically impossible for any raster with `>= 22,394` dots by Pigeonhole Principle) alongside null-calibrated excess overlap `(overlap - coverage)/(1 - coverage)`.
