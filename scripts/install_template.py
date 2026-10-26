#!/usr/bin/env python3
"""Fetch exact, unmodified shared template modules into ignored .cache; verify Git blobs."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "research/template-lock.json"
DEST = ROOT / ".cache/template"


def git_blob(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def main():
    lock = json.loads(LOCK.read_text())
    for row in lock["files"]:
        path = DEST / row["repo"].split("/")[-1] / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file() and git_blob(path.read_bytes()) == row["blob_sha"]:
            continue
        result = subprocess.run(["gh", "api", f"repos/{row['repo']}/contents/{row['path']}?ref={row['ref']}", "-H", "Accept: application/vnd.github.raw"], check=True, capture_output=True)
        content = result.stdout
        if len(content) != row["bytes"] or git_blob(content) != row["blob_sha"]:
            raise ValueError(f"Shared template blob mismatch for {row['repo']}/{row['path']}")
        path.write_bytes(content)
        print(f"Verified {path.relative_to(ROOT)}")
    print("Shared template files installed unchanged (cached, not vendored).")

if __name__ == "__main__":
    main()
