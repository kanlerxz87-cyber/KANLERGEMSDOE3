import numpy as np
import rasterio
from rasterio.transform import from_origin
from validate_submission import validate


def write(path, values, nodata=None):
    values=np.asarray(values,dtype=np.float32)
    with rasterio.open(path,'w',driver='GTiff',height=values.shape[0],width=values.shape[1],
                       count=1,dtype='float32',crs='EPSG:32611',
                       transform=from_origin(100,200,100,100),nodata=nodata) as out:
        out.write(values,1)


def test_infinite_exterior_is_not_null(tmp_path):
    ref=tmp_path/'ref.tif'; candidate=tmp_path/'pred.tif'
    write(ref, [[float('nan'),0],[0,0]], nodata=float('nan'))
    write(candidate, [[float('inf'),0],[0,0]])
    result=validate(ref,candidate)
    assert not result['ok']
    assert result['infinite_outside_footprint']==1


def test_empty_reference_cannot_pass(tmp_path):
    ref=tmp_path/'ref.tif'; candidate=tmp_path/'pred.tif'
    write(ref, [[float('nan')]*2]*2,nodata=float('nan'))
    write(candidate, [[float('nan')]*2]*2,nodata=float('nan'))
    result=validate(ref,candidate)
    assert not result['ok']
    assert 'reference footprint is empty' in result['errors']


def test_reference_nan_without_nodata_tag_is_outside_footprint(tmp_path):
    ref=tmp_path/'ref.tif'; candidate=tmp_path/'pred.tif'
    write(ref, [[float('nan'),0],[0,0]])
    write(candidate, [[float('nan'),0],[0,1]],nodata=float('nan'))
    result=validate(ref,candidate)
    assert result['ok'] and result['footprint_pixels']==3
