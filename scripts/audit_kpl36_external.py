#!/usr/bin/env python3
"""Recheck a pinned peer TIFF against the required calibration lattice.

A read-only forensic audit, not a geological experiment, new candidate,
submission, full-registry comparison or score reproduction. The peer's own
promotion decision is not adopted. Restored inputs go to ignored data/ only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from scripts.audit_parallel_candidate import audit  # noqa: E402
from scripts.github_source import GitHubSource, sha256_file  # noqa: E402
from scripts.validate_submission import validate  # noqa: E402

PEER_REPO = "buffedlizard55-lab/GEMSDOE36"
PEER_COMMIT = "61783525af4aa6dcf8da0bc68b06fa38b89ed27a"
PEER_CARD = ROOT / "evidence/upstream/GEMSDOE36/kpl36-run-card-61783525.json"
PEER_CARD_SHA = "9448983264018a95518f79da1f63ecfb0f981f740f11ceaeebf341abac8a8d04"
PEER_FILE = "docs/downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif"
PEER_SHA = "86fc8243ad573bcdbfac8b432daf0ec5b6800b991b2c3278706358be7eb9922d"


def run(restore: bool = False) -> dict:
    if sha256_file(PEER_CARD) != PEER_CARD_SHA:
        raise ValueError("Pinned peer run card altered")
    card = json.loads(PEER_CARD.read_text())
    if (card.get("verdict") != "promote" or card.get("submission", {}).get("file") != PEER_FILE
            or card["submission"].get("sha256") != PEER_SHA or card["submission"].get("dots") != 37654):
        raise ValueError("Pinned peer identity/claim mismatch")
    lattice_record = next(r for r in json.loads((ROOT / "research/registry-lock.json").read_text())["entries"] if r["id"] == "registry-160")
    core = {r["id"]: r for r in json.loads((ROOT / "data/core-manifest.json").read_text())["files"]}
    candidate = ROOT / "data/registry-review/kpl36-remote.tif"
    lattice = ROOT / "data/registry-review/lattice.tif"
    sample = ROOT / "data/core" / core["sample_submission"]["dest"]
    labels = ROOT / "data/core" / core["labels"]["dest"]
    if restore:
        source = GitHubSource()
        source.restore(PEER_REPO, PEER_COMMIT, PEER_FILE, candidate, PEER_SHA)
        source.restore(lattice_record["repo"], lattice_record["ref"], lattice_record["file"], lattice, lattice_record["sha256"])
    for name, path, expected in (("peer TIFF", candidate, PEER_SHA), ("lattice", lattice, lattice_record["sha256"]),
                                 ("sample", sample, core["sample_submission"]["sha256"]), ("labels", labels, core["labels"]["sha256"])):
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Missing or altered {name}; restore pinned inputs before the audit")
    result = audit(candidate, lattice, sample, labels)
    validator = validate(sample, candidate, "finite-grid", expected_dots=37654)
    # Keep the frozen receipt portable across checkout locations.
    validator["template"] = str(sample.relative_to(ROOT))
    validator["candidate"] = str(candidate.relative_to(ROOT))
    holdout = card["holdout"]
    arm = holdout["arms"]["EXP-3"]
    return {
        "kind": "PEER SAVED-BYTE GEOMETRY AUDIT; not a new model or organizer score",
        "peer_source": {
            "repository": "https://github.com/" + PEER_REPO,
            "commit": PEER_COMMIT, "file": PEER_FILE, "file_sha256": PEER_SHA,
            "run_card_path": "docs/downloads/kpl36-run-card.json", "run_card_sha256": PEER_CARD_SHA,
            "peer_verdict": card["verdict"],
            "peer_holdout": {"evidence_class": "HOLDOUT-DTI", "evaluator_version": holdout["evaluator_version"],
                             "withheld_positive_pixels": holdout["n_withheld_positive_pixels"],
                             "dti": arm["dti"], "ci95": arm["ci95"],
                             "scope": "Participant-reported; not independently rerun or comparable to a different split/evaluator."},
        },
        "lattice_source": lattice_record,
        "final_dot_lattice_comparison": result,
        "validator": validator,
        "surface_registry_comparison": None,
        "full_registry_compared": False,
        "interpretation": "The peer approves its file after excluding the calibration lattice from its detector-only comparison. Under this session's literal all-registry rule, the measured lattice overlap is a duplicate stop. A format pass and the peer's promotion claim do not authorize a slot.",
        "verdict": "negative" if result["duplicate_over_70_percent"] else "blocked_incomplete_registry",
        "slot_authorized": False, "candidate_generated": False, "geological_experiments_run": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="Restore the two pinned peer/lattice inputs, not core data")
    parser.add_argument("--output", type=Path, help="Optional JSON receipt; failure overwrites a stale receipt")
    args = parser.parse_args()
    try:
        result = run(args.restore)
        code = 1  # Duplicate or an incomplete comparison never authorizes a slot.
    except Exception as exc:
        result = {"kind": "PEER GEOMETRY AUDIT FAILED", "verdict": "negative", "slot_authorized": False,
                  "error": str(exc)}
        code = 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
