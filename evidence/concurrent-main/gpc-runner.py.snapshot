#!/usr/bin/env python3
"""GPC-3 lane runner: canary -> segment holdout (B0/EXP-1/2/3) -> final unique TIF.

Protocol (parallel-run): reuse vendored gems template (SegmentHoldout
gems-segment-pooled-v1, submission writer, novelty), leakage canary per GPC
feature, pre-placement surface + final-dot uniqueness vs the 9 focus champions,
whole-array [0,1] validation. Verdict is fail-closed: promote only if the
preregistered gates pass; otherwise the TIF is a research artifact labelled
DO NOT SUBMIT. All scores are HOLDOUT-DTI unless labelled OWNER-REPORTED.
"""
from __future__ import annotations

import argparse, gc, hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SEED = 20261026
TOTAL_BUDGET = 37_654
HGB = dict(max_iter=250, learning_rate=0.06, max_leaf_nodes=48,
           min_samples_leaf=200, l2_regularization=1.0, early_stopping=False,
           random_state=SEED)
RECORDED_GROUP_BEST = 0.16379  # GEMSDOE24 DPRF1, gems-segment-pooled-v1 (site-fetched 2026-10-26)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_store():
    from kanler3.features import build_feature_stack
    from kanler3.paths import cache_dir
    return build_feature_stack(cache_dir() / "features")


def fp_mapping(grid):
    fp_flat = np.flatnonzero(grid.footprint.ravel())
    fp_pos = np.full(grid.footprint.size, -1, np.int64)
    fp_pos[fp_flat] = np.arange(len(fp_flat))
    return fp_flat, fp_pos


def predict_fp(model, store, names, fp_idx, chunk=400_000):
    out = np.empty(len(fp_idx), dtype=np.float32)
    for s in range(0, len(fp_idx), chunk):
        out[s:s + chunk] = model.predict_proba(store.rows(fp_idx[s:s + chunk], names))[:, 1].astype(np.float32)
    return out


def fit_predict(store, grid, names, train_flat, valid_flat, fp_pos):
    from sklearn.ensemble import HistGradientBoostingClassifier
    rng = np.random.default_rng(SEED)
    labels_flat = grid.labels.ravel()
    pos = train_flat[labels_flat[train_flat]]
    neg = train_flat[~labels_flat[train_flat]]
    if len(pos) > 50_000:
        pos = rng.choice(pos, 50_000, replace=False)
    if len(neg) > 300_000:
        neg = rng.choice(neg, 300_000, replace=False)
    tr_flat = np.r_[pos, neg]
    tr_idx = fp_pos[tr_flat]
    y = labels_flat[tr_flat].astype(np.int8)
    model = HistGradientBoostingClassifier(**HGB)
    model.fit(store.rows(tr_idx, names), y)
    p = predict_fp(model, store, names, fp_pos[valid_flat])
    return p, {"n_pos_train": int(len(pos)), "n_neg_train": int(len(neg))}


def phase_canary(store, grid) -> dict:
    from gems.holdout import SegmentHoldout
    from kanler3.gpc import GPC_FEATURE_NAMES
    holdout = SegmentHoldout(grid.footprint, grid.labels, buffer_px=15)
    feats = {}
    for name in GPC_FEATURE_NAMES:
        a = np.zeros(grid.footprint.shape, np.float32)
        a[grid.footprint] = store.column(name)
        feats[name] = a
    res = holdout.canary(feats, seed=SEED)
    out = {"label": "LEAKAGE-CANARY", "evaluator_version": "gems-segment-pooled-v1",
           "generated_utc": now(), "passed": bool(res["passed"]), "features": {}}
    for name, r in res["features"].items():
        worst = max(max(r["pooled_auc"], 1 - r["pooled_auc"]),
                    *[max(f["auc"], 1 - f["auc"]) for f in r["folds"]])
        out["features"][name] = {"pooled_auc": r["pooled_auc"], "worst_two_polarity_auc": worst,
                                 "leakage_suspected": bool(r["leakage_suspected"])}
    (ROOT / "evidence" / "leakage_canary.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"[canary] passed={out['passed']} worst={max(v['worst_two_polarity_auc'] for v in out['features'].values()):.4f}", flush=True)
    return out


def phase_holdout(store, grid) -> dict:
    from gems.holdout import SegmentHoldout
    from kanler3.emission import emit_dots
    from kanler3.gpc import GPC_FEATURE_NAMES
    from scipy.ndimage import distance_transform_edt

    prereg = json.loads((ROOT / "evidence" / "preregistration.json").read_text())
    concord = prereg["gpc_concordance_subset"]
    base59 = [n for n in store.names if n not in GPC_FEATURE_NAMES]
    assert len(base59) == 59, len(base59)
    arms = {"B0": base59, "EXP-1": base59 + list(GPC_FEATURE_NAMES), "EXP-2": base59 + concord}
    holdout = SegmentHoldout(grid.footprint, grid.labels, buffer_px=15)
    fp_flat, fp_pos = fp_mapping(grid)
    n_fp = len(fp_flat)
    budgets = [int(round(TOTAL_BUDGET * int(f["valid"].sum()) / n_fp)) for f in holdout.folds]
    print(f"[holdout] folds={[f['name'] for f in holdout.folds]} budgets={budgets}", flush=True)

    preds: dict[str, list[np.ndarray]] = {a: [] for a in ("B0", "EXP-1", "EXP-2", "EXP-3")}
    fit_info = []
    cache = ROOT / ".cache" / "kanler3" / "holdout_dots"
    cache.mkdir(parents=True, exist_ok=True)
    for fi, fold in enumerate(holdout.folds):
        valid_flat = np.flatnonzero(fold["valid"].ravel())
        train_flat = np.flatnonzero(fold["train"].ravel())
        valid_fp_idx = fp_pos[valid_flat]
        fold_surfaces = {}
        for arm, names in arms.items():
            cpath = cache / f"{arm}_fold{fi}.npy"
            spath = cache / f"{arm}_fold{fi}_surface.npy"
            if cpath.exists() and spath.exists():
                dots = np.load(cpath); surf = np.load(spath, mmap_mode="r")
                preds[arm].append(dots); fold_surfaces[arm] = np.asarray(surf)
                print(f"[holdout] fold {fold['name']} {arm}: cached", flush=True); continue
            t0 = time.time()
            p_fp, info = fit_predict(store, grid, names, train_flat, valid_flat, fp_pos)
            score2d = np.zeros(grid.footprint.shape, np.float32)
            score2d.ravel()[valid_flat] = p_fp
            np.save(spath, score2d)
            dots = emit_dots(score2d, fold["valid"], budgets[fi]).astype(np.uint8)
            np.save(cpath, dots)
            preds[arm].append(dots); fold_surfaces[arm] = score2d
            fit_info.append({"fold": fold["name"], "arm": arm, **info, "seconds": round(time.time() - t0, 1)})
            print(f"[holdout] fold {fold['name']} {arm}: dots={int(dots.sum())} {time.time()-t0:.0f}s", flush=True)
            del p_fp, score2d; gc.collect()
        # EXP-3: EXP-1 surface, >2px from visible catalogue
        cpath = cache / f"EXP-3_fold{fi}.npy"
        if cpath.exists():
            preds["EXP-3"].append(np.load(cpath))
        else:
            surf = fold_surfaces["EXP-1"] if "EXP-1" in fold_surfaces else np.load(cache / f"EXP-1_fold{fi}_surface.npy")
            elig = fold["valid"] & (distance_transform_edt(~fold["visible"]) > 2)
            dots = emit_dots(np.asarray(surf), elig, budgets[fi]).astype(np.uint8)
            np.save(cpath, dots); preds["EXP-3"].append(dots)
            print(f"[holdout] fold {fold['name']} EXP-3: dots={int(dots.sum())}", flush=True)


    results, comparisons = {}, {}
    summaries = {}
    for arm in ("B0", "EXP-1", "EXP-2", "EXP-3"):
        summaries[arm] = holdout.summarize(preds[arm])
        print(f"[holdout] {arm}: HOLDOUT-DTI={summaries[arm]['dti']:.6f} CI={summaries[arm]['ci95']['interval']}", flush=True)
    for arm in ("EXP-1", "EXP-2", "EXP-3"):
        comparisons[arm] = holdout.compare_paired(preds[arm], preds["B0"])
        print(f"[holdout] {arm} vs B0 delta={comparisons[arm]['paired_delta_dti']:+.6f} CI={comparisons[arm]['paired_delta_ci95']}", flush=True)

    best_arm = max(("EXP-1", "EXP-2", "EXP-3"), key=lambda a: summaries[a]["dti"])
    best = summaries[best_arm]; cmpb = comparisons[best_arm]
    gates = {
        "beats_B0_point": bool(best["dti"] > summaries["B0"]["dti"]),
        "paired_ci_vs_B0_strictly_positive": bool(cmpb["paired_delta_ci95"][0] > 0),
        "beats_recorded_group_best_point": bool(best["dti"] > RECORDED_GROUP_BEST),
        "recorded_group_best": RECORDED_GROUP_BEST,
    }
    out = {"label": "HOLDOUT-DTI", "evaluator_version": "gems-segment-pooled-v1",
           "generated_utc": now(), "preregistration_sha256": sha256_file(ROOT / "evidence" / "preregistration.json"),
           "withheld_positives": summaries["B0"]["n_withheld_positive_pixels"],
           "budgets_per_fold": budgets, "fit_info": fit_info,
           "arms": {a: {"dti": summaries[a]["dti"], "ci95": summaries[a]["ci95"]["interval"],
                        "folds": summaries[a]["folds"]} for a in summaries},
           "paired_vs_B0": comparisons, "best_arm": best_arm, "gates": gates,
           "promote_scientific": bool(gates["paired_ci_vs_B0_strictly_positive"] and gates["beats_recorded_group_best_point"])}
    (ROOT / "evidence" / "holdout_experiments.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(f"[holdout] best={best_arm} promote_scientific={out['promote_scientific']}", flush=True)
    return out


def registry_rows(surface2d, dots, grid) -> list[dict]:
    from gems.novelty import dot_overlap, rank_correlation
    from scipy.stats import rankdata
    import rasterio
    reg = json.loads((ROOT / "registry" / "focus9_champions.json").read_text())
    cache = ROOT / ".cache" / "registry"
    s_fp = surface2d[grid.footprint].astype(np.float64)
    ranks = rankdata(s_fp)
    rows = []
    for e in reg["entries"]:
        p = cache / f"{e['site']}__{Path(e['path']).name}"
        with rasterio.open(p) as ds:
            a = ds.read(1)
        ref_dots = grid.footprint & np.isfinite(a) & (a > 0)
        rho = rank_correlation(ranks, a[grid.footprint].astype(np.float64))
        ov = dot_overlap(dots, ref_dots, radius_px=3.0)
        rows.append({"site": e["site"], "name": e["name"], "score_owner_reported": e["score_owner_reported"],
                     "surface_spearman": rho, "dot_overlap_within_3px": ov["candidate_within_3px_of_reference"],
                     "candidate_dots": ov["candidate_dots"], "reference_dots": ov["reference_dots"],
                     "duplicate": bool((rho is not None and abs(rho) > 0.90) or (ov["candidate_within_3px_of_reference"] or 0) > 0.70)})
        print(f"[registry] {e['site']}: rho={rho:.4f} overlap={ov['candidate_within_3px_of_reference']:.4f}", flush=True)
    return rows


def phase_final(store, grid, holdout_res: dict) -> dict:
    from gems.submission import scored_content_id, write_submission, zip_single
    from kanler3.emission import emit_dots
    from kanler3.gpc import GPC_FEATURE_NAMES
    from scipy.ndimage import distance_transform_edt
    from sklearn.ensemble import HistGradientBoostingClassifier

    prereg = json.loads((ROOT / "evidence" / "preregistration.json").read_text())
    best_arm = holdout_res["best_arm"]
    base59 = [n for n in store.names if n not in GPC_FEATURE_NAMES]
    if best_arm in ("EXP-1", "EXP-3"):
        names = base59 + list(GPC_FEATURE_NAMES)
    elif best_arm == "EXP-2":
        names = base59 + prereg["gpc_concordance_subset"]
    else:
        names = base59
    fp_flat, fp_pos = fp_mapping(grid)
    rng = np.random.default_rng(SEED)
    labels_flat = grid.labels.ravel()
    pos = fp_flat[labels_flat[fp_flat]]
    neg = fp_flat[~labels_flat[fp_flat]]
    if len(pos) > 50_000: pos = rng.choice(pos, 50_000, replace=False)
    if len(neg) > 300_000: neg = rng.choice(neg, 300_000, replace=False)
    tr = np.r_[pos, neg]
    print(f"[final] arm={best_arm} features={len(names)} pos={len(pos)} neg={len(neg)}", flush=True)
    model = HistGradientBoostingClassifier(**HGB)
    model.fit(store.rows(fp_pos[tr], names), labels_flat[tr].astype(np.int8))
    p_fp = predict_fp(model, store, names, np.arange(len(fp_flat)))
    surface = np.zeros(grid.footprint.shape, np.float32)
    surface.ravel()[fp_flat] = p_fp

    elig = grid.footprint.copy()
    if best_arm == "EXP-3":
        elig &= distance_transform_edt(~grid.labels) > 2
    dots = emit_dots(surface, elig, TOTAL_BUDGET)
    print(f"[final] dots={int(dots.sum())}", flush=True)

    rows = registry_rows(surface, dots, grid)
    uniq_ok = not any(r["duplicate"] for r in rows)

    cid = scored_content_id(dots.astype(np.float32), grid.footprint, grid.labels)
    date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"kanler3-gpc3-{best_arm.lower()}-{date}-{cid}"
    tif = ROOT / "docs" / "downloads" / f"{stem}-zeros.tif"
    template = ROOT / "data" / "raw" / "sample_submission.tif"
    write_submission(dots.astype(np.float32), template, tif, outside="zero")
    zip_path = zip_single(tif)
    tif_sha = sha256_file(tif)

    promote = bool(holdout_res["promote_scientific"] and uniq_ok)
    verdict = "promote" if promote else "negative"
    note = f"GPC-3 {best_arm} phase-concordance 37654d | HOLDOUT-DTI {holdout_res['arms'][best_arm]['dti']:.4f} | {'PROMOTE' if promote else 'NEGATIVE do not submit'}"
    assert len(note) <= 140, len(note)
    card = {
        "schema": "kanler3.run_card.v1", "generated_utc": now(),
        "hypothesis": prereg["hypothesis"], "mechanism": prereg["mechanism"],
        "named_non_fault_mimic": prereg["named_non_fault_mimic"],
        "holdout": {"label": "HOLDOUT-DTI", "evaluator_version": "gems-segment-pooled-v1",
                    "dti": holdout_res["arms"][best_arm]["dti"], "ci95": holdout_res["arms"][best_arm]["ci95"],
                    "withheld_positives": holdout_res["withheld_positives"],
                    "best_arm": best_arm, "all_arms": {a: holdout_res["arms"][a]["dti"] for a in holdout_res["arms"]},
                    "paired_vs_B0": holdout_res["paired_vs_B0"].get(best_arm)},
        "leaderboard_estimate": "NOT ESTIMABLE from holdout (different truth set); no projection is written as a score",
        "owner_reported_focus9_best": {"site": "GEMSDOE32", "score": 0.2778, "label": "OWNER-REPORTED"},
        "uniqueness_vs_focus9": rows, "unique_vs_focus9": uniq_ok,
        "raster_sha256": tif_sha, "content_id": cid, "dots": int(dots.sum()),
        "submission_name": stem, "submission_note": note, "note_chars": len(note),
        "tif": str(tif.relative_to(ROOT)), "zip": str(zip_path.relative_to(ROOT)),
        "verdict": verdict,
        "ok_to_submit": promote,
        "download_research": True,
    }
    (ROOT / "evidence" / "run_card.json").write_text(json.dumps(card, indent=2, default=float) + "\n")
    (ROOT / "docs" / "downloads" / f"{stem}.run-card.json").write_text(json.dumps(card, indent=2, default=float) + "\n")
    print(f"[final] verdict={verdict} tif={tif.name} sha={tif_sha[:16]}", flush=True)
    return card


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", choices=["canary", "holdout", "final", "all"], default="all")
    args = ap.parse_args()
    store, grid = build_store()
    print(f"[main] features={len(store.names)} n_fp={grid.n_fp}", flush=True)
    if args.phase in ("canary", "all"):
        c = phase_canary(store, grid)
        if not c["passed"]:
            print("[main] CANARY FAILED - stopping fail-closed", flush=True); return 2
    holdout_res = None
    if args.phase in ("holdout", "all"):
        holdout_res = phase_holdout(store, grid)
    if args.phase in ("final", "all"):
        if holdout_res is None:
            holdout_res = json.loads((ROOT / "evidence" / "holdout_experiments.json").read_text())
        phase_final(store, grid, holdout_res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
