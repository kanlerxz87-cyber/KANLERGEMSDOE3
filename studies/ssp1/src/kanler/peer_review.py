"""Nine-site byte-level review. Historical claims are never verified receipts."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from .audit import read_comparable, normalized_ranks, rank_correlation, within3, sha256, mask_sha
from gems32 import holdout

# Reported values were supplied in the user's brief, not inferred from a model.
SITES=[
 ('GEMSDOE24','gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif',0.2477,'Dense H19-5 ridge-family dots; less thinning than D2.8.'),
 ('GEMSDOE25','gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif',0.2600,'D2.8-thinned H19-5 family; geometric efficiency, not an independent discovery model.'),
 ('GEMSDOE27','gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif',0.2449,'Topographic gap-closure on D1.5; reported result does not improve on its parent.'),
 ('GEMSDOE28','gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif',0.2710,'Best reported of four close variants; rung30 on the solo/D2.8 family.'),
 ('GEMSDOE30','gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif',0.2600,'D2.8 reproduction; pixel identity must be checked, not inferred from its name.'),
 ('GEMSDOE31','gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif',0.2708,'Solo D2.8 reproduction; not independent evidence of new fault physics.'),
 ('GEMSDOE32','gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif',0.2778,'H33-2 B2: test whether its mask is exactly the D2.8 parent outside a 2 px known-fault collar.'),
 ('GEMSDOE33','GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif',0.2632,'Analogue tip/stepover method; its geological interpretation is not established by a file name.'),
 ('GEMSDOE36','gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif',0.2750,'Anderson/geothermal-PINN named artifact; compare actual pixels with the shared family before accepting independence.')
]


def strip_internal(d):
    return {k:v for k,v in d.items()if not k.startswith('_')}


def find_row(rows,site,suffix):
    hits=[r for r in rows if r['site']==site and r['path'].endswith('/'+suffix)]
    if len(hits)!=1:
        raise ValueError(f'Expected one pinned raster for {site}/{suffix}, got {len(hits)}')
    return hits[0]


def review(root: Path,ddir: Path,ctx) -> dict:
    manifest=json.loads((root/'registry/rasters.json').read_text())
    masks={};records=[];reference_metrics={}
    template=ddir/'sample_submission.tif'
    for site,suffix,claim,method in SITES:
        row=find_row(manifest['rasters'],site,suffix);path=root/row['local']
        if sha256(path)!=row['sha256']:
            raise ValueError('Peer artifact checksum mismatch')
        a,meta=read_comparable(path,template,ctx.foot);m=(a>0)&ctx.foot;masks[site]=m
        hr=holdout.evaluate_hide_and_recover(m,ctx,name=site+'_FROZEN_RASTER_DIAGNOSTIC')
        reference_metrics[site]=hr
        records.append({'site':site,'filename':suffix,'source_path':row['path'],'commit':row['commit'],'download_url':f"https://github.com/buffedlizard55-lab/{site}/raw/{row['commit']}/{row['path']}",'sha256':row['sha256'],'mask_sha256':mask_sha(m),'historical_claim':{'label':'USER-REPORTED / NOT ORGANIZER-CONFIRMED','value':claim,'receipt':None,'not_promotion_evidence':True},'method':method,'dots':int(m.sum()),'on_catalogue':int((m&ctx.labels).sum()),'format_facts':meta,'frozen_raster_diagnostic':strip_internal(hr),'holdout_caveat':'This persisted historical raster may already exclude the full catalogue or have been trained on these labels. This diagnostic is NOT a clean model-level hide-and-recover estimate and is never used for promotion.','leaderboard_estimate':None,'already_used_or_reproduced':True})
        print(f'Peer {site}: {int(m.sum())} dots; frozen diagnostic only',flush=True)
    pairs=[]
    for i,(sa,*_) in enumerate(SITES):
        ranks=normalized_ranks(masks[sa][ctx.foot].astype(np.float32))
        for sb,*_ in SITES[i+1:]:
            ma,mb=masks[sa],masks[sb]
            rho=rank_correlation(ranks,mb[ctx.foot].astype(np.float32))
            ov_ab=within3(ma,mb);ov_ba=within3(mb,ma)
            pairs.append({'a':sa,'b':sb,'same_dot_mask':bool(np.array_equal(ma,mb)),'spearman':rho,'a_within_3px_of_b':ov_ab,'b_within_3px_of_a':ov_ba,'lane_duplicate':bool((rho is not None and abs(rho)>0.90)or(ov_ab is not None and ov_ab>0.70)or(ov_ba is not None and ov_ba>0.70))})
    for r in records:
        site=r['site'];touch=[p for p in pairs if site in(p['a'],p['b'])]
        r['exact_mask_twins']=[p['b']if p['a']==site else p['a']for p in touch if p['same_dot_mask']]
        r['lane_distinct_from_all_other_priority_sites']=not any(p['lane_duplicate']for p in touch)
        overlaps=[(p['a_within_3px_of_b'] if p['a']==site else p['b_within_3px_of_a'],p['b']if p['a']==site else p['a'])for p in touch]
        r['max_directional_overlap'],r['nearest_priority_site']=max(overlaps)
    dcat=distance_transform_edt(~ctx.labels)
    d28=masks['GEMSDOE25'];champ=masks['GEMSDOE32'];anderson=masks['GEMSDOE36']
    solo_suffix='gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif'
    sr=find_row(manifest['rasters'],'GEMSDOE28',solo_suffix)
    a,_=read_comparable(root/sr['local'],template,ctx.foot);solo=(a>0)&ctx.foot
    anatomy={'champion_equals_d28_outside_2px':bool(np.array_equal(champ,d28&(dcat>2))),'champion_equals_solo_outside_2px':bool(np.array_equal(champ,solo&(dcat>2))),'solo_equals_d28_outside_1px':bool(np.array_equal(solo,d28&(dcat>1))),'site31_equals_site28_solo':bool(np.array_equal(masks['GEMSDOE31'],solo)),'site30_equals_site25':bool(np.array_equal(masks['GEMSDOE30'],d28)),'champion_subset_of_anderson':bool(not np.any(champ&~anderson)),'anderson_extra_vs_champion':int((anderson&~champ).sum()),'d28_dots':int(d28.sum()),'solo_dots':int(solo.sum()),'champion_dots':int(champ.sum()),'removed_d28_to_champion':int((d28&~champ).sum()),'new_dots_vs_d28':int((champ&~d28).sum()),'all_removed_dots_within_2px_catalogue':bool(np.all(dcat[d28&~champ]<=2)),'causal_limit':'Without organizer truth or controlled receipts, the higher reported result cannot be causally assigned to this collar. Known traces alone are masked officially; a 200 m collar is not an official masking rule.'}
    out={'sites':records,'pairwise':pairs,'champion_anatomy':anatomy,'score_policy':'Historical numbers remain unverified claims. HOLDOUT-DTI frozen-raster diagnostics carry their evaluator, withheld-positive count and 95% CI but do not estimate leaderboard performance.','current_best_reproducible_from_saved_rasters':False}
    (root/'evidence/nine_site_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    return {'report':out,'masks':masks,'metrics':reference_metrics}
