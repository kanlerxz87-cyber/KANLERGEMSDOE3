"""Public-only leaderboard feed. A failed request never erases a good snapshot."""
from __future__ import annotations
from html.parser import HTMLParser
import re
from datetime import datetime,timezone

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
            if re.fullmatch(r'(?:0\.\d{1,8}|1(?:\.0{1,8})?)',value):
                return float(value)
    raise ValueError('No recognizable rank-one DW-Tversky table; leave the last verified observation unchanged')


def refresh(old:dict,get=None)->dict:
    import requests
    now=datetime.now(timezone.utc).isoformat()
    out={**old,'last_attempt_utc':now,'authenticated_submission_receipts':None,'remaining_weekly_slots':None}
    try:
        response=(get or requests.get)(URL,timeout=15,headers={'User-Agent':'KANLER-GEMS-public-audit/0.1'})
        response.raise_for_status()
        if '/accounts/login' in response.url:
            raise ValueError('Public page unexpectedly redirected to login')
        value=parse_leaderboard(response.text)
        out.update({'last_success_utc':now,'leading_public_value':value,'stale':False,'last_error':None,'evidence_class':'ORGANIZER-PUBLISHED PUBLIC LEADERBOARD OBSERVATION; not an artifact-specific ORGANIZER-CONFIRMED submission receipt'})
    except (requests.RequestException,ValueError)as exc:
        out.update({'stale':True,'last_error':str(exc)[:400]})
    return out
