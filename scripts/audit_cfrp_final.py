#!/usr/bin/env python3
"""Archived CFRP audit (CLI disabled); use audit_cfrp_archive.py instead.

Original scope: uniqueness vs focus-9 + lattice, catalogue-DTI calibration.

Comparison-only registry rasters. Spearman uses gems.novelty.rank_correlation
(binary-reference affine-rank shortcut, exact over all footprint pixels);
dot overlap uses gems.novelty.dot_overlap (exact, all dots, 3 px).
Catalogue-DTI here is a *calibration diagnostic* (DTI of a raster against the
full mirrored catalogue as truth, no catalogue mask) — NOT a leaderboard score.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.metric import dti_score_fast
from gems.novelty import dot_overlap, rank_correlation, classify_space_filling_control

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()

def main():
    with rasterio.open(ROOT/"data/core/sample_submission.tif") as s: foot=np.isfinite(s.read(1))
    with rasterio.open(ROOT/"data/core/labels.tif") as s: labels=(s.read(1)==1)&foot
    surf=np.load(ROOT/".cache/cfrp/final_surface.npy")
    dots=np.load(ROOT/".cache/cfrp/final_dots.npy").astype(bool)
    ranks=rankdata(surf[foot].astype(np.float64))
    reg=json.loads((ROOT/"registry/focus9_champions.json").read_text())["entries"]
    rows=[]
    cache=ROOT/".cache/registry"
    files={p.name.split("__")[0]:p for p in cache.glob("*.tif")}
    for e in reg:
        p=files[e["site"]]
        with rasterio.open(p) as ds: a=ds.read(1)
        ref=foot & np.isfinite(a) & (a>0)
        rho=rank_correlation(ranks, a[foot].astype(np.float64))
        ov=dot_overlap(dots, ref, 3.0)
        cat=dti_score_fast(ref, labels, valid_mask=foot, catalogue_mask=None)
        rows.append({"site":e["site"],"submission":e["name"],"owner_reported_score":e["score_owner_reported"],
                     "file_sha256":sha(p),"surface_spearman_vs_candidate":rho,
                     "candidate_dots_within_3px":ov["candidate_within_3px_of_reference"],
                     "reference_dots_within_3px_of_candidate":ov["reference_within_3px_of_candidate"],
                     "reference_dots":ov["reference_dots"],
                     "catalogue_dti_diagnostic":cat["dti"],
                     "leaderboard_over_catalogue_dti": e["score_owner_reported"]/cat["dti"] if cat["dti"]>0 else None,
                     "duplicate_by_protocol": bool((rho is not None and abs(rho)>0.90) or (ov["candidate_within_3px_of_reference"] or 0)>0.70)})
        print(rows[-1], flush=True)
    # lattice calibration control
    lp=cache/"LATTICE__13gems_lattice_s5.tif"
    with rasterio.open(lp) as ds: a=ds.read(1)
    lref=foot & np.isfinite(a) & (a>0)
    lrho=rank_correlation(ranks, a[foot].astype(np.float64))
    lov=dot_overlap(dots, lref, 3.0)
    ctrl=classify_space_filling_control(foot, lref, radius_px=3.0, coverage_threshold=0.70, candidate_dot_count=int(dots.sum()))
    cand_cat=dti_score_fast(dots, labels, valid_mask=foot, catalogue_mask=None)
    ratios=[r["leaderboard_over_catalogue_dti"] for r in rows if r["leaderboard_over_catalogue_dti"]]
    out={"generated_utc":datetime.now(timezone.utc).isoformat(),
         "candidate_dots":int(dots.sum()),
         "candidate_catalogue_dti_diagnostic":cand_cat,
         "projection_method":"PROJECTION (not a score): candidate catalogue-DTI x median(owner-reported leaderboard / catalogue-DTI across focus-9 champions); interval = ratio IQR applied likewise. Assumes family-stable calibration; in-sample bias affects candidate and champions in the same direction.",
         "calibration_ratios":ratios,
         "ratio_median":float(np.median(ratios)),"ratio_q1":float(np.percentile(ratios,25)),"ratio_q3":float(np.percentile(ratios,75)),
         "focus9_rows":rows,
         "focus9_max_abs_spearman":max(abs(r["surface_spearman_vs_candidate"]) for r in rows),
         "focus9_max_dot_overlap":max(r["candidate_dots_within_3px"] for r in rows),
         "focus9_unique":not any(r["duplicate_by_protocol"] for r in rows),
         "lattice":{"file":lp.name,"surface_spearman":lrho,"candidate_dots_within_3px":lov["candidate_within_3px_of_reference"],
                    "reference_dots":lov["reference_dots"], **ctrl,
                    "classification":"space-filling calibration control: rank gate applies; 3px-overlap gate is non-discriminating by pigeonhole (see gems.novelty)"}}
    out["projection_point"]=cand_cat["dti"]*out["ratio_median"]
    out["projection_iqr"]=[cand_cat["dti"]*out["ratio_q1"], cand_cat["dti"]*out["ratio_q3"]]
    (ROOT/"evidence/cfrp_uniqueness_calibration_20261028.json").write_text(json.dumps(out,indent=1,default=float)+"\n")
    print(json.dumps({k:out[k] for k in ("candidate_dots","focus9_max_abs_spearman","focus9_max_dot_overlap","focus9_unique","projection_point","projection_iqr")},indent=1))
    print("lattice", out["lattice"])
    return 0

if __name__=="__main__":
    from archive_guard import stop_archived_cli
    stop_archived_cli()
    raise SystemExit(main())
