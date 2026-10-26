#!/usr/bin/env python3
"""Check a claimed research run card; never selects or uploads a submission.

The canonical gate is `gems_audit.eligibility.decide`. This structural check
is not the shared holdout evaluator, not the shared writer, and cannot verify
actual raster bytes, registry completeness or receipt authenticity by itself.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.eligibility import decide  # noqa: E402


def assess(card):
    return decide(card)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/promotion_gate.py RUN_CARD.json", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            result = assess(json.load(f))
    except (OSError, ValueError) as exc:
        print(json.dumps({"verdict": "negative", "slot_authorized": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["eligible_for_separate_selector"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
