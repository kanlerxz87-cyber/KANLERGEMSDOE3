#!/usr/bin/env python3
"""Restore all SHA-256-pinned core, external, and registry rasters into .cache/gems_data.

Uses zero-rate-limit ``https://codeload.github.com/<owner>/<repo>/tar.gz/<commit>``
streams (and reuses local ``/tmp/inspect`` extracts when SHA-256 matches).
Every restored file is cryptographically verified against its pinned SHA-256
digest before being moved into place. Nothing large is ever written into ``data/``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_many(repo: str, commit: str, mapping: dict[str, tuple[Path, str | None]]) -> None:
    """Stream one codeload tarball and extract all needed repo-relative paths."""
    need: dict[str, tuple[Path, str | None]] = {}
    for rel, (dest, expected) in mapping.items():
        if dest.is_file() and (expected is None or sha256_file(dest) == expected):
            continue
        need[rel] = (dest, expected)
    if not need:
        return

    print(f"  [codeload] {repo}@{commit[:10]} -> {len(need)} file(s)", flush=True)
    url = f"https://codeload.github.com/{repo}/tar.gz/{commit}"
    req = urllib.request.Request(url, headers={"User-Agent": "KANLERGEMSDOE3-restore/1.0"})
    found: set[str] = set()
    with urllib.request.urlopen(req, timeout=300) as resp:
        with tarfile.open(fileobj=resp, mode="r|gz") as tf:
            for member in tf:
                if not member.isfile():
                    continue
                parts = member.name.split("/", 1)
                if len(parts) != 2:
                    continue
                rel = parts[1]
                if rel not in need:
                    continue
                dest, expected = need[rel]
                dest.parent.mkdir(parents=True, exist_ok=True)
                fh = tf.extractfile(member)
                if fh is None:
                    raise RuntimeError(f"Cannot extract {rel} from {url}")
                tmp = dest.with_suffix(dest.suffix + ".part")
                h = hashlib.sha256()
                with tmp.open("wb") as out:
                    while True:
                        chunk = fh.read(1 << 20)
                        if not chunk:
                            break
                        h.update(chunk)
                        out.write(chunk)
                actual = h.hexdigest()
                if expected is not None and actual != expected:
                    tmp.unlink(missing_ok=True)
                    raise ValueError(
                        f"SHA-256 mismatch on {repo}@{commit}:{rel}: got {actual}, expected {expected}"
                    )
                tmp.replace(dest)
                found.add(rel)
                if len(found) == len(need):
                    break

    missing = set(need) - found
    if missing:
        raise FileNotFoundError(f"Missing {sorted(missing)} in {repo}@{commit}")


def build_uniqueness_registry_manifest() -> list[dict]:
    """Build deduplicated SHA-256-pinned registry covering focus winners, scored history, GEMSDOE70 & KANLERGEMSDOE1."""
    entries: list[dict] = []
    seen_sha: set[str] = set()

    def add(item: dict) -> None:
        if item["sha256"] in seen_sha:
            return
        seen_sha.add(item["sha256"])
        entries.append(item)

    # 1. All 9 focus-site HEAD winners (audited in focus_site_winner_overlap_20261026.json)
    focus9 = json.loads(
        (ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text()
    )["historical_winners"]
    for row in focus9:
        add(
            {
                "id": f"focus-{row['repo']}",
                "site": row["repo"],
                "repo": f"buffedlizard55-lab/{row['repo']}",
                "ref": row["head"],
                "path": row["file"],
                "dest": f"registry/{row['repo']}.tif",
                "sha256": row["sha256"],
                "reported_dti": row.get("owner_reported_leaderboard_score"),
                "cohort": "focus_9_head_winners",
                "is_calibration_probe": False,
            }
        )

    # 2. Additional 2026-10-25/26 focus-site & GEMSDOE28/33 submissions
    extra_focus = [
        {
            "id": "G28-h32-1-31e35eee884e",
            "site": "GEMSDOE28",
            "repo": "buffedlizard55-lab/GEMSDOE28",
            "ref": "e6321461066f89080e3b1bb670d3951ab20d3638",
            "path": "docs/downloads/gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif",
            "dest": "registry/G28-h32-1-31e35eee884e.tif",
            "sha256": "04d31922f5c1ea4016984fc470ab2b0ff8e266c615792f0e86020da3b940d3ff",
            "reported_dti": 0.2649,
            "cohort": "classic_scored_lineage",
            "is_calibration_probe": False,
        },
        {
            "id": "G28-h36-1-b531dae0a36f",
            "site": "GEMSDOE28",
            "repo": "buffedlizard55-lab/GEMSDOE28",
            "ref": "e6321461066f89080e3b1bb670d3951ab20d3638",
            "path": "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
            "dest": "registry/G28-h36-1-b531dae0a36f.tif",
            "sha256": "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641",
            "reported_dti": 0.2710,
            "cohort": "classic_scored_lineage",
            "is_calibration_probe": False,
        },
        {
            "id": "G28-h38-1-56a9f473edc7",
            "site": "GEMSDOE28",
            "repo": "buffedlizard55-lab/GEMSDOE28",
            "ref": "e6321461066f89080e3b1bb670d3951ab20d3638",
            "path": "docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif",
            "dest": "registry/G28-h38-1-56a9f473edc7.tif",
            "sha256": "81d5b87bc8424f162a8f56aa9aac8fbe630c61646b9cac24d5ebbdc1b1951783",
            "reported_dti": 0.2707,
            "cohort": "classic_scored_lineage",
            "is_calibration_probe": False,
        },
        {
            "id": "G33-a33-r2-csht-0b78c04d5fad",
            "site": "GEMSDOE33",
            "repo": "buffedlizard55-lab/GEMSDOE33",
            "ref": "0384d793b5a23151425f45505ac745b54f84c7c9",
            "path": "docs/downloads/gemsdoe33-a33-r2-csht-transfer-37654-20261026-0b78c04d5fad-zeros.tif",
            "dest": "registry/G33-a33-r2-csht-0b78c04d5fad.tif",
            "sha256": "14ab452c22aaf07444cd02e589fce4627d682e99f44c63e78dc1383955e0c602",
            "reported_dti": None,
            "cohort": "focus_20261026_siblings",
            "is_calibration_probe": False,
        },
        {
            "id": "G33-a33-l1-85c94a805a34",
            "site": "GEMSDOE33",
            "repo": "buffedlizard55-lab/GEMSDOE33",
            "ref": "0384d793b5a23151425f45505ac745b54f84c7c9",
            "path": "docs/downloads/gemsdoe33-a33-l1-analog-transfer-research-37654-20261025-85c94a805a34-zeros.tif",
            "dest": "registry/G33-a33-l1-85c94a805a34.tif",
            "sha256": "2bbbf7e381720f2242959e3efd6f2437f273afe6e7c48540d769524d2b4e8759",
            "reported_dti": None,
            "cohort": "focus_20261026_siblings",
            "is_calibration_probe": False,
        },
        {
            "id": "G24-gvc1-abe8e51c719d",
            "site": "GEMSDOE24",
            "repo": "buffedlizard55-lab/GEMSDOE24",
            "ref": "758af9ffb6ac5e3f82af6bd472f82d246dce55f0",
            "path": "docs/downloads/gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros.tif",
            "dest": "registry/G24-gvc1-abe8e51c719d.tif",
            "sha256": "b5ca6f1755af059e17f5edf0940fd7e945d43a1359e103a4789eae33c536ad41",
            "reported_dti": 0.0859,
            "cohort": "focus_20261025_scored",
            "is_calibration_probe": False,
        },
        {
            "id": "G25-h66-da617550a0e9",
            "site": "GEMSDOE25",
            "repo": "buffedlizard55-lab/GEMSDOE25",
            "ref": "0a45b3ca6403f7e8d4deac5d8b208797d5e8f477",
            "path": "docs/downloads/gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif",
            "dest": "registry/G25-h66-da617550a0e9.tif",
            "sha256": "7503f4d498694c0107e0efad92cd06613b56d6fe402712532c1805e778166c1a",
            "reported_dti": 0.0742,
            "cohort": "focus_20261025_scored",
            "is_calibration_probe": False,
        },
        {
            "id": "G27-h29-511898747886",
            "site": "GEMSDOE27",
            "repo": "buffedlizard55-lab/GEMSDOE27",
            "ref": "927322eadbde56be42ae129ccdfb9b37540d8e60",
            "path": "docs/downloads/gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite.tif",
            "dest": "registry/G27-h29-511898747886.tif",
            "sha256": "8585c5e870f197f84fda5bac7f22047d646fb73d455eb8b1129486c79bb976cf",
            "reported_dti": 0.2190,
            "cohort": "focus_20261025_scored",
            "is_calibration_probe": False,
        },
        {
            "id": "G28-s18-3e95505c011a",
            "site": "GEMSDOE28",
            "repo": "buffedlizard55-lab/GEMSDOE28",
            "ref": "10c26af3dc4d45292189734b0b696c7afb24ffb1",
            "path": "docs/downloads/gems28-s18-mxtp-20261025-3e95505c011a-allfinite.tif",
            "dest": "registry/G28-s18-3e95505c011a.tif",
            "sha256": "ce043566a96a1bf0abae366ba706ed6be5907297248b1d14deace8596500b186",
            "reported_dti": 0.0217,
            "cohort": "focus_20261025_scored",
            "is_calibration_probe": False,
        },
        {
            "id": "G30-MSDB1-e7856ec3f14a",
            "site": "GEMSDOE30",
            "repo": "buffedlizard55-lab/GEMSDOE30",
            "ref": "78ae70817af861c077ce1655c3f9115c5b0f537a",
            "path": "docs/downloads/gems30-MSDB1-edge44090-20261025-e7856ec3f14a.tif",
            "dest": "registry/G30-MSDB1-e7856ec3f14a.tif",
            "sha256": "22850984a68c393f60c6cc9aeafd8d74fd8a3479654bdfcfd3626a4b99ff0381",
            "reported_dti": 0.1462,
            "cohort": "focus_20261025_scored",
            "is_calibration_probe": False,
        },
        # 3. GEMSDOE70 (P8 live-scored 0.2478 and P9 PiedmontSubmod)
        {
            "id": "G70-p8-oof38k",
            "site": "GEMSDOE70",
            "repo": "buffedlizard55-lab/GEMSDOE70",
            "ref": "main",
            "path": "docs/downloads/gems70-p5-dual-submod300-oof38k-20261020.tif",
            "dest": "registry/G70-p8-oof38k.tif",
            "sha256": "d0e41ce921afcf3af33b7d86d75f6a258653dfbb4d050e864babe643245f0ea8",
            "reported_dti": 0.2478,
            "cohort": "gemsdoe70_submodular",
            "is_calibration_probe": False,
        },
        {
            "id": "G70-p9-piedmont-submod",
            "site": "GEMSDOE70",
            "repo": "buffedlizard55-lab/GEMSDOE70",
            "ref": "main",
            "path": "docs/downloads/gems70-p5-multiphysics-submodular-37654-20261020.tif",
            "dest": "registry/G70-p9-piedmont-submod.tif",
            "sha256": "f19a78d511f9d822b47ad4d9ce56cf2ccfa415e3d1ca49709a342158de6e7a84",
            "reported_dti": None,
            "cohort": "gemsdoe70_submodular",
            "is_calibration_probe": False,
        },
        # 4. KANLERGEMSDOE1 sibling rasters
        {
            "id": "KG1-h1-iedr-fe519ae3",
            "site": "KANLERGEMSDOE1",
            "repo": "kanlerxz87-cyber/KANLERGEMSDOE1",
            "ref": "main",
            "path": "docs/downloads/kanlergemsdoe1-h1-iedr-s3p17-b2-32000-20261026T214518Z-fe519ae3-zeros.tif",
            "dest": "registry/KG1-h1-iedr-fe519ae3.tif",
            "sha256": "455c3a1780806718c881480228631046cb3090a4734fac54f398c97533a89d39",
            "reported_dti": None,
            "cohort": "kanlergemsdoe_siblings",
            "is_calibration_probe": False,
        },
        {
            "id": "KG1-h2-htsi-571145eb",
            "site": "KANLERGEMSDOE1",
            "repo": "kanlerxz87-cyber/KANLERGEMSDOE1",
            "ref": "main",
            "path": "docs/downloads/kanlergemsdoe1-h2-htsi-s3p17-b2-32000-20261026T214518Z-571145eb-zeros.tif",
            "dest": "registry/KG1-h2-htsi-571145eb.tif",
            "sha256": "da8d6f42d95ca4a1b525745283f34a47e85d2daf195c08ff8d919003b27522ae",
            "reported_dti": None,
            "cohort": "kanlergemsdoe_siblings",
            "is_calibration_probe": False,
        },
        {
            "id": "KG1-h3-condresid-42802022",
            "site": "KANLERGEMSDOE1",
            "repo": "kanlerxz87-cyber/KANLERGEMSDOE1",
            "ref": "main",
            "path": "docs/downloads/kanlergemsdoe1-h3-condresid-s3p17-b2-32000-20261026T214518Z-42802022-zeros.tif",
            "dest": "registry/KG1-h3-condresid-42802022.tif",
            "sha256": "e5ff0120380fa316ccfa63c27d5383de4d74f963419d41e2ea4418ad73b4c950",
            "reported_dti": None,
            "cohort": "kanlergemsdoe_siblings",
            "is_calibration_probe": False,
        },
    ]
    for row in extra_focus:
        add(row)

    # 5. All classic scored/calibration rasters from GEMSDOE32/registry/data_manifest.json
    g32_manifest = json.loads(
        (ROOT / "sources/GEMSDOE32/registry/data_manifest.json").read_text()
    )["files"]
    for row in g32_manifest:
        if row["group"] != "scored":
            continue
        is_lattice = "r13-lattice-s5" in row["id"] or "r13-lattice-s5" in row["dest"]
        add(
            {
                "id": row["id"],
                "site": "GEMSDOE24_archive",
                "repo": row["repo"],
                "ref": row["ref"],
                "path": row["path"],
                "dest": row["dest"],
                "sha256": row["sha256"],
                "reported_dti": 0.1922 if row["id"] == "scored_h19_5" else None,
                "cohort": "calibration_probe" if is_lattice else "classic_scored_lineage",
                "is_calibration_probe": is_lattice,
            }
        )

    return entries


def try_copy_from_local_inspect(dest: Path, expected_sha: str, candidates: list[Path]) -> bool:
    if dest.is_file() and sha256_file(dest) == expected_sha:
        return True
    for cand in candidates:
        if cand.is_file() and sha256_file(cand) == expected_sha:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cand, dest)
            return True
    return False


def restore_all(dest_dir: Path) -> dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    g32_manifest = json.loads(
        (ROOT / "sources/GEMSDOE32/registry/data_manifest.json").read_text()
    )["files"]

    # 1. Restore 5-part training_features.tif from GEMSDOE@c0c06ac8...
    tf_entry = next(f for f in g32_manifest if f["id"] == "training_features")
    tf_dest = dest_dir / tf_entry["dest"]
    if not (tf_dest.is_file() and sha256_file(tf_dest) == tf_entry["sha256"]):
        part_targets = {
            part: (dest_dir / f".part-{idx:03d}", None)
            for idx, part in enumerate(tf_entry["parts"])
        }
        extract_many(tf_entry["repo"], tf_entry["ref"], part_targets)
        tmp = tf_dest.with_suffix(".tif.part")
        h = hashlib.sha256()
        with tmp.open("wb") as out:
            for idx in range(len(tf_entry["parts"])):
                p = dest_dir / f".part-{idx:03d}"
                with p.open("rb") as fh:
                    while True:
                        chunk = fh.read(1 << 20)
                        if not chunk:
                            break
                        h.update(chunk)
                        out.write(chunk)
                p.unlink(missing_ok=True)
        if h.hexdigest() != tf_entry["sha256"]:
            tmp.unlink(missing_ok=True)
            raise ValueError(f"training_features.tif SHA-256 mismatch: {h.hexdigest()}")
        tmp.replace(tf_dest)

    # 2. Group all other GEMSDOE32 manifest files + 60GEMSDOE 10m DEM/chi + uniqueness registry
    by_tarball: dict[tuple[str, str], dict[str, tuple[Path, str | None]]] = {}

    for row in g32_manifest:
        if row["id"] == "training_features":
            continue
        out_p = dest_dir / row["dest"]
        by_tarball.setdefault((row["repo"], row["ref"]), {})[row["path"]] = (out_p, row["sha256"])

    # Seamless 10m 3DEP DEM & fluvial chi/ksn from 60GEMSDOE@32024716...
    ext60 = {
        "data/external/topo_10m_derived_100m_u8.tif": (
            dest_dir / "external/topo_10m_derived_100m_u8.tif",
            "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
        ),
        "data/external/dem10_chi_100m_i16.tif": (
            dest_dir / "external/dem10_chi_100m_i16.tif",
            "8897ba9c30ef1cd7ad5f23c16c6dfd7bb070e7e757f36fd9486eb45edfd973a5",
        ),
    }
    by_tarball.setdefault(("buffedlizard55-lab/60GEMSDOE", "32024716f218d06a94e01464157392119c03cb15"), {}).update(ext60)

    # Uniqueness registry entries + audit_rasters top-level focus copies
    uniq_entries = build_uniqueness_registry_manifest()
    reg_manifest_path = ROOT / "registry/uniqueness_registry_20261026.json"
    reg_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    reg_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "as_of": "2026-10-26",
                "total_rasters": len(uniq_entries),
                "genuine_detector_rasters": sum(1 for e in uniq_entries if not e["is_calibration_probe"]),
                "calibration_probes": sum(1 for e in uniq_entries if e["is_calibration_probe"]),
                "rasters": uniq_entries,
            },
            indent=2,
        )
        + "\n"
    )

    inspect_root = Path("/tmp/inspect")
    for row in uniq_entries:
        out_p = dest_dir / row["dest"]
        local_candidates = []
        if inspect_root.is_dir():
            for sub in inspect_root.iterdir():
                cand = sub / row["path"]
                if cand.is_file():
                    local_candidates.append(cand)
        if not try_copy_from_local_inspect(out_p, row["sha256"], local_candidates):
            by_tarball.setdefault((row["repo"], row["ref"]), {})[row["path"]] = (out_p, row["sha256"])

    for (repo, ref), targets in by_tarball.items():
        extract_many(repo, ref, targets)

    # Also copy the 9 focus-site winners to dest_dir/<REPO>.tif so scripts/audit_rasters.py works directly
    focus9 = json.loads(
        (ROOT / "sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json").read_text()
    )["historical_winners"]
    for row in focus9:
        src_p = dest_dir / f"registry/{row['repo']}.tif"
        dst_p = dest_dir / f"{row['repo']}.tif"
        if not (dst_p.is_file() and sha256_file(dst_p) == row["sha256"]):
            shutil.copy2(src_p, dst_p)

    return {
        "ok": True,
        "dest_dir": str(dest_dir),
        "training_features_sha256": sha256_file(tf_dest),
        "uniqueness_registry_count": len(uniq_entries),
        "uniqueness_registry_sha256": sha256_file(reg_manifest_path),
    }


def main() -> int:
    default_dest = Path(os.environ.get("GEMS_DATA_DIR", ROOT / ".cache/gems_data"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=default_dest)
    args = parser.parse_args()
    summary = restore_all(args.dest)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
