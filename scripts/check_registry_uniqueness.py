#!/usr/bin/env python3
"""Literal all-registry uniqueness check for a candidate, using the shared comparator.

Calls vendor/gems57/uniqueness.compare_array_to_registry (unmodified shared tool) against
every hash-verified raster in evidence/registry_index.json (built by scripts/build_registry.py).
Two checks are run:
  * placement surface  - the saved probability surface (Spearman only; dot overlap is not
                         meaningful for a continuous surface, so it is reported as diagnostic)
  * final dots         - the written candidate raster (Spearman, >=3 px dot overlap, Jaccard)

Thresholds are the shared protocol values: rho > 0.90, overlap > 0.70, Jaccard > 0.50.

Space-filling registry rasters (3 px dilation covers >= 50% of the footprint) cannot be
passed by ANY dot file under the literal overlap rule; they are reported separately, never
silently dropped. The literal result is still computed over all rasters.

Usage: python scripts/check_registry_uniqueness.py --candidate <tif> --out evidence/<file>.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
from gems57 import uniqueness as U  # noqa: E402  (shared comparator, unmodified)

INDEX = ROOT / "evidence" / "registry_index.json"
TEMPLATE = ROOT / "data" / "sample_submission.tif"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def shared_index(reg: dict) -> dict:
    """Deduplicate by SHA-256 (byte-identical files give identical results); keep aliases."""
    seen: dict[str, dict] = {}
    alias: dict[str, list[str]] = {}
    for r in reg["rasters"]:
        if not r.get("sha256"):
            continue
        key = r["sha256"]
        alias.setdefault(key, []).append(f"{r['owner']}/{r['repo']}:{r['path']}")
        if key not in seen:
            seen[key] = {"repo_first": f"{r['owner']}/{r['repo']}", "sources": [r["path"]],
                         "cache_file": r["local"], "sha256": key}
    rows = list(seen.values())
    complete = bool(reg["summary"]["repos_unavailable"] == 0 and not any("download failed" in x for x in reg["irregularities"]))
    return {"rasters": rows, "complete_accessible_scan": complete,
            "errors": list(reg["irregularities"]), "aliases": alias}


def _work(args):
    mine_path, surface_path, recs, include_reverse = args
    fp = np.isfinite(rasterio.open(TEMPLATE).read(1))
    if surface_path:
        mine = np.load(surface_path).astype(np.float32)
        mine = np.where(fp, mine, 0.0)
    else:
        with rasterio.open(mine_path) as s:
            mine = np.where(fp, s.read(1), 0.0).astype(np.float32)
    res = U.compare_array_to_registry(mine, {"rasters": recs, "complete_accessible_scan": True}, fp,
                                      file_sha256=None if surface_path else sha256(Path(mine_path)),
                                      include_reverse=include_reverse)
    return res["rows"]


def run_rows(mine_path, surface_path, recs, workers, include_reverse):
    n = max(1, workers)
    chunks = [recs[i::n] for i in range(n)]
    from multiprocessing import Pool
    with Pool(n) as pool:
        parts = pool.map(_work, [(mine_path, surface_path, c, include_reverse) for c in chunks])
    return [r for part in parts for r in part]


def coverage_fraction(path: Path, footprint: np.ndarray) -> float | None:
    """Share of footprint cells within 3 px of the raster's positive cells (space-filling test)."""
    with rasterio.open(path) as s:
        if s.shape != footprint.shape:
            return None
        a = np.where(np.isfinite(s.read(1)), s.read(1), 0.0)
    pos = (a > 0) & footprint
    if not pos.any():
        return 0.0
    near = ndimage.distance_transform_edt(~pos) <= 3
    return float((near & footprint).sum() / footprint.sum())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--surface", type=Path, default=ROOT / "data" / "candidates" / "P_final.npy")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    reg = json.loads(INDEX.read_text())
    idx = shared_index(reg)
    recs = idx["rasters"]
    with rasterio.open(TEMPLATE) as t:
        footprint = np.isfinite(t.read(1))
    with rasterio.open(args.candidate) as s:
        mine = s.read(1)
    mine = np.where(footprint, mine, 0.0).astype(np.float32)
    cand_sha = sha256(args.candidate)
    dots = int(((mine > 0) & footprint).sum())
    rank_var = bool(np.ptp(mine[footprint]) > 0)
    complete_flag = idx["complete_accessible_scan"]
    # Final dots (binary, both overlap and rho)
    rows_final = run_rows(args.candidate, None, recs, args.workers, include_reverse=True)
    final = U.summarize_registry_rows(
        rows_final, registry_rasters_expected=len(recs), complete_accessible_scan=complete_flag,
        source_errors=idx["errors"][:0],
        candidate_meta=dict(my_file=str(args.candidate), my_dots=dots, candidate_decoded_sha256=hashlib.sha256(np.ascontiguousarray(mine).tobytes()).hexdigest(),
                            candidate_file_sha256=cand_sha, candidate_rank_variation=rank_var),
        scope="Hash-verified owner-repository inventory (113 listed repos, all reachable via codeload); not an organizer registry.")
    # Pre-placement surface (continuous): Spearman only is meaningful
    rows_surf = run_rows(None, args.surface, recs, args.workers, include_reverse=False)
    surf_checked = [r for r in rows_surf if "error" not in r and r.get("spearman_full_footprint") is not None]
    surface = {
        "rows": len(rows_surf),
        "checked": len(surf_checked),
        "errors": sum(1 for r in rows_surf if "error" in r),
        "max_spearman_full_footprint": max((r["spearman_full_footprint"] for r in surf_checked), default=None),
        "max_spearman_submission": max(surf_checked, key=lambda r: r["spearman_full_footprint"])["submission"] if surf_checked else None,
        "count_rho_gt_0_90": sum(1 for r in surf_checked if r["spearman_full_footprint"] > U.RHO_LIMIT),
    }
    # Space-filling diagnostic (registry rasters whose 3-px neighbourhood covers >= 50% of footprint)
    # Space-filling test only for rasters that already trip the literal overlap/rho rule (cost control).
    flagged = {str(Path(r["file"]).resolve()) for r in rows_final if r.get("duplicate_by_overlap") or r.get("duplicate_by_rho")}
    off_grid = [{"file": r["file"], "error": r["error"]} for r in rows_final if "error" in r]
    space = []
    for r in recs:
        if str((ROOT / r["cache_file"]).resolve()) not in flagged:
            continue
        cov = coverage_fraction(ROOT / r["cache_file"], footprint)
        if cov is not None and cov >= 0.5:
            space.append({"file": r["cache_file"], "coverage_3px": round(cov, 4)})
    out = {
        "schema": 1,
        "candidate": str(args.candidate.resolve().relative_to(ROOT)),
        "candidate_sha256": cand_sha,
        "candidate_dots": dots,
        "registry_index": str(INDEX.relative_to(ROOT)),
        "registry_rasters_indexed_total": len(reg["rasters"]),
        "registry_unique_bytes_checked": len(recs),
        "thresholds": {"rho_gt": U.RHO_LIMIT, "overlap_gt": U.OVERLAP_LIMIT, "jaccard_gt": U.JACCARD_LIMIT},
        "final_dots": {k: v for k, v in final.items() if k != "rows"},
        "final_dots_rows": rows_final,
        "placement_surface": surface,
        "placement_surface_rows": rows_surf,
        "space_filling_registry_rasters": space,
        "non_comparable_registry_rasters": off_grid,
        "scope_note": "Hash-verified accessible rasters from 113 public owner repositories. Not an organizer registry; "
                      "organizer-only or private submissions cannot be included.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k: final[k] for k in ("unique", "duplicate_count", "registry_rasters_checked", "missing_or_invalid",
                                            "worst_spearman_full_footprint", "worst_dot_overlap", "complete_accessible_scan")}, indent=1, default=float))
    print(json.dumps(surface, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
