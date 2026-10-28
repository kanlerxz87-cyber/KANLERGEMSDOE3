#!/usr/bin/env python3
"""ARCHIVED AND CLI-BLOCKED: historical support-cache calculation.

Positive values in a soft field are not automatically dot locations. This
legacy cache cannot establish protocol uniqueness.

Pre-compute the duplicate-gate geometry of every restored registry raster.

For each raster in registry/registry_index.json:
  * support  = finite & > 0 pixels (the literal inherited definition of "dots"; shared
               gems57/uniqueness.py `_dots`)
  * buffer   = support dilated by the official 3-px (300 m) Euclidean disk
  * stats    = support size, footprint share covered by the buffer (space-filling flag),
               binary or soft, values outside [0,1], support outside the footprint.
Buffers are stored as packed bits in a memory-mapped file so that a candidate's dot overlap
against all rasters is a cheap lookup during design.  The final gate (scripts/uniqueness_gate.py)
re-reads the TIFFs and recomputes everything from scratch; this cache is only a design aid.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / "registry_cache"
SPACE_FILLING_SHARE = 0.50   # buffer covers >= 50% of the footprint -> overlap rule cannot discriminate


def disk(r: float = 3.0) -> np.ndarray:
    k = int(np.ceil(r))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    return (yy * yy + xx * xx) <= r * r


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    idx = json.loads((ROOT / "registry" / "registry_index.json").read_text())["rasters"]
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        sample = ds.read(1)
        tpl = (ds.shape, ds.crs, ds.transform)
    foot = np.isfinite(sample)
    H, W = foot.shape
    nbytes = (H * W + 7) // 8
    mm = np.lib.format.open_memmap(CACHE / "buffers_packed.npy", mode="w+", dtype=np.uint8,
                                   shape=(len(idx), nbytes))
    st = disk()
    rows = []
    t0 = time.time()
    for i, r in enumerate(idx):
        p = DATA / "registry" / f"{r['sha256']}.tif"
        rec = {"i": i, "sha256": r["sha256"], "repo": r["repo"], "path": r["path"],
               "sources": r["sources"]}
        try:
            with rasterio.open(p) as ds:
                rec["grid_ok"] = (ds.shape, ds.crs, ds.transform) == tpl
                rec["dtype"] = ds.dtypes[0]
                rec["nodata"] = None if ds.nodata is None else float(ds.nodata)
                a = ds.read(1).astype(np.float32)
        except Exception as exc:  # reported, never silently dropped
            rec["error"] = f"{type(exc).__name__}: {exc}"
            rows.append(rec)
            continue
        if not rec["grid_ok"]:
            rec["error"] = "grid mismatch"
            rows.append(rec)
            continue
        fin = np.isfinite(a)
        sup = fin & (a > 0)
        inside = a[foot & fin]
        rec.update(
            n_support=int(sup.sum()),
            n_support_in_footprint=int((sup & foot).sum()),
            n_support_outside_footprint=int((sup & ~foot).sum()),
            n_nan_in_footprint=int((foot & ~fin).sum()),
            min_in_footprint=float(inside.min()) if inside.size else None,
            max_in_footprint=float(inside.max()) if inside.size else None,
            n_out_of_range_in_footprint=int(((inside < 0) | (inside > 1)).sum()),
            binary=bool(np.isin(a[sup], [1.0]).all()) if sup.any() else True,
        )
        buf = binary_dilation(sup, structure=st)
        share = float(buf[foot].mean())
        rec["buffer_share_of_footprint"] = share
        rec["space_filling"] = share >= SPACE_FILLING_SHARE
        mm[i] = np.packbits(buf.ravel())
        rows.append(rec)
        if i % 25 == 0:
            print(f"{i}/{len(idx)} {time.time() - t0:.0f}s", flush=True)
    mm.flush()
    out = {"schema_version": 1, "n": len(rows), "space_filling_share": SPACE_FILLING_SHARE,
           "shape": [H, W], "rows": rows}
    (CACHE / "registry_stats.json").write_text(json.dumps(out, indent=1) + "\n")
    print("done", time.time() - t0, "s;", sum(1 for r in rows if r.get("space_filling")), "space-filling;",
          sum(1 for r in rows if "error" in r), "errors")
    return 0


if __name__ == "__main__":
    from archive_guard import stop_archived_cli
    stop_archived_cli()
    sys.exit(main())
