#!/usr/bin/env python3
"""Run synthetic invariants against one immutable, unmodified upstream commit.

This is an instrument audit, not a geological experiment or leaderboard score.
It does not install, repin, repair or authorize the observed source. The bytes
are verified as Git blobs, loaded in an isolated temporary package and discarded.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_upstream_prerequisites import REPOSITORY, content_at  # noqa: E402

AUDITED_COMMIT = "e56a10a9d2f218c05ea66c5a5b7228bb780bb5a7"
# Fixed byte identities for the source inspected during this review. Do not run
# arbitrary future GitHub code merely because a caller supplies a commit.
SOURCES = {
    "__init__.py": "e4a584f79eab8c0db81b5704b1525536fef2dcee5bac28da1455a39868983504",
    "metric.py": "382de3eb6d77d549e01bafa718fd01f5a7132263be0b6925dbd5a40a24025289",
    "submission.py": "d397118a7165f674ba45bdea89b65852f2a24450edaa9b7e00e7cd5b87f0b9e1",
    "holdout.py": "9ce9cf359f4d7b7fa844dd8f208ec00c3e6c15afef5d724d9014320b944d318d",
}


def probe_module(holdout) -> dict:
    """Exercise the empty-truth accounting and soft-input contract on a tiny fixture."""
    footprint = np.ones((12, 12), dtype=bool)
    empty = np.zeros_like(footprint)
    truth = empty.copy()
    truth[5, 5] = True
    cells = []
    for draw in holdout.DRAWS:
        for fold in holdout.FOLDS:
            target = empty if (draw, fold) == (holdout.DRAWS[-1], holdout.FOLDS[-1]) else truth
            cells.append(holdout.PreparedCell(
                key=f"draw{draw}_fold{fold}", fold=fold, seed=draw,
                bbox=(slice(0, 12), slice(0, 12)), active_sub=footprint.copy(),
                truth_coords=np.nonzero(target), n_truth=int(target.sum()),
                k_dg_sub=holdout.kernel(distance_transform_edt(~target)),
                visible_sub=empty.copy(), visible_full=empty.copy(),
                d_visible_sub=np.full(footprint.shape, 999.0),
            ))
    context = SimpleNamespace(foot=footprint, cells=cells)
    result = holdout.evaluate_hide_and_recover(truth, context, grid_n=2, n_boot=32, seed=17, name="SYNTHETIC-ONLY")
    fold_fp = float(sum(row["fp"] for row in result["folds"].values()))
    block_fp = float(result["_block_totals"][1].sum())
    try:
        soft = holdout.evaluate_hide_and_recover(truth.astype(float) * 0.05, context, grid_n=2, n_boot=32, seed=17)
    except ValueError as exc:
        soft_behavior = "REJECTED"
        soft_detail = str(exc)
    else:
        # A matching binary result demonstrates coercion in this fixture only.
        soft_behavior = "SILENTLY_BINARIZED" if np.isclose(soft["pooled_dti"], result["pooled_dti"]) else "ACCEPTED_DIFFERENT_RESULT"
        soft_detail = "Accepted; equality with the binary fixture was checked, not probability correctness."
    return {
        "empty_truth_fp_preserved": bool(np.isclose(fold_fp, block_fp, atol=1e-12)),
        "synthetic_fold_fp": fold_fp,
        "synthetic_pooled_block_fp": block_fp,
        "soft_input_behavior": soft_behavior,
        "soft_detail": soft_detail,
        "scope": "Synthetic fixtures only; neither observed behavior proves an organizer result or a complete repair.",
    }


def audit(commit: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or commit != AUDITED_COMMIT:
        raise ValueError("Only the explicitly reviewed and hash-pinned upstream commit may be executed")
    source_rows, contents = [], {}
    for name, expected_sha in SOURCES.items():
        path = f"src/gems32/{name}"
        metadata, raw = content_at(path, commit)
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != expected_sha:
            raise ValueError(f"Observed source SHA-256 mismatch: {path}")
        source_rows.append({"path": path, "git_blob_sha1": metadata["sha"], "sha256": actual_sha})
        contents[name] = raw

    # A separate package name prevents accidentally importing an older installed
    # gems32. Only bytes returned by content_at's Git-blob verifier are executed.
    package_name = "_observed_gems32_synthetic_audit"
    with tempfile.TemporaryDirectory(prefix="gems-shared-audit-") as temporary:
        pkg = Path(temporary) / package_name
        pkg.mkdir()
        for name, raw in contents.items():
            (pkg / name).write_bytes(raw)
        try:
            spec = importlib.util.spec_from_file_location(package_name, pkg / "__init__.py", submodule_search_locations=[str(pkg)])
            if spec is None or spec.loader is None:
                raise ValueError("Cannot load observed source package")
            module = importlib.util.module_from_spec(spec)
            sys.modules[package_name] = module
            spec.loader.exec_module(module)
            holdout = importlib.import_module(package_name + ".holdout")
            checks = probe_module(holdout)
        finally:
            for key in list(sys.modules):
                if key == package_name or key.startswith(package_name + "."):
                    del sys.modules[key]
    return {
        "kind": "UPSTREAM SYNTHETIC OPERATOR AUDIT — NOT HOLDOUT-DTI",
        "repository": REPOSITORY,
        "commit": commit,
        "sources": source_rows,
        "checks": checks,
        "source_repinned": False,
        "candidate_generated": False,
        "slot_authorized": False,
        "verdict": "negative",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True, help="Immutable upstream Git commit")
    parser.add_argument("--output", type=Path, help="Optional audit receipt; stdout otherwise")
    args = parser.parse_args()
    try:
        result = audit(args.commit)
        # A failed conservation invariant remains a blocking negative result.
        code = 0 if result["checks"]["empty_truth_fp_preserved"] else 1
    except Exception as exc:
        result = {"kind": "UPSTREAM OPERATOR AUDIT FAILED", "error": str(exc),
                  "candidate_generated": False, "slot_authorized": False, "verdict": "negative"}
        code = 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
