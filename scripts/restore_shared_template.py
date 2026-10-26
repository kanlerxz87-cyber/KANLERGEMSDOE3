#!/usr/bin/env python3
"""Restore the *unchanged*, hash-pinned shared template and optional band cache.

The public bridge is a participant mirror, not authenticated organizer data.
This is data/tool preparation only: it never runs a model, writes a candidate,
promotes a submission, or contacts DrivenData. Large files stay in .cache/.

    python scripts/restore_shared_template.py                # template only
    python scripts/restore_shared_template.py --check        # no network
    python scripts/restore_shared_template.py --cache-features  # ~419 MB download

Competition use and redistribution remain subject to the source licenses and
competition rules. Hashes establish byte identity, not licensing or origin.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "registry/shared_template_pins.json"
TEMPLATE = ROOT / ".cache/template57"
WORK = ROOT / ".cache/template57-work"
BRIDGE_REPO = "buffedlizard55-lab/6GEMSDOE"
BRIDGE_COMMIT = "e2fe3f41c6f5dd2dcb2fc91958ee67698f114ada"
FEATURE_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
SAMPLE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
PARTS = [
    (94371840, "0a330f8951af6c921029e25c84a579319d2db554d62d30d894d6ddc97f98cff7"),
    (94371840, "3c98037b2c997e3bbfcdfc2d9a982e8b820a77410dd7404b05cdb80594922c50"),
    (94371840, "c375c4dbc40c59bbaece572b5e348700b75935f9a30c879c82b6417e0836f31c"),
    (94371840, "b164159e6d0cb2595bc9f63a948af2646b124114a9c5921880c7516092137320"),
    (41425484, "fa0a6f9c936fac1d6f20ca37f5929b2d60bf7a80f3d477dcab886f941aee2696"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def matches(path: Path, digest: str) -> bool:
    return path.is_file() and sha256(path) == digest


def extract_pinned(stream, targets: dict[str, dict]) -> None:
    """Read selected tar members without extractall/path traversal or unchecked writes.

    Each target supplies a destination, expected sha256 and optional byte size.
    Names in the archive are matched after its generated top-level directory;
    symlinks, missing members, duplicates, unexpected sizes and bad hashes fail.
    """
    remaining = set(targets)
    seen: set[str] = set()
    with tarfile.open(fileobj=stream, mode="r|gz") as archive:
        for member in archive:
            pieces = member.name.split("/", 1)
            if len(pieces) != 2 or pieces[1] not in targets:
                continue
            key = pieces[1]
            if key in seen:
                raise ValueError(f"duplicate archive member: {key}")
            seen.add(key)
            spec = targets[key]
            if not member.isfile():
                raise ValueError(f"archive member is not a regular file: {key}")
            if "size" in spec and member.size != spec["size"]:
                raise ValueError(f"archive member size mismatch: {key}")
            # Template files and sample are small; feature parts have explicit sizes.
            if "size" not in spec and member.size > 8 * 1024 * 1024:
                raise ValueError(f"unexpectedly large unbounded archive member: {key}")
            destination = Path(spec["destination"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(prefix="." + destination.name + ".", dir=destination.parent)
            tmp = Path(tmp_name)
            try:
                h = hashlib.sha256()
                with os.fdopen(fd, "wb") as out:
                    source = archive.extractfile(member)
                    if source is None:
                        raise ValueError(f"cannot read archive member: {key}")
                    for chunk in iter(lambda: source.read(1 << 20), b""):
                        out.write(chunk)
                        h.update(chunk)
                if h.hexdigest() != spec["sha256"]:
                    raise ValueError(f"archive member hash mismatch: {key}")
                os.replace(tmp, destination)
                remaining.remove(key)
            finally:
                tmp.unlink(missing_ok=True)
    if remaining:
        raise ValueError("missing pinned archive members: " + ", ".join(sorted(remaining)))


def download_archive(repo: str, commit: str, targets: dict[str, dict]) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("invalid pinned repository")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("invalid immutable commit")
    url = f"https://codeload.github.com/{repo}/tar.gz/{commit}"
    req = Request(url, headers={"User-Agent": "gems-evidence-recovery/1"})
    with urlopen(req, timeout=180) as response:
        extract_pinned(response, targets)


def verify_template(pins: dict) -> bool:
    return all(matches(TEMPLATE / name, spec["sha256"]) for name, spec in pins["files"].items())


def restore_template(pins: dict, offline: bool) -> bool:
    if not verify_template(pins):
        if offline:
            return False
        prefix = "https://github.com/"
        source = pins["source_repository"]
        if not source.startswith(prefix):
            raise ValueError("template repository must be a GitHub URL")
        targets = {name: {"destination": TEMPLATE / name, **spec}
                   for name, spec in pins["files"].items()}
        download_archive(source[len(prefix):], pins["source_commit"], targets)
    return verify_template(pins)


def restore_bridge(offline: bool) -> tuple[Path, Path]:
    feature = WORK / "data/official/training_features.tif"
    sample = WORK / "data/official/sample_submission.tif"
    if matches(feature, FEATURE_SHA) and matches(sample, SAMPLE_SHA):
        return feature, sample
    if offline:
        raise FileNotFoundError("hash-pinned bridge features or sample not available offline")
    prefix = "data/bridge/gems-geodawn-numerical-features.tif.part-"
    part_dir = WORK / ".cache/source_parts"
    targets = {
        prefix + f"{i:03d}": {"destination": part_dir / f"part-{i:03d}", "size": size, "sha256": digest}
        for i, (size, digest) in enumerate(PARTS)
    }
    targets["data/bridge/example_submission.tif"] = {"destination": sample, "sha256": SAMPLE_SHA}
    download_archive(BRIDGE_REPO, BRIDGE_COMMIT, targets)
    feature.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".training_features.", suffix=".partial", dir=feature.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as out:
            for i in range(len(PARTS)):
                with (part_dir / f"part-{i:03d}").open("rb") as src:
                    shutil.copyfileobj(src, out, length=1 << 20)
        if not matches(tmp, FEATURE_SHA):
            raise ValueError("assembled feature raster does not match pinned SHA-256")
        os.replace(tmp, feature)
    finally:
        tmp.unlink(missing_ok=True)
    for i in range(len(PARTS)):
        (part_dir / f"part-{i:03d}").unlink(missing_ok=True)
    return feature, sample


def verify_band_cache(expected: list[str]) -> bool:
    if len(expected) != 19:
        return False
    return all(matches(WORK / ".cache/features" / f"band-{i:02d}.npy", digest)
               for i, digest in enumerate(expected, 1))


def cache_features(pins: dict, offline: bool) -> dict:
    feature, sample = restore_bridge(offline)
    expected = pins["expected_band_sha256"]
    if not verify_band_cache(expected):
        # Execute the byte-identical original function, not a local reimplementation.
        path = TEMPLATE / "scripts/prepare_data.py"
        spec = importlib.util.spec_from_file_location("pinned_template_prepare_data", path)
        if spec is None or spec.loader is None:
            raise ImportError("cannot load the verified shared cache builder")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.cache_bands(WORK)
    if not verify_band_cache(expected):
        raise ValueError("generated cache does not match every pinned template band")
    return {
        "source_sha256": sha256(feature),
        "sample_sha256": sha256(sample),
        "bands_verified": len(expected),
        "band_hashes_match_shared_template": True,
        "organizer_authenticated": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify existing files without network access")
    ap.add_argument("--cache-features", action="store_true", help="restore mirror and regenerate the shared cached bands")
    args = ap.parse_args()
    try:
        pins = json.loads(PINS.read_text(encoding="utf-8"))
        if not restore_template(pins, args.check):
            raise FileNotFoundError("the complete hash-pinned shared template is not cached")
        result = {"kind": "DATA-MEASUREMENT", "template_verified": True,
                  "template_commit": pins["source_commit"],
                  "provenance": "third-party template and bridge; not organizer-authenticated",
                  "license_status": "not verified", "model_experiment_run": False}
        if args.cache_features:
            result["cache"] = cache_features(pins, args.check)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, tarfile.TarError, ImportError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "candidate_created": False}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
