"""Restore small pinned audit inputs only; no training or submission generation."""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def fetch(repo, path, ref, dest, sha):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.partial')
    try:
        with tmp.open('wb') as f:
            subprocess.run(['gh','api','-H','Accept: application/vnd.github.raw',
                            f'repos/{repo}/contents/{path}?ref={ref}'], stdout=f, check=True)
        if hashlib.sha256(tmp.read_bytes()).hexdigest() != sha:
            raise ValueError('Hash mismatch: '+str(dest))
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)

if __name__ == '__main__':
    archive = json.loads((ROOT/'sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json').read_text())
    for r in archive['historical_winners']:
        fetch('buffedlizard55-lab/'+r['repo'],r['file'],r['head'],ROOT/'data'/f"{r['repo']}.tif",r['sha256'])
    manifest = json.loads((ROOT/'sources/GEMSDOE32/registry/data_manifest.json').read_text())
    for r in manifest['files']:
        if r['id'] in ('sample_submission','labels'):
            fetch(r['repo'],r['path'],r['ref'],ROOT/'data'/r['dest'],r['sha256'])
