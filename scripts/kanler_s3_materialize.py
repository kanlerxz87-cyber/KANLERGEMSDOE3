#!/usr/bin/env python3
"""Write the pre-registered KS3-strain field as a submission GeoTIFF via the vendored writer.

Uses vendor/shared-template/src/gems32/submission.py::write_submission_pair (lock-verified), so the
GeoTIFF profile, footprint masking, [0,1] clipping and 12-point audit are the template's own.
The writer hard-codes a "gemsdoe32-" file prefix; only the file NAME is changed afterwards
(bytes are untouched and their SHA-256 is recorded). The zeros variant is the one published.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shared_tools  # noqa: E402

FIELDS = ROOT / ".cache/kanler_s3_fields.npz"
DATA = ROOT / "data"
OUT_DIR = ROOT / "docs/submission/quarantine"  # not linked as a download: fails uniqueness (see verdict)
RECEIPT = ROOT / "evidence/kanler-s3-materialize-20261029.json"
SLUG = "ks3-strain"
TIMESTAMP = "20261029T000000Z"
FINAL_NAME = "kanlergemsdoe3-ks3-strain-37654-20261029-zeros.tif"
NOTE = ("KANLER-S3 strain prior, 37,654 dots, 2px catalogue exclusion. NOT unique (two-way 3px "
        "test vs GEMSDOE69). Do not submit.")


def main() -> None:
    assert len(NOTE) <= 140, f"note is {len(NOTE)} chars"
    lock = shared_tools.verify_template()
    if not lock["ok"]:
        raise SystemExit("template lock failed: " + "; ".join(lock["failures"]))
    sys.path.insert(0, str(shared_tools.TEMPLATE / "src"))
    from gems32.submission import write_submission_pair, audit_geotiff  # vendored, unmodified

    with rasterio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(DATA / "labels.tif") as ds:
        labels = ds.read(1) > 0
    mask = np.load(FIELDS)["KS3_strain"]

    meta = {
        "candidate_id": "KS3-strain",
        "description": "Pre-registered geod_shearrate prior; greedy 4px suppression; 2px catalogue exclusion.",
        "submission_note_zeros": NOTE,
        "submission_note_nan": NOTE,
        "catalogue_hidden_mean": "HOLDOUT-DTI 0.0522 per-cell leak-free (E2, 400 boot), see evidence/kanler-s3-e2-candidates-20261029.json",
        "catalogue_hidden_per_quadrant": "not computed",
        "sgmc_prevalence_calibrated_dti": "0.0540 SGMC-CAL proxy (95% CI 0.0318-0.0759)",
        "drift_corrected_holdout_mean": "NOT COMPUTED",
        "drift_corrected_per_quadrant": "NOT COMPUTED",
        "predicted_leaderboard_dti": "NOT ESTIMATED (no organizer receipt; proxies are not scores)",
        "ei_drift_corrected": "NOT COMPUTED",
        "slot_decision": "NOT AUTHORIZED",
    }
    with tempfile.TemporaryDirectory() as tmp:
        bundle = write_submission_pair(mask, foot, labels, DATA / "sample_submission.tif",
                                       Path(tmp), SLUG, TIMESTAMP, meta)
        zeros_src = Path(tmp) / bundle["zeros_tif"]["filename"]
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        dst = OUT_DIR / FINAL_NAME
        shutil.copyfile(zeros_src, dst)
    digest = hashlib.sha256(dst.read_bytes()).hexdigest()
    if digest != bundle["zeros_tif"]["sha256"]:
        raise SystemExit("byte mismatch after rename")
    # Re-audit the published bytes with the vendored 12-point validator (not the in-memory copy).
    re_audit = audit_geotiff(dst, foot, labels, mode="zeros", template_tif=DATA / "sample_submission.tif")
    receipt = {
        "kind": "CANDIDATE WRITE RECEIPT (vendored writer; file renamed only)",
        "published_file": str((OUT_DIR / FINAL_NAME).relative_to(ROOT)),
        "sha256": digest,
        "bytes": dst.stat().st_size,
        "writer_original_name": bundle["zeros_tif"]["filename"],
        "writer_digest8": bundle["content_digest8"],
        "note": NOTE,
        "note_chars": len(NOTE),
        "validator": {k: re_audit[k] for k in ("crs", "transform", "shape", "dtype", "nodata", "emitted_positive_pixels",
                                              "in_footprint_min", "in_footprint_max", "full_grid_finite_pixels",
                                              "on_catalogue_positive_pixels", "all_checks_passed")},
        "checks": re_audit["checks"],
        "template_lock_commit": lock["commit"],
        "slot_authorized": False,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("published_file", "sha256", "bytes", "note_chars")}, indent=1))
    print(json.dumps(receipt["validator"], indent=1))


if __name__ == "__main__":
    main()
