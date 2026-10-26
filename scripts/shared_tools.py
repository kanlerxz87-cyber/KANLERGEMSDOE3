"""Load exact, unmodified shared instruments after verifying their source lock.

Never implements a metric, feature transform or submission writer. Numerical
implementations live only in the pinned upstream template under vendor/.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "vendor" / "shared-template"
TOOLS = {"evaluate_holdout", "submission_writer", "prepare_data", "restore_data"}
REQUIRED_PATHS = {f"scripts/{name}.py" for name in TOOLS} | {
    "src/gems32/holdout.py", "src/gems32/metric.py", "src/gems32/submission.py",
    "src/gems32/paths.py", "registry/data_manifest.json", "registry/feature_receipt.json",
}


def verify_template(root: Path = TEMPLATE) -> dict:
    result = {"ok": False, "commit": None, "repository": None, "files_checked": 0, "failures": []}
    try:
        lock = json.loads((root / "PROVENANCE.json").read_text())
        files = lock["files"]
        if not isinstance(files, list) or not files:
            raise ValueError("Nonempty locked file list required")
        paths = [row["path"] for row in files]
        if len(set(paths)) != len(paths) or not REQUIRED_PATHS <= set(paths):
            raise ValueError("Missing/duplicated required shared file entries")
        if lock.get("repository") != "buffedlizard55-lab/GEMSDOE32" or not re.fullmatch(r"[0-9a-f]{40}", lock.get("commit", "")):
            raise ValueError("Invalid immutable shared-template identity")
        result.update(commit=lock["commit"], repository=lock["repository"])
        for row in files:
            path = (root / row["path"]).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                result["failures"].append(row["path"] + ": absent/unsafe")
            else:
                content = path.read_bytes()
                blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
                if hashlib.sha256(content).hexdigest() != row["sha256"] or blob != row.get("git_blob_sha1"):
                    result["failures"].append(row["path"] + ": modified or not the pinned Git tree blob")
            result["files_checked"] += 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["failures"].append("Invalid source lock: " + str(exc))
    result["ok"] = not result["failures"]
    return result


def load_tool(name: str):
    if name not in TOOLS:
        raise ValueError("Only locked shared entry points may be loaded")
    receipt = verify_template()
    if not receipt["ok"]:
        raise ValueError("Shared template source lock failed: " + "; ".join(receipt["failures"]))
    sys.path.insert(0, str(TEMPLATE / "src"))
    # A previously imported package from another template must not win sys.modules.
    for module_name, imported in tuple(sys.modules.items()):
        if module_name == "gems32" or module_name.startswith("gems32."):
            location = getattr(imported, "__file__", None)
            if location and not Path(location).resolve().is_relative_to((TEMPLATE / "src").resolve()):
                raise ValueError("A different gems32 package was already imported; refusing mixed numerical sources")
    path = TEMPLATE / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("_shared_" + name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
