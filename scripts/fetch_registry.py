#!/usr/bin/env python3
"""Download the 9 focus-site champion rasters (comparison only) and verify SHA-256."""
from __future__ import annotations
import hashlib, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".cache" / "registry"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def main() -> int:
    reg = json.loads((ROOT / "registry" / "focus9_champions.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for e in reg["entries"]:
        dest = OUT / f"{e['site']}__{Path(e['path']).name}"
        if dest.exists() and sha256_file(dest) == e["sha256"]:
            print(f"present {e['site']} {dest.name}"); continue
        print(f"fetching {e['site']} {e['path']}...", flush=True)
        with dest.open("wb") as out:
            subprocess.run(["gh", "api", f"repos/{e['repo']}/contents/{e['path']}",
                            "-H", "Accept: application/vnd.github.raw"], stdout=out, check=True)
        got = sha256_file(dest)
        if got != e["sha256"]:
            dest.unlink(); raise SystemExit(f"HASH MISMATCH {e['site']}: {got} != {e['sha256']}")
        print(f"verified {e['site']} sha256={got[:16]}...")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
