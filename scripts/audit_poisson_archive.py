#!/usr/bin/env python3
"""Recheck a parallel session's saved random-control TIFFs; never fit or write one.

This is a scoped geometric/format audit against one registered lattice and an
unauthenticated mirror, not a full registry audit, holdout or submission.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from scripts.audit_parallel_candidate import audit  # noqa: E402
from scripts.github_source import GitHubSource, sha256_file  # noqa: E402
from scripts.validate_submission import validate  # noqa: E402


def run(restore: bool = False) -> dict:
    card_path = ROOT / "evidence/candidate_poisson_20261027.json"
    card = json.loads(card_path.read_text())
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False or card.get("slot_authorized") is not False:
        raise ValueError("The parallel card must remain negative")
    lattice_record = next(r for r in json.loads((ROOT / "research/registry-lock.json").read_text())["entries"] if r["id"] == "registry-160")
    core = {r["id"]: r for r in json.loads((ROOT / "data/core-manifest.json").read_text())["files"]}
    lattice = ROOT / "data/registry-review/lattice.tif"
    sample = ROOT / "data/core" / core["sample_submission"]["dest"]
    labels = ROOT / "data/core" / core["labels"]["dest"]
    if restore:
        GitHubSource().restore(lattice_record["repo"], lattice_record["ref"], lattice_record["file"], lattice, lattice_record["sha256"])
    for name, path, digest in (("lattice", lattice, lattice_record["sha256"]), ("sample", sample, core["sample_submission"]["sha256"]), ("labels", labels, core["labels"]["sha256"])):
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"Missing or altered {name}; restore pinned inputs before the audit")
    files, measured, masks = {}, {}, []
    with rasterio.open(sample) as src:
        foot = (src.dataset_mask() > 0) & np.isfinite(src.read(1))
    for encoding, profile in (("zeros", "finite-grid"), ("nan", "template-mask")):
        name = card["download"][f"{encoding}_tif"]
        path = (ROOT / "docs" / name).resolve()
        if not path.is_relative_to((ROOT / "docs/candidate_downloads").resolve()) or not path.is_file() or sha256_file(path) != card["raster_sha256"][encoding]:
            raise ValueError(f"Parallel {encoding} TIFF is missing, altered, or outside the archive")
        measurement = audit(path, lattice, sample, labels)
        validator = validate(sample, path, profile, expected_dots=37654)
        validator["template"] = str(sample.relative_to(ROOT))
        validator["candidate"] = str(path.relative_to(ROOT))
        with rasterio.open(path) as src:
            masks.append((src.read(1) > 0) & foot)
        zip_path = path.with_suffix(".zip")
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            zip_ok = names == [path.name] and z.read(names[0]) == path.read_bytes()
        files[encoding] = {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path),
                           "zip": str(zip_path.relative_to(ROOT)), "zip_sha256": sha256_file(zip_path),
                           "zip_contains_exact_tiff_only": zip_ok, "profile": profile}
        measured[encoding] = {"lattice": measurement, "validator": validator}
    if not np.array_equal(*masks) or not all(row["zip_contains_exact_tiff_only"] for row in files.values()):
        raise ValueError("TIFF twins or ZIP content differ; do not publish a simplified comparison")
    return {
        "kind": "PARALLEL RESEARCH RASTER FORENSIC AUDIT; not a model or organizer score",
        "source_card": str(card_path.relative_to(ROOT)), "source_card_sha256": sha256_file(card_path),
        "files": files, "same_in_footprint_dot_mask": True,
        "measurements": measured, "lattice_source": lattice_record,
        "surface_registry_comparison": None, "full_registry_compared": False,
        "historical_nine_site_claim": "Prior card lists only a subset of per-site measurements; it is insufficient to establish all-nine uniqueness.",
        "range_error_claim": "The rejected upload was not supplied; these local profiles do not establish that its error was fixed or that the portal will accept either encoding.",
        "interpretation": "The prior session's random control is research-only. Both encodings fail the required literal lattice stop. Neither has an independently run holdout or an authorized weekly slot.",
        "verdict": "negative", "slot_authorized": False, "candidate_generated": False, "geological_experiments_run": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="Restore the pinned lattice, not core data")
    parser.add_argument("--output", type=Path, help="Optional receipt; failure overwrites a stale receipt")
    args = parser.parse_args()
    try:
        result = run(args.restore)
        code = 1
    except Exception as exc:
        result = {"kind": "PARALLEL RASTER AUDIT FAILED", "verdict": "negative", "slot_authorized": False, "error": str(exc)}
        code = 2
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
