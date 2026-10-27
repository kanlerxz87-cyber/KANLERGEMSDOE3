import copy
import json
from pathlib import Path

import pytest

from scripts.build_site import check_kpl36_receipt

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    report = json.loads((ROOT / 'evidence/kpl36-lattice-audit-20261027.json').read_text())
    card = (ROOT / 'evidence/upstream/GEMSDOE36/kpl36-run-card-61783525.json').read_bytes()
    registry = json.loads((ROOT / 'research/registry-lock.json').read_text())
    return report, card, registry


def test_peer_promote_conflicts_with_independent_literal_stop():
    report, card, registry = fixture()
    check_kpl36_receipt(report, card, registry)
    measurement = report['final_dot_lattice_comparison']
    assert measurement['candidate_dots'] == 37654
    assert measurement['candidate_dots_within_3px_of_lattice'] == 37341
    assert measurement['candidate_dot_overlap_fraction'] > .70
    assert report['peer_source']['peer_verdict'] == 'promote'
    assert report['verdict'] == 'negative'
    assert report['slot_authorized'] is False
    assert report['surface_registry_comparison'] is None
    assert report['full_registry_compared'] is False
    assert report['validator']['portal_acceptance_verified'] is False
    assert report['validator']['organizer_acceptance'] == 'NOT_TESTED'


def test_altered_sources_counts_or_authorization_cannot_build_site():
    report, card, registry = fixture()
    with pytest.raises(ValueError):
        check_kpl36_receipt(report, card + b' ', registry)
    for mutation in ('candidate_hash', 'lattice_hash', 'overlap', 'score', 'slot', 'surface'):
        bad = copy.deepcopy(report)
        if mutation == 'candidate_hash':
            bad['final_dot_lattice_comparison']['candidate_sha256'] = '0' * 64
        elif mutation == 'lattice_hash':
            bad['final_dot_lattice_comparison']['lattice_sha256'] = '0' * 64
        elif mutation == 'overlap':
            bad['final_dot_lattice_comparison']['candidate_dot_overlap_fraction'] = .5
        elif mutation == 'score':
            bad['peer_source']['peer_holdout']['dti'] = .9
        elif mutation == 'slot':
            bad['slot_authorized'] = True
        else:
            bad['surface_registry_comparison'] = {'passed': True}
        with pytest.raises(ValueError):
            check_kpl36_receipt(bad, card, registry)


def test_missing_inputs_fails_cli_and_clears_a_stale_output(tmp_path, monkeypatch):
    from scripts import audit_kpl36_external as external
    out = tmp_path / 'result.json'
    out.write_text('{"slot_authorized": true}')
    monkeypatch.setattr(external, 'run', lambda restore=False: (_ for _ in ()).throw(ValueError('missing pinned input')))
    monkeypatch.setattr('sys.argv', ['audit', '--output', str(out)])
    assert external.main() == 2
    result = json.loads(out.read_text())
    assert result['verdict'] == 'negative' and result['slot_authorized'] is False
