"""Synthetic saved-raster tests; these are not geological experiments or scores."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from scripts.check_uniqueness import audit_registry
from scripts.readiness import replay_uniqueness

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raster(path, values):
    with rasterio.open(path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1],
                       count=1, dtype="float32", crs="EPSG:32611",
                       transform=from_origin(243350, 4508550, 100, 100)) as dst:
        dst.write(values.astype("float32"), 1)


def fixture(tmp_path):
    shape = (80, 80)
    surface = np.random.default_rng(4).random(shape).astype("float32")
    preview = np.zeros(shape, dtype="float32"); preview[70, 70] = 1
    reference = np.zeros(shape, dtype="float32"); reference[5, 5] = 1
    for name, value in (("template", np.zeros(shape)), ("surface", surface),
                        ("preview", preview), ("candidate", preview), ("reference", reference)):
        raster(tmp_path / (name + ".tif"), value)
    manifest = {"complete": True, "expected_count": 1,
                "rasters": [{"id": "ref", "path": "reference.tif", "sha256": digest(tmp_path / "reference.tif")}]}
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(manifest))
    pre = audit_registry(tmp_path / "surface.tif", tmp_path / "preview.tif", tmp_path / "template.tif", path, "surface-before-writer")
    final = audit_registry(tmp_path / "candidate.tif", tmp_path / "candidate.tif", tmp_path / "template.tif", path, "final-dots")
    assert pre["unique_under_protocol"] and final["unique_under_protocol"]
    for name, report in (("pre.json", pre), ("final.json", final)):
        (tmp_path / name).write_text(json.dumps(report))
    def stage(report, filename):
        return {"receipt_path": filename, "receipt_sha256": digest(tmp_path / filename),
                "max_rank_correlation": max(r["rank_correlation"] for r in report["comparisons"]),
                "max_within_3px": max(r["directed_dot_overlap_3px"] for r in report["comparisons"])}
    u = {"registry_manifest_path": "registry.json", "registry_snapshot_sha256": digest(path), "raster_count": 1,
         "surface": {**stage(pre, "pre.json"), "surface_file": "surface.tif", "preview_dots_file": "preview.tif"},
         "final_dots": stage(final, "final.json")}
    submission = {"file": "candidate.tif", "sha256": digest(tmp_path / "candidate.tif")}
    validator = {"template_path": "template.tif", "template_sha256": digest(tmp_path / "template.tif")}
    return u, submission, validator


def test_two_stage_replay_reopens_exact_files_and_receipts(tmp_path):
    u, submission, validator = fixture(tmp_path)
    result = replay_uniqueness(tmp_path, u, submission, validator)
    assert result["ok"] is True
    assert result["surface"]["stage"] == "surface-before-writer"
    assert result["final_dots"]["stage"] == "final-dots"
    assert result["final_dots"]["surface_sha256"] == submission["sha256"]
    assert result["final_dots"]["dots_sha256"] == submission["sha256"]


def test_final_stage_cannot_report_original_soft_surface_instead_of_final_dots(tmp_path):
    fixture(tmp_path)
    import pytest
    with pytest.raises(ValueError, match="exact final dot raster"):
        audit_registry(tmp_path / "surface.tif", tmp_path / "candidate.tif", tmp_path / "template.tif",
                       tmp_path / "registry.json", "final-dots")


def test_replay_rejects_changed_candidate_registry_and_summaries(tmp_path):
    u, submission, validator = fixture(tmp_path)
    (tmp_path / "candidate.tif").write_bytes(b"changed")
    assert not replay_uniqueness(tmp_path, u, submission, validator)["ok"]
    u, submission, validator = fixture(tmp_path)
    (tmp_path / "reference.tif").write_bytes(b"changed")
    assert not replay_uniqueness(tmp_path, u, submission, validator)["ok"]
    u, submission, validator = fixture(tmp_path)
    u["surface"]["max_within_3px"] = .7
    assert not replay_uniqueness(tmp_path, u, submission, validator)["ok"]


def test_external_mask_sidecars_cannot_change_footprint_or_reference(tmp_path):
    import pytest
    fixture(tmp_path)
    for name in ("template.tif", "reference.tif"):
        path = tmp_path / name
        original = digest(path)
        mask = np.full((80, 80), 255, dtype="uint8"); mask[1, 1] = 0
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
            with rasterio.open(path, "r+") as dst:
                dst.write_mask(mask)
        assert digest(path) == original
        with pytest.raises(ValueError, match="unhashed sidecar"):
            audit_registry(tmp_path / "surface.tif", tmp_path / "preview.tif", tmp_path / "template.tif",
                           tmp_path / "registry.json", "surface-before-writer")
        Path(str(path) + ".msk").unlink()


def test_replay_rejects_forged_receipt_even_when_rehashed(tmp_path):
    u, submission, validator = fixture(tmp_path)
    path = tmp_path / "pre.json"
    report = json.loads(path.read_text())
    report["comparisons"][0]["directed_dot_overlap_3px"] = .7
    path.write_text(json.dumps(report))
    u["surface"]["receipt_sha256"] = digest(path)
    assert not replay_uniqueness(tmp_path, u, submission, validator)["ok"]


def cli(tmp_path, *, registry="registry.json", surface="surface.tif", out="out.json"):
    return subprocess.run([sys.executable, str(ROOT / "scripts/check_uniqueness.py"),
                           "--surface", str(tmp_path / surface), "--dots", str(tmp_path / "preview.tif"),
                           "--template", str(tmp_path / "template.tif"), "--registry", str(tmp_path / registry),
                           "--stage", "surface-before-writer", "--out", str(tmp_path / out)],
                          text=True, capture_output=True)


def test_cli_replaces_stale_pass_if_input_or_manifest_is_bad(tmp_path):
    fixture(tmp_path)
    out = tmp_path / "out.json"
    out.write_text('{"status":"PASS_SCOPED_REGISTRY","unique_under_protocol":true}')
    run = cli(tmp_path, surface="missing.tif")
    assert run.returncode == 2
    failed = json.loads(out.read_text())
    assert failed["status"] == "BLOCKED_ERROR" and failed["unique_under_protocol"] is False
    out.write_text('{"status":"PASS_SCOPED_REGISTRY","unique_under_protocol":true}')
    (tmp_path / "bad.json").write_text("not json")
    run = cli(tmp_path, registry="bad.json")
    assert run.returncode == 2 and json.loads(out.read_text())["unique_under_protocol"] is False


def test_cli_stops_on_first_duplicate_before_an_unavailable_next_reference(tmp_path):
    fixture(tmp_path)
    ref = tmp_path / "reference.tif"
    # Preview equals the first reference: immediate 100% directional overlap.
    with rasterio.open(ref) as src:
        reference = src.read(1)
    raster(tmp_path / "preview.tif", reference)
    registry = json.loads((tmp_path / "registry.json").read_text())
    registry["expected_count"] = 2
    registry["rasters"].append({"id": "missing", "path": "missing.tif", "sha256": "a" * 64})
    (tmp_path / "registry.json").write_text(json.dumps(registry))
    run = cli(tmp_path)
    assert run.returncode == 1
    report = json.loads((tmp_path / "out.json").read_text())
    assert report["status"] == "STOP_DUPLICATE"
    assert report["registry_entries_compared"] == 1 and report["registry_entries_declared"] == 2
    assert report["comparisons"][0]["directed_dot_overlap_3px"] == 1
    assert report["unique_under_protocol"] is False


def test_output_alias_never_overwrites_registry_or_member(tmp_path):
    fixture(tmp_path)
    manifest = tmp_path / "registry.json"
    before = manifest.read_bytes()
    assert cli(tmp_path, out="registry.json").returncode == 2
    assert manifest.read_bytes() == before
    ref = tmp_path / "reference.tif"
    old_ref = ref.read_bytes()
    (tmp_path / "alias.json").symlink_to(ref)
    assert cli(tmp_path, out="alias.json").returncode == 2
    assert ref.read_bytes() == old_ref
