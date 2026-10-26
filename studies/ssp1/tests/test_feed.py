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


def test_foreign_or_wrong_page_redirect_never_becomes_official_observation():
    old={'leading_public_value':0.4437,'last_success_utc':'2026-10-26'}
    for url in ['https://example.org/leaderboard/', 'http://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/', 'https://www.drivendata.org/competitions/999/leaderboard/']:
        response=Response();response.url=url
        r=refresh(old,lambda*a,**kw:response)
        assert r['stale'] and r['leading_public_value']==0.4437
        assert r['last_success_utc']=='2026-10-26'


def test_cross_run_cache_preserves_newest_good_observation_on_failure():
    from kanler.feed import select_snapshot,URL
    old={'source':URL,'leading_public_value':0.4437,'last_success_utc':'2026-10-26'}
    cache={**old,'leading_public_value':0.5,'last_success_utc':'2026-10-27T12:00:00+00:00'}
    selected=select_snapshot(old,cache)
    def fail(*a,**kw):raise requests.Timeout('unavailable')
    result=refresh(selected,fail)
    assert result['leading_public_value']==0.5 and result['stale']
    assert result['last_success_utc']==cache['last_success_utc']
    assert select_snapshot(cache,old)==cache
    assert select_snapshot(old,{**cache,'source':'https://example.org'})==old
    assert select_snapshot(old,{**cache,'leading_public_value':True})==old
    assert select_snapshot(old,{**cache,'last_success_utc':'malformed'})==old


def test_success_has_precise_updated_provenance_and_zero_is_a_valid_score():
    r=refresh({},lambda*a,**kw:Response())
    assert r['last_success_precision']=='ISO-8601 UTC instant'
    assert r['observed_utc_day']==r['last_success_utc'][:10]
    assert parse_leaderboard(HTML.replace('0.4437','0'))==0


def test_inline_score_fragments_match_browser_text_without_invented_spaces():
    html=HTML.replace('0.4437','<span>0.</span><strong>4437</strong>').replace('DW-Tversky','DW-<span>Tversky</span>')
    assert parse_leaderboard(html)==0.4437
    assert parse_leaderboard(html.replace('Tversky','TVERSKY'))==0.4437


def test_rank_one_cannot_be_borrowed_from_an_unrelated_trailing_table():
    html=HTML.replace('#1','#11')+'<table><tr><td>#1</td><td>unrelated</td><td>0.9999</td></tr></table>'
    with pytest.raises(ValueError):parse_leaderboard(html)


def test_conflicting_metric_tables_fail_closed_but_identical_responsive_twins_agree():
    assert parse_leaderboard(HTML+HTML)==0.4437
    with pytest.raises(ValueError):parse_leaderboard(HTML+HTML.replace('0.4437','0.5'))


def test_parse_failure_has_a_bounded_public_shape_not_a_new_observation():
    response=Response();response.text=HTML.replace('#1','#11')
    old={'leading_public_value':0.4437,'last_success_utc':'2026-10-26'}
    result=refresh(old,lambda*a,**kw:response)
    assert result['stale'] and result['leading_public_value']==0.4437
    assert result['parse_diagnostic']['n_tables']==1
    assert len(result['parse_diagnostic']['first_column_samples'])<=5


def test_private_header_or_malformed_table_never_fabricates_a_public_observation():
    with pytest.raises(ValueError):parse_leaderboard(HTML.replace('public','private'))
    with pytest.raises(ValueError):parse_leaderboard('<table><tr><td>broken</tr></td></table>')
