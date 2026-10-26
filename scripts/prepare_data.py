#!/usr/bin/env python3
"""Delegate to the pinned shared template's prepare_data.py; no private fork."""
from __future__ import annotations
import os
from pathlib import Path
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    template = Path(subprocess.check_output(["bash", str(ROOT / "scripts/bootstrap_template.sh")], text=True).strip())
    os.environ.setdefault("GEMS_DATA_DIR", str(ROOT / ".cache/gems_data"))
    os.environ.setdefault("GEMS_WORK_DIR", str(ROOT / ".cache/gems_work"))
    runpy.run_path(str(template / "scripts/prepare_data.py"), run_name="__main__")


if __name__ == "__main__":
    main()
