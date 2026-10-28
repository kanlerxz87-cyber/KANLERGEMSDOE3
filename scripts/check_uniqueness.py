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
import os
import re
import sys
import tempfile
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
    duplicate = any(row.get("duplicate") is True for row in rows)
    complete = registry_complete is True and type(expected_count) is int and len(rows) == expected_count and expected_count > 0 and all(row.get("comparable") is True for row in rows)
    return {"status": "STOP_DUPLICATE" if duplicate else "PASS_SCOPED_REGISTRY" if complete else "BLOCKED_INCOMPLETE_REGISTRY", "unique_under_protocol": bool(complete and not duplicate), "registry_complete": complete, "slot_authorized": False}


def raster(path: Path, template: Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(template) as ref, rasterio.open(path) as src:
        if ref.count != 1 or ref.crs is None:
            raise ValueError("Uniqueness template must be a single-band georeferenced raster")
        # A sidecar mask changes the pixels being compared without changing the
        # pinned TIFF hash. Require the mask to be contained in the TIFF bytes.
        for dataset, main in ((ref, template), (src, path)):
            if any(Path(name).resolve() != main.resolve() for name in dataset.files):
                raise ValueError(f"Raster has an unhashed sidecar: {main}")
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


def audit_registry(surface_path: Path, dots_path: Path, template_path: Path,
                   registry_path: Path, stage: str) -> dict:
    """Reopen and compare exact saved rasters. Stop at the first duplicate.

    A declared complete manifest is only a scoped inventory, not independent
    proof that every prior submission has been enumerated. This function never
    grants a slot. Callers can reuse it to replay both stages before selection.
    """
    if stage not in ("surface-before-writer", "final-dots"):
        raise ValueError("Unknown uniqueness stage")
    surface_path, dots_path, template_path, registry_path = map(
        Path, (surface_path, dots_path, template_path, registry_path))
    manifest_hash = sha256_file(registry_path)
    manifest = json.loads(registry_path.read_text())
    entries = registry_entries(manifest)
    hashes = {"surface_sha256": sha256_file(surface_path),
              "dots_sha256": sha256_file(dots_path),
              "template_sha256": sha256_file(template_path)}
    if stage == "final-dots" and hashes["surface_sha256"] != hashes["dots_sha256"]:
        raise ValueError("Final-dot rank correlation must use the exact final dot raster")
    surface, foot = raster(surface_path, template_path)
    dots, _ = raster(dots_path, template_path)
    rows = []
    for entry in entries:
        path = member_path(registry_path, entry["path"])
        if sha256_file(path) != entry["sha256"]:
            raise ValueError("Registry hash mismatch: " + entry["id"])
        reference, _ = raster(path, template_path)
        reference_dots = None
        companion_path = None
        if entry.get("dots_path") is not None:
            companion_path = member_path(registry_path, entry["dots_path"])
            if sha256_file(companion_path) != entry["dots_sha256"]:
                raise ValueError("Registry companion-dot hash mismatch: " + entry["id"])
            reference_dots, _ = raster(companion_path, template_path)
        row = {"id": entry["id"], "sha256": entry["sha256"],
               **compare(surface, dots, reference, foot, reference_dots)}
        if companion_path is not None:
            row["dots_sha256"] = entry["dots_sha256"]
        # Do not attest to arrays read from bytes that changed during the audit.
        if sha256_file(path) != entry["sha256"] or (
                companion_path is not None and sha256_file(companion_path) != entry["dots_sha256"]):
            raise ValueError("Registry file changed during audit: " + entry["id"])
        rows.append(row)
        if row["duplicate"]:
            break
    for path, key in ((surface_path, "surface_sha256"), (dots_path, "dots_sha256"),
                      (template_path, "template_sha256")):
        if sha256_file(path) != hashes[key]:
            raise ValueError("Candidate or template changed during uniqueness audit")
    if sha256_file(registry_path) != manifest_hash:
        raise ValueError("Registry manifest changed during uniqueness audit")
    return {"kind": "GEOMETRIC_AUDIT_NOT_SCORE", "stage": stage,
            "registry_manifest_sha256": manifest_hash, **hashes,
            "registry_entries_declared": len(entries), "registry_entries_compared": len(rows),
            "comparisons": rows,
            **decision(rows, manifest.get("complete"), manifest.get("expected_count", -1))}


def safe_output_path(out: Path, primary_inputs: tuple[Path, ...], registry: Path) -> None:
    """Never overwrite an input, even if an output aliases it through a symlink."""
    if out.suffix.lower() != ".json":
        raise ValueError("Uniqueness receipt must have a .json extension")
    output = out.resolve()
    protected = {path.resolve() for path in primary_inputs}
    # Inspect even a partially malformed inventory for member aliases before
    # replacing a receipt. Failure to parse is handled by the audit itself.
    try:
        manifest = json.loads(registry.read_text())
        rows = manifest.get("rasters", []) if isinstance(manifest, dict) else []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    for key in ("path", "dots_path"):
                        if isinstance(row.get(key), str):
                            try:
                                # Protect even malformed or escaping member paths:
                                # the audit will reject them, but must not overwrite them.
                                protected.add((registry.parent / row[key]).resolve())
                            except (OSError, RuntimeError, ValueError):
                                pass
    except (OSError, ValueError):
        pass
    if output in protected:
        raise ValueError("Receipt output aliases an input or registry member")


def write_receipt(path: Path, result: dict) -> None:
    """Atomically replace old results; a failed run must not leave a stale pass."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".uniqueness-", delete=False) as stream:
            temp = Path(stream.name)
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", type=Path, required=True)
    parser.add_argument("--dots", type=Path, required=True, help="Explicit preview dots before writing, or exact final dots")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True, help="JSON: complete, expected_count, rasters:[id,path,sha256]")
    parser.add_argument("--stage", choices=["surface-before-writer", "final-dots"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        safe_output_path(args.out, (args.surface, args.dots, args.template, args.registry), args.registry)
    except (OSError, ValueError) as exc:
        # Do not write a failure receipt over a protected input.
        print(json.dumps({"status": "BLOCKED_UNSAFE_OUTPUT", "error": str(exc),
                          "unique_under_protocol": False, "slot_authorized": False}), file=sys.stderr)
        return 2
    pending = {"kind": "GEOMETRIC_AUDIT_NOT_SCORE", "stage": args.stage,
               "status": "BLOCKED_IN_PROGRESS", "unique_under_protocol": False,
               "registry_complete": False, "slot_authorized": False}
    try:
        # Publish a negative result before any expensive reads, so interruption
        # or an exception cannot leave an earlier pass in place.
        write_receipt(args.out, pending)
        result = audit_registry(args.surface, args.dots, args.template, args.registry, args.stage)
        write_receipt(args.out, result)
    except Exception as exc:
        result = {**pending, "status": "BLOCKED_ERROR", "error": str(exc)}
        try:
            write_receipt(args.out, result)
        except OSError as write_error:
            print("Unable to replace uniqueness receipt: " + str(write_error), file=sys.stderr)
        print(json.dumps(result, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["unique_under_protocol"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
