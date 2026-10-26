#!/usr/bin/env python3
"""Package the E3 candidate with the SHARED writer (vendor/gems57/submission_writer.py, unchanged).

The writer validates in memory, writes to temporary paths, re-validates the on-disk TIFF and ZIP with the
shared validator, and only then atomically publishes <name>.tif / .zip / .json in docs/downloads/.
Format policy (shared): float32, single band, EPSG:32611, sample transform, ALL pixels finite, values in
{0,1}, zeros outside the footprint, no nodata tag, zero dots on mapped catalogue pixels.
"""
from __future__ import annotations

import hashlib
import json
import time
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
from gems57.submission_writer import write_submission  # noqa: E402
from kgems import common as C  # noqa: E402

STAMP = time.strftime("%Y%m%dT%H%MZ", time.gmtime())  # real generation time (UTC)


def main() -> int:
    foot, cat = C.footprint(), C.catalogue()
    flat = np.load(ROOT / "data" / "work" / "e3_live_dots.npy").astype(np.int64)
    pred = np.zeros(foot.size, np.float32)
    pred[flat] = 1.0
    pred = pred.reshape(foot.shape)
    assert not (pred.astype(bool) & ~foot).any() and not (pred.astype(bool) & cat).any()
    tag = hashlib.sha256(np.packbits(pred.astype(bool).ravel()).tobytes()).hexdigest()[:8]
    n = int(pred.sum())
    stem = f"kanler3-k3h1-asgt-hybrid-{n}-{STAMP}-{tag}-zeros"
    name = f"kanler3-k3h1-asgt-hybrid-{n}-{tag}"
    note = "K3-H1 antislope-scarp lidar dots + ASGT-ranked H19-5 core; unique<=69.5%; PROJECTION 0.252, not >0.2778"
    assert len(name) <= 140 and len(note) <= 140, (len(name), len(note))
    out = ROOT / "docs" / "downloads" / f"{stem}.tif"
    receipt = write_submission(out, pred, ROOT / "data" / "sample_submission.tif", foot, note=note, name=name,
                               catalogue=cat, metadata={"lane": "K3-H1 ASGT hybrid (E3)",
                                                        "dots_packbits_sha256_8": tag})
    print(json.dumps({k: receipt[k] for k in ("file", "sha256", "bytes", "submission_name", "note", "note_chars",
                                              "zip_file", "zip_sha256")}, indent=1))
    print("validator all_checks_passed:", receipt["validator"]["all_checks_passed"])
    return 0


if __name__ == "__main__":
    from archive_guard import stop_archived_cli
    stop_archived_cli()
    sys.exit(main())
