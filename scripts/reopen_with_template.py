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
    args = ap.parse_args()
    sys.path.insert(0, str(args.template_root / "src"))
    from gems32.submission import audit_geotiff  # noqa: E402
    with rasterio.open(args.sample) as ds:
        sample = ds.read(1, masked=True)
        foot = ~np.ma.getmaskarray(sample) & np.isfinite(sample.data)
        ref = (ds.shape, ds.crs, ds.transform)
    with rasterio.open(args.labels) as ds:
        if (ds.shape, ds.crs, ds.transform) != ref:
            raise ValueError("label grid does not match the sample")
        label_values = ds.read(1, masked=True)
        labels = (~np.ma.getmaskarray(label_values)) & (label_values.data > 0) & foot
    # The written organizer specification calls for NaN/null outside the footprint.
    report = audit_geotiff(args.candidate, foot, labels, mode="nan", template_tif=args.sample)
    print(json.dumps(report, allow_nan=False))


if __name__ == "__main__":
    main()
