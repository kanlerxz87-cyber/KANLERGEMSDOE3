#!/usr/bin/env python3
"""E2/E3 pre-registered candidates (evidence/preregistration-20261029-kanler-s3.json).

Builds dot fields by greedy descending-prior selection with a 4-px suppression radius,
a 2-px catalogue exclusion (the H33 B2 rule, pixel-exact label mask always removed), and
a fixed dot budget N=37,654. Scores each field with the lock-verified vendored evaluators:
  * SGMC-CAL proxy (evaluate_sgmc_with_ci) - the leaderboard-aligned proxy on focus-9 (n=9)
  * catalogue hide-and-recover (evaluate_hide_and_recover) with a LEAK-FREE per-cell build
    that uses only VISIBLE catalogue faults for the exclusion
Uniqueness: fraction of dots within 3 px of each focus-9 TIFF and the Spearman of the fields.
Nothing here is an organizer score; every number is labelled by its evaluator.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shared_tools  # noqa: E402
from kanler_s3_canary import load_band, ridge_response  # noqa: E402

DATA = ROOT / "data"
FOCUS = ROOT / ".cache/peers/focus9"
OUT = ROOT / "evidence/kanler-s3-e2-candidates-20261029.json"
N_DOTS = 37654
SUPPRESS_PX = 4
EXCL_PX = 2.0


def greedy_select(prior: np.ndarray, cand: np.ndarray, n: int, radius: int) -> np.ndarray:
    """Pick up to n cells in descending prior order, suppressing a disk of `radius` around each pick."""
    H, W = prior.shape
    r = int(radius)
    Wp = W + 2 * r
    blocked = np.zeros((H + 2 * r) * Wp, dtype=np.uint8)
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (dy ** 2 + dx ** 2) <= r * r
    offs = (dy[disk] * Wp + dx[disk]).astype(np.int64)
    idx = np.flatnonzero(cand)
    order = idx[np.argsort(-prior.ravel()[idx], kind="stable")]
    out = np.zeros(H * W, dtype=bool)
    picked = 0
    for p in order:
        y, x = divmod(int(p), W)
        q = (y + r) * Wp + (x + r)
        if blocked[q]:
            continue
        out[p] = True
        blocked[q + offs] = 1
        picked += 1
        if picked == n:
            break
    return out.reshape(H, W)


def build_field(kind: str, prior: np.ndarray, foot: np.ndarray, visible_labels: np.ndarray,
                rng: np.random.Generator | None = None) -> np.ndarray:
    too_close = distance_transform_edt(~visible_labels) <= EXCL_PX
    cand = foot & ~too_close & np.isfinite(prior)
    if kind == "random_off_catalogue":
        score = rng.random(prior.shape)
    else:
        score = np.where(cand, prior, -np.inf)
    return greedy_select(score, cand, N_DOTS, SUPPRESS_PX)


def sgmc_cal(mask: np.ndarray, H, ctx) -> dict:
    r = H.evaluate_sgmc_with_ci(mask, ctx, n_boot=400, name="cand")
    return {
        "sgmc_prevalence_calibrated_dti": round(float(r["sgmc_prevalence_calibrated_dti"]), 6),
        "sgmc_calibrated_ci95": [round(float(x), 6) for x in r["sgmc_calibrated_ci95"]],
        "sgmc_raw_dti": round(float(r["sgmc_raw_pooled_dti"]), 6),
        "sgmc_n_withheld": int(r["n_withheld_positives"]),
        "evaluator_version": r["evaluator_version"],
        "label": "SGMC-CAL proxy (not an organizer score)",
    }


def catalogue_holdout(kind, prior, foot, ctx, H, rng_seed) -> dict:
    cells = {}
    for cell in ctx.cells:
        rng = np.random.default_rng(rng_seed + 100 * cell.seed + cell.fold)  # deterministic per cell
        cells[cell.key] = build_field(kind, prior, foot, ctx.visible_by_cell[cell.key], rng)
    r = H.evaluate_hide_and_recover(cells, ctx, n_boot=400, name=kind)
    return {
        "pooled_dti": round(float(r["pooled_dti"]), 6),
        "ci95": [round(float(x), 6) for x in r["ci95_cluster_bootstrap"]],
        "n_withheld_positives": int(r["n_withheld_positives"]),
        "evaluator_version": r["evaluator_version"],
        "build": "per-cell, VISIBLE-only exclusion (leak-free)",
        "label": "HOLDOUT-DTI (catalogue, leak-free)",
    }


def main() -> None:
    lock = shared_tools.verify_template()
    if not lock["ok"]:
        raise SystemExit("template lock failed")
    sys.path.insert(0, str(shared_tools.TEMPLATE / "src"))
    import gems32.holdout as H

    ctx = H.load_holdout_context(DATA)
    foot = ctx.foot
    labels = ctx.labels

    rtp = load_band(DATA / "training_features.tif", 2)
    geo_shear = load_band(DATA / "training_features.tif", 7)
    priors = {
        "KS3-ridge": ridge_response(rtp, 1.5),
        "KS3-strain": np.where(np.isfinite(geo_shear), geo_shear, np.nan),
    }
    from scipy.ndimage import gaussian_filter
    fill = np.where(np.isfinite(priors["KS3-strain"]), priors["KS3-strain"], np.nanmedian(priors["KS3-strain"][foot]))
    priors["KS3-strain"] = gaussian_filter(fill, 1.5)

    focus = {}
    for f in sorted(FOCUS.glob("*.tif")):
        with rasterio.open(f) as ds:
            a = ds.read(1).astype(np.float64)
        d = np.zeros(foot.shape, bool)
        d[foot] = np.nan_to_num(a[foot], nan=0.0) > 0.5
        focus[f.name] = d

    results = {}
    fields = {}
    for name in ("KS3-ridge", "KS3-strain", "random_off_catalogue"):
        prior = priors.get(name, np.zeros(foot.shape))
        rng = np.random.default_rng(20261029)
        mask = build_field(name, prior, foot, labels, rng)
        fields[name] = mask
        results[name] = {"dots": int(mask.sum()), "on_catalogue": int((mask & labels).sum()),
                         "within_2px_catalogue": int((mask & (distance_transform_edt(~labels) <= 2.0)).sum())}
        results[name]["sgmc"] = sgmc_cal(mask, H, ctx)
        results[name]["catalogue_holdout"] = catalogue_holdout(name, prior, foot, ctx, H, 20261029)
        uniq = {}
        for fn, fm in focus.items():
            near = distance_transform_edt(~fm) if fm.any() else None
            uniq[fn.split("__")[0]] = round(float((near[mask] <= 3.0).mean()), 6) if near is not None else None
        results[name]["overlap_within_3px_vs_focus9"] = uniq
        results[name]["max_overlap_within_3px_vs_focus9"] = max(v for v in uniq.values() if v is not None)
        rho_list = {}
        a_field = mask.ravel()[foot.ravel()].astype(np.float64)
        for fn, fm in focus.items():
            b_field = fm.ravel()[foot.ravel()].astype(np.float64)
            rho_list[fn.split("__")[0]] = round(float(spearmanr(a_field, b_field).statistic), 6)
        results[name]["spearman_vs_focus9"] = rho_list
        results[name]["max_spearman_vs_focus9"] = max(rho_list.values())

    # Reference: H33 B2 under the same evaluators (proxy numbers only, no new build).
    h33 = [f for f in focus if "GEMSDOE32" in f][0]
    results["REFERENCE_H33_B2"] = {"dots": int(focus[h33].sum()), "sgmc": sgmc_cal(focus[h33], H, ctx)}

    out = {
        "kind": "E2/E3 CANDIDATE EVALUATION (pre-registered; proxies, NOT organizer scores)",
        "template_lock_commit": lock["commit"],
        "pre_registration": "evidence/preregistration-20261029-kanler-s3.json",
        "parameters": {"dots": N_DOTS, "suppress_px": SUPPRESS_PX, "catalogue_exclusion_px": EXCL_PX},
        "results": results,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    np.savez_compressed(ROOT / ".cache/kanler_s3_fields.npz", **{k.replace("-", "_"): v for k, v in fields.items()})
    print(json.dumps(out["results"], indent=1))


if __name__ == "__main__":
    main()
