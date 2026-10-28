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
from scripts.sync_focus_feed import Links, retain_last_success

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
        build(check_only=True)
        pages = [DOCS / name for name in ("index.html", "executive-summary.html", "submission.html", "research.html", "sources.html")]
        pages += sorted((DOCS / "sites").glob("*.html"))
        pages += [DOCS / "cadg-submod/index.html", DOCS / "cadg-submod/executive-summary.html"]
        self.assertEqual(len(pages), 16)
        for path in pages:
            parser = PageLinks()
            content = path.read_text()
            parser.feed(content)
            self.assertEqual(parser.h1, 1, path.name)
            self.assertIn('name="viewport"', content)
            self.assertEqual(parser.downloads, [], path.name)
            self.assertNotIn("Research Complete", content, path.name)
            self.assertNotIn("DOWNLOAD READY", content, path.name)
            for link in parser.links:
                uri = urlsplit(link)
                if not uri.scheme and not uri.netloc and uri.path:
                    target = (path.parent / unquote(uri.path)).resolve()
                    self.assertTrue(target.is_relative_to(DOCS.resolve()), (path, link))
                    self.assertTrue(target.is_file(), (path, link))
            if path.parent.name == "sites" or path.name in ("index.html", "executive-summary.html", "submission.html"):
                self.assertIn("DO NOT SUBMIT", content)

    def test_archive_builder_does_not_overwrite_active_pages(self):
        build(check_only=True)
        paths = [DOCS / name for name in ("index.html", "executive-summary.html", "research.html", "submission.html")]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        build_archive()
        after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        self.assertEqual(before, after)

    def test_current_negative_card_cannot_release_candidate(self):
        from copy import deepcopy
        from scripts.build_site import check_current_session_card
        card = json.loads((ROOT / "evidence/session-6ad17006-run-card.json").read_text())
        check_current_session_card(card)
        for keys, value in ((["selector_slot_authorized"], True), (["verdict"], "PROMOTE"),
                            (["raster", "sha256"], "a" * 64), (["holdout", "value"], 0.5),
                            (["leaderboard_estimate"], 0.5), (["organizer_confirmed_score"], 0.5),
                            (["proposed_submission_name"], "candidate"), (["weekly_slots_used_this_session"], False)):
            altered = deepcopy(card)
            target = altered
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value
            with self.assertRaises(ValueError):
                check_current_session_card(altered)

    def test_homepage_fails_closed_and_does_not_republish_legacy_claims(self):
        build(check_only=True)
        homepage = (DOCS / "index.html").read_text()
        self.assertIn("No eligible TIFF yet", homepage)
        self.assertIn("Download unavailable · DO NOT SUBMIT", homepage)
        self.assertIn("Not estimable", homepage)
        self.assertNotIn("Highest Leaderboard Score Reference: 0.4413", homepage)
        self.assertNotIn("DOWNLOAD READY", homepage)
        self.assertNotIn('download href="cadg-submod/downloads/', homepage)

    def test_source_feed_does_not_launder_scores_or_approvals(self):
        feed = json.loads((DOCS / "data/focus-feed.json").read_text())
        self.assertEqual(len(feed["rows"]), 9)
        self.assertFalse(feed["registry_complete"])
        for row in feed["rows"]:
            self.assertIsNone(row["accepted_score"])
            self.assertFalse(row["scientific_approval"])
            self.assertEqual(len(row["commit"]), 40)

    def test_current_session_card_is_explicitly_negative_and_scoreless(self):
        card = json.loads((ROOT / "evidence/session-12817d00-run-card.json").read_text())
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["ok_to_submit"])
        self.assertFalse(card["slot_authorized"])
        self.assertEqual(card["geological_experiments_this_session"], 0)
        self.assertEqual(card["weekly_slots_used_this_session"], 0)
        self.assertIsNone(card["holdout_dti"])
        self.assertIsNone(card["raster_sha256"])
        self.assertIsNone(card["submission_name"])
        self.assertLessEqual(len(card["submission_note"]), 140)

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

    def test_failed_refresh_preserves_only_last_good_source_not_approval(self):
        repo = "buffedlizard55-lab/GEMSDOE32"
        previous = {"checked_utc": "old", "rows": [{"repository": repo, "commit": "a" * 40,
                    "status": "PINNED_SOURCE_ONLY", "source_page": "docs/index.html", "accepted_score": .99, "scientific_approval": True}]}
        failed = [{"repository": repo, "status": "UNKNOWN_REFRESH_FAILED", "commit": None}]
        row = retain_last_success(failed, previous)[0]
        self.assertIsNone(row["commit"])
        self.assertIsNone(row["accepted_score"])
        self.assertFalse(row["scientific_approval"])
        self.assertEqual(row["last_successful_source"]["commit"], "a" * 40)
        self.assertEqual(row["last_successful_source"]["checked_utc"], "old")
        again = retain_last_success(failed, {"rows": [row]})[0]
        self.assertEqual(again["last_successful_source"], row["last_successful_source"])

    def test_malformed_incumbent_metadata_never_clears_its_prerequisite(self):
        import copy
        config = json.loads((ROOT / "config/research-session.json").read_text())
        good = {"evaluator_version": "synthetic-metadata-only", "fold_sha256": "a" * 64,
                "withheld_positives": 10, "value": .2, "ci95": [.1, .3]}
        for field, bad in (("value", True), ("ci95", [.3, .4]), ("fold_sha256", "wrong"), ("withheld_positives", 0), ("evaluator_version", " ")):
            changed = copy.deepcopy(config); changed["same_evaluator_incumbent"] = {**good, field: bad}
            self.assertTrue(any("incumbent" in failure for failure in assess(changed)["failures"]))

    def test_failed_preflight_cli_overwrites_stale_positive_receipt(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            config, output = Path(directory) / "bad.json", Path(directory) / "receipt.json"
            config.write_text("not json")
            output.write_text('{"research_ready":true,"submit_ready":true}')
            run = subprocess.run([sys.executable, str(ROOT / "scripts/preflight.py"), "--config", str(config), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            result = json.loads(output.read_text())
            self.assertFalse(result["research_ready"])
            self.assertFalse(result["submit_ready"])
            self.assertFalse(result["slot_authorized"])

    def test_check_mode_never_repairs_a_stale_individual_site(self):
        build(check_only=True)
        site = ROOT / "docs/sites/GEMSDOE32.html"
        original = site.read_text()
        try:
            site.write_text("stale sentinel")
            with self.assertRaisesRegex(ValueError, "stale"):
                build(check_only=True)
            self.assertEqual(site.read_text(), "stale sentinel")
        finally:
            site.write_text(original)

    def test_inherited_audit_matches_unchanged_saved_files_and_literal_rule(self):
        from scripts.audit_inherited_artifacts import inherited_files
        from scripts.build_site import check_inherited
        report = json.loads((ROOT / "evidence/inherited_literal_audit.json").read_text())
        check_inherited(report)
        self.assertEqual({r["file"] for r in report["rows"]}, set(inherited_files()))
        self.assertTrue(all(row["candidate_dot_overlap_fraction"] > .70 for row in report["rows"]))
        self.assertTrue(all(row["validator"]["ok"] for row in report["rows"]))
        self.assertFalse(report["slot_authorized"])
        bad = json.loads(json.dumps(report)); bad["rows"][0]["candidate_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            check_inherited(bad)

    def test_archived_research_clis_are_operationally_blocked(self):
        import ast
        from scripts.archive_guard import stop_archived_cli
        with self.assertRaisesRegex(SystemExit, "Archived session"):
            stop_archived_cli()
        for name in ("run_e1_holdout.py", "run_e2_unique.py", "run_e3_canary.py", "run_e3_hybrid.py", "run_kanler_h1.py", "finalize_candidate.py", "build_run_card.py", "write_run_card.py"):
            tree = ast.parse((ROOT / "scripts" / name).read_text())
            guard = next(n for n in tree.body if isinstance(n, ast.If) and "__name__" in ast.unparse(n.test))
            self.assertEqual(ast.unparse(guard.body[1]), "stop_archived_cli()")


if __name__ == "__main__":
    unittest.main()
