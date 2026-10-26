import json
from urllib.error import URLError

import pytest
import refresh_feed as feed


HTML = '''<html><table><tr><th> Rank </th><th>Participant</th><th>Best<br>public DW-Tversky</th></tr>
<tr><td><b>#1</b></td><td>someone</td><td>0.4437</td></tr>
<tr><td>#2</td><td>someone else</td><td>0.3916</td></tr></table></html>'''


def test_leaderboard_parser_requires_public_tversky_and_first_rank():
    assert feed.parse_leaderboard(HTML) == .4437
    with pytest.raises(ValueError):
        feed.parse_leaderboard(HTML.replace("#1", "#3"))
    with pytest.raises(ValueError):
        feed.parse_leaderboard(HTML.replace("0.4437", "1.2"))
    with pytest.raises(ValueError):
        feed.parse_leaderboard("<html>login page</html>")


def test_failure_preserves_previous_value_and_marks_stale(monkeypatch):
    def unavailable(*args, **kwargs):
        raise URLError("offline")
    monkeypatch.setattr(feed, "get", unavailable)
    old = {"leaderboard": {"value": .4437, "observed_at_utc": "2026-10-26"}}
    result = feed.refresh(old, {"rows": [{"site": "GEMSDOE32", "ref": "a" * 40}]}, "now")
    assert result["leaderboard"]["value"] == .4437
    assert result["leaderboard"]["status"] == "stale_or_unavailable"
    assert result["leaderboard"]["observed_at_utc"] == "2026-10-26"
    assert result["peer_heads"]["sites"][0]["status"] == "unavailable"


def test_public_observation_and_peer_change_do_not_approve(monkeypatch):
    def fake_get(url, github=False):
        return json.dumps({"sha": "b" * 40}).encode() if github else HTML.encode()
    monkeypatch.setattr(feed, "get", fake_get)
    result = feed.refresh({}, {"rows": [{"site": "GEMSDOE32", "ref": "a" * 40}]}, "now")
    assert result["leaderboard"]["value"] == .4437
    assert "not a submission-page receipt" in result["leaderboard"]["evidence_class"]
    assert result["peer_heads"]["sites"][0]["changed_since_audit"] is True
    assert "approve" in result["peer_heads"]["note"]
