"""Forensics only; never writes, repairs, promotes, or scores a submission."""
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]

def validate(path, template):
    with rasterio.open(template) as ref, rasterio.open(path) as ds:
        a = ds.read(1)
        finite = np.isfinite(a)
        checks = {
            'single_band': ds.count == 1,
            'crs_match': ds.crs is not None and ds.crs == ref.crs,
            'shape_match': ds.shape == ref.shape,
            'transform_match': ds.transform == ref.transform,
            'all_finite': bool(finite.all()),
            'range_0_1': bool(finite.all() and (a >= 0).all() and (a <= 1).all()),
        }
        return {'checks': checks, 'format_pass': all(checks.values()),
                'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                'nonfinite_count': int((~finite).sum()),
                'note': 'Format only; not scientific validation or permission to submit.'}

def overlap(candidate, reference):
    if candidate.shape != reference.shape or not candidate.any() or not reference.any():
        raise ValueError('Nonempty masks on an identical grid are required')
    return float((distance_transform_edt(~reference)[candidate] <= 3).mean())

def main():
    archived = json.loads((ROOT/'sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json').read_text())
    rows, masks, metadata = [], {}, {}
    for r in archived['historical_winners']:
        p = ROOT/'data'/f"{r['repo']}.tif"
        v = validate(p, ROOT/'data/sample_submission.tif')
        if v['sha256'] != r['sha256']:
            raise ValueError('Pinned raster hash mismatch: '+r['repo'])
        with rasterio.open(p) as ds:
            a = ds.read(1)
            masks[r['repo']] = np.isfinite(a) & (a > 0)
            metadata[r['repo']] = (ds.crs, ds.shape, ds.transform)
        rows.append({**r, 'local_validation': v})
    if len(set(metadata.values())) != 1:
        raise ValueError('Registry grids differ; no silent resampling allowed')
    pairs = []
    for ref, mask in masks.items():
        dist = distance_transform_edt(~mask)
        for name, candidate in masks.items():
            if name != ref:
                pairs.append({'candidate':name, 'reference':ref,
                              'overlap_3px':float((dist[candidate] <= 3).mean())})
    for row in rows:
        row['max_overlap_3px'] = max(p['overlap_3px'] for p in pairs if p['candidate'] == row['repo'])
        row['unique_under_protocol'] = False
        row['eligibility'] = 'STOP_DUPLICATE'
        row['estimated_score'] = None
    result = {'kind':'independently recomputed historical raster forensics; NOT HOLDOUT-DTI',
              'rows':rows, 'pairs':pairs,
              'surface_rank_correlation':None,
              'surface_note':'Historical continuous surfaces unavailable; overlap alone triggers STOP.'}
    (ROOT/'docs/audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Audited',len(rows),'pinned TIFFs;',len(pairs),'directed comparisons')
    print('Minimum overlap:',min(p['overlap_3px'] for p in pairs))

if __name__ == '__main__':
    main()
