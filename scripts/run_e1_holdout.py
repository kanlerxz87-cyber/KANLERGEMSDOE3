#!/usr/bin/env python3
"""E1 — ASGT mechanism test on the shared hide-and-recover holdout (vendor/gems57, unchanged).

Arms at a matched budget of 37,654 dots (the champion's count):
  ASGT   antislope-scarp grain traces (K3-H1)
  ABL_A  ablation: P(upface) only (no antislope share / grain / coherence / veto)
  ABL_B  ablation: generic P(step_max) scarp strength
  C1     H19-5 network dotted at 2.8 px with fold-local B2 (champion recipe; LEAK-ADVANTAGED:
         H19-5 was built with the full catalogue)
  C2     champion bytes as published (LEAK-HANDICAPPED: its B2 prune used the full catalogue)
Output: evidence/e1_holdout.json   (all numbers HOLDOUT-DTI with evaluator version + CI)
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import holdout as HO  # noqa: E402
from gems57.grid import load_grid  # noqa: E402
from kgems import asgt as A  # noqa: E402
from kgems import common as C  # noqa: E402

BUDGET = 37_654
SPACING = 2.8


def main() -> int:
    t0 = time.time()
    C.ensure_bridge()
    grid = load_grid()
    folds, quad = HO.buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    visible = folds[0]["visible"]
    hidden = folds[0]["hidden_all"]
    d_vis = ndi.distance_transform_edt(~visible)
    print(f"holdout built: withheld={int(hidden.sum())} visible={int(visible.sum())} ({time.time()-t0:.0f}s)", flush=True)

    comp = A.asgt_components(visible)
    s_full = A.asgt_score(comp)
    arms_scores = {"ASGT": s_full,
                   "ABL_A": np.where(comp["valid"], comp["p_up"], 0).astype(np.float32),
                   "ABL_B": np.where(comp["valid"], comp["p_step"], 0).astype(np.float32)}
    allowed = grid.footprint & ~grid.catalogue & (d_vis > 3.0)
    dots = {}
    for k, s in arms_scores.items():
        dots[k] = A.nms_dots(s, allowed, BUDGET, SPACING)
        print(f"{k}: {int(dots[k].sum())} dots ({time.time()-t0:.0f}s)", flush=True)
    h195 = C.read_support(C.registry_path(C.H19_5_SHA)) & grid.footprint
    rng = np.random.default_rng(20261026)
    prio = rng.random(h195.shape).astype(np.float32) * h195
    dots["C1"] = A.nms_dots(prio, h195 & (d_vis > 2.0) & ~grid.catalogue, BUDGET, SPACING)
    dots["C2"] = C.read_support(C.registry_path(C.CHAMPION_SHA)) & grid.footprint
    print("controls:", {k: int(v.sum()) for k, v in dots.items()}, flush=True)

    terms_by_arm, per_fold = {}, {}
    for arm, d in dots.items():
        pred = d.astype(np.float32)
        tot = None
        per_fold[arm] = []
        for f in folds:
            res, terms = EH.evaluate(pred, f, grid.footprint, block_side=200)
            tot = terms if tot is None else tot + terms
            per_fold[arm].append({"fold": f["name"], "dti": res["dti"], "tp": res["tp"], "fp": res["fp"],
                                  "fn": res["fn"], "n_truth": res["n_truth"], "n_emitted": res["n_emitted"]})
        terms_by_arm[arm] = tot
        print(f"{arm}: per-fold DTI {[round(x['dti'], 4) for x in per_fold[arm]]} ({time.time()-t0:.0f}s)", flush=True)
        gc.collect()
    summary = EH.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate="ASGT")

    # leakage canary: single-feature AUC for withheld positives vs active negatives (fold regions)
    region = np.zeros(grid.shape, bool)
    for f in folds:
        region |= f["region"]
    active = region & grid.footprint & ~folds[0]["masked_known"]
    pos = active & hidden
    neg = active & ~hidden
    rs = np.random.default_rng(7)
    ny, nx = np.nonzero(neg)
    pick = rs.choice(ny.size, size=min(ny.size, 4 * int(pos.sum())), replace=False)
    py, px = np.nonzero(pos)
    yy = np.r_[py, ny[pick]]
    xx = np.r_[px, nx[pick]]
    lab = np.r_[np.ones(py.size), np.zeros(pick.size)]
    feats = {"ASGT": s_full, "p_upface": comp["p_up"], "antislope_share": comp["dom"], "grain_compat_G": comp["G"],
             "grain_confidence_visible": comp["conf_g"], "lineament_coherence": comp["coh_s"],
             "p_step_max": comp["p_step"], "neg_distance_to_visible_catalogue": -d_vis}
    canary = {}
    for k, v in feats.items():
        auc = float(roc_auc_score(lab, v[yy, xx]))
        canary[k] = {"raw_auc": round(auc, 5), "oriented_auc": round(max(auc, 1 - auc), 5)}
    worst = max(canary.items(), key=lambda kv: kv[1]["oriented_auc"])
    out = {
        "schema_version": 1, "experiment": "E1 ASGT mechanism (K3-H1) on shared hide-and-recover holdout",
        "evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION,
        "split": {k: v for k, v in folds[0]["receipt"].items()} | {"folds": [f["receipt"] for f in folds]},
        "withheld_positive_pixels": int(hidden.sum()), "budget_dots": BUDGET, "spacing_px": SPACING,
        "arms": {k: int(v.sum()) for k, v in dots.items()},
        "pooled": summary, "per_fold": per_fold,
        "leakage_canary": {"threshold": 0.90, "n_pos": int(py.size), "n_neg": int(pick.size), "features": canary,
                           "max_feature": worst[0], "max_oriented_auc": worst[1]["oriented_auc"],
                           "passed": worst[1]["oriented_auc"] <= 0.90},
        "seconds": round(time.time() - t0, 1),
    }
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / "e1_holdout.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for k, v in summary["scores"].items():
        print(f"  {k:6s} HOLDOUT-DTI {v['dti']:.4f} CI95 [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]  n_withheld={v['withheld_positive_pixels']}")
    for k, v in summary["paired_differences"].items():
        print(f"  ASGT - {k:6s} delta {v['delta']:+.4f} CI95 [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]")
    print("canary max", worst, "passed", out["leakage_canary"]["passed"])
    print(f"done {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
