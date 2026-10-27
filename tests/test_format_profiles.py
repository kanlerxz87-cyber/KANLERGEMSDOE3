from pathlib import Path
import tempfile
import unittest

import numpy as np
import rasterio
from rasterio.transform import from_origin

from scripts.validate_submission import digest, validate


class FormatProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.template = self.root / "template.tif"
        self.candidate = self.root / "candidate.tif"
        self.profile = dict(driver="GTiff", width=5, height=5, count=1, dtype="float32", crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100), nodata=np.nan)
        self.foot = np.ones((5, 5), dtype="float32")
        self.foot[0, 0] = np.nan
        self.write(self.template, self.foot)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, arr, **changes):
        profile = {**self.profile, **changes}
        with rasterio.open(path, "w", **profile) as dst:
            if arr.ndim == 2:
                dst.write(arr.astype(profile["dtype"]), 1)
            else:
                dst.write(arr.astype(profile["dtype"]))

    def test_zero_padding_is_a_named_local_profile_not_portal_proof(self):
        self.write(self.candidate, np.zeros((5, 5)), nodata=None)
        mask = validate(self.template, self.candidate, "template-mask")
        finite = validate(self.template, self.candidate, "finite-grid")
        self.assertFalse(mask["ok"])
        self.assertTrue(finite["ok"])
        self.assertEqual(mask["local_encoding_compatibility"], {"template-mask": False, "finite-grid": True, "masked-finite": False})
        self.assertEqual(finite["organizer_acceptance"], "NOT_TESTED")
        self.assertFalse(finite["slot_authorized"])

    def test_nan_padding_passes_mask_but_not_whole_grid_range(self):
        arr = np.zeros((5, 5)); arr[0, 0] = np.nan
        self.write(self.candidate, arr)
        mask = validate(self.template, self.candidate)
        self.assertTrue(mask["ok"])
        self.assertFalse(mask["entire_grid_finite_range_0_1"])
        self.assertFalse(validate(self.template, self.candidate, "finite-grid")["ok"])

    def test_negative_nodata_is_not_a_portal_range_guarantee(self):
        arr = np.zeros((5, 5)); arr[0, 0] = -9999
        self.write(self.candidate, arr, nodata=-9999)
        result = validate(self.template, self.candidate)
        self.assertTrue(result["ok"])
        self.assertFalse(result["entire_grid_finite_range_0_1"])

    def test_masked_finite_profile_checks_raw_bytes_and_mask_without_mutating(self):
        arr = np.zeros((5, 5), dtype="float32")
        arr[1, 1] = 0.8
        mask = np.full((5, 5), 255, dtype="uint8")
        mask[0, 0] = 0
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(self.candidate, "w", **{**self.profile, "nodata": None}) as dst:
                dst.write(arr, 1)
                dst.write_mask(mask)
        before = digest(self.candidate)
        report = validate(self.template, self.candidate, "masked-finite")
        self.assertTrue(report["ok"], report["errors"])
        self.assertTrue(report["checks"]["standalone_without_sidecars"])
        self.assertTrue(report["raw_whole_grid_finite_in_range"])
        self.assertTrue(report["masked_outside_footprint"])
        self.assertFalse(report["submission_authorized"])
        self.assertFalse(report["portal_acceptance_verified"])
        self.assertEqual(digest(self.candidate), before)

        # A nonzero pixel hidden by the mask is still read by raw range scans.
        arr[0, 0] = -9999
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(self.candidate, "w", **{**self.profile, "nodata": None}) as dst:
                dst.write(arr, 1)
                dst.write_mask(mask)
        report = validate(self.template, self.candidate, "masked-finite")
        self.assertFalse(report["ok"])
        self.assertTrue(report["local_encoding_compatibility"]["template-mask"])
        self.assertEqual(report["raw_range_diagnostics"]["finite_below_zero"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["out_of_range_outside_footprint"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["out_of_range_masked_pixels"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["finite_min"], -9999.0)

    def test_raw_diagnostics_count_high_values_and_nan(self):
        arr = np.zeros((5, 5))
        arr[0, 0] = np.nan
        arr[1, 1] = 1.1
        self.write(self.candidate, arr, nodata=np.nan)
        report = validate(self.template, self.candidate, "masked-finite")
        self.assertFalse(report["ok"])
        self.assertEqual(report["raw_range_diagnostics"]["nonfinite_pixels"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["nan_pixels"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["nonfinite_masked_pixels"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["nonfinite_outside_footprint"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["finite_above_one"], 1)
        self.assertEqual(report["raw_range_diagnostics"]["out_of_range_inside_footprint"], 1)
        self.assertFalse(report["portal_acceptance_verified"])

    def test_unmasked_infinity_is_not_null_padding(self):
        for value in (np.inf, -np.inf):
            arr = np.zeros((5, 5)); arr[0, 0] = value
            self.write(self.candidate, arr, nodata=None)
            for profile in ("template-mask", "finite-grid", "masked-finite"):
                self.assertFalse(validate(self.template, self.candidate, profile)["ok"])

    def test_invalid_inside_is_rejected_and_never_repaired(self):
        for value in (np.nan, np.inf, -np.inf, -1e-4, 1.0001, -3.4028235e38):
            arr = np.zeros((5, 5)); arr[1, 1] = value
            self.write(self.candidate, arr, nodata=None)
            before = digest(self.candidate)
            for profile in ("template-mask", "finite-grid", "masked-finite"):
                self.assertFalse(validate(self.template, self.candidate, profile)["ok"])
            self.assertEqual(digest(self.candidate), before)

    def test_masked_inside_rejected_even_when_raw_value_is_in_range(self):
        self.write(self.candidate, np.zeros((5, 5)), nodata=0)
        result = validate(self.template, self.candidate, "finite-grid")
        self.assertFalse(result["ok"])
        self.assertGreater(result["masked_inside"], 0)

    def test_all_grid_contract_failures_are_detected(self):
        for changes in (dict(dtype="float64"), dict(crs="EPSG:4326"), dict(transform=from_origin(243351, 4508550, 100, 100))):
            self.write(self.candidate, np.zeros((5, 5)), nodata=None, **changes)
            self.assertFalse(validate(self.template, self.candidate, "finite-grid")["ok"])
        self.write(self.candidate, np.zeros((2, 5, 5)), count=2, nodata=None)
        self.assertFalse(validate(self.template, self.candidate, "finite-grid")["ok"])
        self.write(self.candidate, np.zeros((4, 5)), height=4, nodata=None)
        self.assertFalse(validate(self.template, self.candidate, "finite-grid")["ok"])

    def test_empty_footprint_never_passes(self):
        self.write(self.template, np.full((5, 5), np.nan))
        self.write(self.candidate, np.zeros((5, 5)), nodata=None)
        self.assertFalse(validate(self.template, self.candidate, "finite-grid")["ok"])

    def test_report_binds_exact_candidate_and_template(self):
        self.write(self.candidate, np.zeros((5, 5)), nodata=None)
        result = validate(self.template, self.candidate, "finite-grid")
        self.assertEqual(result["candidate_sha256"], digest(self.candidate))
        self.assertEqual(result["template_sha256"], digest(self.template))
        with self.assertRaises(ValueError):
            validate(self.template, self.candidate, "anything")


if __name__ == "__main__":
    unittest.main()
