"""Public-only leaderboard feed. A failed request never erases a good snapshot."""
from __future__ import annotations
from html.parser import HTMLParser
import re
from datetime import datetime,timezone
from urllib.parse import urlsplit

URL='https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'

class TableRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables=[];self.rows=[];self.row=None;self.cell=None;self.depth=0
    def handle_starttag(self,tag,attrs):
        if tag=='table':
            self.depth+=1
            if self.depth==1:self.tables.append([])
        if self.depth!=1:return
        if tag=='tr':self.row=[]
        if tag in ('td','th')and self.row is not None:self.cell=[]
        if tag=='br'and self.cell is not None:self.cell.append(' ')
    def handle_data(self,data):
        if self.depth==1 and self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=='table':
            self.depth=max(0,self.depth-1)
            if not self.depth:self.row=None;self.cell=None
            return
        if self.depth!=1:return
        if tag in ('td','th')and self.cell is not None:
            # Adjacent inline nodes must not gain invented spaces: a rendered
            # <span>0.</span><span>4437</span> is the number 0.4437.
            if self.row is not None:self.row.append(' '.join(''.join(self.cell).split()))
            self.cell=None
        if tag=='tr'and self.row is not None:
            self.tables[-1].append(self.row);self.rows.append(self.row);self.row=None


def parse_leaderboard(html:str)->float:
    p=TableRows();p.feed(html);values=[]
    for table in p.tables:
        for i,row in enumerate(table):
            score_column=next((j for j,s in enumerate(row)if 'tversky'in s.casefold() and 'public'in s.casefold()),None)
            rank_column=next((j for j,s in enumerate(row)if s.strip().casefold()=='rank'),None)
            if score_column is None or rank_column is None:continue
            for data in table[i+1:]:
                if len(data)<=max(score_column,rank_column):continue
                if not re.fullmatch(r'#?\s*1',data[rank_column]):continue
                value=data[score_column].strip()
                if re.fullmatch(r'(?:0(?:\.\d{1,8})?|1(?:\.0{1,8})?)',value):values.append(float(value))
    if values and len(set(values))==1:return values[0]
    if values:raise ValueError('Conflicting rank-one Tversky tables; preserve the last verified observation')
    raise ValueError('No recognizable rank-one DW-Tversky table; leave the last verified observation unchanged')


def public_table_shape(html:str)->dict:
    """Minimal public parse diagnosis, never an arbitrary-number fallback."""
    p=TableRows();p.feed(html)
    return {'n_tables':len(p.tables),'n_rows':len(p.rows),
            'metric_headers':[[c[:120]for c in row]for row in p.rows if any('tversky'in c.casefold()for c in row)][:2],
            'first_column_samples':[row[0][:80]for row in p.rows[:5]if row]}


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
        try:
            value=parse_leaderboard(response.text)
        except ValueError:
            out['parse_diagnostic']=public_table_shape(response.text)
            raise
        out.pop('parse_diagnostic',None)
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
