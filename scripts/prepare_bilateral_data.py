#!/usr/bin/env python3
"""Verify the restored owner's inputs; write metadata only, never treat sample values as labels."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from restore_bilateral_data import sha256

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/input-manifest.json'
EXPECTED = (3730, 3292)
TRANSFORM = (100., 0., 243350., 0., -100., 4508550.)
BANDS = ['mag_anom','rtp','tmi_hg','geod_2ndinv','iso_grav_anom_slope','tc','geod_shearrate','geod_dilaterate','tmi_vg','deq_n100a15','iso_grav_anom_vg','det_elev','iso_grav_anom','tmi','depth_to_base_surf','ieq_n100a15','cond_surf','iso_grav_anom_hg','det_elev_slope']


def validate(data=ROOT/'data'):
    manifest = json.loads(MANIFEST.read_text())
    by_id = {x['id']:x for x in manifest['inputs']}
    paths = {}
    for id in ['training_features','labels','sample_submission','lidar_cached','geodawn_radiometric_cached','calibration_lattice']:
        row = by_id[id]; p = data / row['dest']
        if not p.is_file(): raise FileNotFoundError(f'Missing {p}; run bash scripts/download_bilateral_data.sh')
        if p.stat().st_size != row['bytes'] or sha256(p)!=row['sha256']:
            raise ValueError(f'Input hash/size mismatch: {p}')
        paths[id] = p
    with rasterio.open(paths['sample_submission']) as t:
        grid=(t.shape,t.crs,t.transform)
        if t.count != 1 or t.shape!=EXPECTED or t.crs.to_epsg()!=32611 or tuple(t.transform)[:6]!=TRANSFORM:
            raise ValueError('Unexpected grid or template band count')
        sample=t.read(1); footprint=np.isfinite(sample)
        if not footprint.any(): raise ValueError('No finite template footprint')
        sample_ones=footprint & (sample>0)
    if footprint.sum()!=5167373:
        raise ValueError('Mirrored template footprint changed')
    infos={}
    for id,p in paths.items():
        with rasterio.open(p) as ds:
            if (ds.shape,ds.crs,ds.transform)!=grid:
                raise ValueError(f'Grid mismatch: {id}')
            infos[id]={'bytes':p.stat().st_size,'sha256':by_id[id]['sha256'],'bands':ds.count,'dtype':list(ds.dtypes)}
            if id=='training_features':
                names=[ds.tags(i).get('band_name') for i in range(1,ds.count+1)]
                if ds.count!=19 or names!=BANDS:
                    raise ValueError(f'Unexpected training feature band metadata: {names}')
                infos[id]['band_names']=names
            elif id=='labels':
                v=ds.read(1); labels=footprint & (v==1)
                if np.any(~np.isin(v[footprint], [0,1])): raise ValueError('Labels inside footprint must be binary')
            elif id=='lidar_cached':
                if ds.count!=12 or list(ds.descriptions)!=['ex_max','ex_mean','step_max','lapneg_max','lappos_max','downface_max','upface_max','cross_max','relief','coh100','strike','valid']:
                    raise ValueError('Unexpected LiDAR cached channels')
            elif id=='geodawn_radiometric_cached':
                if ds.count!=4 or list(ds.descriptions)!=['K','Th','U','TC']: raise ValueError('Unexpected radiometric cached channels')
    return {'generated_utc':datetime.now(timezone.utc).isoformat(), 'grid':{'shape':list(EXPECTED),'epsg':32611,'transform':list(TRANSFORM),'footprint_pixels':int(footprint.sum())},'files':infos,'positive_catalogue_pixels':int(labels.sum()),'sample_positive_pixels':int(sample_ones.sum()),'sample_positives_equal_labels':bool(np.array_equal(sample_ones, labels)), 'warning':'Owner-mirror hashes are not independently organizer-authenticated; sample is footprint metadata only.'}


def main():
    receipt=validate(); dest=ROOT/'evidence/data_preparation.json'; dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
