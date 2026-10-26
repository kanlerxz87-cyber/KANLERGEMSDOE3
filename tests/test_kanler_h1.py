import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from scripts.promotion_gate import assess
from scripts.validate_submission import validate as validate_tif

ROOT = Path(__file__).resolve().parents[1]


class KanlerH1DeliverableTests(unittest.TestCase):
    def test_run_card_and_promotion_gate_consistent(self):
        card_docs = json.loads((ROOT / "docs/run-card.json").read_text())
        card_root = json.loads((ROOT / "run-card.json").read_text())
        self.assertEqual(card_docs, card_root)

        gate = assess(card_docs)
        self.assertEqual(gate["verdict"], card_docs["verdict"])
        self.assertEqual(gate["verdict"], "negative")
        self.assertFalse(gate["slot_authorized"])

        # Protocol budget & canary checks
        self.assertLessEqual(card_docs["experiments_run"], 3)
        self.assertLessEqual(card_docs["max_feature_auc"], 0.90)
        self.assertLessEqual(card_docs["surface_max_rank_correlation"], 0.90)
        self.assertLessEqual(card_docs["final_max_rank_correlation"], 0.90)
        self.assertLessEqual(card_docs["final_dot_overlap_3px"], 0.70)

    def test_on_disk_zeros_and_nan_geotiffs_and_zips(self):
        card = json.loads((ROOT / "docs/run-card.json").read_text())
        z_tif = ROOT / card["deliverable_files"]["primary_zeros_tif"]
        z_zip = ROOT / card["deliverable_files"]["primary_zeros_zip"]
        n_tif = ROOT / card["deliverable_files"]["companion_nan_tif"]
        n_zip = ROOT / card["deliverable_files"]["companion_nan_zip"]

        for p in (z_tif, z_zip, n_tif, n_zip):
            self.assertTrue(p.is_file(), f"Missing deliverable: {p}")

        self.assertEqual(hashlib.sha256(z_tif.read_bytes()).hexdigest(), card["raster_sha256"])
        self.assertEqual(hashlib.sha256(n_tif.read_bytes()).hexdigest(), card["companion_nan_raster_sha256"])

        with rasterio.open(z_tif) as dz, rasterio.open(n_tif) as dn:
            self.assertEqual(dz.count, 1)
            self.assertEqual(dn.count, 1)
            self.assertEqual(dz.dtypes, ("float32",))
            self.assertEqual(dn.dtypes, ("float32",))
            self.assertEqual(dz.shape, (3730, 3292))
            self.assertEqual(dn.shape, (3730, 3292))
            self.assertEqual(dz.crs.to_epsg(), 32611)
            self.assertEqual(dn.crs.to_epsg(), 32611)
            self.assertEqual(tuple(dz.transform)[:6], (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0))
            self.assertEqual(tuple(dn.transform)[:6], (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0))

            az = dz.read(1)
            an = dn.read(1)
            foot = np.isfinite(an)
            self.assertEqual(int(foot.sum()), 5167373)

            # All-finite -zeros.tif check (prevents "Predicted values must be in range [0, 1]")
            self.assertTrue(np.isfinite(az).all())
            self.assertGreaterEqual(float(az.min()), 0.0)
            self.assertLessEqual(float(az.max()), 1.0)
            self.assertTrue(np.all(az[~foot] == 0.0))

            # Companion -nan.tif check
            self.assertTrue(np.isfinite(an[foot]).all())
            self.assertTrue(np.isnan(an[~foot]).all())
            self.assertGreaterEqual(float(an[foot].min()), 0.0)
            self.assertLessEqual(float(an[foot].max()), 1.0)

            # Byte-identical in-footprint predictions and exact 37,654 dot budget
            self.assertTrue(np.array_equal(az[foot], an[foot]))
            self.assertEqual(int((az > 0).sum()), 37654)

        # Single-TIFF ZIP archives must contain exactly the corresponding .tif
        for zp, tp in ((z_zip, z_tif), (n_zip, n_tif)):
            with zipfile.ZipFile(zp, "r") as zf:
                self.assertEqual(zf.namelist(), [tp.name])

    def test_validate_submission_allow_zero_outside_flag(self):
        with tempfile.TemporaryDirectory() as d:
            tpl = Path(d) / "tpl.tif"
            cand_z = Path(d) / "cand_zeros.tif"
            cand_n = Path(d) / "cand_nan.tif"
            prof_nan = dict(
                driver="GTiff",
                width=4,
                height=4,
                count=1,
                dtype="float32",
                crs="EPSG:32611",
                transform=from_origin(243350, 4508550, 100, 100),
                nodata=np.nan,
            )
            ref_a = np.zeros((4, 4), dtype="float32")
            ref_a[0, 0] = np.nan
            with rasterio.open(tpl, "w", **prof_nan) as ds:
                ds.write(ref_a, 1)

            nan_a = ref_a.copy()
            nan_a[2, 2] = 1.0
            with rasterio.open(cand_n, "w", **prof_nan) as ds:
                ds.write(nan_a, 1)

            zero_a = np.where(np.isfinite(nan_a), nan_a, 0.0).astype("float32")
            with rasterio.open(cand_z, "w", **{**prof_nan, "nodata": None}) as ds:
                ds.write(zero_a, 1)

            self.assertTrue(validate_tif(tpl, cand_n)["ok"])
            self.assertFalse(validate_tif(tpl, cand_z, allow_zero_outside=False)["ok"])
            self.assertTrue(validate_tif(tpl, cand_z, allow_zero_outside=True)["ok"])


if __name__ == "__main__":
    unittest.main()
