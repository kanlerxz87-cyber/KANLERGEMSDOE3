#!/usr/bin/env python3
"""Check whether the nine public GitHub heads changed since this review.

A changed head is a freshness warning, not an automatic scientific re-audit.
No predictions are downloaded, selected, or submitted.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def fetch_head(site: str) -> str:
    if not re.fullmatch(r"GEMSDOE(?:24|25|27|28|30|31|32|33|36)", site):
        raise ValueError("Unexpected repository")
    query = 'query($name:String!){repository(owner:"buffedlizard55-lab",name:$name){object(expression:"refs/heads/main"){oid}}}'
    response = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}", "-f", f"name={site}",
                               "--jq", ".data.repository.object.oid"],
                              capture_output=True, text=True, check=True, timeout=30)
    head = response.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ValueError("Invalid GitHub commit response")
    return head


def refresh(out: Path, *, fetch=fetch_head, now=None) -> dict:
    base = json.loads((ROOT / "data/peer_heads.json").read_text())
    heads = base["heads"]
    def check(item):
        site, reviewed = item
        try:
            current = fetch(site)
            if not re.fullmatch(r"[0-9a-f]{40}", current):
                raise ValueError("Invalid head")
            return {"site": site, "reviewed_head": reviewed, "current_head": current,
                    "changed": current != reviewed, "error": None}
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            return {"site": site, "reviewed_head": reviewed, "current_head": None,
                    "changed": None, "error": type(error).__name__}
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, sorted(heads.items())))
    failures = sum(row["error"] is not None for row in rows)
    timestamp = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    result = {
        "schema": "peer-freshness-v1", "checked_utc": timestamp,
        "reviewed_utc": base["observed_utc"], "status": "fresh" if failures == 0 else "error",
        "changed_count": sum(row["changed"] is True for row in rows),
        "error_count": failures, "sites": rows,
        "note": "Head checks only; no updated raster, score, holdout, or scientific evidence was validated.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    tmp.replace(out)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "data/peer_feed.json")
    parser.add_argument("--allow-error", action="store_true")
    args = parser.parse_args()
    result = refresh(args.out)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "fresh" or args.allow_error else 1


if __name__ == "__main__":
    sys.exit(main())
