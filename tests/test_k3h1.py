"""K3-H1 lane: provenance, published-bytes consistency, portal-error diagnosis and algorithm guarantees.

None of these tests needs data/ (gitignored); they run in CI on committed files only.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "vendor", ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

CARD = json.loads((ROOT / "evidence/k3h1-run-card.json").read_text())
TIF = ROOT / "docs/downloads" / CARD["raster_file"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_vendored_shared_tools_are_byte_identical_to_the_pinned_template():
    """Protocol 'reuse, never fork': every pinned gems57 file must match vendor/gems57 byte for byte."""
    pins = json.loads((ROOT / "registry/shared_template_pins.json").read_text())["files"]
    checked = 0
    for name, spec in pins.items():
        if name.startswith("src/gems57/"):
            local = ROOT / "vendor/gems57" / Path(name).name
            assert local.is_file(), name
            assert sha(local) == spec["sha256"], f"{name}: vendored copy differs from the pinned shared template"
            checked += 1
    assert checked >= 11


def test_run_card_matches_published_bytes_and_verdict_is_recomputed():
    from promotion_gate import assess

    assert json.loads((ROOT / "docs/k3h1-run-card.json").read_text()) == CARD
    assert sha(TIF) == CARD["raster_sha256"]
    assert sha(ROOT / "docs/downloads" / CARD["zip_file"]) == CARD["zip_sha256"]
    assert 0 < len(CARD["submission_note"]) <= 140 and CARD["submission_note_chars"] == len(CARD["submission_note"])
    assert CARD["verdict"] == "negative"
    assert assess(CARD)["verdict"] == "negative" and assess(CARD)["slot_authorized"] is False
    assert CARD["download"] == {**CARD["download"], "ok_to_download": True, "ok_to_upload_format": True,
                                "recommended_for_weekly_slot": False}
    h = CARD["holdout"]
    assert h["class"] == "HOLDOUT-DTI" and h["evaluator_version"] and h["withheld_positives"] > 0
    assert h["ci95"][0] <= h["value"] <= h["ci95"][1]
    assert (h["alpha"], h["beta"], h["kernel_m"], h["kernel"], h["aggregation"]) == (0.2, 0.8, 300, "triangular", "pooled")
    assert "NOT a score" in CARD["projection"]["class"]
    assert CARD["final_dot_overlap_3px"] <= 0.70 and CARD["final_max_rank_correlation"] <= 0.90
    assert CARD["leakage_canary"]["max_oriented_auc"] <= 0.90
    assert CARD["slots_used"] == 0


def test_writer_receipt_passed_every_shared_check():
    receipt = json.loads(TIF.with_suffix(".json").read_text())
    assert receipt["sha256"] == CARD["raster_sha256"]
    assert receipt["validator"]["all_checks_passed"] is True and all(receipt["validator"]["checks"].values())
    assert receipt["approved_for_weekly_slot"] is False and receipt["submission_slots_used"] == 0


def test_published_tif_format_from_its_own_bytes():
    rasterio = pytest.importorskip("rasterio")
    with rasterio.open(TIF) as ds:
        a = ds.read(1)
        assert ds.count == 1 and ds.dtypes[0] == "float32" and ds.crs.to_epsg() == 32611
        assert (ds.height, ds.width) == (3730, 3292) and ds.nodata is None
        assert tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(a).all()
    assert set(np.unique(a).tolist()) <= {0.0, 1.0}
    assert int(a.sum()) == 48559


def test_lane_report_numbers_match_the_evidence():
    rep = (ROOT / "research/k3h1-report.md").read_text().replace("\u2212", "-")
    h, p, r = CARD["holdout"], CARD["projection"], CARD["registry"]
    tokens = [CARD["raster_sha256"], CARD["raster_file"], CARD["submission_name"], CARD["submission_note"],
              f"{p['value']:.4f}", f"{p['champion_same_fit']:.4f}", f"{h['value']:.4f}", f"{h['ci95'][0]:.4f}",
              f"{h['ci95'][1]:.4f}", f"{h['incumbent_value']:.4f}", f"{CARD['paired_improvement_delta']:+.4f}",
              f"{CARD['paired_improvement_ci95'][0]:+.4f}", f"{CARD['paired_improvement_ci95'][1]:+.4f}",
              f"{h['withheld_positives']:,}", f"{r['worst_overlap_non_space_filling']['value']:.3f}",
              f"{r['worst_spearman_final_dots']['value']:.3f}", f"{r['worst_spearman_surface_preplacement']['value']:.3f}"]
    missing = [t for t in tokens if t not in rep]
    assert not missing, missing
    fam = json.loads((ROOT / "evidence/focus9_family.json").read_text())
    for row in fam["rows"]:
        line = next(l for l in rep.splitlines() if l.startswith(f"| {row['site']} |"))
        assert f"{row['scored_dots']:,}" in line, row["site"]
        share = 100 * row["share_within_2px_catalogue"]
        assert f"{share:.1f}%" in line or f"{share:.2f}%" in line, row["site"]
        assert f"{row['owner_reported_live_score']:.4f}" in line, row["site"]


def _write(path, a, nodata=None, crs="EPSG:32611"):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin

    prof = dict(driver="GTiff", width=a.shape[1], height=a.shape[0], count=1, dtype="float32", crs=crs,
                transform=from_origin(243350, 4508550, 100, 100))
    if nodata is not None:
        prof["nodata"] = nodata
    with rasterio.open(path, "w", **prof) as ds:
        ds.write(a.astype(np.float32), 1)


@pytest.mark.parametrize("case,expect_ok,cause", [
    ("zeros_outside", True, None),
    ("nan_outside", True, None),
    ("nan_inside", False, "NaN inside"),
    ("sentinel_value", False, "sentinel"),
    ("rounding", False, "rounding"),
    ("negative", False, "negative"),
    ("percent", False, "above 1"),
    ("inf", False, "inf"),
])
def test_portal_check_diagnoses_the_range_error(tmp_path, case, expect_ok, cause):
    from portal_check import official_format

    sample = np.full((12, 12), np.nan, np.float32)
    sample[2:10, 2:10] = 0.0
    fp = np.isfinite(sample)
    _write(tmp_path / "sample.tif", sample)
    a = np.where(fp, 0.0, 0.0).astype(np.float32)
    a[5, 5] = 1.0
    if case == "nan_outside":
        a[~fp] = np.nan
    elif case == "nan_inside":
        a[4, 4] = np.nan
    elif case == "sentinel_value":
        a[~fp] = -9999.0
    elif case == "rounding":
        a[5, 5] = np.float32(1.0000001)
    elif case == "negative":
        a[5, 6] = -0.25
    elif case == "percent":
        a[5, 6] = 37.0
    elif case == "inf":
        a[5, 6] = np.inf
    _write(tmp_path / "cand.tif", a)
    res = official_format(tmp_path / "cand.tif", tmp_path / "sample.tif")
    assert res["ok"] is expect_ok, res
    if cause:
        assert any(cause in c for c in res["likely_range_error_causes"]), res["likely_range_error_causes"]


def test_portal_check_flags_out_of_range_nodata_tag(tmp_path):
    from portal_check import official_format

    sample = np.full((8, 8), np.nan, np.float32)
    sample[2:6, 2:6] = 0.0
    _write(tmp_path / "sample.tif", sample)
    a = np.where(np.isfinite(sample), 0.0, np.nan).astype(np.float32)
    _write(tmp_path / "cand.tif", a, nodata=-9999.0)
    res = official_format(tmp_path / "cand.tif", tmp_path / "sample.tif")
    assert not res["ok"] and any("nodata tag" in c for c in res["likely_range_error_causes"])


def test_binary_spearman_shortcut_equals_scipy():
    from scipy.stats import spearmanr

    rng = np.random.default_rng(3)
    for _ in range(5):
        a = rng.random(5000) < 0.05
        b = rng.random(5000) < 0.2
        assert abs(np.corrcoef(a.astype(float), b.astype(float))[0, 1] - spearmanr(a, b).statistic) < 1e-12


def test_nms_dots_minimum_spacing_and_budget():
    from kgems.asgt import nms_dots

    rng = np.random.default_rng(5)
    score = rng.random((60, 60)).astype(np.float32) + 1e-3
    out = nms_dots(score, np.ones_like(score, bool), 150, 2.8)
    ys, xs = np.nonzero(out)
    assert 0 < ys.size <= 150
    d2 = (ys[:, None] - ys[None, :]) ** 2 + (xs[:, None] - xs[None, :]) ** 2
    np.fill_diagonal(d2, 10 ** 6)
    assert d2.min() > 2.8 ** 2


def test_constrained_greedy_never_exceeds_the_overlap_cap():
    from kgems.allocate import constrained_greedy

    rng = np.random.default_rng(7)
    M = rng.random((6, 4000)) < np.array([0.9, 0.7, 0.5, 0.3, 0.1, 0.0])[:, None]
    acc, counts, limit = constrained_greedy(np.arange(4000), M, 1000, 0.695)
    assert acc.size <= 1000 and limit == int(np.floor(0.695 * 1000))
    assert (M[:, acc].sum(axis=1) <= limit).all()
    assert (M[:, acc].sum(axis=1) == counts).all()


def test_dti_break_even_rule():
    """Adding a dot with credit k raises DTI = T/(0.2T+0.2F+0.8G) iff k > 0.2*DTI (used in the report)."""
    T, F, G = 6456.9, 35101.6, 18004.3
    dti = T / (0.2 * T + 0.2 * F + 0.8 * G)
    for k in (0.2 * dti - 0.01, 0.2 * dti + 0.01):
        new = (T + k) / (0.2 * (T + k) + 0.2 * (F + 1 - k) + 0.8 * G)
        assert (new > dti) == (k > 0.2 * dti)
