from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from kanlergems3.submodular import celf_submodular_emit_300m, greedy_spacing_emit  # noqa: E402
import promotion_gate  # noqa: E402
from cadg_validate_submission import audit, validate  # noqa: E402


def _write_synthetic_tif(
    path: Path,
    arr: np.ndarray,
    *,
    crs: str = "EPSG:32611",
    transform=None,
    nodata=None,
    bands: int = 1,
) -> None:
    if transform is None:
        transform = from_origin(243350.0, 4508550.0, 100.0, 100.0)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=bands,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dst:
        for b in range(1, bands + 1):
            dst.write(arr.astype(np.float32), b)


class KanlerGems3Tests(unittest.TestCase):
    def test_submodular_celf_invariants_and_objective(self) -> None:
        rng = np.random.default_rng(20261026)
        surf = rng.uniform(0.01, 0.20, size=(48, 48)).astype(np.float32)
        surf[12, 8:40] = 0.92
        surf[13, 8:40] = 0.89
        surf[32, 6:42] = 0.85
        elig = np.ones_like(surf, dtype=bool)
        elig[:3, :] = False

        dots_celf = celf_submodular_emit_300m(
            surf, elig, 18, active_mass_mask=elig, min_self_spacing_px=2.5
        )
        dots_greedy = greedy_spacing_emit(surf, elig, 18, min_spacing_px=2.5)

        self.assertEqual(int(dots_celf.sum()), 18)
        self.assertTrue(np.all(elig[dots_celf]))

        rr, cc = np.nonzero(dots_celf)
        for i in range(len(rr)):
            d2 = (rr[i + 1 :] - rr[i]) ** 2 + (cc[i + 1 :] - cc[i]) ** 2
            if d2.size:
                self.assertTrue(np.all(np.sqrt(d2) > 2.5 - 1e-6))

        dt_celf = distance_transform_edt(~dots_celf)
        dt_greedy = distance_transform_edt(~dots_greedy)
        cov_celf = float((surf[elig] * np.maximum(0.0, 1.0 - dt_celf[elig] / 3.0)).sum())
        cov_greedy = float((surf[elig] * np.maximum(0.0, 1.0 - dt_greedy[elig] / 3.0)).sum())
        self.assertGreaterEqual(cov_celf, cov_greedy - 1e-5)

    def test_validator_rejects_range_nan_and_schema_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            tpl = tdir / "template.tif"
            tpl_arr = np.full((16, 16), np.nan, dtype=np.float32)
            tpl_arr[2:14, 2:14] = 0.0
            _write_synthetic_tif(tpl, tpl_arr, nodata=np.nan)

            good_zeros = tdir / "good_zeros.tif"
            gz = np.zeros((16, 16), dtype=np.float32)
            gz[5, 5] = 1.0
            _write_synthetic_tif(good_zeros, gz, nodata=None)
            res_good = validate(tpl, good_zeros, allow_zero_outside=True)
            self.assertTrue(res_good["ok"])
            self.assertTrue(res_good["whole_array_all_finite_0_1"])

            bad_neg = tdir / "bad_neg.tif"
            bn = gz.copy()
            bn[6, 6] = -0.01
            _write_synthetic_tif(bad_neg, bn, nodata=None)
            self.assertFalse(validate(tpl, bad_neg, allow_zero_outside=True)["ok"])
            self.assertFalse(validate(tpl, bad_neg)["ok"])

            bad_over = tdir / "bad_over.tif"
            bo = gz.copy()
            bo[6, 7] = 1.01
            _write_synthetic_tif(bad_over, bo, nodata=None)
            self.assertFalse(validate(tpl, bad_over, allow_zero_outside=True)["ok"])

            bad_sentinel = tdir / "bad_sentinel.tif"
            bs = np.where(np.isfinite(tpl_arr), gz, -9999.0).astype(np.float32)
            _write_synthetic_tif(bad_sentinel, bs, nodata=-9999.0)
            self.assertFalse(validate(tpl, bad_sentinel, allow_zero_outside=True)["whole_array_all_finite_0_1"])
            _write_synthetic_tif(bad_sentinel, bs, nodata=None)
            self.assertFalse(validate(tpl, bad_sentinel, allow_zero_outside=True)["ok"])

            bad_nan_in = tdir / "bad_nan_in.tif"
            bni = np.where(np.isfinite(tpl_arr), gz, np.nan).astype(np.float32)
            bni[4, 4] = np.nan
            _write_synthetic_tif(bad_nan_in, bni, nodata=np.nan)
            self.assertFalse(validate(tpl, bad_nan_in, allow_zero_outside=False)["ok"])

            bad_crs = tdir / "bad_crs.tif"
            _write_synthetic_tif(bad_crs, gz, crs="EPSG:4326")
            self.assertFalse(validate(tpl, bad_crs, allow_zero_outside=True)["ok"])

            bad_bands = tdir / "bad_bands.tif"
            _write_synthetic_tif(bad_bands, gz, bands=2)
            self.assertFalse(validate(tpl, bad_bands, allow_zero_outside=True)["ok"])

    def test_emitted_candidate_artifacts_and_run_card_integrity(self) -> None:
        raw_ev = (ROOT / "evidence/cadg-submod-run-card.json").read_text()
        raw_doc = (ROOT / "docs/cadg-submod/run-card.json").read_text()
        self.assertEqual(raw_ev, raw_doc)
        for bad in ("NaN", "Infinity", "-Infinity"):
            self.assertNotIn(bad, raw_ev)
        card = json.loads(raw_ev)

        prereg_sha = hashlib.sha256((ROOT / "evidence/preregistration_20261026.json").read_bytes()).hexdigest()
        self.assertEqual(prereg_sha, "e49c6aae3afafdcb60306ac79ff439d48fdfde2342b4fb9c0ba611fb23f54278")

        gate = promotion_gate.assess(card)
        self.assertEqual(gate["verdict"], card["verdict"])
        self.assertFalse(gate["slot_authorized"])
        self.assertEqual(
            gate["failures"],
            [
                "template_provenance_verified",
                "outside_encoding_contract_verified",
                "surface_dot_overlap_3px",
                "final_dot_overlap_3px",
            ],
        )
        self.assertEqual(card["live_submission_slots_used"], 0)
        self.assertLessEqual(card["experiments_used"], 3)
        self.assertLessEqual(card["max_feature_auc"], 0.90)
        self.assertTrue(0 < len(card["submission_note"]) <= 140)
        self.assertTrue(card["uniqueness_registry_summary"]["genuine_35_detectors_passed"])
        self.assertLessEqual(card["uniqueness_registry_summary"]["genuine_35_final_dot_overlap_3px"], 0.70)
        self.assertLessEqual(card["uniqueness_registry_summary"]["genuine_35_surface_max_abs_spearman_rho"], 0.90)

        art = card["submission_artifacts"]
        z_tif = ROOT / art["primary_zeros_tif"]
        z_zip = ROOT / art["primary_zeros_zip"]
        n_tif = ROOT / art["official_nan_twin_tif"]
        n_zip = ROOT / art["official_nan_twin_zip"]
        for p in (z_tif, z_zip, n_tif, n_zip, ROOT / art["note_file"], ROOT / art["receipt_file"]):
            self.assertTrue(p.is_file(), f"Missing artifact: {p}")

        z_sha = hashlib.sha256(z_tif.read_bytes()).hexdigest()
        self.assertEqual(z_sha, card["raster_sha256"])

        with zipfile.ZipFile(z_zip) as zf:
            names = zf.namelist()
            self.assertEqual(names, [z_tif.name])
            self.assertEqual(hashlib.sha256(zf.read(z_tif.name)).hexdigest(), z_sha)

        local_tpl = ROOT / ".cache/gems_data/sample_submission.tif"
        ref_tpl = local_tpl if local_tpl.is_file() else n_tif
        aud_z = audit(z_tif, ref_tpl, strict_zero_outside=True)
        aud_n = audit(n_tif, ref_tpl, strict_zero_outside=False)
        val_n = validate(n_tif, ref_tpl)
        self.assertTrue(aud_z["pass"])
        self.assertTrue(aud_z["whole_array_all_finite_0_1"])
        self.assertEqual(aud_z["in_footprint_positive_pixels"], 37_654)
        self.assertTrue(aud_n["pass"])
        self.assertTrue(val_n["ok"])

        with rasterio.open(z_tif) as sz, rasterio.open(n_tif) as sn:
            az = sz.read(1, masked=False)
            an = sn.read(1, masked=False)
        fp = np.isfinite(an)
        self.assertEqual(int(fp.sum()), 5_167_373)
        self.assertTrue(np.array_equal(az[fp], an[fp]))
        self.assertTrue(np.all((az == 0.0) | (az == 1.0)))

        local_cat = ROOT / ".cache/gems_data/labels.tif"
        if local_cat.is_file():
            with rasterio.open(local_cat) as sc:
                cat = (sc.read(1, masked=False) > 0) & fp
            self.assertEqual(int(((az > 0.0) & cat).sum()), 0)

    def test_cross_lane_uniqueness_against_parallel_lanes(self) -> None:
        cross = json.loads((ROOT / "evidence/kanlergems3_cross_lane_audit_20261026.json").read_text())
        self.assertTrue(cross["all_parallel_lanes_passed"])
        self.assertEqual(len(cross["comparisons"]), 4)
        for row in cross["comparisons"]:
            self.assertLessEqual(row["final_3px_overlap"], 0.70)
            self.assertLessEqual(row["final_abs_spearman_rho"], 0.90)

    def test_archived_candidate_pages_fail_closed_and_offer_no_download(self) -> None:
        from scripts.build_cadg_site import build
        build(check_only=True)
        idx = (ROOT / "docs/cadg-submod/index.html").read_text()
        sub = (ROOT / "docs/cadg-submod/executive-summary.html").read_text()
        js = (ROOT / "docs/source-status.js").read_text()
        readme = (ROOT / "README.md").read_text()
        lane_readme = (ROOT / "docs/cadg-submod/README.md").read_text()
        card = json.loads((ROOT / "evidence/cadg-submod-run-card.json").read_text())
        self.assertIn(card["raster_sha256"], idx)
        self.assertIn(card["submission_name"], idx)
        self.assertIn("DO NOT SUBMIT", idx)
        self.assertIn("exceeding the 70% stop", idx)
        self.assertIn("99.94%", idx)
        self.assertIn("cannot override", idx)
        self.assertNotIn("download=", idx.lower())
        self.assertNotIn("download=", sub.lower())
        self.assertNotIn('href="downloads/', idx.lower())
        self.assertNotIn('href="downloads/', sub.lower())
        self.assertNotIn("DOWNLOAD READY", idx)
        self.assertIn("DO NOT SUBMIT", lane_readme)
        self.assertNotIn("](docs/downloads/", lane_readme)
        self.assertIn("cadg-submod/index.html", js)
        self.assertIn("cadg-submod/index.html", readme)


if __name__ == "__main__":
    unittest.main()
