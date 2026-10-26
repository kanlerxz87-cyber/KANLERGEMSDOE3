import numpy as np
import pytest
from gems_project.features import texture_features


def test_constant_profiles_have_no_artificial_offset():
    shape=(20,22); fp=np.ones(shape,bool); a=np.full(shape,128,np.uint8)
    x,s=texture_features(fp,a,a,a,a,a,a,chunk_size=75)
    assert np.isfinite(x).all()
    assert np.max(x[:,6:])==0
    assert not s.reshape(shape)[0,0]
    assert s.reshape(shape)[10,11]


def test_shifted_two_band_profiles_have_positive_agreed_lag():
    h=w=35; fp=np.ones((h,w),bool)
    # Vary smoothly along east-west strike; shift the southern flank by 2 px.
    source=np.tile(np.array([30,35,50,100,150,200,220,200,150,100,50,35],dtype=np.uint8),3)[:w]
    k=np.tile(source,(h,1)); th=k.copy()
    k[18:]=np.roll(k[18:],2,axis=1); th[18:]=np.roll(th[18:],2,axis=1)
    q=np.full((h,w),128,np.uint8); valid=np.full((h,w),255,np.uint8)
    x,s=texture_features(fp,k,th,q,q,q,valid,chunk_size=500)
    center=17*w+14
    assert s[center]
    assert x[center,6]>0 and x[center,7]>0 and x[center,8]>0


def test_incomplete_or_invalid_samples_never_wrap():
    shape=(20,20); fp=np.ones(shape,bool); a=np.full(shape,100,np.uint8); broken=a.copy();broken[10,10]=0
    x,s=texture_features(fp,a,broken,a,a,a,a)
    assert not s.reshape(shape)[0,0]
    assert np.isfinite(x).all()
    with pytest.raises(ValueError): texture_features(fp,a.astype(float),a,a,a,a,a)
