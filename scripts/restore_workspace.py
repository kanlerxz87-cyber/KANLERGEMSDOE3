#!/usr/bin/env python3
"""Restore immutable public-mirror inputs and the *unchanged* shared template.

No secrets or cookies are handled here: gh uses its existing configuration.
SHA-256 pins prove mirror-byte integrity, not independent official provenance.
The target cache is deliberately ignored by Git. Mismatched existing files are
never overwritten; failed downloads cannot become valid-looking files.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "config/pins.json"
ANCHORS = ROOT / "config/focus_anchors.json"
DEFAULT_CACHE = ROOT / ".cache"


def sha256_file(path: Path) -> str:
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verify_file(path: Path, spec: dict) -> bool:
    path = Path(path)
    if not path.is_file():
        return False
    if path.stat().st_size != spec["bytes"] or sha256_file(path) != spec["sha256"]:
        raise ValueError(f"Refusing to overwrite mismatched file: {path}")
    return True


def _endpoint(spec: dict) -> str:
    repo = spec["repo"]
    if spec.get("blob_sha1"):
        return f"repos/{repo}/git/blobs/{spec['blob_sha1']}"
    return f"repos/{repo}/contents/{spec['path']}?ref={spec['commit']}"


def restore_file(path: Path, spec: dict, *, fetch: bool) -> Path:
    path = Path(path)
    if verify_file(path, spec):
        return path
    if not fetch:
        raise FileNotFoundError(f"Missing {path}; rerun with --fetch")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            proc = subprocess.run(
                ["gh", "api", _endpoint(spec), "-H", "Accept: application/vnd.github.raw+json"],
                stdout=stream, stderr=subprocess.PIPE, timeout=300, check=False,
            )
        if proc.returncode:
            raise RuntimeError(f"GitHub download failed: {_endpoint(spec)}: {proc.stderr.decode(errors='replace')[:500]}")
        if not verify_file(temporary, spec):
            raise ValueError(f"Downloaded file is absent: {_endpoint(spec)}")
        # os.link fails rather than clobbering another process's completed file.
        try:
            os.link(temporary, path)
        except FileExistsError:
            verify_file(path, spec)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def restore_features(cache: Path, entry: dict, *, fetch: bool) -> Path:
    destination = cache / "data" / entry["dest"]
    if verify_file(destination, entry):
        return destination
    if not fetch:
        raise FileNotFoundError(f"Missing {destination}; rerun with --fetch")
    part_dir = cache / "data/parts"
    specs = [{**part, "repo": entry["repo"], "commit": entry["commit"]} for part in entry["parts"]]
    def fetch_part(item):
        i, spec = item
        return restore_file(part_dir / f"part-{i:03d}", spec, fetch=fetch)
    with ThreadPoolExecutor(max_workers=3) as pool:
        parts = list(pool.map(fetch_part, enumerate(specs)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=destination.parent, prefix=".features.", suffix=".partial")
    temporary = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as output:
            for part in parts:
                with part.open("rb") as stream:
                    shutil.copyfileobj(stream, output, length=1 << 20)
        verify_file(temporary, entry)
        try:
            os.link(temporary, destination)
        except FileExistsError:
            verify_file(destination, entry)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def restore(cache: Path, *, fetch=False, features=False, anchors=False) -> dict:
    pins = json.loads(PINS.read_text(encoding="utf-8"))
    focus = json.loads(ANCHORS.read_text(encoding="utf-8"))["anchors"]
    cache = Path(cache)
    files = []
    for entry in pins["core"]:
        target = cache / "data" / f"{entry['id']}.tif"
        files.append(restore_file(target, entry, fetch=fetch))
    template = pins["template"]
    for entry in template["files"]:
        spec = {**entry, "repo": template["repo"], "commit": template["commit"]}
        target = cache / "template" / entry["path"]
        files.append(restore_file(target, spec, fetch=fetch))
    if anchors:
        for entry in focus:
            spec = {**entry, "repo": f"buffedlizard55-lab/{entry['site']}"}
            files.append(restore_file(cache / "data/anchors" / f"{entry['site']}.tif", spec, fetch=fetch))
    if features:
        files.append(restore_features(cache, pins["features"], fetch=fetch))
    return {"verified_files": len(files), "feature_stack_verified": bool(features),
            "anchors_verified": bool(anchors), "template_commit": template["commit"],
            "provenance": "SHA-verified public mirrors; not authenticated organizer-origin data"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--fetch", action="store_true", help="Fetch missing, pinned public GitHub files with gh")
    parser.add_argument("--features", action="store_true", help="Also restore the 419 MB, 19-band stack")
    parser.add_argument("--anchors", action="store_true", help="Also restore the nine focus-site reference TIFFs")
    parser.add_argument("--all", action="store_true", help="Include features and the nine anchors")
    args = parser.parse_args()
    try:
        result = restore(args.cache, fetch=args.fetch, features=args.features or args.all, anchors=args.anchors or args.all)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"RESTORE FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
