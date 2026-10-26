import importlib
import importlib.util
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_PKG = ROOT / "vendor/gems57"
_spec = importlib.util.spec_from_file_location(
    "_patched_gems57",
    VENDOR_PKG / "__init__.py",
    submodule_search_locations=[str(VENDOR_PKG)],
)
_pkg = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _pkg
_spec.loader.exec_module(_pkg)

_writer_mod = importlib.import_module("_patched_gems57.submission_writer")
_uniq_mod = importlib.import_module("_patched_gems57.uniqueness")
_temp_path = _writer_mod._temp_path
representation_class = _uniq_mod.representation_class
two_phase_summary = _uniq_mod.two_phase_summary


class VendorTemplateFixTests(unittest.TestCase):
    def test_submission_writer_temp_file_is_world_readable(self):
        with tempfile.TemporaryDirectory() as d:
            p = _temp_path(Path(d), "sample", ".tif")
            try:
                mode = stat.S_IMODE(p.stat().st_mode)
                self.assertEqual(mode, 0o644)
            finally:
                if p.exists():
                    os.unlink(p)

    def test_uniqueness_catches_negative_spearman_and_halo_saturated_probe(self):
        cls_probe = representation_class(206895, 5167373, halo_fraction=0.998713)
        self.assertEqual(cls_probe["kind"], "halo_saturated_probe")

        cls_dot = representation_class(37654, 5167373, halo_fraction=0.145)
        self.assertEqual(cls_dot["kind"], "dot_field")

        rows = [
            {
                "submission": "r13-lattice-s5",
                "repo": "GEMSDOE70",
                "their_dots": 206895,
                "their_3px_halo_fraction": 0.998713,
                "my_dots_within_3px_of_theirs": 0.99997,
                "their_dots_within_3px_of_mine": 0.12,
                "spearman_full_footprint": 0.01,
                "jaccard_dot_sets": 0.02,
            },
            {
                "submission": "genuine-detector",
                "repo": "GEMSDOE32",
                "their_dots": 37654,
                "their_3px_halo_fraction": 0.142,
                "my_dots_within_3px_of_theirs": 0.3974,
                "their_dots_within_3px_of_mine": 0.3821,
                "spearman_full_footprint": 0.04,
                "jaccard_dot_sets": 0.01,
            },
        ]
        summary = two_phase_summary(rows, 5167373)
        self.assertTrue(summary["literal_reading"]["duplicate"])
        self.assertFalse(summary["like_for_like_reading"]["duplicate"])
        self.assertEqual(summary["like_for_like_reading"]["halo_saturated_probe_rasters"], 1)
        self.assertAlmostEqual(summary["like_for_like_reading"]["worst_forward_overlap_dot_fields"], 0.3974)

        rows_inv = [
            *rows,
            {
                "submission": "inverted-clone",
                "repo": "GEMSDOE99",
                "their_dots": 5167373,
                "their_3px_halo_fraction": 1.0,
                "my_dots_within_3px_of_theirs": 1.0,
                "their_dots_within_3px_of_mine": 0.05,
                "spearman_full_footprint": -0.95,
                "jaccard_dot_sets": 0.007,
            },
        ]
        summary_inv = two_phase_summary(rows_inv, 5167373)
        self.assertTrue(summary_inv["literal_reading"]["duplicate"])
        self.assertTrue(summary_inv["like_for_like_reading"]["duplicate"])
        self.assertAlmostEqual(summary_inv["literal_reading"]["worst_spearman_full_footprint"], 0.95)


if __name__ == "__main__":
    unittest.main()
