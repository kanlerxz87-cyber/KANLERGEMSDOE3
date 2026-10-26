"""Synthetic tests for unchanged shared components; never count as model runs."""
import sys
import importlib
import importlib.util
from pathlib import Path
import tempfile
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT=Path(__file__).resolve().parents[1]
# Load the 7ab1c8f template under a unique package name. A concurrent lane
# vendors a different, equally pinned gems package at src/gems; Python's
# sys.modules cache would otherwise silently test whichever was imported first.
locked=ROOT/'.cache/template/GEMSDOE24/src/gems'
if not (locked/'__init__.py').is_file():
    pytest.skip('Install locked shared template before these optional tests',allow_module_level=True)
spec=importlib.util.spec_from_file_location('_locked_gems24',locked/'__init__.py',
                                          submodule_search_locations=[str(locked)])
pkg=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=pkg
spec.loader.exec_module(pkg)
holdout=importlib.import_module('_locked_gems24.holdout')
metric=importlib.import_module('_locked_gems24.metric')
submission=importlib.import_module('_locked_gems24.submission')
write_submission,check_variants=submission.write_submission,submission.check_variants
sys.path.insert(0,str(ROOT/'.cache/template/GEMSDOE32/vendor'))
try:
    from gems57 import evaluate_holdout
except ModuleNotFoundError:
    pytest.skip('Install locked shared evaluator before these optional tests',allow_module_level=True)


def brute_terms(prob,truth,active,radius=3):
    """Independent small-grid definition (not a production evaluator)."""
    gt=np.argwhere(truth & active); pred=np.argwhere((prob>0)&active)
    tp=0.
    for g in gt:
        tp+=max((float(prob[tuple(p)])*max(0.,1.-np.linalg.norm(g-p)/radius) for p in pred),default=0.)
    fp=0.
    for p in pred:
        reach=max((max(0.,1.-np.linalg.norm(p-g)/radius) for g in gt),default=0.)
        fp+=float(prob[tuple(p)])*(1.-reach)
    return tp,fp,len(gt)-tp


def test_shared_metric_matches_independent_probability_definition():
    rng=np.random.default_rng(612)
    for _ in range(5):
        a=(rng.random((12,11))<.08)*rng.random((12,11))
        y=rng.random((12,11))<.09
        valid=rng.random((12,11))>.1
        visible=rng.random((12,11))<.05
        active=valid & ~visible
        expected=brute_terms(a,y,active)
        got=metric.dti_components_exact(a, y & active, valid_mask=valid, catalogue_mask=visible)
        assert np.allclose([got['TP_w'],got['FP_w'],got['FN_w']],expected,atol=1e-8)
        f={'region':valid,'visible':visible,'truth':y & active}
        result,terms=evaluate_holdout.evaluate(a,f,valid,block_side=4,origin=(0,0),global_shape=valid.shape)
        assert np.allclose(terms.sum(axis=0)[:3],expected,atol=1e-8)
        assert np.isclose(result['dti'],got['dti'],atol=1e-8)


def test_hidden_segments_and_canary_fail_on_labels():
    fp=np.ones((100,100),bool);lab=np.zeros_like(fp)
    for row,col in [(20,20),(20,70),(70,20),(70,70)]: lab[row:row+4,col]=1
    ctx=holdout.SegmentHoldout(fp,lab,buffer_px=3)
    for fold in ctx.folds:
        assert not np.any(fold['train'] & fold['valid'])
        assert not np.isin(ctx.components[fold['visible']],fold['hidden_component_ids']).any()
    c=ctx.canary({'deliberately_leaky_label':lab.astype(float)},max_per_class=100,seed=7)
    assert not c['passed']
    assert c['features']['deliberately_leaky_label']['pooled_auc']>.9


def test_canonical_writer_serializes_and_rejects_invalid_inside():
    with tempfile.TemporaryDirectory() as d:
        ref=Path(d)/'template.tif'; out=Path(d)/'smoke-not-a-submission.tif'
        profile=dict(driver='GTiff',width=10,height=8,count=1,dtype='float32',crs='EPSG:32611',transform=from_origin(0,800,100,100))
        template=np.zeros((8,10),np.float32);template[0,0]=np.nan
        with rasterio.open(ref,'w',**{**profile,'nodata':np.nan}) as ds:ds.write(template,1)
        fp=np.ones((8,10),bool);fp[0,0]=False
        a=np.zeros((8,10),np.float32);a[2,3]=.75;a[0,0]=np.nan
        result=write_submission(a,ref,out)  # shared default is outside='zero'
        with rasterio.open(out) as ds:
            actual=ds.read(1)
            assert ds.count==1 and ds.dtypes[0]=='float32' and ds.transform==profile['transform']
            assert np.isfinite(actual).all() and actual[0,0]==0 and actual[2,3]==.75
        # The shared writer's local default and strict official-mask policy disagree.
        from scripts.validate_submission import validate
        assert not validate(ref,out)['ok']
        shared=check_variants(out,ref)['checks']['outside_is_nan_official_text']
        assert not shared['pass'] and not shared['hard_requirement']
        nan_out=Path(d)/'official-mask-smoke-not-a-submission.tif'
        write_submission(a,ref,nan_out,outside='nan')
        assert validate(ref,nan_out)['ok']
        for invalid in [np.nan,-.01,1.01,np.inf]:
            b=a.copy();b[2,3]=invalid
            with pytest.raises(ValueError):write_submission(b,ref,out,outside='zero')


def test_other_pinned_writer_defaults_to_nan_exterior():
    # The earlier fc2bc6f pin is not interchangeable with the 7ab1c8f pin.
    old_path=ROOT/'src/gems'
    old_spec=importlib.util.spec_from_file_location('_vendored_gems24_fc2',old_path/'__init__.py',
                                                   submodule_search_locations=[str(old_path)])
    old_pkg=importlib.util.module_from_spec(old_spec)
    sys.modules[old_spec.name]=old_pkg
    old_spec.loader.exec_module(old_pkg)
    older_writer=importlib.import_module('_vendored_gems24_fc2.submission').write_submission
    with tempfile.TemporaryDirectory() as d:
        ref=Path(d)/'template.tif';out=Path(d)/'old-writer-smoke.tif'
        profile=dict(driver='GTiff',width=3,height=3,count=1,dtype='float32',
                     crs='EPSG:32611',transform=from_origin(0,300,100,100),nodata=np.nan)
        a=np.zeros((3,3),np.float32);a[0,0]=np.nan
        with rasterio.open(ref,'w',**profile) as ds:ds.write(a,1)
        older_writer(a,ref,out)
        with rasterio.open(out) as ds: assert np.isnan(ds.read(1)[0,0])
