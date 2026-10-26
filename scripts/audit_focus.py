#!/usr/bin/env python3
"""Audit the exact historical focus-site anchors, not candidate submissions.

Comparisons are restricted to one named anchor per site, not a complete
registry. Old files may be inspected for education; no file is selected for
resubmission. Hashes and on-footprint binary values are verified first.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

from restore_workspace import ANCHORS, DEFAULT_CACHE, restore, sha256_file


def binary_spearman(left, right, valid):
    """Spearman for two verified binary arrays, via their 2x2 contingency table.

    Binary midranks are affine transformations of their Boolean values. Return
    None rather than invent a correlation for a constant input.
    """
    l, r, valid = np.asarray(left, bool), np.asarray(right, bool), np.asarray(valid, bool)
    if l.shape != r.shape or l.shape != valid.shape:
        raise ValueError("correlation shape mismatch")
    n = int(valid.sum())
    a, b = int((l & valid).sum()), int((r & valid).sum())
    both = int((l & r & valid).sum())
    den = float(a * (n - a)) * float(b * (n - b))
    return (both * n - a * b) / np.sqrt(den) if den else None


def summarize_pair(mine, theirs, valid, near_theirs):
    mine, theirs, valid = map(lambda x: np.asarray(x, bool), (mine, theirs, valid))
    if not mine.shape == theirs.shape == valid.shape == np.shape(near_theirs):
        raise ValueError("pair shape mismatch")
    mine, theirs = mine & valid, theirs & valid
    n = int(mine.sum())
    overlap = float(np.asarray(near_theirs, bool)[mine].mean()) if n else None
    rho = binary_spearman(mine, theirs, valid)
    return {"forward_overlap_3px": overlap, "spearman": rho,
            "same_support_inside_footprint": bool(np.array_equal(mine, theirs)),
            "duplicate_by_literal_threshold": bool((overlap is not None and overlap > 0.70)
                                                  or (rho is not None and rho > 0.90))}


def run(cache: Path) -> dict:
    restore(cache, fetch=False, anchors=True, features=False)
    sys.path.insert(0, str(cache / "template/src"))
    from gems57.uniqueness import _near
    entries = json.loads(ANCHORS.read_text())["anchors"]
    with rasterio.open(cache / "data/sample_submission.tif") as ref:
        valid = np.isfinite(ref.read(1))
        grid = (ref.shape, ref.crs, ref.transform)
    masks, metadata = {}, {}
    for item in entries:
        site = item["site"]
        path = cache / "data/anchors" / f"{site}.tif"
        with rasterio.open(path) as src:
            if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
                raise ValueError(f"{site} does not match mirrored grid")
            a = src.read(1)
            interior = a[valid]
            if not np.isfinite(interior).all():
                raise ValueError(f"{site} has invalid values inside the footprint")
            if not ((interior == 0) | (interior == 1)).all():
                raise ValueError(f"{site} is not binary; binary rank shortcut cannot be used")
            masks[site] = np.isfinite(a) & (a > 0) & valid
            metadata[site] = {"sha256": sha256_file(path),
                              "positive_pixels_inside_footprint": int(masks[site].sum()),
                              "finite_inside_footprint": True,
                              "on_footprint_values": "binary 0 or 1",
                              "nan_outside_footprint": int(np.isnan(a[~valid]).sum()),
                              "dtype": src.dtypes[0],
                              "claimed_value_not_score": item["claimed_value"],
                              "claim_class": "OWNER-REPORTED / UNVERIFIED; no linked organizer receipt",
                              "source_path": item["path"],
                              "source_blob_sha1": item["blob_sha1"]}
    # Compute each target's Euclidean 3-pixel dilation once.
    neighborhoods = {site: _near(mask) for site, mask in masks.items()}
    pairs = {}
    for site, mask in masks.items():
        peers = {other: summarize_pair(mask, other_mask, valid, neighborhoods[other])
                 for other, other_mask in masks.items() if other != site}
        pairs[site] = peers
        max_overlap_site = max(peers, key=lambda key: peers[key]["forward_overlap_3px"]
                               if peers[key]["forward_overlap_3px"] is not None else -1)
        metadata[site].update(max_overlap_other_site=max_overlap_site,
                              max_forward_overlap_3px=peers[max_overlap_site]["forward_overlap_3px"],
                              exact_support_matches=[other for other, v in peers.items() if v["same_support_inside_footprint"]],
                              passes_nine_anchor_subset=all(not v["duplicate_by_literal_threshold"]
                                                            and v["forward_overlap_3px"] is not None
                                                            and v["spearman"] is not None
                                                            for v in peers.values()))
    return {"schema": "gems-focus-anchor-audit-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "evidence_class": "REGISTRY-MEASUREMENT; values attributed to users are not verified scores",
            "scope": "One named historic anchor per focus site, same on-footprint grid; not a complete registry or official receipt. No claim that differences outside the footprint match.",
            "metric": "finite positive support; directional 3-pixel Euclidean overlap; exact full-footprint binary Spearman",
            "references": metadata, "pairwise": pairs}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run(args.cache)
        text = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    except (ValueError, OSError, ImportError, RuntimeError) as exc:
        print(f"FOCUS AUDIT FAILED CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
