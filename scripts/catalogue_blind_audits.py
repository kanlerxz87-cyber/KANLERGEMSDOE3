#!/usr/bin/env python3
"""Read-only audits behind the 28 Oct 2026 catalogue-blind session (no new candidate, no slot).

Writes evidence/catalogue-blind-audits-20261028.json with:
  * incumbent focus-site rasters (9) scored by the shared hide-and-recover and SGMC evaluators;
  * uniform-random and blue-noise controls at the same 37,654-dot budget;
  * leakage canary: AUC of every 35-channel feature ALONE against off-catalogue SGMC positives;
  * catalogue-proximity diagnostics of every dot field;
  * saturation check of the 13GEMSDOE r13-lattice-s5 calibration probe.
Requires: data/core restored (scripts/download_competition_data.sh), .cache/gems_work feature stack
(python scripts/catalogue_blind_candidate.py builds it on first run), .cache/registry_rasters.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.shared_tools import load_tool  # noqa: E402

FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
BUDGET = 37_654
SEED = 20261028
OUT = ROOT / "evidence" / "catalogue-blind-audits-20261028.json"


def main() -> int:
    load_tool("evaluate_holdout")
    from gems32 import holdout
    from sklearn.metrics import roc_auc_score

    ctx = holdout.load_holdout_context(ROOT / "data" / "core")
    foot = ctx.foot
    with rasterio.open(ROOT / "data/core/labels.tif") as s:
        lab = (s.read(1) >= 1) & foot
    with rasterio.open(ROOT / "data/core/external/derived_sgmc_faults_100m_u8.tif") as s:
        sgm = s.read(1) > 0
    dlab = distance_transform_edt(~lab)
    rng = np.random.default_rng(SEED)
    out: dict = {"schema": "kanler3.catalogue_blind_audits.v1",
                 "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    def both(mask: np.ndarray, name: str) -> dict:
        hr = holdout.evaluate_hide_and_recover(mask, ctx, name=name)
        sg = holdout.evaluate_sgmc_with_ci(mask, ctx, name=name)
        return {
            "dots": int(mask.sum()),
            "hide_recover_pooled_dti": round(float(hr["pooled_dti"]), 4),
            "hide_recover_ci95": [round(float(x), 4) for x in hr["ci95_cluster_bootstrap"]],
            "hide_recover_withheld_positives": int(hr["n_withheld_positives"]),
            "hide_recover_evaluator": hr["evaluator_version"],
            "sgmc_raw_pooled_dti": round(float(sg["sgmc_raw_pooled_dti"]), 4),
            "sgmc_raw_ci95": [round(float(x), 4) for x in sg["sgmc_raw_ci95"]],
            "sgmc_calibrated_dti": round(float(sg["sgmc_prevalence_calibrated_dti"]), 4),
            "sgmc_evaluator": sg["evaluator_version"],
            "sgmc_withheld_positives": int(sg["n_withheld_positives"]),
            "label": "HOLDOUT-DTI",
        }

    def proximity(mask: np.ndarray) -> dict:
        d = dlab[mask & foot]
        return {"dots_within_2px_of_catalogue": round(float((d <= 2).mean()), 4),
                "dots_within_3px_of_catalogue": round(float((d <= 3).mean()), 4),
                "dots_on_catalogue": int((d == 0).sum())}

    # 1. Incumbents, same evaluator (fixed masks, identical to the protocol's comparison).
    incumbents, prox = {}, {}
    for site in FOCUS:
        with rasterio.open(ROOT / "data" / f"{site}.tif") as s:
            a = s.read(1)
        m = np.isfinite(a) & (a > 0) & foot
        incumbents[site] = both(m, site)
        prox[site] = proximity(m)
        print(site, incumbents[site]["hide_recover_pooled_dti"], incumbents[site]["sgmc_raw_pooled_dti"], flush=True)
    out["incumbents_same_evaluator"] = incumbents

    # 2. Controls at the same budget.
    fy, fx = np.nonzero(foot)
    idx = rng.choice(len(fy), size=BUDGET, replace=False)
    rnd = np.zeros(foot.shape, bool)
    rnd[fy[idx], fx[idx]] = True
    out["control_uniform_random"] = both(rnd, "uniform_random")
    prox["uniform_random"] = proximity(rnd)
    print("random", out["control_uniform_random"]["hide_recover_pooled_dti"], flush=True)

    # 3. Leakage canary: each channel alone vs off-catalogue SGMC positives (AUC > 0.90 = leakage).
    near = binary_dilation(lab, iterations=3)
    pos = sgm & ~near & foot
    bg = foot & ~near & ~sgm
    stack = np.load(ROOT / ".cache/gems_work/feature_stack_35ch.npy", mmap_mode="r")
    names = json.loads((ROOT / ".cache/gems_work/feature_stack_receipt.json").read_text())["channels"]
    pi = np.flatnonzero(pos.ravel())
    bi = rng.choice(np.flatnonzero(bg.ravel()), size=400_000, replace=False)
    aucs = {}
    for c, n in enumerate(names):
        v = np.asarray(stack[:, :, c]).ravel()
        y = np.r_[np.ones(pi.size), np.zeros(bi.size)]
        aucs[n] = round(float(roc_auc_score(y, np.r_[v[pi], v[bi]])), 4)
    out["leakage_canary_auc_vs_sgmc_offcatalogue"] = {"positives": int(pos.sum()), "background_sample": int(bi.size),
                                                     "max_auc": max(aucs.values()), "channels_above_0_90": [k for k, v in aucs.items() if v > 0.90],
                                                     "auc": aucs}
    print("canary max", max(aucs.values()), flush=True)

    # 4. Hide-and-recover canary: catalogue-distance features alone, one cell (draw20 fold0).
    cell = ctx.cells[0]
    truth = np.zeros(foot.shape, bool)
    ty, tx = cell.truth_coords
    r0, c0 = cell.bbox[0].start, cell.bbox[1].start
    truth[ty + r0, tx + c0] = True
    active = np.zeros(foot.shape, bool)
    active[cell.bbox] = cell.active_sub
    vis = ctx.visible_by_cell[cell.key]
    dvis = distance_transform_edt(~vis)
    p = np.flatnonzero(truth.ravel())
    n = np.random.default_rng(0).choice(np.flatnonzero((active & ~truth).ravel()), size=300_000, replace=False)
    from sklearn.metrics import roc_auc_score as auc_fn
    y = np.r_[np.ones(p.size), np.zeros(n.size)]
    out["hide_recover_distance_canary"] = {
        "cell": cell.key, "n_truth": int(p.size),
        "auc_distance_to_FULL_catalogue": round(float(auc_fn(y, -np.r_[dlab.ravel()[p], dlab.ravel()[n]])), 4),
        "auc_distance_to_VISIBLE_catalogue": round(float(auc_fn(y, -np.r_[dvis.ravel()[p], dvis.ravel()[n]])), 4),
        "reading": "FULL-catalogue distance contains hidden truth (AUC 1.0 = leakage by construction). The visible-only AUC is legitimate but shows the proxy rewards proximity to known faults."}
    print("hr canary", out["hide_recover_distance_canary"], flush=True)

    # 5. Saturation of the calibration lattice.
    lat_path = ROOT / ".cache/registry_rasters/calib_13gems_20261001_r13-lattice-s5_v2_nan-ou.tif"
    with rasterio.open(lat_path) as s:
        lat = s.read(1)
    ldots = np.isfinite(lat) & (lat > 0) & foot
    cov = float((distance_transform_edt(~ldots)[foot] <= 3).mean())
    trials = []
    for _ in range(3):
        j = rng.choice(len(fy), size=BUDGET, replace=False)
        m = np.zeros(foot.shape, bool)
        m[fy[j], fx[j]] = True
        trials.append(round(float((distance_transform_edt(~ldots)[m] <= 3).mean()), 4))
    out["saturation_lattice_r13"] = {"lattice_dots": int(ldots.sum()), "footprint_fraction_within_3px": round(cov, 4),
                                    "uniform_random_directed_overlap_trials": trials,
                                    "reading": "any dot field trips the literal 70% test: the stop is non-discriminative for this reference"}
    # 6. Exact lineage of the GEMSDOE31 -> 32 -> 36 family (set differences, no scoring).
    def read_mask(site: str) -> np.ndarray:
        with rasterio.open(ROOT / "data" / f"{site}.tif") as s2:
            a2 = s2.read(1)
        return np.isfinite(a2) & (a2 > 0)

    m31, m32, m36 = read_mask("GEMSDOE31"), read_mask("GEMSDOE32"), read_mask("GEMSDOE36")
    out["lineage_exact"] = {
        "GEMSDOE32_subset_of_GEMSDOE31": bool(not (m32 & ~m31).any()),
        "removed_31_to_32": int((m31 & ~m32).sum()),
        "removed_31_to_32_within_2px_of_catalogue": int((dlab[m31 & ~m32] <= 2).sum()),
        "GEMSDOE31_dots_within_2px_of_catalogue": int((dlab[m31] <= 2).sum()),
        "added_32_to_36": int((m36 & ~m32).sum()),
        "added_32_to_36_within_2px_of_catalogue": int((dlab[m36 & ~m32] <= 2).sum()),
        "removed_32_to_36": int((m32 & ~m36).sum()),
    }
    out["catalogue_proximity"] = prox
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
