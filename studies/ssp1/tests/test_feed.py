import pytest

from kanler.feed import parse_leaderboard, public_table_shape, refresh


HTML = '''<table><tr><th>Rank</th><th>Participant</th><th>Best public DW-Tversky</th></tr>
<tr><td>#1</td><td>someone 31 submissions</td><td>0.4437</td></tr>
<tr><td>#2</td><td>someone else</td><td>0.3916</td></tr></table>'''


def test_offline_public_table_not_arbitrary_numeric_matches():
    assert parse_leaderboard(HTML) == 0.4437
    with pytest.raises(ValueError):
        parse_leaderboard('<h1>Login</h1>0.9999')
    with pytest.raises(ValueError):
        parse_leaderboard(HTML.replace('#1', '#11'))
    assert parse_leaderboard(HTML.replace('0.4437', '0')) == 0


def test_refresh_never_calls_network_even_when_legacy_callback_is_supplied():
    old = {'leading_public_value': 0.4437, 'last_success_utc': '2026-10-26', 'stale': False}
    def forbidden(*args, **kwargs):
        raise AssertionError('network callback must never be called')
    result = refresh(old, forbidden)
    assert result['leading_public_value'] == old['leading_public_value']
    assert result['last_success_utc'] == old['last_success_utc']
    assert result['stale'] is True
    assert result['monitoring_status'] == 'disabled_under_published_terms'
    assert result['remaining_weekly_slots'] is None
    assert result['authenticated_submission_receipts'] is None
    assert 'last_policy_check_utc' in result
    assert 'last_attempt_utc' not in result  # no network request was attempted


def test_refresh_without_a_past_observation_never_fabricates_one():
    result = refresh({})
    assert result['stale'] is True
    assert 'leading_public_value' not in result
    assert 'last_success_utc' not in result


def test_inline_score_fragments_match_browser_text_without_invented_spaces():
    html = HTML.replace('0.4437', '<span>0.</span><strong>4437</strong>').replace('DW-Tversky', 'DW-<span>Tversky</span>')
    assert parse_leaderboard(html) == 0.4437
    assert parse_leaderboard(html.replace('Tversky', 'TVERSKY')) == 0.4437


def test_rank_one_cannot_be_borrowed_from_an_unrelated_trailing_table():
    html = HTML.replace('#1', '#11') + '<table><tr><td>#1</td><td>unrelated</td><td>0.9999</td></tr></table>'
    with pytest.raises(ValueError):
        parse_leaderboard(html)


def test_conflicting_metric_tables_fail_closed_but_identical_responsive_twins_agree():
    assert parse_leaderboard(HTML + HTML) == 0.4437
    with pytest.raises(ValueError):
        parse_leaderboard(HTML + HTML.replace('0.4437', '0.5'))


def test_parse_diagnostic_is_bounded_and_never_a_new_observation():
    diagnostic = public_table_shape(HTML.replace('#1', '#11'))
    assert diagnostic['n_tables'] == 1
    assert len(diagnostic['first_column_samples']) <= 5


def test_private_header_or_malformed_table_never_fabricates_a_public_observation():
    with pytest.raises(ValueError):
        parse_leaderboard(HTML.replace('public', 'private'))
    with pytest.raises(ValueError):
        parse_leaderboard('<table><tr><td>broken</tr></td></table>')
