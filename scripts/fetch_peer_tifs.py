#!/usr/bin/env python3
"""Inventory every GeoTIFF in the GEMSDOE repositories listed in the request.

Source: the public codeload tarball of each repository's default branch
(https://codeload.github.com/<owner>/<repo>/tar.gz/HEAD). The tarball is streamed and only
*.tif/*.tiff members are kept, so no GitHub REST quota is used (the REST API rate limit blocked
an earlier attempt). Each TIFF is stored under a PATH-DERIVED name in the git-ignored
.cache/peers/all/, so same-named files in different folders cannot overwrite each other.

Writes a small tracked inventory (repo, commit, path, bytes, SHA-256, local file) to
evidence/peer-tif-inventory-20261029.json. Nothing is scored here. A 404 is recorded as
UNAVAILABLE with its HTTP status; no other failure is hidden.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOS = ROOT / "registry/peer_repos_20261029.json"
OUT_DIR = ROOT / ".cache/peers/all"
INVENTORY = ROOT / "evidence/peer-tif-inventory-20261029.json"
UA = "KANLERGEMSDOE3-uniqueness-inventory/2026-10-29"


def safe_name(owner: str, repo: str, path: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", path.replace("/", "__"))
    return f"{owner}__{repo}__{stem}"


def fetch_repo(repo: str) -> dict:
    owner, name = repo.split("/", 1)
    url = f"https://codeload.github.com/{owner}/{name}/tar.gz/HEAD"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    entry = {"repo": repo, "status": "OK", "source": "codeload tar.gz HEAD", "tifs": []}
    try:
        resp = urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as exc:
        entry.update(status="UNAVAILABLE", detail=f"HTTP {exc.code}")
        return entry
    except urllib.error.URLError as exc:
        entry.update(status="UNAVAILABLE", detail=f"network: {exc.reason}")
        return entry
    commit = None
    with resp, tarfile.open(fileobj=resp, mode="r|gz") as tf:
        for member in tf:
            if commit is None:
                head = member.name.split("/", 1)[0]
                m = re.search(r"-([0-9a-f]{40})$", head)
                commit = m.group(1) if m else head
            if not member.isfile():
                continue
            lower = member.name.lower()
            if not lower.endswith((".tif", ".tiff")):
                continue
            rel = member.name.split("/", 1)[1] if "/" in member.name else member.name
            data = tf.extractfile(member).read()
            digest = hashlib.sha256(data).hexdigest()
            local = OUT_DIR / safe_name(owner, name, rel)
            local.write_bytes(data)
            entry["tifs"].append({"path": rel, "bytes": len(data), "sha256": digest,
                                  "local": str(local.relative_to(ROOT))})
    entry["commit"] = commit
    return entry


def main() -> None:
    repos = json.loads(REPOS.read_text())["repos"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.tif"):  # rebuild from scratch so no stale collided files survive
        old.unlink()
    inventory = []
    for repo in repos:
        entry = fetch_repo(repo)
        inventory.append(entry)
        print(f"{repo}: {entry['status']} {len(entry['tifs'])} tif {entry.get('detail', '')}", flush=True)
    available = sum(1 for e in inventory if e["status"] == "OK")
    summary = {
        "kind": "PEER TIF INVENTORY (GEMSDOE repos listed in the request); not scored",
        "date_utc": "2026-10-29",
        "method": "streamed codeload tarball of each default branch; *.tif/*.tiff only; path-derived local names",
        "repos_listed": len(repos),
        "repos_available": available,
        "repos_not_complete": len(repos) - available,
        "tif_files": sum(len(e["tifs"]) for e in inventory),
        "repositories": inventory,
    }
    INVENTORY.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "repositories"}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
