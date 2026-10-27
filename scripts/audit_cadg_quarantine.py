#!/usr/bin/env python3
"""Reopen the inherited CADG TIFFs against a pinned lattice; never create a candidate.

This is a saved-byte geometry/format audit, not a model experiment, a score, a
full-registry comparison, or a submission authorization. Inputs remain local and
ignored. The participant sample is not an organizer-authenticated template.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from scripts.audit_history import disk
from scripts.audit_parallel_candidate import audit
from scripts.github_source import GitHubSource, sha256_file
from scripts.validate_submission import validate

LATTICE_ID = "calib_13gems_20261001_r13-lattice-s5_v2_nan-ou"


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file() or sha256_file(path) != expected:
        raise ValueError(f"Missing or changed pinned input: {path}")


def measure(restore_lattice: bool = False) -> dict:
    manifest = json.loads((ROOT / "vendor/shared-template/registry/data_manifest.json").read_text())
    entries = {entry["id"]: entry for entry in manifest["files"]}
    card = json.loads((ROOT / "evidence/cadg-submod-run-card.json").read_text())
    if card.get("verdict") != "negative" or card.get("slot_authorized") is not False:
        raise ValueError("Archived CADG card is not a negative, slot-unauthorized card")
    sample, labels = (ROOT / "data/core" / entries[name]["dest"] for name in ("sample_submission", "labels"))
    for name, path in (("sample_submission", sample), ("labels", labels)):
        require_hash(path, entries[name]["sha256"])
    row = entries[LATTICE_ID]
    lattice = ROOT / "data/core" / row["dest"]
    if restore_lattice:
        GitHubSource().restore(row["repo"], row["ref"], row["path"], lattice, row["sha256"])
    require_hash(lattice, row["sha256"])

    artifacts = card["submission_artifacts"]
    measurements = {}
    for key, prefix, profile in (("zeros", "primary_zeros", "finite-grid"),
                                  ("nan", "official_nan_twin", "template-mask")):
        candidate = ROOT / artifacts[prefix + "_tif"]
        require_hash(candidate, artifacts[prefix + "_sha256"])
        geom = audit(candidate, lattice, sample, labels)
        fmt = validate(sample, candidate, profile, expected_dots=card["validator"]["predicted_positive_dots"])
        # Portable receipts must not depend on the checkout's absolute directory.
        fmt["template"] = str(sample.relative_to(ROOT))
        fmt["candidate"] = str(candidate.relative_to(ROOT))
        measurements[key] = {"file": str(candidate.relative_to(ROOT)), "geometry": geom, "validator": fmt}

    # A second, older CADG pair remains published under a different content id.
    # It is a distinct prediction field, not another encoding of the main pair.
    old_receipt_path = ROOT / "docs/cadg-submod/downloads/receipt-kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00.json"
    old_receipt = json.loads(old_receipt_path.read_text())
    older = {}
    for key, section, profile in (("zeros", "primary_zero_outside", "finite-grid"),
                                  ("nan", "official_text_nan_outside_twin", "template-mask")):
        source = old_receipt[section]
        candidate = old_receipt_path.parent / source["file"]
        require_hash(candidate, source["sha256"])
        geom = audit(candidate, lattice, sample, labels)
        fmt = validate(sample, candidate, profile, expected_dots=card["validator"]["predicted_positive_dots"])
        fmt["template"] = str(sample.relative_to(ROOT))
        fmt["candidate"] = str(candidate.relative_to(ROOT))
        if not geom["duplicate_over_70_percent"]:
            raise ValueError("Older archived prediction no longer matches the expected duplicate stop")
        older[key] = {"file": str(candidate.relative_to(ROOT)), "geometry": geom, "validator": fmt}

    zero_path = ROOT / artifacts["primary_zeros_tif"]
    nan_path = ROOT / artifacts["official_nan_twin_tif"]
    with rasterio.open(sample) as src:
        template = src.read(1, masked=True)
    footprint = ~np.ma.getmaskarray(template) & np.isfinite(template.data)
    with rasterio.open(zero_path) as src:
        z = src.read(1, masked=False)
    with rasterio.open(nan_path) as src:
        n = src.read(1, masked=False)
    equal = bool(np.array_equal(z[footprint], n[footprint]))
    with rasterio.open(ROOT / older["zeros"]["file"]) as src:
        older_zero = src.read(1, masked=False)
    with rasterio.open(ROOT / older["nan"]["file"]) as src:
        older_nan = src.read(1, masked=False)
    older_equal = bool(np.array_equal(older_zero[footprint], older_nan[footprint]))
    different_pairs = int((older_zero[footprint] != z[footprint]).sum())
    if not older_equal or different_pairs == 0:
        raise ValueError("Archived older pair has changed identity or is not the distinct earlier field")
    with rasterio.open(labels) as src:
        label = src.read(1, masked=True)
    sample_positive = footprint & (template.data > 0)
    label_positive = footprint & ~np.ma.getmaskarray(label) & (label.data > 0)
    with rasterio.open(lattice) as src:
        reference = src.read(1, masked=True)
    reference_dots = footprint & ~np.ma.getmaskarray(reference) & (reference.data > 0)
    off_catalogue = reference_dots & ~label_positive
    candidate_dots = footprint & (z > 0)
    within_offcat = int((candidate_dots & binary_dilation(off_catalogue, structure=disk(3))).sum())
    n_dots = int(candidate_dots.sum())
    if not equal or not all(v["geometry"]["duplicate_over_70_percent"] for v in measurements.values()):
        raise ValueError("The archived bytes do not support the expected negative decision")
    return {
        "schema_version": 1,
        "kind": "SAVED-BYTE FORENSIC MEASUREMENT — NOT A MODEL SCORE",
        "scope": "Four pre-existing TIFFs (two prediction fields and their encodings) versus one pinned binary lattice; not a complete registry or surface re-audit.",
        "lattice_source": {"repo": row["repo"], "commit": row["ref"], "path": row["path"], "sha256": row["sha256"]},
        "measurements": measurements,
        "older_9a_pair": {
            "writer_receipt": str(old_receipt_path.relative_to(ROOT)),
            "writer_receipt_sha256": sha256_file(old_receipt_path),
            "measurements": older,
            "equal_prediction_values_inside_mirrored_footprint": older_equal,
            "pixels_different_from_f056_pair": different_pairs,
            "not_a_new_candidate": True
        },
        "reference_mask_sensitivity": {
            "full_reference_dots": int(reference_dots.sum()),
            "reference_dots_on_catalogue": int((reference_dots & label_positive).sum()),
            "off_catalogue_reference_dots": int(off_catalogue.sum()),
            "candidate_dots_near_off_catalogue_reference": within_offcat,
            "candidate_fraction_near_off_catalogue_reference": within_offcat / n_dots,
            "note": "Earlier CADG reporting removed mapped-fault pixels from the reference lattice; the literal registry check uses the full raster. Both exceed the stop threshold."
        },
        "equal_prediction_values_inside_mirrored_footprint": equal,
        "sample_mirror_positive_pixels": int(sample_positive.sum()),
        "sample_positive_equals_label_positive": bool(np.array_equal(sample_positive, label_positive)),
        "sample_mirror_organizer_authenticated": False,
        "surface_audited_in_this_replay": False,
        "complete_registry_audited_in_this_replay": False,
        "portal_acceptance_verified": False,
        "rejected_upload_bytes_available": False,
        "candidate_generated_in_this_session": False,
        "slots_used_in_this_session": 0,
        "verdict": "negative",
        "ok_to_submit": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore-lattice", action="store_true", help="Restore the pinned participant-mirror lattice via GitHub")
    parser.add_argument("--output", type=Path, help="Write a dated forensic receipt")
    args = parser.parse_args()
    try:
        result = measure(args.restore_lattice)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"verdict": "negative", "ok_to_submit": False, "error": str(exc)}), file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    # Successful forensic execution, not a successful novelty or submission gate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
