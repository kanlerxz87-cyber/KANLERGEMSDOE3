from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data:
            self.ids.add(data["id"])
        for attr in ("href", "src"):
            if attr in data:
                self.links.append(data[attr])


def test_site_generated_from_evidence():
    subprocess.run([sys.executable, str(ROOT / "scripts/build_site.py"), "--check"], check=True)


def test_static_internal_links_exist():
    docs = ROOT / "docs"
    for file in docs.glob("*.html"):
        parser = Links()
        parser.feed(file.read_text())
        for raw in parser.links:
            url = urlsplit(raw)
            if url.scheme or url.netloc or raw.startswith("mailto:"):
                continue
            dest = (file.parent / unquote(url.path)).resolve() if url.path else file.resolve()
            assert dest.is_file(), f"{file.name}: missing {raw}"
            if url.fragment and dest.suffix == ".html":
                target = Links()
                target.feed(dest.read_text())
                assert url.fragment in target.ids, f"{file.name}: missing anchor {raw}"
