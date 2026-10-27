#!/usr/bin/env python3
"""Mark a recorded leaderboard observation stale without contacting DrivenData.

The optional state path is output-only; no cache is promoted to a new trusted
observation. This script never logs in, polls, trains, selects a slot or uploads.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from kanler.feed import refresh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-path', type=Path)
    args = parser.parse_args()
    p = ROOT/'registry/leaderboard_snapshot.json'
    recorded = json.loads(p.read_text())
    result = refresh(recorded)
    serialized = json.dumps(result, indent=2, allow_nan=False)+'\n'
    p.write_text(serialized)
    if args.state_path:
        args.state_path.parent.mkdir(parents=True, exist_ok=True)
        args.state_path.write_text(serialized)
    print(serialized, end='')
    # A stale observation is an explicit state, never a fabricated new score.


if __name__ == '__main__':
    main()
