from datetime import datetime, timezone
import json
import subprocess

import pytest

import update_feed
import update_peer_feed


TABLE = b'''<!doctype html><table><thead><tr><th>Rank</th><th>Team members</th><th>Participant</th>
<th>Best<br>public<br>DW-Tversky<br>(in descending order)</th><th>Shared work</th></tr></thead><tbody>
<tr><td>#1</td><td><a href="/users/a/"><img src="avatar.jpg"></a></td><td><div>Team<br>31 submissions</div></td><td>0.4437</td><td><a>17</a></td></tr>
<tr><td>#2</td><td></td><td>Other</td><td>0.3916</td><td></td></tr></tbody></table>'''


def test_parse_only_the_rank_one_score_cell():
    assert update_feed.parse_leader(TABLE.decode()) == "0.4437"


def test_parse_rejects_login_unrelated_or_ambiguous_tables():
    for html in ("<h1>Login</h1>0.9999", "<table><tr><th>Score</th></tr><tr><td>0.3</td></tr></table>",
                 (TABLE + TABLE).decode(), TABLE.decode().replace("0.4437", "0.4437 0.5")):
        with pytest.raises(ValueError):
            update_feed.parse_leader(html)


def test_fetch_rejects_redirect_and_oversized_body(monkeypatch):
    class Response:
        status = 200
        def __init__(self, url, body): self.url, self.body = url, body
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def geturl(self): return self.url
        def read(self, limit): return self.body
    monkeypatch.setattr(update_feed, "urlopen", lambda *a, **k: Response("https://example.invalid/", TABLE))
    with pytest.raises(ValueError, match="redirect"):
        update_feed.fetch_public_page()
    monkeypatch.setattr(update_feed, "urlopen", lambda *a, **k: Response(update_feed.URL, b"x" * 10_000_001))
    with pytest.raises(ValueError, match="too large"):
        update_feed.fetch_public_page()
    monkeypatch.setattr(update_feed, "urlopen", lambda *a, **k: Response(update_feed.URL, TABLE))
    assert update_feed.fetch_public_page() == TABLE


def test_feed_success_has_actual_response_hash(tmp_path):
    out = tmp_path / "feed.json"
    result = update_feed.refresh(out, fetch=lambda: TABLE, now=datetime(2026, 10, 26, tzinfo=timezone.utc))
    assert result["status"] == "fresh" and result["public_leader"] == "0.4437"
    assert len(result["source_body_sha256"]) == 64
    assert json.loads(out.read_text()) == result


def test_feed_failure_preserves_old_timestamp_but_never_claims_fresh(tmp_path):
    out = tmp_path / "feed.json"
    old = {"schema": "leaderboard-feed-v1", "source": update_feed.URL,
           "public_leader": "0.4", "last_success_utc": "2026-10-01T00:00:00Z"}
    out.write_text(json.dumps(old))
    def broken():
        raise OSError("offline")
    result = update_feed.refresh(out, fetch=broken, now=datetime(2026, 10, 26, tzinfo=timezone.utc))
    assert result["status"] == "error"
    assert result["public_leader"] == "0.4"
    assert result["last_success_utc"] == "2026-10-01T00:00:00Z"
    assert result["checked_utc"].startswith("2026-10-26")


def test_feed_does_not_inherit_snapshot_from_another_source(tmp_path):
    out = tmp_path / "feed.json"
    out.write_text(json.dumps({"schema": "leaderboard-feed-v1", "source": "https://example.invalid", "public_leader": "0.9"}))
    result = update_feed.refresh(out, fetch=lambda: (_ for _ in ()).throw(OSError("offline")))
    assert result["status"] == "error" and result["public_leader"] is None


def test_peer_failures_are_unknown_not_unchanged(tmp_path):
    heads = json.loads((update_peer_feed.ROOT / "data/peer_heads.json").read_text())["heads"]
    def mock(site):
        if site == "GEMSDOE24":
            raise subprocess.CalledProcessError(1, "gh")
        if site == "GEMSDOE25":
            return "a" * 40
        return heads[site]
    result = update_peer_feed.refresh(tmp_path / "peer.json", fetch=mock)
    assert result["status"] == "error" and result["error_count"] == 1
    assert result["changed_count"] == 1
    missing = next(x for x in result["sites"] if x["site"] == "GEMSDOE24")
    assert missing["changed"] is None and missing["current_head"] is None
