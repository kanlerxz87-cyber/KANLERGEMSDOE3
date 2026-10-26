#!/usr/bin/env python3
"""Independently re-measure the 9 focus champions: dot counts, catalogue-distance
bands, and the d2.8 -> solo -> B2 -> Anderson subset chain. Learning only."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]

def load(p: Path, foot):
    with rasterio.open(p) as s:
        a = s.read(1)
    return foot & np.isfinite(a) & (a > 0)

def main() -> int:
    reg = json.loads((ROOT / "registry" / "focus9_champions.json").read_text())
    with rasterio.open(ROOT / "data" / "raw" / "labels.tif") as s:
        lab = s.read(1) == 1
    with rasterio.open(ROOT / "data" / "raw" / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    dcat = distance_transform_edt(~lab)
    masks, rows = {}, {}
    for e in reg["entries"]:
        p = ROOT / ".cache" / "registry" / f"{e['site']}__{Path(e['path']).name}"
        m = load(p, foot)
        masks[e["site"]] = m
        d = dcat[m]
        rows[e["site"]] = {"name": e["name"], "score_owner_reported": e["score_owner_reported"],
                           "dots": int(m.sum()), "dcat_le1": int((d <= 1).sum()),
                           "dcat_1to2": int(((d > 1) & (d <= 2)).sum()), "dcat_2to3": int(((d > 2) & (d <= 3)).sum()),
                           "dcat_median_px": float(np.median(d)) if len(d) else None}
    chain = {
        "d28_minus_solo31": int((masks["GEMSDOE25"] & ~masks["GEMSDOE31"]).sum()),
        "solo31_minus_d28": int((masks["GEMSDOE31"] & ~masks["GEMSDOE25"]).sum()),
        "removed_B0toB1_max_dcat_px": float(dcat[masks["GEMSDOE25"] & ~masks["GEMSDOE31"]].max()),
        "solo31_minus_b2_32": int((masks["GEMSDOE31"] & ~masks["GEMSDOE32"]).sum()),
        "b2_32_minus_solo31": int((masks["GEMSDOE32"] & ~masks["GEMSDOE31"]).sum()),
        "removed_B1toB2_max_dcat_px": float(dcat[masks["GEMSDOE31"] & ~masks["GEMSDOE32"]].max()),
        "anderson36_minus_b2_32": int((masks["GEMSDOE36"] & ~masks["GEMSDOE32"]).sum()),
        "b2_32_minus_anderson36": int((masks["GEMSDOE32"] & ~masks["GEMSDOE36"]).sum()),
    }
    out = {"label": "MEASURED in KANLERGEMSDOE3 from SHA-256-verified champion bytes; scores OWNER-REPORTED",
           "sites": rows, "subset_chain": chain}
    (ROOT / "evidence" / "forensics_focus9.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
