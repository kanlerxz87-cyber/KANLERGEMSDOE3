#!/usr/bin/env python3
"""Verify the frozen lattice obstruction from pinned rasters (not a candidate)."""
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
try:
    from .restore_data import sha256
except ImportError:  # python scripts/check_lattice.py
    from restore_data import sha256

ROOT=Path(__file__).resolve().parents[1]


def minimum_overlap(dots:int, uncovered:int) -> float:
    if dots <= 0 or uncovered < 0: raise ValueError('invalid dot/coverage counts')
    return max(0,dots-uncovered)/dots


def first_impossible_count(uncovered:int, limit:float=.70) -> int:
    if uncovered < 0 or not 0<=limit<1: raise ValueError('invalid overlap limit')
    # Integer arithmetic is useful for the exact default boundary 7/10.
    if limit==.70: return (10*uncovered)//3+1
    return int(np.floor(uncovered/(1-limit)))+1


def run():
    entries={e['id']:e for e in json.loads((ROOT/'data/input-manifest.json').read_text())['inputs']}
    for id in ('sample_submission','calibration_lattice'):
        row=entries[id]; p=ROOT/'data'/row['dest']
        if not p.is_file() or p.stat().st_size!=row['bytes'] or sha256(p)!=row['sha256']:
            raise ValueError(f'{id} mirror is missing or mismatched')
    with rasterio.open(ROOT/'data/sample_submission.tif') as ds:
        fp=np.isfinite(ds.read(1)); grid=(ds.shape,ds.crs,ds.transform)
    with rasterio.open(ROOT/'data/reference/lattice.tif') as ds:
        if (ds.shape,ds.crs,ds.transform)!=grid or ds.count!=1: raise ValueError('Lattice grid mismatch')
        a=ds.read(1)
    dots=fp & np.isfinite(a) & (a>0)
    covered=fp & (distance_transform_edt(~dots)<=3)
    uncovered=int((fp & ~covered).sum());n=37654
    out={'reference_sha256':'b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2',
         'footprint_pixels':int(fp.sum()),'lattice_dots':int(dots.sum()),'radius_px':3,
         'covered_footprint_pixels':int(covered.sum()),'uncovered_footprint_pixels':uncovered,
         'first_budget_for_forced_greater_than_70_percent':first_impossible_count(uncovered),
         'preregistered_budget':n,'guaranteed_minimum_overlap_at_budget':minimum_overlap(n,uncovered),
         'proof':'At most uncovered distinct candidate cells can lie outside coverage, so overlap >= max(0, N - uncovered) / N.',
         'caveats':['This is a mathematical bound, not an observed candidate overlap.',
                    'It does not rule out lower-density candidates.',
                    'Coverage and hash establish mirror identity, not organizer authentication.']}
    p=ROOT/'evidence/lattice-coverage.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':run()
