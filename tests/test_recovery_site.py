import copy
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
        build_site.build(check_only=True)

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
        card = json.loads((ROOT / 'evidence/run-card.json').read_text())
        for path in (ROOT / 'run-card.json', DOCS / 'run-card.json', DOCS / 'data/run_card.json', DOCS / 'data/run-card.json'):
            self.assertEqual(json.loads(path.read_text()), card)
        recovery = json.loads((ROOT / 'evidence/recovery-run-card.json').read_text())
        self.assertEqual(json.loads((DOCS / 'data/recovery-run-card.json').read_text()), recovery)
        self.assertEqual(recovery['verdict'], 'negative')
        self.assertIsNone(recovery['raster_sha256'])
        self.assertIsNone(recovery['score_estimate'])
        self.assertLessEqual(len(recovery['submission_note']), 140)
        parser = LinkParser()
        page = (DOCS / 'index.html').read_text(encoding='utf-8')
        parser.feed(page)
        self.assertEqual(parser.downloads, 0)
        self.assertIn('DO NOT SUBMIT', page)
        self.assertEqual(page.count('Historical file · research reference only; score not bound to bytes'), 9)
        self.assertEqual(page.count('Local mask policy; not a portal verdict'), 9)
        self.assertIn('full-footprint witness', page)

    def test_saturation_evidence_mutations_fail_closed(self):
        evidence = json.loads((ROOT / 'evidence/registry_saturation_20261026.json').read_text())
        registry = (ROOT / 'evidence/upstream/GEMSDOE31/registry/raster_registry.json').read_bytes()
        self.assertEqual(build_site.check_saturation(evidence, registry)['uncovered_allowed_pixels'], 0)
        for key, bad in [('uncovered_allowed_pixels', 1), ('witness_sha256', '0'*64),
                         ('universal_overlap_blocker', False)]:
            altered = copy.deepcopy(evidence); altered['measurement'][key] = bad
            with self.assertRaises(ValueError):
                build_site.check_saturation(altered, registry)
        with self.assertRaises(ValueError):
            build_site.check_saturation(evidence, registry + b' ')

    def test_evidence_copies_are_exact(self):
        for src, published in [
            ('evidence/registry_saturation_20261026.json', 'docs/data/registry_saturation.json'),
            ('evidence/feature_cache_recovery_20261026.json', 'docs/data/feature_cache_recovery.json'),
            ('registry/shared_template_pins.json', 'docs/data/shared_template_pins.json'),
        ]:
            self.assertEqual((ROOT / src).read_bytes(), (ROOT / published).read_bytes())


if __name__ == '__main__':
    unittest.main()
