"""Synthetic grid and path guards for the bounded peer audit."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts.audit_current_peer_candidate import audit


def write_tif(path: Path, array, *, transform=None):
    a = np.asarray(array, dtype="float32")
    with rasterio.open(path, "w", driver="GTiff", width=a.shape[1], height=a.shape[0], count=1,
                       dtype="float32", crs="EPSG:32611", transform=transform or from_origin(0, 400, 100, 100)) as dst:
        dst.write(a, 1)


def files(tmp_path):
    template = tmp_path / "template.tif"
    candidate = tmp_path / "candidate.tif"
    peer = tmp_path / "peer.tif"
    x = np.zeros((4, 4), dtype="float32")
    x[1, 1] = 1
    write_tif(template, np.zeros((4, 4)))
    write_tif(candidate, x)
    write_tif(peer, x)
    manifest = tmp_path / "manifest.json"
    entry = {"local_file": peer.name, "sha256": hashlib.sha256(peer.read_bytes()).hexdigest(),
             "repo": "owner/repo", "repo_path": "candidate.tif", "is_calibration_probe": False}
    manifest.write_text(json.dumps([entry]))
    return template, candidate, peer, manifest, entry


def test_candidate_transform_and_binary_support_are_checked(tmp_path):
    template, candidate, _, manifest, _ = files(tmp_path)
    x = np.zeros((4, 4), dtype="float32"); x[1, 1] = 1
    write_tif(candidate, x, transform=from_origin(100, 400, 100, 100))
    with pytest.raises(ValueError, match="grid"):
        audit(candidate, manifest, template)
    x[1, 1] = .5
    write_tif(candidate, x)
    with pytest.raises(ValueError, match="binary"):
        audit(candidate, manifest, template)


def test_peer_transform_paths_and_representation_flag_are_checked(tmp_path):
    template, candidate, peer, manifest, entry = files(tmp_path)
    bad = {**entry, "local_file": "../peer.tif"}
    manifest.write_text(json.dumps([bad]))
    with pytest.raises(ValueError, match="simple filename"):
        audit(candidate, manifest, template)
    bad = {**entry, "is_calibration_probe": "false"}
    manifest.write_text(json.dumps([bad]))
    with pytest.raises(ValueError, match="explicit boolean"):
        audit(candidate, manifest, template)
    x = np.zeros((4, 4), dtype="float32"); x[1, 1] = 1
    write_tif(peer, x, transform=from_origin(100, 400, 100, 100))
    entry["sha256"] = hashlib.sha256(peer.read_bytes()).hexdigest()
    manifest.write_text(json.dumps([entry]))
    with pytest.raises(ValueError, match="peer grid"):
        audit(candidate, manifest, template)
