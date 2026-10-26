import numpy as np
import pytest
from scipy.spatial.distance import pdist
from kanler.science import OFFSETS, profile_statistics, residual_projection, priority_dots, encoded_lidar


def test_projection_annihilates_smooth_null():
    t=OFFSETS
    q=residual_projection()
    assert np.allclose(q@q,q)
    assert np.allclose(q@np.stack([np.ones(9),t,t*t],axis=1),0,atol=1e-12)


def test_step_vs_symmetric_ridge():
    t=OFFSETS
    step=profile_statistics(np.tanh(t/0.7))
    ridge=profile_statistics(np.exp(-t*t/4))
    assert step[0]>0.999
    assert step[4]>0.999
    assert ridge[0]<1e-8
    assert ridge[4]<1e-8


def test_quadratic_and_datum_invariance():
    t=OFFSETS
    a=profile_statistics(2*np.tanh(t/0.7))
    b=profile_statistics(2*np.tanh(t/0.7)+100+3*t+0.2*t*t)
    assert np.allclose(a,b,atol=1e-6)
    smooth=profile_statistics(100+3*t+0.2*t*t)
    assert np.all(smooth[:5]<1e-6)


def test_profile_reversal_invariant():
    t=OFFSETS
    a=np.tanh(t/1.4)+0.2*np.exp(-t*t)
    assert np.allclose(profile_statistics(a),profile_statistics(a[::-1]),atol=1e-6)


def test_profiles_reject_nonfinite_and_wrong_width():
    with pytest.raises(ValueError): profile_statistics(np.ones(8))
    with pytest.raises(ValueError): profile_statistics(np.full(9,np.nan))


def test_priority_dots_budget_spacing_and_determinism():
    s=np.linspace(0.01,1,400,dtype=np.float32).reshape(20,20)
    eligible=np.ones(s.shape,bool);eligible[0]=False
    a=priority_dots(s,eligible,25)
    assert a.sum()==25
    assert not np.any(a&~eligible)
    assert pdist(np.column_stack(np.nonzero(a))).min()>=2.8
    assert np.array_equal(a,priority_dots(s,eligible,25))


def test_priority_dots_ties_zero_and_nan():
    s=np.ones((6,6),np.float32)
    assert priority_dots(s,np.ones_like(s,bool),1)[0,0]
    s[0,0]=np.nan
    assert not priority_dots(s,np.ones_like(s,bool),1)[0,0]
    assert not priority_dots(s,np.ones_like(s,bool),0).any()
    assert not priority_dots(np.zeros_like(s),np.ones_like(s,bool),10).any()
    with pytest.raises(ValueError):priority_dots(s,np.ones_like(s,bool),1,spacing=0)


def test_lidar_encoding_endpoints_and_missing():
    a=encoded_lidar(np.array([0,1,255]),300)
    assert np.array_equal(a,[0,0,300])
    assert encoded_lidar(np.array([128]),1)[0]<0.3
