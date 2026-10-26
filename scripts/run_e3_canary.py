#!/usr/bin/env python3
"""Leakage canary for the features E3 adds on top of E1 (same split, same sampling as E1's canary).

E3's core is the H19-5 ridge network, which GEMSDOE19 built with the FULL catalogue (power-law tip/relay
stress needs fault tips).  Any single feature whose AUC for withheld catalogue pixels exceeds 0.90 trips the
canary.  Output: evidence/e3_canary.json (does not modify the E3 result).
"""
from __future__ import annotations

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
sys.path.insert(0, str(ROOT / "scripts"))
from gems57 import holdout as HO  # noqa: E402
from gems57.grid import load_grid  # noqa: E402
from kgems import common as C  # noqa: E402
from run_e3_hybrid import build  # noqa: E402


def main() -> int:
    t0 = time.time()
    C.ensure_bridge()
    grid = load_grid()
    folds, _ = HO.buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    hidden, visible = folds[0]["hidden_all"], folds[0]["visible"]
    foot = C.footprint()
    reg = C.RegistryOverlap()
    h195 = C.read_support(C.registry_path(C.H19_5_SHA)) & foot
    dots, s, _ = build(visible, reg, h195, foot)
    region = np.zeros(grid.shape, bool)
    for f in folds:
        region |= f["region"]
    active = region & grid.footprint & ~folds[0]["masked_known"]
    pos, neg = active & hidden, active & ~hidden
    rs = np.random.default_rng(7)
    ny, nx = np.nonzero(neg)
    pick = rs.choice(ny.size, size=min(ny.size, 4 * int(pos.sum())), replace=False)
    py, px = np.nonzero(pos)
    yy, xx = np.r_[py, ny[pick]], np.r_[px, nx[pick]]
    lab = np.r_[np.ones(py.size), np.zeros(pick.size)]
    feats = {"neg_distance_to_H19_5": -ndi.distance_transform_edt(~h195),
             "H19_5_member": h195.astype(np.float32),
             "neg_distance_to_E3_holdout_dots": -ndi.distance_transform_edt(~dots),
             "E3_score_ASGT_visible": s}
    out = {}
    for k, v in feats.items():
        auc = float(roc_auc_score(lab, v[yy, xx]))
        out[k] = {"raw_auc": round(auc, 5), "oriented_auc": round(max(auc, 1 - auc), 5)}
    worst = max(out.items(), key=lambda kv: kv[1]["oriented_auc"])
    res = {"schema_version": 1, "threshold": 0.90, "split": "gems57 buffered_component_draw seed 20 (same as E1/E3)",
           "n_pos": int(py.size), "n_neg": int(pick.size), "features": out, "max_feature": worst[0],
           "max_oriented_auc": worst[1]["oriented_auc"], "passed": worst[1]["oriented_auc"] <= 0.90,
           "note": "H19-5 was built by GEMSDOE19 from the full catalogue, so E3/C1 holdout values are leak-advantaged "
                   "even when the canary passes; only the paired E3-C1 difference is interpretable.",
           "seconds": round(time.time() - t0, 1)}
    (ROOT / "evidence" / "e3_canary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    from archive_guard import stop_archived_cli
    stop_archived_cli()
    sys.exit(main())
