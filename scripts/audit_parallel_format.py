#!/usr/bin/env python3
"""Inspect the existing parallel TIFF with the strict footprint-aware validator.

This is not a portal acceptance test and does not create or alter a submission.
"""
import json
from pathlib import Path
from audit_parallel_lattice import ROOT, CANDIDATE, CANDIDATE_SHA, sha256
from validate_submission import validate


def main():
    entries = {x['id']: x for x in json.loads((ROOT/'data/input-manifest.json').read_text())['inputs']}
    sample = ROOT/'data'/entries['sample_submission']['dest']
    candidate = ROOT/CANDIDATE
    if sha256(sample) != entries['sample_submission']['sha256'] or sha256(candidate) != CANDIDATE_SHA:
        raise ValueError('Pinned sample or parallel artifact hash mismatch')
    result = validate(sample, candidate)
    result['template'] = str(sample.relative_to(ROOT))
    result['candidate'] = CANDIDATE
    result['candidate_sha256'] = CANDIDATE_SHA
    result['template_sha256'] = entries['sample_submission']['sha256']
    result['interpretation'] = 'Strict local null-outside policy only; not a portal receipt or proof of a prior rejection cause.'
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    (ROOT/'evidence/parallel-format-audit.json').write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
