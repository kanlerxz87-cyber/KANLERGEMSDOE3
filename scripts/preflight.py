#!/usr/bin/env python3
"""Fail closed if the pinned registry witness makes literal uniqueness impossible."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from bootstrap import ROOT, INPUTS, ensure_template, sha256


def preflight() -> dict:
    records = {e["name"]: e for e in json.loads((ROOT / "data/audit_inputs.json").read_text())["files"]}
    for name in ("sample_submission.tif", "17gems_eproba.tif"):
        path, record = INPUTS / name, records[name]
        if not path.is_file() or path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise ValueError(f"Missing/changed pinned input {name}; uniqueness is UNKNOWN, not PASS")
    template = ensure_template()
    sys.path.insert(0, str(template / "vendor"))
    from gems57.uniqueness import saturation_certificate
    with rasterio.open(INPUTS / "sample_submission.tif") as src:
        footprint = np.isfinite(src.read(1))
        grid = (src.shape, src.crs, src.transform)
    certificate = saturation_certificate(INPUTS / "17gems_eproba.tif", footprint, expected_grid=grid)
    record = records["17gems_eproba.tif"]
    certificate["witness_file"] = record["name"]
    certificate["source"] = (f"https://github.com/buffedlizard55-lab/{record['repo']}/blob/"
                             f"{record['ref']}/{record['path']}")
    return {
        "schema": "preflight-v1", "reviewed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "One hash-pinned registered witness; this is not a complete registry audit.",
        "rule": "finite positive support, directed <=3 pixels; stop when overlap >0.70",
        "certificate": certificate,
        "stop_required": bool(certificate["universal_overlap_blocker"]),
        "reason": ("Every nonempty footprint support overlaps this witness; stop before placement."
                   if certificate["universal_overlap_blocker"] else
                   "This witness alone does not prove a block; full uniqueness is still unverified."),
        "candidate_created": False, "slot_spent": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="optional JSON receipt")
    args = parser.parse_args()
    result = preflight()
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    # A failed or absent witness can never authorize an experiment. Even if
    # this one witness stops blocking, other requirements remain unverified.
    # Exit 2 = proven blocked; 3 = this witness alone is inconclusive.
    return 2 if result["stop_required"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
