#!/usr/bin/env python3
"""Read the public leaderboard and focus repo heads; never log in or submit.

The job updates a public GitHub Release body, not a branch. If any official
page, parser, or peer-head check fails, exit nonzero without publishing a new
snapshot. The static site retains and timestamps its last verified fallback.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LB_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
SITES = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")
UA = "GEMS-research-workbench/1.0 (public leaderboard; no login or submissions)"


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.table, self.row, self.cell = [], None, None, None
        self.table_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'table':
            self.table_depth += 1
            if self.table_depth == 1:
                self.table = []
        elif self.table_depth == 1 and tag == 'tr':
            self.row = []
        elif self.table_depth == 1 and self.row is not None and tag in ('td', 'th'):
            self.cell = []
        elif self.cell is not None and tag in ('br', 'p', 'div'):
            self.cell.append('\n')

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.table_depth == 1 and tag in ('td', 'th') and self.cell is not None:
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        elif self.table_depth == 1 and tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table_depth:
            if self.table_depth == 1 and self.table is not None:
                self.tables.append(self.table)
                self.table = None
            self.table_depth -= 1

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def parse_leaderboard(html: str) -> dict:
    parser = TableParser()
    parser.feed(html)
    matches = []
    for table in parser.tables:
        if not table:
            continue
        headers = [' '.join(c.lower().split()) for c in table[0]]
        if not any('rank' in c for c in headers) or not any('participant' in c for c in headers):
            continue
        if not any('tversky' in c or ('public' in c and 'best' in c) for c in headers):
            continue
        participant_i = next(i for i, c in enumerate(headers) if 'participant' in c)
        rows = []
        for cells in table[1:]:
            if len(cells) <= participant_i or not re.fullmatch(r'#?\s*\d+', cells[0].strip()):
                continue
            rank = int(re.sub(r'\D', '', cells[0]))
            possibilities = [c.strip() for c in cells[1:] if re.fullmatch(r'(?:0(?:\.\d+)?|1(?:\.0+)?)', c.strip())]
            if len(possibilities) != 1:
                raise ValueError('Ambiguous leaderboard score cells')
            score = possibilities[0]
            participant_lines = [' '.join(line.split()) for line in cells[participant_i].splitlines() if line.strip()]
            if not participant_lines:
                raise ValueError('Missing participant')
            rows.append({'rank': rank, 'participant': participant_lines[0][:200], 'value': score})
        if len(rows) >= 2 and rows[0]['rank'] == 1:
            if any(rows[i]['rank'] >= rows[i+1]['rank'] or float(rows[i]['value']) < float(rows[i+1]['value'])
                   for i in range(len(rows)-1)):
                raise ValueError('Leaderboard rows are not ordered')
            matches.append(rows[0])
    if len(matches) != 1:
        raise ValueError('Could not uniquely identify a ranked public Tversky leaderboard')
    return matches[0]


def fetch(url: str, allowed_host: str, timeout=25) -> str:
    if urlparse(url).scheme != 'https' or urlparse(url).hostname != allowed_host:
        raise ValueError('Unexpected source host')
    request = Request(url, headers={'User-Agent': UA, 'Cache-Control': 'no-cache', 'Accept': 'application/json' if allowed_host == 'api.github.com' else 'text/html'})
    with urlopen(request, timeout=timeout) as response:
        final = urlparse(response.geturl())
        if final.scheme != 'https' or final.hostname != allowed_host or response.status != 200:
            raise ValueError('Unexpected redirect or HTTP response')
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError('Response too large')
    return raw.decode('utf-8', errors='strict')


def refresh() -> dict:
    top = parse_leaderboard(fetch(LB_URL, 'www.drivendata.org'))
    heads = []
    for site in SITES:
        endpoint = f'https://api.github.com/repos/buffedlizard55-lab/{site}/commits/main'
        body = json.loads(fetch(endpoint, 'api.github.com'))
        sha = body.get('sha', '')
        date = body.get('commit', {}).get('committer', {}).get('date')
        if not re.fullmatch(r'[0-9a-f]{40}', sha) or not isinstance(date, str):
            raise ValueError(f'Unverifiable commit head for {site}')
        heads.append({'site': site, 'sha': sha, 'committed_utc': date})
    return {'schema': 'gems-public-feed-v1', 'observed_utc': datetime.now(timezone.utc).isoformat(),
            'source': LB_URL, 'evidence_class': 'ORGANIZER-PUBLISHED PUBLIC LEADERBOARD; not a file-specific receipt',
            'leaderboard': top, 'site_heads': heads,
            'scope': 'Public page and public GitHub heads only; not a candidate score or a uniqueness audit.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = refresh()
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(args.output.suffix + '.tmp')
        tmp.write_text(text, encoding='utf-8')
        tmp.replace(args.output)
        print('Validated public feed:', result['observed_utc'])
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'PUBLIC FEED NOT REFRESHED: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
