#!/usr/bin/env python3
"""Refresh nine participant repository snapshots, not official scores or approvals.

Pins HEAD once per repository, then uses only that commit. A failed refresh is
reported as unknown/stale and never replaces evidence with an optimistic claim.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import GitHubSource, source_path

SITES = (24, 25, 27, 28, 30, 31, 32, 33, 36)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.redirect = None
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            match = re.search(r"url\s*=\s*(.+)", attrs.get("content", ""), re.I)
            if match:
                self.redirect = match[1].strip(" '\"")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def refresh_one(number: int, cache: Path | None = None) -> dict:
    short = "GEMSDOE" + str(number)
    repo = "buffedlizard55-lab/" + short
    result = {"site": short, "repository": repo, "participant_source": True, "scientific_approval": False, "accepted_score": None}
    try:
        source = GitHubSource(cache)
        commit = source.head(repo)
        paths = set(source.paths(repo, commit))
        candidates = ["docs/index.html", "index.html"]
        page = next((path for path in candidates if path in paths), None)
        if page is None:
            raise ValueError("No source homepage found")
        seen = set()
        while True:
            if page in seen or len(seen) >= 4:
                raise ValueError("Cyclic/excessive source homepage redirect")
            seen.add(page)
            data = source.read(repo, commit, page).decode("utf-8")
            parser = Links()
            parser.feed(data)
            if not parser.redirect:
                break
            target = urlsplit(parser.redirect)
            if target.scheme or target.netloc:
                raise ValueError("External redirect not followed as trusted source evidence")
            # Resolve relative paths without allowing escape from the repository.
            pieces = list(PurePosixPath(page).parent.parts)
            for piece in unquote(target.path).split("/"):
                if piece == "..":
                    if not pieces:
                        raise ValueError("Unsafe redirect")
                    pieces.pop()
                elif piece not in ("", "."):
                    pieces.append(piece)
            page = "/".join(pieces)
            if page not in paths:
                raise ValueError("Redirect target absent from pinned tree")
        tif_paths = sorted(p for p in paths if p.lower().endswith((".tif", ".tiff")))
        return {**result, "status": "PINNED_SOURCE_ONLY", "commit": commit, "source_page": page, "source_url": f"https://github.com/{repo}/blob/{commit}/{page}", "source_title": parser.title.strip(), "raster_paths_in_tree": len(tif_paths), "continuous_cache_paths": sorted(p for p in paths if p.lower().endswith((".npy", ".npz"))), "homepage_tiff_links": sum(bool(re.search(r"\.tiff?(?:[?#]|$)", h, re.I)) for h in parser.hrefs), "note": "Source freshness only. Homepage statements, historical scores and any approval labels are not inherited by this project."}
    except Exception as exc:
        return {**result, "status": "UNKNOWN_REFRESH_FAILED", "error": str(exc), "commit": None}



def retain_last_success(rows: list[dict], previous: dict) -> list[dict]:
    """Keep old source identity on failures, never its approval/score fields."""
    previous_rows = previous.get("rows", []) if isinstance(previous, dict) else []
    if not isinstance(previous_rows, list):
        previous_rows = []
    prior = {row.get("repository"): row for row in previous_rows if isinstance(row, dict)}
    output = []
    for current in rows:
        row = {**current, "scientific_approval": False, "accepted_score": None}
        if row.get("status") == "UNKNOWN_REFRESH_FAILED":
            old = prior.get(row.get("repository"), {})
            old = old if old.get("status") == "PINNED_SOURCE_ONLY" else old.get("last_successful_source", {})
            if isinstance(old, dict) and isinstance(old.get("commit"), str) and re.fullmatch(r"[0-9a-f]{40}", old["commit"]):
                page = old.get("source_page")
                try:
                    if not isinstance(page, str):
                        raise ValueError("Missing old source page")
                    source_path(page)
                except ValueError:
                    pass
                else:
                    row["last_successful_source"] = {
                        "commit": old["commit"], "source_page": page,
                        "source_url": f"https://github.com/{row['repository']}/blob/{old['commit']}/{page}",
                        "checked_utc": old.get("checked_utc", previous.get("checked_utc")),
                    }
        output.append(row)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "data" / "focus-feed.json")
    args = parser.parse_args()
    try:
        previous = json.loads(args.output.read_text())
    except (OSError, ValueError):
        previous = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(refresh_one, SITES))
    rows = retain_last_success(rows, previous)
    report = {"schema_version": 1, "checked_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "kind": "PARTICIPANT_SOURCE_CHANGE_FEED_NOT_SCORE_RECEIPTS", "rows": rows, "all_refreshed": all(row["status"] == "PINNED_SOURCE_ONLY" for row in rows), "registry_complete": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Pinned {sum(row['status'] == 'PINNED_SOURCE_ONLY' for row in rows)}/{len(rows)} focus repository sources; no approvals or scores inferred.")
    return 0 if report["all_refreshed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
