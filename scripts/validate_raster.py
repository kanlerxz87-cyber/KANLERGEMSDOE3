#!/usr/bin/env python3
"""Run the pinned shared on-disk format validator. This is NOT slot approval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from bootstrap import INPUTS, ensure_template


def check(path: Path, sample: Path) -> dict:
    template = ensure_template()
    sys.path.insert(0, str(template / "vendor"))
    from gems57.gates import format_report
    if not path.is_file() or not sample.is_file():
        raise FileNotFoundError("Both candidate and sample GeoTIFF must exist")
    with rasterio.open(sample) as src:
        if src.count != 1:
            raise ValueError("Reference must be a single-band sample")
        footprint = np.isfinite(src.read(1))
    if not footprint.any():
        raise ValueError("Reference has no finite footprint")
    report = format_report(path, sample, footprint=footprint)
    return {
        "kind": "local-format-only", "format_ok": report["ok"],
        "ok_to_submit": False,
        "reason": "Format cannot prove leakage safety, uniqueness, holdout efficacy, organizer acceptance, or slot approval.",
        "policy": "All stored values finite in [0,1], no positive mass outside footprint; stricter local policy, not a portal acceptance guarantee.",
        "reference": str(sample), "report": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raster", type=Path)
    parser.add_argument("--sample", type=Path, default=INPUTS / "sample_submission.tif")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = check(args.raster, args.sample)
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["format_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
