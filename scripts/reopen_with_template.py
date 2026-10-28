#!/usr/bin/env python3
"""Call the pinned shared template's TIFF auditor on exact saved bytes.

No writer or evaluator is copied here. The shared auditor is the authoritative
local validator used by this wrapper, not proof of organizer acceptance.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template-root", required=True, type=Path)
    ap.add_argument("--sample", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--mode", choices=("nan", "zeros"), default="nan",
                    help="Choose the pinned shared auditor's existing encoding mode; not portal approval")
    args = ap.parse_args()
    sys.path.insert(0, str(args.template_root / "src"))
    from gems32.submission import audit_geotiff  # noqa: E402

    def require_standalone(ds, path):
        if any(Path(name).resolve() != path.resolve() for name in ds.files):
            raise ValueError(f"Unhashed raster sidecar: {path}")
        if ds.count != 1:
            raise ValueError(f"Single-band raster required: {path}")
    with rasterio.open(args.sample) as ds:
        require_standalone(ds, args.sample)
        sample = ds.read(1, masked=True)
        foot = ~np.ma.getmaskarray(sample) & np.isfinite(sample.data)
        ref = (ds.shape, ds.crs, ds.transform)
    with rasterio.open(args.labels) as ds:
        require_standalone(ds, args.labels)
        if (ds.shape, ds.crs, ds.transform) != ref:
            raise ValueError("label grid does not match the sample")
        label_values = ds.read(1, masked=True)
        if (np.ma.getmaskarray(label_values)[foot].any()
                or not np.isfinite(label_values.data[foot]).all()
                or not np.isin(label_values.data[foot], (0, 1)).all()):
            raise ValueError("Finite binary labels are required throughout the footprint")
        labels = (label_values.data > 0) & foot
    with rasterio.open(args.candidate) as ds:
        require_standalone(ds, args.candidate)
    # The organizer specifies null/NaN outside. A shared `zeros` audit checks
    # raw bytes only; callers must additionally validate an internal mask if
    # they use that mode to represent null outside the footprint.
    report = audit_geotiff(args.candidate, foot, labels, mode=args.mode, template_tif=args.sample)
    print(json.dumps(report, allow_nan=False))


if __name__ == "__main__":
    main()
