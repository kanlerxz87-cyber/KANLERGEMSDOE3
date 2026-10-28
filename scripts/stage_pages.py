#!/usr/bin/env python3
"""Stage tracked public files with legacy-compatible paths; exclude all caches.

Copies current working bytes (including the freshly refreshed public feed), not
Git objects. No source branch is committed or pushed by the publishing workflow.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEST = ROOT/'.cache/pages'


def main():
    # Validate the source bytes before copying anything; never let a stale
    # committed root page be silently replaced or shipped by an isolated lane.
    from scripts.build_site import build as check_root
    from scripts.build_cadg_site import build as check_cadg
    from scripts.build_atsc_site import build as check_atsc
    from scripts.build_cfrp_site import build as check_cfrp
    from scripts.build_cpx_site import build as check_cpx
    check_root(check_only=True)
    check_cadg(check_only=True)
    check_atsc(check_only=True)
    check_cfrp(check_only=True)
    check_cpx(check_only=True)
    tracked = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0')
    files = []
    blocked = {'.git','.cache','.venv','node_modules','__pycache__','.pytest_cache'}
    for name in filter(None, tracked):
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or blocked.intersection(p.parts):
            raise ValueError('Private/cache path must never be in a Pages artifact: '+name)
        if p.name == '.env' or p.name.startswith('.env.') or p.name in ('.npmrc','.pypirc','.netrc','.git-credentials'):
            raise ValueError('Sensitive configuration must not be published: '+name)
        source = ROOT/p
        if source.is_symlink():
            raise ValueError('Tracked symlinks are not published: '+name)
        if source.is_file():
            files.append(p)
    if not (ROOT/'docs/ssp1/index.html').is_file():
        raise ValueError('Build and publish the SSP1 portal first')
    if DEST.exists():
        shutil.rmtree(DEST)
    for p in files:
        out = DEST/p
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/p, out)
    print(f'Staged {len(files)} tracked public files; root redirect and all existing docs paths preserved.')


if __name__ == '__main__':
    main()
