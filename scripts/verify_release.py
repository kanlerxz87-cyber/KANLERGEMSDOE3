#!/usr/bin/env python3
"""Independent saved-byte, evidence, gate, OOF, and site-link verification.

Runs offline in CI from compact validation masks + recorded template geometry.
When the restored data is present, also re-evaluates the retained OOF masks with
THE shared evaluator and independently repeats the final-dot overlap measurement.
This script cannot turn a negative scientific result into a submission approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import Affine
from gems32.submission import audit_geotiff
from gems32 import holdout
from kanler.audit import sha256,mask_sha,within3,read_comparable
from kanler.gates import promotion,score_record

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.lang=False;self.main=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html':self.lang=a.get('lang')=='en'
        if tag=='main':self.main=True
        if 'id'in a:self.ids.add(a['id'])
        for k in ('href','src'):
            if k in a:self.links.append(a[k])


def check_links(docs:Path):
    parsed={}
    for path in docs.rglob('*.html'):
        p=Links();p.feed(path.read_text());parsed[path.resolve()]=p
        assert p.lang and p.main,f'Missing language/main landmark: {path}'
    checked=0
    for path,doc in parsed.items():
        for link in doc.links:
            parts=urlsplit(link)
            if parts.scheme or parts.netloc:continue
            target=(path.parent/unquote(parts.path)).resolve()if parts.path else path
            assert target.is_relative_to(docs.resolve()),f'Link escapes Pages: {path} -> {link}'
            if target.is_dir():target/= 'index.html'
            assert target.exists(),f'Broken local link: {path.name} -> {link}'
            if parts.fragment and target.suffix=='.html':
                assert unquote(parts.fragment) in parsed[target]['ids'],f'Broken anchor: {link}'
            checked+=1
    return {'html_pages':len(parsed),'internal_links_and_assets_checked':checked}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true',help='Verify only published compact evidence, without restored inputs')
    args=parser.parse_args()
    checks={};details={}
    def require(name,condition):
        checks[name]=bool(condition)
        if not condition:raise AssertionError(name)
    c=json.loads((ROOT/'evidence/run_card.json').read_text())
    bundle=json.loads((ROOT/'evidence/submission_bundle.json').read_text())
    geom=json.loads((ROOT/'evidence/input_geometry_audit.json').read_text())
    # Make the self-link resolvable while verification is running; never write a
    # success marker before all checks finish.
    dest=ROOT/'docs/data/verification.json'
    dest.write_text(json.dumps({'status':'RUNNING, NOT YET VERIFIED'})+'\n')
    require('primary_metric_labeled',score_record(c['holdout_dti'])['label']=='HOLDOUT-DTI')
    require('one_experiment_stopped_on_duplicate',c['experiments_executed']==1 and not c['next_experiment_allowed_in_this_run'])
    require('note_within_140_characters',len(c['submission_note'])<=140)
    require('no_leaderboard_projection_written_as_score',c['leaderboard_estimate']is None and c['organizer_confirmed_submission_score']is None)
    require('no_slot_used',c['decision']['slot_used']is False)
    expected=promotion(c['decision']['gates'])
    require('decision_is_fail_closed_and_consistent',expected['verdict']==c['verdict']and expected['ok_to_submit']==c['decision']['ok_to_submit'])
    masks=ROOT/'docs/data/validation_masks.npz'
    require('published_validation_masks_hash',sha256(masks)==geom['validation_masks_sha256'])
    with np.load(masks)as z:foot=z['footprint'];known=z['catalogue']
    require('published_oof_masks_hash',sha256(ROOT/'evidence/ssp1_oof_masks.npz')==geom['oof_masks_sha256'])
    require('footprint_count',int(foot.sum())==c['validator_output']['in_footprint_finite_pixels'])
    profile={'driver':'GTiff','height':geom['template']['shape'][0],'width':geom['template']['shape'][1],'count':1,'dtype':'float32','crs':geom['template']['crs'],'transform':Affine(*geom['template']['transform']),'nodata':np.nan,'tiled':True,'compress':'deflate'}
    with MemoryFile()as mem:
        with mem.open(**profile):pass
        zero=ROOT/'docs/downloads'/c['downloads']['tif'];nan=ROOT/'docs/downloads'/c['downloads']['nan_twin']
        z_audit=audit_geotiff(zero,foot,known,mode='zeros',template_tif=Path(mem.name))
        n_audit=audit_geotiff(nan,foot,known,mode='nan',template_tif=Path(mem.name))
    require('zero_tiff_exact_sha',z_audit['sha256']==c['raster_sha256'])
    require('nan_tiff_exact_sha',n_audit['sha256']==c['nan_twin_validator']['sha256'])
    require('both_shared_saved_byte_audits_pass',z_audit['all_checks_passed']and n_audit['all_checks_passed'])
    with rasterio.open(zero)as ds:final=(ds.read(1)>0)&foot
    require('recorded_dot_mask_hash',mask_sha(final)==c['registry']['dot_mask_sha256'])
    zip_path=ROOT/'docs/downloads'/c['downloads']['zip']
    with zipfile.ZipFile(zip_path)as zf:
        require('zip_contains_exactly_one_tif',zf.namelist()==[zero.name])
        require('zip_tif_bytes_identical',hashlib.sha256(zf.read(zero.name)).hexdigest()==c['raster_sha256'])
    require('zip_hash_matches_bundle',sha256(zip_path)==bundle['zeros_zip']['sha256'])
    legacy=bundle['holdout_metrics']
    require('unmeasured_legacy_metrics_are_null',all(legacy[k]is None for k in ('catalogue_hidden_mean','sgmc_prevalence_calibrated_dti','drift_corrected_holdout_mean')))
    surf=json.loads((ROOT/'evidence/surface_guard.json').read_text())
    require('surface_inventory_count_consistent',surf['n_checked_files']==surf['n_manifest_files']==2729)
    require('quarantines_cannot_pass_universal_comparison',not surf['n_quarantined']or(c['decision']['gates']['surface_unique']is False and c['decision']['gates']['registry_snapshot_complete']is False))
    require('pixel_novelty_scoped_to_comparable_snapshot',c['registry']['final_dots']['exact_dot_mask_unique_within_comparable_snapshot'] and not c['registry']['final_dots']['exact_dot_mask_matches'])
    pins=json.loads((ROOT/'registry/template_pins.json').read_text())
    require('shared_tools_not_privately_forked',all(sha256(ROOT/r['path'])==r['sha256']for r in pins['files']))
    require('frozen_preregistration_hash',sha256(ROOT/'registry/hypotheses.json')==(ROOT/'evidence/preregistration_sha256.txt').read_text().split()[0])
    details['geometry_validation_basis']='Recorded owner-mirror template geometry + published integrity-pinned footprint/catalogue masks; NOT fresh organizer authentication'
    details['format_checks']=z_audit['checks']
    # Data are deliberately not committed. Only a local restored workspace can
    # make these additional reproducibility checks; CI states that scope.
    ddir=ROOT/'.cache/gems_data'
    if not args.offline and all((ddir/f).exists()for f in ['labels.tif','sample_submission.tif','external/derived_sgmc_faults_100m_u8.tif']):
        ctx=holdout.load_holdout_context(ddir)
        with np.load(ROOT/'evidence/ssp1_oof_masks.npz')as z:cells={k:z[k]for k in z.files}
        result=holdout.evaluate_hide_and_recover(cells,ctx,name='SSP1-INDEPENDENT-REEVALUATION')
        require('shared_oof_dti_reproduced',abs(result['pooled_dti']-c['holdout_dti']['pooled_dti'])<1e-12)
        require('shared_oof_ci_reproduced',np.allclose(result['ci95_cluster_bootstrap'],c['holdout_dti']['ci95_cluster_bootstrap'],rtol=0,atol=1e-12))
        require('shared_oof_positive_count_reproduced',result['n_withheld_positives']==c['holdout_dti']['n_withheld_positives'])
        registry=json.loads((ROOT/'registry/all_rasters.json').read_text())
        viol=c['registry']['final_dots']['checks'][0]
        row=next(r for r in registry['rasters']if r['site']==viol['site']and r['path']==viol['path'])
        ref,meta=read_comparable(ROOT/row['local'],ddir/'sample_submission.tif',foot)
        measured=within3(final,(ref>0)&foot)
        require('final_dot_overlap_independently_reproduced',abs(measured-viol['fraction_candidate_dots_within_3px'])<1e-12)
        details['oof_recheck']={'scope':'Restored local inputs + saved OOF masks; full shared-evaluator rerun','HOLDOUT-DTI':result['pooled_dti'],'evaluator_version':result['evaluator_version'],'n_withheld_positives':result['n_withheld_positives'],'ci95_cluster_bootstrap':result['ci95_cluster_bootstrap']}
    else:
        details['oof_recheck']={'scope':'Offline CI: original restored inputs not present; synthetic evaluator tests and published OOF hash only. No claim of a fresh real-data reevaluation.'}
    links=check_links(ROOT/'docs');details['site']=links
    for page in ['index.html','executive-summary.html','submission-guide.html','audit.html']:
        text=(ROOT/'docs'/page).read_text()
        require(page+'_rejects_upload',('do not upload' in text.lower()or 'do not submit' in text.lower())and c['downloads']['tif']in text)
    require('no_generated_or_data_file_over_8MB',not any(p.is_file()and p.stat().st_size>8_000_000 for base in ['docs','evidence','registry','src','scripts']for p in (ROOT/base).rglob('*')if '__pycache__'not in p.parts))
    out={'status':'PASS — technical/reproducibility verification, NOT a scientific promotion','verified_utc':datetime.now(timezone.utc).isoformat(),'scientific_verdict':c['verdict'],'ok_to_submit':False,'checks':checks,'details':details,'raster_sha256':c['raster_sha256']}
    (ROOT/'evidence/verification.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    dest.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    try:main()
    except (AssertionError,ValueError,KeyError,FileNotFoundError)as exc:
        print(f'RELEASE VERIFICATION FAILED: {exc}',file=sys.stderr)
        raise SystemExit(1)
