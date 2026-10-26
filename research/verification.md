# Three-Pass Verification Record — 2026-10-26 (Lane `L-K3-CADG-SUBMOD`)

## Official Primary Sources Fetched & Verified (`2026-10-26 UTC`)

1. **DrivenData Live Public Leaderboard (`#306`):** <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> — verified live DW-Tversky leaderboard: `#1 xiaofanhu = 0.4437` (`31` submissions), `#2 cfld__ = 0.3916` (`18`), `#3 Batik Shirt Brothers = 0.3904` (`53`), `#4 BrandenKMurray = 0.3724` (`32`), `#5 No Fault of Our Own = 0.3561` (`44`). Resolves stale/conflicting `0.4413` and `0.3195` numbers in earlier notes.
2. **DOE / NLR Official GEMS Prize Rules (September 2026):** <https://docs.nlr.gov/docs/fy26osti/96647.pdf> — verified `$300,000` total purse (`$50k` Phase 1 + `$250k` Phase 2), **maximum `3` submissions per week**, **one** final submission evaluated across both Phase 1 and Phase 2, reproducible code requirement for finalists, and generative-AI disclosure rule.
3. **DrivenData Task, Metric & GeoTIFF Specification:** <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> — verified `DTI(alpha=0.2, beta=0.8)` with `300 m` (`3 px`) triangular kernel, `EPSG:32611`, `100 m` grid, single-band `float32` in `[0, 1]`.
4. **DrivenData Staff Catalogue-Masking Confirmation (`chrisk-dd`, Sep 16):** <https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516> — verified known USGS/INGENIOUS catalogue pixels are masked/excluded from evaluation in both Phase 1 and Final Round.
5. **DOE GDR #1391 & GBCGE INGENIOUS Data Releases:** <https://gdr.openei.org/submissions/1391> (`DOI: 10.15121/1881483`, CC-BY-4.0) and <https://gbcge.org/current-projects/ingenious/> — verified USGS/GBCGE DOIs `10.5066/P9TWT2LU` (MT conductance), `10.5066/P9MQRCBY` (detrended elevation), `10.5066/P9Z6SA1Z` (gravity/magnetics), `10.5066/P9BZPVUC` (heat flow), `10.5066/P93LGLVQ` (USGS GeoDAWN, CC0), and `10.1785/0220220153` (Kreemer et al. geodetic strain).

---

## Pass 1 — End-to-End Implementation, Data Restoration & Preregistered Execution

- Vendored and SHA-256-verified canonical shared template `vendor/gems24_template/` (`GEMSDOE24@fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1`) and centralized `evaluate_holdout.py` + `submission_writer.py`.
- Restored and SHA-256-verified all core rasters, external geoscience layers, and `36` registry rasters (`registry/uniqueness_registry_20261026.json`, `SHA-256: 3da610db...`) into gitignored `.cache/gems_data/`.
- Re-ran `scripts/audit_rasters.py` across the 9 focus sites (`GEMSDOE24/25/27/28/30/31/32/33/36`), verifying all 9 SHA-256 hashes and all 72 directed `3-px` overlaps (minimum `86.718954% > 70%`).
- Locked frozen preregistration `evidence/preregistration_20261026.json` (`SHA-256: e49c6aae3afafdcb60306ac79ff439d48fdfde2342b4fb9c0ba611fb23f54278`) for lane `L-K3-CADG-SUBMOD` and hypotheses `H-K3-1`..`H-K3-4`.
- Built label-free 77-feature memmap `.cache/gems_work/features_fp_v1.f32` (`5,167,373` footprint cells, digest `da968c3cd1a170e4`), verified `80/80` two-polarity leakage canaries (`max AUC = 0.6296 <= 0.90`), and executed all `3` preregistered experiments on `SegmentHoldout(buffer_px=15)` plus orthogonal `DiagonalSegmentHoldout(buffer_px=20)`.

---

## Pass 2 — Adversarial Bug Hunt, Irregularities Flagged & Fixed

1. **`IR-33-LIDAR-VOID-01` (LiDAR Coverage Void & Swath-Seam Step Artifacts):**
   `lidar_scarp_features_u8.tif` encodes uncovered tiles (`36.9%` of footprint) with band-7 `valid == 0` and creates artificial linear steps along tile borders. Fixed in `src/kanlergems3/features.py` by eroding `valid > 0` inward by `2 px` (`200 m`), setting void cells to `NaN`, and training a dedicated LiDAR-void 10 m/subsurface specialist blended on `!has_lidar`.
2. **`IR-34-NODATA-01` (`"Predicted values must be in range [0, 1]"` Portal Trap):**
   Whole-array portal range checks fail if `NaN` or negative sentinel nodata (`-9999.0`) is evaluated before masking. Fixed via `submission_writer.py` + `scripts/validate_submission.py`: primary `-zeros.tif` stores finite `0.0` outside the footprint (`nodata=None`), guaranteeing all `12,279,160` cells are finite `{0.0, 1.0}`, while also emitting the strict official-text `-nan.tif` twin (`validate(...) -> ok: True`).
3. **`IR-K3-HISTORICAL-LEAK-01` (Contaminated Static `H19-5` / `D2.8` Holdout Diagnostics):**
   Audited `19GEMSDOE` source scripts and proved static `H19-5` (`121,131` dots) and `D2.8` (`44,090` dots) were trained on unbuffered quadrant splits (retaining cross-boundary halves of withheld faults) and post-masked on full `labels.tif == 0` across all 4 quadrants (`6,436` dots at `1 <= d_truth <= 2 px`). Separated them cleanly from leak-free `37,654`-dot `SegmentHoldout` baselines (`B0_regional_d28 = 0.102267`, `unsupervised_D28_37654 = 0.064020`).
4. **`IR-K3-INSAMPLE-COLLAR-01` (In-Sample Refit Collar Collapse Fixed via 8-Fold Spatial OOF):**
   In Pass 1, fitting a full-footprint in-sample tree for deployment memorized leaf splits around `labels.tif`, packing `60.6%` (`22,812` dots) into `2 < d_catalogue <= 5 px` (`d_cat > 10 px = 9.7%`) and inflating overlap with dense archive halo maps (`0.7863`). Replacing in-sample refitting with **stitched 8-fold spatial out-of-fold cross-fitting** (`0.5 * quadrant OOF + 0.5 * diagonal-wedge OOF`) shifted **`62.9%` (`23,684` dots) to `d_catalogue > 10 px`**, boosted blind-piedmont `C_pied` to `0.1124`, and reduced max 3-px overlap across **all `35` genuine detector rasters to `0.5711 <= 0.70`** (`PASS`).
5. **`IR-42-UNIQ-01` (Un-Weakened `r13-lattice-s5` Pigeonhole Obstruction):**
   `13GEMSDOE` `r13-lattice-s5` (`206,895` uniform spacing-5 grid dots) covers `5,160,724 / 5,167,373` footprint cells (`99.8713%`) within `3 px`, forcing `>= 82.34%` overlap for any `37,654`-dot raster. Per `research/review.md` (*"report that conflict rather than weakening the gate"*), top-level `run-card.json` retains the un-weakened literal overlap (`0.9975`) and `template_provenance_verified = false`, keeping `promotion_gate.py` at `verdict = "negative"` (`slot_authorized = false`) while reporting `genuine_35_detectors_passed = true` (`0.5711 <= 0.70`) for human selector review.

---

## Pass 3 — Full Prompt Audit, CI Workflow Parity & Test Suite Verification

- Synchronized `run-card.json`, `docs/run-card.json`, `docs/data/run_card.json`, `docs/index.html`, `docs/executive-summary.html`, `docs/EXECUTIVE_SUMMARY.md`, and `README.md` via `scripts/review.py` and `scripts/build_site.py`.
- Verified SHA-256 integrity of `evidence/snapshot_hashes.json` (`test_evidence_hashes`), frozen preregistration `evidence/preregistration_20261026.json`, saved GeoTIFFs (`--verify-only`), ZIP archives, and GitHub Actions CI command `python scripts/review.py && python scripts/build_site.py && git diff --exit-code`.
- Executed full automated `unittest` suite (`tests/test_audit.py`, `tests/test_review.py`, `tests/test_kanlergems3.py`) with `0` failures and `0` human-inspector steps.
