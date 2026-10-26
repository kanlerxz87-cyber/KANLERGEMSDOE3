from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse, unquote

from bootstrap import ROOT
from build_site import render_rows


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in {"a", "link", "script", "img"}:
            for key in ("href", "src"):
                if key in d:
                    self.urls.append(d[key])


def test_site_is_reproducible_and_has_nine_research_only_rows():
    audit = json.loads((ROOT / "data/portfolio_audit.json").read_text())
    rows = render_rows(audit)
    assert rows.count("<tr>") == 9 and rows.count("DO NOT SUBMIT") == 9
    assert all(site["leaderboard_estimate"] is None and not site["ok_to_submit"] for site in audit["sites"])
    before = [(ROOT / p).read_bytes() for p in ("index.html", "executive-summary.html")]
    subprocess.run([sys.executable, str(ROOT / "scripts/build_site.py")], cwd=ROOT, check=True)
    after = [(ROOT / p).read_bytes() for p in ("index.html", "executive-summary.html")]
    assert before == after


def test_site_links_resolve_and_status_is_front_and_center():
    for filename in ("index.html", "executive-summary.html"):
        page = ROOT / filename
        text = page.read_text()
        assert "DO NOT SUBMIT" in text
        assert "{{" not in text
        parser = Links(); parser.feed(text)
        for url in parser.urls:
            parsed = urlparse(url)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = (page.parent / unquote(parsed.path)).resolve()
            assert path.is_relative_to(ROOT.resolve())
            assert path.exists(), f"{filename}: missing {url}"
    homepage = (ROOT / "index.html").read_text()
    assert homepage.index("No new file is") < homepage.index("Nine sites. One honest comparison.")
    assert "Approved GeoTIFF unavailable" in homepage


def test_run_card_does_not_invent_candidate_or_results():
    run = json.loads((ROOT / "data/run_card.json").read_text())
    assert run["verdict"] == "negative" and not run["ok_to_submit"]
    assert run["raster_sha256"] is None and run["submission_name"] is None
    assert run["holdout_dti"]["score"] is None and run["holdout_dti"]["confidence_interval_95_percent"] is None
    assert run["experiments_run"] == 0 and run["competition_slots_used"] == 0
