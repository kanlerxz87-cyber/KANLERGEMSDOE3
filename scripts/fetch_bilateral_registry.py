#!/usr/bin/env python3
"""Restore a frozen comparison-only registry to .cache. No registry raster enters predictions."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import subprocess
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/registry'
LOCK = ROOT / 'research/registry-lock.json'


def digest(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as fh:
        while b:=fh.read(1024*1024): h.update(b)
    return h.hexdigest()


def fetch(row):
    dest = CACHE / (row['id'] + '.tif')
    if dest.exists() and digest(dest)==row['sha256']:
        return row['id'], 'cached'
    url = f"repos/{row['repo']}/contents/{urllib.parse.quote(row['file'], safe='/')}?ref={row['ref']}"
    part=dest.with_suffix('.partial')
    try:
        with part.open('wb') as out:
            subprocess.run(['gh','api',url,'-H','Accept: application/vnd.github.raw'],stdout=out,stderr=subprocess.PIPE,check=True)
        if digest(part)!=row['sha256']:
            raise ValueError('sha256 mismatch')
        part.replace(dest)
        return row['id'], 'restored'
    finally:
        part.unlink(missing_ok=True)


def main():
    entries=json.loads(LOCK.read_text())['entries']
    CACHE.mkdir(parents=True,exist_ok=True)
    failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures={pool.submit(fetch,r):r for r in entries}
        for f in concurrent.futures.as_completed(futures):
            row=futures[f]
            try:
                _, status=f.result(); print(row['id'], status, flush=True)
            except Exception as exc:
                failures.append({'id':row['id'],'error':str(exc)})
                print('FAILED',row['id'],str(exc),flush=True)
    if failures:
        raise SystemExit(f"Registry incomplete; {len(failures)} missing or mismatched: {failures}")
    print(f"Verified all {len(entries)} files in the frozen snapshot; other registries may exist.")

if __name__ == '__main__': main()
