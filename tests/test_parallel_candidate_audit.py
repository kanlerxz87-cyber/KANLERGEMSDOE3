import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from audit_parallel_candidate import audit


def write(path, array, nodata=None, shift=0):
    with rasterio.open(path, 'w', driver='GTiff', height=9, width=9, count=1,
                       dtype='float32', crs='EPSG:32611', nodata=nodata,
                       transform=from_origin(shift, 900, 100, 100)) as ds:
        ds.write(array.astype('float32'), 1)


def test_exact_three_pixel_boundary_and_outside_footprint(tmp_path):
    sample = np.zeros((9, 9)); sample[0, 0] = np.nan
    lattice = np.zeros((9, 9)); lattice[4, 4] = 1
    candidate = np.zeros((9, 9)); candidate[4, 7] = candidate[8, 8] = 1
    labels = np.zeros((9, 9)); labels[4, 7] = 1
    for name, arr in [('sample', sample), ('lattice', lattice), ('candidate', candidate), ('labels', labels)]:
        write(tmp_path / (name + '.tif'), arr, nodata=np.nan if name == 'sample' else None)
    result = audit(*(tmp_path / (name + '.tif') for name in ('candidate', 'lattice', 'sample', 'labels')))
    assert result['candidate_dots'] == 2
    assert result['candidate_dots_within_3px_of_lattice'] == 1
    assert result['candidate_dot_overlap_fraction'] == .5
    assert not result['duplicate_over_70_percent']
    assert result['catalogue_positive_pixels'] == 1
    assert result['outside_unmasked_finite_count'] == 1
    assert not result['strict_nan_outside']
    # Grid misalignment must not be silently compared.
    write(tmp_path / 'candidate.tif', candidate, shift=1)
    with pytest.raises(ValueError, match='grid'):
        audit(*(tmp_path / (name + '.tif') for name in ('candidate', 'lattice', 'sample', 'labels')))


def test_empty_or_nonbinary_masks_fail_closed(tmp_path):
    zeros = np.zeros((9, 9))
    for name in ('candidate', 'lattice', 'sample', 'labels'):
        write(tmp_path / (name + '.tif'), zeros)
    paths = [tmp_path / (name + '.tif') for name in ('candidate', 'lattice', 'sample', 'labels')]
    with pytest.raises(ValueError, match='Empty'):
        audit(*paths)
    nonbinary = zeros.copy(); nonbinary[2, 2] = .2
    write(paths[0], nonbinary)
    with pytest.raises(ValueError, match='binary'):
        audit(*paths)


def test_archived_parallel_runner_does_not_start_another_experiment():
    import subprocess
    import sys
    from pathlib import Path
    runner = Path(__file__).resolve().parents[1] / 'scripts' / 'evaluate_holdout.py'
    result = subprocess.run([sys.executable, str(runner), '--phase', 'all'], text=True, capture_output=True)
    assert result.returncode != 0
    assert 'three-experiment budget' in result.stderr
