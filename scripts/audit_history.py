#!/usr/bin/env python3
"""Audit pinned historical rasters; never create a new submission or infer scores.

Downloads only the nine historical references and one calibration lattice for
research into an ignored cache. Each file is hash-verified before use. Comparisons
are directional: fraction of a candidate's positive pixels within 3 pixels of each
other reference. This is a historical subset, NOT the full current registry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_entry(entry: dict, cache: Path, *, offline: bool = False) -> Path:
    """Get immutable GitHub bytes through gh, verify SHA, and atomically cache them."""
    target = cache / entry["site"] / Path(entry["path"]).name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and sha256_file(target) == entry["sha256"]:
        return target
    if offline:
        raise ValueError(f"missing or corrupt offline reference: {target}")
    repo = f"buffedlizard55-lab/{entry['repo']}"
    endpoint = f"repos/{repo}/contents/{entry['path']}?ref={entry['ref']}"
    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".partial", delete=False) as fh:
            tmp = Path(fh.name)
            subprocess.run(
                ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"],
                stdout=fh, check=True, timeout=180,
            )
        actual = sha256_file(tmp)
        if actual != entry["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {entry['site']}: {actual}")
        os.replace(tmp, target)
        return target
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def disk(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return x * x + y * y <= radius * radius


def phi_binary(a: np.ndarray, b: np.ndarray) -> float | None:
    """Spearman correlation for two binary arrays with average tied ranks."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if a.shape != b.shape:
        raise ValueError("shape mismatch")
    n11 = int(np.count_nonzero(a & b))
    n10 = int(np.count_nonzero(a & ~b))
    n01 = int(np.count_nonzero(~a & b))
    n00 = int(a.size) - n11 - n10 - n01
    denom = math.sqrt(float(n11 + n10) * float(n01 + n00) *
                      float(n11 + n01) * float(n10 + n00))
    return float((n11 * n00 - n10 * n01) / denom) if denom else None


def read_mask(path: Path, template: dict, foot: np.ndarray) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        if (ds.count != 1 or ds.shape != template["shape"] or ds.crs != template["crs"]
                or ds.transform != template["transform"]):
            raise ValueError(f"grid mismatch: {path}")
        arr = ds.read(1)
        inside = arr[foot]
        if not np.isfinite(inside).all() or not np.all((inside == 0) | (inside == 1)):
            raise ValueError(f"historical audit requires finite binary values inside footprint: {path}")
        mask = np.zeros(foot.shape, dtype=bool)
        mask[foot] = inside > 0
        return mask, {
            "sha256": sha256_file(path),
            "positive_pixels": int(mask.sum()),
            "in_footprint_mask_sha256": hashlib.sha256(np.packbits(mask[foot]).tobytes()).hexdigest(),
            "inside_binary_finite": True,
            "grid_matches_owner_mirror": True,
        }


def audit(manifest: dict, sample_path: Path, label_path: Path, cache: Path, *, offline: bool = False) -> dict:
    if sha256_file(sample_path) != manifest["sample_submission_sha256"]:
        raise ValueError("sample mirror hash mismatch")
    if sha256_file(label_path) != manifest["label_sha256"]:
        raise ValueError("labels mirror hash mismatch")
    with rasterio.open(sample_path) as ds:
        foot = np.isfinite(ds.read(1))
        template = {"shape": ds.shape, "crs": ds.crs, "transform": ds.transform}
        sample_positive = (ds.read(1) > 0) & foot
    with rasterio.open(label_path) as ds:
        if ds.shape != template["shape"] or ds.crs != template["crs"] or ds.transform != template["transform"]:
            raise ValueError("label grid mismatch")
        labels = (ds.read(1) > 0) & foot
    masks: dict[str, np.ndarray] = {}
    metadata: dict[str, dict] = {}
    for entry in manifest["rows"]:
        local = fetch_entry(entry, cache, offline=offline)
        masks[entry["site"]], metadata[entry["site"]] = read_mask(local, template, foot)
    local = fetch_entry(manifest["lattice"], cache, offline=offline)
    lattice, lattice_meta = read_mask(local, template, foot)
    dilation = disk(3)
    comparisons: dict[str, list[dict]] = {key: [] for key in masks}
    for other, other_mask in masks.items():
        nearby = binary_dilation(other_mask, structure=dilation)
        b = other_mask[foot]
        for site, candidate in masks.items():
            if site == other:
                continue
            count = int(candidate.sum())
            overlap = float(np.count_nonzero(candidate & nearby) / count) if count else None
            correlation = phi_binary(candidate[foot], b)
            comparisons[site].append({"other_site": other, "within_3px_fraction": overlap,
                                      "binary_spearman": correlation,
                                      "exact_mask_equal": bool(np.array_equal(candidate, other_mask))})
    rows = []
    for entry in manifest["rows"]:
        site = entry["site"]
        other = comparisons[site]
        worst_overlap = max(other, key=lambda x: x["within_3px_fraction"] if x["within_3px_fraction"] is not None else -1)
        defined_rho = [x for x in other if x["binary_spearman"] is not None]
        max_rho = max(defined_rho, key=lambda x: abs(x["binary_spearman"])) if defined_rho else None
        rows.append({**entry, **metadata[site], "comparisons": other,
                     "max_within_3px": worst_overlap["within_3px_fraction"],
                     "max_within_3px_site": worst_overlap["other_site"],
                     "max_abs_binary_spearman": abs(max_rho["binary_spearman"]) if max_rho else None,
                     "max_abs_binary_spearman_site": max_rho["other_site"] if max_rho else None,
                     "exact_mask_alias_sites": [x["other_site"] for x in other if x["exact_mask_equal"]],
                     "passes_nine_site_final_dot_threshold": bool(
                         worst_overlap["within_3px_fraction"] is not None and
                         worst_overlap["within_3px_fraction"] <= .70 and
                         max_rho is not None and abs(max_rho["binary_spearman"]) <= .90)})
    lattice_near = binary_dilation(lattice, structure=dilation)
    uncovered = int(np.count_nonzero(foot & ~lattice_near))
    h33, d28, r1, h36 = (masks[k] for k in ("GEMSDOE32", "GEMSDOE25", "GEMSDOE31", "GEMSDOE36"))
    dist = distance_transform_edt(~labels)
    lineage = {
        "d28_dots": int(d28.sum()), "r1_dots": int(r1.sum()), "h33_dots": int(h33.sum()),
        "r1_equals_d28_with_catalogue_distance_gt_1px": bool(np.array_equal(r1, d28 & (dist > 1))),
        "h33_equals_d28_with_catalogue_distance_gt_2px": bool(np.array_equal(h33, d28 & (dist > 2))),
        "h33_minus_d28": int(np.count_nonzero(h33 & ~d28)),
        "d28_minus_h33": int(np.count_nonzero(d28 & ~h33)),
        "h33_minus_gems36": int(np.count_nonzero(h33 & ~h36)),
        "gems36_minus_h33": int(np.count_nonzero(h36 & ~h33)),
    }
    n_foot = int(foot.sum())
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Nine pinned historical files and one pinned lattice; not a full registry or pre-placement audit.",
        "score_provenance": "Historical claims are USER-REPORTED and lack a byte-bound organizer receipt. They are not verified scores or forecasts.",
        "template_sha256": manifest["sample_submission_sha256"],
        "template_authenticity": "owner mirror hash-verified, not organizer-authenticated",
        "footprint_pixels": n_foot,
        "sample_positive_pixels": int(sample_positive.sum()),
        "label_positive_pixels": int(labels.sum()),
        "sample_positive_equals_labels": bool(np.array_equal(sample_positive, labels)),
        "rows": rows,
        "lattice": {**manifest["lattice"], **lattice_meta,
                    "within_3px_footprint_pixels": int(np.count_nonzero(foot & lattice_near)),
                    "within_3px_footprint_fraction": 1.0 - uncovered / n_foot,
                    "uncovered_footprint_pixels": uncovered,
                    "necessary_upper_bound_dots_for_literal_70pct": math.floor(uncovered / .30),
                    "upper_bound_caveat": "Necessary, not sufficient; assumes each dot occupies a distinct footprint pixel and ignores every other registry raster."},
        "lineage": lineage,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/historical-manifest.json")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/history")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/concurrent-main/observatory-portfolio-audit.json")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    result = audit(json.loads(args.manifest.read_text()), args.sample, args.labels, args.cache, offline=args.offline)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Audited {len(result['rows'])} pinned historical rasters; wrote {args.out}")
    print(f"Lattice within 3px of {result['lattice']['within_3px_footprint_fraction']:.5%} of footprint; "
          f"necessary upper bound {result['lattice']['necessary_upper_bound_dots_for_literal_70pct']} dots")


if __name__ == "__main__":
    main()
