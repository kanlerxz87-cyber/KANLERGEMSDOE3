import hashlib
import json
from pathlib import Path
import numpy as np
import pytest
from scipy.stats import spearmanr
from kanler.audit import rank_correlation, normalized_ranks, within3, mask_sha
from kanler.gates import promotion, REQUIRED, score_record


def test_exact_spearman_binary_shortcut_with_ties():
    x=np.array([1,1,2,4,8,8,9],dtype=float)
    y=np.array([0,0,1,1,0,1,0],dtype=float)
    assert rank_correlation(normalized_ranks(x),y)==pytest.approx(spearmanr(x,y).statistic)
    y=np.array([1,3,3,2,9,7,8],dtype=float)
    assert rank_correlation(normalized_ranks(x),y)==pytest.approx(spearmanr(x,y).statistic)
    assert rank_correlation(normalized_ranks(x),np.zeros_like(y)) is None


def test_proximity_includes_exact_radius_and_is_directional():
    a=np.zeros((20,20),bool);b=a.copy()
    a[4,4]=True;b[4,7]=True;b[19,19]=True
    assert within3(a,b)==1
    assert within3(b,a)==0.5
    b[:]=False;b[7,7]=True
    assert within3(a,b)==0
    assert within3(np.zeros_like(a),b) is None


def test_mask_hash_ignores_input_dtype_not_position():
    a=np.eye(10,dtype=bool)
    assert mask_sha(a)==mask_sha(a.astype(float))
    assert mask_sha(a)!=mask_sha(np.roll(a,1,axis=0))


def test_promotion_is_fail_closed():
    all_true={k:True for k in REQUIRED}
    assert promotion(all_true)['ok_to_submit']
    for k in REQUIRED:
        gates=all_true.copy();gates[k]=None
        assert not promotion(gates)['ok_to_submit']
        gates[k]='true'
        assert not promotion(gates)['ok_to_submit']
    assert promotion({})['verdict']=='negative'
    assert promotion({'saved_bytes_valid':True})['verdict']=='negative'


def test_score_needs_version_count_and_interval():
    with pytest.raises(ValueError): score_record({'pooled_dti':0.5})
    r={'evaluator_version':'test','n_withheld_positives':10,'pooled_dti':0.5,'ci95_cluster_bootstrap':[0.3,0.7]}
    assert score_record(r)['label']=='HOLDOUT-DTI'
    assert score_record(r)['leaderboard_estimate'] is None
    with pytest.raises(ValueError):score_record({**r,'pooled_dti':float('nan')})


def test_shared_template_is_not_privately_forked():
    root=Path(__file__).resolve().parents[1]
    pins=json.loads((root/'registry/template_pins.json').read_text())
    for record in pins['files']:
        assert hashlib.sha256((root/record['path']).read_bytes()).hexdigest()==record['sha256'],record['path']


def test_preregistration_unchanged():
    root=Path(__file__).resolve().parents[1]
    expected=(root/'evidence/preregistration_sha256.txt').read_text().split()[0]
    assert hashlib.sha256((root/'registry/hypotheses.json').read_bytes()).hexdigest()==expected


def test_lattice_pigeonhole_bound_not_heuristic():
    root=Path(__file__).resolve().parents[1]
    r=json.loads((root/'evidence/lattice_feasibility.json').read_text())
    assert r['minimum_possible_overlap_for_any_distinct_pixel_map_at_this_budget']==pytest.approx(1-r['uncovered_pixels']/r['candidate_fixed_budget'])
    assert r['gate_is_mathematically_incompatible_with_budget']
    assert r['minimum_possible_overlap_for_any_distinct_pixel_map_at_this_budget']>0.70


@pytest.mark.parametrize('count',[0,-1,1.5,True,'20',None])
def test_score_requires_a_real_positive_integer_count(count):
    with pytest.raises(ValueError):
        score_record({'evaluator_version':'synthetic-test','n_withheld_positives':count,'pooled_dti':0.5,'ci95_cluster_bootstrap':[0.3,0.7]})


def test_score_requires_a_nonempty_evaluator_version():
    with pytest.raises(ValueError,match='version'):
        score_record({'evaluator_version':'','n_withheld_positives':10,'pooled_dti':0.5,'ci95_cluster_bootstrap':[0.3,0.7]})
