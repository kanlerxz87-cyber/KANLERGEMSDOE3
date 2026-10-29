"""Regression checks for the 29 Oct 2026 KS3-strain candidate, its receipts and the submission desk.

Tests that need git-ignored caches (.cache/, data/) skip with a reason instead of failing in a
fresh clone. Nothing here authorizes a submission; the submit gate is asserted to stay closed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
CARD = EV / "kanler-s3-verdict-20261029.json"
MAT = EV / "kanler-s3-materialize-20261029.json"
UNIQ = EV / "kanler-s3-uniqueness-20261029.json"
AUDIT = EV / "focus9-audit-20261029.json"
FOCUS = ROOT / ".cache/peers/focus9"


def _json(p: Path):
    return json.loads(p.read_text())


def test_verdict_card_exists_and_keeps_submit_gate_closed():
    card = _json(CARD)
    g = card["gates"]
    assert card["slot_authorized"] is False
    assert card["estimated_leaderboard_score"] == "NOT ESTIMATED"
    # Submit requires every gate, including value (G6) and organizer provenance (G7). G7 is
    # not established for owner mirrors, so submission must stay closed.
    assert g["G7_organizer_provenance"] is False
    assert card["submit_allowed"] is False
    assert card["submit_allowed"] == (
        card["download_allowed"] and g["G6_value_gate_sgmc_cal_ge_H33"] and g["G7_organizer_provenance"]
    )


def test_download_gate_matches_receipts():
    card = _json(CARD)
    uniq = _json(UNIQ)
    inv = _json(EV / "peer-tif-inventory-20261029.json")
    g = card["gates"]
    assert g["G4_unique_vs_inventory_and_inventory_complete"] == (
        uniq["unique_vs_inventory"] and inv["repos_not_complete"] == 0
    )
    assert card["download_allowed"] == all(
        g[k] for k in (
            "G1_format_validator_passed", "G2_range_0_1_full_grid_finite", "G3_grid_crs_shape_transform",
            "G4_unique_vs_inventory_and_inventory_complete", "G5_zero_catalogue_dots",
        )
    )


def test_note_is_at_most_140_characters():
    note = _json(CARD)["note"]
    assert len(note) <= 140
    assert _json(CARD)["note_chars"] == len(note)


def test_published_file_matches_receipt_hash():
    card = _json(CARD)
    path = ROOT / card["file"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card["sha256"]
    assert path.name.startswith("kanlergemsdoe3-")


def test_published_file_format_range_grid_and_no_catalogue_dots():
    rasterio = pytest.importorskip("rasterio")
    np = pytest.importorskip("numpy")
    ref = ROOT / "data/sample_submission.tif"
    labels = ROOT / "data/labels.tif"
    if not ref.exists() or not labels.exists():
        pytest.skip("data/ is git-ignored and not restored in this checkout")
    with rasterio.open(ROOT / _json(CARD)["file"]) as ds:
        arr = ds.read()
        assert arr.shape == (1, 3730, 3292)
        assert ds.dtypes == ("float32",)
        assert str(ds.crs).endswith("32611")
        assert tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None
    a = arr[0]
    assert np.isfinite(a).all()
    assert float(a.min()) >= 0.0 and float(a.max()) <= 1.0
    with rasterio.open(labels) as ds:
        lab = ds.read(1) > 0
    assert int(((a > 0.5) & lab).sum()) == 0
    assert int((a > 0.5).sum()) == 37654


def test_vendored_writer_and_template_lock_verify():
    sys.path.insert(0, str(ROOT / "scripts"))
    import shared_tools

    result = shared_tools.verify_template()
    assert result["ok"] is True
    assert result["files_checked"] == 13


def test_h33_is_gemsdoe30_minus_within_2px_catalogue():
    rasterio = pytest.importorskip("rasterio")
    np = pytest.importorskip("numpy")
    ndi = pytest.importorskip("scipy.ndimage")
    import glob

    h33 = glob.glob(str(FOCUS / "GEMSDOE32__*.tif"))
    g30 = glob.glob(str(FOCUS / "GEMSDOE30__*.tif"))
    labels = ROOT / "data/labels.tif"
    if not (h33 and g30 and labels.exists()):
        pytest.skip("focus-9 cache or data/ not restored")
    foot = np.isfinite(rasterio.open(ROOT / "data/sample_submission.tif").read(1))
    lab = rasterio.open(labels).read(1) > 0
    dist = ndi.distance_transform_edt(~lab)

    def dots(p):
        return (np.nan_to_num(rasterio.open(p).read(1), nan=0.0) > 0.5) & foot

    a30, a32 = dots(g30[0]), dots(h33[0])
    assert int(a30.sum()) == 44090 and int(a32.sum()) == 37654
    assert np.array_equal(a32, a30 & ~(dist <= 2))
    assert int((a30 & (dist <= 2)).sum()) == 6436


def test_uniqueness_receipt_is_v2_with_controls():
    uniq = _json(UNIQ)
    assert uniq["rule_version"].startswith("v2")
    c = uniq["controls"]
    assert c["positive_control_candidate_shifted_1px"]["duplicate_flag"] is True
    assert c["positive_control_H33_B2_vs_GEMSDOE30_known_subset"]["duplicate_flag"] is True
    assert c["negative_control_random_dots"]["duplicate_flag"] is False
    assert uniq["files_compared"] + uniq["files_not_submission_like"] + uniq["files_not_comparable"] \
        + uniq["files_unreadable"] == uniq["files_inventoried"]


def test_run_card_is_unchanged_from_session_base():
    # Pinned digest of evidence/run-card.json at base 295efea (git show 295efea:evidence/run-card.json).
    # Not a git-history lookup: CI uses a shallow checkout that lacks the base commit.
    base_sha256 = "2fb875f77e96b97369a8af160722d8f0d8b35ebe9e2a054f228a24d9c1aae330"
    assert hashlib.sha256((EV / "run-card.json").read_bytes()).hexdigest() == base_sha256


def test_focus9_champions_pinned_hashes_match_cache():
    reg = _json(ROOT / "registry/focus9_champions.json")["entries"]
    missing = [e["name"] for e in reg if not list(FOCUS.glob(f"{e['site']}__*.tif"))]
    if len(missing) == len(reg):
        pytest.skip("focus-9 cache not restored")
    for e in reg:
        hits = list(FOCUS.glob(f"{e['site']}__*.tif"))
        if not hits:
            continue
        assert hashlib.sha256(hits[0].read_bytes()).hexdigest() == e["sha256"], e["site"]


def test_desk_page_is_current_and_site_builder_exists():
    import subprocess as sp

    r = sp.run([sys.executable, str(ROOT / "scripts/build_submission_desk.py"), "--check"],
               cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_blocked_candidate_is_quarantined_and_not_linked():
    card = _json(CARD)
    name = Path(card["file"]).name
    if not card["download_allowed"]:
        assert card["file"].startswith("docs/submission/quarantine/"), card["file"]
        desk = (ROOT / "docs/submission/index.html").read_text()
        assert f'href="./{name}"' not in desk and f'href="quarantine/{name}"' not in desk
        assert card["verdict"].startswith("DO NOT DOWNLOAD")
    else:
        assert card["verdict"] != "DO NOT DOWNLOAD OR SUBMIT"


def test_uniqueness_flags_are_reported_with_direction():
    uniq = _json(UNIQ)
    for f in uniq["duplicate_flags"]:
        assert f["trigger"] in ("candidate_side", "peer_side", "candidate_sidepeer_side")
        assert f["f_c"] > 0.70 or f["f_p"] > 0.70
