"""Pinned, read-only public GitHub source retrieval over Git transport.

No checkout, new working branch, credential handling, or GitHub API quota needed.
Bare object stores are ignored audit/download caches, never work branches.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_path(value: str) -> str:
    p = Path(value)
    if not value or p.is_absolute() or ".." in p.parts or value.startswith("-") or ":" in value or "\x00" in value or "\\" in value:
        raise ValueError("Expected a safe relative source path")
    return value


class GitHubSource:
    def __init__(self, cache: Path | None = None):
        self.cache = cache or ROOT / "data" / "mirrors"

    @staticmethod
    def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(args, check=True, timeout=180, **kwargs)

    def head(self, repo: str) -> str:
        if not isinstance(repo, str) or not REPO.fullmatch(repo) or repo.split("/")[1] in (".", ".."):
            raise ValueError("Invalid GitHub repository")
        result = self._run(["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        if len(lines) != 1 or not COMMIT.fullmatch(lines[0].split()[0]):
            raise ValueError("Repository HEAD is missing or ambiguous")
        return lines[0].split()[0]

    def repository(self, repo: str, commit: str) -> Path:
        if not isinstance(repo, str) or not REPO.fullmatch(repo) or repo.split("/")[1] in (".", "..") or not isinstance(commit, str) or not COMMIT.fullmatch(commit):
            raise ValueError("Public GitHub repo and immutable 40-character commit required")
        # Separate path components avoid delimiter collisions between owner/name pairs.
        owner, name = repo.split("/")
        bare = self.cache / owner / (name + ".git")
        if not (bare / "HEAD").exists():
            bare.parent.mkdir(parents=True, exist_ok=True)
            self._run(["git", "init", "--bare", "--quiet", str(bare)], capture_output=True)
            self._run(["git", "-C", str(bare), "remote", "add", "origin", f"https://github.com/{repo}.git"], capture_output=True)
            self._run(["git", "-C", str(bare), "config", "remote.origin.promisor", "true"], capture_output=True)
            self._run(["git", "-C", str(bare), "config", "remote.origin.partialclonefilter", "blob:none"], capture_output=True)
        found = subprocess.run(["git", "-C", str(bare), "cat-file", "-e", commit + "^{commit}"], capture_output=True, timeout=30)
        if found.returncode:
            self._run(["git", "-C", str(bare), "fetch", "--quiet", "--filter=blob:none", "--depth=1", "origin", commit], capture_output=True)
        return bare

    def read(self, repo: str, commit: str, path: str) -> bytes:
        bare = self.repository(repo, commit)
        result = self._run(["git", "-C", str(bare), "show", f"{commit}:{source_path(path)}"], capture_output=True)
        return result.stdout

    def paths(self, repo: str, commit: str) -> list[str]:
        bare = self.repository(repo, commit)
        result = self._run(["git", "-C", str(bare), "ls-tree", "-r", "--name-only", "-z", commit], capture_output=True)
        return [p.decode("utf-8") for p in result.stdout.split(b"\0") if p]

    def restore(self, repo: str, commit: str, path: str, dest: Path, expected_sha256: str) -> dict:
        if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise ValueError("Expected SHA-256 is required")
        if not isinstance(repo, str) or not REPO.fullmatch(repo) or repo.split("/")[1] in (".", "..") or not isinstance(commit, str) or not COMMIT.fullmatch(commit):
            raise ValueError("Public GitHub repo and immutable commit required even for cached inputs")
        source_path(path)
        if dest.exists() and sha256_file(dest) == expected_sha256:
            return {"status": "present", "sha256": expected_sha256, "bytes": dest.stat().st_size}
        bare = self.repository(repo, commit)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="." + dest.name + ".", suffix=".partial", dir=dest.parent, delete=False) as out:
            temporary = Path(out.name)
        try:
            with temporary.open("wb") as out:
                self._run(["git", "-C", str(bare), "show", f"{commit}:{source_path(path)}"], stdout=out, stderr=subprocess.PIPE)
            if sha256_file(temporary) != expected_sha256:
                raise ValueError(f"SHA-256 mismatch for {repo}@{commit}:{path}; destination was not replaced")
            temporary.replace(dest)
        finally:
            temporary.unlink(missing_ok=True)
        return {"status": "restored", "sha256": expected_sha256, "bytes": dest.stat().st_size}
