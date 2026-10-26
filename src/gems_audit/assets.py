"""Resolve and verify the pinned public template and mirrored inputs."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, expected: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}; run python scripts/restore_assets.py --focus")
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected}, got {actual}")


def load_template():
    """Import the original shared package only after verifying every pinned byte."""
    pin = json.loads((ROOT / "registry/template_pins.json").read_text())
    for name, expected in pin["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("unsafe template pin path")
        verify(CACHE / "template" / name, expected)
    # Fail if another package with this name has already been imported.
    existing = sys.modules.get("gems57")
    expected_dir = (CACHE / "template/vendor/gems57").resolve()
    if existing and Path(existing.__file__).resolve().parent != expected_dir:
        raise RuntimeError("different gems57 package already loaded; refusing private fork")
    vendor = str(expected_dir.parent)
    if vendor not in sys.path:
        sys.path.insert(0, vendor)
    return importlib.import_module("gems57")


def verify_core() -> None:
    pins = json.loads((ROOT / "registry/data_pins.json").read_text())["files"]
    for row in pins:
        if row["group"] == "core" and row["id"] != "training_features":
            verify(CACHE / "data" / row["dest"], row["sha256"])
