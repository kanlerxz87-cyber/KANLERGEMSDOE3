#!/usr/bin/env python3
"""Freeze every non-data GeoTIFF in the nine peer trees, without a size cutoff.

Peer prediction bytes are educational controls only, never model features.
GitHub blob identity is checked as well as SHA-256; failed downloads block promotion.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITES = ('GEMSDOE24','GEMSDOE25','GEMSDOE27','GEMSDOE28','GEMSDOE30','GEMSDOE31','GEMSDOE32','GEMSDOE33','GEMSDOE36')


def gh_bytes(endpoint: str) -> bytes:
    return subprocess.run(['gh','api',endpoint,'-H','Accept: application/vnd.github.raw+json'], check=True, capture_output=True).stdout


def restore(row: dict) -> dict:
    local = ROOT / '.cache' / 'registry' / row['site'] / row['path']
    try:
        if local.exists():
            b = local.read_bytes()
        else:
            b = gh_bytes(f"repos/buffedlizard55-lab/{row['site']}/contents/{row['path']}?ref={row['commit']}")
        blob = hashlib.sha1(f'blob {len(b)}\0'.encode() + b).hexdigest()
        if blob != row['git_blob_sha']:
            raise ValueError(f'Git blob checksum mismatch: {blob}')
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(b)
        return {**row, 'status':'ok','local':str(local.relative_to(ROOT)), 'sha256':hashlib.sha256(b).hexdigest()}
    except Exception as e:
        return {**row, 'status':'failed', 'error':str(e)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Refresh peer tree pins; otherwise use the frozen snapshot')
    args = parser.parse_args()
    pins_path = ROOT / 'registry' / 'site_pins.json'
    pins = json.loads(pins_path.read_text()) if pins_path.exists() and not args.refresh else {}
    rows = []
    for site in SITES:
        ref = pins.get(site,{}).get('commit','main')
        tree = json.loads(gh_bytes(f'repos/buffedlizard55-lab/{site}/git/trees/{ref}?recursive=1'))
        if tree.get('truncated'):
            raise RuntimeError(f'Truncated GitHub tree for {site}')
        pins[site] = {'commit':tree['sha']}
        for f in tree['tree']:
            path = f['path']
            if f['type']=='blob' and path.lower().endswith(('.tif','.tiff')) and not path.startswith('data/'):
                rows.append({'site':site,'commit':tree['sha'],'path':path,'bytes':f['size'],'git_blob_sha':f['sha']})
    pins_path.write_text(json.dumps(pins,indent=2)+'\n')
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, row in enumerate(pool.map(restore,rows),1):
            results.append(row)
            print(f"[{i}/{len(rows)}] {row['status']} {row['site']}/{row['path']}",flush=True)
    failures = [r for r in results if r['status']!='ok']
    out = {'schema_version':1,'generated_utc':datetime.now(timezone.utc).isoformat(),'scope':'Every non-data/**/*.tif or .tiff in the nine pinned full trees; no byte-size cutoff. Format-incompatible rasters remain in the manifest and are quarantined explicitly at comparison time. Not every unseen parallel session.', 'n_files':len(results),'n_failed':len(failures),'rasters':results}
    (ROOT/'registry'/'rasters.json').write_text(json.dumps(out,indent=2)+'\n')
    if failures:
        raise SystemExit(f'{len(failures)} registry downloads failed; promotion blocked')


if __name__=='__main__':
    main()
