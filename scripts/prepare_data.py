#!/usr/bin/env python3
"""Delegate raw-band preparation to the locked shared template, without a fork.

This sanitizes raw band copies using upstream prepare_data.py. It does NOT build
or replace the parallel protocol's 35-channel cached feature stack.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.shared_tools import load_tool


def main() -> int:
    os.environ.setdefault("GEMS_DATA_DIR", str(ROOT / "data" / "core"))
    os.environ.setdefault("GEMS_WORK_DIR", str(ROOT / "data" / "prepared"))
    tool = load_tool("prepare_data")
    result = tool.prepare()
    # Upstream also writes inside its own data/ directory. Keep the durable
    # report with this project's ignored inputs, not in the source-locked files.
    (ROOT / "data" / "prepared_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "RAW_BANDS_PREPARED", "feature_stack_rebuilt": False, "grid": result["grid"], "counts": result["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
