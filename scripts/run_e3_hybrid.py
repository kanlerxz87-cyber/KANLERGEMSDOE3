#!/usr/bin/env python3
"""E3 — the single variant chosen from E2 diagnostics: ASGT-ranked H19-5 core + ASGT novel share.

Why (E2): pure ASGT files sit ~70% off the H19-5 network and project at 0.07-0.12; the live ledger puts most
hidden truth near that network.  So the variant keeps <=69.5% of scored dots on the network (core: H19-5
pixels with catalogue distance > 3 px, priority = ASGT score at/next to the pixel, NMS spacing 2.8 px, our own
placement) and >=30.5% ASGT dots outside every H19-5 3-px buffer pixel (catalogue distance > 5 px).
All per-raster forward overlaps are capped at 0.695 by the constrained greedy allocator.

Two builds of the identical recipe:
  live    : full catalogue visible            -> PROJECTION (shared LLI) + the candidate dots (.npy)
  holdout : visible catalogue of the shared buffered draw (seed 20) -> HOLDOUT-DTI vs controls (paired CI)
Output: evidence/e3_hybrid.json, data/work/e3_live_dots.npy
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import holdout as HO  # noqa: E402
from gems57.grid import load_grid  # noqa: E402
from kgems import allocate as AL  # noqa: E402
from kgems import asgt as A  # noqa: E402
from kgems import common as C  # noqa: E402
from kgems import lli as L  # noqa: E402

N_CORE_TARGET = 37_654          # the champion's dot count: same core density as the incumbent
CORE_SHARE = 0.695
SPACING = 2.8
CORE_EXCL = 3.0
NOVEL_EXCL = 5.0


def build(visible: np.ndarray, reg: C.RegistryOverlap, h195: np.ndarray, foot: np.ndarray):
    d_vis = ndi.distance_transform_edt(~visible)
    comp = A.asgt_components(visible)
    s = A.asgt_score(comp)
    del comp
    gc.collect()
    s_core = ndi.maximum_filter(s, size=3)            # ASGT evidence at or next to the network pixel
    core_allowed = h195 & foot & ~visible & (d_vis > CORE_EXCL)
    tie = (np.random.default_rng(20261026).random(s.shape) * 1e-6).astype(np.float32)
    core = A.nms_dots(np.where(core_allowed, s_core + tie + 1e-3, 0), core_allowed, N_CORE_TARGET, SPACING)
    d_h = ndi.distance_transform_edt(~h195)
    novel_allowed = foot & ~visible & (d_vis > NOVEL_EXCL) & (d_h > 3.0)
    novel_pool = A.nms_dots(s, novel_allowed, 200_000, SPACING, forbid=ndi.binary_dilation(core, iterations=2))
    del d_h, s_core
    n_core = int(core.sum())
    n_total = int(np.ceil(n_core / CORE_SHARE))
    # priority: all core dots first (they carry the projected value), then novel dots by ASGT score
    cf = np.flatnonzero(core.ravel())
    nf = np.flatnonzero(novel_pool.ravel())
    nf = nf[np.argsort(-s.ravel()[nf], kind="stable")]
    flat = np.r_[cf, nf]
    use, M = AL.membership(reg, flat)
    acc, counts, limit = AL.constrained_greedy(np.arange(flat.size), M, n_total, CORE_SHARE)
    pick = flat[acc]
    dots = np.zeros(foot.size, bool)
    dots[pick] = True
    info = {"core_available": n_core, "n_total_target": n_total, "accepted": int(pick.size),
            "accepted_core": int(np.isin(pick, cf).sum()), "accepted_novel": int(np.isin(pick, nf).sum()),
            "overlap_limit_count": limit}
    return dots.reshape(foot.shape), s, info


def main() -> int:
    t0 = time.time()
    foot, cat = C.footprint(), C.catalogue()
    reg = C.RegistryOverlap()
    h195 = C.read_support(C.registry_path(C.H19_5_SHA)) & foot
    # ---------------- live build + projection ----------------
    live, s_live, info_live = build(cat, reg, h195, foot)
    np.save(ROOT / "data" / "work" / "e3_live_dots.npy", np.flatnonzero(live.ravel()).astype(np.int32))
    np.save(ROOT / "data" / "work" / "e3_live_asgt_score.npy", s_live)
    del s_live
    spec = L.build_spec_s3()
    lam = L.archived_lambda(spec)
    pr = L.project(live.astype(np.float32), spec, lam)
    champ = C.read_support(C.registry_path(C.CHAMPION_SHA))
    pr_ch = L.project(champ.astype(np.float32), spec, lam)
    ov = reg.overlaps(np.flatnonzero(live.ravel()))
    nsf = reg.ok & ~reg.space_filling
    worst = int(np.nanargmax(np.where(nsf, ov, -1)))
    h_i = next(i for i, r in enumerate(reg.rows) if r["sha256"].startswith(C.H19_5_SHA))
    c_i = next(i for i, r in enumerate(reg.rows) if r["sha256"].startswith(C.CHAMPION_SHA))
    print(f"live: {info_live} PROJECTION {pr['dti']:.4f} vs champion {pr_ch['dti']:.4f}; overlap H19-5 {ov[h_i]:.3f} "
          f"champion {ov[c_i]:.3f} worst {ov[worst]:.3f} {reg.label(worst)} ({time.time()-t0:.0f}s)", flush=True)
    del spec, lam
    gc.collect()
    # ---------------- holdout build ----------------
    grid = load_grid()
    folds, _ = HO.buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    visible = folds[0]["visible"]
    hold, _, info_hold = build(visible, reg, h195, foot)
    d_vis = ndi.distance_transform_edt(~visible)
    rng = np.random.default_rng(20261026)
    prio = rng.random(h195.shape).astype(np.float32) * h195
    c1 = A.nms_dots(prio, h195 & (d_vis > 2.0) & ~grid.catalogue, 37_654, SPACING)
    e1 = json.loads((ROOT / "evidence" / "e1_holdout.json").read_text())
    arms = {"E3_HYBRID": hold, "C1": c1}
    terms_by_arm, per_fold = {}, {}
    for arm, d in arms.items():
        tot = None
        per_fold[arm] = []
        for f in folds:
            res, terms = EH.evaluate(d.astype(np.float32), f, grid.footprint, block_side=200)
            tot = terms if tot is None else tot + terms
            per_fold[arm].append({"fold": f["name"], "dti": res["dti"], "n_truth": res["n_truth"],
                                  "n_emitted": res["n_emitted"]})
        terms_by_arm[arm] = tot
    summary = EH.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate="E3_HYBRID")
    out = {"schema_version": 1, "experiment": "E3 ASGT-ranked H19-5 core + ASGT novel share (K3-H1 variant)",
           "recipe": {"n_core_target": N_CORE_TARGET, "core_share_cap": CORE_SHARE, "spacing_px": SPACING,
                      "core_catalogue_exclusion_px": CORE_EXCL, "novel_catalogue_exclusion_px": NOVEL_EXCL,
                      "novel_min_distance_to_H19_5_px": 3.0},
           "live": {"info": info_live, "projection": pr, "champion_projection_same_fit": pr_ch,
                    "evidence_class": "PROJECTION (shared LLI S3; LOO MAE 0.0219; q90 0.054)",
                    "overlap_H19_5": float(ov[h_i]), "overlap_champion": float(ov[c_i]),
                    "worst_overlap_non_space_filling": float(ov[worst]), "worst_overlap_raster": reg.label(worst)},
           "holdout": {"evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION, "info": info_hold,
                       "pooled": summary, "per_fold": per_fold,
                       "e1_reference_scores": {k: v["dti"] for k, v in e1["pooled"]["scores"].items()}},
           "seconds": round(time.time() - t0, 1)}
    (ROOT / "evidence" / "e3_hybrid.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for k, v in summary["scores"].items():
        print(f"  {k:10s} HOLDOUT-DTI {v['dti']:.4f} CI95 [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}] n_withheld={v['withheld_positive_pixels']}")
    for k, v in summary["paired_differences"].items():
        print(f"  E3 - {k} delta {v['delta']:+.4f} CI95 [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]")
    print(f"done {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
