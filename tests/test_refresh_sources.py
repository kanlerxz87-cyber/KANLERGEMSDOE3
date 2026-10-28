from __future__ import annotations

import base64
import hashlib
import json

import pytest

from scripts import refresh_sources


def focus_feed() -> dict:
    return {
        "rows": [
            {
                "site": f"GEMSDOE{number}",
                "repository": f"buffedlizard55-lab/GEMSDOE{number}",
                "status": "PINNED_SOURCE_ONLY",
                "commit": f"{number:040x}",
                "source_page": "index.html" if number == 30 else "docs/index.html",
            }
            for number in (24, 25, 27, 28, 30, 31, 32, 33, 36)
        ]
    }


def test_pinned_tasks_use_immutable_focus_heads_and_official_ref():
    official = "a" * 40
    tasks = refresh_sources.pinned_tasks(focus_feed(), official)
    assert len(tasks) == 40
    assert all(ref == f"{int(repo[-2:]):040x}" for repo, _, ref in tasks if repo.startswith("buffedlizard55-lab/GEMSDOE") and repo.endswith("GEMSDOE24"))
    assert ("drivendataorg/gems-prize-reference-solution", "README.md", official) in tasks
    assert ("buffedlizard55-lab/GEMSDOE32", "registry/feature_receipt.json", f"{32:040x}") in tasks
    assert ("buffedlizard55-lab/GEMSDOE30", "index.html", f"{30:040x}") in tasks


def test_pinned_tasks_fail_closed_for_missing_or_unpinned_site():
    feed = focus_feed()
    feed["rows"] = feed["rows"][:-1]
    with pytest.raises(ValueError, match="exactly the nine"):
        refresh_sources.pinned_tasks(feed, "a" * 40)
    feed = focus_feed()
    feed["rows"][0]["commit"] = None
    with pytest.raises(ValueError, match="immutable source commit"):
        refresh_sources.pinned_tasks(feed, "a" * 40)


def test_retrieve_verifies_blob_then_atomically_writes(monkeypatch, tmp_path):
    raw = b"pinned source bytes\n"
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    monkeypatch.setattr(
        refresh_sources,
        "gh_json",
        lambda endpoint: {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(raw).decode(),
            "size": len(raw),
            "sha": blob,
        },
    )
    result = refresh_sources.retrieve(
        ("buffedlizard55-lab/GEMSDOE24", "docs/index.html", "b" * 40), tmp_path
    )
    destination = tmp_path / "GEMSDOE24" / "docs" / "index.html"
    assert result["status"] == "retrieved"
    assert result["ref"] == "b" * 40
    assert result["sha256"] == hashlib.sha256(raw).hexdigest()
    assert destination.read_bytes() == raw
    assert not list(destination.parent.glob("*.partial"))


def test_retrieve_marks_missing_pinned_file_without_overwriting_old_snapshot(monkeypatch, tmp_path):
    destination = tmp_path / "GEMSDOE24" / "docs" / "score-ledger.csv"
    destination.parent.mkdir(parents=True)
    destination.write_text("old historical snapshot")
    monkeypatch.setattr(refresh_sources, "gh_json", lambda endpoint: (_ for _ in ()).throw(FileNotFoundError(endpoint)))
    result = refresh_sources.retrieve(
        ("buffedlizard55-lab/GEMSDOE24", "docs/score-ledger.csv", "c" * 40), tmp_path
    )
    assert result["status"] == "not_found"
    assert "does not exist" in result["note"]
    assert destination.read_text() == "old historical snapshot"


def test_retrieve_rejects_wrong_blob_without_replacing_file(monkeypatch, tmp_path):
    destination = tmp_path / "GEMSDOE24" / "README.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("old snapshot")
    raw = b"bad or mismatched bytes"
    monkeypatch.setattr(
        refresh_sources,
        "gh_json",
        lambda endpoint: {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(raw).decode(),
            "size": len(raw),
            "sha": "0" * 40,
        },
    )
    result = refresh_sources.retrieve(
        ("buffedlizard55-lab/GEMSDOE24", "README.md", "c" * 40), tmp_path
    )
    assert result["status"] == "unavailable"
    assert result["error"] == "ValueError"
    assert destination.read_text() == "old snapshot"


def test_help_is_side_effect_free(monkeypatch, capsys):
    def unexpected(*args, **kwargs):
        raise AssertionError("--help must not refresh any source")

    monkeypatch.setattr(refresh_sources, "refresh", unexpected)
    with pytest.raises(SystemExit) as stopped:
        refresh_sources.main(["--help"])
    assert stopped.value.code == 0
    assert "--feed" in capsys.readouterr().out
