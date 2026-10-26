#!/usr/bin/env python3
"""Reopen the exact nine owner files, compare supports, and verify the H33 subset claim.

These files are learning/comparison inputs only and are never candidate inputs.
Reports owner claims, not organizer-confirmed submission scores.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/historical'


def run():
    records=json.loads((ROOT/'research/historical-sites.json').read_text())['sites']
    CACHE.mkdir(parents=True,exist_ok=True)
    with rasterio.open(ROOT/'data/sample_submission.tif') as t:
        fp=np.isfinite(t.read(1));grid=(t.shape,t.crs,t.transform)
    masks={}; results=[]
    for row in records:
        path=CACHE/f"{row['site']}.tif"
        if not path.exists():
            endpoint=f"repos/{row['repo']}/contents/{row['file']}?ref={row['ref']}"
            tmp=path.with_suffix('.partial')
            try:
                with tmp.open('wb') as out: subprocess.run(['gh','api',endpoint,'-H','Accept: application/vnd.github.raw'],stdout=out,check=True)
                tmp.replace(path)
            finally: tmp.unlink(missing_ok=True)
        content=path.read_bytes()
        if hashlib.sha256(content).hexdigest()!=row['sha256']:
            raise ValueError(f"{row['site']}: pinned SHA-256 mismatch")
        blob=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
        if blob != row['git_blob_sha']:
            raise ValueError(f"{row['site']}: pinned Git blob mismatch")
        with rasterio.open(path) as ds:
            if (ds.shape,ds.crs,ds.transform)!=grid or ds.count!=1: raise ValueError(f"{row['site']}: grid mismatch")
            a=ds.read(1)
        if not np.isfinite(a[fp]).all(): raise ValueError(f"{row['site']}: nonfinite inside footprint")
        mask=fp & (a>0)
        masks[row['site']]=mask
        results.append({**row,'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'positive_footprint_pixels':int(mask.sum()),'owner_score_is_organizer_confirmed':False})
    for row in results:
        m=masks[row['site']];points=np.argwhere(m)
        peers=[]
        for other,other_mask in masks.items():
            if other==row['site']: continue
            other_points=np.argwhere(other_mask)
            overlap=float(np.mean(cKDTree(other_points).query(points)[0]<=3)) if len(points) and len(other_points) else 0.
            peers.append({'site':other,'candidate_within_3px':overlap,'exact_mask':bool(np.array_equal(m,other_mask))})
        row['max_3px_peer']=max(peers,key=lambda r:r['candidate_within_3px'])
        row['exact_peers']=[p['site'] for p in peers if p['exact_mask']]
        row['passes_nine_site_final_dot_limit']=bool(row['max_3px_peer']['candidate_within_3px']<=0.70)
    with rasterio.open(ROOT/'data/labels.tif') as ds: cat=fp & (ds.read(1)==1)
    d28=masks['GEMSDOE25'];h33=masks['GEMSDOE32']
    dist=distance_transform_edt(~cat)
    expected=d28 & (dist>2)
    r={'generated_utc':datetime.now(timezone.utc).isoformat(),'score_evidence':'OWNER-REPORTED, UNVERIFIED; no submission receipt tied to SHA',
       'files':results,'h33_anatomy':{'d28_dots':int(d28.sum()),'h33_dots':int(h33.sum()),
       'd28_dots_at_or_within_two_pixels_of_catalogue':int((d28 & (dist<=2)).sum()),
       'symmetric_difference_h33_vs_d28_excluding_two_pixel_collar':int(np.count_nonzero(expected ^ h33)),
       'interpretation':'Geometry verified against owner mirrors; the reason for the reported hidden-test score cannot be established from these files.'}}
    out=ROOT/'evidence/portfolio-audit.json';out.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps(r,indent=2))

if __name__=='__main__':run()
