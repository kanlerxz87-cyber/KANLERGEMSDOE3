#!/usr/bin/env python3
"""Uniqueness gate for a candidate GeoTIFF against every GEMSDOE TIFF in the inventory.

Two literal stops from the parallel-run protocol (rule 1), checked on the saved candidate bytes:
  * overlap3: fraction of candidate dots (value > 0.5 inside the footprint) that have a peer dot
    within 3 px. Duplicate if > 0.70.
  * rho: rank correlation (Spearman) of the footprint values. For binary rasters the Spearman
    rank correlation equals the phi coefficient exactly (ranks of a binary variable are an affine
    function of it), so the computed value is exact for binary peers; soft peers use a 300k-pixel
    random subsample of Spearman. Duplicate if > 0.90.
Peers on a different grid are recorded as NOT COMPARABLE, never as unique.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
PEERS = ROOT / ".cache/peers/all"
SAMPLE = ROOT / "data/sample_submission.tif"
INVENTORY = ROOT / "evidence/peer-tif-inventory-20261029.json"
OUT = ROOT / "evidence/kanler-s3-uniqueness-20261029.json"
OVERLAP_STOP = 0.70
RHO_STOP = 0.90
RADIUS = 3.0


def load(path: Path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float64)
        crs, shape, tr = str(ds.crs), ds.shape, tuple(ds.transform)[:6]
    return a, crs, shape, tr


def main(candidate: Path) -> dict:
    with rasterio.open(SAMPLE) as ds:
        foot = np.isfinite(ds.read(1))
        ref_shape, ref_tr = ds.shape, tuple(ds.transform)[:6]
    ca, ccrs, cshape, ctr = load(candidate)
    cfield = np.where(foot, np.nan_to_num(ca, nan=0.0), np.nan)
    cdots = np.argwhere(foot & (np.nan_to_num(ca, nan=0.0) > 0.5))
    rng = np.random.default_rng(20261029)
    sub = rng.choice(np.flatnonzero(foot.ravel()), 300_000, replace=False)
    c_sub = cfield.ravel()[sub]

    rows = []
    sources = {}
    for inv in json.loads(INVENTORY.read_text())["repositories"]:
        for t in inv.get("tifs", []):
            if "local" in t:
                sources[ROOT / t["local"]] = (inv["repo"], t["path"], t["sha256"])
    for path in sorted(PEERS.glob("*.tif")):
        repo, rel, sha = sources.get(path, (path.name, path.name, None))
        try:
            pa, pcrs, pshape, ptr = load(path)
        except Exception as exc:  # unreadable TIFF is recorded, not hidden
            rows.append({"file": path.name, "repo": repo, "status": "UNREADABLE", "detail": str(exc)[:120]})
            continue
        comparable = pshape == ref_shape and np.allclose(ptr, ref_tr) and ("32611" in pcrs)
        if not comparable:
            rows.append({"file": path.name, "repo": repo, "path": rel, "status": "NOT_COMPARABLE",
                         "shape": list(pshape), "crs": pcrs})
            continue
        pdots = np.argwhere(foot & (np.nan_to_num(pa, nan=0.0) > 0.5))
        if pdots.size == 0:
            overlap = 0.0
        else:
            tree_p = cKDTree(pdots.astype(np.float64))
            d_c, _ = tree_p.query(cdots.astype(np.float64), k=1)
            overlap = float((d_c <= RADIUS).mean())
        p_field = np.where(foot, np.nan_to_num(pa, nan=0.0), np.nan)
        p_sub = p_field.ravel()[sub]
        binary = bool(np.isin(np.unique(p_sub), [0.0, 1.0]).all())
        if binary and np.isin(np.unique(c_sub), [0.0, 1.0]).all():
            rho = float(np.corrcoef(c_sub, p_sub)[0, 1]) if p_sub.std() > 0 and c_sub.std() > 0 else 0.0
            rho_kind = "exact (binary; equals phi)"
        else:
            rho = float(spearmanr(c_sub, p_sub).statistic)
            rho_kind = "Spearman on 300k-pixel subsample"
        rows.append({"file": path.name, "repo": repo, "path": rel, "sha256": sha,
                     "status": "COMPARED", "peer_dots": int(pdots.shape[0]),
                     "overlap_within_3px": round(overlap, 6), "rho": round(rho, 6), "rho_kind": rho_kind,
                     "duplicate_flag": bool(overlap > OVERLAP_STOP or rho > RHO_STOP)})

    compared = [r for r in rows if r.get("status") == "COMPARED"]
    worst_o = max(compared, key=lambda r: r["overlap_within_3px"]) if compared else None
    worst_r = max(compared, key=lambda r: r["rho"]) if compared else None
    result = {
        "kind": "UNIQUENESS GATE vs GEMSDOE TIFF inventory (protocol rule 1; not a score)",
        "candidate": candidate.name,
        "candidate_sha256": __import__("hashlib").sha256(candidate.read_bytes()).hexdigest(),
        "candidate_dots": int(cdots.shape[0]),
        "stops": {"overlap_within_3px_gt": OVERLAP_STOP, "rank_corr_gt": RHO_STOP},
        "files_inventoried": len(rows),
        "files_compared": len(compared),
        "files_not_comparable": sum(1 for r in rows if r.get("status") == "NOT_COMPARABLE"),
        "files_unreadable": sum(1 for r in rows if r.get("status") == "UNREADABLE"),
        "max_overlap_within_3px": worst_o and {"file": worst_o["file"], "repo": worst_o["repo"], "value": worst_o["overlap_within_3px"]},
        "max_rank_corr": worst_r and {"file": worst_r["file"], "repo": worst_r["repo"], "value": worst_r["rho"]},
        "duplicate_flags": [r["file"] for r in compared if r["duplicate_flag"]],
        "unique_vs_inventory": not any(r["duplicate_flag"] for r in compared),
        "rows": rows,
    }
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


if __name__ == "__main__":
    res = main(Path(sys.argv[1]))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
