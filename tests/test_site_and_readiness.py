from datetime import datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

from scripts.build_site import build
from scripts.preflight import assess
from scripts.review import build as build_archive
from scripts.sync_focus_feed import Links

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.h1 = 0
        self.downloads = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if "download" in attrs:
            self.downloads.append(attrs)
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


class SiteAndReadinessTests(unittest.TestCase):
    def test_all_active_pages_have_local_links_and_no_approved_downloads(self):
        build()
        pages = [DOCS / name for name in ("index.html", "executive-summary.html", "submission.html", "research.html", "sources.html")]
        pages += sorted((DOCS / "sites").glob("*.html"))
        self.assertEqual(len(pages), 14)
        for path in pages:
            parser = PageLinks()
            content = path.read_text()
            parser.feed(content)
            self.assertEqual(parser.h1, 1, path.name)
            self.assertIn('name="viewport"', content)
            self.assertEqual(parser.downloads, [], path.name)
            for link in parser.links:
                uri = urlsplit(link)
                if not uri.scheme and not uri.netloc and uri.path:
                    target = (path.parent / unquote(uri.path)).resolve()
                    self.assertTrue(target.is_relative_to(DOCS.resolve()), (path, link))
                    self.assertTrue(target.is_file(), (path, link))
            if path.parent.name == "sites" or path.name in ("index.html", "executive-summary.html", "submission.html"):
                self.assertIn("DO NOT SUBMIT", content)

    def test_archive_builder_does_not_overwrite_active_pages(self):
        build()
        paths = [DOCS / name for name in ("index.html", "executive-summary.html", "research.html", "submission.html")]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        build_archive()
        after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        self.assertEqual(before, after)

    def test_source_feed_does_not_launder_scores_or_approvals(self):
        feed = json.loads((DOCS / "data/focus-feed.json").read_text())
        self.assertEqual(len(feed["rows"]), 9)
        self.assertFalse(feed["registry_complete"])
        for row in feed["rows"]:
            self.assertIsNone(row["accepted_score"])
            self.assertFalse(row["scientific_approval"])
            self.assertEqual(len(row["commit"]), 40)

    def test_source_html_parsing_does_not_execute_html(self):
        parser = Links()
        parser.feed('<title>A &amp; B</title><meta http-equiv="REFRESH" content="0; URL=docs/index.html"><a href="x.tif">File</a>')
        self.assertEqual(parser.title, "A & B")
        self.assertEqual(parser.redirect, "docs/index.html")
        self.assertEqual(parser.hrefs, ["x.tif"])

    def test_budget_and_lane_fail_closed(self):
        config = json.loads((ROOT / "config/research-session.json").read_text())
        now = datetime(2026, 10, 26, 22, 0, tzinfo=timezone.utc)
        result = assess(config, now=now)
        self.assertFalse(result["research_ready"])
        self.assertFalse(result["submit_ready"])
        self.assertFalse(result["slot_authorized"])
        self.assertTrue(any("lane" in message for message in result["failures"]))
        self.assertTrue(any("operator" in message for message in result["failures"]))
        self.assertIsNone(result["leaderboard_estimate"])
        self.assertFalse(any("budget" in message for message in result["failures"]))
        late = assess(config, now=now + timedelta(hours=3))
        self.assertTrue(any("budget" in message for message in late["failures"]))
        config["geological_experiments"] = [{}, {}, {}]
        exhausted = assess(config, now=now)
        self.assertTrue(any("budget" in message for message in exhausted["failures"]))

    def test_missing_or_malformed_config_never_ready(self):
        for config in (None, [], 7):
            result = assess(config)
            self.assertFalse(result["research_ready"])
            self.assertFalse(result["submit_ready"])


if __name__ == "__main__":
    unittest.main()
