#!/usr/bin/env python3
"""Build the all-listed-site submission registry from public GitHub repositories.

Why: the uniqueness rule compares a candidate against EVERY registry raster. The
user-listed Pages sites are backed by public GitHub repositories with the same
names (github.com/<owner>/<repo>). This script reads each repository's git tree
through the GitHub API, finds small single-band GeoTIFF submissions, and downloads them
into the git-ignored ``data/registry/`` directory. The default transport is one
``codeload.github.com`` HEAD tarball per repository, because the anonymous+authenticated
REST quota (5,000/h) was exhausted mid-crawl on the first attempt (recorded as
irregularity). Tarballs are streamed in memory and only candidate TIFFs are written. Only a small, tracked index (names, sizes,
SHA-256, git blob SHA, source repo/path/commit) is written to evidence/.

Nothing here is an organizer receipt. Repositories are identified by name only;
the owner's Pages site text is not parsed. Missing or private repositories are
recorded as irregularities, not silently dropped.

Usage: python scripts/build_registry.py [--max-bytes 5000000] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG_DIR = ROOT / "data" / "registry"
INDEX = ROOT / "evidence" / "registry_index.json"
SITES = ROOT / "docs" / "data" / "sites.json"

# Owner/repo pairs taken from the user's listed Pages URLs. Each entry is
# (owner, repo). Pages-to-repo mapping is by name; see irregularities in the index.
LISTED = [
    ("buffedlizard55-lab", r) for r in [
        "GEMSDOE", "6GEMSDOE", "GEMSDOE3", "GEMSDOE2", "GEMSDOE4", "5GEMSDOE", "7GEMSDOE",
        "8GEMSDOE", "GEMSDOE9", "11GEMSDOE", "12GEMSDOE", "15GEMSDOE", "14GEMSDOE", "17GEMSDOE",
        "18GEMSDOE", "19GEMSDOE", "GEMSDOE10", "13GEMSDOE", "16GEMSDOE", "GEMSDOE21", "20GEMSDOE",
        "GEMSDOE22", "GEMSDOE23", "GEMSDOE24", "GEMSDOE25", "GEMSDOE26", "GEMSDOE27", "GEMSDOE28",
        "GEMSDOE29", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE34", "GEMSDOE35",
        "GEMSDOE36", "GEMSDOE37", "GEMSDOE38", "GEMSDOE42", "GEMSDOE43", "GEMSDOE45", "GEMSDOE49",
        "GEMSDOE46", "GEMSDOE39", "GEMSDOE40", "GEMSDOE41", "GEMSDOE44", "GEMSDOE47", "GEMSDOE48",
        "GEMSDOE50", "GEMSDOE51", "GEMSDOE52", "GEMSDOE53", "GEMSDOE54", "55GEMSDOE", "56GEMSDOE",
        "57GEMSDOE", "58GEMSDOE", "59GEMSDOE", "60GEMSDOE", "61GEMSDOE", "62GEMSDOE", "GEMSDOE63",
        "GEMSDOE64", "GEMSDOE65", "GEMSDOE66", "GEMSDOE67", "GEMSDOE68", "GEMSDOE69", "GEMSDOE70",
        "GEMSDOE71", "GEMSDOE72", "GEMSDOE73", "GEMSDOE74", "GEMSDOE75", "GEMSDOE76", "GEMSDOE77",
        "GEMSDOE78", "GEMSDOE79", "GEMSDOE80", "GEMSDOE81", "GEMSDOE82", "GEMSDOE83", "GEMSDOE84",
        "GEMSDOE85", "GEMSDOE86", "GEMSDOE87", "GEMSDOE88", "GEMSDOE89", "GEMSDOE90", "GEMSDOE91",
        "GEMSDOE92",
    ]
] + [
    ("kanlerxz87-cyber", r) for r in ["KANLERGEMSDOE1", "KANLERGEMSDOE2", "KANLERGEMSDOE3"]
] + [
    ("eugboogieman123-ops", r) for r in ["EUGGEMSDOE1", "EUGGEMSDOE2", "EUGGEMSDOE3"]
] + [
    ("wingbangboozle1-lang", r) for r in ["WBGGEMSDOE1", "WBGGEMSDOE2", "WBGGEMSDOE3"]
] + [
    ("ginnymcfiner23-ux", r) for r in ["GINNYGEMSDOE1", "GINNYGEMSDOE2", "GINNYGEMSDOE3"]
] + [
    ("karagemop466-tech", r) for r in ["GEMSDOEkarage1", "GEMSDOEkarage2", "GEMSDOEkarage3"]
] + [
    ("apartanish22-droid", r) for r in ["ApartGEMSDOE1", "ApartGEMSDOE2", "ApartGEMSDOE3"]
] + [
    ("sassnarep3-star", r) for r in ["GEMSDOESASS1", "GEMSDOESASS2", "GEMSDOESASS3"]
]


def gh_json(endpoint: str):
    proc = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["error"]
    return json.loads(proc.stdout), None


def gh_raw(endpoint: str, out: Path) -> None:
    with out.open("wb") as f:
        proc = subprocess.run(
            ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"],
            stdout=f, stderr=subprocess.PIPE, timeout=300,
        )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode(errors="replace")[-300:])


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def is_submission_candidate(path: str, size: int, max_bytes: int) -> bool:
    low = path.lower()
    if not low.endswith((".tif", ".tiff")):
        return False
    if size > max_bytes or size <= 0:
        return False
    # Ignore raw inputs / mirrored training data; submissions live in download folders
    # or the repository root in these projects. Keep it broad: any small TIFF.
    if low.startswith(("data/bridge/", "data/external/", "inputs/", "reference/")):
        return False
    return True


def tarball_rasters(owner: str, repo: str, max_bytes: int):
    """Yield (path, size, git_blob_sha1, bytes) for candidate TIFFs in the HEAD tarball."""
    import io
    import tarfile
    import urllib.request

    url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/HEAD"
    req = urllib.request.Request(url, headers={"User-Agent": "KANLERGEMSDOE3-registry"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            rel = m.name.split("/", 1)[1] if "/" in m.name else m.name
            if not is_submission_candidate(rel, m.size, max_bytes):
                continue
            data = tf.extractfile(m).read()
            blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
            yield rel, len(data), blob, data


def main_codeload(args) -> int:
    REG_DIR.mkdir(parents=True, exist_ok=True)
    index = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "codeload.github.com HEAD tarball per repository; candidate .tif members (<= max-bytes, outside data/bridge, data/external, inputs, reference) written to data/registry (git-ignored); sha256 and git blob sha1 recorded.",
        "authentication_note": "Public repositories; no organizer receipt. Repository names are not scores.",
        "repos": [], "rasters": [], "irregularities": [],
    }
    repos = LISTED[: args.limit_repos] if args.limit_repos else LISTED
    for owner, repo in repos:
        rec = {"owner": owner, "repo": repo, "status": None, "tif_count": 0}
        try:
            members = list(tarball_rasters(owner, repo, args.max_bytes))
        except Exception as exc:  # 404 / network: record, continue
            rec["status"] = "unavailable"
            rec["error"] = str(exc)[:200]
            index["repos"].append(rec)
            index["irregularities"].append(f"{owner}/{repo}: archive unavailable ({str(exc)[:120]})")
            print(f"{owner}/{repo}: UNAVAILABLE", flush=True)
            continue
        rec["status"] = "ok"
        rec["tif_count"] = len(members)
        index["repos"].append(rec)
        for rel, size, blob, data in members:
            dest = REG_DIR / owner / repo / rel  # keep repo-relative path: basenames collide
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not args.dry_run:
                dest.write_bytes(data)
                if hashlib.sha256(dest.read_bytes()).hexdigest() != hashlib.sha256(data).hexdigest():
                    raise RuntimeError(f"write verification failed: {dest}")
            index["rasters"].append({
                "owner": owner, "repo": repo, "path": rel, "blob_sha": blob, "bytes": size,
                "local": str(dest.relative_to(ROOT)),
                **({"sha256": hashlib.sha256(data).hexdigest(), "bytes_on_disk": size} if not args.dry_run else {}),
            })
        print(f"{owner}/{repo}: {len(members)} candidate tif(s)", flush=True)
    index["summary"] = {
        "repos_listed": len(LISTED),
        "repos_ok": sum(1 for r in index["repos"] if r["status"] == "ok"),
        "repos_unavailable": sum(1 for r in index["repos"] if r["status"] != "ok"),
        "rasters": len(index["rasters"]),
        "unique_sha256": len({r.get("sha256") for r in index["rasters"] if r.get("sha256")}),
    }
    if not args.dry_run:
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        INDEX.write_text(json.dumps(index, indent=1, sort_keys=True) + "\n")
    print(json.dumps(index["summary"], indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-bytes", type=int, default=5_000_000)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit-repos", type=int, default=0)
    ap.add_argument("--transport", choices=("codeload", "api"), default="codeload")
    args = ap.parse_args()
    if args.transport == "codeload":
        return main_codeload(args)

    REG_DIR.mkdir(parents=True, exist_ok=True)
    index = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "GitHub git-tree listing via gh api; small .tif blobs downloaded to data/registry (git-ignored).",
        "authentication_note": "Public repositories; no organizer receipt. Names are not scores.",
        "repos": [],
        "rasters": [],
        "irregularities": [],
    }
    repos = LISTED[: args.limit_repos] if args.limit_repos else LISTED
    for owner, repo in repos:
        rec = {"owner": owner, "repo": repo, "status": None, "commit": None, "tif_count": 0}
        tree, err = gh_json(f"repos/{owner}/{repo}/git/trees/HEAD?recursive=1")
        if tree is None:
            rec["status"] = "unavailable"
            rec["error"] = err
            index["repos"].append(rec)
            index["irregularities"].append(f"{owner}/{repo}: tree unavailable ({err})")
            continue
        rec["status"] = "ok"
        rec["truncated"] = bool(tree.get("truncated"))
        if rec["truncated"]:
            index["irregularities"].append(f"{owner}/{repo}: git tree truncated by API; list incomplete")
        cands = [t for t in tree.get("tree", []) if t.get("type") == "blob" and is_submission_candidate(t["path"], t.get("size", 0), args.max_bytes)]
        rec["tif_count"] = len(cands)
        index["repos"].append(rec)
        for t in cands:
            dest_dir = REG_DIR / owner / repo
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / Path(t["path"]).name
            entry = {
                "owner": owner,
                "repo": repo,
                "path": t["path"],
                "blob_sha": t["sha"],
                "bytes": t.get("size"),
                "local": str(dest.relative_to(ROOT)),
            }
            if not args.dry_run:
                if not (dest.exists() and dest.stat().st_size == t["size"]):
                    try:
                        gh_raw(f"repos/{owner}/{repo}/git/blobs/{t['sha']}", dest)
                    except Exception as exc:  # record, continue
                        index["irregularities"].append(f"{owner}/{repo}:{t['path']} download failed: {exc}")
                        continue
                entry["sha256"] = sha256(dest)
                entry["bytes_on_disk"] = dest.stat().st_size
            index["rasters"].append(entry)
        print(f"{owner}/{repo}: {len(cands)} candidate tif(s)", flush=True)
        time.sleep(0.05)

    index["summary"] = {
        "repos_listed": len(LISTED),
        "repos_ok": sum(1 for r in index["repos"] if r["status"] == "ok"),
        "repos_unavailable": sum(1 for r in index["repos"] if r["status"] != "ok"),
        "rasters": len(index["rasters"]),
        "unique_sha256": len({r.get("sha256") for r in index["rasters"] if r.get("sha256")}),
    }
    if not args.dry_run:
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        INDEX.write_text(json.dumps(index, indent=1, sort_keys=True) + "\n")
    print(json.dumps(index["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
