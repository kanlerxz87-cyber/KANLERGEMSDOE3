#!/usr/bin/env python3
"""Audit the preserved CADG TIFF against all lattice dots and the card's subset.

No model score, prediction, competition upload, or registry exemption is created.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.audit_history import disk  # noqa: E402
from scripts.audit_parallel_candidate import audit, read  # noqa: E402
from scripts.github_source import GitHubSource, sha256_file  # noqa: E402
from scripts.restore_inputs import restore_entry  # noqa: E402
from scripts.shared_tools import TEMPLATE, verify_template  # noqa: E402

LATTICE_SHA256 = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"


def run(restore: bool = False) -> dict:
    card = json.loads((ROOT / "evidence/cadg-submod-run-card.json").read_text())
    if card["verdict"] != "negative" or card["slot_authorized"] is not False:
        raise ValueError("Historical CADG card is not the expected negative record")
    if not verify_template()["ok"]:
        raise ValueError("Pinned shared source lock failed")
    core = {r["id"]: r for r in json.loads((TEMPLATE / "registry/data_manifest.json").read_text())["files"]}
    candidate = ROOT / card["submission_artifacts"]["primary_zeros_tif"]
    sample, labels = ROOT / "data/core/sample_submission.tif", ROOT / "data/core/labels.tif"
    lattice = ROOT / "data/registry-review/lattice.tif"
    if restore:
        source = GitHubSource()
        for name in ("sample_submission", "labels"):
            restore_entry(core[name], ROOT / "data/core", source)
        source.restore("buffedlizard55-lab/GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
                       "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
                       lattice, LATTICE_SHA256)
    for path, digest in ((candidate, card["raster_sha256"]), (lattice, LATTICE_SHA256),
                         (sample, core["sample_submission"]["sha256"]), (labels, core["labels"]["sha256"])):
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"Missing or mismatched pinned input: {path.relative_to(ROOT)}")
    full = audit(candidate, lattice, sample, labels)
    sample_a, grid, _ = read(sample)
    pred, pred_grid, _ = read(candidate)
    ref, ref_grid, _ = read(lattice)
    labels_a, labels_grid, _ = read(labels)
    if not (grid == pred_grid == ref_grid == labels_grid):
        raise ValueError("Grid mismatch")
    footprint = ~np.ma.getmaskarray(sample_a) & np.isfinite(sample_a.data)
    labels_mask = ~np.ma.getmaskarray(labels_a) & (labels_a.data > 0) & footprint
    refs = ~np.ma.getmaskarray(ref) & (ref.data > 0) & footprint & ~labels_mask
    dots = ~np.ma.getmaskarray(pred) & (pred.data > 0) & footprint
    n = int(dots.sum())
    hits = int((dots & binary_dilation(refs, structure=disk(3))).sum())
    fraction = hits / n
    recorded = card["final_dot_overlap_3px"]
    if (n != full["candidate_dots"] or not full["duplicate_over_70_percent"]
            or not math.isclose(fraction, recorded, abs_tol=0.0000005, rel_tol=0)):
        raise ValueError("Lattice/card geometry is inconsistent; refuse an authoritative receipt")
    return {
        "kind": "HISTORICAL CADG SAVED-BYTE AUDIT; NOT HOLDOUT-DTI OR PROMOTION",
        "full_registered_lattice": full,
        "catalogue_excluded_lattice": {
            "definition": "Reference lattice cells on the mirrored visible catalogue excluded; included only to reproduce the historical card, not a registry exemption.",
            "reference_dots": int(refs.sum()), "candidate_dots": n,
            "candidate_dots_within_3px": hits, "directed_overlap_3px": fraction,
            "card_rounded_overlap": recorded, "matches_card": True,
        },
        "scope": "One prior candidate against one pinned lattice; no complete registry or surface audit. Mirrors are not organizer-authenticated.",
        "candidate_generated": False, "geological_experiments": 0, "slots_used": 0,
        "ok_to_submit": False, "slot_authorized": False, "verdict": "negative",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="Restore only pinned sample, labels and lattice")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result, code = run(args.restore), 1  # a duplicate is an intentional stop
    except Exception as exc:
        result, code = {"kind": "CADG AUDIT FAILED", "error": str(exc), "verdict": "negative",
                        "ok_to_submit": False, "slot_authorized": False}, 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
