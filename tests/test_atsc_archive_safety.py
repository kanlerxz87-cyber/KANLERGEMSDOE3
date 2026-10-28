"""Synthetic and saved-byte regressions; no training or competition upload."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit_atsc_archive import (
    CANARY_PATH,
    CARD_PATH,
    canary_coverage,
    check_receipt,
    marginal_counterexample,
    paired_evidence_scope,
)
from scripts.promotion_gate import assess

ROOT = Path(__file__).resolve().parents[1]


def receipt():
    return json.loads((ROOT / "evidence/session-cfcca804-atsc-audit.json").read_text())


def test_atsc_saved_receipt_binds_both_twins_and_the_full_lattice():
    observed = receipt()
    check_receipt(observed)
    for kind in ("zeros", "nan"):
        geometry = observed["measurements"][kind]["geometry"]
        assert geometry["candidate_dots"] == 37654
        assert geometry["candidate_dots_within_3px_of_lattice"] == 37652
        assert geometry["candidate_dot_overlap_fraction"] > .70
        assert geometry["duplicate_over_70_percent"] is True
    assert observed["measurements"]["zeros"]["local_profiles"]["finite-grid"]["ok"] is True
    assert observed["measurements"]["zeros"]["local_profiles"]["template-mask"]["ok"] is False
    assert observed["measurements"]["nan"]["local_profiles"]["template-mask"]["ok"] is True
    assert observed["measurements"]["nan"]["local_profiles"]["finite-grid"]["ok"] is False
    assert observed["full_registry_compared"] is False
    assert observed["portal_acceptance_verified"] is False
    assert observed["slot_authorized"] is False


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(slot_authorized=True),
    lambda r: r.update(full_registry_compared=True),
    lambda r: r.update(portal_acceptance_verified=True),
    lambda r: r.update(source_card_sha256="0" * 64),
    lambda r: r["artifacts"]["zeros"].update(sha256="0" * 64),
    lambda r: r["measurements"]["zeros"]["geometry"].update(candidate_dots_within_3px_of_lattice=1),
    lambda r: r["measurements"]["nan"]["geometry"].update(lattice_sha256="0" * 64),
    lambda r: r["measurements"]["zeros"]["local_profiles"]["template-mask"].update(ok=True),
    lambda r: r["measurements"]["nan"].update(zip_sha256="0" * 64),
    lambda r: r["canary_coverage"].update(stage2_corridor_features_in_recorded_inventory=22),
    lambda r: r["paired_evidence_scope"].update(paired_interval_for_named_incumbent_established=True),
    lambda r: r["synthetic_marginal_counterexample"].update(unconditional_iff_claim_disproved=False),
])
def test_contradictory_atsc_receipt_fails_closed(mutation):
    observed = copy.deepcopy(receipt())
    mutation(observed)
    with pytest.raises(ValueError):
        check_receipt(observed)


def test_recorded_canaries_do_not_cover_stage2_and_ci_belongs_to_b0():
    canary = canary_coverage(json.loads(CANARY_PATH.read_text()))
    assert canary["recorded_feature_count"] == 103
    assert canary["stage2_corridor_feature_count"] == 22
    assert canary["stage2_corridor_features_in_recorded_inventory"] == 0
    assert not canary["full_feature_canary_gate_proven"]
    pairing = paired_evidence_scope(json.loads(CARD_PATH.read_text()))
    assert pairing["paired_interval_baseline"] == "B0_regional_d28"
    assert not pairing["paired_interval_for_named_incumbent_established"]
    assert "paired_incumbent_binding" in assess(json.loads(CARD_PATH.read_text()))["failures"]


def test_synthetic_marginal_threshold_is_not_an_iff_rule():
    example = marginal_counterexample()
    assert example["after_metric"] > example["baseline_metric"]
    assert example["incremental_tp"] < example["claimed_unconditional_threshold"]
    alpha, beta = .2, .8
    left = example["incremental_tp"] * (1 - (1 - beta) * example["baseline_metric"])
    right = alpha * example["baseline_metric"] * example["incremental_fp"]
    assert left > right


def test_archived_atsc_and_cadg_cli_cannot_rerun_or_rewrite_evidence():
    for name in ("run_atsc_experiments.py", "run_kanlergems3_experiments.py"):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / name)], capture_output=True, text=True)
        assert result.returncode != 0
        assert "Archived session" in result.stderr


def test_atsc_site_is_fail_closed_and_uses_no_tiff_download_control():
    from scripts.build_atsc_site import build
    build(check_only=True)
    for name in ("index.html", "executive-summary.html", "hypotheses.html"):
        page = (ROOT / "docs/atsc-submod" / name).read_text()
        assert "DO NOT SUBMIT" in page
        assert "99.99%" in page
        assert "22" in page and "canar" in page.lower()
        assert "<a download" not in page.lower()
        assert "Research download" not in page
        assert "CONFIRMED" not in page
        assert "Three Live-Leaderboard Physical Laws" not in page
        assert "excising them gave" not in page
