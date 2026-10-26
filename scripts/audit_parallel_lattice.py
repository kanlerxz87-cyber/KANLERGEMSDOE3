#!/usr/bin/env python3
"""Recheck the existing parallel GPC-3 raster against the registered lattice.

This inspects saved bytes only; it does not generate, tune, or submit a candidate.
The original sample/lattice mirrors must first be restored and hash-verified.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = 'docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif'
CANDIDATE_SHA = '16ec0585a884224460f0e5d09e7448a54ab5a3348db92279452a9a4e0453b0f7'
SOURCE_COMMIT = '50488287492b3e973818dba86bb9fd839ebc4337'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def audit():
    inputs = {x['id']: x for x in json.loads((ROOT/'data/input-manifest.json').read_text())['inputs']}
    for name in ('sample_submission', 'calibration_lattice'):
        row = inputs[name]
        p = ROOT/'data'/row['dest']
        if not p.is_file() or p.stat().st_size != row['bytes'] or sha256(p) != row['sha256']:
            raise ValueError(f'{name}: missing or mismatched pinned input')
    candidate = ROOT/CANDIDATE
    digest = sha256(candidate)
    if digest != CANDIDATE_SHA:
        raise ValueError('Parallel candidate hash mismatch; refusing to apply a stale audit')
    with rasterio.open(ROOT/'data'/inputs['sample_submission']['dest']) as ds:
        footprint = np.isfinite(ds.read(1))
        grid = ds.shape, ds.crs, ds.transform
    with rasterio.open(candidate) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
            raise ValueError('Candidate grid mismatch')
        a = ds.read(1)
    with rasterio.open(ROOT/'data'/inputs['calibration_lattice']['dest']) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
            raise ValueError('Lattice grid mismatch')
        b = ds.read(1)
    dots = footprint & np.isfinite(a) & (a > 0)
    reference = footprint & np.isfinite(b) & (b > 0)
    n = int(dots.sum())
    if not n or not reference.any():
        raise ValueError('Empty candidate or lattice')
    near = int((dots & (distance_transform_edt(~reference) <= 3)).sum())
    return {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'source_commit': SOURCE_COMMIT,
        'candidate': CANDIDATE,
        'candidate_sha256': digest,
        'expected_owner_sha256': CANDIDATE_SHA,
        'reference': 'registry-160: 13GEMSDOE spacing-5 lattice',
        'reference_sha256': inputs['calibration_lattice']['sha256'],
        'grid_matches_mirror': True,
        'candidate_dots': n,
        'within_3px': near,
        'candidate_overlap': near/n,
        'duplicate': near/n > 0.70,
        'interpretation': 'Independent comparison of an existing parallel research artifact, not another candidate experiment. A nine-champion pass does not satisfy the literal all-registry rule.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='update the recorded receipt; default prints only')
    args = parser.parse_args()
    result = audit()
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.write:
        (ROOT/'evidence/parallel-lattice-audit.json').write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
