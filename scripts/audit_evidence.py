#!/usr/bin/env python3
"""Re-open pinned witnesses and the nine historical masks. No model or TIFF is produced."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems_audit.assets import CACHE, load_template, sha256, verify, verify_core  # noqa: E402

WITNESS_SHA = "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be"
LATTICE_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"


def binary_spearman(a: np.ndarray, b: np.ndarray, footprint_count: int) -> float | None:
    """Exact Spearman correlation for two binary arrays on the same footprint.

    Binary midranks are affine transforms of binary values, so their Pearson
    correlation is Spearman's rho. a and b must already be footprint-masked.
    """
    a, b = np.asarray(a, dtype=bool), np.asarray(b, dtype=bool)
    if a.shape != b.shape:
        raise ValueError("binary correlation masks must share a grid")
    n = int(footprint_count)
    na, nb = int(a.sum()), int(b.sum())
    if n < 0 or n > a.size or na > n or nb > n:
        raise ValueError("binary counts exceed the specified footprint")
    both = int((a & b).sum())
    if n == 0 or na in (0, n) or nb in (0, n):
        return None
    return (n * both - na * nb) / math.sqrt(na * (n - na) * nb * (n - nb))


def run() -> dict:
    load_template()
    from gems57 import grid, uniqueness  # imported from verified shared template

    verify_core()
    witness_path, lattice_path = CACHE / "registry/witness.tif", CACHE / "registry/lattice5.tif"
    verify(witness_path, WITNESS_SHA)
    verify(lattice_path, LATTICE_SHA)
    data = CACHE / "data"
    with rasterio.open(data / "sample_submission.tif") as ref:
        sample = ref.read(1)
        footprint = np.isfinite(sample) & (ref.dataset_mask() > 0)
        expected = (ref.shape, ref.crs, ref.transform)
    with rasterio.open(data / "existing_faults.tif") as cat:
        if (cat.shape, cat.crs, cat.transform) != expected or cat.count != 1:
            raise ValueError("catalogue/reference grid mismatch")
        known = (cat.read(1) > 0) & footprint
    if expected != (grid.SHAPE, rasterio.crs.CRS.from_epsg(grid.EPSG), grid.TRANSFORM):
        raise ValueError("owner-mirror reference grid differs from the shared template")
    certificate = uniqueness.saturation_certificate(witness_path, footprint, known, expected_grid=expected)
    # Relative names in committed evidence; no private paths or credentials.
    certificate["witness_file"] = "17GEMSDOE/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif"
    with rasterio.open(witness_path) as ref:
        soft = ref.read(1)
        witness_on_foot = int((np.isfinite(soft) & (soft > 0) & footprint).sum())
    del soft
    if not certificate["universal_overlap_blocker"] or witness_on_foot != int(footprint.sum()):
        raise ValueError("Pinned witness no longer establishes the published full-footprint stop; do not reuse the prior conclusion")
    with rasterio.open(lattice_path) as ref:
        if (ref.shape, ref.crs, ref.transform) != expected or ref.count != 1:
            raise ValueError("lattice grid mismatch")
        a = ref.read(1)
        lattice = np.isfinite(a) & (a > 0) & footprint
    del a
    covered = uniqueness._near(lattice, 3)  # pinned shared implementation, no policy exception
    uncovered = int((footprint & ~covered).sum())
    lattice_report = {"sha256": LATTICE_SHA, "positive_pixels": int(lattice.sum()),
                      "footprint_pixels": int(footprint.sum()),
                      "footprint_within_3_pixels": int((footprint & covered).sum()),
                      "uncovered_footprint_pixels": uncovered,
                      "covered_fraction": float((footprint & covered).sum() / footprint.sum()),
                      "maximum_dots_to_allow_at_most_70_percent_overlap": math.floor(uncovered / 0.30),
                      "bound_note": "Necessary only; at least 30% of candidate dots must be among uncovered footprint cells. The full-footprint soft witness blocks every nonempty candidate regardless of budget."}
    del covered, lattice

    manifest = json.loads((ROOT / "registry/focus_historical.json").read_text())
    masks = {}
    file_audits = []
    for entry in manifest["files"]:
        path = CACHE / "registry/focus" / f"{entry['site']}.tif"
        verify(path, entry["sha256"])
        with rasterio.open(path) as src:
            if (src.shape, src.crs, src.transform) != expected or src.count != 1:
                raise ValueError(f"bad grid for {entry['site']}")
            a = src.read(1)
            dtype = src.dtypes[0]
        good = np.isfinite(a[footprint])
        interior = a[footprint]
        if not good.all() or (interior < 0).any() or (interior > 1).any():
            raise ValueError(f"invalid in-footprint values for {entry['site']}")
        m = np.isfinite(a) & (a > 0) & footprint
        masks[entry["site"]] = m
        file_audits.append({"site": entry["site"], "sha256": sha256(path), "ref": entry["ref"],
                            "path": entry["path"], "dtype": dtype, "positive_pixels": int(m.sum()),
                            "expected_positive_pixels_match": int(m.sum()) == entry["expected_positive_pixels"],
                            "finite_inside": int(good.sum()), "nan_inside": int((~good).sum()),
                            "minimum_inside": float(interior.min()), "maximum_inside": float(interior.max()),
                            "finite_outside": int(np.isfinite(a[~footprint]).sum()),
                            "note": "Historical research reference; not a new candidate or score receipt."})
        del a, interior

    nfoot = int(footprint.sum())
    comparisons = []
    # One shared-template dilation per reference; overlap is directed, never symmetric by assumption.
    for site_b, b in masks.items():
        near = uniqueness._near(b, 3)
        for site_a, m in masks.items():
            if site_a == site_b:
                continue
            comparisons.append({"candidate": site_a, "reference": site_b,
                                "directed_overlap_within_3px": float(near[m].mean()) if m.any() else None,
                                "binary_spearman": binary_spearman(m, b, nfoot),
                                "same_in_footprint_mask": bool(np.array_equal(m, b))})
        del near

    dist = ndi.distance_transform_edt(~known)
    d28, b1, b2, p36 = (masks[f"GEMSDOE{i}"] for i in (25, 31, 32, 36))
    identity = {
        "gems25_equals_gems30_mask": bool(np.array_equal(d28, masks["GEMSDOE30"])),
        "gems31_equals_gems25_after_1px_collar": bool(np.array_equal(b1, d28 & (dist > 1.0))),
        "gems32_equals_gems25_after_2px_collar": bool(np.array_equal(b2, d28 & (dist > 2.0))),
        "gems32_equals_gems31_after_2px_collar": bool(np.array_equal(b2, b1 & (dist > 2.0))),
        "removed_d28_to_b1": int((d28 & ~b1).sum()),
        "removed_b1_to_b2": int((b1 & ~b2).sum()),
        "b2_pixels_missing_from_36": int((b2 & ~p36).sum()),
        "extra_pixels_in_36_vs_b2": int((p36 & ~b2).sum()),
    }
    pairs = sorted(comparisons, key=lambda x: x["directed_overlap_within_3px"], reverse=True)
    return {
        "schema": "kanler-gems-evidence-audit-v1", "audited_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "REGISTRY-MEASUREMENT; no organizer score and no scientific experiment",
        "template": {"source": "buffedlizard55-lab/GEMSDOE31", "commit": "597b04cd1afb65d1ebbe3e9417fd952be48e3d74", "pins_verified": True},
        "grid": {"crs": str(expected[1]), "shape": list(expected[0]), "transform": list(expected[2])[:6],
                 "footprint_pixels": nfoot, "known_pixels": int(known.sum()),
                 "sample_positive_pixels": int(((sample > 0) & footprint).sum()),
                 "sample_positive_on_known": int(((sample > 0) & known).sum()),
                 "sample_note": "Mirror sample is NOT a zero-absence prediction; use its finite mask/grid only, never as a predictor."},
        "saturation_witness": {**certificate, "positive_inside_footprint": witness_on_foot,
                               "repo": "buffedlizard55-lab/17GEMSDOE",
                               "ref": "6fc71d19d49dca4960d5434bd81b6dd06fcc030a",
                               "scope": "A single counterexample suffices to disprove literal uniqueness; not a complete registry scan."},
        "lattice": lattice_report, "historical_files": file_audits,
        "historic_pairwise_comparisons": comparisons,
        "max_historical_directed_overlap": pairs[0] if pairs else None,
        "lineage": identity, "new_model_experiments": 0, "new_tiff": None,
        "competition_slots_used": 0, "decision": "negative", "ok_to_submit": False,
    }


def main() -> int:
    try:
        result = run()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"AUDIT FAILED CLOSED: {exc}", file=sys.stderr)
        return 1
    target = ROOT / "evidence/audit.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    card_path = ROOT / "evidence/run-card.json"
    if card_path.is_file():
        card = json.loads(card_path.read_text())
        card["audited_utc"] = result["audited_utc"]
        card["correlation_overlap_vs_registry"]["witness_sha256"] = result["saturation_witness"]["witness_sha256"]
        card["correlation_overlap_vs_registry"]["witness_footprint_positive_cells"] = result["saturation_witness"]["positive_inside_footprint"]
        card["correlation_overlap_vs_registry"]["allowed_cells_uncovered"] = result["saturation_witness"]["uncovered_allowed_pixels"]
        card_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print("AUDIT COMPLETE: universal blocker =", result["saturation_witness"]["universal_overlap_blocker"])
    print("Historical lineage:", json.dumps(result["lineage"]))
    print("Saved evidence/audit.json; no candidate TIFF generated; no submission slot used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
