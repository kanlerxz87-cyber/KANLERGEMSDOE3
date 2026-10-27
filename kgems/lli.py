"""Live-Ledger Inversion projections with the shared GEMSDOE32 instrument (vendor/gems32lli, unchanged).

The S3 strata are rebuilt exactly as in vendor/gems32lli/run_live_ledger_inversion_reference.py and the
archived S3 fit (registry/live_ledger_inversion_gemsdoe32.json) is reused, so no private refit is involved.
`verify_against_archive` checks that rebuilt strata reproduce the archived fitted values of scored rasters.
Every output for an unscored raster is a PROJECTION (LOO MAE 0.0219, q90 |err| 0.054), never a score.
"""
from __future__ import annotations

import json
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt

from . import ROOT
from . import common as C

sys.path.insert(0, str(ROOT / "vendor"))
from gems32lli import ledger_inversion as li  # noqa: E402

ARCHIVE = ROOT / "registry" / "live_ledger_inversion_gemsdoe32.json"


def _digitize(d, edges, codes):
    return np.asarray(codes, np.int8)[np.digitize(d, edges, right=True)]


def build_spec_s3() -> "li.StrataSpec":
    foot = C.footprint()
    cat = C.catalogue()
    active = foot & ~cat
    d_cat = distance_transform_edt(~cat)
    cat_lv = _digitize(d_cat, [2.01, 3.01, 5.01, 10.01, 30.01], [1, 2, 3, 4, 5, 0])
    del d_cat
    h = C.read_support(C.registry_path(C.H19_5_SHA)) & foot
    d_h = distance_transform_edt(~h)
    h_lv = _digitize(d_h, [0.01, 1.01, 2.01, 3.01, 4.01, 5.01, 8.01, 15.01], [1, 2, 3, 4, 5, 6, 7, 8, 0])
    del d_h
    for lv in (cat_lv, h_lv):
        lv[~active] = 0
    return li.StrataSpec(names=["d_catalogue_px", "d_H19-5_px"], levels=[cat_lv, h_lv], n_levels=[6, 9],
                         level_labels=[[">30", "1-2", "2.2-3", "3.2-5", "5-10", "10-30"],
                                       [">15", "on", "1", "1.4-2", "2.2-3", "3.2-4", "4.1-5", "5-8", "8-15"]],
                         active=active)


def archived_lambda(spec) -> np.ndarray:
    arch = json.loads(ARCHIVE.read_text())["designs"]["S3"]
    theta = np.asarray(arch["fit"]["theta"], float)
    return li.strata_lambda(theta, spec)


def archive_meta() -> dict:
    arch = json.loads(ARCHIVE.read_text())["designs"]["S3"]
    return {"design": "S3", "n_unique_rasters": arch["n_unique_rasters"], "loo": arch["loo"],
            "leave_site_out": arch["leave_site_out"],
            "g_public_truth_pixels": arch["fit"]["g_public_truth_pixels_full_footprint_scale"],
            "source": "buffedlizard55-lab/GEMSDOE32 evidence/live_ledger_inversion.json (archived fit, reused unchanged)"}


def project(pred: np.ndarray, spec, lam) -> dict:
    row = li.design_row(np.asarray(pred, np.float32), spec)
    out = li.project(row, spec, lam)
    out["dots"] = row["dots"]
    return out
