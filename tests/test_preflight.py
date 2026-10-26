import hashlib
from pathlib import Path
from preflight import inspect


def sha(data):
    return hashlib.sha256(data).hexdigest()


def test_mirror_file_does_not_establish_missing_stack_or_lane(tmp_path: Path):
    data = tmp_path / 'data'
    work = tmp_path / 'work'
    data.mkdir()
    work.mkdir()
    (data / 'input.tif').write_bytes(b'mirror')
    manifest = {'files': [{'id': 'input', 'dest': 'input.tif', 'sha256': sha(b'mirror')}]}
    result = inspect(data, work, manifest, {})
    assert result['core'][0]['verified_against_owner_mirror'] is True
    assert result['mirror_authentication'] == 'not established from organizer'
    assert result['ready_for_experiment'] is False


def test_matching_declared_stack_and_lane_cannot_override_corrupt_input(tmp_path: Path):
    data = tmp_path / 'data'
    work = tmp_path / 'work'
    data.mkdir()
    work.mkdir()
    (data / 'input.tif').write_bytes(b'corrupt')
    (work / 'feature_stack.npy').write_bytes(b'stack')
    manifest = {'files': [{'id': 'input', 'dest': 'input.tif', 'sha256': sha(b'original')}]}
    card = {'feature_cache': {'provenance_verified': True, 'sha256': sha(b'stack')},
            'lane': {'explicitly_assigned': True, 'assigned_method': 'declared lane'}}
    result = inspect(data, work, manifest, card)
    assert result['feature_stack']['provenance_verified'] is True
    assert result['core'][0]['verified_against_owner_mirror'] is False
    assert result['ready_for_experiment'] is False


def test_stack_provenance_must_match_actual_bytes(tmp_path: Path):
    data = tmp_path / 'data'
    work = tmp_path / 'work'
    data.mkdir()
    work.mkdir()
    (data / 'input.tif').write_bytes(b'original')
    (work / 'feature_stack.npy').write_bytes(b'actual')
    manifest = {'files': [{'id': 'input', 'dest': 'input.tif', 'sha256': sha(b'original')}]}
    card = {'feature_cache': {'provenance_verified': True, 'sha256': sha(b'different')},
            'lane': {'explicitly_assigned': True, 'assigned_method': 'declared lane'}}
    assert inspect(data, work, manifest, card)['ready_for_experiment'] is False
    card['feature_cache']['sha256'] = sha(b'actual')
    assert inspect(data, work, manifest, card)['ready_for_experiment'] is True
