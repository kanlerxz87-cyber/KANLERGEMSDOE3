import numpy as np
import pytest

try:
    from gems57.metric import dti_binary, dti_exact, dti_bruteforce
    HAVE_TEMPLATE = True
except ImportError:
    HAVE_TEMPLATE = False
pytestmark = pytest.mark.skipif(not HAVE_TEMPLATE, reason='Restore the pinned shared template first')


def test_shared_binary_and_soft_match_bruteforce():
    rng=np.random.default_rng(2026)
    for _ in range(10):
        truth=rng.random((6,8))<.12
        p=(rng.random((6,8))<.08).astype(float)
        exact=dti_exact(p,truth); binary=dti_binary(p,truth); brute=dti_bruteforce(p,truth)
        assert exact['dti']==pytest.approx(brute['dti'], abs=1e-12)
        assert binary['dti']==pytest.approx(brute['dti'], abs=1e-12)
        p=rng.random((6,8))*(rng.random((6,8))<.2)
        assert dti_exact(p,truth)['dti']==pytest.approx(dti_bruteforce(p,truth)['dti'], abs=1e-12)


def test_one_dot_can_cover_multiple_truth_cells():
    truth=np.zeros((3,5),bool);truth[1,1:4]=True
    pred=np.zeros((3,5));pred[1,2]=1
    result=dti_exact(pred,truth)
    assert result['tp']==pytest.approx(7/3)
    assert result['tp']>1  # Contradicts the upstream prose, not the implementation.


def test_known_fault_mask_is_pixel_exact():
    truth=np.zeros((6,7),bool);truth[2,2]=True
    pred=np.zeros((6,7));pred[2,3]=1
    known=np.zeros((6,7),bool);known[2,2]=True
    assert dti_exact(pred,truth,known=known)['n_emitted']==1
    assert dti_exact(pred,truth,known=known)['n_truth']==0


def test_pinned_default_fold_can_leave_adjacent_same_trace_visible():
    # This documents a limitation of the pinned default, NOT a compliance test:
    # withholding a chunk of a 20-pixel branch leaves the adjacent chunk visible.
    from scipy.ndimage import binary_dilation
    from gems57.grid import Grid
    from gems57.holdout import build_holdout
    valid=np.ones((100,100),bool); catalogue=np.zeros_like(valid)
    for y in (25,75):
        for x in (15,65): catalogue[y,x:x+20]=True
    grid=Grid(valid,catalogue,None,None,100,100)
    context=build_holdout(grid,hide_frac=.2,seeds=(20,),modes=('all',))
    for key, hidden in context.hidden_by_cell.items():
        assert hidden.any()
        assert np.any(binary_dilation(hidden) & context.visible(key))
