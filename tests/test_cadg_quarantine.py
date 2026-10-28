"""Publication and receipt regressions; no model training or slot use."""
import copy
import json
from pathlib import Path

import pytest

from scripts.build_cadg_site import build, check_receipt

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    return (json.loads((ROOT / "evidence/cadg-submod-run-card.json").read_text()),
            json.loads((ROOT / "evidence/session-5c1613da-cadg-audit.json").read_text()))


def test_saved_byte_receipt_is_negative_and_accounts_for_reference_mask():
    card, receipt = fixtures()
    check_receipt(card, receipt)
    z = receipt["measurements"]["zeros"]["geometry"]
    n = receipt["measurements"]["nan"]["geometry"]
    assert receipt["equal_prediction_values_inside_mirrored_footprint"]
    assert z["candidate_dots"] == n["candidate_dots"]
    assert z["candidate_dots_within_3px_of_lattice"] == n["candidate_dots_within_3px_of_lattice"]
    assert z["candidate_dot_overlap_fraction"] > .70
    sensitivity = receipt["reference_mask_sensitivity"]
    assert sensitivity["candidate_fraction_near_off_catalogue_reference"] > .70
    assert sensitivity["candidate_dots_near_off_catalogue_reference"] < z["candidate_dots_within_3px_of_lattice"]
    older = receipt["older_9a_pair"]
    assert older["pixels_different_from_f056_pair"] > 0
    assert older["equal_prediction_values_inside_mirrored_footprint"]
    assert all(row["geometry"]["candidate_dot_overlap_fraction"] > .70
               for row in older["measurements"].values())
    assert not receipt["portal_acceptance_verified"]
    assert not receipt["complete_registry_audited_in_this_replay"]


@pytest.mark.parametrize("mutation", [
    lambda c, r: c.update(slot_authorized=True),
    lambda c, r: r.update(ok_to_submit=True),
    lambda c, r: r.update(complete_registry_audited_in_this_replay=True),
    lambda c, r: r["measurements"]["zeros"]["geometry"].update(candidate_dots_within_3px_of_lattice=0),
    lambda c, r: r["measurements"]["zeros"]["validator"].update(portal_acceptance_verified=True),
    lambda c, r: r["measurements"]["nan"]["geometry"].update(sample_mirror_sha256="0" * 64),
    lambda c, r: r["reference_mask_sensitivity"].update(reference_dots_on_catalogue=0),
    lambda c, r: r["older_9a_pair"].update(pixels_different_from_f056_pair=0),
    lambda c, r: r["older_9a_pair"]["measurements"]["nan"]["geometry"].update(lattice_sha256="0" * 64),
    lambda c, r: r["lattice_source"].update(path="wrong.tif"),
])
def test_contradictory_receipts_fail_closed(mutation):
    card, receipt = fixtures()
    card, receipt = copy.deepcopy(card), copy.deepcopy(receipt)
    mutation(card, receipt)
    with pytest.raises((ValueError, KeyError)):
        check_receipt(card, receipt)


def test_quarantine_pages_are_current_and_do_not_claim_approval():
    build(check_only=True)
    for name in ("index.html", "executive-summary.html"):
        text = (ROOT / "docs/cadg-submod" / name).read_text()
        assert "DO NOT SUBMIT" in text
        assert "Research only" in text
        assert "99.94%" in text
        assert "selector signature cannot change" in text
        assert "portal" in text.lower() and "unverified" in text.lower()
        assert "DOWNLOAD READY" not in text
        assert '<a download' not in text.lower()
        assert "Those claims are withdrawn" in text
        assert "eliminating portal validator rejections" not in text
