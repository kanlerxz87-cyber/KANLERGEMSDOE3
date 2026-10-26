import math
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scipy.stats import spearmanr

from audit_portfolio import binary_spearman, duplicate_status
from bootstrap import ensure_template


def test_binary_phi_is_exact_tied_rank_spearman():
    rng = np.random.default_rng(87)
    a = rng.random((12, 15)) < .25
    b = rng.random((12, 15)) < .35
    foot = rng.random((12, 15)) < .8
    expected = spearmanr(a[foot], b[foot]).statistic
    assert binary_spearman(a, b, foot) == pytest.approx(expected, abs=1e-14)
    assert binary_spearman(np.zeros_like(a), b, foot) is None


def test_duplicate_thresholds_and_missing_evidence():
    assert duplicate_status([.70], [.90], 1) is False
    assert duplicate_status([.70001], [], 2) is True
    assert duplicate_status([.2], [.90001], 1) is True
    assert duplicate_status([.2], [-.95], 1) is False  # rule says positive Spearman
    assert duplicate_status([.2], [], 1) is None


def test_shared_three_pixel_disk_includes_boundary_and_is_directional():
    sys.path.insert(0, str(ensure_template() / "vendor"))
    from gems57.uniqueness import dot_overlap
    a = np.zeros((12, 12)); b = np.zeros_like(a)
    a[5, 5] = 1; a[0, 0] = 1
    b[5, 8] = 1
    assert dot_overlap(a, b) == pytest.approx(.5)
    assert dot_overlap(b, a) == pytest.approx(1)
    b[:] = 0; b[8, 6] = 1  # sqrt(10) > 3 pixels
    assert dot_overlap(a, b) == 0


def test_shared_witness_certificate_checks_grid_and_not_only_shape(tmp_path):
    sys.path.insert(0, str(ensure_template() / "vendor"))
    from gems57.uniqueness import saturation_certificate
    path = tmp_path / "witness.tif"
    transform = from_origin(10, 20, 100, 100)
    with rasterio.open(path, "w", driver="GTiff", height=5, width=6, count=1,
                       dtype="float32", crs="EPSG:32611", transform=transform) as ds:
        ds.write(np.full((5, 6), .1, np.float32), 1)
    foot = np.ones((5, 6), bool)
    with rasterio.open(path) as ds:
        grid = (ds.shape, ds.crs, ds.transform)
    result = saturation_certificate(path, foot, expected_grid=grid)
    assert result["universal_overlap_blocker"] and result["uncovered_allowed_pixels"] == 0
    bad_grid = (grid[0], grid[1], from_origin(11, 20, 100, 100))
    with pytest.raises(ValueError, match="CRS/transform"):
        saturation_certificate(path, foot, expected_grid=bad_grid)


def test_lattice_bound_is_a_lower_bound_not_an_average():
    uncovered, dots = 6649, 37654
    lower_bound = max(0, 1 - uncovered / dots)
    assert lower_bound == pytest.approx(.8234184947150369)
    assert math.floor(uncovered / .3) == 22163
