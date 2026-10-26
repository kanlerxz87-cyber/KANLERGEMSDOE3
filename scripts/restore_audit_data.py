#!/usr/bin/env python3
"""Restore pinned competition and focus-site rasters via zero-quota codeload tarballs.

Replaces ``gh api`` blob fetches (which exhaust GitHub REST API rate limits)
with streaming ``https://codeload.github.com/<owner>/<repo>/tar.gz/<commit>``
extractions verified byte-for-byte against pinned SHA-256 digests.

Defaults to ``.cache/gems_data`` so large rasters stay out of Git and Arena
turn-end snapshots; pass ``--dest data`` if needed locally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_from_codeload(repo: str, commit: str, targets: list[tuple[str, Path, str]]) -> None:
    """Stream one codeload tarball and extract all matching repo-relative paths."""
    pending = {rel_path: (dest, expected_sha) for rel_path, dest, expected_sha in targets}
    to_fetch: dict[str, tuple[Path, str]] = {}
    for rel_path, (dest, expected_sha) in pending.items():
        if dest.is_file() and sha256_file(dest) == expected_sha:
            continue
        to_fetch[rel_path] = (dest, expected_sha)
    if not to_fetch:
        return

    url = f"https://codeload.github.com/{repo}/tar.gz/{commit}"
    req = urllib.request.Request(url, headers={"User-Agent": "KANLERGEMSDOE3-repro/1.0"})
    found: set[str] = set()
    with urllib.request.urlopen(req, timeout=180) as resp:
        with tarfile.open(fileobj=resp, mode="r|gz") as tf:
            for member in tf:
                if not member.isfile():
                    continue
                parts = member.name.split("/", 1)
                if len(parts) != 2:
                    continue
                rel = parts[1]
                if rel not in to_fetch:
                    continue
                dest, expected_sha = to_fetch[rel]
                dest.parent.mkdir(parents=True, exist_ok=True)
                extracted = tf.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"Unable to extract {rel} from {url}")
                tmp = dest.with_suffix(dest.suffix + ".part")
                h = hashlib.sha256()
                with tmp.open("wb") as out:
                    while True:
                        chunk = extracted.read(1 << 20)
                        if not chunk:
                            break
                        h.update(chunk)
                        out.write(chunk)
                actual = h.hexdigest()
                if actual != expected_sha:
                    tmp.unlink(missing_ok=True)
                    raise ValueError(
                        f"SHA-256 mismatch for {repo}@{commit}:{rel}: got {actual}, expected {expected_sha}"
                    )
                tmp.replace(dest)
                found.add(rel)
                if len(found) == len(to_fetch):
                    break

    missing = set(to_fetch) - found
    if missing:
        raise FileNotFoundError(f"Missing paths {sorted(missing)} in {repo}@{commit}")


def restore_audit_rasters(dest_dir: Path) -> list[dict]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    extract_from_codeload(
        "buffedlizard55-lab/GEMSDOE",
        "c0c06ac88116bbda91ff6e6bb9f209aa7d89d9b2",
        [
            (
                "data/sample_submission.tif",
                dest_dir / "sample_submission.tif",
                "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
            )
        ],
    )
    archived = json.loads(
        (ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text()
    )
    by_source: dict[tuple[str, str], list[tuple[str, Path, str]]] = {}
    receipts: list[dict] = []
    for row in archived["historical_winners"]:
        repo = f"buffedlizard55-lab/{row['repo']}"
        commit = row["head"]
        out_path = dest_dir / f"{row['repo']}.tif"
        by_source.setdefault((repo, commit), []).append((row["file"], out_path, row["sha256"]))
        receipts.append({"repo": row["repo"], "path": str(out_path), "sha256": row["sha256"]})
    for (repo, commit), targets in by_source.items():
        extract_from_codeload(repo, commit, targets)
    return receipts


def main() -> int:
    default_dest = Path(os.environ.get("GEMS_DATA_DIR", ROOT / ".cache/gems_data"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=default_dest)
    args = parser.parse_args()
    receipts = restore_audit_rasters(args.dest)
    print(json.dumps({"ok": True, "dest": str(args.dest), "restored_count": len(receipts)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
