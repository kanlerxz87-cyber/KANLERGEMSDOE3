import copy
import json
from pathlib import Path

import pytest

from scripts.build_site import check_poisson_archive

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return (json.loads((ROOT / 'evidence/parallel-poisson-audit-20261027.json').read_text()),
            (ROOT / 'evidence/candidate_poisson_20261027.json').read_bytes(),
            json.loads((ROOT / 'research/registry-lock.json').read_text()))


def test_parallel_control_stays_negative_and_its_twins_are_bound():
    report, card, registry = fixture()
    check_poisson_archive(report, card, registry)
    assert report['same_in_footprint_dot_mask'] is True
    for encoding in ('zeros', 'nan'):
        measured = report['measurements'][encoding]['lattice']
        assert measured['candidate_dots'] == 37654
        assert measured['candidate_dots_within_3px_of_lattice'] == 37611
        assert measured['candidate_dot_overlap_fraction'] > .70
        assert report['files'][encoding]['zip_contains_exact_tiff_only'] is True
    assert report['slot_authorized'] is False
    assert report['full_registry_compared'] is False
    assert report['surface_registry_comparison'] is None
    assert 'rejected upload was not supplied' in report['range_error_claim']


def test_altered_card_measurement_or_authorization_refuses_build():
    report, card, registry = fixture()
    with pytest.raises(ValueError):
        check_poisson_archive(report, card + b' ', registry)
    for mutation in ('file', 'zip', 'overlap', 'slot', 'surface'):
        bad = copy.deepcopy(report)
        if mutation == 'file':
            bad['files']['zeros']['sha256'] = '0' * 64
        elif mutation == 'zip':
            bad['files']['nan']['zip_sha256'] = '0' * 64
        elif mutation == 'overlap':
            bad['measurements']['zeros']['lattice']['candidate_dot_overlap_fraction'] = .5
        elif mutation == 'slot':
            bad['slot_authorized'] = True
        else:
            bad['surface_registry_comparison'] = {'passed': True}
        with pytest.raises(ValueError):
            check_poisson_archive(bad, card, registry)


def test_audit_failure_overwrites_a_stale_positive_output(tmp_path, monkeypatch):
    from scripts import audit_poisson_archive as audit
    out = tmp_path / 'result.json'
    out.write_text('{"slot_authorized": true}')
    monkeypatch.setattr(audit, 'run', lambda restore=False: (_ for _ in ()).throw(ValueError('missing input')))
    monkeypatch.setattr('sys.argv', ['audit', '--output', str(out)])
    assert audit.main() == 2
    result = json.loads(out.read_text())
    assert result['verdict'] == 'negative' and result['slot_authorized'] is False
