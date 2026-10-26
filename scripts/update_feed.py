#!/usr/bin/env python3
"""Refresh the public-leader snapshot for a Pages build, without logging in.

Failures are explicit and retain the last observed value with its old timestamp;
they never turn an inaccessible page into a fresh leaderboard claim.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.stack: list[dict] = []
        self.ignore = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style"):
            self.ignore += 1
        if tag == "table":
            self.stack.append({"rows": [], "row": None, "cell": None})
        elif self.stack and tag == "tr":
            self.stack[-1]["row"] = []
        elif self.stack and tag in ("td", "th") and self.stack[-1]["row"] is not None:
            self.stack[-1]["cell"] = []
        elif self.stack and tag == "br" and self.stack[-1]["cell"] is not None:
            self.stack[-1]["cell"].append(" ")

    def handle_data(self, data: str) -> None:
        if self.stack and not self.ignore and self.stack[-1]["cell"] is not None:
            self.stack[-1]["cell"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self.ignore:
            self.ignore -= 1
        if not self.stack:
            return
        state = self.stack[-1]
        if tag in ("td", "th") and state["cell"] is not None:
            state["row"].append(" ".join("".join(state["cell"]).split()))
            state["cell"] = None
        elif tag == "tr" and state["row"] is not None:
            state["rows"].append(state["row"])
            state["row"] = None
        elif tag == "table":
            self.tables.append(self.stack.pop()["rows"])


def parse_leader(html: str) -> str:
    parser = TableParser()
    parser.feed(html)
    candidates: list[str] = []
    for table in parser.tables:
        for i, header in enumerate(table):
            lowered = [c.lower() for c in header]
            rank_cols = [j for j, cell in enumerate(lowered) if "rank" in cell]
            score_cols = [j for j, cell in enumerate(lowered) if "tversky" in cell]
            if len(rank_cols) != 1 or len(score_cols) != 1:
                continue
            rcol, scol = rank_cols[0], score_cols[0]
            for row in table[i + 1:]:
                if max(rcol, scol) >= len(row) or not re.fullmatch(r"#?\s*1", row[rcol].strip()):
                    continue
                # Avoid grabbing submission counts, dates, or a number from an adjacent cell.
                text = row[scol].strip()
                if re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", text):
                    candidates.append(text)
    if len(candidates) != 1:
        raise ValueError("Could not identify exactly one rank-1 DW-Tversky cell")
    return candidates[0]


def fetch_public_page() -> bytes:
    req = Request(URL, headers={"User-Agent": "GEMS-evidence-dashboard/1.0 (+public leaderboard)"})
    with urlopen(req, timeout=30) as response:
        u = urlparse(response.geturl())
        if response.status != 200 or u.scheme != "https" or u.hostname != "www.drivendata.org" or u.path != urlparse(URL).path:
            raise ValueError("Unexpected redirect or response; not the public leaderboard")
        body = response.read(10_000_001)
        if len(body) > 10_000_000:
            raise ValueError("Leaderboard response too large")
        return body


def refresh(out: Path, *, fetch=fetch_public_page, now=None) -> dict:
    now = now or datetime.now(timezone.utc)
    when = now.isoformat().replace("+00:00", "Z")
    previous = {}
    if out.is_file():
        try:
            previous = json.loads(out.read_text())
        except (ValueError, OSError):
            previous = {}
    base = {"schema": "leaderboard-feed-v1", "source": URL, "checked_utc": when,
            "evidence_class": "ORGANIZER-PUBLISHED-LEADERBOARD",
            "note": "Public leaderboard leader, not an artifact-linked submission receipt or a forecast."}
    try:
        body = fetch()
        score = parse_leader(body.decode("utf-8", errors="strict"))
        base.update(status="fresh", public_leader=score, last_success_utc=when,
                    source_body_sha256=hashlib.sha256(body).hexdigest())
    except (OSError, URLError, UnicodeError, ValueError) as error:
        # Never reuse an unrelated or malformed prior snapshot as authoritative.
        keep = previous.get("source") == URL and previous.get("schema") == "leaderboard-feed-v1"
        base.update(status="error", public_leader=previous.get("public_leader") if keep else None,
                    last_success_utc=previous.get("last_success_utc") if keep else None,
                    source_body_sha256=previous.get("source_body_sha256") if keep else None,
                    error=f"{type(error).__name__}: {str(error)[:180]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(base, indent=2, allow_nan=False) + "\n")
    tmp.replace(out)
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/live_feed.json"))
    parser.add_argument("--allow-error", action="store_true", help="publish explicit error/stale status rather than fail the build")
    args = parser.parse_args()
    result = refresh(args.out)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "fresh" or args.allow_error else 1


if __name__ == "__main__":
    sys.exit(main())
