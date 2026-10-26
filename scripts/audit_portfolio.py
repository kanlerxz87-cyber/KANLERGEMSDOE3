#!/usr/bin/env python3
"""Reopen pinned historical TIFFs and measure their geometry, not their scores.

This is a forensic comparison, not a new candidate or a registry clearance. It
checks nine named files plus two explicit witnesses; it does not pretend to be a
complete or current registry. Shared code supplies the 3 px disk and saturation
certificate. The historic files happen to be binary; tied-rank Spearman is the
binary phi coefficient. Invalid or nonbinary inputs cause the audit to stop.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from bootstrap import ROOT, INPUTS, ensure_template, sha256
from fetch_audit_inputs import PORTFOLIO_DIR


def binary_spearman(a: np.ndarray, b: np.ndarray, footprint: np.ndarray) -> float | None:
    """Exact Spearman on two nonconstant 0/1 masks with average tied ranks."""
    n = int(footprint.sum())
    na = int((a & footprint).sum())
    nb = int((b & footprint).sum())
    both = int((a & b & footprint).sum())
    den = math.sqrt(float(na) * (n - na) * nb * (n - nb))
    return (n * both - na * nb) / den if den else None


def duplicate_status(overlaps: list[float], correlations: list[float], expected: int) -> bool | None:
    """A failure can be proved by one pair; a pass requires every measurement."""
    if any(value > 0.70 for value in overlaps) or any(value > 0.90 for value in correlations):
        return True
    if len(overlaps) != expected or len(correlations) != expected:
        return None
    return False


def _verify_inputs() -> dict[str, dict]:
    entries = json.loads((ROOT / "data/audit_inputs.json").read_text())["files"]
    for entry in entries:
        p = INPUTS / entry["name"]
        if not p.exists() or p.stat().st_size != entry["bytes"] or sha256(p) != entry["sha256"]:
            raise RuntimeError(f"Missing or altered audit input: {entry['name']}")
    return {e["name"]: e for e in entries}


def _source_url(e: dict) -> str:
    return f"https://github.com/buffedlizard55-lab/{e['repo']}/blob/{e['ref']}/{e['path']}"


def run_audit() -> dict:
    inputs = _verify_inputs()
    template = ensure_template()
    sys.path.insert(0, str(template / "vendor"))
    from gems57.uniqueness import _near, saturation_certificate  # shared immutable implementation

    with rasterio.open(INPUTS / "sample_submission.tif") as ref:
        reference = ref.read(1)
        foot = np.isfinite(reference)
        grid = (ref.shape, ref.crs, ref.transform)
    if not foot.any():
        raise ValueError("Sample footprint is empty")
    with rasterio.open(INPUTS / "labels.tif") as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
            raise ValueError("Labels do not align to sample")
        cat = (src.read(1) > 0) & foot

    historic = json.loads((ROOT / "data/focus_sources.json").read_text())["rasters"]
    records: list[dict] = []
    masks: dict[str, np.ndarray] = {}
    for source in historic:
        name = source["repo"]
        path = PORTFOLIO_DIR / f"{name}.tif"
        if not path.is_file() or path.stat().st_size != source["bytes"] or sha256(path) != source["sha256"]:
            raise ValueError(f"Historical file missing or hash mismatch: {name}")
        with rasterio.open(path) as src:
            if src.count != 1 or src.dtypes[0] != "float32" or (src.shape, src.crs, src.transform) != grid:
                raise ValueError(f"Historical file does not match single-band float32 template: {name}")
            values = src.read(1)
        v = values[foot]
        if not np.isfinite(v).all() or not np.all((v == 0) | (v == 1)):
            raise ValueError(f"Historical file is non-finite or not binary inside footprint: {name}")
        mask = (values > 0) & foot
        masks[name] = mask
        content_hash = hashlib.sha256(np.ascontiguousarray(v, dtype="<f4").tobytes()).hexdigest()
        records.append({
            "site": name, "filename": Path(source["path"]).name,
            "reference_url": _source_url(source), "ref": source["ref"],
            "file_sha256": source["sha256"], "decoded_footprint_sha256": content_hash,
            "owner_reported_claim_not_receipt": source["owner_reported_claim"],
            "dots_in_footprint": int(mask.sum()), "inside_nonfinite": int((~np.isfinite(v)).sum()),
            "outside_positive": int(((values > 0) & ~foot).sum()),
            "whole_array_all_finite": bool(np.isfinite(values).all()),
            "grid_matches_mirror": True, "download_for_research_only": True,
            "leaderboard_estimate": None, "ok_to_submit": False,
        })

    names = [r["site"] for r in records]
    pairs = []
    # Only 9 dilations, rather than a separate distance transform for every pair.
    halos = {name: _near(masks[name]) for name in names}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ma, mb = masks[a], masks[b]
            a_n, b_n = int(ma.sum()), int(mb.sum())
            a_in_b = float(halos[b][ma].mean()) if a_n else None
            b_in_a = float(halos[a][mb].mean()) if b_n else None
            rho = binary_spearman(ma, mb, foot)
            pairs.append({"a": a, "b": b, "a_near_b_fraction": a_in_b,
                          "b_near_a_fraction": b_in_a, "spearman": rho,
                          "identical_footprint": bool(np.array_equal(ma, mb))})
    for row in records:
        site = row["site"]
        directed = []
        correlations = []
        for pair in pairs:
            if pair["a"] == site:
                directed.append((pair["a_near_b_fraction"], pair["b"]))
                correlations.append((pair["spearman"], pair["b"]))
            elif pair["b"] == site:
                directed.append((pair["b_near_a_fraction"], pair["a"]))
                correlations.append((pair["spearman"], pair["a"]))
        directed = [(v, n) for v, n in directed if v is not None]
        correlations = [(v, n) for v, n in correlations if v is not None]
        worst = max(directed, default=(None, None))
        largest_abs_rho = max(correlations, key=lambda x: abs(x[0]), default=(None, None))
        largest_rho = max(correlations, default=(None, None))
        row["max_directed_overlap_other_focus_site"] = worst[0]
        row["closest_other_focus_site"] = worst[1]
        row["max_abs_spearman_other_focus_site"] = abs(largest_abs_rho[0]) if largest_abs_rho[0] is not None else None
        row["max_spearman_other_focus_site"] = largest_rho[0]
        row["duplicate_in_nine_site_sample"] = duplicate_status(
            [v for v, _ in directed], [v for v, _ in correlations], len(names) - 1)
        # This is a historical dot comparison; a pre-placement surface was not obtained.
        row["preplacement_surface_test"] = "not available; not reconstructed from dots"

    dense = saturation_certificate(INPUTS / "17gems_eproba.tif", foot, expected_grid=grid)
    lattice = saturation_certificate(INPUTS / "lattice13.tif", foot, expected_grid=grid)
    for value, filename in ((dense, "17gems_eproba.tif"), (lattice, "lattice13.tif")):
        value["source"] = _source_url(inputs[filename])
        value["witness_file"] = filename
    n_uncovered = lattice["uncovered_allowed_pixels"]
    lattice["bound_for_37654_dot_candidate"] = max(0.0, 1.0 - n_uncovered / 37654)
    lattice["max_dots_that_could_pass_70pct_in_best_case"] = n_uncovered * 10 // 3

    d28, champion, anderson = masks["GEMSDOE25"], masks["GEMSDOE32"], masks["GEMSDOE36"]
    dcat = distance_transform_edt(~cat)
    pruned = d28 & (dcat > 2.0)
    h33_chain = {
        "d28_dots": int(d28.sum()), "champion_dots": int(champion.sum()),
        "d28_removed_by_2px_prune": int((d28 & ~pruned).sum()),
        "d28_pruned_vs_champion_xor_pixels": int(np.logical_xor(pruned, champion).sum()),
        "champion_not_in_anderson": int((champion & ~anderson).sum()),
        "anderson_added_to_champion": int((anderson & ~champion).sum()),
        "d28_gems25_gems30_identical": bool(np.array_equal(d28, masks["GEMSDOE30"])),
    }
    return {
        "schema": "historical-forensic-audit-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "REGISTRY-MEASUREMENT", "not_a_leaderboard_score": True,
        "scope": "Nine named historical files and two explicit witnesses only; not a complete or current registry.",
        "mirror_provenance": "Pinned owner mirrors; organizer authenticity and historical score-to-hash bindings unverified.",
        "template_commit": "07806249f4ed3efe70b4fbf866183c32392b7853",
        "sample_footprint_pixels": int(foot.sum()), "catalogue_pixels": int(cat.sum()),
        "sample_positive_pixels": int(((reference > 0) & foot).sum()),
        "sample_positive_equals_catalogue": bool(np.array_equal((reference > 0) & foot, cat)),
        "dense_witness": dense, "lattice_witness": lattice,
        "h33_lineage": h33_chain, "sites": records, "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/portfolio_audit.json")
    args = parser.parse_args()
    result = run_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.output}; witness blocks every nonempty candidate: {result['dense_witness']['universal_overlap_blocker']}")
    for row in result["sites"]:
        print(f"{row['site']}: {row['dots_in_footprint']} dots; nearest other {row['closest_other_focus_site']} "
              f"{row['max_directed_overlap_other_focus_site']:.2%}; submit NO")


if __name__ == "__main__":
    main()
