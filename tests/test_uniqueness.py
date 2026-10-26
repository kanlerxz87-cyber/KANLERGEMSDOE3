import unittest

import numpy as np

from scripts.check_uniqueness import compare, decision


class UniquenessTests(unittest.TestCase):
    @staticmethod
    def fixture():
        foot = np.ones((80, 80), dtype=bool)
        dots = np.zeros(foot.shape, dtype=bool)
        for x in range(10):
            dots[5 + (x // 5) * 20, 5 + (x % 5) * 12] = True
        reference = np.zeros_like(dots)
        points = np.argwhere(dots)
        for y, x in points[:7]:
            reference[y, x] = True
        surface = np.random.default_rng(11).random(foot.shape)
        return surface, dots, reference.astype(float), foot

    def test_seventy_percent_is_not_over_threshold(self):
        row = compare(*self.fixture())
        self.assertEqual(row["directed_dot_overlap_3px"], 0.7)
        self.assertFalse(row["duplicate"])
        self.assertTrue(decision([row], True, 1)["unique_under_protocol"])

    def test_more_than_seventy_percent_is_stop(self):
        surface, dots, reference, foot = self.fixture()
        reference[25, 29] = 1
        row = compare(surface, dots, reference, foot)
        self.assertGreater(row["directed_dot_overlap_3px"], .7)
        self.assertTrue(row["duplicate"])
        self.assertEqual(decision([row], False, 99)["status"], "STOP_DUPLICATE")

    def test_direction_and_euclidean_boundary(self):
        foot = np.ones((20, 20), bool)
        dots = np.zeros_like(foot)
        ref = np.zeros_like(foot)
        dots[5, 5] = dots[15, 15] = True
        ref[5, 8] = True
        surface = np.arange(400).reshape(20, 20)
        row = compare(surface, dots, ref, foot)
        self.assertEqual(row["directed_dot_overlap_3px"], .5)
        self.assertEqual(row["reverse_dot_overlap_3px"], 1)
        ref[:] = False
        ref[8, 8] = True
        self.assertEqual(compare(surface, dots, ref, foot)["directed_dot_overlap_3px"], 0)

    def test_surface_correlation_can_stop_without_dot_overlap(self):
        foot = np.ones((20, 20), bool)
        reference = np.linspace(0, 1, 400).reshape(20, 20)
        companion = np.zeros_like(foot)
        companion[1, 1] = True
        dots = np.zeros_like(foot)
        dots[18, 18] = True
        result = compare(reference * 2 + 5, dots, reference, foot, companion)
        self.assertAlmostEqual(result["rank_correlation"], 1)
        self.assertEqual(result["directed_dot_overlap_3px"], 0)
        self.assertTrue(result["duplicate"])

    def test_soft_reference_requires_explicit_dots_not_positive_support(self):
        surface, dots, reference, foot = self.fixture()
        with self.assertRaises(ValueError):
            compare(surface, dots, reference * .5 + .1, foot)

    def test_incomplete_registry_never_unique(self):
        row = compare(*self.fixture())
        for complete, expected in ((False, 1), (True, 2), (True, 0), (True, True), ("true", 1)):
            self.assertFalse(decision([row], complete, expected)["unique_under_protocol"])
        self.assertFalse(decision([], True, 0)["unique_under_protocol"])

    def test_constant_surface_and_empty_masks_not_unique(self):
        surface, dots, reference, foot = self.fixture()
        row = compare(np.ones_like(surface), dots, reference, foot)
        self.assertIsNone(row["rank_correlation"])
        self.assertFalse(decision([row], True, 1)["unique_under_protocol"])
        for a, b in ((np.zeros_like(dots), reference), (dots, np.zeros_like(reference))):
            with self.assertRaises(ValueError):
                compare(surface, a, b, foot)

    def test_nonfinite_grid_mismatch_and_fractional_dots_rejected(self):
        surface, dots, reference, foot = self.fixture()
        bad = surface.copy()
        bad[0, 0] = np.nan
        with self.assertRaises(ValueError):
            compare(bad, dots, reference, foot)
        with self.assertRaises(ValueError):
            compare(surface[:-1], dots, reference, foot)
        with self.assertRaises(ValueError):
            compare(surface, dots.astype(float) * .5, reference, foot)

    def test_nan_padding_ignored_only_outside_footprint(self):
        surface, dots, reference, foot = self.fixture()
        foot[-1, -1] = False
        surface[-1, -1] = reference[-1, -1] = np.nan
        self.assertTrue(compare(surface, dots, reference, foot)["comparable"])


if __name__ == "__main__":
    unittest.main()
