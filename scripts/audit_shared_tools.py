#!/usr/bin/env python3
"""Synthetic operator tests of the UNMODIFIED shared evaluator.

These are not geological experiments, HOLDOUT-DTI model results, forecasts, or
organizer receipts. No competition input or candidate prediction is evaluated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.shared_tools import load_tool, verify_template


def synthetic_context(empty_last: bool = True):
    module = load_tool("evaluate_holdout")
    holdout = module.holdout
    foot = np.ones((12, 12), dtype=bool)
    visible = np.zeros_like(foot)
    truth = visible.copy()
    truth[5, 5] = True
    cells = []
    for draw in holdout.DRAWS:
        for fold in holdout.FOLDS:
            empty = empty_last and draw == holdout.DRAWS[-1] and fold == holdout.FOLDS[-1]
            target = visible if empty else truth
            cells.append(holdout.PreparedCell(
                key=f"draw{draw}_fold{fold}", fold=fold, seed=draw,
                bbox=(slice(0, 12), slice(0, 12)), active_sub=foot.copy(),
                truth_coords=np.nonzero(target), n_truth=int(target.sum()),
                k_dg_sub=holdout.kernel(distance_transform_edt(~target)),
                visible_sub=visible.copy(), visible_full=visible.copy(),
                d_visible_sub=np.full(foot.shape, 999.0),
            ))
    return holdout, SimpleNamespace(foot=foot, cells=cells), truth


def audit() -> dict:
    lock = verify_template()
    if not lock["ok"]:
        return {"kind": "SYNTHETIC OPERATOR AUDIT — NOT HOLDOUT-DTI", "ok": False, "source_lock": lock, "blocking_findings": ["Shared files differ from their source lock"]}
    holdout, context, prediction = synthetic_context()
    output = holdout.evaluate_hide_and_recover(prediction, context, grid_n=2, n_boot=32, seed=17, name="SYNTHETIC-OPERATOR-ONLY")
    fold_fp = sum(fold["fp"] for fold in output["folds"].values())
    block_fp = float(output["_block_totals"][1].sum())
    preserved = bool(np.isclose(fold_fp, block_fp, atol=1e-12))
    # The contract is binary masks. Expose silent soft-value coercion rather than
    # describing a soft field's nonzero support as a calibrated probability test.
    soft_output = holdout.evaluate_hide_and_recover(prediction.astype(float) * 0.05, context, grid_n=2, n_boot=32, seed=17)
    soft_binarized = bool(np.isclose(soft_output["pooled_dti"], output["pooled_dti"]))
    findings = [] if preserved else [{
        "id": "SHARED-EMPTY-TRUTH-FP", "severity": "BLOCKER",
        "path": "src/gems32/holdout.py", "lines": [682, 684],
        "description": "The n_t == 0 branch records cell false positives, then continues without adding them to fp_blk. Pooled DTI/bootstrap therefore omit this prediction mass.",
        "reproduction": "python scripts/audit_shared_tools.py; tests/test_shared_tools.py",
        "resolution": "Repair once upstream, pin the corrected commit, rerun these tests; no local evaluator fork is permitted.",
        "upstream_issue": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41",
        "upstream_issue_status_at_review": "OPEN; existing issue independently reproduced, no duplicate issue opened",
    }]
    return {
        "schema_version": 1,
        "kind": "SYNTHETIC OPERATOR AUDIT — NOT HOLDOUT-DTI",
        "source_lock": lock,
        "checks": {"empty_truth_cell_fp_preserved_in_pooled_totals": preserved, "soft_fields_are_silently_binarized": soft_binarized},
        "blocking_findings": findings,
        "ok": not findings,
        "numerical_model_scores": None,
        "note": "Synthetic fixtures only. This does not show that any historical competition result was affected. Use binary masks only; soft probability evaluation is not supported by this shared hide-and-recover entry point.",
    }


def main() -> int:
    result = audit()
    out = ROOT / "evidence" / "shared_tool_audit.json"
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
