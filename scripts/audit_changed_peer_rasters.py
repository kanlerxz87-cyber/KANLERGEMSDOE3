#!/usr/bin/env python3
"""Check changed peer TIFF bytes against one pinned lattice; never train or write a prediction.

A >70% directed overlap is a definitive stop under the literal protocol. A
smaller overlap is NOT a uniqueness pass: the full registry/surfaces and
before-placement stage are not assessed. Peer artifacts are research only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_history import disk  # noqa: E402
from scripts.github_source import GitHubSource, sha256_file, source_path  # noqa: E402
from scripts.snapshot_raster_changes import SITES, SHA  # noqa: E402

MAX_RASTER_BYTES = 8_000_000


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def inspect(data: bytes, expected_blob: str, footprint: np.ndarray, grid: tuple, halo: np.ndarray) -> dict:
    if not SHA.fullmatch(expected_blob) or git_blob(data) != expected_blob:
        raise ValueError("Git tree/blob identity mismatch")
    if len(data) > MAX_RASTER_BYTES or data.startswith(b"version https://git-lfs.github.com/spec/"):
        raise ValueError("Raster too large or Git LFS content unavailable")
    with MemoryFile(data) as stream, stream.open() as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
            raise ValueError("Not a single-band raster on the exact mirror grid")
        values = src.read(1, masked=True)
        inside = values.data[footprint]
        if np.ma.getmaskarray(values)[footprint].any() or not np.isfinite(inside).all():
            raise ValueError("Masked or nonfinite pixels inside mirror footprint")
        if not np.isin(inside, [0, 1]).all():
            raise ValueError("Nonbinary values require an explicit companion dot mask")
        dots = (values.data == 1) & footprint
        count = int(dots.sum())
        if not count:
            raise ValueError("Empty candidate dots do not establish novelty")
        near = int((dots & halo).sum())
        fraction = near / count
        return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                "dtype": src.dtypes[0], "candidate_dots": count,
                "candidate_dots_within_3px_of_full_lattice": near,
                "directed_overlap_fraction": fraction,
                "status": "STOP_DUPLICATE" if fraction > .70 else "BLOCKED_INCOMPLETE_REGISTRY",
                "surface_correlation": None, "surface_before_placement": None,
                "format_or_portal_approval": False, "slot_authorized": False}


def run(changes: dict, root: Path = ROOT, source_factory=GitHubSource) -> dict:
    root = root.resolve()
    if (changes.get("all_compared") is not True or changes.get("registry_complete") is not False
            or changes.get("scientific_approval") is not False):
        raise ValueError("Complete nine-tree source observation required, not an approval")
    rows = changes.get("rows")
    if not isinstance(rows, list) or {r.get("site") for r in rows} != {"GEMSDOE" + str(n) for n in SITES} or len(rows) != len(SITES):
        raise ValueError("Changed-source inventory must cover the exact nine focus sites")
    lattice_row = next(row for row in json.loads((root / "research/registry-lock.json").read_text())["entries"] if row["id"] == "registry-160")
    core = {row["id"]: row for row in json.loads((root / "data/core-manifest.json").read_text())["files"]}
    lattice = root / "data/registry-review/lattice.tif"
    sample = root / "data/core" / core["sample_submission"]["dest"]
    for path, digest in ((lattice, lattice_row["sha256"]), (sample, core["sample_submission"]["sha256"])):
        if not path.is_file() or not path.resolve().is_relative_to(root) or sha256_file(path) != digest:
            raise ValueError("Pinned lattice or sample mirror is missing/altered")
    with rasterio.open(sample) as src:
        footprint = (src.dataset_mask() > 0) & np.isfinite(src.read(1))
        grid = (src.shape, src.crs, src.transform)
    with rasterio.open(lattice) as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
            raise ValueError("Lattice and mirror grid differ")
        ref = src.read(1, masked=True)
        lattice_dots = (~np.ma.getmaskarray(ref)) & (ref.data > 0) & footprint
    if not footprint.any() or not lattice_dots.any():
        raise ValueError("Empty reference footprint or lattice")
    halo = binary_dilation(lattice_dots, structure=disk(3))
    findings = []
    source = source_factory()
    seen = set()
    for row in rows:
        site, repo, commit = row["site"], row["repository"], row["after_commit"]
        if (repo != "buffedlizard55-lab/" + site or row.get("status") != "PINNED_TREE_COMPARISON_ONLY"
                or not isinstance(commit, str) or not SHA.fullmatch(commit)):
            raise ValueError("Malformed site, repository or immutable commit")
        for category in ("added", "changed"):
            for item in row[category]:
                path = source_path(item["path"])
                ident = (repo, path)
                if ident in seen or not path.lower().endswith((".tif", ".tiff")):
                    raise ValueError("Duplicate or non-TIFF changed path")
                seen.add(ident)
                new = item["after"]
                finding = {"site": site, "repository": repo, "commit": commit, "path": path,
                           "git_blob": new["git_blob"], "mode": new["mode"], "category": category}
                try:
                    if new["mode"] not in ("100644", "100755"):
                        raise ValueError("Symlink or unsupported tree mode")
                    data = source.read(repo, commit, path)
                    finding.update(inspect(data, new["git_blob"], footprint, grid, halo))
                except Exception as exc:
                    finding.update({"status": "UNKNOWN", "error": str(exc), "sha256": None,
                                    "slot_authorized": False, "surface_correlation": None})
                findings.append(finding)
    return {"schema_version": 1, "kind": "CHANGED PEER SAVED-BYTE LATTICE AUDIT; NOT A MODEL OR SCORE",
            "snapshot_checked_utc": changes.get("current_checked_utc"), "lattice_source": lattice_row,
            "sample_mirror_sha256": core["sample_submission"]["sha256"], "organizer_template_authenticated": False,
            "findings": findings, "files_seen": len(findings),
            "duplicate_stops": sum(r["status"] == "STOP_DUPLICATE" for r in findings),
            "unknown": sum(r["status"] == "UNKNOWN" for r in findings),
            "incomplete_registry": sum(r["status"] == "BLOCKED_INCOMPLETE_REGISTRY" for r in findings),
            "full_registry_compared": False, "new_candidate_generated": False, "geological_experiments_run": 0,
            "slot_authorized": False, "verdict": "negative",
            "limitations": "Each exact Git blob is checked once against one lattice; no surface, full registry, holdout, organizer acceptance or leaderboard score is verified."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(json.loads(args.changes.read_text()))
        result["change_snapshot_sha256"] = sha256_file(args.changes)
        code = 1  # A one-reference audit is always non-authorizing.
    except Exception as exc:
        result = {"kind": "CHANGED PEER AUDIT FAILED", "verdict": "negative", "slot_authorized": False,
                  "new_candidate_generated": False, "error": str(exc)}
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Changed-file audit: {result.get('duplicate_stops', 0)} duplicate stops, {result.get('unknown', 0)} unknown; no approval.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
