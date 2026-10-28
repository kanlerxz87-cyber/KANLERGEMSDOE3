#!/usr/bin/env python3
"""Staged runner for lane L-K3-CPX-EDTI (preregistration: evidence/preregistration_cpx_20261028.json).

Stages (checkpointed under .cache/cpx/, ignored by git):
  physics   build 16 label-free physics channels from the 19 bands
  canary    single-feature AUC leakage canary for all 93 used features
  holdout   4-fold quadrant hide-and-recover: Exp-CPX-1/2/3 + B0 + random + statics
  deploy    OOF deployment surface + final 37,654-dot emission
  finalize  uniqueness audit, shared-writer GeoTIFF pair, validators, run card

All metric/holdout/writer calls delegate to the SHA-pinned vendor template.
No competition slot is touched.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.cadg_evaluate_holdout import audit_uniqueness_against_registry  # noqa: E402
from scripts.cadg_submission_writer import write_pair  # noqa: E402
from src.kanlergems3.features import build_or_load_feature_cache  # noqa: E402
from src.kanlergems3.models import (  # noqa: E402
    fit_baseline_regional_19band,
    predict_baseline_regional_19band,
    _make_hgb,
    _prior_calibrate,
)
from src.kanlergems3.submodular import celf_submodular_emit_300m, greedy_spacing_emit  # noqa: E402
from src.kanlergems3_cpx.emission import edti_greedy_emit  # noqa: E402
from src.kanlergems3_cpx.physics import (  # noqa: E402
    build_or_load_physics_cache,
    physics_coincidence_surface,
    rank_fusion,
)
from vendor.gems24_template.holdout import SegmentHoldout  # noqa: E402
from vendor.gems24_template.metric import ridge_nms, select_top_positive  # noqa: E402
from vendor.gems24_template.validator import sha256_file  # noqa: E402

DATA = ROOT / ".cache/gems_data"
WORK = ROOT / ".cache/cpx"
FULL_BUDGET = 37_654
COLLAR_PX = 2.05
DATE = "20261028"


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def load_grid() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with rasterio.open(DATA / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(DATA / "labels.tif") as s:
        labels = (s.read(1) > 0) & foot
    return foot, labels, np.flatnonzero(foot.ravel())


def load_caches():
    base = build_or_load_feature_cache(DATA, WORK / "base_cache")
    phys = build_or_load_physics_cache(DATA, WORK / "physics_cache")
    assert np.array_equal(base["fp_idx"], phys["fp_idx"])
    return base, phys


def gather(base_mm, phys_mm, rows: np.ndarray) -> np.ndarray:
    return np.concatenate([np.asarray(base_mm[rows], dtype=np.float32),
                           np.asarray(phys_mm[rows], dtype=np.float32)], axis=1)


# ---------------------------------------------------------------- physics
def stage_physics() -> None:
    t0 = time.monotonic()
    phys = build_or_load_physics_cache(DATA, WORK / "physics_cache")
    print(f"[physics] {phys['memmap'].shape} in {time.monotonic()-t0:.1f}s", flush=True)


# ---------------------------------------------------------------- canary
def stage_canary() -> None:
    foot, labels, fp_idx = load_grid()
    ho = SegmentHoldout(foot, labels, buffer_px=15)
    base, phys = load_caches()
    buf = np.zeros(foot.shape, dtype=np.float32)

    def surf(mm, j):
        buf.fill(0.0)
        buf.ravel()[fp_idx] = np.asarray(mm[:, j], dtype=np.float32)
        return buf.copy()

    # Memory-bounded: canary in batches of 8 surfaces (each 49 MB). The
    # shared canary reseeds its sampler per call (seed=20261025), so fold
    # samples are identical across batches; merging is exact.
    items: list[tuple[str, Any, int]] = (
        [(n, base["memmap"], j) for j, n in enumerate(base["meta"]["feature_names"])]
        + [(n, phys["memmap"], j) for j, n in enumerate(phys["meta"]["feature_names"])])
    t0 = time.monotonic()
    merged: dict[str, Any] = {}
    for s in range(0, len(items), 8):
        batch = {n: surf(mm, j) for n, mm, j in items[s:s + 8]}
        part = ho.canary(batch, seed=20261025, max_per_class=15000)
        merged.update(part["features"])
        del batch, part
        gc.collect()
    # Fused physics coincidence is itself an input surface: canary it too.
    part = ho.canary({"cpx_physics_coincidence": physics_coincidence_surface(phys, foot)},
                     seed=20261025, max_per_class=15000)
    merged.update(part["features"])
    feats = merged
    report = {"passed": not any(v["leakage_suspected"] for v in merged.values()),
              "features": merged}
    aucs = {k: max(v["pooled_auc"], 1 - v["pooled_auc"]) for k, v in report["features"].items()}
    summary = {"passed": report["passed"], "n_features": len(feats),
               "max_two_polarity_auc": float(max(aucs.values())),
               "worst5": sorted(aucs.items(), key=lambda kv: -kv[1])[:5],
               "elapsed_sec": round(time.monotonic() - t0, 1)}
    wjson(ROOT / "evidence/cpx_leakage_canary_20261028.json",
          {"lane": "L-K3-CPX-EDTI", **summary, "detail": report})
    print(f"[canary] passed={report['passed']} maxAUC={summary['max_two_polarity_auc']:.4f} "
          f"n={len(feats)} {summary['elapsed_sec']}s", flush=True)
    if not report["passed"]:
        raise SystemExit("LEAKAGE CANARY FAILED - stop per protocol")


# ---------------------------------------------------------------- models
def fit_cpx(base_mm, phys_mm, foot, fp_idx, train, visible, *, seed):
    d_vis = distance_transform_edt(~visible)
    train_fp = train.ravel()[fp_idx]
    vis_fp = visible.ravel()[fp_idx]
    d_fp = d_vis.ravel()[fp_idx]
    pos = np.flatnonzero(train_fp & vis_fp)
    neg_pool = np.flatnonzero(train_fp & (d_fp >= 5.0))
    rng = np.random.default_rng(seed)
    neg = np.sort(rng.choice(neg_pool, size=min(len(neg_pool), len(pos) * 6), replace=False))
    idx = np.concatenate([pos, neg])
    X = gather(base_mm, phys_mm, idx)
    y = np.concatenate([np.ones(len(pos), np.int8), np.zeros(len(neg), np.int8)])
    clf: HistGradientBoostingClassifier = _make_hgb(max_iter=200, seed=seed)
    clf.fit(X, y)
    true_prior = float(len(pos)) / max(int(train_fp.sum()), 1)
    sample_ratio = float(len(pos)) / max(len(neg), 1)
    prior_ratio = true_prior / max((1.0 - true_prior) * sample_ratio, 1e-6)
    return clf, prior_ratio, {"n_pos": int(len(pos)), "n_neg": int(len(neg))}


def predict_cpx(clf, prior_ratio, base_mm, phys_mm, foot, fp_idx, domain):
    dom = np.flatnonzero(np.asarray(domain, bool).ravel()[fp_idx])
    out = np.zeros(foot.shape, dtype=np.float32)
    probs = np.empty(len(dom), dtype=np.float32)
    for s in range(0, len(dom), 200_000):
        sl = dom[s:s + 200_000]
        probs[s:s + len(sl)] = _prior_calibrate(
            clf.predict_proba(gather(base_mm, phys_mm, sl))[:, 1], prior_ratio, sharpness=1.28)
    out.ravel()[fp_idx[dom]] = probs
    return out


# ---------------------------------------------------------------- holdout
SERIES = ["matched_random", "static_GEMSDOE30_D28", "static_GEMSDOE32_H33B2",
          "B0_regional_19band", "Exp-CPX-1", "Exp-CPX-2", "Exp-CPX-3"]


def stage_holdout() -> None:
    foot, labels, fp_idx = load_grid()
    n_fp = len(fp_idx)
    ho = SegmentHoldout(foot, labels, buffer_px=15)
    base, phys = load_caches()
    base_mm, phys_mm = base["memmap"], phys["memmap"]
    phys_surf_full = physics_coincidence_surface(phys, foot)

    def static(path):
        with rasterio.open(path) as s:
            a = s.read(1)
        return np.isfinite(a) & (a > 0) & foot

    st30, st32 = static(DATA / "GEMSDOE30.tif"), static(DATA / "GEMSDOE32.tif")
    preds: dict[str, list[np.ndarray]] = {k: [] for k in SERIES}
    oof_sup = np.zeros(foot.shape, dtype=np.float32)
    fold_reports = []
    ck = WORK / "holdout_checkpoint.json"

    for fold in ho.folds:
        fid, fname = int(fold["id"]), fold["name"]
        valid, train, visible = fold["valid"], fold["train"], fold["visible"]
        assert not (train & valid).any() and not (visible & fold["truth"]).any()
        d_vis = distance_transform_edt(~visible)
        eligible = valid & (d_vis > COLLAR_PX)
        active_mass = valid & ~visible
        budget = int(round(FULL_BUDGET * int(valid.sum()) / n_fp))
        t0 = time.monotonic()
        rep: dict[str, Any] = {"fold": fname, "budget": budget,
                               "withheld_positives": int(fold["truth"].sum())}

        rng = np.random.default_rng(20261028 + 31 * fid)
        rnd = np.zeros(foot.shape, dtype=np.float32)
        rnd[eligible] = rng.random(int(eligible.sum()), dtype=np.float32)
        preds["matched_random"].append(
            greedy_spacing_emit(rnd, eligible, budget, min_spacing_px=2.8).astype(np.uint8))
        preds["static_GEMSDOE30_D28"].append((st30 & valid & ~visible).astype(np.uint8))
        preds["static_GEMSDOE32_H33B2"].append((st32 & valid & ~visible).astype(np.uint8))

        b0_clf, b0_cols, b0_pr = fit_baseline_regional_19band(
            base_mm, base["meta"], foot, train, visible, seed=20261028 + 100 * fid)
        b0_surf = predict_baseline_regional_19band(b0_clf, b0_cols, b0_pr, base_mm, foot, fp_idx, valid)
        preds["B0_regional_19band"].append(
            greedy_spacing_emit(b0_surf, eligible, budget, min_spacing_px=2.8).astype(np.uint8))
        del b0_clf, b0_surf

        clf, pr, fitrep = fit_cpx(base_mm, phys_mm, foot, fp_idx, train, visible,
                                  seed=20261028 + 100 * fid)
        sup = predict_cpx(clf, pr, base_mm, phys_mm, foot, fp_idx, valid)
        oof_sup[valid] = sup[valid]
        rep["cpx_fit"] = fitrep
        fused = rank_fusion([phys_surf_full, sup], [0.5, 0.5], active_mass)

        d1 = celf_submodular_emit_300m(fused, eligible, budget, active_mass_mask=active_mass,
                                       min_self_spacing_px=2.85)
        preds["Exp-CPX-1"].append(d1.astype(np.uint8))
        d2, _ = edti_greedy_emit(fused, eligible, budget, mass_mask=active_mass)
        preds["Exp-CPX-2"].append(d2.astype(np.uint8))
        d3, _ = edti_greedy_emit(sup, eligible, budget, mass_mask=active_mass)
        preds["Exp-CPX-3"].append(d3.astype(np.uint8))
        for k, d in (("Exp-CPX-1", d1), ("Exp-CPX-2", d2), ("Exp-CPX-3", d3)):
            sc, _ = ho.score_fold(d.astype(np.uint8), fold)
            rep[k] = {"fold_dti": float(sc["dti"]), "dots": int(d.sum())}
        rep["elapsed_sec"] = round(time.monotonic() - t0, 1)
        fold_reports.append(rep)
        np.save(WORK / "oof_sup_surface.npy", oof_sup)
        wjson(ck, {"folds_done": fold_reports})
        print(f"[holdout] {fname}: E1={rep['Exp-CPX-1']['fold_dti']:.4f} "
              f"E2={rep['Exp-CPX-2']['fold_dti']:.4f} E3={rep['Exp-CPX-3']['fold_dti']:.4f} "
              f"({rep['elapsed_sec']}s)", flush=True)
        del clf, sup, fused, d1, d2, d3
        gc.collect()

    summaries = {}
    for k in SERIES:
        summaries[k] = ho.summarize(preds[k], ci_draws=1999)
        print(f"[holdout] {k}: HOLDOUT-DTI {summaries[k]['dti']:.6f} "
              f"CI {summaries[k]['ci95']['interval']}", flush=True)
    paired = {
        "Exp-CPX-2_vs_B0": ho.compare_paired(preds["Exp-CPX-2"], preds["B0_regional_19band"], ci_draws=1999, seed=20261025),
        "Exp-CPX-2_vs_Exp-CPX-1": ho.compare_paired(preds["Exp-CPX-2"], preds["Exp-CPX-1"], ci_draws=1999, seed=20261025),
        "Exp-CPX-2_vs_Exp-CPX-3": ho.compare_paired(preds["Exp-CPX-2"], preds["Exp-CPX-3"], ci_draws=1999, seed=20261025),
    }
    np.savez_compressed(WORK / "holdout_preds.npz",
                        **{f"{k}_{i}": np.packbits(p.ravel()) for k in SERIES for i, p in enumerate(preds[k])},
                        shape=np.array(foot.shape))
    wjson(ROOT / "evidence/cpx_holdout_20261028.json", {
        "lane": "L-K3-CPX-EDTI", "class": "HOLDOUT-DTI",
        "evaluator_version": "gems-segment-pooled-v1 (vendor gems24_template SegmentHoldout, buffer 15 px)",
        "summaries": summaries, "paired": paired, "fold_reports": fold_reports,
        "recorded_incumbent_ATSC_Exp_ATSC_2": 0.1637154060975635,
        "recorded_incumbent_source": "evidence/atsc_holdout_20261027.json (same evaluator/split; not rerun this session)",
    })


# ---------------------------------------------------------------- deploy
def stage_deploy() -> None:
    foot, labels, fp_idx = load_grid()
    base, phys = load_caches()
    oof_sup = np.load(WORK / "oof_sup_surface.npy")
    domain = foot & ~labels
    phys_surf = physics_coincidence_surface(phys, domain)
    fused = rank_fusion([phys_surf, oof_sup], [0.5, 0.5], domain)
    np.save(WORK / "deployment_surface.npy", fused)
    d_cat = distance_transform_edt(~labels)
    eligible = foot & (d_cat > COLLAR_PX)
    t0 = time.monotonic()
    dots, order = edti_greedy_emit(fused, eligible, FULL_BUDGET, mass_mask=domain,
                                   pool_multiplier=8)
    np.save(WORK / "deployment_dots.npy", dots)
    np.save(WORK / "deployment_order.npy", order)
    # Nested-budget diagnostics (reported, never used to retune the fixed budget).
    diag = {"dots": int(dots.sum()), "elapsed_sec": round(time.monotonic() - t0, 1),
            "on_catalogue": int((dots & labels).sum()),
            "min_dist_to_catalogue_px": float(d_cat[dots].min()),
            "median_dist_to_catalogue_px": float(np.median(d_cat[dots])),
            "frac_beyond_15px_from_catalogue": float((d_cat[dots] > 15).mean())}
    wjson(WORK / "deployment_diag.json", diag)
    print(f"[deploy] {diag}", flush=True)


# ---------------------------------------------------------------- finalize
def registry_entries(foot) -> tuple[list[dict], list[dict]]:
    entries, classified = [], []
    seen = set()
    paths = (sorted((DATA / "registry").glob("*.tif")) + sorted((DATA / "scored").glob("*.tif"))
             + sorted(DATA.glob("GEMSDOE*.tif")) + sorted(ROOT.glob("docs/**/downloads/*.tif"))
             + sorted(ROOT.glob("docs/candidate_downloads/*.tif")) + sorted(ROOT.glob("docs/downloads/*.tif")))
    n_fp = int(foot.sum())
    for p in paths:
        if "cpx-edti" in str(p):
            continue
        h = sha256_file(p)
        if h in seen:
            continue
        seen.add(h)
        with rasterio.open(p) as s:
            a = s.read(1)
            shape_ok = s.shape == foot.shape
        if not shape_ok:
            classified.append({"file": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name,
                               "sha256": h, "class": "excluded_shape_mismatch"})
            continue
        pos = int((np.isfinite(a) & (a > 0) & foot).sum())
        is_lattice = "lattice" in p.name.lower()
        is_continuous = pos > 0.25 * n_fp and not is_lattice
        probe = bool(is_lattice or is_continuous)
        cls = ("calibration_lattice_probe" if is_lattice else
               "continuous_diagnostic_probe" if is_continuous else "genuine_detector")
        entries.append({"id": f"{p.parent.name}:{p.stem}", "site": p.parent.name,
                        "resolved_path": str(p), "sha256": h, "is_calibration_probe": probe,
                        "reported_dti": None})
        classified.append({"file": p.name, "sha256": h, "positive_px_in_footprint": pos,
                           "class": cls})
    return entries, classified


def stage_finalize() -> None:
    foot, labels, fp_idx = load_grid()
    fused = np.load(WORK / "deployment_surface.npy")
    dots = np.load(WORK / "deployment_dots.npy")
    d_cat = distance_transform_edt(~labels)
    eligible = foot & (d_cat > COLLAR_PX)
    # Pre-placement surface preview dots (protocol: check surface before placement).
    ridges = ridge_nms(fused, foot, sigma=1.0)
    preview = select_top_positive(np.where(ridges, fused, 0.0), eligible, FULL_BUDGET)
    if int(preview.sum()) < FULL_BUDGET:
        preview |= select_top_positive(fused, eligible & ~preview, FULL_BUDGET - int(preview.sum()))

    entries, classified = registry_entries(foot)
    audit = audit_uniqueness_against_registry(fused, preview, dots, foot, labels, entries)
    wjson(ROOT / "evidence/cpx_uniqueness_20261028.json",
          {"lane": "L-K3-CPX-EDTI", "registry_classification": classified, "audit": audit})
    print("[finalize] uniqueness:", json.dumps({k: audit[k] for k in audit
          if k not in ("detectors", "calibration_probes")}, indent=1)[:1500], flush=True)

    hold = json.loads((ROOT / "evidence/cpx_holdout_20261028.json").read_text())
    canary = json.loads((ROOT / "evidence/cpx_leakage_canary_20261028.json").read_text())
    e2 = hold["summaries"]["Exp-CPX-2"]
    gates = {
        "canary_pass": bool(canary["passed"] and canary["max_two_polarity_auc"] <= 0.90),
        "paired_vs_B0_ci_positive": bool(hold["paired"]["Exp-CPX-2_vs_B0"]["ci95_strictly_positive"]),
        "fold_wins_vs_B0": f"{hold['paired']['Exp-CPX-2_vs_B0']['fold_wins']}/4",
        "emission_mechanism_E2_ge_E1": bool(e2["dti"] >= hold["summaries"]["Exp-CPX-1"]["dti"]),
        "fusion_mechanism_E2_ge_E3": bool(e2["dti"] >= hold["summaries"]["Exp-CPX-3"]["dti"]),
        "beats_recorded_ATSC_holdout_best": bool(e2["dti"] > hold["recorded_incumbent_ATSC_Exp_ATSC_2"]),
    }
    # Write the GeoTIFF pair with the shared writer regardless of promote verdict
    # (research deliverable); the run card + site carry the submit decision.
    pred = np.where(dots, 1.0, 0.0).astype(np.float32)
    outdir = ROOT / "docs/cpx-edti/downloads"
    receipt = write_pair(
        pred, template=DATA / "sample_submission.tif", catalogue=labels, footprint=foot,
        outdir=outdir, family="kanlergemsdoe3", hypothesis="h-cpx1-edti-fusion-37654",
        date=DATE,
        note_template="CPX coincident grav-mag-strain fusion + exact E-DTI emission 37.7k dots b2 {cid}",
        scientific_verdict="see run card",
    )
    wjson(WORK / "writer_receipt.json", receipt)
    wjson(WORK / "gates.json", gates)
    print(f"[finalize] wrote {receipt['primary_zero_outside']['file']} gates={gates}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", required=True,
                    choices=["physics", "canary", "holdout", "deploy", "finalize"])
    args = ap.parse_args()
    print(f"== L-K3-CPX-EDTI stage={args.stage} {datetime.now(timezone.utc).isoformat()} ==", flush=True)
    {"physics": stage_physics, "canary": stage_canary, "holdout": stage_holdout,
     "deploy": stage_deploy, "finalize": stage_finalize}[args.stage]()
    print("== stage done ==", flush=True)
    return 0


if __name__ == "__main__":
    from archive_guard import stop_archived_cli
    stop_archived_cli()
    raise SystemExit(main())
