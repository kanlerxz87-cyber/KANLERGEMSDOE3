#!/usr/bin/env python3
"""Refresh public facts only; never log in, train, choose a slot, or upload.

--state-path persists the last good observation across scheduled Pages builds,
without pushing a commit to main or regressing to an old checkout on failures.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from kanler.feed import refresh, select_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-path', type=Path)
    args = parser.parse_args()
    p = ROOT/'registry/leaderboard_snapshot.json'
    recorded = json.loads(p.read_text())
    cached = None
    if args.state_path and args.state_path.is_file():
        try:
            cached = json.loads(args.state_path.read_text())
        except (ValueError, OSError):
            pass
    result = refresh(select_snapshot(recorded, cached))
    serialized = json.dumps(result, indent=2, allow_nan=False)+'\n'
    p.write_text(serialized)
    if args.state_path:
        args.state_path.parent.mkdir(parents=True, exist_ok=True)
        args.state_path.write_text(serialized)
    print(serialized, end='')
    # A stale observation is an explicit state, never a fabricated new score.


if __name__ == '__main__':
    main()
