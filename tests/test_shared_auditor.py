"""Exercise the pinned shared auditor, not an independent local validator fork.

The shared auditor has historical-grid constants; only those constants are
monkeypatched to make the synthetic 2x2 fixtures inexpensive. CI bootstraps the
pinned template; an offline clone without it skips these integration tests.
"""
import hashlib
import importlib.util
import os
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
PIN = '07806249f4ed3efe70b4fbf866183c32392b7853'


@pytest.fixture
def shared(monkeypatch):
    root = Path(os.environ.get('GEMS_TEMPLATE_DIR', ROOT / f'.cache/shared-template-{PIN}'))
    source = root / 'src/gems32/submission.py'
    if not source.exists():
        pytest.skip('pinned shared template not bootstrapped')
    expected = next(line.split()[0] for line in (ROOT / 'data/shared-tool-hashes.txt').read_text().splitlines()
                    if line.endswith('src/gems32/submission.py'))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location('shared_submission_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for key, value in {'EXPECTED_HEIGHT': 2, 'EXPECTED_WIDTH': 2,
                       'EXPECTED_TOTAL_PIXELS': 4, 'EXPECTED_FOOTPRINT_PIXELS': 3}.items():
        monkeypatch.setattr(module, key, value)
    return module


@pytest.fixture
def grid(tmp_path):
    transform = from_origin(243350, 4508550, 100, 100)
    profile = dict(driver='GTiff', height=2, width=2, count=1, dtype='float32',
                   crs='EPSG:32611', transform=transform, nodata=np.nan)
    template = tmp_path / 'template.tif'
    with rasterio.open(template, 'w', **profile) as ds:
        ds.write(np.array([[0, 0], [0, np.nan]], dtype='float32'), 1)
    foot = np.array([[True, True], [True, False]])
    labels = np.zeros((2, 2), dtype=bool)
    return template, profile, foot, labels


def write_tiff(path, profile, values):
    with rasterio.open(path, 'w', **profile) as ds:
        ds.write(np.asarray(values, dtype='float32'), 1)


def test_actual_shared_auditor_accepts_valid_saved_bytes(shared, grid, tmp_path):
    template, profile, foot, labels = grid
    candidate = tmp_path / 'valid.tif'
    write_tiff(candidate, profile, [[0, .5], [1, np.nan]])
    report = shared.audit_geotiff(candidate, foot, labels, mode='nan', template_tif=template)
    assert report['all_checks_passed'] is True
    assert report['sha256'] == hashlib.sha256(candidate.read_bytes()).hexdigest()


@pytest.mark.parametrize('bad_value', [np.nan, np.inf, -3.4028235e38, -.01, 1.01])
def test_actual_shared_auditor_rejects_bad_in_footprint_values(shared, grid, tmp_path, bad_value):
    template, profile, foot, labels = grid
    candidate = tmp_path / 'bad.tif'
    write_tiff(candidate, profile, [[0, bad_value], [1, np.nan]])
    with pytest.raises(ValueError, match='Submission audit failed'):
        shared.audit_geotiff(candidate, foot, labels, mode='nan', template_tif=template)


def test_actual_shared_auditor_rejects_outside_value_and_wrong_grid(shared, grid, tmp_path):
    template, profile, foot, labels = grid
    candidate = tmp_path / 'bad-outside.tif'
    write_tiff(candidate, profile, [[0, .5], [1, 0]])
    with pytest.raises(ValueError, match='outside_footprint_compliant'):
        shared.audit_geotiff(candidate, foot, labels, mode='nan', template_tif=template)
    wrong = dict(profile, transform=from_origin(243351, 4508550, 100, 100))
    write_tiff(candidate, wrong, [[0, .5], [1, np.nan]])
    with pytest.raises(ValueError, match='grid'):
        shared.audit_geotiff(candidate, foot, labels, mode='nan', template_tif=template)
