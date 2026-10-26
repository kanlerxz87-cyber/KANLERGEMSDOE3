import pytest
from refresh_public_feed import parse_leaderboard


def table(rows, header=True):
    # Structure informed by the public page, not a saved raw-HTML fixture.
    th = '<tr><th>Rank</th><th>Team members</th><th>Participant</th><th>Best<br>public<br>DW-Tversky</th><th>Shared work</th></tr>' if header else ''
    return '<html><body><table>' + th + ''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in row) + '</tr>' for row in rows) + '</table></body></html>'


GOOD = [('#1','','<a>xiao&amp;fan</a><br>18h ago<br>31 submissions','<strong>0.4437</strong>',''),
        ('#2','','second<br>2d ago','0.3916','')]


def test_extract_rank_one_with_nested_tags_and_entities():
    assert parse_leaderboard(table(GOOD)) == {'rank':1, 'participant':'xiao&fan', 'value':'0.4437'}


@pytest.mark.parametrize('data', [
    '<html>login required</html>',
    table(GOOD, header=False),
    table([('1','','person','NaN',''), ('2','','other','0.1','')]),
    table([('1','','person','-0.1',''), ('2','','other','0.1','')]),
    table([('1','','person','1.1',''), ('2','','other','0.1','')]),
    table([('2','','person','0.9',''), ('3','','other','0.1','')]),
    table([('1','','first','0.9',''),('1','','other','0.8','')]),
    table([('1','','','0.9',''),('2','','other','0.8','')]),
    table([('1','','person','0.8',''),('2','','other','0.9','')]),
    table([('1','','person','0.9','0.2'),('2','','other','0.8','')]),
])
def test_invalid_or_ambiguous_feed_fails_closed(data):
    with pytest.raises(ValueError):
        parse_leaderboard(data)
