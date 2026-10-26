#!/usr/bin/env python3
"""Publish the isolated SSP1 portal without replacing another lane's files."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'studies/ssp1/docs'
DEST = ROOT/'docs/ssp1'


def publish(check_only=False):
    card = json.loads((ROOT/'studies/ssp1/evidence/run_card.json').read_text())
    if card['verdict'] != 'negative' or card['decision']['ok_to_submit'] is not False:
        raise ValueError('This closed negative-study publisher cannot authorize a new candidate')
    artifact = SOURCE/'downloads'/card['downloads']['tif']
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != card['raster_sha256']:
        raise ValueError('SSP1 artifact changed; refuse publication')
    files = [p for p in SOURCE.rglob('*') if p.is_file()]
    stale = []
    for p in files:
        if p.is_symlink():
            raise ValueError('Do not publish source links to cache or external files')
        dest = DEST/p.relative_to(SOURCE)
        if check_only:
            if not dest.is_file() or dest.read_bytes() != p.read_bytes():
                stale.append(str(dest.relative_to(ROOT)))
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
    if stale:
        raise ValueError('Published SSP1 portal is stale: '+', '.join(stale))
    return len(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(f'SSP1 portal: {publish(args.check)} files checked/published; negative remains negative.')
