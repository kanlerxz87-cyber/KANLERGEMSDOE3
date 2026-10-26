import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.github_source import GitHubSource, source_path
from scripts.restore_inputs import restore_entry


class FakeSource(GitHubSource):
    def __init__(self, payload=b"verified input"):
        self.payload = payload
        self.calls = 0

    def repository(self, repo, commit):
        self.calls += 1
        return Path("FAKE-BARE-NO-NETWORK")

    def _run(self, args, **kwargs):
        self.calls += 1
        kwargs["stdout"].write(self.payload)
        return subprocess.CompletedProcess(args, 0)


class TransportTests(unittest.TestCase):
    def test_safe_relative_paths(self):
        self.assertEqual(source_path("data/core/a.tif"), "data/core/a.tif")
        for invalid in ("../a", "/tmp/a", "a/../../b", "C:\\a", "a:b", "-a", "", "a\x00b"):
            with self.assertRaises(ValueError, msg=invalid):
                source_path(invalid)

    def test_atomic_hash_verification_and_cache(self):
        source = FakeSource()
        digest = hashlib.sha256(source.payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "input.tif"
            result = source.restore("owner/repo", "a" * 40, "data/input.tif", target, digest)
            self.assertEqual(result["status"], "restored")
            self.assertEqual(target.read_bytes(), source.payload)
            calls = source.calls
            self.assertEqual(source.restore("owner/repo", "a" * 40, "data/input.tif", target, digest)["status"], "present")
            self.assertEqual(source.calls, calls)
            self.assertEqual(list(Path(directory).glob("*.partial")), [])

    def test_failed_hash_does_not_replace_previous_file(self):
        source = FakeSource()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "input.tif"
            target.write_bytes(b"retain previous audit evidence")
            with self.assertRaises(ValueError):
                source.restore("owner/repo", "a" * 40, "input.tif", target, "b" * 64)
            self.assertEqual(target.read_bytes(), b"retain previous audit evidence")
            self.assertEqual([path.name for path in Path(directory).iterdir()], ["input.tif"])

    def test_invalid_identity_is_rejected_before_network(self):
        source = GitHubSource()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "a"
            target.write_bytes(b"already cached")
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            for repo, commit in (("../repo", "a" * 40), ("owner/..", "a" * 40), ("owner/repo", "main"), ("https://example.org/x", "a" * 40)):
                with self.assertRaises(ValueError):
                    source.restore(repo, commit, "a", target, digest)

    def test_parts_assemble_and_verify_before_replace(self):
        source = FakeSource(b"part")
        payload = b"partpart"
        row = {"id": "test", "dest": "core/test.tif", "repo": "owner/repo", "ref": "a" * 40, "parts": ["parts/000", "parts/001"], "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "provenance": "SYNTHETIC TEST ONLY"}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            result = restore_entry(row, target, source)
            self.assertEqual((target / row["dest"]).read_bytes(), payload)
            self.assertEqual(result["status"], "restored")
            calls = source.calls
            self.assertEqual(restore_entry(row, target, source)["status"], "present")
            self.assertEqual(source.calls, calls)
            self.assertFalse(result["organizer_authenticated"])

    def test_unsafe_dest_and_incorrect_size_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            row = {"id": "test", "dest": "../escape", "sha256": "a" * 64}
            with self.assertRaises(ValueError):
                restore_entry(row, Path(directory), FakeSource())


if __name__ == "__main__":
    unittest.main()
