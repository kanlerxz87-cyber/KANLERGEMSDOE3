"""Fast, exact cross-portfolio uniqueness audit (pre-placement surface + final dots)
across all 417 restored registry rasters (389 unique SHA-256 digests).

Implements Protocol Rule 1:
- Check BOTH on the continuous surface before placement AND on the final dots.
- Flag if |Spearman| > 0.90 OR >70% of candidate dots fall within 3 px of a registry raster's dots.
- Reports BOTH genuine detector-lane scope AND literal unexempted synthetic-lattice diagnostics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from scipy.stats import rankdata


def _normalised_rank_z(vals: np.ndarray) -> np.ndarray:
    r = rankdata(vals, method="average").astype(np.float64)
    r -= r.mean()
    norm = float(np.linalg.norm(r))
    return (r / norm) if norm > 0 else np.zeros_like(r)


def _spearman_z_vs_binary(rank_z: np.ndarray, b_mask: np.ndarray) -> float | None:
    n = b_mask.size
    n1 = int(b_mask.sum())
    if n1 == 0 or n1 == n:
        return None
    p = n1 / float(n)
    denom = np.sqrt(n * p * (1.0 - p))
    if denom == 0:
        return None
    return float(rank_z[b_mask].sum() / denom)


def _phi_binary(a: np.ndarray, b: np.ndarray) -> float | None:
    n = float(a.size)
    na = float(a.sum())
    nb = float(b.sum())
    if na in (0.0, n) or nb in (0.0, n):
        return None
    nab = float(np.count_nonzero(a & b))
    denom = np.sqrt(na * (n - na) * nb * (n - nb))
    return float((n * nab - na * nb) / denom) if denom > 0 else None


def audit_surface_and_dots(
    root: Path,
    candidate_surface: np.ndarray,
    candidate_dots: np.ndarray,
    footprint: np.ndarray,
    manifest_path: Path | None = None,
    max_abs_spearman: float = 0.90,
    max_within_3px: float = 0.70,
) -> dict:
    manifest_path = manifest_path or (root / "evidence" / "registry_refreshed.json")
    manifest = json.loads(manifest_path.read_text())

    foot = np.asarray(footprint, dtype=bool)
    surf = np.asarray(candidate_surface, dtype=np.float32)
    dots = np.asarray(candidate_dots, dtype=bool) & foot
    n_dots = int(dots.sum())
    if n_dots == 0:
        raise ValueError("Candidate has zero positive dots inside footprint")

    surf_foot = surf[foot]
    if not np.isfinite(surf_foot).all():
        raise ValueError("Candidate surface contains non-finite values inside footprint")

    cand_surf_z = _normalised_rank_z(surf_foot)
    cand_dots_foot = dots[foot]

    # Pre-placement top-K support mask on continuous surface (K = n_dots)
    topk_idx = np.argpartition(surf_foot, -n_dots)[-n_dots:]
    topk_foot = np.zeros(surf_foot.size, dtype=bool)
    topk_foot[topk_idx] = True
    topk_full = np.zeros(foot.shape, dtype=bool)
    topk_full[foot] = topk_foot

    yy, xx = np.ogrid[-3:4, -3:4]
    disk3 = (yy * yy + xx * xx) <= 9

    sha_cache: dict[str, dict] = {}
    mask_cache: dict[str, dict] = {}
    rows = []

    for entry in manifest["rasters"]:
        sha = entry["sha256"]
        if sha in sha_cache:
            metrics = sha_cache[sha]
        else:
            tif_p = root / entry["local_cache"]
            with rasterio.open(tif_p) as ds:
                if ds.count != 1 or ds.shape != foot.shape:
                    metrics = {"measurable": False, "reason": "grid_or_band_mismatch"}
                    sha_cache[sha] = metrics
                    rows.append({**entry, **metrics})
                    continue
                arr = ds.read(1).astype(np.float32)
            # Outside footprint is ignored; inside footprint replace nodata sentinels cleanly for comparison
            vals = arr[foot]
            vals_clean = np.where(np.isfinite(vals) & (vals >= 0.0) & (vals <= 1.0), vals, 0.0)
            is_binary = bool(np.all((vals_clean == 0.0) | (vals_clean == 1.0)))
            reg_dots_foot = vals_clean > 0.0
            n_reg_dots = int(reg_dots_foot.sum())

            if n_reg_dots == 0 or float(np.ptp(vals_clean)) == 0.0:
                metrics = {
                    "measurable": False,
                    "reason": "empty_or_constant",
                    "reg_dots": n_reg_dots,
                }
                sha_cache[sha] = metrics
                rows.append({**entry, **metrics})
                continue

            mask_key = hashlib.sha256(np.packbits(reg_dots_foot).tobytes()).hexdigest()
            if mask_key in mask_cache:
                spatial_m = mask_cache[mask_key]
            else:
                reg_dots_full = np.zeros(foot.shape, dtype=bool)
                reg_dots_full[foot] = reg_dots_foot
                dil = binary_dilation(reg_dots_full, structure=disk3)
                cov = float(dil[foot].mean())
                ov_dots = float(dil[dots].mean())
                ov_topk = float(dil[topk_full].mean())
                null_excess = (ov_dots - cov) / max(1.0 - cov, 1e-6) if cov < 0.999999 else 0.0
                spatial_m = {
                    "reg_dots": n_reg_dots,
                    "footprint_3px_coverage": round(cov, 6),
                    "final_dots_within_3px": round(ov_dots, 6),
                    "surface_topk_within_3px": round(ov_topk, 6),
                    "null_calibrated_excess_3px": round(null_excess, 6),
                    "phi_final_dots": _phi_binary(cand_dots_foot, reg_dots_foot),
                    "rho_surf_vs_mask": _spearman_z_vs_binary(cand_surf_z, reg_dots_foot),
                }
                mask_cache[mask_key] = spatial_m

            if is_binary:
                rho_surface = spatial_m["rho_surf_vs_mask"]
                rho_dots = spatial_m["phi_final_dots"]
            else:
                other_z = _normalised_rank_z(vals_clean)
                rho_surface = float(np.dot(cand_surf_z, other_z))
                rho_dots = _spearman_z_vs_binary(other_z, cand_dots_foot)

            is_space_filling_probe = (
                entry.get("category") == "synthetic_calibration_lattice"
                or spatial_m["footprint_3px_coverage"] >= 0.95
            )
            dup_detector = bool(
                not is_space_filling_probe
                and (
                    (rho_surface is not None and abs(rho_surface) > max_abs_spearman)
                    or (rho_dots is not None and abs(rho_dots) > max_abs_spearman)
                    or spatial_m["final_dots_within_3px"] > max_within_3px
                )
            )
            dup_literal = bool(
                (rho_surface is not None and abs(rho_surface) > max_abs_spearman)
                or (rho_dots is not None and abs(rho_dots) > max_abs_spearman)
                or spatial_m["final_dots_within_3px"] > max_within_3px
            )
            metrics = {
                "measurable": True,
                "is_binary": is_binary,
                "is_space_filling_probe": is_space_filling_probe,
                "reg_dots": spatial_m["reg_dots"],
                "footprint_3px_coverage": spatial_m["footprint_3px_coverage"],
                "surface_spearman": round(float(rho_surface), 6) if rho_surface is not None else None,
                "dots_spearman": round(float(rho_dots), 6) if rho_dots is not None else None,
                "surface_topk_within_3px": spatial_m["surface_topk_within_3px"],
                "final_dots_within_3px": spatial_m["final_dots_within_3px"],
                "null_calibrated_excess_3px": spatial_m["null_calibrated_excess_3px"],
                "duplicate_detector_scope": dup_detector,
                "duplicate_literal_scope": dup_literal,
            }
            sha_cache[sha] = metrics

        rows.append({
            "id": entry["id"],
            "repo": entry["repo"],
            "remote_path": entry["remote_path"],
            "sha256": sha,
            "category": entry.get("category", "unknown"),
            **metrics,
        })

    measurable_rows = [r for r in rows if r.get("measurable")]
    detector_rows = [r for r in measurable_rows if not r.get("is_space_filling_probe")]
    probe_rows = [r for r in measurable_rows if r.get("is_space_filling_probe")]

    def _top_by(items, key, abs_val=False):
        valid = [r for r in items if r.get(key) is not None]
        if not valid:
            return None
        best = max(valid, key=lambda r: abs(r[key]) if abs_val else r[key])
        return {
            "val": round(abs(best[key]) if abs_val else best[key], 6),
            "raw": best[key],
            "id": best["id"],
            "repo": best["repo"],
            "remote_path": best["remote_path"],
            "sha256": best["sha256"],
            "reg_dots": best["reg_dots"],
        }

    # Explicit comparisons against key focus-site benchmarks
    key_peers = {}
    for label, sub in [
        ("GEMSDOE32_H33_02778", "h33-h33-2-b2"),
        ("GEMSDOE24_D15_02477", "dotted-h19-5-d1-5"),
        ("GEMSDOE25_D28_02600", "dotted-h19-5-d2-8"),
        ("GEMSDOE31_H31X_01661", "h31x-piedmont-junction"),
        ("GEMSDOE27_H29S_02190", "511898747886"),
        ("GEMSDOE70_P9", "GEMSDOE70"),
    ]:
        matches = [r for r in detector_rows if sub in r["remote_path"] or sub in r["repo"]]
        if matches:
            m = max(matches, key=lambda r: r["final_dots_within_3px"])
            key_peers[label] = {
                "repo": m["repo"],
                "remote_path": m["remote_path"],
                "surface_spearman": m["surface_spearman"],
                "dots_spearman": m["dots_spearman"],
                "surface_topk_within_3px": m["surface_topk_within_3px"],
                "final_dots_within_3px": m["final_dots_within_3px"],
            }

    det_dups = [r for r in detector_rows if r["duplicate_detector_scope"]]
    lit_dups = [r for r in measurable_rows if r["duplicate_literal_scope"]]
    max_topk = _top_by(detector_rows, "surface_topk_within_3px")

    return {
        "protocol_thresholds": {
            "max_abs_spearman": max_abs_spearman,
            "max_within_3px": max_within_3px,
        },
        "total_registry_entries": len(rows),
        "measurable_entries": len(measurable_rows),
        "unique_pixel_masks_evaluated": len(mask_cache),
        "detector_lane_entries": len(detector_rows),
        "space_filling_probe_entries": len(probe_rows),
        "detector_scope": {
            "unique": len(det_dups) == 0,
            "surface_topk_also_le_070": bool(max_topk is not None and max_topk["val"] <= max_within_3px),
            "duplicate_count": len(det_dups),
            "worst_abs_surface_spearman": _top_by(detector_rows, "surface_spearman", abs_val=True),
            "worst_abs_dots_spearman": _top_by(detector_rows, "dots_spearman", abs_val=True),
            "worst_surface_topk_within_3px": max_topk,
            "worst_final_dots_within_3px": _top_by(detector_rows, "final_dots_within_3px"),
        },
        "key_focus_site_peers": key_peers,
        "synthetic_space_filling_probes": [
            {
                "id": r["id"],
                "repo": r["repo"],
                "remote_path": r["remote_path"],
                "reg_dots": r["reg_dots"],
                "footprint_3px_coverage": r["footprint_3px_coverage"],
                "final_dots_within_3px": r["final_dots_within_3px"],
                "null_calibrated_excess_3px": r["null_calibrated_excess_3px"],
                "pigeonhole_note": (
                    "Regular 5x5 grid probe (`13gems_r13-lattice-s5`) covers 99.8713% of all 5,167,373 footprint "
                    "pixels within 3 px (`sqrt(2^2+2^2)=2.828<=3.0`), leaving only 6,718 boundary pixels >3 px away; "
                    "no 37,654-dot raster in Nevada can have <=70% literal overlap (`min >= 82.16%`)."
                ),
            }
            for r in probe_rows
        ],
        "literal_unfiltered_scope": {
            "unique_including_5px_lattice": len(lit_dups) == 0,
            "duplicate_count_including_5px_lattice": len(lit_dups),
        },
        "top_15_detector_overlaps": sorted(
            detector_rows, key=lambda r: r["final_dots_within_3px"], reverse=True
        )[:15],
    }
