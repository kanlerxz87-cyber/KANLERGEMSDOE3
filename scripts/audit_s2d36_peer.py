#!/usr/bin/env python3
"""Reproduce a bounded saved-byte audit of the S2D-36 peer's research TIFF.

This does not train a model, calculate DTI, write a submission, or select a
weekly slot. Inputs are immutable participant-mirror bytes, not authenticated
organizer data. Only nine pinned historic dot rasters and one lattice are
compared; the candidate's pre-placement surface and the full registry are not.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.audit_history import disk, phi_binary, read_mask  # noqa: E402
from scripts.audit_parallel_candidate import audit as lattice_audit  # noqa: E402
from scripts.github_source import GitHubSource, sha256_file  # noqa: E402
from scripts.restore_inputs import restore_entry  # noqa: E402
from scripts.shared_tools import TEMPLATE, verify_template  # noqa: E402
from scripts.validate_submission import validate  # noqa: E402

PEER_REPO = "buffedlizard55-lab/GEMSDOE36"
PEER_COMMIT = "21eec80b50f0daa34e2c06536ab7ffafdfc1095e"
PEER_PATH = "docs/downloads/gemsdoe36-s2d36-exp2-20261027-31189d084a83-zeros.tif"
PEER_SHA256 = "d3ba2fdb987bec34fc0c61148829032a431a95b8921b1bd66d61ddd047f56b72"
CARD_PATH = ROOT / "evidence/peer-s2d36-card-21eec80b.json"
CARD_SHA256 = "5df79bfe5d1da5c04bac8e57d78333385105a31f5777eabfe452441ba2f2114c"
LATTICE_REPO = "buffedlizard55-lab/GEMSDOE24"
LATTICE_COMMIT = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"
LATTICE_PATH = "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
LATTICE_SHA256 = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"


def compare_dots(candidate: np.ndarray, reference: np.ndarray, footprint: np.ndarray) -> dict:
    """Directional proximity and binary Spearman; no support invented for soft rasters."""
    arrays = (candidate, reference, footprint)
    if any(not isinstance(a, np.ndarray) or a.ndim != 2 or a.dtype != np.bool_ for a in arrays):
        raise ValueError("Candidate, reference and footprint must be 2-D boolean arrays")
    if any(a.shape != footprint.shape for a in arrays) or not footprint.any():
        raise ValueError("Candidate, reference and nonempty footprint must share a grid")
    if any((a & ~footprint).any() for a in (candidate, reference)):
        raise ValueError("Dots must lie inside the footprint")
    n = int(candidate.sum())
    if not n or not reference.any():
        raise ValueError("Both dot sets must be nonempty")
    near = binary_dilation(reference, structure=disk(3))
    within = int((candidate & near).sum())
    rho = phi_binary(candidate[footprint], reference[footprint])
    if rho is None:
        raise ValueError("Binary rank correlation is undefined")
    return {
        "candidate_dots": n,
        "reference_dots": int(reference.sum()),
        "candidate_dots_within_3px": within,
        "directed_overlap_3px": within / n,
        "binary_spearman": rho,
        "duplicate": within / n > 0.70 or rho > 0.90,
    }


def peer_card() -> dict:
    if not CARD_PATH.is_file() or sha256_file(CARD_PATH) != CARD_SHA256:
        raise ValueError("Pinned peer run card is missing or altered")
    card = json.loads(CARD_PATH.read_text())
    s, h = card["submission"], card["holdout"]
    if (card.get("verdict") != "negative" or card.get("slot_approved") is not False
            or s.get("file") != PEER_PATH or s.get("sha256") != PEER_SHA256
            or s.get("dots") != 37654 or h.get("best_arm") != "EXP-2"):
        raise ValueError("Pinned peer card identity or negative status is inconsistent")
    return card


def run(restore: bool = False) -> dict:
    card = peer_card()
    lock = verify_template()
    if not lock["ok"]:
        raise ValueError("Pinned shared source lock failed")
    core = {r["id"]: r for r in json.loads((TEMPLATE / "registry/data_manifest.json").read_text())["files"]}
    winners = json.loads((ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text())["historical_winners"]
    if len(winners) != 9 or len({r["repo"] for r in winners}) != 9:
        raise ValueError("Expected nine distinct pinned historic winners")
    candidate = ROOT / "data/new-peer/s2d36.tif"
    lattice = ROOT / "data/registry-review/lattice.tif"
    sample = ROOT / "data/core/sample_submission.tif"
    labels = ROOT / "data/core/labels.tif"
    source = GitHubSource()
    if restore:
        source.restore(PEER_REPO, PEER_COMMIT, PEER_PATH, candidate, PEER_SHA256)
        source.restore(LATTICE_REPO, LATTICE_COMMIT, LATTICE_PATH, lattice, LATTICE_SHA256)
        for name in ("sample_submission", "labels"):
            restore_entry(core[name], ROOT / "data/core", source)
        for row in winners:
            source.restore("buffedlizard55-lab/" + row["repo"], row["head"], row["file"],
                           ROOT / "data" / (row["repo"] + ".tif"), row["sha256"])
    expected = [(candidate, PEER_SHA256), (lattice, LATTICE_SHA256),
                (sample, core["sample_submission"]["sha256"]), (labels, core["labels"]["sha256"])]
    expected += [(ROOT / "data" / (r["repo"] + ".tif"), r["sha256"]) for r in winners]
    for path, digest in expected:
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"Missing or mismatched pinned input: {path.relative_to(ROOT)}")
    with rasterio.open(sample) as src:
        raw = src.read(1)
        footprint = (src.dataset_mask() > 0) & np.isfinite(raw)
        grid = {"shape": src.shape, "crs": src.crs, "transform": src.transform}
    peer, _ = read_mask(candidate, grid, footprint)
    lattice_result = lattice_audit(candidate, lattice, sample, labels)
    rows = []
    for row in winners:
        ref_path = ROOT / "data" / (row["repo"] + ".tif")
        ref, _ = read_mask(ref_path, grid, footprint)
        rows.append({"site": row["repo"], "reference_sha256": row["sha256"],
                     **compare_dots(peer, ref, footprint)})
    validations = {profile: validate(sample, candidate, profile, expected_dots=37654)
                   for profile in ("template-mask", "finite-grid", "masked-finite")}
    finite = validations["finite-grid"]
    best = card["holdout"]["arms"]["EXP-2"]
    return {
        "schema_version": 1,
        "observed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": "PEER SAVED-BYTE GEOMETRY AND FORMAT AUDIT; NOT A MODEL SCORE",
        "peer": {"repository": "https://github.com/" + PEER_REPO, "commit": PEER_COMMIT,
                 "file": PEER_PATH, "sha256": PEER_SHA256,
                 "card_path": "docs/downloads/s2d36-run-card.json", "card_sha256": CARD_SHA256,
                 "source_card": "evidence/peer-s2d36-card-21eec80b.json",
                 "peer_verdict": card["verdict"],
                 "source_holdout": {"evidence_class": "HOLDOUT-DTI", "value": best["dti"],
                                    "ci95": best["ci95"],
                                    "evaluator_version": card["holdout"]["evaluator_version"],
                                    "withheld_positives": card["holdout"]["n_withheld_positive_pixels"],
                                    "scope": "Participant-reported; not independently rerun or a leaderboard estimate."}},
        "lattice": lattice_result,
        "nine_historical_final_dot_comparisons": rows,
        "validator": {"version": finite["validator"], "candidate_sha256": finite["candidate_sha256"],
                      "sample_mirror_sha256": finite["template_sha256"],
                      "profiles": {key: value["ok"] for key, value in validations.items()},
                      "checks": finite["checks"], "in_footprint_finite_range": finite["finite_range_inside"],
                      "raw_range_diagnostics": finite["raw_range_diagnostics"],
                      "portal_acceptance_verified": False,
                      "organizer_template_authenticated": False},
        "surface_compared": False,
        "complete_registry_compared": False,
        "scope": "One prior peer TIFF against nine historical winners and one lattice; no new candidate or pre-placement surface. Hash-pinned mirrors are not organizer-authenticated.",
        "candidate_generated": False,
        "geological_experiments": 0,
        "slots_used": 0,
        "ok_to_submit": False,
        "slot_authorized": False,
        "verdict": "negative",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="Restore only pinned forensic inputs from GitHub")
    parser.add_argument("--output", type=Path, help="Write the audit (including a negative error receipt on failure)")
    args = parser.parse_args()
    try:
        result = run(args.restore)
        code = 1  # A bounded forensic audit cannot authorize an upload.
    except Exception as exc:
        result = {"kind": "PEER AUDIT FAILED", "error": str(exc), "verdict": "negative",
                  "ok_to_submit": False, "slot_authorized": False}
        code = 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
