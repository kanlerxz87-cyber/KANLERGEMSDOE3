#!/usr/bin/env python3
"""Certify a registry-saturation blocker with the unchanged shared template.

This is a geometric registry measurement, not a geological experiment, score,
candidate, or upload. Positive finite pixels count as dots under the pinned
shared implementation. A continuous diagnostic need not be an actual submitted
dot raster; that scope/representation ambiguity is reported, never hidden.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import rasterio

import restore_shared_template as recovery

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence/upstream/GEMSDOE31/registry/raster_registry.json"
REGISTRY_SHA = "e1f10c7bf4c0b9c61a427a6106a0073ca2ea449f6d30b2b787931fbda2d2e104"
WITNESS_REPO = "buffedlizard55-lab/GEMSDOE48"
WITNESS_REF = "268ec599f51c517cc3485da077c24d83af5be81d"
WITNESS_PATH = "docs/downloads/GEMSDOE48-unassigned-mass-20261006.tif"
WITNESS_SHA = "975c217ef803a45041077a219ba460134a8c84c8ea9f7ffc0414ddb47cb54ccd"
SAMPLE_REPO = "buffedlizard55-lab/GEMSDOE24"
SAMPLE_REF = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"
SAMPLE_PATH = "data/bridge/sample_submission.tif"
WITNESS = ROOT / ".cache/registry48" / WITNESS_PATH
SAMPLE = ROOT / "data/sample_submission.tif"


def verify_registry() -> dict:
    if not recovery.matches(REGISTRY, REGISTRY_SHA):
        raise ValueError("the pinned registry snapshot is missing or changed")
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [r for r in reg["rasters"] if r.get("repo") == "GEMSDOE48"
               and r.get("ref") == WITNESS_REF and r.get("path") == WITNESS_PATH
               and r.get("sha256") == WITNESS_SHA]
    if len(matches) != 1:
        raise ValueError("the witness must appear exactly once in the pinned registry")
    return reg


def ensure_file(path: Path, digest: str, repo: str, ref: str, member: str, restore: bool) -> None:
    if not recovery.matches(path, digest):
        if not restore:
            raise FileNotFoundError(f"missing or unverified file: {path}; use --restore")
        recovery.download_archive(repo, ref, {member: {"destination": path, "sha256": digest}})
    if not recovery.matches(path, digest):
        raise ValueError(f"pin mismatch: {path}")


def measure(restore: bool = False) -> dict:
    registry = verify_registry()
    pins = json.loads(recovery.PINS.read_text(encoding="utf-8"))
    if not recovery.restore_template(pins, offline=not restore):
        raise FileNotFoundError("shared template absent or changed; use --restore")
    ensure_file(WITNESS, WITNESS_SHA, WITNESS_REPO, WITNESS_REF, WITNESS_PATH, restore)
    ensure_file(SAMPLE, recovery.SAMPLE_SHA, SAMPLE_REPO, SAMPLE_REF, SAMPLE_PATH, restore)
    sys.path.insert(0, str(recovery.TEMPLATE / "src"))
    from gems57.uniqueness import saturation_certificate

    with rasterio.open(SAMPLE) as sample:
        footprint = sample.dataset_mask() > 0
        grid = (sample.shape, sample.crs, sample.transform)
    measured = saturation_certificate(WITNESS, footprint, expected_grid=grid)
    # Avoid an environment-specific cache path in the archived report.
    measured["witness_file"] = WITNESS_PATH
    return {
        "kind": "REGISTRY-MEASUREMENT; not HOLDOUT-DTI or an organizer score",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": f"https://github.com/{WITNESS_REPO}",
        "source_commit": WITNESS_REF,
        "source_url": f"https://github.com/{WITNESS_REPO}/blob/{WITNESS_REF}/{WITNESS_PATH}",
        "registry_source": "https://github.com/buffedlizard55-lab/GEMSDOE31/blob/2a7cd0c8f1c30341a3a655a01a1ff5bff67b23d2/registry/raster_registry.json",
        "registry_sha256": REGISTRY_SHA,
        "registry_as_of": registry["generated_utc"],
        "registry_unique_dot_sets_claimed": registry["unique_dot_sets"],
        "sample_sha256": recovery.SAMPLE_SHA,
        "sample_provenance": "participant mirror, not organizer-authenticated",
        "shared_template_commit": pins["source_commit"],
        "shared_uniqueness_sha256": pins["files"]["src/gems57/uniqueness.py"]["sha256"],
        "measurement": measured,
        "scope_caveat": "Witness is a continuous unassigned-mass diagnostic, not established as a submitted dot field. The pinned template nevertheless treats every finite positive cell as a dot. Under that literal interpretation any nonempty footprint candidate fails; excluding diagnostics requires an explicit protocol/registry decision.",
        "candidate_generated": False,
        "experiments_run": 0,
        "weekly_slots_used": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="recover missing pinned inputs from GitHub")
    parser.add_argument("--output", type=Path, help="optional path for a JSON measurement")
    args = parser.parse_args()
    try:
        result = measure(args.restore)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "candidate_generated": False}, indent=2), file=sys.stderr)
        return 1
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
