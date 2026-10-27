#!/usr/bin/env python3
"""Refresh GitHub peer-head observations; never automate DrivenData access.

DrivenData terms prohibit automated monitoring, so the leaderboard remains a dated,
manual observation. A changed peer commit is not a re-audit or authorization.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LEADERBOARD = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"


class Tables(HTMLParser):
    """Extract visible text cells, tolerating nested markup within each table cell."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._ignore = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._ignore += 1
        if tag == "table" and self._table is None:
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("th", "td") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._ignore:
            self._ignore -= 1
        if tag in ("th", "td") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None and not self._ignore:
            self._cell.append(data)


def parse_leaderboard(html: str) -> float:
    parser = Tables()
    parser.feed(html)
    for table in parser.tables:
        if not table:
            continue
        headers = [x.casefold() for x in table[0]]
        columns = [i for i, h in enumerate(headers) if "tversky" in h and "public" in h]
        if not columns:
            continue
        i = columns[0]
        for row in table[1:]:
            if not row or not re.fullmatch(r"\s*#?\s*1\s*", row[0]) or len(row) <= i:
                continue
            text = row[i].strip()
            if not re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", text):
                raise ValueError("first-rank score is not a single value in [0,1]")
            value = float(text)
            if not 0 <= value <= 1:
                raise ValueError("first-rank score outside [0,1]")
            return value
    raise ValueError("public leaderboard table or first rank not found")


def get(url: str, *, github: bool = False) -> bytes:
    if not github or urlparse(url).hostname != "api.github.com":
        raise ValueError("Automatic access is restricted to the public GitHub API")
    headers = {"User-Agent": "GEMS-Evidence-Workspace/1.0", "Accept": "application/vnd.github+json" if github else "text/html"}
    token = os.environ.get("GITHUB_TOKEN")
    if github and token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return response.read(5_000_000)


def refresh(previous: dict, manifest: dict, now: str) -> dict:
    result = {"schema_version": 1}
    old_lb = previous.get("leaderboard", {}) if isinstance(previous.get("leaderboard"), dict) else {}
    result["leaderboard"] = {**old_lb, "status": "stale_or_unavailable",
                             "last_reviewed_utc": now, "source": LEADERBOARD,
                             "reason": "Automatic DrivenData monitoring disabled under site terms; use only access permitted by the site."}

    refs: dict[str, str] = {}
    for row in manifest.get("rows", []):
        refs[row["site"]] = row["ref"]
    sites = []
    for site, pinned in sorted(refs.items()):
        try:
            url = f"https://api.github.com/repos/buffedlizard55-lab/{site}/commits/main"
            commit = json.loads(get(url, github=True))
            current = commit["sha"]
            if not re.fullmatch(r"[0-9a-f]{40}", current):
                raise ValueError("invalid GitHub commit")
            sites.append({"site": site, "audited_ref": pinned, "observed_head": current,
                          "changed_since_audit": current != pinned, "status": "checked"})
        except (KeyError, ValueError, TypeError, HTTPError, URLError, TimeoutError, OSError) as exc:
            sites.append({"site": site, "audited_ref": pinned, "observed_head": None,
                          "changed_since_audit": None, "status": "unavailable", "error": type(exc).__name__})
    result["peer_heads"] = {"last_attempt_utc": now, "sites": sites,
                            "note": "Head checks do not fetch TIFFs, verify uniqueness or approve submissions."}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data/feed.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/historical-manifest.json")
    args = parser.parse_args()
    previous = json.loads(args.output.read_text()) if args.output.exists() else {}
    now = datetime.now(timezone.utc).isoformat()
    result = refresh(previous, json.loads(args.manifest.read_text()), now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=args.output.parent, delete=False, encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, allow_nan=False)
        fh.write("\n")
        temp_name = fh.name
    os.replace(temp_name, args.output)
    print("Leaderboard:", result["leaderboard"]["status"], "; peer heads:", len(result["peer_heads"]["sites"]))


if __name__ == "__main__":
    main()
