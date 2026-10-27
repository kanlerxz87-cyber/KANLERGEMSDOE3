#!/usr/bin/env python3
"""Restore every registry raster (live-scored ledger + nine focus sites) by plain `git`.

Why plain git: the GitHub REST API is rate-limited for this account during parallel
sessions, while blobless git fetches from github.com are not.  Every file is verified
against the SHA-256 pinned in the source manifest; a mismatch is a hard failure and the
file is not kept.  Nothing here is organizer-authenticated: these are participant
mirrors used ONLY for (a) duplicate/uniqueness gates and (b) live-ledger projections.

Inputs (copied verbatim from buffedlizard55-lab/GEMSDOE32 @ registry/SOURCE_COMMIT_GEMSDOE32.txt):
  registry/live_ledger_rasters.json      118 scored rasters (OWNER-REPORT live scores)
  registry/focus_registry_manifest.json  362 rasters published by the nine focus sites
Output: data/registry/<sha256>.tif (git-ignored) and registry/registry_index.json
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "buffedlizard55-lab"
OUT = ROOT / "data" / "registry"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args, cwd, check=True, capture=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check,
                          capture_output=capture, timeout=900)


def fetch_pair(repo: str, ref: str, items: list[dict]) -> list[dict]:
    """Blobless shallow fetch of one commit, then read only the requested blobs."""
    results = []
    todo = [it for it in items if not (OUT / f"{it['sha256']}.tif").exists()]
    for it in items:
        if it not in todo:
            results.append({**it, "status": "ok-cached"})
    if not todo:
        return results
    with tempfile.TemporaryDirectory(prefix="reg-") as tmp:
        git("init", "-q", cwd=tmp)
        git("remote", "add", "origin", f"https://github.com/{OWNER}/{repo}.git", cwd=tmp)
        r = git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", ref, cwd=tmp, check=False)
        if r.returncode != 0:
            return results + [{**it, "status": "fetch-failed",
                               "error": r.stderr.decode(errors="replace")[-300:]} for it in todo]
        for it in todo:
            r = git("cat-file", "-p", f"FETCH_HEAD:{it['path']}", cwd=tmp, check=False)
            if r.returncode != 0:
                results.append({**it, "status": "missing-at-ref"})
                continue
            got = sha256_bytes(r.stdout)
            if got != it["sha256"]:
                results.append({**it, "status": "sha256-mismatch", "got": got})
                continue
            (OUT / f"{it['sha256']}.tif").write_bytes(r.stdout)
            results.append({**it, "status": "ok"})
    return results


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    led = json.loads((ROOT / "registry" / "live_ledger_rasters.json").read_text())["rows"]
    foc = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())["rasters"]
    wanted: dict[str, dict] = {}
    for r in led:
        if r.get("status") != "ok":
            continue
        e = wanted.setdefault(r["sha256"], {"sha256": r["sha256"], "repo": r["repo"], "ref": r["ref"],
                                            "path": r["path"], "sources": []})
        e["sources"].append({"kind": "live_ledger", "site": r["site"], "submission": r["submission"],
                             "owner_reported_live_score": r["score"]})
    for r in foc:
        e = wanted.setdefault(r["sha256"], {"sha256": r["sha256"], "repo": r["repo"], "ref": r["ref"],
                                            "path": r["path"], "sources": []})
        e["sources"].append({"kind": "focus_site", "repo": r["repo"], "path": r["path"]})
    groups: dict[tuple, list] = {}
    for e in wanted.values():
        groups.setdefault((e["repo"], e["ref"]), []).append(e)
    print(f"{len(wanted)} unique rasters in {len(groups)} repo/ref pairs", flush=True)
    results = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch_pair, k[0], k[1], v): k for k, v in groups.items()}
        for i, f in enumerate(cf.as_completed(futs), 1):
            res = f.result()
            results.extend(res)
            bad = [x for x in res if not x["status"].startswith("ok")]
            print(f"[{i}/{len(groups)}] {futs[f][0]}: {len(res) - len(bad)} ok, {len(bad)} failed", flush=True)
    results.sort(key=lambda x: (x["repo"], x["path"]))
    summary = {
        "schema_version": 1,
        "source_manifests_commit": (ROOT / "registry" / "SOURCE_COMMIT_GEMSDOE32.txt").read_text().strip(),
        "evidence_class": "participant mirrors; SHA-256 verified against pinned manifests; NOT organizer-authenticated",
        "n_unique": len(results),
        "n_ok": sum(x["status"].startswith("ok") for x in results),
        "n_failed": sum(not x["status"].startswith("ok") for x in results),
        "rasters": [{k: v for k, v in x.items() if k != "error"} | ({"error": x["error"]} if "error" in x else {})
                    for x in results],
    }
    (ROOT / "registry" / "registry_index.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("n_unique", "n_ok", "n_failed")}))
    return 0 if summary["n_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
