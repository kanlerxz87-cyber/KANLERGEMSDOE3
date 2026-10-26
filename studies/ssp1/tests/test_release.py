"""Regression tests for review defects and saved-byte negative paths.

The actual unmodified shared writer/validator is used, with the actual published
3730x3292 artifact and compact masks. No production constants are monkeypatched.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pytest
import rasterio
from rasterio.windows import Window

from gems32.submission import audit_geotiff
from kanler import audit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_release import check_links
from restore_registry import validate_manifest


def _synthetic_registry(tmp_path, n=2):
    rows = []
    for i in range(n):
        p = tmp_path/f'{i}.tif'
        p.write_bytes(f'synthetic-{i}'.encode())
        rows.append({'site':f'S{i}', 'path':p.name, 'git_blob_sha':str(i),
                     'status':'ok', 'local':p.name, 'sha256':audit.sha256(p)})
    return {'rasters':rows}


def test_quarantine_is_not_a_universal_surface_pass(tmp_path, monkeypatch):
    manifest = _synthetic_registry(tmp_path)
    def read(path, *_):
        if path.name == '1.tif':
            raise ValueError('incompatible grid')
        return np.eye(4, dtype=np.float32), {}
    monkeypatch.setattr(audit, 'read_comparable', read)
    r = audit.surface_guard(np.arange(16).reshape(4,4), np.ones((4,4), bool),
                            tmp_path/'template', manifest, tmp_path, tmp_path/'out.json')
    assert r['complete'] and r['inventory_complete']
    assert r['n_compared_files'] == 1 and r['n_quarantined'] == 1
    assert r['correlation_threshold_clear_on_comparable_entries']
    assert not r['comparison_complete'] and not r['passed']


def test_missing_registry_entry_fails_closed(tmp_path):
    m = {'rasters':[{'status':'failed', 'site':'S', 'path':'missing.tif'}]}
    r = audit.surface_guard(np.arange(16).reshape(4,4), np.ones((4,4), bool),
                            tmp_path/'template', m, tmp_path, tmp_path/'out.json')
    assert r['n_missing'] == 1
    assert not r['complete'] and not r['comparison_complete'] and not r['passed']


def test_constant_surface_cannot_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'read_comparable', lambda *_: (np.eye(4), {}))
    r = audit.surface_guard(np.ones((4,4)), np.ones((4,4), bool), tmp_path/'template',
                            _synthetic_registry(tmp_path, 1), tmp_path, tmp_path/'out.json')
    assert r['comparison_complete']
    assert not r['passed']


def test_surface_duplicate_stops_before_remaining_registry_reads(tmp_path, monkeypatch):
    m = _synthetic_registry(tmp_path)
    calls = []
    def read(path, *_):
        calls.append(path)
        return np.arange(16).reshape(4,4), {}
    monkeypatch.setattr(audit, 'read_comparable', read)
    r = audit.surface_guard(np.arange(16).reshape(4,4), np.ones((4,4), bool),
                            tmp_path/'template', m, tmp_path, tmp_path/'out.json')
    assert len(calls) == 1 and len(r['violations']) == 1
    assert not r['complete'] and not r['passed']


def test_final_guard_cannot_certify_unresolved_registry(tmp_path, monkeypatch):
    own = np.zeros((20,20), bool); own[0,0] = True
    ref = np.zeros((20,20), np.float32); ref[-1,-1] = 1
    monkeypatch.setattr(audit, 'read_comparable', lambda *_: (ref, {}))
    r = audit.final_guard(own, np.ones_like(own), tmp_path/'template',
                          _synthetic_registry(tmp_path, 1),
                          {'rows':[], 'complete':True, 'comparison_complete':False}, tmp_path)
    assert not r['duplicate'] and not r['passed']


def test_internal_anchor_and_broken_link_detection(tmp_path):
    (tmp_path/'index.html').write_text('<html lang="en"><main id="main"><a href="next.html#target">go</a></main></html>')
    (tmp_path/'next.html').write_text('<html lang="en"><main id="target"></main></html>')
    assert check_links(tmp_path)['html_pages'] == 2
    (tmp_path/'next.html').write_text('<html lang="en"><main id="wrong"></main></html>')
    with pytest.raises(AssertionError, match='Broken anchor'):
        check_links(tmp_path)


def test_links_cannot_escape_pages_root(tmp_path):
    (tmp_path/'index.html').write_text('<html lang="en"><main><a href="../secret">go</a></main></html>')
    with pytest.raises(AssertionError, match='escapes Pages'):
        check_links(tmp_path)


def test_published_unmeasured_metrics_are_not_zero():
    bundle = json.loads((ROOT/'evidence/submission_bundle.json').read_text())
    for key in ('catalogue_hidden_mean', 'sgmc_prevalence_calibrated_dti', 'drift_corrected_holdout_mean'):
        assert bundle['holdout_metrics'][key] is None
    surface = json.loads((ROOT/'evidence/surface_guard.json').read_text())
    assert surface['n_quarantined'] == 18 and not surface['passed']


def test_frozen_manifest_and_verified_commit_objects():
    pins = json.loads((ROOT/'registry/all_listed_site_pins.json').read_text())
    manifest = json.loads((ROOT/'registry/all_rasters.json').read_text())
    assert len(validate_manifest(manifest, pins)) == 1921
    for p in pins.values():
        assert p['object_type'] == 'Commit' and p['tree_sha'] != p['commit']
    manifest['rasters'][0]['commit'] = 'wrong'
    with pytest.raises(ValueError, match='frozen commit'):
        validate_manifest(manifest, pins)


@pytest.fixture(scope='module')
def saved_raster_fixture():
    c = json.loads((ROOT/'evidence/run_card.json').read_text())
    with np.load(ROOT/'docs/data/validation_masks.npz') as z:
        foot, known = z['footprint'], z['catalogue']
    return ROOT/'docs/downloads'/c['downloads']['tif'], foot, known


@pytest.mark.parametrize('kind,expected', [
    ('nan', 'in_footprint_zero_nan'),
    ('inf', 'in_footprint_zero_inf'),
    ('sentinel', 'in_footprint_zero_sentinel'),
    ('above_one', 'in_footprint_range_0_1'),
    ('catalogue', 'zero_on_catalogue_leakage'),
    ('outside', 'outside_footprint_compliant'),
    ('shifted_grid', 'CRS/shape/transform mismatch'),
])
def test_saved_byte_validator_rejects_real_grid_corruptions(tmp_path, saved_raster_fixture, kind, expected):
    original, foot, known = saved_raster_fixture
    p = tmp_path/'corrupted.tif'
    shutil.copyfile(original, p)
    with rasterio.open(p, 'r+') as ds:
        if kind == 'shifted_grid':
            ds.transform = ds.transform * rasterio.Affine.translation(1,0)
        else:
            domain = known if kind == 'catalogue' else (~foot if kind == 'outside' else foot & ~known)
            y, x = np.unravel_index(np.flatnonzero(domain)[0], domain.shape)
            value = {'nan':np.nan, 'inf':np.inf, 'sentinel':-3.4028235e38,
                     'above_one':1.1, 'catalogue':1., 'outside':1.}[kind]
            ds.write(np.array([[value]], np.float32), 1, window=Window(int(x),int(y),1,1))
    with pytest.raises(ValueError, match=expected):
        audit_geotiff(p, foot, known, template_tif=original)
    # Mutation testing must never alter the real downloadable artifact.
    assert audit.sha256(original) == json.loads((ROOT/'evidence/run_card.json').read_text())['raster_sha256']


def test_full_archived_prompt_is_preserved():
    marker='## Original project brief — read before each session'
    archive=marker+(ROOT/'README.md').read_text().split(marker,1)[1]
    assert hashlib.sha256(archive.encode()).hexdigest()==(ROOT/'evidence/prompt_archive_sha256.txt').read_text().split()[0]


def test_closed_negative_cannot_be_silently_rerun_or_rebased():
    import subprocess
    paths=[ROOT/'evidence/run_card.json',ROOT/'registry/all_rasters.json']
    before=[audit.sha256(p)for p in paths]
    for script in ['run_experiment.py','cache_registry.py','cache_all_registry.py']:
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,capture_output=True,text=True,timeout=15)
        assert result.returncode!=0
        assert any(word in (result.stdout+result.stderr).lower()for word in ['already recorded','closed'])
    assert [audit.sha256(p)for p in paths]==before


def test_workflows_have_offline_validation_and_no_training_or_branch_push():
    import yaml
    ci=yaml.load((ROOT/'.github/workflows/ci.yml').read_text(),Loader=yaml.BaseLoader)
    pages=yaml.load((ROOT/'.github/workflows/pages.yml').read_text(),Loader=yaml.BaseLoader)
    assert 'pull_request'in ci['on']
    assert pages['on']['schedule'][0]['cron']=='17 */12 * * *'
    assert pages['permissions']['contents']=='read'
    for name in ['ci.yml','pages.yml']:
        text=(ROOT/'.github/workflows'/name).read_text()
        assert 'verify_release.py --offline'in text
        assert 'git push'not in text and 'run_experiment.py'not in text
        assert 'npm test --prefix tools/browser'in text
    assert 'actions/cache/restore@'in (ROOT/'.github/workflows/pages.yml').read_text()
    assert '--state-path'in (ROOT/'.github/workflows/pages.yml').read_text()
