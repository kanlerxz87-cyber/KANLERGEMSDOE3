from __future__ import annotations
import os
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[2]
DATA_RAW: Path = Path(os.environ.get("KANLER3_DATA_DIR", ROOT / "data" / "raw"))
CACHE_DIR: Path = Path(os.environ.get("KANLER3_CACHE_DIR", ROOT / ".cache" / "kanler3"))

def data_dir() -> Path:
    return DATA_RAW

def cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR
