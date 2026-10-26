#!/usr/bin/env python3
"""Fail closed if the concurrent research-file lattice receipt is inconsistent."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PATH = 'docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be-zeros.tif'


def check(audit, card, registry, root=ROOT):
    if audit.get('candidate') != EXPECTED_PATH or card.get('tif') != EXPECTED_PATH:
        raise ValueError('parallel artifact path mismatch')
    p = root/EXPECTED_PATH
    if not p.is_file():
        raise ValueError('parallel historical artifact missing')
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    if not (digest == audit.get('candidate_sha256') == audit.get('expected_owner_sha256') == card.get('raster_sha256')):
        raise ValueError('parallel artifact SHA-256 mismatch')
    entries = [x for x in registry['entries'] if x.get('id') == 'registry-160']
    if len(entries) != 1 or entries[0]['sha256'] != audit.get('reference_sha256'):
        raise ValueError('lattice identity mismatch')
    n, near = audit.get('candidate_dots'), audit.get('within_3px')
    if not isinstance(n, int) or n <= 0 or not isinstance(near, int) or not 0 <= near <= n:
        raise ValueError('invalid overlap counts')
    overlap = near/n
    if card.get('dots') != n or audit.get('candidate_overlap') != overlap:
        raise ValueError('inconsistent overlap fraction')
    if (audit.get('duplicate') is not True or overlap <= .70 or
        card.get('all_registry_novelty_verdict') != 'duplicate' or
        card.get('registered_lattice_overlap_3px') != overlap or
        card.get('ok_to_submit') is not False or card.get('download_research') is not False):
        raise ValueError('parallel verdict is not fail-closed')
    mirror = root/'docs/downloads/kanler3-gpc3-exp-2-20261026T215945Z-84217adc42be.run-card.json'
    if json.loads(mirror.read_text()) != card:
        raise ValueError('parallel run-card mirror mismatch')


def main():
    load = lambda p: json.loads((ROOT/p).read_text())
    check(load('evidence/parallel-lattice-audit.json'), load('evidence/run_card.json'),
          load('research/registry-lock.json'))
    print('Parallel lattice audit is consistent; artifact remains a duplicate.')


if __name__ == '__main__':
    main()
