import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from validate_raster import check


TRANSFORM = from_origin(10, 20, 100, 100)


def write(path, array, *, transform=TRANSFORM, crs="EPSG:32611", dtype="float32", nodata=None):
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1],
                       count=1, dtype=dtype, crs=crs, transform=transform, nodata=nodata) as ds:
        ds.write(array.astype(dtype), 1)


@pytest.fixture
def sample(tmp_path):
    arr = np.zeros((6, 7), dtype=np.float32)
    arr[0, :] = np.nan
    path = tmp_path / "sample.tif"
    write(path, arr, nodata=np.nan)
    return path


def test_valid_format_is_not_submission_approval(tmp_path, sample):
    arr = np.zeros((6, 7), dtype=np.float32)
    arr[3, 4] = 1
    path = tmp_path / "valid.tif"
    write(path, arr)
    result = check(path, sample)
    assert result["format_ok"] is True
    assert result["ok_to_submit"] is False
    assert result["report"]["nan_pixels"] == 0


@pytest.mark.parametrize("bad", [np.nan, np.inf, -0.01, 1.01])
def test_reject_invalid_values_without_silent_repair(tmp_path, sample, bad):
    arr = np.zeros((6, 7), dtype=np.float32)
    arr[3, 4] = bad
    path = tmp_path / "bad.tif"
    write(path, arr)
    assert check(path, sample)["format_ok"] is False
    with rasterio.open(path) as src:
        value = src.read(1)[3, 4]
    assert (np.isnan(value) and np.isnan(bad)) or value == pytest.approx(bad)


def test_reject_grid_dtype_outside_mass_and_bad_nodata(tmp_path, sample):
    arr = np.zeros((6, 7), dtype=np.float32)
    variants = [dict(transform=from_origin(11, 20, 100, 100)), dict(crs="EPSG:32612"),
                dict(dtype="uint16"), dict(nodata=-9999)]
    for i, kwargs in enumerate(variants):
        path = tmp_path / f"bad-{i}.tif"
        write(path, arr, **kwargs)
        assert check(path, sample)["format_ok"] is False
    arr[0, 0] = 1  # outside the sample footprint
    outside = tmp_path / "outside.tif"
    write(outside, arr)
    assert check(outside, sample)["format_ok"] is False


def test_reject_multiband_and_shape_mismatch(tmp_path, sample):
    multi = tmp_path / "multi.tif"
    with rasterio.open(multi, "w", driver="GTiff", height=6, width=7, count=2,
                       dtype="float32", crs="EPSG:32611", transform=TRANSFORM) as ds:
        ds.write(np.zeros((2, 6, 7), dtype=np.float32))
    assert not check(multi, sample)["format_ok"]
    smaller = tmp_path / "smaller.tif"
    write(smaller, np.zeros((5, 7), dtype=np.float32))
    assert not check(smaller, sample)["format_ok"]


def test_nan_outside_fails_local_strict_policy_not_a_claim_about_portal(tmp_path, sample):
    arr = np.zeros((6, 7), dtype=np.float32)
    arr[0, :] = np.nan
    path = tmp_path / "outside-nan.tif"
    write(path, arr, nodata=np.nan)
    result = check(path, sample)
    assert not result["format_ok"] and not result["ok_to_submit"]
    assert "stricter local policy" in result["policy"]
