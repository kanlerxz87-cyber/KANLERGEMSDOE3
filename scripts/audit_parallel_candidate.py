#!/usr/bin/env python3
"""Audit an existing binary research raster against a pinned lattice, not a full registry."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from audit_history import disk


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path):
    with rasterio.open(path) as ds:
        return (ds.read(1, masked=True), (ds.shape, ds.crs, ds.transform),
                {'bands': ds.count, 'dtype': ds.dtypes[0], 'crs': str(ds.crs),
                 'shape': list(ds.shape), 'transform': list(ds.transform)[:6],
                 'nodata': None if ds.nodata is None or not np.isfinite(ds.nodata) else ds.nodata})


def audit(candidate: Path, lattice: Path, sample: Path, labels: Path) -> dict:
    sample_arr, grid, _ = read(sample)
    foot = (~np.ma.getmaskarray(sample_arr)) & np.isfinite(sample_arr.data)
    if not foot.any():
        raise ValueError('Empty reference footprint')
    pred, c_grid, info = read(candidate)
    refs, l_grid, _ = read(lattice)
    lab, y_grid, _ = read(labels)
    if c_grid != grid or l_grid != grid or y_grid != grid:
        raise ValueError('Candidate, lattice or labels do not match the mirror grid')
    # This comparison is defined for saved binary dots, not arbitrary probabilities.
    active = pred.data[foot]
    if (np.ma.getmaskarray(pred)[foot].any() or not np.isfinite(active).all()
            or not np.isin(active, [0, 1]).all()):
        raise ValueError('Candidate is not finite binary inside the footprint')
    lm = (~np.ma.getmaskarray(refs)) & (refs.data > 0) & foot
    dots = (pred.data > 0) & foot
    positive = int(dots.sum())
    if not lm.any() or not positive:
        raise ValueError('Empty lattice or candidate dots cannot establish uniqueness')
    near = binary_dilation(lm, structure=disk(3))
    within = int((dots & near).sum())
    label_dots = (~np.ma.getmaskarray(lab)) & (lab.data > 0) & foot
    outside = pred.data[~foot]
    outside_mask = np.ma.getmaskarray(pred)[~foot]
    return {
        'schema_version': 1,
        'scope': 'Saved binary dots versus one pinned lattice; not a full live-registry or surface audit.',
        'candidate_sha256': digest(candidate), 'lattice_sha256': digest(lattice),
        'sample_mirror_sha256': digest(sample), 'label_mirror_sha256': digest(labels),
        'organizer_template_authenticated': False,
        'geometry': info, 'candidate_dots': positive,
        'candidate_dots_within_3px_of_lattice': within,
        'candidate_dot_overlap_fraction': within / positive,
        'candidate_dots_outside_lattice_radius': positive - within,
        'duplicate_over_70_percent': within / positive > .70,
        'catalogue_positive_pixels': int((dots & label_dots).sum()),
        'in_footprint_nan': int(np.isnan(active).sum()),
        'in_footprint_inf': int(np.isinf(active).sum()),
        'in_footprint_min': float(active.min()), 'in_footprint_max': float(active.max()),
        'outside_pixel_count': int(outside.size),
        'outside_unmasked_finite_count': int((~outside_mask & np.isfinite(outside)).sum()),
        'outside_nan_count': int(np.isnan(outside).sum()),
        'strict_nan_outside': bool(np.isnan(outside).all()),
        'note': 'Research-only forensic audit. No selector authorization or organizer acceptance is implied.'
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'lattice', 'sample', 'labels'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.candidate, args.lattice, args.sample, args.labels)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
