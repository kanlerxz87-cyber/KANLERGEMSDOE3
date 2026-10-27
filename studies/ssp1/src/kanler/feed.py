"""Offline leaderboard snapshot helpers; no automated DrivenData access.

DrivenData's published terms prohibit automated access, including monitoring.
Keep the historical observation explicitly stale; a parser is retained only
for offline fixtures, never as permission to fetch or authenticate the website.
"""
from __future__ import annotations
from html.parser import HTMLParser
import re
from datetime import datetime,timezone

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
    """Mark the recorded snapshot stale without performing any network request.

    The legacy `get` argument is ignored deliberately, even when supplied: a
    callback must not accidentally reactivate monitoring from a scheduled job.
    This function cannot turn a public board observation into a file receipt.
    """
    now=datetime.now(timezone.utc).isoformat()
    return {**old, 'source':URL, 'last_policy_check_utc':now,
            'authenticated_submission_receipts':None, 'remaining_weekly_slots':None,
            'stale':True, 'monitoring_status':'disabled_under_published_terms',
            'last_error':'Automated DrivenData monitoring disabled; the historical observation is not live.'}
