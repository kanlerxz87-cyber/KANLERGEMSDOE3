#!/usr/bin/env python3
"""Restore the shared template's hash-pinned mirror inputs, never organizer credentials.

Only the transport is local. The manifest, preparation, evaluator and writer
remain the unmodified shared implementations. Git transport avoids the shared
REST quota and supports streaming the already-published multipart core raster.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import GitHubSource, sha256_file, source_path
from scripts.shared_tools import TEMPLATE, verify_template


def restore_entry(row: dict, target: Path, source: GitHubSource) -> dict:
    dest = target / source_path(row["dest"])
    expected = row["sha256"]
    if dest.is_file() and sha256_file(dest) == expected:
        status = "present"
    elif "parts" not in row:
        result = source.restore(row["repo"], row["ref"], row["path"], dest, expected)
        status = result["status"]
    else:
        if not row["parts"]:
            raise ValueError("Multipart input has no parts")
        bare = source.repository(row["repo"], row["ref"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        temporary = dest.with_name(dest.name + ".assembling")
        try:
            with temporary.open("wb") as out:
                for part in row["parts"]:
                    source._run(["git", "-C", str(bare), "show", f"{row['ref']}:{source_path(part)}"], stdout=out)
            if sha256_file(temporary) != expected:
                raise ValueError("Assembled mirror SHA-256 mismatch; destination not replaced")
            temporary.replace(dest)
        finally:
            temporary.unlink(missing_ok=True)
        status = "restored"
    if dest.stat().st_size != row["bytes"]:
        raise ValueError("Mirror byte count differs from locked manifest")
    return {"id": row["id"], "path": str(dest.relative_to(ROOT)) if dest.is_relative_to(ROOT) else str(dest), "status": status, "sha256": expected, "bytes": dest.stat().st_size, "provenance": row["provenance"], "organizer_authenticated": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=ROOT / "data" / "core")
    parser.add_argument("--include", nargs="*", default=["training_features", "labels", "existing_faults", "sample_submission", "ext_derived_sgmc_faults_100m_u8"])
    args = parser.parse_args()
    lock = verify_template()
    if not lock["ok"]:
        raise ValueError("Shared template modified; refusing restoration")
    manifest = json.loads((TEMPLATE / "registry" / "data_manifest.json").read_text())
    entries = {row["id"]: row for row in manifest["files"]}
    unknown = set(args.include) - entries.keys()
    if unknown:
        raise ValueError("Unknown manifest identifiers: " + ", ".join(sorted(unknown)))
    if not args.include:
        raise ValueError("At least one input identifier is required")
    target = args.target_dir.resolve()
    source = GitHubSource()
    rows = []
    for name in args.include:
        row = restore_entry(entries[name], target, source)
        rows.append(row)
        print(f"{row['status']}: {row['path']} ({row['bytes']} bytes)", flush=True)
    receipt = {"schema_version": 1, "template_commit": lock["commit"], "files": rows, "organizer_authenticated": False, "note": "Byte/hash consistency with the participant mirror, not organizer authentication. No historic prediction used as a candidate."}
    out = ROOT / "data" / "input_receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
