#!/usr/bin/env python3
"""Offline consistency and fail-closed checks for the one recorded run card."""
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load(path):
    def bad(v): raise ValueError(f'non-finite JSON constant {v}')
    return json.loads(path.read_text(),parse_constant=bad)


def require(condition, message):
    # Do not use assert: a fail-closed validator must work under python -O.
    if not condition: raise ValueError(message)


def check(card, lock):
    require(card['verdict']=='negative' and card['ok_to_submit'] is False, 'verdict is not negative')
    require(card['raster_sha256'] is None and card['validator_output'] is None, 'unexpected saved-file claim')
    require(card['submission_slot_spent'] is False, 'unexpected slot claim')
    require(len(card['submission_note'])<=140, 'submission note too long')
    require(card['leakage_canary']['passed'] and card['oof_model_canary']['passed'], 'leakage canary failed')
    require(all(not f['training_validation_overlap'] and not f['hidden_components_in_visible'] for f in card['fold_integrity']), 'fold isolation failed')
    locked={r['id'] for r in lock['entries']}
    require(len(locked)==len(lock['entries'])==167, 'registry count or ID mismatch')
    require(set(card['surface_registry'])=={'out_of_fold_surface','full_fit_surface'}, 'missing surface')
    for name,s in card['surface_registry'].items():
        require(s['passed_frozen_snapshot'] and not s['global_registry_complete'], f'{name}: incorrect registry scope')
        require(s['checked']==167 and len(s['rows'])==167, f'{name}: missing comparisons')
        require({r['id'] for r in s['rows']}==locked, f'{name}: reference identity mismatch')
        require(all(math.isfinite(r['rho']) and abs(r['rho'])<=.9 for r in s['rows']), f'{name}: invalid or duplicate correlation')
        require(math.isclose(s['max_abs_rho'],max(abs(r['rho']) for r in s['rows']),rel_tol=1e-12), f'{name}: incorrect maximum')
    overlap=card['correlation_overlap_vs_registry']
    require(overlap['duplicate'] and overlap['candidate_within_3px_of_reference']>.7, 'missing duplicate stop')
    require(overlap['candidate_dots']==37654 and overlap['other_final_rasters_checked']==0, 'unexpected final-dot audit')
    h=card['holdout_dti']
    require(h['evidence_class']=='HOLDOUT-DTI' and h['evaluator_version']=='gems57-pooled-hide-v2', 'unknown score provenance')
    for arm in ['candidate','ablation']:
        s=h['scores'][arm]
        require(s['withheld_positive_pixels']==sum(f['withheld_positives'] for f in card['fold_integrity'])==60988, f'{arm}: withheld count mismatch')
        require(0<=s['ci95'][0]<=s['ci95'][1]<=1 and 0<=s['dti']<=1, f'{arm}: invalid interval')
        c=[sum(f[arm+'_components'][k] for f in h['folds']) for k in ('tpw','fpw','fnw')]
        require(all(math.isclose(c[i],s[k],rel_tol=1e-11,abs_tol=1e-7) for i,k in enumerate(('tpw','fpw','fnw'))), f'{arm}: additive components mismatch')
        require(math.isclose(s['dti'],c[0]/(c[0]+.2*c[1]+.8*c[2]),rel_tol=1e-11), f'{arm}: pooled score mismatch')
    diff=h['paired_differences']['ablation']
    require(diff['ci95'][0]<=0<=diff['ci95'][1], 'paired interval does not match negative conclusion')
    require(math.isclose(diff['delta'],h['scores']['candidate']['dti']-h['scores']['ablation']['dti'],abs_tol=1e-12), 'paired difference mismatch')
    return {'ok':True,'verdict':'negative','surface_comparisons':334,'final_comparisons_before_stop':1,
            'note':'Consistency only; not an independent rerun, organizer receipt, or global novelty clearance.'}

if __name__=='__main__':
    print(json.dumps(check(load(ROOT/'evidence/run-card.json'),load(ROOT/'research/registry-lock.json')),indent=2))
