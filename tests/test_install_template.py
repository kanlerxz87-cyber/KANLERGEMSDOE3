import io
import tarfile
from pathlib import Path

import pytest

from scripts import install_template as installer


def archive_bytes(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        for path, payload in entries:
            info = tarfile.TarInfo('pinned-root/' + path)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return output.getvalue()


def test_codeload_fallback_only_installs_verified_members(tmp_path, monkeypatch):
    monkeypatch.setattr(installer, 'DEST', tmp_path / 'template')
    good = b'# immutable shared source\n'
    row = {'repo': 'owner/repo', 'ref': 'immutable', 'path': 'src/gems/metric.py',
           'bytes': len(good), 'blob_sha': installer.git_blob(good)}
    tar = archive_bytes([(row['path'], good), ('irrelevant.txt', b'ignore')])
    monkeypatch.setattr(installer.urllib.request, 'urlopen', lambda *a, **kw: io.BytesIO(tar))
    installer.install_archive(row['repo'], row['ref'], [row])
    assert (tmp_path / 'template/repo/src/gems/metric.py').read_bytes() == good
    assert not (tmp_path / 'template/repo/irrelevant.txt').exists()


def test_codeload_fallback_rejects_bad_missing_or_duplicate_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(installer, 'DEST', tmp_path / 'template')
    good = b'good'
    row = {'repo': 'owner/repo', 'ref': 'immutable', 'path': 'src/metric.py',
           'bytes': len(good), 'blob_sha': installer.git_blob(good)}
    for entries in ([('src/metric.py', b'evil')], [],
                    [('src/metric.py', good), ('src/metric.py', good)]):
        tar = archive_bytes(entries)
        monkeypatch.setattr(installer.urllib.request, 'urlopen', lambda *a, **kw: io.BytesIO(tar))
        with pytest.raises(ValueError):
            installer.install_archive(row['repo'], row['ref'], [row])
        assert not (tmp_path / 'template/repo/src/metric.py').exists()
    unsafe = dict(row, path='../escape')
    with pytest.raises(ValueError):
        installer.destination(unsafe)
