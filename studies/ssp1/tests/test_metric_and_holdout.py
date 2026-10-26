from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scipy.ndimage import label
from gems32.metric import dti_exact,dti_binary,kernel
from gems32 import holdout


def test_kernel_matches_official_300m_support():
    assert np.allclose(kernel(np.array([0,1,2,3,4])),[1,2/3,1/3,0,0])


@pytest.mark.parametrize('seed',range(5))
def test_binary_fast_metric_matches_exact_probability_formula(seed):
    rng=np.random.default_rng(seed)
    pred=rng.random((19,22))<0.04;truth=rng.random(pred.shape)<0.04
    valid=rng.random(pred.shape)>0.1;known=rng.random(pred.shape)<0.03
    a=dti_exact(pred.astype(float),truth,valid,known)
    b=dti_binary(pred,truth,valid,known)
    for key in ['tp','fp','fn','dti']:
        assert a[key]==pytest.approx(b[key],abs=1e-10)


def test_known_faults_are_pixel_exact_not_buffer_masked():
    p=np.zeros((12,12));g=np.zeros_like(p,bool);known=g.copy()
    p[5,5]=1;known[5,5]=True;g[5,6]=True
    r=dti_exact(p,g,known=known)
    assert r['tp']==0
    p[5,6]=1
    assert dti_exact(p,g,known=known)['dti']==pytest.approx(1)


def test_probability_range_rejected_not_silently_clipped_by_metric():
    p=np.zeros((7,7));g=np.zeros_like(p)
    p[3,3]=-0.001
    with pytest.raises(ValueError):dti_exact(p,g)
    p[3,3]=1.001
    with pytest.raises(ValueError):dti_exact(p,g)
    p[3,3]=np.nan
    with pytest.raises(ValueError):dti_exact(p,g)


def make_context(tmp_path):
    shape=(100,100);foot=np.ones(shape,bool);labels=np.zeros(shape,np.uint8)
    # Separated whole segments in every spatial quadrant, away from the eroded rim.
    for y in [15,25,65,75]:
        for x in [16,26,66,76]:
            labels[y:y+8,x]=1
    profile={'driver':'GTiff','height':100,'width':100,'count':1,'dtype':'float32','crs':'EPSG:32611','transform':from_origin(243350,4508550,100,100),'nodata':np.nan}
    (tmp_path/'external').mkdir()
    for name,a in [('sample_submission.tif',foot.astype(float)),('labels.tif',labels),('external/derived_sgmc_faults_100m_u8.tif',np.zeros(shape))]:
        with rasterio.open(tmp_path/name,'w',**profile)as ds:ds.write(a.astype(np.float32),1)
    return holdout.load_holdout_context(tmp_path),labels


def test_hide_recover_withholds_whole_components_and_only_masks_visible(tmp_path):
    ctx,labels=make_context(tmp_path)
    components,n=label(labels,structure=np.ones((3,3),int))
    masks={}
    for cell in ctx.cells:
        for comp in range(1,n+1):
            trace=components==comp
            v=cell.visible_full[trace]
            assert v.all() or not v.any()
        truth=np.zeros(cell.active_sub.shape,bool);truth[cell.truth_coords]=True
        assert not np.any(truth&cell.visible_sub)
        assert not np.any(cell.active_sub&cell.visible_sub)
        masks[cell.key]=truth
    result=holdout.evaluate_hide_and_recover(masks,ctx,n_boot=20)
    assert result['n_withheld_positives']>0
    assert result['pooled_dti']==pytest.approx(1)
    assert result['ci95_cluster_bootstrap']==pytest.approx([1,1])
    empty=holdout.evaluate_hide_and_recover(np.zeros(ctx.foot.shape,bool),ctx,n_boot=20)
    assert empty['pooled_dti']==0
    assert empty['n_withheld_positives']==result['n_withheld_positives']
