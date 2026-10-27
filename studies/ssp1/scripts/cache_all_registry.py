#!/usr/bin/env python3
"""Restore the frozen all-listed-sites registry with content-addressed deduplication.

At most five GitHub calls/second; never silently skip a missing or inaccessible raster.
The nine priority trees stay pinned to the same snapshot used in the executive table.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from cache_registry import ROOT, gh_bytes

_lock = threading.Lock()
_last = 0.0


def fetch_one(row):
    global _last
    dest = ROOT / '.cache/blobs' / (row['git_blob_sha']+'.tif')
    try:
        if not dest.exists():
            with _lock:
                delay = max(0, _last+0.2-time.monotonic())
                time.sleep(delay)
                _last = time.monotonic()
            b = gh_bytes(f"repos/buffedlizard55-lab/{row['site']}/contents/{row['path']}?ref={row['commit']}")
            blob = hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
            if blob != row['git_blob_sha']:
                raise ValueError('Git blob mismatch')
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(b)
        b = dest.read_bytes()
        blob = hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
        if blob != row['git_blob_sha']:
            raise ValueError('Cached blob mismatch')
        digest = hashlib.sha256(b).hexdigest()
        if row.get('sha256') and digest != row['sha256']:
            raise ValueError('SHA-256 differs from frozen manifest')
        return row['git_blob_sha'], {'status':'ok','sha256':digest,'local':str(dest.relative_to(ROOT))}
    except Exception as e:
        return row['git_blob_sha'], {'status':'failed','error':str(e)}


def main():
    if (ROOT/'evidence/run_card.json').exists():
        raise SystemExit('Recorded experiment closed: use restore_registry.py; do not rebuild its snapshot.')
    pins = json.loads((ROOT/'registry/all_listed_site_pins.json').read_text())
    rows=[]
    for site,pin in pins.items():
        path=ROOT/'.cache/audit'/f'{site}-tree.json'
        tree=json.loads(path.read_text()) if path.exists() else json.loads(gh_bytes(f"repos/buffedlizard55-lab/{site}/git/trees/{pin['commit']}?recursive=1"))
        if tree.get('truncated') or tree['sha']not in (pin['commit'],pin.get('tree_sha')):
            raise ValueError(f'Tree not complete or changed: {site}')
        for f in tree['tree']:
            if f['type']=='blob' and f['path'].lower().endswith(('.tif','.tiff')) and not f['path'].startswith(('data/','.cache/')):
                rows.append({'site':site,'commit':pin['commit'],'path':f['path'],'bytes':f['size'],'git_blob_sha':f['sha']})
    blob_dir=ROOT/'.cache/blobs';blob_dir.mkdir(parents=True,exist_ok=True)
    focus=json.loads((ROOT/'registry/rasters.json').read_text())
    for r in focus['rasters']:
        src=ROOT/r['local'];dst=blob_dir/(r['git_blob_sha']+'.tif')
        if not dst.exists():
            dst.hardlink_to(src)
    unique={r['git_blob_sha']:r for r in rows}
    fetched={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,(sha,receipt) in enumerate(pool.map(fetch_one,unique.values()),1):
            fetched[sha]=receipt
            if i%50==0 or receipt['status']!='ok':
                print(f'{i}/{len(unique)} unique blobs: latest {receipt["status"]}',flush=True)
    records=[{**r,**fetched[r['git_blob_sha']]}for r in rows]
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'scope':'All non-data GeoTIFFs in all 92 named repositories through GEMSDOE92 at frozen commits; no size cutoff. This includes prediction mirrors and quarantines nonprediction/incompatible grids explicitly. Unpublished files and later parallel changes are outside scope.','n_sites':len(pins),'n_files':len(records),'n_unique_blobs':len(unique),'n_failed':sum(r['status']!='ok'for r in records),'rasters':records}
    (ROOT/'registry/all_rasters.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rasters'},indent=2),flush=True)
    if result['n_failed']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
