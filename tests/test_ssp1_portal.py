"""The isolated parallel study must not replace root lane evidence or authorize upload."""
import hashlib
import json
from pathlib import Path

from publish_ssp1 import publish

ROOT = Path(__file__).resolve().parents[1]


def test_isolated_negative_portal_is_current_and_downloads_the_measured_bytes():
    assert publish(check_only=True) >= 40
    c = json.loads((ROOT/'studies/ssp1/evidence/run_card.json').read_text())
    artifact = ROOT/'docs/ssp1/downloads'/c['downloads']['tif']
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == c['raster_sha256']
    assert c['verdict'] == 'negative' and c['decision']['ok_to_submit'] is False
    assert len(list((ROOT/'docs/ssp1').rglob('*.html'))) == 15
    assert 'ssp1/executive-summary.html' in (ROOT/'docs/index.html').read_text()


def test_parallel_evaluators_and_cards_are_not_overwritten_or_combined():
    c = json.loads((ROOT/'studies/ssp1/evidence/run_card.json').read_text())
    root = json.loads((ROOT/'evidence/run-card.json').read_text())
    assert c['hypothesis'] != root['hypothesis']
    assert c['holdout_dti']['evaluator_version'] != root['holdout_dti']['evaluator_version']
    assert (ROOT/'evidence/run_card.json').is_file()  # Prior GPC-3 card also preserved.
    assert (ROOT/'evidence/recovery-run-card.json').is_file()
    assert 'not directly comparable' in (ROOT/'README.md').read_text()
