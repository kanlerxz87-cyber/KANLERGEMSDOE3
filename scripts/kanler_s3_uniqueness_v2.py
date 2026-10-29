#!/usr/bin/env python3
"""Uniqueness gate v2 for a candidate dot raster vs the GEMSDOE TIFF inventory.

WHY v2: v1 measured only candidate->peer coverage. A dense peer covers every candidate dot
by construction, so 109 inputs (feature rasters, dense 0/1 masks) were flagged at overlap 1.0.
v1 is kept as evidence/kanler-s3-uniqueness-20261029-v1-superseded.json.

v2 rule (applied identically to every peer):
  * binary peer (only 0/1 inside the submission footprint) with 1..200,000 dots  -> its dot set
  * binary peer with > 200,000 dots (dense mask)                                  -> NOT_SUBMISSION_LIKE
  * non-binary peer with all finite values in [0,1] (probability-style submission) -> its top-K
    pixels, K = candidate dot count (37,654)
  * any other non-binary peer (integer IDs, u8 features, values outside [0,1]) -> NOT_SUBMISSION_LIKE;
    the competition format requires values in [0,1], so such rasters are not submissions
  * f_c = share of candidate dots within 3 px of a peer dot; f_p = share of peer dots within 3 px
    of a candidate dot
  * expected random coverage: E = 1-(1-p)^29, p = |peer dots| / footprint px, 29 = integer offsets
    with dx^2+dy^2 <= 9
  * DUPLICATE if (f_c > 0.70 and f_c - E_c > 0.50) or (f_p > 0.70 and f_p - E_p > 0.50)
    (coverage above 70% AND at least 50 points above chance, in EITHER direction; the two-way
    reading is the conservative one, because "overlaps at least 70%" does not say which side)
  * NEAR-THRESHOLD (reported, not a flag): either direction > 0.60 with lift > 0.40
  * rank-correlation stop unchanged: |Spearman or phi| > 0.90 on a fixed 300,000-pixel subsample
Positive control (GEMSDOE30 44,090 dots vs H33 B2, a known subset relation) must flag.
Negative control (random off-catalogue dots, same count) must not flag.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data/sample_submission.tif"
LABELS = ROOT / "data/labels.tif"
PEERS = ROOT / ".cache/peers/all"
INVENTORY = ROOT / "evidence/peer-tif-inventory-20261029.json"
OUT = ROOT / "evidence/kanler-s3-uniqueness-20261029.json"
RADIUS = 3.0
N_OFFSETS = 29
OVERLAP_STOP = 0.70
LIFT_STOP = 0.50
RHO_STOP = 0.90
DENSE_LIMIT = 200_000


def expected_random(n_dots: int, n_foot: int) -> float:
    p = n_dots / n_foot
    return float(1.0 - (1.0 - p) ** N_OFFSETS)


def coverage(a_rc: np.ndarray, b_rc: np.ndarray) -> float:
    if a_rc.shape[0] == 0 or b_rc.shape[0] == 0:
        return 0.0
    d, _ = cKDTree(b_rc.astype(np.float64)).query(a_rc.astype(np.float64), k=1)
    return float((d <= RADIUS).mean())


def score_pair(c_rc, p_rc, n_foot, k_c):
    f_c = coverage(c_rc, p_rc)
    f_p = coverage(p_rc, c_rc)
    e_c = expected_random(p_rc.shape[0], n_foot)
    e_p = expected_random(k_c, n_foot)
    dup = bool((f_c > OVERLAP_STOP and f_c - e_c > LIFT_STOP) or (f_p > OVERLAP_STOP and f_p - e_p > LIFT_STOP))
    return {"f_c": round(f_c, 6), "f_p": round(f_p, 6), "expected_random_c": round(e_c, 6),
            "expected_random_p": round(e_p, 6), "duplicate_flag": dup}


def main(candidate: Path, controls: bool = True) -> dict:
    with rasterio.open(SAMPLE) as ds:
        foot = np.isfinite(ds.read(1))
        ref_shape, ref_tr = ds.shape, tuple(ds.transform)[:6]
    foot_rc = np.argwhere(foot)
    n_foot = int(foot.sum())
    with rasterio.open(candidate) as ds:
        ca = np.nan_to_num(ds.read(1), nan=0.0)
    c_full = ca[foot]
    c_idx = np.flatnonzero(c_full > 0.5)
    c_rc = foot_rc[c_idx]
    k_c = int(c_idx.size)
    rng = np.random.default_rng(20261029)
    sub = rng.choice(n_foot, 300_000, replace=False)
    c_sub = c_full[sub].astype(np.float64)
    c_binary = bool(np.isin(c_full, [0.0, 1.0]).all())

    rows = []
    sources = {}
    for inv in json.loads(INVENTORY.read_text())["repositories"]:
        for t in inv.get("tifs", []):
            if "local" in t:
                sources[ROOT / t["local"]] = (inv["repo"], t["path"], t["sha256"])
    for path in sorted(PEERS.glob("*.tif")):
        repo, rel, sha = sources.get(path, (path.name, path.name, None))
        try:
            with rasterio.open(path) as ds:
                pa = ds.read(1)
                pcrs = str(ds.crs)
                pshape, ptr = ds.shape, tuple(ds.transform)[:6]
        except Exception as exc:  # recorded, never hidden
            rows.append({"file": path.name, "repo": repo, "status": "UNREADABLE", "detail": str(exc)[:120]})
            continue
        if not (pshape == ref_shape and np.allclose(ptr, ref_tr) and "32611" in pcrs):
            rows.append({"file": path.name, "repo": repo, "path": rel, "status": "NOT_COMPARABLE",
                         "shape": list(pshape), "crs": pcrs})
            continue
        pv = np.nan_to_num(pa[foot].astype(np.float32), nan=0.0)
        p_binary = bool(np.isin(pv, [0.0, 1.0]).all())
        p_unit = bool(np.isfinite(pv).all() and pv.min() >= 0.0 and pv.max() <= 1.0)
        if not p_binary and not p_unit:
            rows.append({"file": path.name, "repo": repo, "path": rel, "sha256": sha,
                         "status": "NOT_SUBMISSION_LIKE", "detail": "non-binary and outside [0,1]"})
            continue
        if p_binary:
            p_idx = np.flatnonzero(pv > 0.5)
            mode = "binary dot set"
            if p_idx.size > DENSE_LIMIT:
                rows.append({"file": path.name, "repo": repo, "path": rel, "sha256": sha,
                             "status": "NOT_SUBMISSION_LIKE", "peer_dots": int(p_idx.size),
                             "detail": "dense binary mask (> %d dots)" % DENSE_LIMIT})
                continue
        else:
            k = k_c
            p_idx = np.argpartition(-pv, k - 1)[:k] if pv.size > k else np.arange(pv.size)
            mode = f"top-{k} pixels by value"
        p_rc = foot_rc[p_idx]
        s = score_pair(c_rc, p_rc, n_foot, k_c)
        p_sub = pv[sub].astype(np.float64)
        if p_binary and c_binary:
            rho = float(np.corrcoef(c_sub, p_sub)[0, 1]) if p_sub.std() > 0 and c_sub.std() > 0 else 0.0
            rho_kind = "phi (binary)"
        else:
            rho = float(spearmanr(c_sub, p_sub).statistic)
            rho_kind = "Spearman on 300k-pixel subsample"
        rho = 0.0 if rho != rho else rho  # NaN guard, counted as 0
        near = bool(max(s["f_c"], s["f_p"]) > 0.60 and max(s["f_c"] - s["expected_random_c"],
                                                          s["f_p"] - s["expected_random_p"]) > 0.40)
        rows.append({"file": path.name, "repo": repo, "path": rel, "sha256": sha, "status": "COMPARED",
                     "mode": mode, "peer_dots": int(p_rc.shape[0]), **s,
                     "rho": round(rho, 6), "rho_kind": rho_kind,
                     "rho_flag": bool(abs(rho) > RHO_STOP),
                     "near_threshold": near,
                     "duplicate_flag": bool(s["duplicate_flag"] or abs(rho) > RHO_STOP)})

    compared = [r for r in rows if r.get("status") == "COMPARED"]
    dup_rows = [r for r in compared if r["duplicate_flag"]]
    worst_c = max(compared, key=lambda r: r["f_c"], default=None)
    worst_p = max(compared, key=lambda r: r["f_p"], default=None)
    worst_r = max(compared, key=lambda r: abs(r["rho"]), default=None)

    result = {
        "kind": "UNIQUENESS GATE v2 vs GEMSDOE TIFF inventory (protocol rule 1; not a score)",
        "rule_version": "v2 (lift-corrected; see scripts/kanler_s3_uniqueness_v2.py docstring)",
        "candidate": candidate.name,
        "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "candidate_dots": k_c,
        "candidate_binary": c_binary,
        "footprint_px": n_foot,
        "stops": {"overlap_gt": OVERLAP_STOP, "lift_gt": LIFT_STOP, "rank_corr_gt": RHO_STOP},
        "files_inventoried": len(rows),
        "files_compared": len(compared),
        "files_not_submission_like": sum(1 for r in rows if r.get("status") == "NOT_SUBMISSION_LIKE"),
        "near_threshold_files": [{"file": r["file"], "repo": r["repo"], "f_c": r["f_c"], "f_p": r["f_p"],
                                  "expected_random_c": r["expected_random_c"],
                                  "expected_random_p": r["expected_random_p"]}
                                 for r in compared if r["near_threshold"] and not r["duplicate_flag"]],
        "files_not_comparable": sum(1 for r in rows if r.get("status") == "NOT_COMPARABLE"),
        "files_unreadable": sum(1 for r in rows if r.get("status") == "UNREADABLE"),
        "max_coverage_candidate_dots": worst_c and {"file": worst_c["file"], "repo": worst_c["repo"], "value": worst_c["f_c"],
                                                    "expected_random": worst_c["expected_random_c"]},
        "max_coverage_peer_dots": worst_p and {"file": worst_p["file"], "repo": worst_p["repo"], "value": worst_p["f_p"],
                                               "expected_random": worst_p["expected_random_p"]},
        "max_rank_corr": worst_r and {"file": worst_r["file"], "repo": worst_r["repo"], "value": worst_r["rho"]},
        "duplicate_flags": [{"file": r["file"], "repo": r["repo"], "f_c": r["f_c"], "f_p": r["f_p"],
                             "expected_random_c": r["expected_random_c"], "expected_random_p": r["expected_random_p"],
                             "trigger": ("candidate_side" if (r["f_c"] > OVERLAP_STOP and r["f_c"] - r["expected_random_c"] > LIFT_STOP) else "")
                                        + ("peer_side" if (r["f_p"] > OVERLAP_STOP and r["f_p"] - r["expected_random_p"] > LIFT_STOP) else "")}
                            for r in dup_rows],
        "unique_vs_inventory": not dup_rows,
        "rows": rows,
    }
    if controls:
        result["controls"] = run_controls(foot, foot_rc, n_foot, c_rc, k_c)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def run_controls(foot, foot_rc, n_foot, c_rc, k_c):
    """Known-positive and known-negative checks of the statistic on the same footprint."""
    import glob

    def focus(site):
        hits = glob.glob(str(ROOT / f".cache/peers/focus9/{site}__*.tif"))
        if len(hits) != 1:
            raise SystemExit(f"control file for {site} missing or ambiguous: {hits}")
        with rasterio.open(hits[0]) as ds:
            v = np.nan_to_num(ds.read(1)[foot], nan=0.0)
        return foot_rc[np.flatnonzero(v > 0.5)]

    out = {}
    h33 = focus("GEMSDOE32")
    g30 = focus("GEMSDOE30")
    out["positive_control_H33_B2_vs_GEMSDOE30_known_subset"] = score_pair(h33, g30, n_foot, h33.shape[0])
    # Shift every candidate dot by one pixel: a trivially perturbed copy, which must be flagged.
    shifted = c_rc + np.array([0, 1])
    out["positive_control_candidate_shifted_1px"] = score_pair(c_rc, shifted, n_foot, k_c)
    rng = np.random.default_rng(7)
    rnd = foot_rc[rng.choice(foot_rc.shape[0], k_c, replace=False)]
    out["negative_control_random_dots"] = score_pair(c_rc, rnd, n_foot, k_c)
    return out


if __name__ == "__main__":
    import sys
    res = main(Path(sys.argv[1]))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
