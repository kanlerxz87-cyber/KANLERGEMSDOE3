import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts import build_site

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.downloads = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for field in ('href', 'src'):
            if field in values:
                self.links.append(values[field])
        if 'download' in values:
            self.downloads += 1


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_site.build()

    def test_current_pages_have_resolvable_local_links(self):
        for name in ('index.html', 'executive-summary.html', 'research.html',
                     'hypotheses.html', 'sources.html', 'summary.html', 'submission.html'):
            parser = LinkParser()
            page = DOCS / name
            parser.feed(page.read_text(encoding='utf-8'))
            for link in parser.links:
                target = urlsplit(link)
                if target.scheme or target.netloc or not target.path:
                    continue
                destination = (page.parent / unquote(target.path)).resolve()
                self.assertTrue(destination.is_relative_to(DOCS.resolve()), f'{name}: {link} leaves published site')
                self.assertTrue(destination.is_file(), f'{name}: missing {link}')

    def test_one_canonical_negative_card_and_no_download(self):
        card = json.loads((ROOT / 'run-card.json').read_text())
        for path in (DOCS / 'run-card.json', DOCS / 'data/run_card.json'):
            self.assertEqual(json.loads(path.read_text()), card)
        self.assertEqual(card['verdict'], 'negative')
        self.assertIsNone(card['raster_sha256'])
        self.assertIsNone(card['score_estimate'])
        self.assertLessEqual(len(card['submission_note']), 140)
        parser = LinkParser()
        page = (DOCS / 'index.html').read_text(encoding='utf-8')
        parser.feed(page)
        self.assertEqual(parser.downloads, 0)
        self.assertIn('DO NOT SUBMIT', page)
        self.assertEqual(page.count('Historical reference variant; score is not bound to these bytes.'), 9)
        self.assertEqual(page.count('Not a portal verdict'), 9)

    def test_evidence_copies_are_exact(self):
        for src, published in [
            ('evidence/registry_saturation_20261026.json', 'docs/data/registry_saturation.json'),
            ('evidence/feature_cache_recovery_20261026.json', 'docs/data/feature_cache_recovery.json'),
            ('registry/shared_template_pins.json', 'docs/data/shared_template_pins.json'),
        ]:
            self.assertEqual((ROOT / src).read_bytes(), (ROOT / published).read_bytes())


if __name__ == '__main__':
    unittest.main()
