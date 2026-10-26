#!/usr/bin/env python3
"""E2 — protocol-unique ASGT allocation + shared LLI projection (+ HOLDOUT-DTI of the same recipe).

Pre-declared grid (research/preregistration-20261026.md): budget N in {30k, 40k, 50k, 60k} x catalogue
exclusion radius in {3, 5} px, spacing 2.8 px, overlap cap 0.695 per comparable non-space-filling registry
raster.  Selection rule: highest LLI PROJECTION.  The unconstrained ASGT emission at the same N is reported
as a diagnostic of what uniqueness costs.  Output: evidence/e2_unique.json
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
from kgems import allocate as AL  # noqa: E402
from kgems import asgt as A  # noqa: E402
from kgems import common as C  # noqa: E402
from kgems import lli as L  # noqa: E402

BUDGETS = (30_000, 40_000, 50_000, 60_000)
EXCL = (3.0, 5.0)
SPACING = 2.8
CAP = 0.695


def main() -> int:
    t0 = time.time()
    foot, cat = C.footprint(), C.catalogue()
    d_cat = ndi.distance_transform_edt(~cat)
    comp = A.asgt_components(cat)          # live submission: the whole catalogue is visible
    score = A.asgt_score(comp)
    del comp
    gc.collect()
    spec = L.build_spec_s3()
    lam = L.archived_lambda(spec)
    champ = C.read_support(C.registry_path(C.CHAMPION_SHA)).astype(np.float32)
    champ_proj = L.project(champ, spec, lam)
    del champ
    reg = C.RegistryOverlap()
    h_i = next(i for i, r in enumerate(reg.rows) if r["sha256"].startswith(C.H19_5_SHA))
    print(f"setup {time.time()-t0:.0f}s; champion PROJECTION {champ_proj['dti']:.4f}", flush=True)
    results = []
    for ex in EXCL:
        allowed = foot & ~cat & (d_cat > ex)
        cand = A.nms_dots(score, allowed, 400_000, SPACING)
        flat = np.flatnonzero(cand.ravel())
        pri = score.ravel()[flat]
        order = np.argsort(-pri, kind="stable")
        use, M = AL.membership(reg, flat)
        print(f"ex={ex}: {flat.size} spaced candidates, membership {M.shape} ({time.time()-t0:.0f}s)", flush=True)
        for n in BUDGETS:
            for constrained in (True, False):
                if constrained:
                    acc, counts, limit = AL.constrained_greedy(order, M, n, CAP)
                else:
                    acc = order[:n]
                pick = flat[acc]
                pred = np.zeros(foot.size, np.float32)
                pred[pick] = 1.0
                pred = pred.reshape(foot.shape)
                pr = L.project(pred, spec, lam)
                ov = reg.overlaps(pick)
                nsf = reg.ok & ~reg.space_filling
                worst = int(np.nanargmax(np.where(nsf, ov, -1)))
                rec = {"excl_px": ex, "budget": n, "constrained": constrained, "dots": int(pick.size),
                       "lli_projection": round(pr["dti"], 5), "lli_tp": round(pr["tp"], 1), "lli_fp": round(pr["fp"], 1),
                       "overlap_H19_5": round(float(ov[h_i]), 4),
                       "worst_overlap_non_space_filling": round(float(ov[worst]), 4),
                       "worst_overlap_raster": reg.label(worst),
                       "worst_overlap_space_filling": round(float(np.nanmax(np.where(reg.space_filling, ov, -1))), 4)}
                results.append(rec)
                print(json.dumps(rec), flush=True)
                del pred
        del M, cand
        gc.collect()
    best = max((r for r in results if r["constrained"]), key=lambda r: r["lli_projection"])
    out = {"schema_version": 1, "experiment": "E2 protocol-unique ASGT allocation (K3-H1)",
           "evidence_class": "PROJECTION (shared LLI S3 archived fit; LOO MAE 0.0219, q90 0.054) — never a score",
           "lli": L.archive_meta(), "champion_projection_same_fit": round(champ_proj["dti"], 5),
           "champion_owner_reported_live": 0.2778, "cap": CAP, "spacing_px": SPACING,
           "grid": results, "selected": best, "seconds": round(time.time() - t0, 1)}
    (ROOT / "evidence" / "e2_unique.json").write_text(json.dumps(out, indent=1) + "\n")
    print("SELECTED", json.dumps(best))
    return 0


if __name__ == "__main__":
    from archive_guard import stop_archived_cli
    stop_archived_cli()
    sys.exit(main())
