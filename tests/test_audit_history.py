import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scipy.stats import spearmanr

import audit_history as audit


def test_binary_spearman_matches_tied_rank_reference():
    rng = np.random.default_rng(2026)
    a, b = rng.random(500) < .15, rng.random(500) < .2
    assert audit.phi_binary(a, b) == pytest.approx(spearmanr(a, b).statistic)
    assert audit.phi_binary(np.zeros(8), np.ones(8)) is None
    with pytest.raises(ValueError):
        audit.phi_binary(np.zeros(3), np.zeros(4))


def test_distance_disk_uses_euclidean_not_square_or_manhattan():
    d = audit.disk(3)
    assert d.shape == (7, 7)
    assert d[3, 6] and d[5, 5] and not d[6, 6]
    assert d.sum() == 29


def test_read_mask_rejects_nonbinary_and_wrong_grid(tmp_path):
    path = tmp_path / "tiny.tif"
    transform = from_origin(0, 300, 100, 100)
    profile = dict(driver="GTiff", height=3, width=3, count=1, dtype="float32", crs="EPSG:32611", transform=transform)
    foot = np.ones((3, 3), bool)
    template = {"shape": (3, 3), "crs": rasterio.crs.CRS.from_epsg(32611), "transform": transform}
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], dtype="float32"), 1)
    mask, info = audit.read_mask(path, template, foot)
    assert info["positive_pixels"] == 1 and mask[0, 1]
    wrong = dict(template, transform=from_origin(1, 300, 100, 100))
    with pytest.raises(ValueError, match="grid mismatch"):
        audit.read_mask(path, wrong, foot)
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(np.full((3, 3), .5, dtype="float32"), 1)
    with pytest.raises(ValueError, match="finite binary"):
        audit.read_mask(path, template, foot)
