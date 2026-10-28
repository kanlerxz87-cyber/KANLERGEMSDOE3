#!/usr/bin/env python3
"""Read-only uniqueness audit of ANY candidate TIFF against the restored registry (no scoring, no slot).

Applies the same full-footprint geometry rule as scripts/catalogue_blind_candidate.py
(scripts/check_uniqueness.compare; stop at Spearman > 0.90 or > 70% directed 3 px overlap) to a
file produced by another lane. Writes evidence/uniqueness-audit-<stem>-20261028.json.

With --holdout, also scores the file on the SAME shared evaluators as the catalogue-blind incumbents
(GEMSDOE32-HIDE-RECOVER-v3.0 and GEMSDOE32-SGMC-CAL-v3.0). Read-only; not an experiment; no slot.

Usage: python scripts/audit_candidate_uniqueness.py <path/to/candidate.tif> [--holdout]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.catalogue_blind_candidate import REGISTRY, RESTORE_LOG, TEMPLATE, reference_coverage, sha256_file, uniqueness  # noqa: E402


def main(argv: list[str]) -> int:
    holdout = "--holdout" in argv
    argv = [a for a in argv if a != "--holdout"]
    if len(argv) != 1:
        print(__doc__)
        return 2
    cand = Path(argv[0]).resolve()
    with rasterio.open(TEMPLATE) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(cand) as s:
        arr = s.read(1)
        shape_ok = (s.height, s.width) == (3730, 3292) and s.crs.to_string() == "EPSG:32611"
    dots = np.isfinite(arr) & (arr > 0) & foot
    u = uniqueness(dots, foot, "external-candidate-final-dots")
    rows = [{k: v for k, v in r.items() if k != "rows"} for r in u["rows"]]
    out = {
        "schema": "kanler3.external_uniqueness_audit.v1",
        "candidate": str(cand.relative_to(ROOT)) if cand.is_relative_to(ROOT) else str(cand),
        "candidate_sha256": sha256_file(cand),
        "grid_matches_template": shape_ok,
        "dots": int(dots.sum()),
        "registry_file": str(REGISTRY.relative_to(ROOT)),
        "registry_total_listed": u["registry_total_listed"],
        "registry_compared": u["registry_compared"],
        "registry_missing": u["registry_missing"],
        "max_directed_overlap_3px_non_saturated": max((r["directed_dot_overlap_3px"] for r in rows if r.get("comparable") and not r.get("saturated")), default=None),
        "max_abs_rank_corr": u["max_abs_rank_corr"],
        "duplicates_non_saturated": u["duplicates"],
        "saturated_probe_flags": u["saturated_probe_flags"],
        "label": "GEOMETRIC_AUDIT_NOT_SCORE",
        "slot_authorized": False,
    }
    if holdout:
        from scripts.shared_tools import load_tool
        load_tool("evaluate_holdout")
        from gems32 import holdout as ho
        ctx = ho.load_holdout_context(ROOT / "data" / "core")
        hr = ho.evaluate_hide_and_recover(dots, ctx, name=cand.stem)
        sg = ho.evaluate_sgmc_with_ci(dots, ctx, name=cand.stem)
        out["same_evaluator_holdout"] = {
            "label": "HOLDOUT-DTI",
            "hide_recover_pooled_dti": round(float(hr["pooled_dti"]), 4),
            "hide_recover_ci95": [round(float(x), 4) for x in hr["ci95_cluster_bootstrap"]],
            "hide_recover_evaluator": hr["evaluator_version"],
            "sgmc_raw_pooled_dti": round(float(sg["sgmc_raw_pooled_dti"]), 4),
            "sgmc_raw_ci95": [round(float(x), 4) for x in sg["sgmc_raw_ci95"]],
            "sgmc_evaluator": sg["evaluator_version"],
            "incumbent_best_same_evaluator": {"hide_recover": 0.0967, "sgmc_raw": 0.1024},
        }
        print(json.dumps(out["same_evaluator_holdout"], indent=2))
    dest = ROOT / "evidence" / f"uniqueness-audit-{cand.stem}-20261028.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("dots", "registry_compared", "max_directed_overlap_3px_non_saturated", "max_abs_rank_corr", "duplicates_non_saturated", "saturated_probe_flags")}, indent=2))
    print("wrote", dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
