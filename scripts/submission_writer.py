#!/usr/bin/env python3
"""Thin CLI/module entry delegating to root ``submission_writer.py``."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from submission_writer import MAX_NOTE_CHARS, main, write_pair  # noqa: E402,F401

if __name__ == "__main__":
    raise SystemExit(main())
