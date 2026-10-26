#!/usr/bin/env python3
"""Shared strict GeoTIFF writer for KANLERGEMSDOE3.

Numerical GeoTIFF writing, ZIP packaging, content hashing, and multi-variant
saved-byte format validation delegate directly to the SHA-256-pinned shared
template ``vendor/gems24_template/submission.py`` (no local numerical edits).

Emits both:
- ``-zeros.tif`` + ``.zip`` (primary portal-safe deliverable: ``nodata=None``,
  outside-footprint cells set to ``0.0``, so ``((arr >= 0) & (arr <= 1)).all()``
  is True over all 12,279,160 cells — eliminating DrivenData's portal error
  ``"Predicted values must be in range [0, 1]"`` per IR-34-NODATA-01), and
- ``-nan.tif`` + ``.zip`` (literal DrivenData page-967 twin: ``nodata=NaN``,
  outside-footprint cells set to ``NaN`` matching ``sample_submission.tif``).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vendor.gems24_template import submission  # noqa: E402

MAX_NOTE_CHARS = 140


def write_pair(
    prediction: np.ndarray,
    *,
    template: Path,
    catalogue: np.ndarray,
    footprint: np.ndarray,
    outdir: Path,
    family: str = "kanlergemsdoe3",
    hypothesis: str,
    date: str = "20261026",
    note_template: str,
    scientific_verdict: str,
) -> dict:
    values = np.asarray(prediction, dtype=np.float32)
    footprint = np.asarray(footprint, dtype=bool)
    catalogue = np.asarray(catalogue, dtype=bool)
    if values.shape != footprint.shape or catalogue.shape != footprint.shape:
        raise ValueError("Prediction/catalogue/footprint grids must match")
    if not np.isfinite(values[footprint]).all() or np.any(
        (values[footprint] < 0.0) | (values[footprint] > 1.0)
    ):
        raise ValueError("Predictions must be finite in [0, 1] inside the footprint")
    content_id = submission.scored_content_id(values, footprint, catalogue)
    note = note_template.replace("{cid}", content_id)
    if not (0 < len(note) <= MAX_NOTE_CHARS):
        raise ValueError(f"Note has {len(note)} characters; must be in 1..{MAX_NOTE_CHARS}")
    zero_name = submission.make_filename(family, hypothesis, date, content_id, "zeros")
    nan_name = submission.make_filename(family, hypothesis, date, content_id, "nan")
    outdir.mkdir(parents=True, exist_ok=True)
    zero_path = submission.write_submission(values, template, outdir / zero_name, outside="zero")
    nan_path = submission.write_submission(values, template, outdir / nan_name, outside="nan")
    zero_zip = submission.zip_single(zero_path)
    nan_zip = submission.zip_single(nan_path)
    zero_check = submission.check_variants(zero_path, template)
    nan_check = submission.check_variants(nan_path, template)
    if not zero_check["format_valid"] or not nan_check["format_valid"]:
        raise RuntimeError(
            f"Saved-byte format validation failed: zero={zero_check['hard_failures']} nan={nan_check['hard_failures']}"
        )
    if not zero_check["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]:
        raise RuntimeError("Primary -zeros.tif failed strict whole-array [0, 1] check")
    if not nan_check["official_format_compliant"]:
        raise RuntimeError("Twin -nan.tif failed literal NaN-outside check")
    stem = zero_path.stem.removesuffix("-zeros")
    note_path = outdir / f"note-{stem}.txt"
    note_path.write_text(note + "\n")
    receipt = {
        "schema": 1,
        "writer_source": "vendor/gems24_template/submission.py",
        "writer_source_manifest": "vendor/gems24_template/SOURCE.json",
        "submission_name": zero_path.stem,
        "content_id": content_id,
        "note": note,
        "note_characters": len(note),
        "scientific_verdict": scientific_verdict,
        "format_valid": True,
        "format_validation_is_not_portal_acceptance": True,
        "weekly_slot_authorized": False,
        "primary_zero_outside": {
            "file": zero_path.name,
            "zip": zero_zip.name,
            "sha256": zero_check["sha256"],
            "bytes": zero_check["bytes"],
            "validator": zero_check,
        },
        "official_text_nan_outside_twin": {
            "file": nan_path.name,
            "zip": nan_zip.name,
            "sha256": nan_check["sha256"],
            "bytes": nan_check["bytes"],
            "validator": nan_check,
        },
        "note_file": note_path.name,
    }
    receipt_path = outdir / f"receipt-{stem}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    receipt["receipt_file"] = receipt_path.name
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction", type=Path, required=True, help="Aligned 2D .npy values")
    parser.add_argument("--template", type=Path, default=ROOT / ".cache/gems_data/sample_submission.tif")
    parser.add_argument("--labels", type=Path, default=ROOT / ".cache/gems_data/labels.tif")
    parser.add_argument("--outdir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--family", default="kanlergemsdoe3")
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--date", default="20261026")
    parser.add_argument("--note", required=True)
    parser.add_argument("--verdict", choices=("promote", "negative"), required=True)
    args = parser.parse_args()
    import rasterio

    values = np.load(args.prediction, allow_pickle=False)
    with rasterio.open(args.template) as source:
        footprint = np.isfinite(source.read(1))
    with rasterio.open(args.labels) as source:
        catalogue = (source.read(1) > 0) & footprint
    receipt = write_pair(
        values,
        template=args.template,
        catalogue=catalogue,
        footprint=footprint,
        outdir=args.outdir,
        family=args.family,
        hypothesis=args.hypothesis,
        date=args.date,
        note_template=args.note,
        scientific_verdict=args.verdict,
    )
    print(json.dumps(receipt, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
