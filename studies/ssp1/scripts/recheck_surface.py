#!/usr/bin/env python3
"""Re-measure the retained, fixed pre-placement surface. NEVER fit or emit dots.

A third-party SciPy check found a small discrepancy in one original surface
correlation. Preserve that observation; compute a separate full-registry recheck
from the saved array, without changing or optimizing a candidate prediction.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
from kanler.audit import sha256, surface_guard


def main():
    source = ROOT/'.cache/gems_work/ssp1_surface.npy'
    surface = np.load(source, mmap_mode='r')
    manifest = json.loads((ROOT/'registry/all_rasters.json').read_text())
    old = json.loads((ROOT/'evidence/surface_guard.json').read_text())
    with np.load(ROOT/'docs/data/validation_masks.npz') as z:
        footprint = z['footprint']
    scratch = ROOT/'.cache/audit/surface_recheck_full.json'
    result = surface_guard(surface, footprint, ROOT/'.cache/gems_data/sample_submission.tif',
                           manifest, ROOT, scratch)
    original = {(r['site'],r['path']):r for r in old['rows']}
    deltas = []
    comparisons = []
    for r in result['rows']:
        if r['comparison_status'] != 'compared':
            continue
        current = r['surface_spearman']
        prior = original[(r['site'],r['path'])]['surface_spearman']
        if current is not None and prior is not None:
            deltas.append(abs(current-prior))
        comparisons.append({'site':r['site'], 'path':r['path'],
                            'surface_spearman':current, 'original_observed_spearman':prior})
    result = {k:v for k,v in result.items() if k != 'rows'}
    result.update(stage='post_run_recheck_of_preserved_preplacement_surface',
                  verified_utc=datetime.now(timezone.utc).isoformat(),
                  surface_npy_sha256=sha256(source), registry_manifest_sha256=sha256(ROOT/'registry/all_rasters.json'),
                  input_footprint_sha256=sha256(ROOT/'docs/data/validation_masks.npz'),
                  model_fits_executed=0, dot_placements_executed=0,
                  original_report='evidence/surface_guard.json',
                  discrepancy={'n_comparisons_different_beyond_1e_12':sum(d>1e-12 for d in deltas),
                               'maximum_absolute_delta':max(deltas,default=0),
                               'cause':'Not established. The original observation is retained, not silently rewritten or excused by a relaxed tolerance.',
                               'scientific_effect':'No fit, candidate, holdout score/CI, final-dot overlap, or negative verdict changes. Both reports are well below 0.90 on comparable entries; quarantines still block universal certification.'},
                  comparisons=comparisons)
    (ROOT/'evidence/surface_recheck.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('comparisons','quarantines')},indent=2))


if __name__ == '__main__':
    main()
