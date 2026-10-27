import json
from pathlib import Path

import numpy as np
import pytest

from scripts.audit_h33_lineage import measure


ROOT = Path(__file__).resolve().parents[1]


def masks():
    foot = np.ones((7, 7), dtype=bool)
    known = np.zeros_like(foot)
    known[3, 3] = True
    d28 = np.zeros_like(foot)
    d28[3, 3] = d28[3, 5] = d28[0, 0] = True
    b2 = np.zeros_like(foot)
    b2[0, 0] = True
    return foot, known, d28, d28.copy(), b2


def test_exact_subtraction_and_two_pixel_boundary():
    result = measure(*masks())
    assert result['gemsdoe25_and_30_exact_dot_mask_equal']
    assert result['gemsdoe32_equals_30_after_two_pixel_exclusion']
    assert result['gemsdoe30_dots_removed_to_get_32'] == 2
    assert result['removed_within_two_pixels_of_catalogue'] == 2
    assert result['removed_beyond_two_pixels_of_catalogue'] == 0
    assert result['gemsdoe32_dots_added_to_30'] == 0


def test_added_and_retained_dots_prevent_false_lineage_claim():
    foot, known, a, b, c = masks()
    c[6, 6] = True
    c[3, 5] = True
    result = measure(foot, known, a, b, c)
    assert result['gemsdoe32_dots_added_to_30'] == 1
    assert result['gemsdoe32_retained_within_two_pixels'] == 1
    assert not result['gemsdoe32_equals_30_after_two_pixel_exclusion']


def test_empty_or_invalid_masks_fail_closed():
    foot, known, a, b, c = masks()
    with pytest.raises(ValueError):
        measure(foot, np.zeros_like(known), a, b, c)
    with pytest.raises(ValueError):
        measure(foot, known, a.astype(float), b, c)
    with pytest.raises(ValueError):
        measure(foot, known, a, b[:-1], c)
    foot[0, 0] = False
    with pytest.raises(ValueError):
        measure(foot, known, a, b, c)


def test_builder_rejects_inconsistent_or_rebound_geometry_evidence():
    from copy import deepcopy
    from scripts.build_site import check_h33_lineage

    report = json.loads((ROOT / 'evidence/h33-lineage-20261027.json').read_text())
    winners = json.loads((ROOT / 'sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json').read_text())['historical_winners']
    manifest = json.loads((ROOT / 'data/core-manifest.json').read_text())
    check_h33_lineage(report, winners, manifest)
    for mutation in ('hash', 'count', 'authorization'):
        bad = deepcopy(report)
        if mutation == 'hash':
            bad['input_hashes']['GEMSDOE32'] = '0' * 64
        elif mutation == 'count':
            bad['measurement']['removed_within_two_pixels_of_catalogue'] -= 1
        else:
            bad['slot_authorized'] = True
        with pytest.raises(ValueError):
            check_h33_lineage(bad, winners, manifest)


def test_saved_evidence_keeps_hash_identity_and_no_score_claim():
    report = json.loads((ROOT / 'evidence/h33-lineage-20261027.json').read_text())
    archived = json.loads((ROOT / 'sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json').read_text())
    for row in archived['historical_winners']:
        if row['repo'] in ('GEMSDOE25', 'GEMSDOE30', 'GEMSDOE32'):
            assert report['input_hashes'][row['repo']] == row['sha256']
    values = report['measurement']
    assert values['gemsdoe32_equals_30_after_two_pixel_exclusion']
    assert values['gemsdoe30_dots_removed_to_get_32'] == values['removed_within_two_pixels_of_catalogue']
    assert values['gemsdoe32_dots_added_to_30'] == 0
    assert report['candidate_generated'] is False and report['slot_authorized'] is False
    assert 'not HOLDOUT-DTI' in report['kind']
