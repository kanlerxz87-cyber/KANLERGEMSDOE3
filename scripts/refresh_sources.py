#!/usr/bin/env python3
"""Refresh pinned public participant-source snapshots, not scores or approvals.

The nine focus-site refs come from docs/data/focus-feed.json. Every saved blob is
retrieved at that immutable commit and verified against GitHub's blob SHA before
replacement. The official reference-solution README is separately pinned to the
observed upstream main commit. This script does not access DrivenData.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "sources"
FOCUS_SITES = (24, 25, 27, 28, 30, 31, 32, 33, 36)
FOCUS_PATHS = ("README.md", "docs/index.html", "docs/score-ledger.csv")
GEMSDOE32_PATHS = (
    "evidence/h33_holdout.json",
    "evidence/h33_candidates.json",
    "evidence/h33_validation.json",
    "docs/research/why-02778-analysis-20261025.md",
    "scripts/evaluate_holdout.py",
    "scripts/submission_writer.py",
    "vendor/PROVENANCE.json",
    "registry/data_manifest.json",
    "registry/feature_receipt.json",
    "scripts/restore_data.py",
    "evidence/focus_site_winner_overlap_20261026.json",
)
OFFICIAL_REPO = "drivendataorg/gems-prize-reference-solution"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def gh_json(endpoint: str) -> Any:
    """Read JSON through gh; the caller always supplies a repository API endpoint."""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint], check=True, capture_output=True, text=True, timeout=120
        )
    except subprocess.CalledProcessError as exc:
        if re.search(r"\b404\b|not found", exc.stderr or "", re.IGNORECASE):
            raise FileNotFoundError(endpoint) from exc
        raise
    return json.loads(result.stdout)


def pinned_tasks(feed: dict, official_ref: str) -> list[tuple[str, str, str]]:
    """Build an explicit (repo, path, immutable commit) list from the feed."""
    if not isinstance(feed, dict) or not isinstance(feed.get("rows"), list):
        raise ValueError("Focus feed must contain a rows array")
    expected = {f"GEMSDOE{number}" for number in FOCUS_SITES}
    rows = {row.get("site"): row for row in feed["rows"] if isinstance(row, dict)}
    if set(rows) != expected or len(feed["rows"]) != len(expected):
        raise ValueError("Focus feed must contain exactly the nine configured sites")
    tasks: list[tuple[str, str, str]] = []
    for site in sorted(expected):
        row = rows[site]
        commit = row.get("commit")
        if row.get("status") != "PINNED_SOURCE_ONLY" or not isinstance(commit, str) or not HEX40.fullmatch(commit):
            raise ValueError(f"No valid immutable source commit for {site}")
        repo = row.get("repository")
        if repo != f"buffedlizard55-lab/{site}":
            raise ValueError(f"Unexpected repository for {site}")
        source_page = row.get("source_page")
        if (not isinstance(source_page, str) or source_page.startswith("/")
                or ".." in PurePosixPath(source_page).parts or "\\" in source_page):
            raise ValueError(f"Unsafe or missing source_page for {site}")
        tasks.extend((repo, path, commit) for path in (*FOCUS_PATHS, source_page))
    tasks.extend(("buffedlizard55-lab/GEMSDOE32", path, rows["GEMSDOE32"]["commit"]) for path in GEMSDOE32_PATHS)
    if not isinstance(official_ref, str) or not HEX40.fullmatch(official_ref):
        raise ValueError("Official reference-solution commit is invalid")
    tasks.append((OFFICIAL_REPO, "README.md", official_ref))
    return list(dict.fromkeys(tasks))


def retrieve(task: tuple[str, str, str], source_root: Path = SOURCE_ROOT) -> dict:
    """Fetch one file at its pin, verify Git blob identity, then atomically save it."""
    repo, path, ref = task
    row = {
        "repo": repo,
        "path": path,
        "ref": ref,
        "status": "unavailable",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        response = gh_json(f"repos/{repo}/contents/{path}?ref={ref}")
        if not isinstance(response, dict) or response.get("type") != "file":
            raise ValueError("GitHub response is not a regular file")
        if response.get("encoding") != "base64" or not isinstance(response.get("content"), str):
            raise ValueError("GitHub did not return base64 file contents")
        raw = base64.b64decode(response["content"], validate=False)
        if len(raw) != response.get("size"):
            raise ValueError("GitHub size differs from downloaded bytes")
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if blob != response.get("sha"):
            raise ValueError("GitHub Git-blob SHA differs from downloaded bytes")
        destination = source_root / repo.split("/")[-1] / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".partial", dir=destination.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, destination)
        finally:
            Path(temporary_name).unlink(missing_ok=True)
        row.update({
            "sha": blob,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "status": "retrieved",
        })
    except FileNotFoundError:
        row.update({"status": "not_found", "note": "Path does not exist at the pinned commit"})
    except Exception as exc:  # Keep a failed fetch explicit; never imply the old file is current.
        row["error"] = type(exc).__name__
    return row


def refresh(feed_path: Path, output_path: Path, jobs: int = 8) -> list[dict]:
    feed = json.loads(feed_path.read_text())
    official_meta = gh_json(f"repos/{OFFICIAL_REPO}")
    branch = official_meta.get("default_branch")
    if not isinstance(branch, str) or not branch:
        raise ValueError("Official reference-solution default branch unavailable")
    official_head = gh_json(f"repos/{OFFICIAL_REPO}/commits/{branch}").get("sha")
    if not isinstance(official_head, str) or not HEX40.fullmatch(official_head):
        raise ValueError("Official reference-solution head unavailable")
    tasks = pinned_tasks(feed, official_head)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(retrieve, tasks))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed", type=Path, default=ROOT / "docs" / "data" / "focus-feed.json")
    parser.add_argument("--output", type=Path, default=SOURCE_ROOT / "retrieval.json")
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 16:
        parser.error("--jobs must be between 1 and 16")
    try:
        rows = refresh(args.feed, args.output, args.jobs)
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        parser.exit(1, f"refresh_sources: {exc}\n")
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"source_files": len(rows), "counts": counts, "output": str(args.output)}, indent=2))
    return 0 if counts.get("unavailable", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
