#!/usr/bin/env python3
"""Audit restored competition rasters and write data/prepared_manifest.json.

Verifies EPSG:32611, 3730x3292 shape, 100 m transform, footprint/label counts
against the pinned manifest in data/prepared_manifest.json format used by the
shared template lanes. No file is modified.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
BASE_NAMES = ["mag_anom","rtp","tmi_hg","geod_2ndinv","iso_grav_anom_slope","tc","geod_shearrate",
"geod_dilaterate","tmi_vg","deq_n100a15","iso_grav_anom_vg","det_elev","iso_grav_anom","tmi",
"depth_to_base_surf","ieq_n100a15","cond_surf","iso_grav_anom_hg","det_elev_slope"]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def main() -> int:
    d = ROOT / "data" / "raw"
    for n in ("training_features.tif", "labels.tif", "sample_submission.tif"):
        if not (d / n).exists():
            raise SystemExit(f"Missing {d/n}; run: .venv/bin/python scripts/restore_data.py --group core")
    with rasterio.open(d / "sample_submission.tif") as s:
        assert s.crs.to_epsg() == 32611 and s.shape == (3730, 3292)
        assert tuple(float(v) for v in s.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        foot = np.isfinite(s.read(1))
    with rasterio.open(d / "labels.tif") as s:
        lab = s.read(1)
    assert np.array_equal(foot, lab >= 0), "footprint != labels>=0"
    bands = []
    with rasterio.open(d / "training_features.tif") as s:
        names = [desc.split(" - ")[0] if desc else "" for desc in s.descriptions]
        assert names == BASE_NAMES, f"Band order mismatch: {names}"
        for i, name in enumerate(names, 1):
            a = s.read(i)
            sent = (~np.isfinite(a)) | (a < -1e38)
            v = a[foot & ~sent]
            bands.append({"index": i, "name": name, "sentinel_in_footprint": int((sent & foot).sum()),
                          "min": float(v.min()), "median": float(np.median(v)), "max": float(v.max())})
    manifest = {
        "schema_version": 1, "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "grid": {"epsg": 32611, "height": 3730, "width": 3292, "total_cells": 3730*3292,
                 "transform": [100.0,0.0,243350.0,0.0,-100.0,4508550.0], "pixel_size_m": [100.0,100.0]},
        "counts": {"footprint_valid_pixels": int(foot.sum()), "outside_footprint_pixels": int((~foot).sum()),
                   "positive_catalogue_label_pixels": int(((lab == 1) & foot).sum())},
        "source_hashes": {n: sha256_file(d / n) for n in ("training_features.tif","labels.tif","sample_submission.tif")},
        "bands": bands,
        "provenance": "Owner-supplied GitHub mirrors, SHA-256 pinned in registry/data_manifest.json; NOT organizer-authenticated.",
    }
    expected = {"training_features.tif":"4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
                "labels.tif":"7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
                "sample_submission.tif":"2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"}
    for k, v in expected.items():
        assert manifest["source_hashes"][k] == v, f"Hash mismatch {k}"
    assert manifest["counts"] == {"footprint_valid_pixels":5167373,"outside_footprint_pixels":7111787,"positive_catalogue_label_pixels":60988}
    (ROOT / "data" / "prepared_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["counts"], indent=2)); print("Wrote data/prepared_manifest.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
