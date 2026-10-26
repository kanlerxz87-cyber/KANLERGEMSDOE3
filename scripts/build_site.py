#!/usr/bin/env python3
"""Render the static Pages front door from the pinned forensic audit."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render_rows(audit: dict) -> str:
    sites = audit.get("sites", [])
    expected = {f"GEMSDOE{i}" for i in (24, 25, 27, 28, 30, 31, 32, 33, 36)}
    if {s.get("site") for s in sites} != expected or len(sites) != len(expected):
        raise ValueError("The audit must contain exactly the nine named historical sites")
    parts = []
    for row in sites:
        site = escape(row["site"])
        filename = escape(row["filename"], quote=True)
        href = escape(row["reference_url"] + "?raw=1", quote=True)
        claim = escape(row["owner_reported_claim_not_receipt"])
        overlap = row.get("max_directed_overlap_other_focus_site")
        nearest = escape(row.get("closest_other_focus_site") or "unknown")
        duplicate = row.get("duplicate_in_nine_site_sample")
        if overlap is None or duplicate is not True or not 0 <= overlap <= 1:
            raise ValueError(f"Incomplete or unexpected uniqueness evidence for {site}")
        site_href = f"https://buffedlizard55-lab.github.io/{site}/"
        if site in {"GEMSDOE31", "GEMSDOE32", "GEMSDOE36"}:
            site_href += "docs/"
        parts.append(f'''<tr><td><a class="site-name" href="{site_href}">{site} ↗</a><small class="sr-only">Site review</small></td>
        <td class="claim"><strong>{claim}</strong><small>user-reported · unverified</small></td>
        <td><a class="file-link" href="{href}" title="{filename}" aria-label="Download {filename} for research only"><span class="filename">{filename}</span><small>Research reference ↗</small></a></td>
        <td class="estimate">Not estimable</td><td class="unique"><b>No</b><small>{overlap:.2%} near {nearest}</small></td><td><span class="no-pill">DO NOT SUBMIT</span></td></tr>''')
    return "\n".join(parts)


def main() -> None:
    audit = json.loads((ROOT / "data/portfolio_audit.json").read_text())
    feed = json.loads((ROOT / "data/live_feed.json").read_text())
    peer_feed = json.loads((ROOT / "data/peer_feed.json").read_text())
    html = (ROOT / "site/index.template.html").read_text()
    html = html.replace("{{PORTFOLIO_ROWS}}", render_rows(audit))
    html = html.replace("{{AUDIT_DATE}}", escape(audit["generated_utc"][:10]))
    html = html.replace("{{LEADER}}", escape(str(feed.get("public_leader") or "Unavailable")))
    html = html.replace("{{FEED_STATUS}}", "Snapshot, not live · observed " + escape(str(feed.get("last_success_utc") or "unknown")))
    if peer_feed.get("status") == "fresh":
        freshness = f"{int(peer_feed['changed_count'])} peer heads changed since review · re-audit may be needed"
    else:
        freshness = "Peer freshness check incomplete · review freshness is unknown"
    html = html.replace("{{PEER_FRESHNESS}}", escape(freshness))
    if "{{" in html:
        raise ValueError("Unresolved site template placeholder")
    (ROOT / "index.html").write_text(html)
    (ROOT / "executive-summary.html").write_text((ROOT / "site/executive.template.html").read_text())
    print("Built index.html and executive-summary.html from the historical audit.")


if __name__ == "__main__":
    main()
