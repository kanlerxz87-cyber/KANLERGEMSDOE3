import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kanler3.gpc import GPC_FEATURE_NAMES, compute_gpc_features

def _fields(step=True):
    y, x = np.mgrid[0:60, 0:80]
    base = (x > 40).astype(np.float32) * 10.0 if step else np.zeros((60, 80), np.float32)
    rng = np.random.default_rng(0)
    return {
        "rtp": base + rng.normal(0, 0.5, base.shape).astype(np.float32),
        "iso_grav_anom": base * 0.5 + rng.normal(0, 0.5, base.shape).astype(np.float32),
        "depth_to_base_surf": -base * 2 + rng.normal(0, 0.5, base.shape).astype(np.float32),
        "det_elev": base + rng.normal(0, 0.5, base.shape).astype(np.float32),
    }

def test_gpc_aligned_step_beats_flat():
    foot = np.ones((60, 80), bool)
    a = compute_gpc_features(_fields(True), foot)
    b = compute_gpc_features(_fields(False), foot)
    assert set(a) == set(GPC_FEATURE_NAMES)
    for v in a.values():
        assert v.dtype == np.float32 and np.isfinite(v).all()
    # At the shared step (col ~40) concordance must exceed the flat/noise field.
    assert a["gpc_mean_absdot_s1"][:, 38:43].mean() > b["gpc_mean_absdot_s1"][:, 38:43].mean()
    assert a["gpc_consensus_count_s1"][:, 38:43].mean() > 0.5

def test_gpc_single_field_mimic_fails_min():
    foot = np.ones((60, 80), bool)
    f = _fields(False)
    y, x = np.mgrid[0:60, 0:80]
    f["rtp"] = (x > 40).astype(np.float32) * 10  # only magnetics turns
    a = compute_gpc_features(f, foot)
    assert a["gpc_min_absdot_s1"][:, 38:43].mean() < 0.9
