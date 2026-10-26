"""Exact, footprint-wide lane checks. No sampling-based uniqueness claims."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.spatial import cKDTree
from scipy.stats import rankdata


def sha256(path: Path) -> str:
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def mask_sha(mask: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(np.asarray(mask,bool)).tobytes()).hexdigest()


def normalized_ranks(values: np.ndarray) -> np.ndarray | None:
    r=rankdata(values,method='average').astype(np.float64)
    r-=r.mean()
    n=np.linalg.norm(r)
    return r/n if n else None


def rank_correlation(centered_unit_ranks: np.ndarray | None, ref_values: np.ndarray) -> float | None:
    if centered_unit_ranks is None:
        return None
    v=np.asarray(ref_values)
    lo,hi=float(v.min()),float(v.max())
    if lo==hi:
        return None
    # Exact two-level Spearman shortcut, including all zero/one dot rasters.
    if np.all((v==lo)|(v==hi)):
        upper=v==hi;n1=int(upper.sum());n0=v.size-n1
        return float(centered_unit_ranks[upper].sum()/np.sqrt(n1*n0/v.size))
    rr=normalized_ranks(v)
    return float(centered_unit_ranks@rr) if rr is not None else None


def within3(query_mask: np.ndarray, reference_mask: np.ndarray) -> float | None:
    q=np.column_stack(np.nonzero(query_mask))
    r=np.column_stack(np.nonzero(reference_mask))
    if not len(q):
        return None
    if not len(r):
        return 0.0
    d,_=cKDTree(r).query(q,k=1,distance_upper_bound=3.00000001,workers=2)
    return float(np.mean(d<=3.0))


def read_comparable(path: Path, template: Path, footprint: np.ndarray) -> tuple[np.ndarray,dict]:
    with rasterio.open(template) as tpl,rasterio.open(path) as ds:
        geometry_ok=(ds.shape==tpl.shape and ds.crs==tpl.crs and ds.transform==tpl.transform and ds.count==1)
        if not geometry_ok:
            raise ValueError(f'Noncompetition grid or bands: {ds.shape}, {ds.crs}, {ds.count}')
        a=ds.read(1)
        meta={'shape':list(ds.shape),'crs':str(ds.crs),'transform':list(ds.transform)[:6],'bands':ds.count,'dtype':ds.dtypes[0]}
    v=a[footprint]
    meta.update({'nonfinite_inside':int((~np.isfinite(v)).sum()),'range_0_1_inside':bool(np.isfinite(v).all() and np.all((v>=0)&(v<=1)))})
    # NaN conventions differ across historical rasters. Record them, but do not
    # silently remove those rasters from comparisons: normalize missing to zero.
    clean=np.where(np.isfinite(a),a,0).astype(np.float32)
    return clean,meta


def surface_guard(surface: np.ndarray, footprint: np.ndarray, template: Path, manifest: dict, root: Path, output: Path) -> dict:
    vals=np.asarray(surface,dtype=np.float32)[footprint]
    if not np.isfinite(vals).all():
        raise ValueError('Nonfinite candidate surface')
    ranks=normalized_ranks(vals)
    rows=[];seen={};bad=[];violations=[]
    for i,row in enumerate(manifest['rasters'],1):
        if row.get('status')!='ok' or not row.get('local'):
            bad.append({**row,'comparison_status':'missing'});continue
        key=row['git_blob_sha']
        if key not in seen:
            p=root/row['local']
            if not p.exists() or sha256(p)!=row['sha256']:
                raise ValueError(f'Registry missing or corrupt: {p}')
            try:
                a,meta=read_comparable(p,template,footprint)
                ref=a[footprint]
                rho=rank_correlation(ranks,ref)
                mask=(a>0)&footprint
                rec={**meta,'comparison_status':'compared','surface_spearman':rho,'dot_pixels':int(mask.sum()),'mask_sha256':mask_sha(mask),'canonical_pixel_sha256':hashlib.sha256(ref.astype('<f4').tobytes()).hexdigest()}
                del a,ref,mask
            except (ValueError,rasterio.errors.RasterioError) as e:
                rec={'comparison_status':'quarantined_incompatible','reason':str(e)}
            seen[key]=rec
        rec={**row,**seen[key]}
        rows.append(rec)
        rho=rec.get('surface_spearman')
        if rho is not None and abs(rho)>0.90:
            violations.append({'site':row['site'],'path':row['path'],'rho':rho})
            # Stop candidate development at the first lane duplicate. There is no
            # reweighting, jitter, or exemption to make a failing surface pass.
            break
        if i%100==0:
            print(f'Surface guard: {i}/{len(manifest["rasters"])} files, {len(seen)} blobs',flush=True)
    compared=[r for r in rows if r['comparison_status']=='compared']
    quarantine=[r for r in rows if r['comparison_status']!='compared']
    max_row=max((r for r in compared if r['surface_spearman'] is not None),key=lambda r:abs(r['surface_spearman']),default=None)
    result={'stage':'surface_before_placement','correlation':'Exact full-footprint Spearman, average ties, absolute threshold 0.90; no positive continuous pixel is treated as a placed dot. Final dot proximity is a separate gate.','n_manifest_files':len(manifest['rasters']),'n_checked_files':len(rows),'n_compared_files':len(compared),'n_unique_blobs_read':len(seen),'n_missing':len(bad),'n_quarantined':len(quarantine),'quarantines':quarantine,'max_abs_spearman':abs(max_row['surface_spearman']) if max_row else None,'nearest_raster':{'site':max_row['site'],'path':max_row['path']}if max_row else None,'violations':violations,'complete':len(rows)==len(manifest['rasters']) and not bad,'passed':not violations and not bad and len(rows)==len(manifest['rasters']) and ranks is not None,'rows':rows}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    return result


def final_guard(mask: np.ndarray, footprint: np.ndarray, template: Path, manifest: dict, surface_result: dict, root: Path, first_path_contains: str='r13-lattice-s5') -> dict:
    """Stop at first final-dot duplicate as required; report tested scope honestly.

    Pixel uniqueness can still be checked against the complete surface-stage
    canonical mask index without continuing to optimize or relocate a single dot.
    """
    own_hash=mask_sha(mask)
    exact=[{'site':r['site'],'path':r['path']}for r in surface_result['rows']if r.get('mask_sha256')==own_hash]
    rows=manifest['rasters']
    rows=sorted(rows,key=lambda r:(first_path_contains not in r['path'],r['site'],r['path']))
    ranks=normalized_ranks(np.asarray(mask,dtype=np.float32)[footprint])
    checks=[];seen=set()
    for row in rows:
        if row.get('status')!='ok' or row['git_blob_sha']in seen:
            continue
        seen.add(row['git_blob_sha'])
        try:
            a,_=read_comparable(root/row['local'],template,footprint)
        except (ValueError,rasterio.errors.RasterioError):
            continue
        rho=rank_correlation(ranks,a[footprint])
        overlap=within3(mask,(a>0)&footprint)
        rec={'site':row['site'],'path':row['path'],'spearman':rho,'fraction_candidate_dots_within_3px':overlap}
        checks.append(rec)
        if (rho is not None and abs(rho)>0.90)or(overlap is not None and overlap>0.70):
            return {'stage':'final_dots','passed':False,'duplicate':True,'stopped_at_first_duplicate':True,'n_unique_rasters_checked':len(checks),'checks':checks,'exact_dot_mask_matches':exact,'exact_dot_mask_unique_within_comparable_snapshot':not exact and surface_result['complete'],'file_sha_uniqueness_is_not_lane_uniqueness':True}
    return {'stage':'final_dots','passed':bool(mask.any()and surface_result['complete']),'duplicate':False,'stopped_at_first_duplicate':False,'n_unique_rasters_checked':len(checks),'checks':checks,'exact_dot_mask_matches':exact,'exact_dot_mask_unique_within_comparable_snapshot':not exact and surface_result['complete']}
