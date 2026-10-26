#!/usr/bin/env python3
"""Restore pinned PUBLIC owner mirrors for research, never credentials.

Default: pinned shared template, sample grid, catalogue, and saturation witness.
Use --focus for the nine historical comparison files and --features for the
419 MB 19-band feature TIFF. All outputs are in the ignored .cache directory.
SHA-256 verification proves mirror integrity, not DrivenData provenance.
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
CACHE = ROOT / ".cache"
OWNER = "buffedlizard55-lab"
WITNESS = {
    "repo": "17GEMSDOE",
    "ref": "6fc71d19d49dca4960d5434bd81b6dd06fcc030a",
    "path": "docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
    "sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "dest": "registry/witness.tif",
}
LATTICE = {
    "repo": "GEMSDOE24",
    "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
    "path": "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
    "sha256": "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2",
    "dest": "registry/lattice5.tif",
}
PART_SHA = [
    "0a330f8951af6c921029e25c84a579319d2db554d62d30d894d6ddc97f98cff7",
    "3c98037b2c997e3bbfcdfc2d9a982e8b820a77410dd7404b05cdb80594922c50",
    "c375c4dbc40c59bbaece572b5e348700b75935f9a30c879c82b6417e0836f31c",
    "b164159e6d0cb2595bc9f63a948af2646b124114a9c5921880c7516092137320",
    "fa0a6f9c936fac1d6f20ca37f5929b2d60bf7a80f3d477dcab886f941aee2696",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fetch(repo: str, ref: str, source: str, destination: Path, expected: str) -> dict:
    destination = Path(destination)
    if destination.exists() and digest(destination) == expected:
        return {"path": str(destination.relative_to(ROOT)), "sha256": expected, "status": "verified cached"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".restore-", suffix=".partial", dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output:
            subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{source}?ref={ref}",
                 "-H", "Accept: application/vnd.github.raw"],
                stdout=output, stderr=subprocess.PIPE, timeout=240, check=True,
            )
        actual = digest(temporary)
        if actual != expected:
            raise ValueError(f"hash mismatch for {repo}/{source}: {actual} != {expected}")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": str(destination.relative_to(ROOT)), "sha256": expected, "status": "restored"}


def restore_template() -> list[dict]:
    pin = json.loads((ROOT / "registry/template_pins.json").read_text())
    def one(item):
        source, expected = item
        if source.startswith("/") or ".." in Path(source).parts:
            raise ValueError("unsafe path in template manifest")
        return fetch(pin["source_repo"], pin["source_commit"], source,
                     CACHE / "template" / source, expected)
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(one, pin["files"].items()))


def restore_core(features: bool, external: bool = False) -> list[dict]:
    pin = json.loads((ROOT / "registry/data_pins.json").read_text())
    receipts = []
    for e in pin["files"]:
        if e["group"] == "external" and not external:
            continue
        relative = Path(e["dest"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe destination in data manifest")
        if e["id"] == "training_features":
            if not features:
                continue
            if len(e["parts"]) != len(PART_SHA):
                raise ValueError("feature part count differs from pinned part hashes")
            dest = CACHE / "data" / relative
            if dest.exists() and digest(dest) == e["sha256"]:
                receipts.append({"path": str(dest.relative_to(ROOT)), "sha256": e["sha256"], "status": "verified cached"})
                continue
            parts = []
            for i, part in enumerate(e["parts"]):
                part_path = CACHE / "parts" / Path(part).name
                receipts.append(fetch(e["repo"], e["ref"], part, part_path, PART_SHA[i]))
                parts.append(part_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=".features-", suffix=".partial", dir=dest.parent)
            tmp = Path(name)
            try:
                with os.fdopen(fd, "wb") as out:
                    for part in parts:
                        with part.open("rb") as stream:
                            shutil.copyfileobj(stream, out, length=1024 * 1024)
                if digest(tmp) != e["sha256"]:
                    raise ValueError("reassembled feature TIFF SHA-256 does not match the pin")
                os.replace(tmp, dest)
            finally:
                tmp.unlink(missing_ok=True)
            receipts.append({"path": str(dest.relative_to(ROOT)), "sha256": e["sha256"], "status": "assembled"})
        else:
            receipts.append(fetch(e["repo"], e["ref"], e["path"], CACHE / "data" / relative, e["sha256"]))
    return receipts


def restore_focus() -> list[dict]:
    rows = json.loads((ROOT / "registry/focus_historical.json").read_text())["files"]
    def one(r):
        return fetch(f"{OWNER}/{r['site']}", r["ref"], r["path"],
                     CACHE / "registry/focus" / f"{r['site']}.tif", r["sha256"])
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(one, rows))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focus", action="store_true", help="also restore nine historical rasters for learning")
    parser.add_argument("--features", action="store_true", help="also restore the 419 MB feature raster")
    parser.add_argument("--external", action="store_true", help="also restore pinned public derived geological inputs")
    args = parser.parse_args()
    # Never leave an earlier success receipt masquerading as this failed attempt.
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "restore_receipt.json").unlink(missing_ok=True)
    if not shutil.which("gh"):
        parser.error("GitHub CLI (gh) is required; this script never asks for credentials")
    receipts = []
    try:
        receipts.extend(restore_template())
        receipts.extend(restore_core(args.features, args.external))
        for item in (WITNESS, LATTICE):
            receipts.append(fetch(f"{OWNER}/{item['repo']}", item["ref"], item["path"],
                                  CACHE / item["dest"], item["sha256"]))
        if args.focus:
            receipts.extend(restore_focus())
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        print(f"RESTORE FAILED; no audit clearance: {exc}", file=sys.stderr)
        return 1
    report = {"schema": "restore-v1", "integrity_only": True,
              "notice": "Public owner mirrors are not organizer-authenticated. No competition credentials used.",
              "features_requested": args.features, "external_requested": args.external,
              "focus_requested": args.focus, "files": receipts}
    (CACHE / "restore_receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Verified {len(receipts)} pinned files; receipt: .cache/restore_receipt.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
