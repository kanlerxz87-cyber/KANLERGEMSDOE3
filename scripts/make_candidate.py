#!/usr/bin/env python3
"""Write the dot-candidate GeoTIFF from the saved final probability surface.

Reuses the experiment's dot selector (scripts/run_offcat_hgb.select_dots) so the
written dots are exactly the ones selected by the shared procedure. Output is
single-band float32 on the template grid, values exactly 0 or 1, and finite
everywhere (zeros outside the footprint) so the [0,1] range holds for the whole
grid. The validator in scripts/validate_submission.py checks the saved bytes.

Usage: python scripts/make_candidate.py --name <file-stem> --note "<=140 chars>"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_offcat_hgb as E  # noqa: E402  (shared selector; same code as the experiment)

DOWNLOADS = ROOT / "docs" / "downloads-candidate"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--surface", type=Path, default=E.DATA / "candidates" / "P_final.npy")
    ap.add_argument("--stem", required=True)
    ap.add_argument("--note", required=True)
    ap.add_argument("--out-dir", type=Path, default=DOWNLOADS)
    ap.add_argument("--dots-out", type=Path, default=E.DATA / "candidates" / "dots_final.npy")
    args = ap.parse_args()
    if len(args.note) > 140:
        raise SystemExit("note must be at most 140 characters")

    footprint, _pos, meta = E.load_grid()
    with rasterio.open(E.DATA / "sample_submission.tif") as t:
        crs, transform = t.crs, t.transform
    P = np.load(args.surface)
    if P.shape != footprint.shape:
        raise SystemExit("surface grid mismatch")
    dots, n = E.select_dots(P, footprint, E.BUDGET, excl=None)
    np.save(args.dots_out, np.argwhere(dots > 0).astype(np.int32))
    out = np.where(footprint, dots, 0.0).astype(np.float32)
    assert out.min() >= 0.0 and out.max() <= 1.0 and np.isfinite(out).all()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tmp = (args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir) / f"{args.stem}-zeros.tif"
    profile = dict(driver="GTiff", height=out.shape[0], width=out.shape[1], count=1, dtype="float32",
                   crs=crs, transform=transform, nodata=None, compress="deflate", tiled=False)
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(out, 1)
        dst.update_tags(
            description="Binary dot prediction (1 = dot, 0 = not), finite everywhere; unofficial candidate",
            note=args.note,
        )
    digest = sha256(tmp)
    info = {
        "file": str(tmp.resolve().relative_to(ROOT)),
        "sha256": digest,
        "bytes": tmp.stat().st_size,
        "dots_placed": int(n),
        "budget": E.BUDGET,
        "footprint_px": int(footprint.sum()),
        "positive_px": int((out > 0).sum()),
        "crs": str(crs),
        "transform": list(transform),
        "shape": list(out.shape),
        "note": args.note,
        "note_chars": len(args.note),
    }
    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
