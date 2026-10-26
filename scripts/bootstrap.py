#!/usr/bin/env python3
"""Restore the immutable shared template and, optionally, its owner-mirrored data.

No source is privately forked. Large inputs and the derived cache remain ignored
under .cache/. Hashes authenticate the mirror's bytes, not their organizer origin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
TEMPLATE_REF = "07806249f4ed3efe70b4fbf866183c32392b7853"
TEMPLATE_ARCHIVE_SHA = "74421783a733593d61893de323c3dfd6f4a2cf4a2af2d07bdd872e17bc3df12d"
TEMPLATE_URL = f"https://codeload.github.com/buffedlizard55-lab/GEMSDOE32/tar.gz/{TEMPLATE_REF}"
TEMPLATE = CACHE / "upstream" / f"GEMSDOE32-{TEMPLATE_REF}"
INPUTS = CACHE / "inputs"
WORK = CACHE / "work"
FEATURE_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
CRITICAL = {
    "vendor/gems57/evaluate_holdout.py": "ad86640b46f3c5fc6b1aceec4c4bfc82d03e35008b37ab2a8ad6076e6810ff3a",
    "vendor/gems57/submission_writer.py": "41220185ac2823fe5358603d38f2a915ea3e5f1ab1f94f0b237295b38b4a2565",
    "vendor/gems57/uniqueness.py": "1c5094b814277ae801ccea6a47cf744429cffcdc10f9cc79f229d5fc44a8df95",
    "vendor/gems57/metric.py": "4afe10cbaa229948520c75194b1ebc32676e72544f05582f0725092b097b4d7f",
    "vendor/gems57/holdout.py": "7a0a84176986190b527aa9c6a84216c2dab4b599f25b1143db5f420e85020ab1",
    "vendor/gems57/spatial.py": "fad7b09db9efc512247b9a176a7e7ce8631e287592b4e07902d0b9c38bed00f8",
    "vendor/gems57/gates.py": "7c57f70dbba58bb1112df4193a3de56516af0f981970d4b943b394f99b573dae",
    "vendor/gems57/grid.py": "b96df7ec0f33658a61b0baa5db85fcd19be2cd8b1873f99699bd26bddae8cd8d",
    "scripts/restore_data.py": "46d97fd30dea0b7ae62e0286f837059ad08828e7f74d49498693dc7dce50670f",
    "scripts/build_features.py": "8232b42e06c42d00942b1b2bc3bff2a3dba3d16c171be0a47d2435ee92e39087",
    "src/gems32/features.py": "58cff8551ba2f2eb5bbc5656306d8e19243c38721368ddd3d5e393c8e889e316",
    "registry/data_manifest.json": "e28b33ba35216e6b699bc0dd7a61926706276b558d21d2152f044b366b4cf795",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_template(path: Path) -> None:
    for relative, expected in CRITICAL.items():
        file = path / relative
        if not file.is_file() or sha256(file) != expected:
            raise RuntimeError(f"Shared template missing or changed: {relative}. Refusing private edits.")


def ensure_template() -> Path:
    """Fetch a pinned upstream archive; reject path traversal and modified code."""
    if TEMPLATE.exists():
        _verify_template(TEMPLATE)
        return TEMPLATE
    CACHE.mkdir(parents=True, exist_ok=True)
    archive = CACHE / f"template-{TEMPLATE_REF}.tar.gz"
    if not archive.exists() or sha256(archive) != TEMPLATE_ARCHIVE_SHA:
        tmp = archive.with_suffix(".download")
        try:
            with urllib.request.urlopen(TEMPLATE_URL, timeout=120) as source, tmp.open("wb") as out:
                shutil.copyfileobj(source, out)
            if sha256(tmp) != TEMPLATE_ARCHIVE_SHA:
                raise RuntimeError("Pinned template archive SHA-256 mismatch")
            os.replace(tmp, archive)
        finally:
            tmp.unlink(missing_ok=True)
    TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TEMPLATE.parent, prefix="extract-") as td:
        staging = Path(td)
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar.getmembers():
                p = Path(member.name)
                if (p.is_absolute() or ".." in p.parts or not p.parts
                        or p.parts[0] != TEMPLATE.name or not (member.isdir() or member.isfile())):
                    raise RuntimeError(f"Unsafe archive member: {member.name}")
            tar.extractall(staging)
        extracted = staging / TEMPLATE.name
        _verify_template(extracted)
        extracted.rename(TEMPLATE)
    return TEMPLATE


def restore_core(template: Path) -> None:
    if not shutil.which("gh"):
        raise RuntimeError("GitHub CLI (gh) is required to restore the pinned owner mirror")
    INPUTS.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(template / "scripts/restore_data.py"),
                    "--group", "core", "--target-dir", str(INPUTS)], check=True, cwd=ROOT)
    if sha256(INPUTS / "training_features.tif") != FEATURE_SHA:
        raise RuntimeError("Competition-feature mirror hash mismatch")


def build_features(template: Path) -> None:
    import numpy as np

    WORK.mkdir(parents=True, exist_ok=True)
    cache = WORK / "feature_stack.npy"
    receipt = WORK / "cache_integrity.json"
    if cache.exists() and receipt.exists():
        info = json.loads(receipt.read_text())
        if (info.get("source_sha256") == FEATURE_SHA and info.get("cache_sha256") == sha256(cache)
                and np.load(cache, mmap_mode="r").shape == (3730, 3292, 35)):
            print("Shared feature cache already verified.")
            return
        raise RuntimeError("Existing feature cache or receipt failed integrity checks; do not use it")
    env = os.environ.copy()
    env.update(GEMS_DATA_DIR=str(INPUTS), GEMS_WORK_DIR=str(WORK))
    subprocess.run([sys.executable, str(template / "scripts/build_features.py"),
                    "--features", str(INPUTS / "training_features.tif"),
                    "--out", str(cache), "--receipt", str(WORK / "feature_receipt.json")],
                   check=True, cwd=ROOT, env=env)
    if np.load(cache, mmap_mode="r").shape != (3730, 3292, 35):
        raise RuntimeError("Unexpected feature-cache shape")
    receipt.write_text(json.dumps({"source_sha256": FEATURE_SHA, "cache_sha256": sha256(cache),
                                   "template_ref": TEMPLATE_REF,
                                   "note": "Owner mirror; organizer provenance not authenticated"}, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", action="store_true", help="restore all four hash-pinned owner-mirror inputs")
    parser.add_argument("--features", action="store_true", help="restore data and build the shared 35-channel cache")
    args = parser.parse_args()
    template = ensure_template()
    print(f"Verified shared template: {template}", flush=True)
    if args.data or args.features:
        restore_core(template)
    if args.features:
        build_features(template)
    print("No experiment, prediction, or competition submission was made.")


if __name__ == "__main__":
    main()
