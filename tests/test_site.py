from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import json
import pytest
import build_site

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=set(); self.lang=None
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag == 'html': self.lang=d.get('lang')
        if tag in ('a','link','script'):
            href=d.get('href') or d.get('src')
            if href: self.links.append(href)
        if d.get('id'): self.ids.add(d['id'])


def test_generated_pages_current_and_local_links_exist():
    for name, contents in build_site.render().items():
        assert (ROOT/name).read_text() == contents + '\n'
        parser=Links(); parser.feed(contents)
        assert parser.lang == 'en' and 'main' in parser.ids
        for href in parser.links:
            url=urlparse(href)
            if url.scheme or url.netloc: continue
            target = ((ROOT/name).parent / unquote(url.path)).resolve() if url.path else (ROOT/name)
            assert target.is_file(), (name, href, target)
            if url.fragment and target.suffix == '.html':
                p=Links();p.feed(target.read_text());assert url.fragment in p.ids, (name,href)


def test_site_is_explicitly_negative_and_nine_rows():
    pages = build_site.render()
    home=pages['index.html']
    assert 'Do not submit' in home and 'No file cleared yet' in home
    assert 'disabled aria-describedby="download-reason"' in home
    assert home.count('<tr><td><a class="site-name"') == 9
    assert home.count('USER/OWNER-REPORTED · UNVERIFIED') == 9
    assert 'Not run · n — · CI —' in home
    assert 'not a complete fleet audit' in home


def test_fail_closed_on_modified_promotion_or_missing_witness(monkeypatch):
    real = build_site.load
    def modified(path):
        value = real(path)
        if path == 'evidence/run_card.json': value['verdict']='promote'
        return value
    monkeypatch.setattr(build_site, 'load', modified)
    with pytest.raises(ValueError, match='unverified promotion'):
        build_site.render()


def test_one_negative_run_card_no_fabricated_score():
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['raster_sha256'] is None and card['submission_name'] is None
    assert card['holdout']['dti'] is None
    assert card['holdout']['withheld_positive_pixels'] is None
    assert card['experiments_run'] == card['submission_slots_used'] == 0
