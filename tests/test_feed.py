import requests
from kanler.feed import parse_leaderboard,refresh
import pytest

HTML='''<table><tr><th>Rank</th><th>Participant</th><th>Best public DW-Tversky</th></tr>
<tr><td>#1</td><td>someone 31 submissions</td><td>0.4437</td></tr>
<tr><td>#2</td><td>someone else</td><td>0.3916</td></tr></table>'''

class Response:
    url='https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'
    text=HTML
    def raise_for_status(self):pass


def test_public_table_not_arbitrary_numeric_matches():
    assert parse_leaderboard(HTML)==0.4437
    with pytest.raises(ValueError):parse_leaderboard('<h1>Login</h1>0.9999')
    with pytest.raises(ValueError):parse_leaderboard(HTML.replace('#1','#11'))


def test_network_failure_preserves_last_good_value():
    old={'leading_public_value':0.4437,'last_success_utc':'2026-10-26','stale':False}
    def fail(*a,**kw):raise requests.Timeout('blocked official host')
    r=refresh(old,fail)
    assert r['leading_public_value']==old['leading_public_value']
    assert r['last_success_utc']==old['last_success_utc']
    assert r['stale']
    assert r['remaining_weekly_slots']is None
    assert r['authenticated_submission_receipts']is None


def test_success_refresh_is_not_a_submission_receipt():
    r=refresh({},lambda*a,**kw:Response())
    assert not r['stale']
    assert r['leading_public_value']==0.4437
    assert 'not an artifact-specific' in r['evidence_class']
