#!/usr/bin/env python3
"""Recover only pinned source files for inherited synthetic integration tests.

Git transport avoids downloading full raster-bearing repository archives. These
are separate historical instrument versions, never interchangeable evaluators.
The active review's 13-file gems32 lock remains under vendor/shared-template.
No model, feature cache, candidate writer, upload or branch checkout runs here.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import GitHubSource, sha256_file, source_path

LEGACY32 = "07806249f4ed3efe70b4fbf866183c32392b7853"
LEGACY_INIT_SHA256 = "e4a584f79eab8c0db81b5704b1525536fef2dcee5bac28da1455a39868983504"


def restore(profile: str) -> Path:
    if profile == "legacy32":
        repo, commit = "buffedlizard55-lab/GEMSDOE32", LEGACY32
        destination = Path(os.environ.get("GEMS_TEMPLATE_DIR", ROOT / (".cache/shared-template-" + commit)))
        rows = [line.split() for line in (ROOT / "data/shared-tool-hashes.txt").read_text().splitlines() if line.strip()]
        rows.append([LEGACY_INIT_SHA256, "src/gems32/__init__.py"])
    elif profile == "saturation57":
        pins = json.loads((ROOT / "registry/shared_template_pins.json").read_text())
        repo = pins["source_repository"].removeprefix("https://github.com/")
        commit = pins["source_commit"]
        destination = ROOT / ".cache/template57"
        rows = [[spec["sha256"], name] for name, spec in pins["files"].items()]
    else:
        raise ValueError("Unknown instrument profile")
    destination = destination.resolve()
    if not destination.is_relative_to((ROOT / ".cache").resolve()):
        raise ValueError("Inherited instrument caches must remain under the ignored project .cache directory")
    if not rows or any(len(row) != 2 for row in rows) or len({row[1] for row in rows}) != len(rows):
        raise ValueError("Nonempty, nonduplicated source lock required")
    source = GitHubSource()
    for digest, member in rows:
        source_path(member)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid pinned source digest")
        target = destination / member
        if not target.resolve().is_relative_to(destination):
            raise ValueError("Source cache member symlink escapes its directory")
        source.restore(repo, commit, member, target, digest)
        if sha256_file(target) != digest:
            raise ValueError("Pinned instrument verification failed: " + member)
    if profile == "legacy32":
        (destination / ".template-commit").write_text(commit + "\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("legacy32", "saturation57"), required=True)
    args = parser.parse_args()
    try:
        print(restore(args.profile))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("Instrument restoration blocked: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
