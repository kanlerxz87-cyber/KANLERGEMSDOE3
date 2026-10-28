#!/usr/bin/env python3
"""Exact full-footprint geometry audit; NOT an evaluator or a score estimator.

Continuous-surface Spearman rank correlation and directed Euclidean <=3 pixel
preview/final-dot overlap are both required. Unknown is never treated as unique.
No sampling, resampling, file repair, placement, or model training occurs here.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import sha256_file, source_path


CORRELATION_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
RADIUS_PX = 3


def compare(surface: np.ndarray, dots: np.ndarray, reference: np.ndarray, footprint: np.ndarray, reference_dots: np.ndarray | None = None) -> dict:
    if len({x.shape for x in (surface, dots, reference, footprint)}) != 1 or surface.ndim != 2:
        raise ValueError("Identical two-dimensional grids are required; never silently resample")
    foot = np.asarray(footprint, dtype=bool)
    if not foot.any() or not np.isfinite(surface[foot]).all() or not np.isfinite(reference[foot]).all():
        raise ValueError("Nonempty footprint and finite in-footprint surfaces required")
    if not np.isfinite(dots[foot]).all() or not np.isin(dots[foot], (0, 1)).all():
        raise ValueError("Dots must be a finite binary preview/final mask, not a threshold invented by this audit")
    if reference_dots is None:
        if not np.isin(reference[foot], (0, 1)).all():
            raise ValueError("A non-binary registry surface requires its explicit companion dot mask; positive probability is not a dot")
        reference_dots = reference
    if reference_dots.shape != foot.shape or not np.isfinite(reference_dots[foot]).all() or not np.isin(reference_dots[foot], (0, 1)).all():
        raise ValueError("Registry companion dots must be finite binary values on the exact grid")
    a = np.asarray(dots, dtype=bool) & foot
    b = np.asarray(reference_dots, dtype=bool) & foot
    if not a.any() or not b.any():
        raise ValueError("Empty candidate/reference dots are not evidence of novelty")
    ra = rankdata(surface[foot], method="average")
    rb = rankdata(reference[foot], method="average")
    if np.ptp(ra) == 0 or np.ptp(rb) == 0:
        rho = None
    else:
        ra -= ra.mean()
        rb -= rb.mean()
        rho = float(np.dot(ra, rb) / math.sqrt(float(np.dot(ra, ra) * np.dot(rb, rb))))
        rho = float(np.clip(rho, -1.0, 1.0))
    distance = distance_transform_edt(~b)
    directed = float((distance[a] <= RADIUS_PX).mean())
    reverse = float((distance_transform_edt(~a)[b] <= RADIUS_PX).mean())
    duplicate = directed > OVERLAP_LIMIT or (rho is not None and rho > CORRELATION_LIMIT)
    return {"rank_correlation": rho, "directed_dot_overlap_3px": directed, "reverse_dot_overlap_3px": reverse, "candidate_dots": int(a.sum()), "reference_dots": int(b.sum()), "duplicate": duplicate, "comparable": rho is not None, "measurement_class": "GEOMETRIC_AUDIT_NOT_SCORE"}


def decision(rows: list[dict], registry_complete: bool, expected_count: int) -> dict:
    duplicate = any(isinstance(row, dict) and row.get("duplicate") is True for row in rows)
    complete = registry_complete is True and type(expected_count) is int and len(rows) == expected_count and expected_count > 0 and all(isinstance(row, dict) and row.get("comparable") is True and type(row.get("duplicate")) is bool for row in rows)
    return {"status": "STOP_DUPLICATE" if duplicate else "PASS_SCOPED_REGISTRY" if complete else "BLOCKED_INCOMPLETE_REGISTRY", "unique_under_protocol": bool(complete and not duplicate), "registry_complete": complete, "slot_authorized": False}


def raster(path: Path, template: Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(template) as ref, rasterio.open(path) as src:
        if src.count != 1 or src.shape != ref.shape or src.crs is None or src.crs != ref.crs or src.transform != ref.transform:
            raise ValueError(f"Raster grid mismatch: {path}")
        foot = (ref.dataset_mask() > 0) & np.isfinite(ref.read(1))
        values = src.read(1)
        if not (src.dataset_mask()[foot] > 0).all():
            raise ValueError(f"Missing in-footprint values: {path}")
        return values, foot



def registry_entries(manifest: dict) -> list[dict]:
    """Validate the declared inventory; never infer global completeness from it."""
    if not isinstance(manifest, dict) or type(manifest.get("complete")) is not bool:
        raise ValueError("Registry must declare a literal boolean complete flag")
    count = manifest.get("expected_count")
    if type(count) is not int or count <= 0:
        raise ValueError("Registry expected_count must be a positive integer")
    rows = manifest.get("rasters")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Nonempty raster inventory required")
    ids, paths = set(), set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip():
            raise ValueError("Every registry raster needs a nonempty identity")
        if row["id"] in ids:
            raise ValueError("Duplicate registry ID: " + row["id"])
        ids.add(row["id"])
        for path_key, hash_key in (("path", "sha256"), ("dots_path", "dots_sha256")):
            if path_key == "dots_path" and row.get(path_key) is None and row.get(hash_key) is None:
                continue
            if not isinstance(row.get(path_key), str) or not isinstance(row.get(hash_key), str) or not re.fullmatch(r"[0-9a-f]{64}", row[hash_key]):
                raise ValueError("Every registry file/companion needs a relative path and SHA-256")
            member = Path(source_path(row[path_key]))
            if member.suffix.lower() not in (".tif", ".tiff"):
                raise ValueError("Registry paths must identify GeoTIFF files")
            if path_key == "path":
                if member.as_posix() in paths:
                    raise ValueError("Repeated registry file path")
                paths.add(member.as_posix())
    return rows


def member_path(manifest_path: Path, name: str) -> Path:
    path = (manifest_path.parent / source_path(name)).resolve()
    if not path.is_relative_to(manifest_path.parent.resolve()):
        raise ValueError("Registry member symlink escapes its inventory directory")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", type=Path, required=True)
    parser.add_argument("--dots", type=Path, required=True, help="Explicit preview dots before writing, or exact final dots")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True, help="JSON: complete, expected_count, rasters:[id,path,sha256]")
    parser.add_argument("--stage", choices=["surface-before-writer", "final-dots"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.registry.read_text())
    entries = registry_entries(manifest)
    surface, foot = raster(args.surface, args.template)
    dots, _ = raster(args.dots, args.template)
    rows = []
    for entry in entries:
        path = member_path(args.registry, entry["path"])
        if sha256_file(path) != entry["sha256"]:
            raise ValueError("Registry hash mismatch: " + entry["id"])
        reference, _ = raster(path, args.template)
        reference_dots = None
        if entry.get("dots_path") is not None:
            dots_path = member_path(args.registry, entry["dots_path"])
            if sha256_file(dots_path) != entry.get("dots_sha256"):
                raise ValueError("Registry companion-dot hash mismatch: " + entry["id"])
            reference_dots, _ = raster(dots_path, args.template)
        rows.append({"id": entry["id"], "sha256": entry["sha256"], **compare(surface, dots, reference, foot, reference_dots)})
    result = {"kind": "GEOMETRIC_AUDIT_NOT_SCORE", "stage": args.stage, "registry_manifest_sha256": sha256_file(args.registry), "surface_sha256": sha256_file(args.surface), "dots_sha256": sha256_file(args.dots), "template_sha256": sha256_file(args.template), "comparisons": rows, **decision(rows, manifest.get("complete"), manifest.get("expected_count", -1))}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["unique_under_protocol"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc), "unique_under_protocol": False}), file=sys.stderr)
        raise SystemExit(2)
