#!/usr/bin/env python3
"""Audit existing CADG TIFF/ZIP bytes against one registered lattice.

Forensic only: no placement, model, score, writer, promotion or upload. A
one-reference overlap stop is conclusive for a duplicate, not a complete
registry pass. Inputs are pinned participant mirrors, not organizer data.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from scripts.audit_history import disk  # noqa: E402
from scripts.audit_parallel_candidate import audit  # noqa: E402
from scripts.github_source import GitHubSource, sha256_file  # noqa: E402
from scripts.validate_submission import validate  # noqa: E402


def archive_member(directory: Path, name: object, suffix: str) -> Path:
    """Allow only regular, direct children; receipts cannot select other files."""
    if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name or not name.endswith(suffix):
        raise ValueError("Unsafe archive member name")
    path = directory / name
    if path.is_symlink() or not path.is_file() or path.resolve().parent != directory.resolve():
        raise ValueError("Missing or unsafe archive member: " + name)
    return path


def run(root: Path = ROOT, restore: bool = False) -> dict:
    root = root.resolve()
    archive = root / "docs/cadg-submod/downloads"
    card_path = root / "evidence/cadg-submod-run-card.json"
    card = json.loads(card_path.read_text())
    if card.get("verdict") != "negative" or card.get("slot_authorized") is not False:
        raise ValueError("CADG's original card is not a negative, unauthorized run")
    registry = json.loads((root / "research/registry-lock.json").read_text())
    lattice_row = next(row for row in registry["entries"] if row["id"] == "registry-160")
    core = {row["id"]: row for row in json.loads((root / "data/core-manifest.json").read_text())["files"]}
    lattice = root / "data/registry-review/lattice.tif"
    sample = root / "data/core" / core["sample_submission"]["dest"]
    labels = root / "data/core" / core["labels"]["dest"]
    if restore:
        GitHubSource().restore(lattice_row["repo"], lattice_row["ref"], lattice_row["file"], lattice, lattice_row["sha256"])
    for name, path, expected in (("lattice", lattice, lattice_row["sha256"]),
                                 ("sample", sample, core["sample_submission"]["sha256"]),
                                 ("labels", labels, core["labels"]["sha256"])):
        if not path.is_file() or not path.resolve().is_relative_to(root) or sha256_file(path) != expected:
            raise ValueError(f"Missing or altered {name}; restore pinned inputs")

    with rasterio.open(sample) as src:
        foot = (src.dataset_mask() > 0) & np.isfinite(src.read(1))
    # The older CADG report removed catalogue pixels from the *reference* lattice.
    # Reproduce that narrower comparison as a diagnostic, but the literal registry
    # rule uses every positive lattice pixel, including those on the catalogue.
    with rasterio.open(labels) as src:
        catalogue = (src.dataset_mask() > 0) & (src.read(1) > 0) & foot
    with rasterio.open(lattice) as src:
        lattice_dots = (src.dataset_mask() > 0) & (src.read(1) > 0) & foot
    filtered = lattice_dots & ~catalogue
    if not filtered.any():
        raise ValueError("Empty catalogue-filtered reference; diagnostic undefined")
    filtered_halo = binary_dilation(filtered, structure=disk(3))
    results = []
    referenced = set()
    for receipt_path in sorted(archive.glob("receipt-*.json")):
        if receipt_path.is_symlink():
            raise ValueError("Receipt symlinks are not allowed")
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("scientific_verdict") != "negative" or receipt.get("weekly_slot_authorized") is not False:
            raise ValueError("Archive receipt does not explicitly deny promotion")
        twins = []
        version = {"receipt": str(receipt_path.relative_to(root)), "receipt_sha256": sha256_file(receipt_path), "files": []}
        for key, profile in (("primary_zero_outside", "finite-grid"), ("official_text_nan_outside_twin", "template-mask")):
            entry = receipt[key]
            path = archive_member(archive, entry["file"], ".tif")
            zipped = archive_member(archive, entry["zip"], ".zip")
            if path.name in referenced or sha256_file(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
                raise ValueError("Repeated, changed, or receipt-inconsistent TIFF")
            referenced.add(path.name)
            with zipfile.ZipFile(zipped) as package:
                if package.namelist() != [path.name] or package.read(path.name) != path.read_bytes():
                    raise ValueError("ZIP must contain only the exact named TIFF")
            measured = audit(path, lattice, sample, labels)
            checked = validate(sample, path, profile, expected_dots=measured["candidate_dots"])
            # Record repository-relative paths instead of machine-specific absolute paths.
            checked["template"] = str(sample.relative_to(root))
            checked["candidate"] = str(path.relative_to(root))
            with rasterio.open(path) as src:
                dots = (src.read(1) > 0) & foot
                twins.append(dots)
            filtered_near = int((dots & filtered_halo).sum())
            version["files"].append({"file": str(path.relative_to(root)), "sha256": measured["candidate_sha256"],
                                     "zip": str(zipped.relative_to(root)), "zip_sha256": sha256_file(zipped),
                                     "zip_contains_exact_tiff_only": True,
                                     "lattice": measured,
                                     "catalogue_filtered_lattice_diagnostic": {
                                         "reference_dots": int(filtered.sum()),
                                         "candidate_dots_within_3px": filtered_near,
                                         "overlap_fraction": filtered_near / measured["candidate_dots"],
                                         "protocol_novelty_pass": False,
                                     },
                                     "validator": checked})
        if not np.array_equal(twins[0], twins[1]):
            raise ValueError("Claimed TIFF twins have different in-footprint dot masks")
        version["same_in_footprint_dot_mask"] = True
        results.append(version)
    if not results or referenced != {p.name for p in archive.glob("*.tif")}:
        raise ValueError("Archive inventory incomplete; do not omit TIFFs")
    hashes = {item["sha256"] for version in results for item in version["files"]}
    if card["raster_sha256"] not in hashes:
        raise ValueError("Current card's exact TIFF is not in the audited inventory")
    comparisons = [item for version in results for item in version["files"]]
    return {
        "schema_version": 1,
        "kind": "SAVED-BYTE GEOMETRIC AUDIT, NOT A MODEL RESULT OR SCORE",
        "scope": "Existing CADG archive only versus one required lattice, not a complete registry or surface audit.",
        "source_card": str(card_path.relative_to(root)), "source_card_sha256": sha256_file(card_path),
        "template_authenticated_by_organizer": False, "lattice_source": lattice_row,
        "versions": results,
        "all_files_exceed_70_percent": all(item["lattice"]["duplicate_over_70_percent"] for item in comparisons),
        "status": "STOP_DUPLICATE" if any(item["lattice"]["duplicate_over_70_percent"] for item in comparisons) else "BLOCKED_INCOMPLETE_REGISTRY",
        "surface_registry_comparison": None, "full_registry_compared": False,
        "range_error": "The rejected file was not supplied. Local profiles do not prove its cause or future portal acceptance.",
        "overlap_scope": "The full registered lattice determines the literal stop. The separately reported catalogue-filtered reference reproduces the narrower prior calculation and is diagnostic only.",
        "verdict": "negative", "slot_authorized": False, "candidate_generated": False, "geological_experiments_run": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="Restore the pinned lattice, not the core inputs")
    parser.add_argument("--output", type=Path, help="Optional receipt; failure overwrites a stale receipt")
    args = parser.parse_args()
    try:
        result = run(restore=args.restore)
        code = 1  # No one-reference forensic audit can authorize a submission.
    except Exception as exc:
        result = {"kind": "CADG ARCHIVE AUDIT FAILED", "status": "BLOCKED", "verdict": "negative",
                  "slot_authorized": False, "candidate_generated": False, "error": str(exc)}
        code = 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
