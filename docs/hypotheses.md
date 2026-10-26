# Five Untried Geological Hypotheses & `KANLER-H1` Experimental Report (`2026-10-26`)

Full pre-registration (frozen prior to data restoration and holdout evaluation) is archived in [`research/preregistration_kanler_h1.md`](preregistration_kanler_h1.md). Below is the complete specification of all five untried geological hypotheses, their expected DTI / implementation-cost ranking, official external data verification, and the complete 3-experiment outcome for Rank #1 (`KANLER-H1: DCAP-LHC`).

---

## 1. Ranked Candidate Hypotheses

| Rank | ID | Hypothesis | Specific Layers | Physical Transform & Missing-Fault Mechanism | Non-Fault Mimic & Veto | Expected Gain & Cost |
|---:|---|---|---|---|---|---|
| **1** | **`KANLER-H1`** | **Dip-Coupled Asymmetric Piedmont-Scarp, Road-Vetoed 1m LiDAR & Hydrothermal-Magnetic Conduit (`DCAP-LHC`)** | `B12 det_elev`, `B19 det_elev_slope`, `B05 iso_grav_anom_slope`, `B15 depth_to_base_surf`, `B03 tmi_hg`, `B09 tmi_vg`, `B17 cond_surf`, `B04/B07/B10` strain/EQ, 3DEP 1m `step_max/upface/downface/coh100`, GeoDAWN `K/Th/TMI_up150`, GDR `#1391` paleo/2m probes, Census `tiger_road_distance_m` | **(L1)** Scale-normalized concave-up break $-\nabla\ln(s+2^\circ)\cdot\hat{u}_{\text{down}}$ integrated 600 m along strike; **(L2)** Andersonian $50^\circ\text{–}60^\circ$ normal-fault hanging-wall projection $\max_{d\in\{0,5,10,14\}\text{ px}} R_{\text{grav,base}}(x+d\hat{u}_{\text{down}})$; **(L3)** single-facing 1m LiDAR scarplets; **(L4)** upward-continued magnetic tilt-zero $\exp(-|\theta_{\text{tilt}}|/0.35)$ + `K/Th` + playa-debiased $|\nabla\text{cond}|$ + sinter/2m-probe corridor. Catches weathered piedmont fronts, `<1.5 m` Holocene fan scarps, and buried hydrothermal conduits. | Canyon thalwegs & 2-bank washes (`upface/downface` polarity + step asymmetry); US/NV highways/railroads (`tiger_road_distance_m`); inactive pediments (`SUB_DIP` down-dip gravity); flat playas (slope-debiased `cond_surf`). | **Rank #1** — High multi-regime complementarity, Low–Med CPU (~4.5 min). **Executed in this session.** |
| 2 | `KANLER-H2` | Upward-Continued Magnetic Euler-Tilt & Magnetite-Destruction Trough (`ETD-MDT`) | `B02 rtp`, `B03 tmi_hg`, `B09 tmi_vg`, `B14 tmi`, GeoDAWN `TMI_up150`, `K`, `Th`, `U`, `B05` | Structural Index $N=0.5$ contact depth consistency (`0 m` vs `+150 m` upward continuation) paired with cross-strike $\partial_{nn}\text{RTP} > 0$ magnetite-leaching trough + `K/Th` adularia-sericite enrichment along blind hydrothermal fault damage zones. | Mafic volcanic flow margins (`derived_gdr_volcanics`) and circular pluton aureoles (closed-ring curvature veto). | **Rank #2** — Strong blind-basin precision, moderate whole-survey recall; core physics integrated into `H1` Line 4. Low cost. |
| 3 | `KANLER-H3` | Multi-Catchment Wineglass-Facet & Knickpoint Alignment (`WF-KPA`) | `B12 det_elev`, `B19 det_elev_slope`, 1m LiDAR `relief`, `ex_max`, `cross_max` | Colinear alignment across adjacent catchments of truncated planar interfluve triangular facets + incised channel-mouth longitudinal knickpoints ($-\partial_{ss}z > 0$) over 3 km strike windows. Catches pre-Holocene range fronts buried at the toe by young fan aggradation (`Qfy`). | Resistant dipping tuff hogbacks/cuestas and ~1,330 m Lake Lahontan wave-cut cliffs (constant-contour elevation veto). | **Rank #3** — High range-front recall, zero basin sensitivity; Medium compute cost. |
| 4 | `KANLER-H4` | Transtensional Riedel-Relay Azimuthal Steered Detector (`RCSD-BRIDGE`) | `B04 geod_2ndinv`, `B07 geod_shearrate`, `B08 geod_dilaterate`, `B10/B16` seismicity, `B05`, `B12` | Steers 100 m anisotropic Steger ridge filters specifically along local Coulomb R-shear ($\psi \pm 15^\circ$) and normal-relay ($\psi \pm 45^\circ$) azimuths derived from $\frac{1}{2}\arctan(\dot{\gamma}/\dot{\Delta})$ in elevated swarm seismicity (`ieq - deq`) zones. Catches short oblique Walker Lane stepover splays. | 10–25 km GPS/seismic interpolation kernels (used strictly as azimuth prior, never raw amplitude). | **Rank #4** — Moderate gain in Walker Lane, Low cost. |
| 5 | `KANLER-H5` | Upslope-Backprojected Sinter/Tufa & 2m Thermal Feeder Inversion (`PHT-SPI`) | GDR `#1391` `paleo_geothermal_regional`, `2m_temperature_probe`, `B17 cond_surf`, GeoDAWN `U/Th`, `B05` | Back-projects shallow thermal/outflow anomalies upslope (`+\nabla z`) against lateral groundwater flow to the nearest potential-field feeder contact. Directly targets blind geothermal upflow conduits (~39% of Great Basin systems; Faulds et al., 2021). | Lateral stratabound warm outflow plumes in permeable Quaternary gravel channels. | **Rank #5** — High district precision, sparse (`<5%` footprint) standalone coverage; Low cost. |

---

## 2. Official Free External Data Verification

All external datasets used in `KANLER-H1` are free, publicly licensed US Government (`CC0` / Public Domain) or DOE OpenEI (`CC-BY-4.0`) releases verified live on `2026-10-26` and SHA-256-pinned on the exact `EPSG:32611` `3730 × 3292` 100 m grid:

1. **USGS 3DEP 1 m Digital Elevation Model (`lidar_scarp_features_u8.tif`, SHA `d580bb8b...`):** Public Domain (`https://www.usgs.gov/3d-elevation-program`, 706 tiles covering `75.37%` of footprint; explicitly referenced in DOE GEMS Official Rules `96647.pdf` Sec. 1.2).
2. **USGS GeoDAWN Airborne Magnetic & Radiometric Survey (`geodawn_rad_u8.tif` SHA `c22420f7...`, `geodawn_extensions_u8.tif` SHA `a35a9c6d...`):** `CC0` Public Domain (`doi:10.5066/P93LGLVQ`, `https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and`).
3. **DOE / GBCGE INGENIOUS Regional Dataset (`derived_gdr_2m_probes_100m_u8.tif` SHA `7ac3cfdf...`, `derived_gdr_paleo_100m_u8.tif` SHA `d6a3609b...`):** `CC-BY-4.0` (`doi:10.15121/1881483`, `https://gdr.openei.org/submissions/1391` — zero label-distance columns used).
4. **US Census Bureau TIGER/Line 2024 Roads (`tiger_road_distance_m.tif`, SHA `e5350423...`):** US Government Public Domain (`https://www2.census.gov/geo/tiger/TIGER2024/ROADS/`).
5. **USGS State Geologic Map Compilation (`derived_sgmc_faults_100m_u8.tif`, SHA `26d142c4...`):** US Government Public Domain (`https://mrdata.usgs.gov/geology/state/`), used **strictly as an off-catalogue evaluation diagnostic (`d_cat > 300 m`, `61,664` pixels)** and **never** as a model feature.

---

## 3. Complete `KANLER-H1` 3-Experiment Results (`gems57-pooled-hide-v2`)

### 3.1 Single-Feature Leakage Canary (`Protocol Rule 4` — Ceiling `AUC <= 0.90`)
All 10 individual lines and composite surfaces passed (`all_pass = true` in `evidence/kanler_h1/canary.json`):
- `J_ASYM`: `AUC_cat = 0.6366`, `AUC_sgmc = 0.5816`
- `SUB_DIP`: `AUC_cat = 0.5429`, `AUC_sgmc = 0.4105`
- `LIDAR_SCARP`: `AUC_cat = 0.5897`, `AUC_sgmc = 0.4514`
- `BLIND_CONDUIT`: `AUC_cat = 0.5207`, `AUC_sgmc = 0.4773`
- `TECT_CTX`: `AUC_cat = 0.5685`, `AUC_sgmc = 0.4804`
- `H1_JASYM`: `AUC_cat = 0.6415`, `AUC_sgmc = 0.5687`
- `H1_MULTI`: `AUC_cat = 0.6528`, `AUC_sgmc = 0.5037`
- Controls `CTRL` (`0.5261`), `SLOPE` (`0.5582` cat / `0.7577` SGMC), `REF_H31X` (`0.6423`).

### 3.2 Holdout Experiments (`EXP-1`, `EXP-2`, `EXP-3`, `withheld_positives = 60,988`, `buffer_px = 80`)

| Experiment / Arm | Emitter | Q0 (`29,319`) | Q1 (`12,596`) | Q2 (`9,473`) | Q3 (`9,600`) | Pooled `HOLDOUT-DTI` (`95% CI`) | Confirm `seed=3103` ($N=29,965$) |
|---|---|---:|---:|---:|---:|---|---|
| **`EXP-1: H1_MULTI` (Winner)** | `2.8 px` Poisson | `0.1210` | `0.0707` | `0.1520` | **`0.1726`** | **`0.1253` `[0.1080, 0.1414]`** | **`0.1107` `[0.0929, 0.1274]`** |
| `EXP-1: H1_JASYM` | `2.8 px` Poisson | `0.1139` | `0.1480` | `0.0989` | `0.1420` | `0.1242` `[0.1095, 0.1391]` | — |
| `EXP-2: H1_PU_OOF` (`SAR-PU` OOF) | `2.8 px` Poisson | `0.1188` | `0.0327` | `0.1437` | `0.1698` | `0.1159` `[0.0958, 0.1345]` | — |
| `EXP-3: H1_MULTI_CELF` (300 m Submod) | `300 m` `CELF` | `0.1191` | `0.0743` | `0.1498` | `0.1465` | `0.1211` `[0.1045, 0.1369]` | — |
| `REF_H31X` (Portfolio Holdout Best) | `2.8 px` Poisson | `0.1456` | `0.2212` | `0.1680` | `0.1602` | **`0.1674` `[0.1518, 0.1840]`** | **`0.1476` `[0.1289, 0.1654]`** |
| `CTRL` (`|tmi_hg|` ridge) | `2.8 px` Poisson | `0.0910` | `0.0149` | `0.0859` | `0.0323` | `0.0671` `[0.0501, 0.0846]` | `0.0656` `[0.0493, 0.0827]` |
| `SLOPE` (`det_elev_slope`) | `2.8 px` Poisson | `0.0396` | `0.0596` | `0.0579` | `0.0512` | `0.0486` `[0.0408, 0.0565]` | `0.0478` `[0.0385, 0.0574]` |

### 3.3 Key Post-Run Scientific Diagnosis (Why `verdict = negative` Is Preserved Without Retuning)
1. **Genuine Walker Lane & Piedmont Breakthrough:** Where 1 m LiDAR is present (`92.9%` in Q3), `H1_MULTI` **beat `REF_H31X` (`0.1726 vs 0.1602`)**, and across the entire survey `H1_MULTI` boosted low-slope piedmont (`<= 6°`) off-catalogue `SGMC` discovery **`+28.1%` over `REF_H31X` (`0.0569 vs 0.0444`)** while maintaining **`<= 58.47%`** 3-px dot overlap with every single detector raster in the 417-raster registry (`39.74%` vs `GEMSDOE32` `0.2778`).
2. **Exact Cause of Quadrant-1 Deficit:** `47.4%` of Quadrant 1 has `lidar_valid == 0`, starving Q1 of dots (`3,296` vs `9,823`) when `r_lidar` enters an un-normalized global sum; additionally, `Band 12 det_elev` has negative high-pass troughs at steep range-front toes. Per Protocol Rules 5 & 6 (`budget = 3` experiments, zero post-holdout retuning), we preserve the honest `verdict: "negative"` receipt and document the exact 2-line sensor-availability quantile fix for `KANLER-H1.1`.
