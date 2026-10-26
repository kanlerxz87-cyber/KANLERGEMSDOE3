#!/usr/bin/env python3
"""Refresh public facts only; never log in, train, pick a slot or submit a file."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from kanler.feed import refresh
if __name__=='__main__':
    p=ROOT/'registry/leaderboard_snapshot.json'
    result=refresh(json.loads(p.read_text()))
    p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))
    # Staleness is an explicit observable state, not an excuse to fabricate a score.
