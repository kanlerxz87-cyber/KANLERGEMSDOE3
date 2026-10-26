import hashlib
import io
import tarfile

import pytest

import bootstrap


def test_existing_template_modification_is_rejected(tmp_path, monkeypatch):
    template = tmp_path / "template"
    template.mkdir()
    (template / "important.py").write_text("modified\n")
    monkeypatch.setattr(bootstrap, "TEMPLATE", template)
    monkeypatch.setattr(bootstrap, "CRITICAL", {"important.py": hashlib.sha256(b"original\n").hexdigest()})
    with pytest.raises(RuntimeError, match="missing or changed"):
        bootstrap.ensure_template()


@pytest.mark.parametrize("kind", ["traversal", "symlink", "hardlink"])
def test_archive_paths_and_links_cannot_escape_staging(tmp_path, monkeypatch, kind):
    cache = tmp_path / "cache"; cache.mkdir()
    ref = "testref"
    template = cache / "upstream" / f"GEMSDOE32-{ref}"
    archive = cache / f"template-{ref}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("../escape" if kind == "traversal" else f"{template.name}/link")
        if kind == "traversal":
            data = b"no"; info.size = len(data); tar.addfile(info, io.BytesIO(data))
        else:
            info.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
            info.linkname = "../../outside"
            tar.addfile(info)
    monkeypatch.setattr(bootstrap, "CACHE", cache)
    monkeypatch.setattr(bootstrap, "TEMPLATE_REF", ref)
    monkeypatch.setattr(bootstrap, "TEMPLATE", template)
    monkeypatch.setattr(bootstrap, "TEMPLATE_ARCHIVE_SHA", bootstrap.sha256(archive))
    with pytest.raises(RuntimeError, match="Unsafe archive member"):
        bootstrap.ensure_template()
    assert not (tmp_path / "escape").exists() and not template.exists()
