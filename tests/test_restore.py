import hashlib
from pathlib import Path
from types import SimpleNamespace
import pytest
import restore_workspace as rw


def spec(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'repo':'someone/repo', 'blob_sha1':'0'*40}


def test_verify_existing_good_and_refuse_mismatch(tmp_path):
    path = tmp_path / 'x'
    assert not rw.verify_file(path, spec(b'good'))
    path.write_bytes(b'good')
    assert rw.verify_file(path, spec(b'good'))
    with pytest.raises(ValueError, match='Refusing to overwrite'):
        rw.restore_file(path, spec(b'bad'), fetch=True)
    assert path.read_bytes() == b'good'


def test_fetch_hash_and_atomic_promotion(tmp_path, monkeypatch):
    data = b'public bytes'
    def fake_run(cmd, stdout, **kwargs):
        stdout.write(data)
        return SimpleNamespace(returncode=0, stderr=b'')
    monkeypatch.setattr(rw.subprocess, 'run', fake_run)
    target = rw.restore_file(tmp_path/'nested/x', spec(data), fetch=True)
    assert target.read_bytes() == data
    assert not list(target.parent.glob('*.partial'))


def test_bad_download_and_network_error_leave_no_destination(tmp_path, monkeypatch):
    def fake_run(cmd, stdout, **kwargs):
        stdout.write(b'wrong')
        return SimpleNamespace(returncode=0, stderr=b'')
    monkeypatch.setattr(rw.subprocess, 'run', fake_run)
    target = tmp_path/'out'
    with pytest.raises(ValueError):
        rw.restore_file(target, spec(b'expected'), fetch=True)
    assert not target.exists()
    assert not list(tmp_path.iterdir())
    monkeypatch.setattr(rw.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b'403'))
    with pytest.raises(RuntimeError, match='403'):
        rw.restore_file(target, spec(b'expected'), fetch=True)
    assert not list(tmp_path.iterdir())


def test_no_fetch_never_calls_network(tmp_path, monkeypatch):
    monkeypatch.setattr(rw.subprocess, 'run', lambda *a, **k: pytest.fail('network called'))
    with pytest.raises(FileNotFoundError):
        rw.restore_file(tmp_path/'missing', spec(b'data'), fetch=False)
