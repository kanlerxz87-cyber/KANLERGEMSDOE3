import copy
import hashlib
import json
from pathlib import Path

import readiness


def eligible_card(tmp_path):
    tif = tmp_path / "candidate.tif"
    tif.write_bytes(b"test bytes; upstream auditor is mocked in these logical-gate tests")
    h = hashlib.sha256(tif.read_bytes()).hexdigest()
    cache = tmp_path / "feature_stack.npy"
    cache.write_bytes(b"test feature cache")
    cache_sha = hashlib.sha256(cache.read_bytes()).hexdigest()
    fold = "a" * 64
    snap = "b" * 64
    return {
        "lane": {"explicitly_assigned": True, "assigned_method": "test lane"},
        "feature_cache": {"provenance_verified": True, "path": "feature_stack.npy", "sha256": cache_sha},
        "budget": {"experiments": 1, "hours": 0.5},
        "leakage_canaries": {"complete": True, "two_polarities_checked": True,
                             "folds_sha256": fold, "withheld_positives": 100,
                             "expected_features": ["mag", "elev"], "results": {"mag": .66, "elev": .9}},
        "holdout": {"protocol": {"whole_segments_with_buffer": True, "catalogue_features_visible_only": True,
                                  "visible_mask_pixel_exact": True, "pooled_dti": True,
                                  "alpha": .2, "beta": .8, "kernel_radius_m": 300},
                    "candidate": {"evaluator": "test-v1", "withheld_positives": 100, "folds_sha256": fold,
                                  "dti": .2, "ci95": [.18, .22]},
                    "same_evaluator_best": {"evaluator": "test-v1", "withheld_positives": 100, "folds_sha256": fold,
                                            "dti": .1, "ci95": [.08, .12]}, "paired_delta_ci95": [.04, .16]},
        "uniqueness": {"complete": True, "current_snapshot_verified": True, "registry_snapshot_sha256": snap,
                       "raster_count": 3, "missing_or_incompatible": 0,
                       "surface": {"complete": True, "snapshot_sha256": snap, "max_rank_correlation": .9,
                                   "max_within_3px": .7},
                       "final_dots": {"complete": True, "snapshot_sha256": snap, "max_rank_correlation": .3,
                                      "max_within_3px": .7, "raster_sha256": h}},
        "validator": {"sha256": h, "template_sha256": "d" * 64,
                      "receipt_source": "shared-template-reopened-geotiff", "single_band": True,
                      "float32": True, "no_nan_or_inf_inside_footprint": True, "values_in_0_1": True,
                      "crs_shape_transform_match": True, "outside_matches_official_spec": True},
        "submission": {"file": "candidate.tif", "sha256": h, "name": "TEST", "note": "research"},
    }


def review(card, tmp_path):
    # Logic-only fixtures: actual validators, operator and geometric replay have
    # separate integration tests; these callbacks do not authorize a real file.
    return readiness.evaluate(card, tmp_path, shared_validator=lambda root, path, val: True,
                              shared_operator=lambda root, hold: True,
                              uniqueness_validator=lambda root, u, s, v: {"ok": True})


def test_missing_card_is_negative_and_not_approved():
    decision = readiness.evaluate({})
    assert not decision["eligible_for_separate_selector"]
    assert not decision["ok_to_submit"]
    assert "saved_bytes_and_validator" in decision["failed_checks"]


def test_current_run_card_is_negative():
    p = Path(__file__).resolve().parents[1] / "evidence/run-card.json"
    result = readiness.evaluate(json.loads(p.read_text()))
    assert not result["ok_to_submit"] and not result["eligible_for_separate_selector"]
    assert "explicit_method_lane" in result["failed_checks"]


def test_good_evidence_only_reaches_separate_selector(tmp_path):
    card = eligible_card(tmp_path)
    result = review(card, tmp_path)
    assert result["eligible_for_separate_selector"]
    assert not result["ok_to_submit"]
    # The protocol stops on positive correlation above .90, not a negative
    # correlation whose magnitude is above .90.
    card["uniqueness"]["surface"]["max_rank_correlation"] = -.99
    assert review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]


def test_canary_must_cover_all_features_and_catch_both_polarities(tmp_path):
    card = eligible_card(tmp_path)
    card["leakage_canaries"]["results"]["mag"] = .91
    assert not review(card, tmp_path)["checks"]["all_feature_canaries"]
    card["leakage_canaries"]["results"]["mag"] = .02
    assert not review(card, tmp_path)["checks"]["all_feature_canaries"]
    card["leakage_canaries"]["results"].pop("mag")
    assert not review(card, tmp_path)["checks"]["all_feature_canaries"]
    card = eligible_card(tmp_path)
    card["leakage_canaries"]["two_polarities_checked"] = False
    assert not review(card, tmp_path)["checks"]["all_feature_canaries"]
    card = eligible_card(tmp_path)
    card["leakage_canaries"]["folds_sha256"] = "e" * 64
    assert not review(card, tmp_path)["checks"]["all_feature_canaries"]
    card = eligible_card(tmp_path)
    card["leakage_canaries"]["withheld_positives"] = True
    assert not review(card, tmp_path)["checks"]["all_feature_canaries"]


def test_holdout_requires_matched_folds_and_positive_paired_interval(tmp_path):
    card = eligible_card(tmp_path)
    card["holdout"]["paired_delta_ci95"] = [-.01, .2]
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]
    card = eligible_card(tmp_path)
    card["holdout"]["same_evaluator_best"]["folds_sha256"] = "f" * 64
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]
    card = eligible_card(tmp_path)
    card["holdout"]["protocol"]["catalogue_features_visible_only"] = False
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]
    card = eligible_card(tmp_path)
    card["holdout"]["candidate"]["ci95"] = [.01, .02]
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]
    card = eligible_card(tmp_path)
    card["holdout"]["paired_delta_ci95"] = [.2, .3]
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]
    card = eligible_card(tmp_path)
    card["holdout"]["same_evaluator_best"]["withheld_positives"] = True
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]
    card = eligible_card(tmp_path)
    card["holdout"]["candidate"]["ci95"] = [.01, .03]
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]
    card = eligible_card(tmp_path)
    card["holdout"]["paired_delta_ci95"] = [.04, 2.0]
    assert not review(card, tmp_path)["checks"]["comparable_holdout_and_paired_win"]


def test_uniqueness_requires_complete_current_literal_registry(tmp_path):
    card = eligible_card(tmp_path)
    card["uniqueness"]["final_dots"]["max_within_3px"] = .70001
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]
    card = eligible_card(tmp_path)
    card["uniqueness"]["surface"]["max_rank_correlation"] = .90001
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]
    card = eligible_card(tmp_path)
    card["uniqueness"]["surface"]["max_within_3px"] = .70001
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]
    card = eligible_card(tmp_path)
    del card["uniqueness"]["surface"]["max_within_3px"]
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]
    card = eligible_card(tmp_path)
    card["uniqueness"]["surface"]["max_within_3px"] = .70001
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]
    card = eligible_card(tmp_path)
    del card["uniqueness"]["surface"]["max_within_3px"]
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]
    card = eligible_card(tmp_path)
    card["uniqueness"]["missing_or_incompatible"] = 1
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]
    card = eligible_card(tmp_path)
    card["uniqueness"]["current_snapshot_verified"] = False
    assert not review(card, tmp_path)["checks"]["literal_all_registry_uniqueness"]


def test_saved_file_hash_and_validation_cannot_be_skipped(tmp_path):
    card = eligible_card(tmp_path)
    (tmp_path / "candidate.tif").write_bytes(b"modified after receipt")
    assert not review(card, tmp_path)["checks"]["saved_bytes_and_validator"]
    card = eligible_card(tmp_path)
    card["validator"]["outside_matches_official_spec"] = False
    assert not review(card, tmp_path)["checks"]["saved_bytes_and_validator"]
    card = eligible_card(tmp_path)
    assert not readiness.evaluate(card, tmp_path, shared_validator=lambda *args: False)["checks"]["saved_bytes_and_validator"]


def test_budget_note_and_malformed_objects_fail_closed(tmp_path):
    card = eligible_card(tmp_path)
    card["budget"]["experiments"] = 4
    card["submission"]["note"] = "x" * 141
    decision = review(card, tmp_path)
    assert not decision["checks"]["budget"] and not decision["checks"]["submission_name_and_note"]
    for name in ("lane", "holdout", "uniqueness", "validator", "submission"):
        bad = copy.deepcopy(card)
        bad[name] = None
        assert not review(bad, tmp_path)["eligible_for_separate_selector"]


def test_summary_flags_alone_cannot_skip_actual_two_stage_replay(tmp_path):
    card = eligible_card(tmp_path)
    decision = readiness.evaluate(card, tmp_path, shared_validator=lambda *args: True,
                                  shared_operator=lambda *args: True)
    assert not decision["checks"]["literal_all_registry_uniqueness"]
    assert not decision["eligible_for_separate_selector"]
    assert "Missing registry" in decision["uniqueness_replay"]["error"]


def test_broken_operator_and_replay_exceptions_fail_closed(tmp_path):
    card = eligible_card(tmp_path)
    def broken(*args):
        raise ValueError("broken instrument")
    result = readiness.evaluate(card, tmp_path, shared_validator=lambda *args: True,
                                shared_operator=broken, uniqueness_validator=lambda *args: {"ok": True})
    assert not result["checks"]["shared_operator_correct_and_pinned"]
    assert not result["eligible_for_separate_selector"]
    result = readiness.evaluate(card, tmp_path, shared_validator=lambda *args: True,
                                shared_operator=lambda *args: True, uniqueness_validator=broken)
    assert not result["checks"]["literal_all_registry_uniqueness"]
    assert not result["eligible_for_separate_selector"]


def test_name_and_note_reject_unsafe_or_empty_fields(tmp_path):
    for field, bad in (("name", "../candidate"), ("name", "bad\nname"),
                       ("note", " "), ("note", "line one\nline two")):
        card = eligible_card(tmp_path)
        card["submission"][field] = bad
        assert not review(card, tmp_path)["checks"]["submission_name_and_note"]


def test_default_validator_does_not_trust_receipt_flags(tmp_path):
    # The test file is not a GeoTIFF and no authenticated sample is present.
    assert not readiness.evaluate(eligible_card(tmp_path), tmp_path)["checks"]["saved_bytes_and_validator"]


def test_lane_and_feature_cache_must_be_actual_nonempty_and_hash_matched(tmp_path):
    card = eligible_card(tmp_path)
    card['lane']['assigned_method'] = ' '
    assert not review(card, tmp_path)['checks']['explicit_method_lane']
    card = eligible_card(tmp_path)
    (tmp_path / 'feature_stack.npy').write_bytes(b'tampered')
    assert not review(card, tmp_path)['checks']['shared_feature_cache_provenance']
    card = eligible_card(tmp_path)
    card['feature_cache']['path'] = '../outside.npy'
    assert not review(card, tmp_path)['checks']['shared_feature_cache_provenance']
