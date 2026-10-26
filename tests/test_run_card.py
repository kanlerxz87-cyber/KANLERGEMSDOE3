import copy
import json
from pathlib import Path
import pytest
from scripts.check_run import check
from scripts.check_lattice import first_impossible_count, minimum_overlap

ROOT=Path(__file__).resolve().parents[1]


def test_recorded_run_is_negative_and_pooled_consistent():
    card=json.loads((ROOT/'evidence/run-card.json').read_text())
    lock=json.loads((ROOT/'research/registry-lock.json').read_text())
    assert check(card,lock)['ok']
    assert json.loads((ROOT/'docs/run-card.json').read_text())==card
    assert json.loads((ROOT/'run-card.json').read_text())==card
    bad=copy.deepcopy(card);bad['holdout_dti']['scores']['candidate']['dti']=.99
    with pytest.raises(ValueError):check(bad,lock)
    bad=copy.deepcopy(card);bad['surface_registry']['full_fit_surface']['rows'].pop()
    with pytest.raises(ValueError):check(bad,lock)
    bad=copy.deepcopy(card);bad['leakage_canary']['features']['K']['folds'][0]['auc']=.99
    with pytest.raises(ValueError):check(bad,lock)
    bad=copy.deepcopy(card);bad['surface_registry']['full_fit_surface']['rows'][0]['file']='wrong.tif'
    with pytest.raises(ValueError):check(bad,lock)
    bad=copy.deepcopy(card);bad['feature_cache']['template_feature_stack_reused']=True
    with pytest.raises(ValueError):check(bad,lock)
    bad=copy.deepcopy(card);bad['ok_to_submit']=True
    with pytest.raises(ValueError):check(bad,lock)


def test_density_bound_and_strict_boundary():
    uncovered=6649;n=first_impossible_count(uncovered)
    assert n==22164
    assert minimum_overlap(n-1,uncovered)<=.70
    assert minimum_overlap(n,uncovered)>.70
    assert minimum_overlap(37654,uncovered)==pytest.approx(31005/37654)
    assert minimum_overlap(20,20)==0
    with pytest.raises(ValueError): minimum_overlap(0,20)


def test_derived_site_text_is_fail_closed():
    from scripts.build_site import build
    build()
    home=(ROOT/'docs/index.html').read_text()
    guide=(ROOT/'docs/executive-summary.html').read_text()
    assert 'DO NOT SUBMIT' in home and 'DO NOT SUBMIT' in guide
    assert '0.1134' in home and 'Owner-reported / unverified' in home
    assert home.count('Historical file · research reference only')==9
    assert 'download=' not in home and 'download=' not in guide
    assert 'prior error is unknown' in guide
    js=(ROOT/'docs/source-status.js').read_text()
    assert 'api.github.com' in js and "fetch('https://www.drivendata.org" not in js
