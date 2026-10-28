"""Unit and artifact-integrity tests for lane L-K3-ATSC-SUBMOD."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import rasterio

from scripts.promotion_gate import assess
from src.kanlergems3.submodular import celf_submodular_emit_300m
from src.kanlergems3_atsc.features import (
    ATSC_GROUP_D_NAMES,
    ATSC_GROUP_E_NAMES,
    STAGE2_CORRIDOR_NAMES,
    STAGE2_TIP_NAMES,
    compute_stage2_corridor_features,
    compute_visible_tip_bridge_features,
)

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class TestATSCSubmodLane(unittest.TestCase):
    def test_preregistration_hash_locked(self) -> None:
        prereg = ROOT / "evidence/preregistration_atsc_20261027.json"
        self.assertTrue(prereg.is_file())
        self.assertEqual(
            _sha256(prereg),
            "e87228d624bcca28a5d6ec7475a10582a82d833c996644bbc8b5312b6e189201",
        )
        data = json.loads(prereg.read_text())
        self.assertEqual(len(data["ranked_hypotheses"]), 4)
        self.assertEqual(len(data["budget"]["planned_experiments"]), 3)

    def test_feature_schema_and_synthetic_operators(self) -> None:
        self.assertEqual(len(ATSC_GROUP_D_NAMES) + len(ATSC_GROUP_E_NAMES), 22)
        self.assertEqual(len(STAGE2_CORRIDOR_NAMES), 22)
        self.assertEqual(len(STAGE2_TIP_NAMES), 4)

        # Horizontal fault corridor should yield strong anisotropy ratio (>3.0) and bilateral continuity
        fp = np.ones((41, 41), dtype=bool)
        fp_idx = np.flatnonzero(fp)
        p1 = np.zeros((41, 41), dtype=np.float32)
        p1[20, 4:37] = 0.80
        n_fp = len(fp_idx)
        fc = {
            k: np.zeros(n_fp, dtype=np.float32)
            for k in (
                "has_lidar",
                "geod_transtension_index",
                "dip_grav_hg_p3",
                "depth_to_base_surf",
                "det_elev_slope",
                "topo10_relief_local",
                "flat_playa_indicator",
                "tiger_road_logdist",
                "piedmont_sweetspot_prior",
                "iso_grav_anom_hg",
                "tmi_up150_grad",
                "topo_gx",
                "topo_gy",
            )
        }
        fc["has_lidar"][:] = 1.0
        s2 = compute_stage2_corridor_features(
            p1, fp, fp_idx, np.zeros((1, 1), dtype=np.float32), {}, np.zeros((1, 1), dtype=np.float32), {}, fast_cols=fc
        )
        center_row = 20 * 41 + 20
        self.assertEqual(s2.shape, (n_fp, 22))
        self.assertGreater(float(s2[center_row, 1]), 0.75)  # s2_corr_max_1km
        self.assertGreater(float(s2[center_row, 3]), 0.75)  # s2_corr_bilateral_min_1km
        self.assertGreater(float(s2[center_row, 7]), 3.0)   # s2_anisotropy_ratio_1km

        # Visible tip features must return strictly zeros if visible mask is empty (leakage safety)
        empty_vis = np.zeros((41, 41), dtype=bool)
        ones = np.ones(n_fp, dtype=np.float32)
        tips = compute_visible_tip_bridge_features(empty_vis, fp, fp_idx, ones, ones)
        self.assertEqual(tips.shape, (n_fp, 4))
        self.assertEqual(float(np.abs(tips).max()), 0.0)

    def test_d285_blocks_diagonal_22_clumping_and_keeps_cardinal_30(self) -> None:
        surf = np.zeros((15, 15), dtype=np.float32)
        elig = np.zeros((15, 15), dtype=bool)
        elig[5, 5] = True
        elig[7, 7] = True  # dist from (5,5) = sqrt(8) = 2.828 < 2.85 -> must be blocked
        elig[2, 5] = True  # dist from (5,5) = 3.000 >= 2.85 (and 5.39 from (7,7)) -> must be selected
        surf[5, 5] = 1.0
        surf[7, 7] = 0.90
        surf[2, 5] = 0.70
        dots = celf_submodular_emit_300m(
            surf, elig, budget=2, active_mass_mask=np.ones((15, 15), dtype=bool), min_self_spacing_px=2.85
        )
        self.assertTrue(bool(dots[5, 5]))
        self.assertFalse(bool(dots[7, 7]))
        self.assertTrue(bool(dots[2, 5]))

    def test_leakage_canary_and_holdout_evidence(self) -> None:
        canary = json.loads((ROOT / "evidence/atsc_leakage_canary_20261027.json").read_text())
        self.assertEqual(canary["tested_features_count"], 103)
        self.assertFalse(canary["leakage_suspected"])
        self.assertLessEqual(canary["max_feature_auc"], 0.90)

        holdout = json.loads((ROOT / "evidence/atsc_holdout_20261027.json").read_text())
        self.assertEqual(holdout["selected_ablation_id"], "Exp-ATSC-2")
        p_sum = holdout["primary_screen"]["summaries"]
        self.assertGreater(p_sum["Exp-ATSC-2"]["dti"], holdout["primary_screen"]["recorded_cadg_exp_k3_3_dti"])
        self.assertGreater(p_sum["Exp-ATSC-1"]["dti"], holdout["primary_screen"]["recorded_cadg_exp_k3_3_dti"])
        self.assertTrue(holdout["primary_screen"]["paired_vs_b0_regional"]["ci95_strictly_positive"])

        d_sum = holdout["orthogonal_confirmation"]["summaries"]
        self.assertGreater(d_sum["Exp-ATSC-2"]["dti"], 0.147663)
        self.assertTrue(holdout["orthogonal_confirmation"]["paired_vs_b0_regional"]["ci95_strictly_positive"])

    def test_physical_laws_and_run_card_and_geotiffs(self) -> None:
        raw_ev = (ROOT / "evidence/atsc-submod-run-card.json").read_text()
        raw_doc = (ROOT / "docs/atsc-submod/run-card.json").read_text()
        self.assertEqual(raw_ev, raw_doc)
        card = json.loads(raw_ev)

        gate = assess(card)
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["slot_authorized"])
        self.assertEqual(gate["verdict"], "negative")
        self.assertFalse(gate["slot_authorized"])
        self.assertEqual(card["experiments_used"], 3)
        self.assertLess(card["elapsed_seconds"], 7200.0)
        self.assertLessEqual(len(card["submission_note"]), 140)

        laws = card["physical_laws"]
        self.assertGreaterEqual(laws["law1_far_field_gt_1p5km_frac"], 0.52)
        self.assertLessEqual(laws["law2_flat_deep_basin_spill_frac"], 0.043)
        self.assertLess(laws["law3_clump_ge3_300m_frac"], 0.02)

        ureg = card["uniqueness_registry_summary"]
        self.assertTrue(ureg["genuine_detectors_passed"])
        self.assertGreaterEqual(ureg["genuine_detector_rasters_checked"], 85)
        self.assertLessEqual(ureg["genuine_final_dot_overlap_3px"], 0.70)
        self.assertLessEqual(ureg["genuine_final_max_abs_spearman_rho"], 0.90)

        z_path = ROOT / card["submission_artifacts"]["primary_zeros_tif"]
        n_path = ROOT / card["submission_artifacts"]["official_nan_twin_tif"]
        self.assertTrue(z_path.is_file())
        self.assertTrue(n_path.is_file())
        self.assertEqual(_sha256(z_path), card["raster_sha256"])
        self.assertEqual(_sha256(n_path), card["submission_artifacts"]["official_nan_twin_sha256"])

        with rasterio.open(z_path) as zs, rasterio.open(n_path) as ns:
            self.assertEqual(zs.count, 1)
            self.assertEqual(zs.dtypes, ("float32",))
            self.assertEqual(str(zs.crs), "EPSG:32611")
            self.assertEqual(zs.shape, (3730, 3292))
            za = zs.read(1, masked=False)
            na = ns.read(1, masked=False)
            self.assertTrue(np.isfinite(za).all())
            self.assertTrue(((za >= 0.0) & (za <= 1.0)).all())
            self.assertEqual(int((za > 0.0).sum()), 37_654)
            self.assertEqual(int(np.isnan(na).sum()), 7_111_787)
            self.assertTrue(np.array_equal(za > 0.0, np.isfinite(na) & (na > 0.0)))

    def test_subportal_pages_and_root_links(self) -> None:
        card = json.loads((ROOT / "evidence/atsc-submod-run-card.json").read_text())
        for name in ("index.html", "executive-summary.html", "hypotheses.html"):
            p = ROOT / "docs/atsc-submod" / name
            self.assertTrue(p.is_file(), name)
            txt = p.read_text()
            self.assertNotIn("ORGANIZER-CONFIRMED: 0.", txt)
        idx = (ROOT / "docs/atsc-submod/index.html").read_text()
        sub = (ROOT / "docs/atsc-submod/executive-summary.html").read_text()
        self.assertIn(card["raster_sha256"], idx)
        self.assertIn(card["submission_note"], sub)
        self.assertIn("atsc-submod/index.html", (ROOT / "docs/source-status.js").read_text())
        self.assertIn("atsc-submod/index.html", (ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
