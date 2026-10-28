#!/usr/bin/env python3
"""Bind the nine latest participant decision pages to both refreshed GitHub feeds.

This is a source-freshness and text-presence receipt only. It does not fetch or
compare new TIFFs, authenticate organizer score receipts, validate a model, or
approve a competition upload.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.github_source import sha256_file


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()

FOCUS_FEED = ROOT / "docs/data/focus-feed.json"
PEER_FEED = ROOT / "docs/data/feed.json"
RETRIEVAL = ROOT / "sources/retrieval.json"
OLD_REGISTRY = ROOT / "registry/focus_registry_manifest.json"
OUTPUT = ROOT / "evidence/session-20261028-focus-source-review.json"
SITES = (24, 25, 27, 28, 30, 31, 32, 33, 36)
DECISIONS = {
    "GEMSDOE24": "Participant page: research download only; SUBMIT NO.",
    "GEMSDOE25": "Participant page: no competition-ready TIFF, no eligible download, and no slot; SUBMIT NO.",
    "GEMSDOE27": "Participant page: DO NOT SUBMIT; no candidate approved and no historical or research TIFF should be uploaded.",
    "GEMSDOE28": "Participant page: no new TIFF approved; prior duplicates and missing validation remain blocking; SUBMIT NO.",
    "GEMSDOE30": "Participant page: no new TIFF; published calibration-lattice overlap blocks the historical artifact; SUBMIT NO.",
    "GEMSDOE31": "Participant page: newest H31-CC is negative and explicitly DO NOT SUBMIT.",
    "GEMSDOE32": "Participant page: no upload authorized; research artifacts remain DO NOT SUBMIT.",
    "GEMSDOE33": "Participant page: zero eligible candidates; research downloads only, SUBMIT NO.",
    "GEMSDOE36": "Participant page: literal uniqueness gate failed; no candidate or slot approved; SUBMIT NO.",
}


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def load(path: Path):
    return json.loads(path.read_text())


def build() -> dict:
    focus = load(FOCUS_FEED)
    peers = load(PEER_FEED)
    retrieval = load(RETRIEVAL)
    previous = load(OLD_REGISTRY)
    focus_rows = focus.get("rows")
    peer_rows = peers.get("peer_heads", {}).get("sites")
    if not isinstance(focus_rows, list) or not isinstance(peer_rows, list):
        raise ValueError("Both current focus and peer feeds must have site rows")
    expected_sites = {f"GEMSDOE{number}" for number in SITES}
    focus_by_site = {row.get("site"): row for row in focus_rows if isinstance(row, dict)}
    peer_by_site = {row.get("site"): row for row in peer_rows if isinstance(row, dict)}
    if set(focus_by_site) != expected_sites or set(peer_by_site) != expected_sites:
        raise ValueError("Both feeds must contain exactly the nine requested sites")
    if focus.get("all_refreshed") is not True:
        raise ValueError("Not every focus source is pinned successfully")
    old_refs = previous.get("refs")
    if not isinstance(old_refs, dict) or set(old_refs) != expected_sites:
        raise ValueError("Previous registry pins do not cover exactly the nine focus sites")
    retrieval_by_pair = {
        (row.get("repo"), row.get("path"), row.get("ref")): row
        for row in retrieval if isinstance(row, dict) and row.get("status") == "retrieved"
    }
    sites = []
    heads_match = True
    all_changed = True
    for site in sorted(expected_sites):
        row = focus_by_site[site]
        peer = peer_by_site[site]
        commit = row.get("commit")
        if (row.get("status") != "PINNED_SOURCE_ONLY" or not isinstance(commit, str)
                or not re.fullmatch(r"[0-9a-f]{40}", commit)):
            raise ValueError(f"Invalid pinned source row for {site}")
        repo = f"buffedlizard55-lab/{site}"
        if row.get("repository") != repo or peer.get("observed_head") != commit:
            heads_match = False
        if peer.get("status") != "checked" or peer.get("audited_ref") is None:
            heads_match = False
        if old_refs.get(site) == commit:
            all_changed = False
        path = row.get("source_page")
        if (not isinstance(path, str) or path.startswith("/")
                or ".." in PurePosixPath(path).parts or "\\" in path):
            raise ValueError(f"Unsafe source page path for {site}")
        pinned = retrieval_by_pair.get((repo, path, commit))
        local = ROOT / "sources" / site / path
        if not isinstance(pinned, dict) or not local.is_file():
            raise ValueError(f"Current source-page bytes are not retained for {site}")
        raw = local.read_bytes()
        sha256 = hashlib.sha256(raw).hexdigest()
        blob = git_blob_sha1(raw)
        if sha256 != pinned.get("sha256") or blob != pinned.get("sha"):
            raise ValueError(f"Retained source-page bytes do not match pinned metadata for {site}")
        parser = VisibleText()
        parser.feed(raw.decode("utf-8", "replace"))
        text = parser.text.casefold()
        if not any(marker in text for marker in ("do not submit", "submit: no", "submit no", "not ok to submit")):
            raise ValueError(f"Pinned participant page has no clear negative submission statement: {site}")
        sites.append({
            "site": site,
            "repository": repo,
            "commit": commit,
            "source_page": path,
            "source_url": row["source_url"],
            "source_page_git_blob_sha1": blob,
            "source_page_sha256": sha256,
            "participant_page_decision_summary": DECISIONS[site],
            "evidence_class": "PARTICIPANT_SOURCE_PAGE_NOT_ORGANIZER_RECEIPT",
        })
    if not heads_match:
        raise ValueError("Refreshed focus and peer-head feeds are inconsistent")
    old_generated = previous.get("generated_utc")
    if not all_changed:
        raise ValueError("At least one focus source still equals an old registry ref; do not imply a full refresh")
    return {
        "schema_version": 1,
        "kind": "NINE_SITE_PARTICIPANT_SOURCE REVIEW — NOT SCORE RECEIPTS",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "focus_feed_checked_utc": focus.get("checked_utc"),
        "peer_head_checked_utc": peers.get("peer_heads", {}).get("last_attempt_utc"),
        "feed_hashes": {
            "focus_feed_sha256": sha256_file(FOCUS_FEED),
            "peer_feed_sha256": sha256_file(PEER_FEED),
            "retrieval_manifest_sha256": sha256_file(RETRIEVAL),
            "previous_registry_manifest_sha256": sha256_file(OLD_REGISTRY),
        },
        "feeds_consistent_for_all_nine": heads_match,
        "all_nine_heads_differ_from_previous_registry": all_changed,
        "previous_registry_generated_utc": old_generated,
        "current_site_decisions": sites,
        "score_provenance": {
            "current_official_leaderboard": "STALE_OR_UNAVAILABLE; the stored observation is not a current score and is not used as a projection.",
            "historical_site_scores": "OWNER/USER-REPORTED unless bound to an organizer receipt; no new receipt was found in this source-page review.",
            "best_historical_claim": "0.2778, owner/user-reported and not organizer-confirmed; not a new candidate estimate.",
        },
        "raster_audit": {
            "current_refreshed_tree_raster_audit_performed": False,
            "complete_representation_resolved_registry": False,
            "novelty_clearance": False,
            "reason": "All nine heads moved since the previous registry snapshot. Source-page freshness does not compare new TIFF bytes, surfaces, or final dots.",
        },
        "decision": "DO NOT SUBMIT; this project authorizes no file or slot.",
        "candidate_generated": False,
        "slot_authorized": False,
        "organizer_confirmed_score": None,
        "leaderboard_estimate": None,
    }


def main() -> int:
    receipt = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "output": str(OUTPUT),
        "focus_feed_checked_utc": receipt["focus_feed_checked_utc"],
        "feeds_consistent_for_all_nine": receipt["feeds_consistent_for_all_nine"],
        "all_nine_heads_differ_from_previous_registry": receipt["all_nine_heads_differ_from_previous_registry"],
        "candidate_generated": receipt["candidate_generated"],
        "slot_authorized": receipt["slot_authorized"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
