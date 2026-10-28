#!/usr/bin/env python3
"""Catalogue-blind dot candidates E1-E3 (pre-registered), final-file validation, uniqueness, evidence.

Pre-registration: research/catalogue-blind-prereg-20261028.md (written before any candidate was
scored on the SGMC or hide-and-recover holdouts). Everything here calls the shared, source-locked
evaluator (vendor/shared-template via scripts/shared_tools.load_tool) and the repo's exact
full-footprint geometry audit (scripts/check_uniqueness.compare). No evaluator fork.

Selection is LABEL-FREE: the ranking uses only the 35-channel template feature stack, so the
hide-and-recover evaluator (which masks visible catalogue itself) sees no hidden-fault information.
The only catalogue step is the shared writer's removal of catalogue pixels from the FINAL file,
which is a post-selection step, the same rule the 12-point audit applies.

Outputs: .cache/experiments (scratch), docs/downloads (final TIFF only if --publish),
evidence/catalogue-blind-*.json (receipts). Exit 0 always; the verdict field carries the decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.shared_tools import load_tool  # noqa: E402

BUDGET = 37_654  # participant convention observed in GEMSDOE32/36 outputs; not an organizer rule
SEED = 20261028
NOTE_MAX = 140
REGISTRY = ROOT / "registry" / "uniqueness_registry_20261026.json"
RESTORE_LOG = ROOT / ".cache" / "registry_rasters"
TEMPLATE = ROOT / "data" / "core" / "sample_submission.tif"
LABELS = ROOT / "data" / "core" / "labels.tif"
SGMC = ROOT / "data" / "core" / "external" / "derived_sgmc_faults_100m_u8.tif"
STACK = ROOT / ".cache" / "gems_work" / "feature_stack_35ch.npy"
STACK_RECEIPT = ROOT / ".cache" / "gems_work" / "feature_stack_receipt.json"
# A reference whose dots already cover >= 70% of the footprint within 3 px makes the literal test
# trip for ANY dot field (see evidence/catalogue-blind-saturation-20261028.json). Such a flag is
# reported as an unresolved rule defect, never silently waived and never counted as a clean pass.
INCUMBENT_BEST = {"hide_recover": 0.0967, "sgmc_raw": 0.1024}  # GEMSDOE25/30 and GEMSDOE27, same evaluator


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def nms_select(score: np.ndarray, foot: np.ndarray, n_target: int, min_sep: int = 3) -> np.ndarray:
    """Greedy highest-first; accept a pixel only if no accepted dot is within Chebyshev distance < min_sep."""
    H, W = foot.shape
    s = np.where(foot, score, -np.inf).ravel()
    order = np.argsort(-s, kind="stable")
    order = order[np.isfinite(s[order])]
    taken = np.zeros((H, W), bool)
    out = np.zeros(H * W, bool)
    cnt = 0
    for idx in order:
        y, x = divmod(int(idx), W)
        if taken[y, x]:
            continue
        out[idx] = True
        cnt += 1
        taken[max(0, y - min_sep + 1): y + min_sep, max(0, x - min_sep + 1): x + min_sep] = True
        if cnt >= n_target:
            break
    return out.reshape(H, W)


def blue_noise_fill(foot: np.ndarray, existing: np.ndarray, n: int, rng, sep: int = 5) -> np.ndarray:
    H, W = foot.shape
    avail = np.flatnonzero((foot & ~binary_dilation(existing, iterations=2)).ravel())
    rng.shuffle(avail)
    taken = binary_dilation(existing, iterations=4).copy()
    out = np.zeros(H * W, bool)
    cnt = 0
    for idx in avail:
        y, x = divmod(int(idx), W)
        if taken[y, x]:
            continue
        out[idx] = True
        cnt += 1
        taken[max(0, y - sep + 1): y + sep, max(0, x - sep + 1): x + sep] = True
        if cnt >= n:
            break
    return out.reshape(H, W)


def build_candidates(foot: np.ndarray) -> dict[str, np.ndarray]:
    names = json.loads(STACK_RECEIPT.read_text())["channels"]
    stack = np.load(STACK, mmap_mode="r")
    ridge2 = np.asarray(stack[:, :, names.index("ridge_s2")], dtype=np.float32)
    coh2 = np.asarray(stack[:, :, names.index("coherence_s2")], dtype=np.float32)
    e1 = nms_select(ridge2, foot, BUDGET)
    e2 = nms_select(ridge2 * coh2, foot, BUDGET)
    half = BUDGET // 2
    e3a = nms_select(ridge2, foot, half)
    e3b = blue_noise_fill(foot, e3a, BUDGET - int(e3a.sum()), np.random.default_rng(SEED))
    return {"E1_ridge2_nms": e1, "E2_ridge2xcoh_nms": e2, "E3_half_nms_half_bluenoise": e3a | e3b}


def write_tif(mask: np.ndarray, foot: np.ndarray, out: Path) -> None:
    with rasterio.open(TEMPLATE) as t:
        prof = t.profile.copy()
    prof.update(driver="GTiff", dtype="float32", count=1, nodata=None, compress="deflate",
                predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256)
    arr = np.where(foot, mask.astype(np.float32), np.float32(0.0)).astype(np.float32)
    out.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(arr, 1)
        dst.update_tags(AREA_OR_POINT="Area")


def format_check(path: Path) -> dict:
    """Independent format check against the official template (shape, CRS, transform, dtype, range)."""
    with rasterio.open(TEMPLATE) as t:
        tfoot = np.isfinite(t.read(1))
        t_crs, t_tr, t_shape = t.crs, t.transform, t.shape
    with rasterio.open(path) as s:
        a = s.read(1)
        ok = {
            "single_band": s.count == 1,
            "dtype_float32": s.dtypes == ("float32",),
            "crs_epsg_32611": s.crs == t_crs and s.crs.to_epsg() == 32611,
            "shape_matches_template": s.shape == t_shape,
            "transform_matches_template": s.transform == t_tr,
            "nodata_tag_none_or_nan": s.nodata is None or math.isnan(s.nodata),
        }
    ok["no_nan_anywhere"] = bool(np.isfinite(a).all())
    ok["all_values_in_0_1"] = bool(((a >= 0) & (a <= 1)).all())
    ok["footprint_pixels"] = int(tfoot.sum())
    ok["emitted_positive_pixels"] = int((a > 0).sum())
    ok["unique_values"] = [float(v) for v in np.unique(a)]
    ok["format_valid"] = all(v for k, v in ok.items() if isinstance(v, bool))
    ok["sha256"] = sha256_file(path)
    ok["bytes"] = path.stat().st_size
    return ok


def uniqueness(surface_dots: np.ndarray, foot: np.ndarray, stage: str) -> dict:
    from scripts.check_uniqueness import compare
    rows = []
    reg = json.loads(REGISTRY.read_text())
    for r in reg["rasters"]:
        p = RESTORE_LOG / (r["id"] + ".tif")
        if not p.is_file():
            rows.append({"id": r["id"], "comparable": False, "reason": "not restored (see registry_restore)"})
            continue
        with rasterio.open(p) as s:
            ref = s.read(1)
        ref_dots = np.isfinite(ref) & (ref > 0) & foot
        ref_surface = np.where(np.isfinite(ref), ref, 0.0).astype(np.float64)
        row = compare(dots_to_surface(surface_dots), surface_dots, ref_surface, foot, reference_dots=ref_dots)
        cov = reference_coverage(ref_dots, foot)
        row.update(id=r["id"], sha256_expected=r["sha256"], sha256_actual=sha256_file(p), reported_dti=r.get("reported_dti"),
                   reference_footprint_coverage_3px=round(cov, 4), saturated=bool(cov >= 0.70))
        rows.append(row)
    dup = [x["id"] for x in rows if x.get("duplicate") is True and x.get("saturated") is not True]
    sat_dup = [x["id"] for x in rows if x.get("duplicate") is True and x.get("saturated") is True]
    comparable = [x for x in rows if x.get("comparable") is True]
    return {"stage": stage, "registry_file": str(REGISTRY.relative_to(ROOT)), "registry_complete": False,
            "registry_total_listed": len(reg["rasters"]), "registry_compared": len(comparable),
            "registry_missing": [x["id"] for x in rows if x.get("comparable") is not True],
            "max_directed_overlap_3px": max((x.get("directed_dot_overlap_3px") or 0.0) for x in comparable) if comparable else None,
            "max_abs_rank_corr": max((abs(x["rank_correlation"]) for x in comparable if x.get("rank_correlation") is not None), default=None),
            "duplicates": dup, "saturated_probe_flags": sat_dup, "rows": rows}


def reference_coverage(ref_dots: np.ndarray, foot: np.ndarray) -> float:
    from scipy.ndimage import distance_transform_edt
    return float((distance_transform_edt(~ref_dots)[foot] <= 3).mean())


def dots_to_surface(dots: np.ndarray) -> np.ndarray:
    """Binary preview surface: the dot indicator itself (no threshold invented here)."""
    return dots.astype(np.float64)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", default="E2_ridge2xcoh_nms")
    ap.add_argument("--publish-dir", type=Path, default=None, help="copy final TIFF here (docs/downloads)")
    ap.add_argument("--name", default="kanler3-catalogue-blind-e2-ridgecoh-37654-20261028")
    ap.add_argument("--note", default="Catalogue-blind ridge x coherence dots, NaN-free. Holdout gate failed. Do not submit.")
    ap.add_argument("--evidence", type=Path, default=ROOT / "evidence" / "catalogue-blind-e123-20261028.json")
    args = ap.parse_args()
    if len(args.note) > NOTE_MAX:
        raise SystemExit(f"note exceeds {NOTE_MAX} characters")
    t0 = time.time()
    ev = load_tool("evaluate_holdout")
    from gems32 import holdout
    ctx = holdout.load_holdout_context(ROOT / "data" / "core")
    foot = ctx.foot
    with rasterio.open(LABELS) as s:
        labels = (s.read(1) >= 1) & foot

    cands = build_candidates(foot)
    results = {}
    for name, m in cands.items():
        hr = holdout.evaluate_hide_and_recover(m, ctx, name=name)
        sg = holdout.evaluate_sgmc_with_ci(m, ctx, name=name)
        results[name] = {
            "selected_dots_label_free": int(m.sum()),
            "hide_recover_pooled_dti": round(float(hr["pooled_dti"]), 4),
            "hide_recover_ci95": [round(float(x), 4) for x in hr["ci95_cluster_bootstrap"]],
            "hide_recover_withheld_positives": int(hr["n_withheld_positives"]),
            "hide_recover_evaluator": hr["evaluator_version"],
            "sgmc_raw_pooled_dti": round(float(sg["sgmc_raw_pooled_dti"]), 4),
            "sgmc_raw_ci95": [round(float(x), 4) for x in sg["sgmc_raw_ci95"]],
            "sgmc_calibrated_dti": round(float(sg["sgmc_prevalence_calibrated_dti"]), 4),
            "sgmc_evaluator": sg["evaluator_version"],
            "label": "HOLDOUT-DTI",
        }
        print(name, json.dumps(results[name]), flush=True)

    chosen = args.candidate
    m = cands[chosen]
    # Final file = writer rule: catalogue pixels removed after selection.
    final = m & ~labels
    scratch = ROOT / ".cache" / "experiments" / f"{chosen}-final.tif"
    write_tif(final, foot, scratch)
    fmt = format_check(scratch)
    # Score the exact file bytes that would be published (shared evaluator on the GeoTIFF).
    file_eval = ev.evaluate_path(scratch, ddir=ROOT / "data" / "core", name=args.name)
    fhr = file_eval["hide_and_recover"]
    fsg = file_eval["sgmc_off_catalogue"]
    final_metrics = {
        "hide_recover_pooled_dti": round(float(fhr["pooled_dti"]), 4),
        "hide_recover_ci95": [round(float(x), 4) for x in fhr["ci95_cluster_bootstrap"]],
        "hide_recover_withheld_positives": int(fhr["n_withheld_positives"]),
        "sgmc_raw_pooled_dti": round(float(fsg["sgmc_raw_pooled_dti"]), 4),
        "sgmc_raw_ci95": [round(float(x), 4) for x in fsg["sgmc_raw_ci95"]],
        "sgmc_calibrated_dti": round(float(fsg["sgmc_prevalence_calibrated_dti"]), 4),
        "label": "HOLDOUT-DTI",
    }

    u_surface = uniqueness(cands[chosen], foot, "surface-before-writer")
    u_final = uniqueness(final, foot, "final-dots")

    gate_holdout = (final_metrics["hide_recover_pooled_dti"] > INCUMBENT_BEST["hide_recover"]
                    and final_metrics["sgmc_raw_pooled_dti"] > INCUMBENT_BEST["sgmc_raw"])
    gate_unique = (not u_surface["duplicates"] and not u_final["duplicates"]
                   and u_final["registry_compared"] > 0)
    saturated_block = bool(u_final["saturated_probe_flags"] or u_surface["saturated_probe_flags"])
    gate_format = fmt["format_valid"] and fmt["no_nan_anywhere"] and fmt["all_values_in_0_1"]
    registry_complete = False  # the 36-raster inventory is not a complete GEMSDOE registry
    if not gate_format:
        verdict = "BLOCKED_FORMAT"
    elif not gate_unique:
        verdict = "STOP_DUPLICATE"
    elif not gate_holdout:
        verdict = "NEGATIVE_HOLDOUT_NOT_BEATEN"
    elif saturated_block:
        verdict = "BLOCKED_SATURATED_UNIQUENESS_PROBE"
    elif not registry_complete:
        verdict = "PROMOTE_PENDING_COMPLETE_REGISTRY"
    else:
        verdict = "PROMOTE"

    receipt = {
        "schema": "kanler3.catalogue_blind_e123.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "budget_dots": BUDGET,
        "selection": "label-free (35-channel template stack only); final file removes catalogue pixels per shared writer rule",
        "pre_registration": "research/catalogue-blind-prereg-20261028.md",
        "evaluators": {"hide_recover": "GEMSDOE32-HIDE-RECOVER-v3.0", "sgmc": "GEMSDOE32-SGMC-CAL-v3.0"},
        "incumbent_best_same_evaluator": INCUMBENT_BEST,
        "candidates": results,
        "chosen": chosen,
        "name": args.name,
        "note": args.note,
        "note_chars": len(args.note),
        "final_file": {"path": scratch.relative_to(ROOT).as_posix(), "sha256": fmt["sha256"], "bytes": fmt["bytes"],
                       "dots_after_catalogue_removal": fmt["emitted_positive_pixels"],
                       "catalogue_pixels_removed": int((m & labels).sum()), "format": fmt, "holdout_on_file": final_metrics},
        "uniqueness": {"surface_before_writer": {k: v for k, v in u_surface.items() if k != "rows"},
                       "final_dots": {k: v for k, v in u_final.items() if k != "rows"}},
        "uniqueness_rows_final": u_final["rows"],
        "gates": {"format": gate_format, "unique_vs_compared_registry_non_saturated": gate_unique,
                  "saturated_probe_flagged_literal_stop": saturated_block,
                  "beats_same_evaluator_incumbent_on_both_proxies": gate_holdout,
                  "registry_complete": registry_complete},
        "verdict": verdict,
        "slot_authorized": False,
        "seconds": round(time.time() - t0, 1),
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("chosen", "verdict", "gates")}, indent=2))
    if args.publish_dir is not None and str(args.publish_dir) not in ("", "."):
        args.publish_dir.mkdir(parents=True, exist_ok=True)
        out = args.publish_dir / (args.name + ".tif")
        out.write_bytes(scratch.read_bytes())
        print("published", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
