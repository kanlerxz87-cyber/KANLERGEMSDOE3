"""The concurrent research artifact cannot be promoted on a nine-file screen."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_parallel_audit_and_historical_card_are_fail_closed():
    audit = json.loads((ROOT/'evidence/parallel-lattice-audit.json').read_text())
    card = json.loads((ROOT/'evidence/run_card.json').read_text())
    entries = json.loads((ROOT/'research/registry-lock.json').read_text())['entries']
    lattice = next(x for x in entries if x['id'] == 'registry-160')
    candidate = ROOT/audit['candidate']
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == audit['candidate_sha256']
    assert audit['candidate_sha256'] == audit['expected_owner_sha256'] == card['raster_sha256']
    assert audit['reference_sha256'] == lattice['sha256']
    assert audit['candidate_dots'] == card['dots'] == 37654
    assert audit['within_3px'] == audit['candidate_dots']
    assert audit['candidate_overlap'] == 1.0 and audit['duplicate']
    assert card['unique_vs_focus9'] and card['all_registry_novelty_verdict'] == 'duplicate'
    assert card['registered_lattice_overlap_3px'] == 1.0
    assert card['ok_to_submit'] is False and card['download_research'] is False
    mirror = ROOT/'docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be.run-card.json'
    assert json.loads(mirror.read_text()) == card


def test_parallel_status_mutations_fail_closed():
    from copy import deepcopy
    import pytest
    from scripts.check_parallel_audit import check
    audit = json.loads((ROOT/'evidence/parallel-lattice-audit.json').read_text())
    card = json.loads((ROOT/'evidence/run_card.json').read_text())
    registry = json.loads((ROOT/'research/registry-lock.json').read_text())
    check(audit, card, registry)
    for field, value in [('candidate_overlap', .3), ('duplicate', False),
                         ('candidate_sha256', '0'*64), ('within_3px', 1)]:
        bad = deepcopy(audit); bad[field] = value
        with pytest.raises(ValueError): check(bad, card, registry)
    for field, value in [('ok_to_submit', True), ('download_research', True),
                         ('all_registry_novelty_verdict', 'unique')]:
        bad = deepcopy(card); bad[field] = value
        with pytest.raises(ValueError): check(audit, bad, registry)


def test_parallel_strict_footprint_report_does_not_claim_portal_result():
    audit = json.loads((ROOT/'evidence/parallel-format-audit.json').read_text())
    card = json.loads((ROOT/'evidence/run_card.json').read_text())
    inputs = {x['id']: x for x in json.loads((ROOT/'data/input-manifest.json').read_text())['inputs']}
    assert audit['candidate_sha256'] == card['raster_sha256']
    assert audit['template_sha256'] == inputs['sample_submission']['sha256']
    assert audit['ok'] is False and audit['valid_outside_footprint'] == 7111787
    assert audit['nonfinite_inside'] == 0 and audit['finite_range_inside'] == [0.0, 1.0]
    assert 'not a portal receipt' in audit['interpretation']
