import json
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

import verify_submission as wrapper

try:
    from gems57.gates import format_report
    import gems57.validate as shared_validate
    HAVE_TEMPLATE = True
except ImportError:
    HAVE_TEMPLATE = False

pytestmark = pytest.mark.skipif(not HAVE_TEMPLATE, reason='Restore the pinned shared template first')


def write_raster(path, data, *, dtype='float32', crs='EPSG:32611', transform=None, nodata=None):
    a=np.asarray(data, dtype=dtype)
    if a.ndim==2: a=a[None, ...]
    with rasterio.open(path,'w',driver='GTiff',height=a.shape[1],width=a.shape[2],count=a.shape[0],
                       dtype=dtype,crs=crs,transform=transform or from_origin(100,200,100,100),nodata=nodata) as dst:
        dst.write(a)


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    cache=tmp_path/'cache'; (cache/'data').mkdir(parents=True)
    sample=cache/'data/sample_submission.tif'; catalogue=cache/'data/existing_faults.tif'
    sample_values=np.zeros((4,5),np.float32);sample_values[0,0]=np.nan
    labels=np.zeros((4,5),np.float32);labels[2,2]=1
    write_raster(sample,sample_values,nodata=np.nan);write_raster(catalogue,labels)
    monkeypatch.setattr(wrapper,'restore',lambda *a,**k: None)
    monkeypatch.setattr(shared_validate, 'HEIGHT', 4)
    monkeypatch.setattr(shared_validate, 'WIDTH', 5)
    monkeypatch.setattr(shared_validate, 'TRANSFORM', from_origin(100,200,100,100))
    return cache,sample,tmp_path


def test_valid_saved_bytes_and_known_positive_are_not_format_error(tiny):
    cache,sample,tmp=tiny
    # Full-rectangle sample allows both local exterior policies to agree.
    write_raster(sample,np.zeros((4,5),np.float32))
    a=np.zeros((4,5),np.float32);a[2,2]=1
    candidate=tmp/'candidate.tif';write_raster(candidate,a)
    result=wrapper.run(candidate,sample,cache)
    assert result['local_format_ok'] and not result['submit_approved']
    assert result['positive_known_fault_pixels_informational']==1


@pytest.mark.parametrize('value', [np.nan,np.inf,-1,1.001,-3.4028235e38])
def test_invalid_inside_footprint_never_passes(tiny, value):
    cache,sample,tmp=tiny
    a=np.zeros((4,5),np.float32);a[1,1]=value
    candidate=tmp/'invalid.tif';write_raster(candidate,a,nodata=np.nan if np.isnan(value) else None)
    result=wrapper.run(candidate,sample,cache)
    assert not result['local_format_ok']
    # A NaN declared as nodata must not make JSON output fail.
    json.dumps(wrapper.json_safe(result), allow_nan=False)


def test_nan_outside_fails_shared_stricter_policy(tiny):
    cache,sample,tmp=tiny
    a=np.zeros((4,5),np.float32);a[0,0]=np.nan
    candidate=tmp/'outside.tif';write_raster(candidate,a,nodata=np.nan)
    result=wrapper.run(candidate,sample,cache)
    assert result['reference_footprint_null_policy_ok']
    assert not result['shared_all_finite_policy_ok']
    assert result['policies_disagree'] and not result['local_format_ok']


def test_finite_exterior_is_shared_pass_but_reference_mask_failure(tiny):
    cache,sample,tmp=tiny
    candidate=tmp/'finite-exterior.tif';write_raster(candidate,np.zeros((4,5),np.float32))
    result=wrapper.run(candidate,sample,cache)
    assert result['shared_all_finite_policy_ok']
    assert not result['reference_footprint_null_policy_ok']
    assert result['policies_disagree'] and not result['local_format_ok']


@pytest.mark.parametrize('kind',['shape','crs','transform','dtype','bands'])
def test_grid_band_and_dtype_mismatch_fail_closed(tiny, kind):
    cache,sample,tmp=tiny
    a=np.zeros((4,5),np.float32);kw={}
    if kind=='shape': a=np.zeros((5,5),np.float32)
    if kind=='crs': kw['crs']='EPSG:4326'
    if kind=='transform': kw['transform']=from_origin(101,200,100,100)
    if kind=='dtype': kw['dtype']='float64'
    if kind=='bands': a=np.zeros((2,4,5),np.float32)
    candidate=tmp/'invalid-grid.tif';write_raster(candidate,a,**kw)
    result=wrapper.run(candidate,sample,cache)
    assert not result['local_format_ok']
    assert result['report']['problems']


def test_nodata_zero_masks_valid_cells_even_though_values_are_in_range(tiny):
    cache,sample,tmp=tiny
    a=np.zeros((4,5),np.float32);a[2,2]=1
    candidate=tmp/'zero-nodata.tif';write_raster(candidate,a,nodata=0)
    result=wrapper.run(candidate,sample,cache)
    assert result['report']['ok']  # The shared raw-numeric check alone misses the mask.
    assert result['masked_inside_footprint'] > 0
    assert not result['local_format_ok']
