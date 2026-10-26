#!/usr/bin/env python3
"""Run the single frozen displacement-lane experiment; no automatic slot selection.

Requires the pinned shared template and frozen registry, installed unmodified by
scripts/install_template.py and scripts/fetch_registry.py. Data are never trained
from the sample raster. A duplicate stops before writing a candidate GeoTIFF.
"""
from __future__ import annotations
import gc
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'.cache/template/GEMSDOE24/src'))
sys.path.insert(0,str(ROOT/'.cache/template/GEMSDOE32/vendor'))
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from gems import emission, holdout, novelty
from gems57 import evaluate_holdout
from gems_project.features import FEATURE_NAMES, texture_features
from prepare_data import validate

BUDGET=37654
LIMIT_SECONDS=2*60*60
CARD=ROOT/'evidence/run-card.json'
CACHE=ROOT/'.cache/experiment'


def now(): return datetime.now(timezone.utc).isoformat()

def dump(obj):
    CARD.parent.mkdir(parents=True,exist_ok=True)
    tmp=CARD.with_suffix('.json.partial')
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
    os.replace(tmp,CARD)


def check_time(start):
    if time.monotonic()-start>=LIMIT_SECONDS:
        raise TimeoutError('Two-hour experiment budget exceeded; stopped before the next stage')


def fits(features, eligible, positive, seed, columns):
    rng=np.random.default_rng(seed)
    ip=np.flatnonzero(eligible & positive)
    ineg=np.flatnonzero(eligible & ~positive)
    if not len(ip) or not len(ineg): raise ValueError('A training split lacks positives or background')
    ip=rng.choice(ip,min(len(ip),30000),replace=False)
    ineg=rng.choice(ineg,min(len(ineg),6*len(ip)),replace=False)
    select=np.r_[ip,ineg]
    y=np.r_[np.ones(len(ip),np.uint8),np.zeros(len(ineg),np.uint8)]
    clf=HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,learning_rate=0.08,
          min_samples_leaf=30,l2_regularization=1.0,early_stopping=False,random_state=seed)
    clf.fit(features[select,:columns],y)
    return clf, {'visible_positive_train':len(ip),'background_train':len(ineg)}


def candidate_map(values,ids,shape):
    out=np.zeros(shape,np.float32)
    out.ravel()[ids]=values
    return out


def rank_against_registry(surface,fp,lock,*,name,start):
    vals=surface[fp]
    if not np.isfinite(vals).all() or np.ptp(vals)==0:
        raise ValueError(f'{name} is nonfinite or constant inside the footprint')
    ranks=rankdata(vals,method='average')
    records=[]
    with rasterio.open(ROOT/'data/sample_submission.tif') as template:
        grid=(template.shape,template.crs,template.transform)
    for i,row in enumerate(lock['entries']):
        check_time(start)
        p=ROOT/'.cache/registry'/f"{row['id']}.tif"
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError(f"Missing or mismatched registry raster {row['id']}")
        with rasterio.open(p) as ds:
            if (ds.shape,ds.crs,ds.transform)!=grid or ds.count!=1:
                raise ValueError(f"Registry grid mismatch {row['id']}")
            ref=ds.read(1)[fp]
        if not np.isfinite(ref).all(): raise ValueError(f"Nonfinite registry footprint: {row['id']}")
        if hashlib.sha256(np.asarray(ref,dtype='<f4').tobytes()).hexdigest()!=row['footprint_sha256']:
            raise ValueError(f"Registry footprint checksum mismatch: {row['id']}")
        rho=novelty.rank_correlation(ranks,ref)
        records.append({'id':row['id'],'file':row['file'],'rho':rho})
        if rho is None:
            raise ValueError(f"Undefined rank correlation against {row['id']}; cannot claim pass")
        if abs(rho)>0.90:
            return {'stage':name,'checked':len(records),'planned':len(lock['entries']),
                    'passed_frozen_snapshot':False,'duplicate':records[-1],'rows':records}
        if (i+1)%25==0: print(f'{name}: {i+1}/{len(lock["entries"])} checked',flush=True)
    return {'stage':name,'checked':len(records),'planned':len(lock['entries']),
            'passed_frozen_snapshot':True,'max_abs_rho':max(abs(r['rho']) for r in records),
            'rows':records,'global_registry_complete':False}


def crop_valid(valid,pad=3):
    yy,xx=np.nonzero(valid)
    if not len(yy): raise ValueError('Empty evaluation region')
    h,w=valid.shape
    return (slice(max(0,int(yy.min())-pad),min(h,int(yy.max())+pad+1)),
            slice(max(0,int(xx.min())-pad),min(w,int(xx.max())+pad+1)))


def execute():
    if CARD.exists(): raise SystemExit('Run card already exists. Do not silently repeat or tune; preserve the frozen result.')
    started=time.monotonic()
    card={'schema_version':1,'generated_utc':now(),'hypothesis':'Bilateral K/Th texture displacement across a coherent LiDAR scarp',
          'mechanism':'Nonzero along-strike offset of matched radiometric flank profiles; LiDAR provides a candidate surface break.',
          'named_non_fault_process':'Alluvial fan channels or lithological contacts, plus roads and survey seams',
          'lane':'provisional; prompt does not identify a named method paragraph', 'experiment_number':2,'experiment_limit':3,
          'prior_attempt':'evidence/run-01-error.json (clock-variable bug; no holdout or raster; unchanged scientific parameters)',
          'time_limit_seconds':LIMIT_SECONDS,'status':'running','verdict':'negative','ok_to_submit':False,
          'submission_slot_spent':False,'organizer_confirmed_score':None,
          'holdout_dti':None,'correlation_overlap_vs_registry':None,'raster_sha256':None,
          'validator_output':None,'submission_name':None,
          'submission_note':'Bilateral K/Th displacement at LiDAR scarp; research only; DO NOT SUBMIT',
          'note':'Bilateral K/Th displacement at LiDAR scarp; research only; DO NOT SUBMIT',
          'notes':['A catalogue-recovery holdout is not an estimate of the hidden leaderboard score.',
                   'The frozen snapshot cannot cover all concurrent or unregistered rasters.']}
    dump(card)
    try:
        print('Checking pinned inputs...',flush=True)
        prep=validate()
        card['data_validation']={'grid':prep['grid'],'sample_positives_equal_labels':prep['sample_positives_equal_labels'],'mirror_only':True}
        with rasterio.open(ROOT/'data/sample_submission.tif') as ds: fp=np.isfinite(ds.read(1))
        with rasterio.open(ROOT/'data/labels.tif') as ds: labels=fp&(ds.read(1)==1)
        with rasterio.open(ROOT/'data/external/geodawn_rad_u8.tif') as ds: k,th=ds.read([1,2])
        with rasterio.open(ROOT/'data/external/lidar_scarp_features_u8.tif') as ds: step,coh,strike,valid=ds.read([3,10,11,12])
        print('Building physical features, label-free...',flush=True)
        X,support=texture_features(fp,k,th,step,coh,strike,valid)
        del k,th,step,coh,strike,valid; gc.collect()
        ids=np.flatnonzero(fp); shape=fp.shape
        card['features']={'names':list(FEATURE_NAMES),'support_pixels':int(support.sum()),
                          'label_based_features':[],'matrix_shape':list(X.shape)}
        ctx=holdout.SegmentHoldout(fp,labels,buffer_px=15)
        card['fold_integrity']=[{'name':f['name'],'withheld_positives':int(f['truth'].sum()),
            'hidden_components':int(len(f['hidden_component_ids'])),
            'training_validation_overlap':bool((f['train'] & f['valid']).any()),
            'hidden_components_in_visible':bool(np.isin(ctx.components[f['visible']],f['hidden_component_ids']).any())}
            for f in ctx.folds]
        if any(r['training_validation_overlap'] or r['hidden_components_in_visible'] for r in card['fold_integrity']):
            raise ValueError('Fold isolation check failed')
        print('Testing each source/derived feature for leakage...',flush=True)
        canary_features={name:candidate_map(X[:,i],ids,shape) for i,name in enumerate(FEATURE_NAMES)}
        canary_features['profile_support']=candidate_map(support,ids,shape)
        canary=ctx.canary(canary_features)
        del canary_features; gc.collect()
        card['leakage_canary']=canary; dump(card)
        if not canary['passed']:
            card.update(status='stopped: leakage canary',stop_reason='At least one feature has two-sided holdout AUC above 0.90')
            return card
        check_time(started)
        print('Training spatially purged fold models...',flush=True)
        oof_c=np.zeros(len(ids),np.float32);oof_b=np.zeros(len(ids),np.float32); counts=[]
        labels_vec=labels.ravel()[ids]
        for fold in ctx.folds:
            check_time(started)
            visible=fold['visible']; f=fold['id']
            train=fold['train'].ravel()[ids] & support
            pos=visible.ravel()[ids]
            # Excluding the visible-fault neighborhood from background is a
            # training sampling rule, not an evaluation mask. No hidden labels.
            dist=distance_transform_edt(~visible)
            train &= pos | (dist.ravel()[ids]>3)
            del dist
            cand,n1=fits(X,train,pos,20261026+f,9)
            base,n2=fits(X,train,pos,20261026+f,6)
            to_predict=np.flatnonzero(fold['valid'].ravel()[ids] & support)
            oof_c[to_predict]=cand.predict_proba(X[to_predict,:9])[:,1]
            oof_b[to_predict]=base.predict_proba(X[to_predict,:6])[:,1]
            counts.append({'fold':fold['name'],'candidate':n1,'ablation':n2,'predicted_supported_pixels':len(to_predict)})
            print(f"{fold['name']}: trained; predicted {len(to_predict)} supported cells",flush=True)
        card['training']=counts
        oof_surface=candidate_map(oof_c,ids,shape)
        model_canary=ctx.canary({'oof_model_probability':oof_surface})
        card['oof_model_canary']=model_canary;dump(card)
        if not model_canary['passed']:
            card.update(status='stopped: OOF model canary',stop_reason='OOF probability AUC above 0.90')
            return card
        check_time(started)
        print('Fitting final surface from full visible catalogue...',flush=True)
        dist=distance_transform_edt(~labels)
        all_train=support & (labels_vec | (dist.ravel()[ids]>3)); del dist
        final_model,final_counts=fits(X,all_train,labels_vec,20261031,9)
        full=np.zeros(len(ids),np.float32)
        supported_ids=np.flatnonzero(support)
        for offset in range(0,len(supported_ids),250000):
            ix=supported_ids[offset:offset+250000]
            full[ix]=final_model.predict_proba(X[ix,:9])[:,1]
        full_surface=candidate_map(full,ids,shape)
        card['full_training']=final_counts
        lock=json.loads((ROOT/'research/registry-lock.json').read_text())
        # Both continuous surfaces must clear the frozen snapshot before any
        # Poisson dot placement. Presence of further rasters is not excluded.
        print('Checking OOF surface against the frozen registry...',flush=True)
        for label,surface in [('out_of_fold_surface',oof_surface),('full_fit_surface',full_surface)]:
            result=rank_against_registry(surface,fp,lock,name=label,start=started)
            card.setdefault('surface_registry',{})[label]=result; dump(card)
            if not result['passed_frozen_snapshot']:
                card.update(status='stopped: surface duplicate',stop_reason='Surface exceeds |Spearman| 0.90 against a registered raster')
                return card
        print('Computing paired, pooled holdout components...',flush=True)
        cand_terms=[];base_terms=[];fold_results=[]
        base_surface=candidate_map(oof_b,ids,shape)
        support_map=candidate_map(support,ids,shape).astype(bool)
        for fold in ctx.folds:
            check_time(started)
            n=int(round(BUDGET*int(fold['valid'].sum())/int(fp.sum())))
            eligible=fold['valid'] & support_map & ~fold['visible']
            pc=emission.priority_poisson(oof_surface,eligible,n,min_dist=3.0)
            pb=emission.priority_poisson(base_surface,eligible,n,min_dist=3.0)
            if int(pc.sum())!=n or int(pb.sum())!=n:
                raise ValueError(f"Insufficient eligible dot capacity for {fold['name']}")
            sl=crop_valid(fold['valid'])
            f={'region':fold['valid'][sl],'visible':fold['visible'][sl],'truth':fold['truth'][sl]}
            kw={'block_side':100,'origin':(sl[0].start,sl[1].start),'global_shape':shape}
            rc,tc=evaluate_holdout.evaluate(pc[sl].astype(np.float32),f,fp[sl],**kw)
            rb,tb=evaluate_holdout.evaluate(pb[sl].astype(np.float32),f,fp[sl],**kw)
            cand_terms.append(tc);base_terms.append(tb)
            # Only pooled scores have the required confidence intervals. Keep
            # additive fold components, not unlabeled per-fold score estimates.
            components=('tpw','fpw','fnw','n_truth','emitted')
            fold_results.append({'fold':fold['name'],'budget':n,
                'candidate_components':{key:rc[key] for key in components},
                'ablation_components':{key:rb[key] for key in components}})
            print(f"{fold['name']}: HOLDOUT-DTI candidate {rc['dti']:.6f}; ablation {rb['dti']:.6f}",flush=True)
        result=evaluate_holdout.pooled_summary({'candidate':np.sum(cand_terms,axis=0),
            'ablation':np.sum(base_terms,axis=0)},draws=1999,seed=20261026,candidate='candidate')
        result['folds']=fold_results
        result['protocol']={'buffer_m':1500,'catalogue_features':'none','visible_fault_mask':'pixel-exact',
            'alpha':0.2,'beta':0.8,'triangular_radius_m':300,'whole_components_hidden':True}
        card['holdout_dti']=result;dump(card)
        print('Creating final dots in memory and checking the lattice first...',flush=True)
        check_time(started)
        final_dots=emission.priority_poisson(full_surface,support_map & ~labels,BUDGET,min_dist=3.0)
        if int(final_dots.sum())!=BUDGET: raise ValueError('Insufficient final dot capacity')
        lattice=next(row for row in lock['entries'] if 'lattice-s5' in row['file'])
        with rasterio.open(ROOT/'.cache/registry'/f"{lattice['id']}.tif") as ds: ref=ds.read(1)
        lattice_dots=fp & np.isfinite(ref) & (ref>0)
        overlap=novelty.dot_overlap(final_dots,lattice_dots)
        rho=novelty.correlation(final_dots[fp].astype(float),np.where(lattice_dots[fp],1.0,0.0))
        duplicate=novelty.is_duplicate(rho,overlap['candidate_within_3px_of_reference'])
        card['correlation_overlap_vs_registry']={'stage':'final_dots','registry_file':lattice['file'],
            'registry_id':lattice['id'],'reference_sha256':lattice['sha256'],'rho':rho,**overlap,
            'duplicate':duplicate,'other_final_rasters_checked':0,
            'explanation':'Literal early-stop: a registered calibration lattice is not exempt; no placement adjustment was made.'}
        if duplicate:
            card.update(status='stopped: final dots duplicate',stop_reason='More than 70% of candidate dots lie within 3 pixels of a registered raster; no GeoTIFF written')
            return card
        # A pass against just this one reference cannot establish global novelty.
        # This code intentionally does not write an unverified submission. Extend
        # the literal final-dot comparison to all entries before any writing.
        card.update(status='stopped: final registry incomplete',stop_reason='One comparator is not sufficient for an all-registry uniqueness pass; no GeoTIFF written')
        return card
    except Exception as exc:
        card.update(status='stopped: error',stop_reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        card['duration_seconds']=round(time.monotonic()-started,2)
        dump(card)
        print('Run card:',CARD,flush=True)

if __name__=='__main__': execute()
