#!/usr/bin/env python3
"""Fetch exact shared template modules into ignored .cache and verify Git blobs.

Try GitHub's contents API first; if its core rate limit is exhausted, fall back
once per immutable repository/ref to codeload. Extract only exact listed regular
files and check size and Git blob before writing. No private template fork is
created and a missing or changed upstream byte is always an error.
"""
import hashlib
import json
import subprocess
import tarfile
import tempfile
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'research/template-lock.json'
DEST = ROOT / '.cache/template'


def git_blob(content: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()


def verified(row, content: bytes) -> bool:
    return len(content) == row['bytes'] and git_blob(content) == row['blob_sha']


def destination(row) -> Path:
    # The lock is reviewed repository data, but do not allow paths to escape.
    rel = Path(row['path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError(f"Unsafe template path: {row['path']}")
    return DEST / row['repo'].split('/')[-1] / rel


def install_archive(repo: str, ref: str, rows: list[dict]) -> None:
    """Recover the requested members only, checking all content before writes."""
    url = f'https://codeload.github.com/{repo}/tar.gz/{ref}'
    wanted = {row['path']: row for row in rows}
    if len(wanted) != len(rows):
        raise ValueError(f'Duplicate template path for {repo}@{ref}')
    found = {}
    with tempfile.TemporaryFile() as archive_file:
        with urllib.request.urlopen(url, timeout=90) as response:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                archive_file.write(chunk)
        archive_file.seek(0)
        with tarfile.open(fileobj=archive_file, mode='r:gz') as archive:
            for member in archive:
                name = member.name.split('/', 1)
                if len(name) != 2 or name[1] not in wanted:
                    continue
                rel = name[1]
                row = wanted[rel]
                if rel in found or not member.isfile() or member.size != row['bytes']:
                    raise ValueError(f'Invalid or duplicate archive member: {rel}')
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f'Unreadable archive member: {rel}')
                with stream:
                    content = stream.read(row['bytes'] + 1)
                if not verified(row, content):
                    raise ValueError(f'Git blob mismatch: {repo}/{rel}')
                found[rel] = content
    if set(found) != set(wanted):
        raise ValueError(f'Missing template members for {repo}@{ref}: {sorted(set(wanted)-set(found))}')
    for rel, content in found.items():
        path = destination(wanted[rel])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        print(f'Verified {path}')


def main():
    lock = json.loads(LOCK.read_text())
    missing = defaultdict(list)
    for row in lock['files']:
        path = destination(row)
        if path.is_file() and verified(row, path.read_bytes()):
            continue
        missing[(row['repo'], row['ref'])].append(row)
    for (repo, ref), rows in missing.items():
        # API requests are efficient for small files. When rate-limited, one
        # archive recovery replaces the remaining group; it never trusts API
        # errors or unexpected blobs as a successful restore.
        for index, row in enumerate(rows):
            try:
                result = subprocess.run(
                    ['gh', 'api', f"repos/{repo}/contents/{row['path']}?ref={ref}",
                     '-H', 'Accept: application/vnd.github.raw'],
                    check=True, capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                install_archive(repo, ref, rows[index:])
                break
            if not verified(row, result.stdout):
                raise ValueError(f"Shared template blob mismatch for {repo}/{row['path']}")
            path = destination(row)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(result.stdout)
            print(f'Verified {path.relative_to(ROOT)}')
    print('Shared template files installed unchanged (cached, not vendored).')


if __name__ == '__main__':
    main()
