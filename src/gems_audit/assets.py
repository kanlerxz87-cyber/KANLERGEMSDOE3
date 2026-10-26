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
    # Refuse a previously loaded alternative parent OR submodule. Prioritize
    # the verified vendor directory even if sys.path was already modified.
    expected_dir = (CACHE / "template/vendor/gems57").resolve()
    def check_loaded():
        for name, module in list(sys.modules.items()):
            if name == "gems57" or name.startswith("gems57."):
                location = getattr(module, "__file__", None)
                if not location or not Path(location).resolve().is_relative_to(expected_dir):
                    raise RuntimeError(f"different {name} package already loaded; refusing private fork")
    check_loaded()
    vendor = str(expected_dir.parent)
    if vendor in sys.path:
        sys.path.remove(vendor)
    sys.path.insert(0, vendor)
    result = importlib.import_module("gems57")
    check_loaded()
    return result


def verify_core() -> None:
    pins = json.loads((ROOT / "registry/data_pins.json").read_text())["files"]
    for row in pins:
        if row["group"] == "core" and row["id"] != "training_features":
            destination = Path(row["dest"])
            if destination.is_absolute() or ".." in destination.parts:
                raise ValueError("unsafe destination in data manifest")
            verify(CACHE / "data" / destination, row["sha256"])
