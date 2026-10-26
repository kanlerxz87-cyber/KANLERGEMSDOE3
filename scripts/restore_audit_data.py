"""Restore pinned historical audit inputs only, never a candidate submission."""
import hashlib
import json
import subprocess
from pathlib import Path

from restore_shared_template import download_archive

ROOT = Path(__file__).resolve().parents[1]


def fetch(repo, path, ref, dest, sha):
    """Use gh when available; fall back to a hash-checked pinned codeload archive."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest() == sha:
        return
    tmp = dest.with_suffix(dest.suffix + '.partial')
    try:
        try:
            with tmp.open('wb') as out:
                result = subprocess.run(
                    ['gh', 'api', '-H', 'Accept: application/vnd.github.raw',
                     f'repos/{repo}/contents/{path}?ref={ref}'],
                    stdout=out, stderr=subprocess.PIPE, timeout=180, check=False)
            if result.returncode == 0 and hashlib.sha256(tmp.read_bytes()).hexdigest() == sha:
                tmp.replace(dest)
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        # REST may be rate-limited. Codeload still uses the immutable commit,
        # checks the expected digest, and never extracts arbitrary archive paths.
        tmp.unlink(missing_ok=True)
        download_archive(repo, ref, {path: {'destination': dest, 'sha256': sha}})
    finally:
        tmp.unlink(missing_ok=True)


def main():
    archive = json.loads((ROOT/'sources/GEMSDOE32/evidence/focus_site_winner_overlap_20261026.json').read_text())
    for r in archive['historical_winners']:
        fetch('buffedlizard55-lab/'+r['repo'], r['file'], r['head'], ROOT/'data'/f"{r['repo']}.tif", r['sha256'])
    manifest = json.loads((ROOT/'sources/GEMSDOE32/registry/data_manifest.json').read_text())
    for r in manifest['files']:
        if r['id'] in ('sample_submission', 'labels'):
            fetch(r['repo'], r['path'], r['ref'], ROOT/'data'/r['dest'], r['sha256'])
    print('Pinned audit inputs recovered; participant mirrors are not organizer-authenticated.')


if __name__ == '__main__':
    main()
