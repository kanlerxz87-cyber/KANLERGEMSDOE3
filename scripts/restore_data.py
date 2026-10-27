#!/usr/bin/env python3
"""Restore SHA-256-pinned competition/external files from GitHub mirrors in registry/data_manifest.json.

Provenance: owner-supplied mirrors of DrivenData files (login-walled); integrity-pinned,
NOT organizer-authenticated. See registry/data_manifest.json per-file provenance.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch(repo: str, ref: str, path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        if shutil.which("gh"):
            with tmp.open("wb") as out:
                subprocess.run(["gh","api",f"repos/{repo}/contents/{path}?ref={ref}","-H","Accept: application/vnd.github.raw"], stdout=out, check=True)
        else:
            import urllib.request
            url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
            req = urllib.request.Request(url, headers={"User-Agent":"KANLERGEMSDOE3-DataFetcher/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as out:
                shutil.copyfileobj(r, out)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)

def restore_entry(entry: dict, root: Path) -> dict:
    dest = root / entry["dest"]
    if dest.exists() and sha256_file(dest) == entry["sha256"]:
        return {"id":entry["id"],"dest":entry["dest"],"group":entry["group"],"status":"present","bytes":dest.stat().st_size,"sha256":entry["sha256"]}
    if "parts" in entry:
        tmp = dest.with_suffix(".assembling"); tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("wb") as out:
            for part in entry["parts"]:
                p = root / "raw_parts" / Path(part).name
                print(f"  fetching part {Path(part).name}...", flush=True)
                fetch(entry["repo"], entry["ref"], part, p)
                with p.open("rb") as src: shutil.copyfileobj(src, out, 1 << 20)
                p.unlink(missing_ok=True)
        got = sha256_file(tmp)
        if got != entry["sha256"]:
            tmp.unlink(missing_ok=True); raise SystemExit(f"HASH MISMATCH {entry['id']}: {got} != {entry['sha256']}")
        tmp.replace(dest)
    else:
        print(f"  fetching {entry['id']} -> {dest}...", flush=True)
        fetch(entry["repo"], entry["ref"], entry["path"], dest)
        got = sha256_file(dest)
        if got != entry["sha256"]:
            dest.unlink(missing_ok=True); raise SystemExit(f"HASH MISMATCH {entry['id']}: {got} != {entry['sha256']}")
    return {"id":entry["id"],"dest":entry["dest"],"group":entry["group"],"status":"restored","bytes":dest.stat().st_size,"sha256":entry["sha256"]}

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--group", default="core", choices=["core","external","scored","all"])
    ap.add_argument("--manifest", default=str(ROOT/"registry"/"data_manifest.json"))
    ap.add_argument("--target-dir", default=None)
    args = ap.parse_args()
    man = json.loads(Path(args.manifest).read_text())
    root = Path(args.target_dir) if args.target_dir else (ROOT/"data"/"raw")
    root.mkdir(parents=True, exist_ok=True)
    results=[]
    for e in man["files"]:
        if args.group in ("all", e["group"]):
            r=restore_entry(e, root); results.append(r); print(f"{r['status']:>8}  {e['dest']:60s} sha256={r['sha256'][:16]}...", flush=True)
    receipt={"schema_version":1,"requested_group":args.group,"verified_files":results}
    (ROOT/"data").mkdir(exist_ok=True)
    (ROOT/"data"/"restore_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(f"Verified {len(results)} files; receipt data/restore_receipt.json")
if __name__=="__main__": main()
