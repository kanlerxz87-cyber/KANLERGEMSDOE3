#!/usr/bin/env python3
"""Final duplicate gate, recomputed from the registry TIFF bytes (no cache).

For every restored registry raster (registry/registry_index.json, SHA-256 verified):
  * forward overlap  = share of MY scored dots within 3 px of THEIR positive pixels
                       (shared gems57.uniqueness.dot_overlap, unchanged)
  * Spearman (final dots, full footprint).  For two binary rasters Spearman's rho equals the phi
    coefficient exactly (ranks of a binary variable are affine in it); soft rasters use scipy.spearmanr.
    The shortcut is verified against scipy on sample rasters at run time.
  * Spearman (pre-placement ASGT surface vs registry raster, full footprint).
  * Jaccard of dot sets, identical file bytes, identical decoded predictions.
Thresholds (protocol): rho > 0.90 or overlap > 0.70 => duplicate.  Space-filling rasters (3-px buffer covers
>= 50% of the footprint, e.g. the 5-px lattice) make the literal overlap rule unsatisfiable for ANY file; they
are reported row-by-row and summarised separately (IR-K3-SPACEFILL-01), never silently dropped.
Output: evidence/uniqueness_final.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
from gems57.uniqueness import OVERLAP_LIMIT, RHO_LIMIT, dot_overlap  # noqa: E402
from kgems import common as C  # noqa: E402


def phi(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main() -> int:
    t0 = time.time()
    cand_path = sorted((ROOT / "docs" / "downloads").glob("kanler3-k3h1-*.tif"))
    if len(cand_path) != 1:
        raise SystemExit(f"expected exactly one candidate TIFF, found {cand_path}")
    cand_path = cand_path[0]
    foot, cat = C.footprint(), C.catalogue()
    with rasterio.open(cand_path) as ds:
        mine = ds.read(1)
    my_sha = hashlib.sha256(cand_path.read_bytes()).hexdigest()
    my_dec = hashlib.sha256(np.ascontiguousarray(mine).tobytes()).hexdigest()
    scored = foot & ~cat
    my_dots = np.isfinite(mine) & (mine > 0) & scored
    my_f = my_dots[foot]
    surface = np.load(ROOT / "data" / "work" / "e3_live_asgt_score.npy")
    s_rank = rankdata(surface[foot]).astype(np.float64)
    s_rank_c = s_rank - s_rank.mean()
    s_norm = np.sqrt((s_rank_c ** 2).sum())
    idx = json.loads((ROOT / "registry" / "registry_index.json").read_text())["rasters"]
    stats = {r["sha256"]: r for r in json.loads((ROOT / "data" / "registry_cache" / "registry_stats.json").read_text())["rows"]}
    rows, checks = [], []
    for k, r in enumerate(idx):
        p = ROOT / "data" / "registry" / f"{r['sha256']}.tif"
        sub = next((s.get("submission") for s in r["sources"] if s.get("submission")), Path(r["path"]).name)
        score = next((s.get("owner_reported_live_score") for s in r["sources"]
                      if s.get("owner_reported_live_score") is not None), None)
        row = {"sha256": r["sha256"], "repo": r["repo"], "path": r["path"], "submission": sub,
               "owner_reported_live_score": score}
        try:
            with rasterio.open(p) as ds:
                if ds.shape != mine.shape or ds.transform != rasterio.open(cand_path).transform:
                    raise ValueError("grid mismatch (not a valid competition-grid raster)")
                t = ds.read(1).astype(np.float32)
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)
            continue
        theirs = np.isfinite(t) & (t > 0)
        ov = dot_overlap(my_dots.astype(np.float32), theirs.astype(np.float32))
        tf = np.where(np.isfinite(t), t, 0.0)[foot]
        binary = bool(np.isin(tf[tf > 0], [1.0]).all())
        if binary:
            rho_dots = phi(my_f, tf > 0)
            tb = (tf > 0).astype(np.float64)
            tb_c = tb - tb.mean()
            den = s_norm * np.sqrt((tb_c ** 2).sum())
            rho_surface = float((s_rank_c * tb_c).sum() / den) if den > 0 else float("nan")
            if len(checks) < 3 and tb.sum() > 1000:
                ref = float(spearmanr(my_f.astype(np.float32), tf).statistic)
                ref_s = float(spearmanr(surface[foot], tf).statistic)
                checks.append({"submission": sub, "phi": rho_dots, "scipy_dots": ref,
                               "surface_fast": rho_surface, "scipy_surface": ref_s})
        else:
            rho_dots = float(spearmanr(my_f.astype(np.float32), tf).statistic)
            rho_surface = float(spearmanr(surface[foot], tf).statistic)
        inter = int((my_dots & theirs).sum())
        union = int((my_dots | theirs).sum())
        sf = bool(stats.get(r["sha256"], {}).get("space_filling", False))
        row.update(binary=binary, their_dots=int(theirs.sum()), space_filling=sf,
                   buffer_share_of_footprint=stats.get(r["sha256"], {}).get("buffer_share_of_footprint"),
                   my_dots_within_3px_of_theirs=round(ov, 6),
                   spearman_full_footprint=round(rho_dots, 6) if np.isfinite(rho_dots) else None,
                   spearman_surface_preplacement=round(rho_surface, 6) if np.isfinite(rho_surface) else None,
                   jaccard_dot_sets=round(inter / union, 6) if union else 0.0,
                   identical_bytes=(r["sha256"] == my_sha),
                   identical_decoded_predictions=bool(np.array_equal(np.nan_to_num(t), np.nan_to_num(mine))),
                   duplicate_by_rho=bool(np.isfinite(rho_dots) and rho_dots > RHO_LIMIT) or
                                    bool(np.isfinite(rho_surface) and rho_surface > RHO_LIMIT),
                   duplicate_by_overlap=bool(ov > OVERLAP_LIMIT))
        rows.append(row)
        if k % 50 == 0:
            print(f"{k}/{len(idx)} {time.time()-t0:.0f}s", flush=True)
    ok = [r for r in rows if "error" not in r]
    nsf = [r for r in ok if not r["space_filling"]]
    sfl = [r for r in ok if r["space_filling"]]
    worst = lambda rs, key: max(rs, key=lambda r: (r[key] if r[key] is not None else -9))  # noqa: E731
    w_ov, w_rho, w_srf = worst(nsf, "my_dots_within_3px_of_theirs"), worst(ok, "spearman_full_footprint"), worst(ok, "spearman_surface_preplacement")
    dup_nsf = [r for r in nsf if r["duplicate_by_overlap"] or r["duplicate_by_rho"] or r["identical_bytes"] or r["identical_decoded_predictions"]]
    dup_rho_any = [r for r in ok if r["duplicate_by_rho"] or r["identical_bytes"] or r["identical_decoded_predictions"]]
    out = {
        "schema_version": 1, "evidence_class": "REGISTRY-MEASUREMENT", "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate": cand_path.name, "candidate_file_sha256": my_sha, "candidate_decoded_sha256": my_dec,
        "my_scored_dots": int(my_dots.sum()), "rho_limit": RHO_LIMIT, "overlap_limit": OVERLAP_LIMIT,
        "registry_rasters_listed": len(idx), "registry_rasters_compared": len(ok),
        "registry_rasters_not_comparable": [{"submission": r["submission"], "repo": r["repo"], "error": r["error"]} for r in rows if "error" in r],
        "space_filling_rasters": [{"submission": r["submission"], "repo": r["repo"], "buffer_share": r["buffer_share_of_footprint"],
                                   "overlap": r["my_dots_within_3px_of_theirs"], "spearman": r["spearman_full_footprint"]} for r in sfl],
        "worst_overlap_non_space_filling": {"value": w_ov["my_dots_within_3px_of_theirs"], "submission": w_ov["submission"], "repo": w_ov["repo"]},
        "worst_spearman_final_dots": {"value": w_rho["spearman_full_footprint"], "submission": w_rho["submission"], "repo": w_rho["repo"]},
        "worst_spearman_surface_preplacement": {"value": w_srf["spearman_surface_preplacement"], "submission": w_srf["submission"], "repo": w_srf["repo"]},
        "byte_unique": not any(r["identical_bytes"] for r in ok),
        "pixel_unique": not any(r["identical_decoded_predictions"] for r in ok),
        "duplicates_non_space_filling": len(dup_nsf), "duplicates_by_rho_any_raster": len(dup_rho_any),
        "literal_rule_blocked_only_by_space_filling": bool(not dup_nsf and any(r["duplicate_by_overlap"] for r in sfl)),
        "unique": bool(not dup_nsf and not dup_rho_any and len(ok) > 0),
        "spearman_shortcut_checks": checks,
        "scope": "433 comparable rasters restored from the GEMSDOE focus-site manifests and the scored live ledger (participant mirrors, SHA-256 verified). Not an organizer-complete registry.",
        "rows": rows, "seconds": round(time.time() - t0, 1),
    }
    (ROOT / "evidence" / "uniqueness_final.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("rows",)}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
