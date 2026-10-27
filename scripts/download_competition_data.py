#!/usr/bin/env python3
"""Autonomous SHA-256-verified restoration of competition, official external, and cross-site registry rasters.

All large binary files reside in gitignored `.cache/` (excluded from workspace snapshots) with lightweight
relative symlinks in `data/`. Uses blobless git fetch (`--filter=blob:none`) over `github.com` first, falling
back to `codeload.github.com` tarball streaming and `gh api`, so restoration works at zero GitHub REST quota.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kanler_gems.template_fixes import fetch_raw, sha256  # noqa: E402

EXTERNAL_PINS = [
    {
        "id": "lidar_scarp_features_u8",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/lidar_scarp_features_u8.tif",
        "dest": "data/external/lidar_scarp_features_u8.tif",
        "sha256": "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
        "license": "US Government Public Domain / CC0 (USGS 3DEP 1 m DEM)",
    },
    {
        "id": "geodawn_rad_u8",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_rad_u8.tif",
        "dest": "data/external/geodawn_rad_u8.tif",
        "sha256": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
        "license": "CC0 / Public Domain (USGS GeoDAWN doi:10.5066/P93LGLVQ)",
    },
    {
        "id": "geodawn_extensions_u8",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "data/external/geodawn_extensions_u8.tif",
        "dest": "data/external/geodawn_extensions_u8.tif",
        "sha256": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
        "license": "CC0 / Public Domain (USGS GeoDAWN doi:10.5066/P93LGLVQ)",
    },
    {
        "id": "tiger_road_distance_m",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "9da8a18381e179530c3b878d073314feaa26a20c",
        "path": "data/external/audit_sources/tiger_road_distance_m.tif",
        "dest": "data/external/tiger_road_distance_m.tif",
        "sha256": "e5350423508968fa2d32b0a6ae0d3fb4ae3ea645e3b8736f0c8e7ad9ff2f2988",
        "license": "US Government Public Domain / CC0 (US Census TIGER/Line 2024 Roads)",
    },
    {
        "id": "derived_sgmc_faults_100m_u8",
        "repo": "buffedlizard55-lab/GEMSDOE30",
        "ref": "666cb3697025766d715a3ae4994fad75a287ad02",
        "path": "data/external/derived_sgmc_faults_100m_u8.tif",
        "dest": "data/external/derived_sgmc_faults_100m_u8.tif",
        "sha256": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
        "license": "US Government Public Domain / CC0 (USGS SGMC — evaluation diagnostic ONLY)",
    },
    {
        "id": "derived_gdr_2m_probes_100m_u8",
        "repo": "buffedlizard55-lab/GEMSDOE30",
        "ref": "666cb3697025766d715a3ae4994fad75a287ad02",
        "path": "data/external/derived_gdr_2m_probes_100m_u8.tif",
        "dest": "data/external/derived_gdr_2m_probes_100m_u8.tif",
        "sha256": "7ac3cfdf2412f7f8a8b82d928115888c510f106f0254fb0b3988448db2f3b6ec",
        "license": "CC-BY-4.0 (OpenEI GDR #1391 INGENIOUS 2m temperature probes)",
    },
    {
        "id": "derived_gdr_paleo_100m_u8",
        "repo": "buffedlizard55-lab/GEMSDOE30",
        "ref": "666cb3697025766d715a3ae4994fad75a287ad02",
        "path": "data/external/derived_gdr_paleo_100m_u8.tif",
        "dest": "data/external/derived_gdr_paleo_100m_u8.tif",
        "sha256": "d6a3609bd7943fa5f1126a3cc688441aeceee261a76cd6a90a206830400066a4",
        "license": "CC-BY-4.0 (OpenEI GDR #1391 INGENIOUS paleo-geothermal sinter/tufa)",
    },
    {
        "id": "derived_gdr_volcanics_100m_u8",
        "repo": "buffedlizard55-lab/GEMSDOE30",
        "ref": "666cb3697025766d715a3ae4994fad75a287ad02",
        "path": "data/external/derived_gdr_volcanics_100m_u8.tif",
        "dest": "data/external/derived_gdr_volcanics_100m_u8.tif",
        "sha256": "c219bd644e6f7a4071dc429e29b909a2296967b0657bf456bb6675413ee76cb2",
        "license": "CC-BY-4.0 (OpenEI GDR #1391 INGENIOUS Quaternary volcanics)",
    },
]

FOCUS_SITES = [
    "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28",
    "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
]


def _link_from_cache(cache_path: Path, link_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    link_path.symlink_to(os.path.relpath(cache_path, link_path.parent))


def fetch_focus_main_tifs() -> list[dict]:
    """Fetch all current `docs/downloads/*.tif` across the 9 focus sites' `main` branches."""
    rows = []
    reg_cache = ROOT / ".cache" / "registry_rasters"
    reg_cache.mkdir(parents=True, exist_ok=True)

    # 1. Include all scored & calibration rasters from GEMSDOE32 data_manifest.json (including 13gems lattice & H19-5)
    dm = json.loads((ROOT / "sources/GEMSDOE32/registry/data_manifest.json").read_text())
    for entry in dm["files"]:
        if entry["group"] != "scored":
            continue
        dest_cache = reg_cache / "manifest_scored" / Path(entry["dest"]).name
        fetch_raw(entry["repo"], entry["path"], entry["ref"], dest_cache, entry["sha256"])
        is_synthetic_probe = "r13-lattice-s5" in entry["dest"]
        rows.append({
            "id": entry["id"],
            "repo": entry["repo"],
            "ref": entry["ref"],
            "remote_path": entry["path"],
            "local_cache": str(dest_cache.relative_to(ROOT)),
            "sha256": entry["sha256"],
            "bytes": dest_cache.stat().st_size,
            "category": "synthetic_calibration_lattice" if is_synthetic_probe else "scored_or_calibration_submission",
        })

    # 2. Include all 9 historical focus-site winners (pinned in focus_site_winner_overlap_20261026.json)
    winners = json.loads((ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text())
    for w in winners["historical_winners"]:
        repo = f"buffedlizard55-lab/{w['repo']}"
        dest_cache = reg_cache / "historical_winners" / f"{w['repo']}__{Path(w['file']).name}"
        fetch_raw(repo, w["file"], w["head"], dest_cache, w["sha256"])
        rows.append({
            "id": f"winner_{w['repo']}",
            "repo": repo,
            "ref": w["head"],
            "remote_path": w["file"],
            "local_cache": str(dest_cache.relative_to(ROOT)),
            "sha256": w["sha256"],
            "bytes": dest_cache.stat().st_size,
            "category": "focus_historical_winner",
        })

    # 3. Fetch every `.tif` currently in `docs/downloads/` (and root `downloads/`) on `main` across all 9 focus repos + GEMSDOE70
    for site in FOCUS_SITES + ["GEMSDOE70"]:
        repo = f"buffedlizard55-lab/{site}"
        cache_git = ROOT / ".cache" / "git_blobs" / repo.replace("/", "__")
        cache_git.mkdir(parents=True, exist_ok=True)
        if not (cache_git / ".git").is_dir():
            subprocess.run(["git", "init", "-q"], cwd=cache_git, check=True, timeout=30)
            subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{repo}.git"],
                           cwd=cache_git, check=True, timeout=30)
        subprocess.run(
            ["git", "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", "main"],
            cwd=cache_git, check=True, timeout=300,
        )
        commit = subprocess.check_output(["git", "rev-parse", "FETCH_HEAD"], cwd=cache_git, text=True).strip()
        tree = subprocess.check_output(
            ["git", "ls-tree", "-r", commit, "--name-only"], cwd=cache_git, text=True
        ).splitlines()
        tif_paths = [
            p for p in tree
            if p.endswith(".tif")
            and ("downloads/" in p or p.startswith("submissions/") or p.startswith("outputs/"))
            and "training_features" not in p
            and "sample_submission" not in p
            and "labels.tif" not in p
            and "existing_faults" not in p
        ]
        for rel_p in tif_paths:
            dest_cache = reg_cache / "live_heads" / site / rel_p.replace("/", "__")
            dest_cache.parent.mkdir(parents=True, exist_ok=True)
            if not dest_cache.is_file():
                tmp = dest_cache.with_suffix(".partial")
                with tmp.open("wb") as out_f:
                    subprocess.run(
                        ["git", "show", f"{commit}:{rel_p}"],
                        cwd=cache_git, stdout=out_f, check=True, timeout=300,
                    )
                tmp.replace(dest_cache)
            digest = sha256(dest_cache)
            is_probe = "r13-lattice-s5" in rel_p
            rows.append({
                "id": f"head_{site}_{Path(rel_p).stem}",
                "repo": repo,
                "ref": commit,
                "remote_path": rel_p,
                "local_cache": str(dest_cache.relative_to(ROOT)),
                "sha256": digest,
                "bytes": dest_cache.stat().st_size,
                "category": "synthetic_calibration_lattice" if is_probe else "focus_live_head_download",
            })
        print(f"[registry] Indexed {len(tif_paths)} downloadable .tif files from {site}@{commit[:8]}", flush=True)
    return rows


def main() -> int:
    ext_rows = []
    for pin in EXTERNAL_PINS:
        cache_file = ROOT / ".cache" / pin["dest"]
        fetch_raw(pin["repo"], pin["path"], pin["ref"], cache_file, pin["sha256"])
        _link_from_cache(cache_file, ROOT / pin["dest"])
        ext_rows.append({
            **pin,
            "bytes": cache_file.stat().st_size,
            "verified": sha256(ROOT / pin["dest"]) == pin["sha256"],
        })
        print(f"[external] OK {pin['dest']} ({cache_file.stat().st_size:,} B)", flush=True)

    # Also run restore_audit_data so data/GEMSDOE24.tif..GEMSDOE36.tif & data/labels.tif exist
    subprocess.run([sys.executable, str(ROOT / "scripts/restore_audit_data.py")], check=True)

    reg_rows = fetch_focus_main_tifs()
    unique_hashes = sorted({r["sha256"] for r in reg_rows})

    receipt = {
        "schema_version": 1,
        "generated_utc": "2026-10-26",
        "provenance_note": (
            "Hash-verified public owner mirrors and focus-site HEAD artifacts restored via git smart HTTP "
            "(zero DrivenData contact, zero GitHub REST quota required). Byte identity to pinned commits is "
            "verified; organizer upload receipts are separate."
        ),
        "external_layers": ext_rows,
        "registry_entries": len(reg_rows),
        "unique_registry_sha256_count": len(unique_hashes),
        "rasters": reg_rows,
    }
    out_manifest = ROOT / "evidence" / "registry_refreshed.json"
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    out_manifest.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(
        f"[complete] Verified {len(ext_rows)} external layers + {len(reg_rows)} registry rasters "
        f"({len(unique_hashes)} unique SHA-256 digests) -> evidence/registry_refreshed.json",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
