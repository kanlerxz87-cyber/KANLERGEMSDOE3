#!/usr/bin/env python3
"""CFRP lane experiments E1-E3 (preregistration: research/cfrp-20261028-preregistration.md).

Reuse, don't rebuild: SegmentHoldout + pooled DTI from src/gems/holdout.py,
ridge-NMS dotted emission from src/kanler3/emission.py, writer/validator from
src/gems/submission.py + scripts/validate_submission.py. Features are built
only from data/core/training_features.tif (19 raw bands); no catalogue-based
feature, no registry raster is read here.
"""
from __future__ import annotations
import gc, hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CACHE = ROOT / ".cache" / "cfrp"
SEED = 20261028


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------- features
def build_features():
    CACHE.mkdir(parents=True, exist_ok=True)
    meta_p = CACHE / "features.json"
    with rasterio.open(ROOT / "data/core/sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(ROOT / "data/core/labels.tif") as s:
        labels = (s.read(1) == 1) & foot
    if meta_p.exists():
        meta = json.loads(meta_p.read_text())
        if all((CACHE / f"{n}.npy").exists() for n in meta["names"]):
            return meta, foot, labels

    names: list[str] = []
    base_names: list[str] = []
    cfrp_names: list[str] = []

    def add(name, full, group):
        np.save(CACHE / f"{name}.npy", np.asarray(full[foot], dtype=np.float32))
        names.append(name)
        (base_names if group == "base" else cfrp_names).append(name)
        print(f"  feat {len(names):3d} {name}", flush=True)

    fields: dict[str, np.ndarray] = {}
    keep = {"rtp", "tmi", "iso_grav_anom", "det_elev", "iso_grav_anom_hg", "tmi_hg", "det_elev_slope"}
    with rasterio.open(ROOT / "data/core/training_features.tif") as s:
        band_names = [d.split(" - ")[0] for d in s.descriptions]
        for i, name in enumerate(band_names, 1):
            a = s.read(i).astype(np.float32)
            a[a < -1e30] = np.nan
            add(f"org_{name}", a, "base")
            if name in keep:
                fields[name] = a
    # context: gaussian mean + anomaly at sigma 3 for key bands
    for name in ("det_elev", "rtp", "iso_grav_anom", "tmi_hg", "det_elev_slope"):
        a = fields[name]
        filled = np.where(np.isfinite(a), a, np.nanmedian(a[foot])).astype(np.float32)
        g = gaussian_filter(filled, 3.0)
        add(f"ctx_{name}_g3", g, "base")
        add(f"ctx_{name}_anom3", filled - g, "base")
        del filled, g

    # ---- CFRP: Hessian ridge/saddle per field & scale, cross-field products
    def ridge_saddle(a, sigma):
        filled = np.where(np.isfinite(a), a, np.nanmedian(a[foot])).astype(np.float32)
        sm = gaussian_filter(filled, sigma)
        gy, gx = np.gradient(sm)
        hyy, hyx = np.gradient(gy)
        hxy, hxx = np.gradient(gx)
        hxy = 0.5 * (hxy + hyx)
        tmp = np.sqrt(((hxx - hyy) * 0.5) ** 2 + hxy ** 2)
        lam_min = 0.5 * (hxx + hyy) - tmp
        lam_max = 0.5 * (hxx + hyy) + tmp
        ridge = np.maximum(-lam_min, 0.0)
        saddle = np.sqrt(np.maximum(-lam_min, 0.0) * np.maximum(lam_max, 0.0))
        del filled, sm, gy, gx, hyy, hyx, hxy, hxx, tmp
        return ridge.astype(np.float32), saddle.astype(np.float32)

    def norm(x):
        s = np.percentile(x[foot], 99.0)
        return (x / s).astype(np.float32) if s > 0 else x.astype(np.float32)

    ridges: dict[tuple[str, float], np.ndarray] = {}
    for fname in ("rtp", "tmi", "iso_grav_anom", "det_elev"):
        per_scale = []
        for sigma in (1.5, 3.0, 6.0):
            r, sad = ridge_saddle(fields[fname], sigma)
            rn = norm(r)
            ridges[(fname, sigma)] = rn
            per_scale.append(rn)
            add(f"cfrp_ridge_{fname}_s{sigma:g}", rn, "cfrp")
            if sigma == 3.0:
                add(f"cfrp_saddle_{fname}_s3", norm(sad), "cfrp")
            del r, sad
            gc.collect()
        stack = np.stack(per_scale)
        add(f"cfrp_persist_min_{fname}", stack.min(0), "cfrp")
        add(f"cfrp_persist_mean_{fname}", stack.mean(0), "cfrp")
        del stack, per_scale
    # cross-field co-location at sigma 3 (magnetic vs gravity vs elevation)
    mag = np.maximum(ridges[("rtp", 3.0)], ridges[("tmi", 3.0)])
    grav = ridges[("iso_grav_anom", 3.0)]
    elev = ridges[("det_elev", 3.0)]
    add("cfrp_x_mag_grav_min", np.minimum(mag, grav), "cfrp")
    add("cfrp_x_mag_grav_prod", np.sqrt(np.maximum(mag, 0) * np.maximum(grav, 0)), "cfrp")
    add("cfrp_x_mag_elev_min", np.minimum(mag, elev), "cfrp")
    add("cfrp_x_grav_elev_min", np.minimum(grav, elev), "cfrp")
    add("cfrp_x_all3_min", np.minimum(np.minimum(mag, grav), elev), "cfrp")
    del mag, grav, elev, ridges, fields
    meta = {"names": names, "base": base_names, "cfrp": cfrp_names,
            "n_fp": int(foot.sum()), "shape": list(foot.shape)}
    meta_p.write_text(json.dumps(meta, indent=1) + "\n")
    return meta, foot, labels


class Store:
    def __init__(self, meta):
        self.names, self.n_fp = meta["names"], meta["n_fp"]

    def col(self, n):
        return np.load(CACHE / f"{n}.npy", mmap_mode="r")

    def rows(self, idx, names):
        out = np.empty((len(idx), len(names)), np.float32)
        for j, n in enumerate(names):
            out[:, j] = self.col(n)[idx]
        return out


def fit_predict(store, labels, foot, names, train_flat, valid_flat, fp_pos):
    from sklearn.ensemble import HistGradientBoostingClassifier
    rng = np.random.default_rng(SEED)
    lf = labels.ravel()
    pos = train_flat[lf[train_flat]]
    neg = train_flat[~lf[train_flat]]
    if len(pos) > 50_000: pos = rng.choice(pos, 50_000, replace=False)
    if len(neg) > 300_000: neg = rng.choice(neg, 300_000, replace=False)
    tr = np.r_[pos, neg]
    m = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.06, max_leaf_nodes=48,
                                       min_samples_leaf=200, l2_regularization=1.0,
                                       early_stopping=False, random_state=SEED)
    m.fit(store.rows(fp_pos[tr], names), lf[tr].astype(np.int8))
    out = np.empty(len(valid_flat), np.float32)
    idx = fp_pos[valid_flat]
    for s in range(0, len(idx), 400_000):
        out[s:s+400_000] = m.predict_proba(store.rows(idx[s:s+400_000], names))[:, 1]
    return out, {"n_pos": int(len(pos)), "n_neg": int(len(neg))}


def main():
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("phase", choices=["canary", "e1", "e2", "final"])
    args = ap.parse_args()
    t0 = time.time()
    meta, foot, labels = build_features()
    store = Store(meta)
    from gems.holdout import SegmentHoldout
    holdout = SegmentHoldout(foot, labels, buffer_px=15)
    fp_flat = np.flatnonzero(foot.ravel())
    fp_pos = np.full(foot.size, -1, np.int64); fp_pos[fp_flat] = np.arange(len(fp_flat))
    shape = foot.shape

    if args.phase == "canary":
        feats = {}
        for n in meta["cfrp"]:
            a = np.zeros(shape, np.float32); a[foot] = store.col(n); feats[n] = a
        res = holdout.canary(feats, seed=SEED)
        out = {"label": "LEAKAGE-CANARY", "evaluator_version": res["evaluator_version"],
               "generated_utc": now(), "passed": res["passed"], "features": res["features"],
               "threshold_two_polarity_auc": 0.90}
        (ROOT / "evidence/cfrp_canary_20261028.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
        worst = max(max(v["pooled_auc"], 1-v["pooled_auc"]) for v in res["features"].values())
        print(f"[canary] passed={res['passed']} worst_two_polarity_auc={worst:.4f}")
        return 0

    if args.phase == "e1":
        from kanler3.emission import emit_dots
        arms = {"BASE": meta["base"], "CFRP": meta["base"] + meta["cfrp"]}
        total_budget = 37_654
        budgets = [int(round(total_budget * int(f["valid"].sum()) / store.n_fp)) for f in holdout.folds]
        preds, surfaces = {}, {}
        for arm, names in arms.items():
            preds[arm], surfaces[arm] = [], []
            for fi, fold in enumerate(holdout.folds):
                sp = CACHE / f"e1_{arm}_fold{fi}.npy"; dp = CACHE / f"e1_{arm}_fold{fi}_dots.npy"
                valid_flat = np.flatnonzero(fold["valid"].ravel())
                if sp.exists():
                    surf = np.load(sp)
                else:
                    p, info = fit_predict(store, labels, foot, names,
                                          np.flatnonzero(fold["train"].ravel()), valid_flat, fp_pos)
                    surf = np.zeros(shape, np.float32); surf.ravel()[valid_flat] = p
                    np.save(sp, surf); print(f"[e1] {arm} fold{fi} fit {info}", flush=True)
                surfaces[arm].append(surf)
                if dp.exists():
                    dots = np.load(dp)
                else:
                    elig = fold["valid"] & (distance_transform_edt(~fold["visible"]) > 2)
                    dots = emit_dots(surf, elig, budgets[fi]).astype(np.uint8)
                    np.save(dp, dots)
                preds[arm].append(dots)
                print(f"[e1] {arm} fold {fold['name']} dots={int(dots.sum())}", flush=True)
        summ = {a: holdout.summarize([p.astype(np.uint8) for p in preds[a]]) for a in arms}
        paired = holdout.compare_paired([p.astype(np.uint8) for p in preds["CFRP"]],
                                        [p.astype(np.uint8) for p in preds["BASE"]])
        out = {"label": "HOLDOUT-DTI", "evaluator_version": "gems-segment-pooled-v1",
               "generated_utc": now(), "experiment": "E1", "budgets_per_fold": budgets,
               "withheld_positives": summ["BASE"]["n_withheld_positive_pixels"],
               "arms": {a: {"dti": summ[a]["dti"], "ci95": summ[a]["ci95"]["interval"], "folds": summ[a]["folds"]} for a in summ},
               "paired_CFRP_minus_BASE": paired,
               "promote_CFRP": bool(paired["ci95_strictly_positive"])}
        (ROOT / "evidence/cfrp_e1_holdout_20261028.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
        print(f"[e1] BASE={summ['BASE']['dti']:.5f} CFRP={summ['CFRP']['dti']:.5f} delta={paired['paired_delta_dti']:+.5f} CI={paired['paired_delta_ci95']} promote={out['promote_CFRP']}")
        return 0

    if args.phase == "e2":
        from kanler3.emission import emit_dots
        e1 = json.loads((ROOT / "evidence/cfrp_e1_holdout_20261028.json").read_text())
        arm = "CFRP" if e1["promote_CFRP"] else "BASE"
        variants = {"V1_b37654_collar2": (37_654, True), "V2_b44090_collar2": (44_090, True),
                    "V3_b37654_nocollar": (37_654, False), "V4_b30000_collar2": (30_000, True)}
        all_preds = {}
        for vname, (budget, collar) in variants.items():
            plist = []
            for fi, fold in enumerate(holdout.folds):
                surf = np.load(CACHE / f"e1_{arm}_fold{fi}.npy")
                fb = int(round(budget * int(fold["valid"].sum()) / store.n_fp))
                elig = fold["valid"] & (distance_transform_edt(~fold["visible"]) > 2) if collar else fold["valid"]
                plist.append(emit_dots(surf, elig, fb).astype(np.uint8))
            all_preds[vname] = plist
            s = holdout.summarize(plist)
            print(f"[e2] {vname}: HOLDOUT-DTI={s['dti']:.5f} CI={s['ci95']['interval']}", flush=True)
            all_preds[vname + "__summary"] = s
        out = {"label": "HOLDOUT-DTI", "evaluator_version": "gems-segment-pooled-v1",
               "generated_utc": now(), "experiment": "E2", "surface_arm": arm,
               "variants": {v: {"dti": all_preds[v+"__summary"]["dti"],
                                "ci95": all_preds[v+"__summary"]["ci95"]["interval"],
                                "withheld_positives": all_preds[v+"__summary"]["n_withheld_positive_pixels"]}
                            for v in variants}}
        best = max(variants, key=lambda v: out["variants"][v]["dti"])
        out["selected_variant"] = best
        out["selected_budget"], out["selected_collar"] = variants[best]
        (ROOT / "evidence/cfrp_e2_emission_20261028.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
        print(f"[e2] selected={best}")
        return 0

    if args.phase == "final":
        from kanler3.emission import emit_dots
        e1 = json.loads((ROOT / "evidence/cfrp_e1_holdout_20261028.json").read_text())
        e2 = json.loads((ROOT / "evidence/cfrp_e2_emission_20261028.json").read_text())
        names = meta["base"] + meta["cfrp"] if e1["promote_CFRP"] else meta["base"]
        budget, collar = int(e2["selected_budget"]), bool(e2["selected_collar"])
        all_flat = np.flatnonzero(foot.ravel())
        train_flat = all_flat  # final model: full visible catalogue (organizer-known labels)
        p, info = fit_predict(store, labels, foot, names, train_flat, all_flat, fp_pos)
        surf = np.zeros(shape, np.float32); surf[foot] = p
        np.save(CACHE / "final_surface.npy", surf)
        elig = foot & (distance_transform_edt(~labels) > 2) if collar else foot.copy()
        dots = emit_dots(surf, elig, budget)
        np.save(CACHE / "final_dots.npy", dots.astype(np.uint8))
        out = {"generated_utc": now(), "fit": info, "budget": budget, "collar_gt2px": collar,
               "dots": int(dots.sum()), "surface_sha256": sha256_file(CACHE / "final_surface.npy"),
               "note": "Binary 1.0 on emitted dots, 0.0 elsewhere inside footprint in zeros variant"}
        (ROOT / "evidence/cfrp_final_model_20261028.json").write_text(json.dumps(out, indent=1) + "\n")
        print(f"[final] dots={out['dots']} budget={budget} collar={collar}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
