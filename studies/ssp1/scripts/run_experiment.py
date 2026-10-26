#!/usr/bin/env python3
"""One preregistered SSP1 experiment. Stop at any duplicate; never use a slot.

OOF fits are the folds of ONE fixed experiment, not hyperparameter trials.
No frozen peer raster is ever a feature or a training target.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation,distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from gems32 import holdout
from gems32.paths import data_dir,work_dir
from kanler.science import FEATURE_NAMES,priority_dots
from kanler.audit import surface_guard,final_guard,sha256,mask_sha
from kanler.gates import promotion,score_record
from kanler.peer_review import review,strip_internal
from submission_writer import write_validated_submission

BUDGET=37654
STARTED=time.monotonic()


def save_json(name,obj):
    p=ROOT/'evidence'/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')


def canaries(x,ctx):
    positives=[];negatives=[];counts=[]
    rng=np.random.default_rng(20261026)
    unique_truth=np.zeros(ctx.foot.shape,bool)
    for cell in ctx.cells:
        tile=x[cell.bbox]
        y,xx=cell.truth_coords
        positives.append(np.asarray(tile[y,xx],dtype=np.float32))
        truth=np.zeros(cell.active_sub.shape,bool);truth[y,xx]=True
        unique_truth[cell.bbox]|=truth
        # Withheld truth is consulted ONLY by this diagnostic/evaluator, never by
        # training, the feature builder, or the production emission eligibility.
        bg=cell.active_sub & (distance_transform_edt(~truth)>3)
        idx=np.flatnonzero(bg);idx=rng.choice(idx,min(20000,len(idx)),replace=False)
        negatives.append(np.asarray(tile.reshape(-1,tile.shape[-1])[idx],dtype=np.float32))
        counts.append({'cell':cell.key,'positive_events':int(len(y)),'unlabeled_controls':int(len(idx))})
    xp=np.concatenate(positives);xn=np.concatenate(negatives)
    y=np.r_[np.ones(len(xp)),np.zeros(len(xn))]
    values=np.concatenate([xp,xn]);rows=[]
    for j,name in enumerate(FEATURE_NAMES):
        auc=float(roc_auc_score(y,values[:,j]));either=max(auc,1-auc)
        rows.append({'feature':name,'raw_auc':auc,'either_direction_auc':either,'passed':bool(either<=0.90)})
    result={'label':'LEAKAGE-CANARY AUC DIAGNOSTIC; NOT DTI OR A LEADERBOARD SCORE','evaluator_version':holdout.HIDE_RECOVER_EVALUATOR_VERSION,'n_withheld_positive_events':len(xp),'n_unique_withheld_positive_pixels':int(unique_truth.sum()),'n_unlabeled_controls':len(xn),'n_features':len(rows),'threshold':0.90,'passed':all(r['passed']for r in rows),'max_either_direction_auc':max(r['either_direction_auc']for r in rows),'features':rows,'cells':counts,'limitation':'Background is unlabeled, not proven fault absence. Passing a canary does not prove no leakage; split provenance and label-free feature derivation are separately checked.'}
    save_json('feature_canaries.json',result)
    return result


def fit_model(x,visible,train_domain,seed):
    rng=np.random.default_rng(seed)
    pos=np.flatnonzero(visible&train_domain)
    if len(pos)==0:
        raise ValueError('No visible training positives')
    if len(pos)>24000:
        pos=rng.choice(pos,24000,replace=False)
    dvis=distance_transform_edt(~visible)
    neg=np.flatnonzero(train_domain&(dvis>3));del dvis
    if not len(neg):
        raise ValueError('No unlabeled training controls')
    neg=rng.choice(neg,min(96000,len(neg)),replace=False)
    flat=x.reshape(-1,x.shape[-1]);idx=np.r_[pos,neg]
    features=np.asarray(flat[idx],dtype=np.float32)
    y=np.r_[np.ones(len(pos),np.int8),np.zeros(len(neg),np.int8)]
    weights=np.r_[np.full(len(pos),len(neg)/len(pos)),np.ones(len(neg))]
    model=HistGradientBoostingClassifier(max_iter=70,max_leaf_nodes=15,learning_rate=0.08,l2_regularization=10,min_samples_leaf=60,early_stopping=False,random_state=seed)
    with threadpool_limits(limits=2):
        model.fit(features,y,sample_weight=weights)
    rec={'training_positive_pixels':len(pos),'training_unlabeled_pixels':len(neg),'train_domain_pixels':int(train_domain.sum()),'seed':seed,'positive_indices_sha256':hashlib.sha256(pos.astype('<i8').tobytes()).hexdigest(),'unlabeled_indices_sha256':hashlib.sha256(neg.astype('<i8').tobytes()).hexdigest(),'not_calibrated_probabilities':True}
    return model,rec


def predict(model,x,eligible):
    p=np.zeros(eligible.shape,np.float32)
    flat=x.reshape(-1,x.shape[-1]);out=p.ravel();idx=np.flatnonzero(eligible)
    with threadpool_limits(limits=2):
        for k in range(0,len(idx),100000):
            ii=idx[k:k+100000]
            out[ii]=model.predict_proba(np.asarray(flat[ii],np.float32))[:,1]
    return p


def main():
    card_path=ROOT/'evidence/run_card.json'
    if card_path.exists():
        raise SystemExit('An experiment is already recorded. Do not overwrite or rerun a stopped negative experiment.')
    prereg=ROOT/'registry/hypotheses.json'
    expected=(ROOT/'evidence/preregistration_sha256.txt').read_text().split()[0]
    if sha256(prereg)!=expected:
        raise ValueError('Preregistration changed after freezing')
    ddir=data_dir();work=work_dir();ctx=holdout.load_holdout_context(ddir)
    x=np.load(work/'ssp1_features.npy',mmap_mode='r')
    if x.shape!=(*ctx.foot.shape,len(FEATURE_NAMES)):
        raise ValueError('Feature shape mismatch')
    print('Peer byte review and diagnostic controls',flush=True)
    peers=review(ROOT,ddir,ctx)
    print('Every feature alone: leakage canaries',flush=True)
    canary=canaries(x,ctx)
    if not canary['passed']:
        save_json('run_card.json',{'hypothesis':'SSP1','verdict':'negative','stop_reason':'Feature-only leakage canary failed','canary':canary,'slot_used':False})
        return
    print('Fit full-catalogue production surface, independently of all peer rasters',flush=True)
    full_model,full_fit=fit_model(x,ctx.labels,ctx.foot,20261026)
    surface=predict(full_model,x,ctx.foot)
    np.save(work/'ssp1_surface.npy',surface)
    manifest=json.loads((ROOT/'registry/all_rasters.json').read_text())
    print('Full registry surface check BEFORE any SSP1 dot placement',flush=True)
    surf=surface_guard(surface,ctx.foot,ddir/'sample_submission.tif',manifest,ROOT,ROOT/'evidence/surface_guard.json')
    if not surf['passed']:
        save_json('run_card.json',{'hypothesis':'SSP1','verdict':'negative','stop_reason':'Pre-placement surface duplicate or incomplete registry','surface_guard':{k:v for k,v in surf.items()if k!='rows'},'slot_used':False})
        return
    print('One frozen experiment: eight buffered hide-and-recover fits',flush=True)
    cells={};fits=[]
    for i,cell in enumerate(ctx.cells):
        test=(ctx.quad==cell.fold)
        collar=binary_dilation(test,structure=np.ones((3,3),bool),iterations=holdout.COLLAR_PX)
        train=ctx.foot&~collar
        visible=cell.visible_full
        if visible is None:
            raise ValueError('Missing fold-local visible catalogue')
        model,fit=fit_model(x,visible,train,20261027+i)
        if np.any((visible&train)&collar):
            raise AssertionError('Training crossed holdout collar')
        sub=predict(model,x[cell.bbox],cell.active_sub)
        n=round(BUDGET*int(cell.active_sub.sum())/int(ctx.foot.sum()))
        dots=priority_dots(sub,cell.active_sub,n)
        if np.any(dots&cell.visible_sub):
            raise AssertionError('Visible fault was not masked pixel-exactly')
        cells[cell.key]=dots
        fits.append({'cell':cell.key,**fit,'eligible_pixels':int(cell.active_sub.sum()),'emitted_dots':int(dots.sum()),'catalogue_feature_provenance':'none; labels used only for fold-visible supervision, visible-only negative sampling and exact visible mask','buffer_px':holdout.COLLAR_PX})
        print(f"  {cell.key}: {int(dots.sum())} dots, {fit['training_positive_pixels']} visible train positives",flush=True)
    np.savez_compressed(work/'ssp1_oof_masks.npz',**cells)
    hr=holdout.evaluate_hide_and_recover(cells,ctx,name='KANLER3-SSP1-E1')
    print(f"HOLDOUT-DTI {hr['evaluator_version']}: {hr['pooled_dti']:.6f} {hr['ci95_cluster_bootstrap']}",flush=True)
    # This comparison is deliberately diagnostic only: peer masks were stored
    # after their full-catalogue operations, not regenerated fold-locally.
    frozen=peers['metrics']['GEMSDOE32']
    deltas=hr['_boots']-frozen['_boots']
    paired_frozen={'label':'HOLDOUT-DTI DIAGNOSTIC; NOT PROMOTION EVIDENCE','evaluator_version':hr['evaluator_version'],'n_withheld_positives':hr['n_withheld_positives'],'delta':float(hr['pooled_dti']-frozen['pooled_dti']),'ci95':[float(np.percentile(deltas,2.5)),float(np.percentile(deltas,97.5))],'caveat':'Frozen Champion predictions are not a clean re-trained hide-and-recover comparator.'}
    print('Place the final fixed-budget dots, then STOP if final guard fails',flush=True)
    final=priority_dots(surface,ctx.foot&~ctx.labels,BUDGET)
    np.save(work/'ssp1_final_mask.npy',final)
    guard=final_guard(final,ctx.foot,ddir/'sample_submission.tif',manifest,surf,ROOT)
    # No more model fits, alternative budgets, or emissions are allowed after
    # this point. Writing a rejected research artifact is a negative deliverable.
    sg=holdout.evaluate_sgmc_with_ci(final,ctx,name='KANLER3-SSP1-E1')
    sg_raw={'label':'HOLDOUT-DTI / EXTERNAL-CATALOGUE DIAGNOSTIC','evaluator_version':sg['evaluator_version'],'n_withheld_positives':sg['n_withheld_positives'],'pooled_dti':sg['sgmc_raw_pooled_dti'],'ci95_cluster_bootstrap':sg['sgmc_raw_ci95'],'not_newly_withheld_training_truth':True,'caveat':'SGMC is another public fault catalogue, not organizer test truth. Template exclusion uses a three-iteration cross-shaped dilation, not a Euclidean 300 m disk. No prevalence-based leaderboard projection is used.'}
    note='KANLER3 SSP1 E1 | signed scarp-profile vs smooth null | fixed 37654 dots | negative; DO NOT SUBMIT'
    bundle=write_validated_submission(final,slug='kanler3-ssp1-e1-RESEARCH',candidate_meta={'candidate_id':'KANLER3-SSP1-E1','description':'New independently generated SSP1 profile-model raster; automated negative research deliverable, not a competition-slot recommendation','submission_note_zeros':note,'submission_note_nan':note,'slot_decision':'NEGATIVE-DO-NOT-SUBMIT','catalogue_hidden_mean':None,'catalogue_hidden_per_quadrant':None,'sgmc_prevalence_calibrated_dti':None,'drift_corrected_holdout_mean':None,'drift_corrected_per_quadrant':None},ddir=ddir,out_dir=ROOT/'docs/downloads')
    final_file=ROOT/'docs/downloads'/bundle['zeros_tif']['filename']
    file_new=all(bundle['zeros_tif']['sha256']!=r.get('sha256')for r in manifest['rasters'])
    decision=promotion({'declared_lane':True,'leakage_canaries':canary['passed'],'surface_unique':surf['passed'],'final_dots_unique':guard['passed'],'registry_snapshot_complete':surf['comparison_complete'] and manifest['n_failed']==0,'saved_bytes_valid':bundle['zeros_tif']['all_checks_passed'],'current_best_reproduced':False,'paired_holdout_improvement':False,'weekly_selector_approved':None})
    card={
      'schema_version':1,'generated_utc':datetime.now(timezone.utc).isoformat(),'experiment_id':'SSP1-E1','experiments_executed':1,'experiment_limit':3,'wall_seconds':round(time.monotonic()-STARTED,2),
      'hypothesis':'Residualized odd-symmetric topographic step profiles identify fault scarps beyond the current catalogue more specifically than generic ridge strength.',
      'mechanism':'Nine cross-normal elevation samples; tanh step templates residualized against a quadratic smooth-terrain null; tangent persistence, gravity alignment and independently derived LiDAR/radiometric nuisance controls; buffered HistGB ranking; no peer-raster blend.',
      'named_non_fault_process':'Alluvial-fan terrace or paleoshoreline break; road embankment; lithologic contact.',
      'method_lane':json.loads(prereg.read_text())['lane'],'lane_assignment_caveat':'Declared autonomously; the prompt omitted an explicit coordinator-assigned method paragraph.',
      'holdout_dti':score_record(hr),'holdout_full':strip_internal(hr),'paired_delta_vs_frozen_champion_diagnostic':paired_frozen,
      'current_best':json.loads((ROOT/'registry/upstream_best.json').read_text()),'paired_delta_vs_clean_current_best':None,
      'external_catalogue_diagnostic':sg_raw,'leakage_canary':canary,
      'registry':{'surface':{k:v for k,v in surf.items()if k!='rows'},'final_dots':guard,'file_sha_unique_in_snapshot':file_new,'dot_mask_sha256':mask_sha(final),'universe_sites':manifest['n_sites'],'universe_files':manifest['n_files'],'universe_unique_blobs':manifest['n_unique_blobs'],'scope':manifest['scope']},
      'lattice_feasibility':json.loads((ROOT/'evidence/lattice_feasibility.json').read_text()),
      'raster_sha256':bundle['zeros_tif']['sha256'],'validator_output':bundle['zeros_tif'],'nan_twin_validator':bundle['nan_tif'],
      'submission_name':'KANLER3-SSP1-E1-'+bundle['content_digest8'].upper(),'submission_note':note,'note_characters':len(note),
      'downloads':{'tif':bundle['zeros_tif']['filename'],'zip':bundle['zeros_zip']['filename'],'nan_twin':bundle['nan_tif']['filename']},
      'verdict':decision['verdict'],'decision':decision,'leaderboard_estimate':None,'organizer_confirmed_submission_score':None,'organizer_receipt':None,
      'stop_reason':'Final literal registry duplicate: stop without changing placement or method. No clean current-best paired comparison or selector approval exists.',
      'next_experiment_allowed_in_this_run':False,'full_training':full_fit,'fold_training':fits,'input_preregistration_sha256':expected,'raster_is_copied_peer_submission':False,
      'limitations':['The highest hidden leaderboard result cannot be guaranteed from public labels.','Official data binaries were not freshly authenticated against DrivenData; owner-mirror SHA-256 checks establish mirror identity, not organizer authenticity.','No DrivenData session, submission receipt or authenticated weekly cap/usage is available.','Feature AUC and a spatial bootstrap do not eliminate public-to-new-fault distribution shift.']
    }
    save_json('run_card.json',card);save_json('submission_bundle.json',bundle)
    print(json.dumps({'verdict':card['verdict'],'tif':str(final_file),'sha256':card['raster_sha256'],'ok_to_submit':decision['ok_to_submit'],'stop_reason':card['stop_reason']},indent=2),flush=True)

if __name__=='__main__':
    main()
