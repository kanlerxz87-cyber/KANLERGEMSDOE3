"""Forensic and publishing guards; none of these tests fits a geological model."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from scipy.ndimage import binary_dilation

from scripts import audit_cadg_archive as cadg_audit
from scripts import build_cadg_site as cadg_site
from scripts.audit_changed_peer_rasters import git_blob, inspect
from scripts.audit_history import disk
from scripts.build_site import check_changed_peer_receipt, check_inherited
from scripts.snapshot_raster_changes import compare, observe, parse_raster_tree, rows_by_site

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def test_cadg_receipt_binds_four_preserved_artifacts_and_negative_decision():
    report = read('evidence/session-91270cac-cadg-audit.json')
    card = read('evidence/cadg-submod-run-card.json')
    rows = cadg_site.checked_archive(report, card)
    assert len(rows) == 4
    assert all(r['lattice']['candidate_dot_overlap_fraction'] > .70 for r in rows)
    assert all(r['validator']['portal_acceptance_verified'] is False for r in rows)
    assert report['verdict'] == 'negative' and report['slot_authorized'] is False
    assert len(report['versions']) == 2 and all(v['same_in_footprint_dot_mask'] is True for v in report['versions'])
    old = next(r for r in rows if r['sha256'] == card['raster_sha256'])
    assert old['lattice']['candidate_dots_within_3px_of_lattice'] == 37630
    assert old['catalogue_filtered_lattice_diagnostic']['candidate_dots_within_3px'] == 37553
    assert round(old['catalogue_filtered_lattice_diagnostic']['overlap_fraction'], 6) == card['final_dot_overlap_3px']


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(verdict='promote'),
    lambda r: r.update(slot_authorized=True),
    lambda r: r['lattice_source'].update(sha256='0' * 64),
    lambda r: r['versions'][0]['files'][0].update(sha256='0' * 64),
    lambda r: r['versions'][0]['files'][0]['lattice'].update(candidate_dot_overlap_fraction=.2),
    lambda r: r['versions'][0]['files'][0]['lattice'].update(duplicate_over_70_percent=False),
    lambda r: r['versions'][0]['files'][0]['catalogue_filtered_lattice_diagnostic'].update(overlap_fraction=.9),
    lambda r: r['versions'][0]['files'][0]['validator'].update(portal_acceptance_verified=True),
    lambda r: r['versions'][0]['files'][0]['validator'].update(ok='true'),
    lambda r: r['versions'][0].update(same_in_footprint_dot_mask=False),
    lambda r: r['versions'].pop(),
])
def test_cadg_receipt_mutations_fail_closed(mutation):
    report = read('evidence/session-91270cac-cadg-audit.json')
    card = read('evidence/cadg-submod-run-card.json')
    mutation(report)
    with pytest.raises(ValueError):
        cadg_site.checked_archive(report, card)


def test_cadg_bad_local_profile_is_reported_not_hidden():
    report = read('evidence/session-91270cac-cadg-audit.json')
    report['versions'][0]['files'][0]['validator']['ok'] = False
    rows = cadg_site.checked_archive(report, read('evidence/cadg-submod-run-card.json'))
    assert rows[0]['validator']['ok'] is False  # renderer prints FAIL rather than unconditional PASS


def test_cadg_zip_mismatch_rejected_without_touching_original(tmp_path):
    archive = tmp_path / 'docs/cadg-submod/downloads'
    shutil.copytree(ROOT / 'docs/cadg-submod/downloads', archive)
    (tmp_path / 'research').mkdir()
    (tmp_path / 'evidence').mkdir()
    (tmp_path / 'data').mkdir()
    shutil.copy2(ROOT / 'research/registry-lock.json', tmp_path / 'research/registry-lock.json')
    shutil.copy2(ROOT / 'evidence/cadg-submod-run-card.json', tmp_path / 'evidence/cadg-submod-run-card.json')
    shutil.copy2(ROOT / 'data/core-manifest.json', tmp_path / 'data/core-manifest.json')
    report = read('evidence/session-91270cac-cadg-audit.json')
    card = read('evidence/cadg-submod-run-card.json')
    assert len(cadg_site.checked_archive(report, card, tmp_path)) == 4
    item = report['versions'][0]['files'][0]
    target = tmp_path / item['zip']
    with zipfile.ZipFile(target, 'w') as z:
        z.writestr(Path(item['file']).name, b'tampered')
    with pytest.raises(ValueError):
        cadg_site.checked_archive(report, card, tmp_path)


def test_stale_cadg_check_is_nonmutating(monkeypatch, tmp_path):
    file = tmp_path / 'generated.html'
    file.write_text('stale sentinel')
    monkeypatch.setattr(cadg_site, 'ROOT', tmp_path)
    monkeypatch.setattr(cadg_site, 'render', lambda: {file: 'current output'})
    with pytest.raises(ValueError, match='stale'):
        cadg_site.build(check_only=True)
    assert file.read_text() == 'stale sentinel'
    file.write_text('current output')
    cadg_site.build(check_only=True)
    assert file.read_text() == 'current output'


def test_archive_members_reject_traversal_and_symlinks(tmp_path):
    (tmp_path / 'valid.tif').write_bytes(b'fixture')
    (tmp_path / 'alias.tif').symlink_to(tmp_path / 'valid.tif')
    assert cadg_audit.archive_member(tmp_path, 'valid.tif', '.tif').name == 'valid.tif'
    for name in ('../valid.tif', '/absolute.tif', 'alias.tif', 'valid.zip', 'missing.tif'):
        with pytest.raises(ValueError):
            cadg_audit.archive_member(tmp_path, name, '.tif')


def tree_item(mode, kind, sha, path):
    return f'{mode} {kind} {sha}\t{path}\0'.encode()


def test_tree_parser_and_path_diffs_never_approve():
    a, b = 'a' * 40, 'b' * 40
    old = parse_raster_tree(tree_item('100644', 'blob', a, 'docs/old.tif') + tree_item('100644', 'blob', a, 'docs/change.TIFF'))
    new = parse_raster_tree(tree_item('100644', 'blob', b, 'docs/new.tif') + tree_item('100644', 'blob', b, 'docs/change.TIFF'))
    result = compare(old, new)
    assert [x['path'] for x in result['added']] == ['docs/new.tif']
    assert [x['path'] for x in result['removed']] == ['docs/old.tif']
    assert [x['path'] for x in result['changed']] == ['docs/change.TIFF']
    assert result['unchanged_count'] == 0
    with pytest.raises(ValueError):
        parse_raster_tree(tree_item('100644', 'blob', a, '../bad.tif'))
    with pytest.raises(ValueError):
        parse_raster_tree(tree_item('100644', 'blob', a, 'same.tif') * 2)
    with pytest.raises(ValueError):
        parse_raster_tree(tree_item('100644', 'blob', 'not-a-sha', 'x.tif'))
    with pytest.raises(ValueError):
        parse_raster_tree(b'invalid without tab\0')


def test_failed_or_missing_source_comparison_is_unknown(monkeypatch):
    old = read('evidence/session-20261027-focus-feed.json')
    new = read('evidence/session-91270cac-focus-feed.json')
    with pytest.raises(ValueError):
        rows_by_site({'rows': new['rows'][:-1]})
    changed = copy.deepcopy(new)
    changed['rows'][0]['commit'] = None
    monkeypatch.setattr('scripts.snapshot_raster_changes.tree', lambda *args: (_ for _ in ()).throw(OSError('offline fixture')))
    result = observe(old, changed, source_factory=lambda: object())
    assert result['all_compared'] is False
    assert all(row['status'] == 'UNKNOWN' for row in result['rows'])
    assert result['registry_complete'] is False and result['scientific_approval'] is False


def raster_bytes(arr, shift=0, nodata=None):
    with MemoryFile() as memory:
        with memory.open(driver='GTiff', width=arr.shape[1], height=arr.shape[0], count=1,
                         dtype='float32', crs='EPSG:32611', transform=from_origin(shift, 900, 100, 100), nodata=nodata) as dst:
            dst.write(arr.astype('float32'), 1)
        return memory.read()


def test_changed_peer_geometry_exact_70_percent_is_still_not_a_pass():
    footprint = np.ones((9, 9), dtype=bool)
    reference = np.zeros((9, 9), dtype=bool); reference[4, 4] = True
    halo = binary_dilation(reference, structure=disk(3))
    arr = np.zeros((9, 9), dtype='float32')
    for point in [(4, 4), (4, 5), (4, 6), (4, 7), (3, 4), (2, 4), (1, 4), (0, 0), (0, 8), (8, 0)]:
        arr[point] = 1
    data = raster_bytes(arr)
    grid = ((9, 9), rasterio.crs.CRS.from_epsg(32611), from_origin(0, 900, 100, 100))
    outcome = inspect(data, git_blob(data), footprint, grid, halo)
    assert outcome['candidate_dots'] == 10 and outcome['candidate_dots_within_3px_of_full_lattice'] == 7
    assert outcome['directed_overlap_fraction'] == .70
    assert outcome['status'] == 'BLOCKED_INCOMPLETE_REGISTRY' and outcome['slot_authorized'] is False
    arr[5, 4] = 1
    data = raster_bytes(arr)
    assert inspect(data, git_blob(data), footprint, grid, halo)['status'] == 'STOP_DUPLICATE'


def test_changed_peer_rejects_soft_empty_nan_shift_and_wrong_blob():
    footprint = np.ones((9, 9), dtype=bool)
    grid = ((9, 9), rasterio.crs.CRS.from_epsg(32611), from_origin(0, 900, 100, 100))
    halo = np.zeros((9, 9), dtype=bool); halo[4, 4] = True
    for kind in ('soft', 'empty', 'nan', 'shift', 'wrongblob', 'lfs'):
        arr = np.zeros((9, 9), dtype='float32'); arr[4, 4] = 1
        if kind == 'soft': arr[3, 4] = .3
        if kind == 'empty': arr[4, 4] = 0
        if kind == 'nan': arr[3, 4] = np.nan
        data = b'version https://git-lfs.github.com/spec/v1\n' if kind == 'lfs' else raster_bytes(arr, shift=1 if kind == 'shift' else 0)
        with pytest.raises((ValueError, rasterio.errors.RasterioIOError)):
            inspect(data, '0' * 40 if kind == 'wrongblob' else git_blob(data), footprint, grid, halo)


def bound_peer_data():
    path = ROOT / 'evidence/session-91270cac-raster-changes.json'
    return (json.loads(path.read_bytes()), read('evidence/session-91270cac-changed-peer-audit.json'), path.read_bytes(),
            read('research/registry-lock.json'), read('data/core-manifest.json'),
            read('evidence/session-20261027-focus-feed.json'), read('evidence/session-91270cac-focus-feed.json'))


def test_peer_receipt_bindings_and_twins_are_explicit():
    args = bound_peer_data()
    check_changed_peer_receipt(*args)
    report = args[1]
    assert report['files_seen'] == report['duplicate_stops'] == 29
    assert report['unknown'] == 0 and report['incomplete_registry'] == 0
    assert report['new_candidate_generated'] is False and report['slot_authorized'] is False
    assert all(x['directed_overlap_fraction'] > .70 and x['surface_correlation'] is None for x in report['findings'])


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(change_snapshot_sha256='0' * 64),
    lambda r: r.update(slot_authorized=True),
    lambda r: r.update(verdict='promote'),
    lambda r: r['lattice_source'].update(sha256='0' * 64),
    lambda r: r['findings'][0].update(git_blob='0' * 40),
    lambda r: r['findings'][0].update(sha256='not-a-digest'),
    lambda r: r['findings'][0].update(directed_overlap_fraction=.1),
    lambda r: r['findings'][0].update(surface_correlation=.1),
    lambda r: r['findings'][0].update(status='BLOCKED_INCOMPLETE_REGISTRY'),
    lambda r: r.update(duplicate_stops=0),
    lambda r: r['findings'].pop(),
])
def test_peer_receipt_tampering_never_publishes(mutation):
    args = list(bound_peer_data())
    mutation(args[1])
    with pytest.raises((ValueError, KeyError)):
        check_changed_peer_receipt(*args)


def test_inherited_duplicate_and_saved_bytes_checked():
    report = read('evidence/inherited_literal_audit.json')
    check_inherited(report)
    report['rows'][0]['lattice_sha256'] = '0' * 64
    with pytest.raises(ValueError):
        check_inherited(report)


def test_concurrent_main_candidates_are_hash_bound_but_never_promoted(monkeypatch):
    from scripts import build_site
    receipt = build_site.check_quarantined_artifacts()
    assert len(receipt['files']) == 4
    assert 'legacy_geofault' in receipt
    assert receipt['geocontrast']['verdict'] == 'promote'
    assert receipt['geocontrast']['ok_to_download'] is True
    assert receipt['geocontrast']['validator']['ok_to_upload'] is False
    assert 'submission_authorization' not in receipt['geocontrast']
    assert 'input_provenance' not in receipt['geocontrast']
    assert receipt['baseline']['verdict'] == 'negative'
    assert receipt['baseline']['ok_to_submit'] is False
    page = (ROOT / 'docs/index.html').read_text()
    assert 'Preserved bytes. No download or upload authorization.' in page
    assert 'HOLDOUT-DTI' in page and '0.300267' in page
    assert 'QUARANTINED' in page
    assert 'href="downloads/kanler-geocontrast-v1-' not in page
    assert 'href="downloads/gemsdoe32-kanler-baseline-lr-v1-' not in page

    original_read = build_site.read
    def tampered(path):
        value = original_read(path)
        if path == 'evidence/unique_submission_run_card.json':
            value['validator']['submission_authorized'] = True
        return value
    monkeypatch.setattr(build_site, 'read', tampered)
    with pytest.raises(ValueError, match='fail-closed'):
        build_site.check_quarantined_artifacts()


def test_default_preflight_does_not_reopen_expired_clock(tmp_path):
    import subprocess
    import sys
    output = tmp_path / 'preflight.json'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/preflight.py'), '--out', str(output)], capture_output=True, text=True)
    assert result.returncode == 1
    receipt = json.loads(output.read_text())
    assert receipt['config'] == 'config/research-session-52a91352.json'
    assert any('budget' in f for f in receipt['failures'])
    assert receipt['research_ready'] is False and receipt['slot_authorized'] is False


def test_current_run_card_is_honestly_negative_and_empty():
    card = read('evidence/session-91270cac-run-card.json')
    assert card['geological_experiments_this_session'] == 0
    assert card['weekly_slots_used_this_session'] == 0
    assert card['verdict'] == 'negative' and card['slot_authorized'] is False and card['ok_to_submit'] is False
    assert card['holdout_dti'] is None and card['holdout_ci95'] is None and card['raster_sha256'] is None
    assert card['correlation_overlap_vs_registry']['candidate_surface'] is None
    assert card['correlation_overlap_vs_registry']['candidate_final_dots'] is None
    assert card['validator_output']['status'] == 'NOT_RUN_NO_NEW_CANDIDATE'
    assert len(card['submission_note']) <= 140


def test_original_unsafe_presentations_are_preserved_as_history():
    expected = {
        'parallel-gpc-dashboard.html': 'bf13ebf72aba2b90ff11c51848f8252a870b4379466ad3bec8b5e22d7eae0677',
        'parallel-gpc-submission-guide.html': '809be3fb5c6d1a68d5fd0de0d988289ac62b0f559d2de65cb91040c6f6fc8b2a',
        'parallel-gpc-readme.md': 'c6ae1a3d4931ad9c95b17bb7ca91aceb1008b8665974eb930fb9003a109f9983',
        'parallel-root-research.md': 'dbfc41df2757ef4d09322edbbdf9f1759f8ba1b3dfafbd12d9b6654b73af5a21',
        'gpc-why-02778.md': '55dfeb7923ebdbd6d17ef76a51db2e9fabd82cbf4cb229022709a916984cb712',
        'gpc-hypotheses.md': '72d29da813f00d74a848768bf7b188c24e1607c3f33e584f8d9fa73e70e263ea',
    }
    for path, digest in expected.items():
        assert hashlib.sha256((ROOT / 'evidence/archived-pages' / path).read_bytes()).hexdigest() == digest
    for path in ('docs/parallel-gpc-dashboard.html', 'docs/parallel-gpc-submission-guide.html',
                 'docs/cadg-submod/index.html', 'docs/cadg-submod/executive-summary.html'):
        text = (ROOT / path).read_text()
        assert 'DO NOT SUBMIT' in text
        assert 'selector cannot waive' in text.lower()
        assert 'Download the unique GPC' not in text
        assert 'Scored historical files prove' not in text
        assert 'NaN outside the footprint triggers' not in text
