#!/usr/bin/env python3
"""Compare immutable peer Git trees for raster-path changes, not approval.

No TIFF blobs are downloaded, no geometry or scores are inferred, and this
nine-repository inventory is not the complete parallel-run registry.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import GitHubSource, source_path  # noqa: E402
from scripts.sync_focus_feed import SITES  # noqa: E402

SHA = re.compile(r"[0-9a-f]{40}\Z")


def parse_raster_tree(raw: bytes) -> dict[str, dict]:
    """Parse `git ls-tree -r -z`: no Git/LFS blob contents are fetched."""
    result = {}
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, separator, raw_path = item.partition(b"\t")
        if not separator:
            raise ValueError("Malformed tree record")
        try:
            mode, kind, blob = metadata.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
        except (UnicodeError, ValueError) as exc:
            raise ValueError("Invalid tree record encoding") from exc
        if not path.lower().endswith((".tif", ".tiff")):
            continue
        source_path(path)
        if kind != "blob" or mode not in ("100644", "100755", "120000") or not SHA.fullmatch(blob) or path in result:
            raise ValueError("Invalid, repeated or non-blob raster tree record")
        result[path] = {"git_blob": blob, "mode": mode}
    return result


def tree(source: GitHubSource, repo: str, commit: str) -> dict[str, dict]:
    bare = source.repository(repo, commit)
    raw = source._run(["git", "-C", str(bare), "ls-tree", "-r", "-z", commit], capture_output=True).stdout
    return parse_raster_tree(raw)


def compare(before: dict, after: dict) -> dict:
    """Compare paths AND Git object IDs/modes; renamed files appear as add/remove."""
    old, new = set(before), set(after)
    added, removed = sorted(new - old), sorted(old - new)
    changed = sorted(path for path in old & new if before[path] != after[path])
    def row(path: str) -> dict:
        return {"path": path, "before": before.get(path), "after": after.get(path)}
    return {"before_raster_paths": len(before), "after_raster_paths": len(after),
            "added": [row(path) for path in added], "removed": [row(path) for path in removed],
            "changed": [row(path) for path in changed],
            "unchanged_count": len(old & new) - len(changed)}


def rows_by_site(feed: object) -> dict[str, dict]:
    if not isinstance(feed, dict) or not isinstance(feed.get("rows"), list):
        raise ValueError("Malformed source feed")
    sites = {"GEMSDOE" + str(number) for number in SITES}
    result = {}
    for row in feed["rows"]:
        if not isinstance(row, dict) or row.get("site") not in sites or row["site"] in result:
            raise ValueError("Unknown or duplicated focus site")
        if row.get("repository") != "buffedlizard55-lab/" + row["site"]:
            raise ValueError("Unexpected focus repository")
        result[row["site"]] = row
    if set(result) != sites:
        raise ValueError("Focus source feed is incomplete")
    return result


def observe(before_feed: dict, after_feed: dict, source_factory=GitHubSource) -> dict:
    before, after = rows_by_site(before_feed), rows_by_site(after_feed)
    def one(number: int) -> dict:
        site = "GEMSDOE" + str(number)
        a, b = before[site], after[site]
        base = {"site": site, "repository": b["repository"], "before_commit": a.get("commit"), "after_commit": b.get("commit"),
                "scientific_approval": False, "accepted_score": None}
        try:
            if (a.get("status") != "PINNED_SOURCE_ONLY" or b.get("status") != "PINNED_SOURCE_ONLY"
                    or not isinstance(a.get("commit"), str) or not SHA.fullmatch(a["commit"])
                    or not isinstance(b.get("commit"), str) or not SHA.fullmatch(b["commit"])):
                raise ValueError("Missing pinned commit; no changes inferred")
            source = source_factory()
            comparison = compare(tree(source, b["repository"], a["commit"]), tree(source, b["repository"], b["commit"]))
            for category in ("added", "changed"):
                for item in comparison[category]:
                    item["source_url"] = f"https://github.com/{b['repository']}/blob/{b['commit']}/{quote(item['path'], safe='/')}"
            for item in comparison["removed"]:
                item["source_url"] = f"https://github.com/{a['repository']}/blob/{a['commit']}/{quote(item['path'], safe='/')}"
            return {**base, "status": "PINNED_TREE_COMPARISON_ONLY", **comparison}
        except Exception as exc:
            return {**base, "status": "UNKNOWN", "error": str(exc)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(one, SITES))
    return {"schema_version": 1, "kind": "PARTICIPANT RASTER-PATH CHANGE INVENTORY; NOT SCORES OR APPROVAL",
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "baseline_checked_utc": before_feed.get("checked_utc"), "current_checked_utc": after_feed.get("checked_utc"),
            "rows": rows, "all_compared": all(row["status"] == "PINNED_TREE_COMPARISON_ONLY" for row in rows),
            "registry_complete": False, "scientific_approval": False,
            "limitations": ["Only nine peer repository trees are inventoried; other registries and continuous surfaces are not covered.",
                            "Git blob IDs identify tree objects, not independently verified TIFF SHA-256 or LFS content; no raster bytes or scores were checked.",
                            "Changes and symlinks require independent saved-byte, surface and final-dot audits before any novelty decision."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = observe(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
        code = 0 if result["all_compared"] else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result = {"schema_version": 1, "kind": "RASTER TREE INVENTORY FAILED", "all_compared": False,
                  "registry_complete": False, "scientific_approval": False, "error": str(exc)}
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Tree comparisons: {sum(r.get('status') == 'PINNED_TREE_COMPARISON_ONLY' for r in result.get('rows', []))}/{len(SITES)}; no score or approval inferred.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
