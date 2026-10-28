"""Instrument binding checks; no organizer account or model experiment is used."""
import hashlib
import json
from pathlib import Path

from scripts import readiness
from scripts import shared_tools

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_reopened_validator_uses_active_lock_and_independent_mask_check(tmp_path, monkeypatch):
    sample, labels, candidate = (tmp_path / name for name in ("sample.tif", "labels.tif", "candidate.tif"))
    for path in (sample, labels, candidate):
        path.write_bytes(path.name.encode())
    manifest = "a" * 64
    lock = {"ok": True, "manifest_sha256": manifest}
    observed = []
    monkeypatch.setattr(shared_tools, "verify_template", lambda path: lock)
    def run(argv, **kwargs):
        observed.append(argv)
        if argv[1].endswith("reopen_with_template.py"):
            assert argv[argv.index("--mode") + 1] == "zeros"
            return json.dumps({"all_checks_passed": True, "mode": "zeros", "sha256": sha(candidate)})
        assert argv[1].endswith("validate_submission.py")
        assert argv[argv.index("--profile") + 1] == "masked-finite"
        return json.dumps({"ok": True, "encoding_profile": "masked-finite", "sha256": sha(candidate), "template_sha256": sha(sample)})
    monkeypatch.setattr(readiness.subprocess, "check_output", run)
    val = {"template_path": "sample.tif", "labels_path": "labels.tif",
           "template_sha256": sha(sample), "labels_sha256": sha(labels),
           "organizer_template_authenticated": True, "authenticated_template_sha256": sha(sample),
           "shared_template_manifest_sha256": manifest}
    assert readiness.validate_with_shared(tmp_path, candidate, val)
    assert len(observed) == 2
    assert observed[0][observed[0].index("--template-root") + 1] == str(tmp_path / "vendor/shared-template")
    assert all("bootstrap_template.sh" not in " ".join(cmd) for cmd in observed)
    val["shared_template_manifest_sha256"] = "b" * 64
    assert not readiness.validate_with_shared(tmp_path, candidate, val)


def test_reopened_gate_requires_both_shared_raw_zeros_and_internal_null_mask(tmp_path, monkeypatch):
    """Real synthetic TIFFs; only shared dimension constants are reduced for the fixture."""
    import contextlib
    import io
    import subprocess
    import sys

    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    from scripts import reopen_with_template
    from scripts.validate_submission import validate

    writer = shared_tools.load_tool("submission_writer")
    instrument = writer.submission
    for name, value in (("EXPECTED_HEIGHT", 5), ("EXPECTED_WIDTH", 5),
                        ("EXPECTED_TOTAL_PIXELS", 25), ("EXPECTED_FOOTPRINT_PIXELS", 24)):
        monkeypatch.setattr(instrument, name, value)
    monkeypatch.setattr(shared_tools, "verify_template", lambda path: {"ok": True, "manifest_sha256": "a" * 64})
    profile = dict(driver="GTiff", height=5, width=5, count=1, dtype="float32", crs="EPSG:32611",
                   transform=from_origin(243350, 4508550, 100, 100))
    sample, labels, candidate = (tmp_path / name for name in ("sample.tif", "labels.tif", "candidate.tif"))
    template_values = np.zeros((5, 5), dtype="float32"); template_values[0, 0] = np.nan
    with rasterio.open(sample, "w", **profile, nodata=np.nan) as dst:
        dst.write(template_values, 1)
    label_array = np.zeros((5, 5), dtype="float32"); label_array[1, 1] = 1
    with rasterio.open(labels, "w", **profile) as dst:
        dst.write(label_array, 1)
    def write_candidate(outside, masked):
        values = np.zeros((5, 5), dtype="float32"); values[2, 2] = 1; values[0, 0] = outside
        mask = np.full((5, 5), 255, dtype="uint8")
        if masked:
            mask[0, 0] = 0
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(candidate, "w", **profile) as dst:
                dst.write(values, 1)
                dst.write_mask(mask)
    def run(argv, **kwargs):
        if argv[1].endswith("reopen_with_template.py"):
            output = io.StringIO()
            with monkeypatch.context() as context, contextlib.redirect_stdout(output):
                context.setattr(sys, "argv", argv[1:])
                reopen_with_template.main()
            return output.getvalue()
        report = validate(sample, candidate, argv[argv.index("--profile") + 1])
        if not report["ok"]:
            raise subprocess.CalledProcessError(1, argv)
        return json.dumps(report)
    monkeypatch.setattr(readiness.subprocess, "check_output", run)
    val = {"template_path": sample.name, "labels_path": labels.name,
           "template_sha256": sha(sample), "labels_sha256": sha(labels),
           "organizer_template_authenticated": True, "authenticated_template_sha256": sha(sample),
           "shared_template_manifest_sha256": "a" * 64}
    write_candidate(0, True)
    assert readiness.validate_with_shared(tmp_path, candidate, val)
    label_hash = sha(labels)
    label_mask = np.full((5, 5), 255, dtype="uint8"); label_mask[1, 1] = 0
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(labels, "r+") as dst:
            dst.write_mask(label_mask)
    assert sha(labels) == label_hash  # the untracked sidecar can hide a labelled pixel
    assert not readiness.validate_with_shared(tmp_path, candidate, val)
    Path(str(labels) + ".msk").unlink()
    with rasterio.open(labels, "w", **profile, nodata=0) as dst:
        dst.write(np.zeros((5, 5), dtype="float32"), 1)
    val["labels_sha256"] = sha(labels)
    assert not readiness.validate_with_shared(tmp_path, candidate, val)  # masked inside footprint
    with rasterio.open(labels, "w", **{**profile, "count": 2}) as dst:
        dst.write(np.zeros((2, 5, 5), dtype="float32"))
    val["labels_sha256"] = sha(labels)
    assert not readiness.validate_with_shared(tmp_path, candidate, val)  # unexpected band
    with rasterio.open(labels, "w", **profile) as dst:
        dst.write(np.zeros((5, 5), dtype="float32"), 1)
    val["labels_sha256"] = sha(labels)
    write_candidate(-9999, True)  # raw sentinel hidden by the mask: shared zeros must fail
    assert not readiness.validate_with_shared(tmp_path, candidate, val)
    write_candidate(0, False)  # raw zeros pass the shared audit, but are not null outside
    assert not readiness.validate_with_shared(tmp_path, candidate, val)


def test_shared_operator_reproduces_known_pinned_failure():
    lock = shared_tools.verify_template(ROOT / "vendor/shared-template")
    assert lock["ok"]
    hold = {"candidate": {"evaluator": "GEMSDOE32-HIDE-RECOVER-v3.0", "template_manifest_sha256": lock["manifest_sha256"]},
            "same_evaluator_best": {"evaluator": "GEMSDOE32-HIDE-RECOVER-v3.0", "template_manifest_sha256": lock["manifest_sha256"]}}
    # The source-pinned v3 operator fails a synthetic conservation probe; this
    # is not a real holdout result and says nothing about historic submissions.
    assert readiness.validate_shared_operator(ROOT, hold) is False
