"""Public-only leaderboard feed. A failed request never erases a good snapshot."""
from __future__ import annotations
from html.parser import HTMLParser
import re
from datetime import datetime,timezone
from urllib.parse import urlsplit

URL='https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'

class TableRows(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ('td','th')and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th')and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
        if tag=='tr'and self.row is not None:
            self.rows.append(self.row);self.row=None


def parse_leaderboard(html:str)->float:
    p=TableRows();p.feed(html)
    for i,row in enumerate(p.rows):
        if not any('Tversky'in s for s in row):continue
        score_column=next((j for j,s in enumerate(row)if 'Tversky'in s),None)
        for data in p.rows[i+1:]:
            if not data or score_column is None or len(data)<=score_column:continue
            # Require the leading ranked data row, not an arbitrary number in an
            # error page, a submission count, or an unrelated trailing table.
            if not re.fullmatch(r'#?\s*1',data[0]):continue
            value=data[score_column].strip()
            if re.fullmatch(r'(?:0(?:\.\d{1,8})?|1(?:\.0{1,8})?)',value):
                return float(value)
    raise ValueError('No recognizable rank-one DW-Tversky table; leave the last verified observation unchanged')


def refresh(old:dict,get=None)->dict:
    import requests
    now=datetime.now(timezone.utc).isoformat()
    out={**old,'source':URL,'last_attempt_utc':now,'authenticated_submission_receipts':None,'remaining_weekly_slots':None}
    try:
        response=(get or requests.get)(URL,timeout=15,headers={'User-Agent':'KANLER-GEMS-public-audit/0.1'})
        response.raise_for_status()
        if '/accounts/login' in response.url:
            raise ValueError('Public page unexpectedly redirected to login')
        final=urlsplit(response.url)
        if final.scheme!='https' or final.hostname not in ('www.drivendata.org','drivendata.org') or final.path.rstrip('/')!=urlsplit(URL).path.rstrip('/'):
            raise ValueError('Unexpected source redirect; do not label another page as an official GEMS leaderboard')
        value=parse_leaderboard(response.text)
        out.update({'last_success_utc':now,'last_success_precision':'ISO-8601 UTC instant','observed_utc_day':now[:10],'observation_method':'HTTPS official public rank-one Tversky table parsed by the public-only feed','leading_public_value':value,'stale':False,'last_error':None,'evidence_class':'ORGANIZER-PUBLISHED PUBLIC LEADERBOARD OBSERVATION; not an artifact-specific ORGANIZER-CONFIRMED submission receipt'})
    except (requests.RequestException,ValueError)as exc:
        out.update({'stale':True,'last_error':str(exc)[:400]})
    return out


def select_snapshot(recorded:dict,cached:dict|None)->dict:
    """Choose the newer last-good official observation across stateless CI jobs.

    A cache is a persistence layer, not a new source or an authorization receipt.
    Malformed, foreign-source, or older cache records never erase the Git record.
    """
    if not isinstance(cached,dict) or cached.get('source')!=URL:
        return recorded.copy()
    def instant(value):
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    try:
        value=cached['leading_public_value']
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not 0<=value<=1:
            return recorded.copy()
        if instant(cached['last_success_utc'])>instant(recorded['last_success_utc']):
            return cached.copy()
    except (KeyError,ValueError,TypeError,AttributeError):
        pass
    return recorded.copy()
