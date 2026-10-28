"""Concurrent CFRP archive is a saved-byte duplicate, never an upload permission."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.audit_cfrp_archive import check_receipt

ROOT = Path(__file__).resolve().parents[1]


def receipt():
    return json.loads((ROOT / "evidence/session-cfcca804-cfrp-audit.json").read_text())


def test_cfrp_forensic_receipt_is_a_negative_literal_stop():
    report = receipt()
    check_receipt(report)
    geometry = report["geometry"]
    assert geometry["candidate_dots"] == geometry["candidate_dots_within_3px_of_lattice"] == 44090
    assert geometry["candidate_dot_overlap_fraction"] == 1.0
    assert report["local_profiles"]["finite-grid"]["ok"] is True
    assert report["local_profiles"]["template-mask"]["ok"] is False
    assert report["portal_acceptance_verified"] is False and report["slot_authorized"] is False


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(ok_to_submit=True),
    lambda r: r.update(full_registry_compared=True),
    lambda r: r.update(portal_acceptance_verified=True),
    lambda r: r.update(candidate_sha256="0" * 64),
    lambda r: r["geometry"].update(candidate_dots_within_3px_of_lattice=1),
    lambda r: r["geometry"].update(lattice_sha256="0" * 64),
    lambda r: r["local_profiles"]["template-mask"].update(ok=True),
])
def test_cfrp_receipt_mutations_fail_closed(mutation):
    report = copy.deepcopy(receipt())
    mutation(report)
    with pytest.raises(ValueError):
        check_receipt(report)


def test_cfrp_check_mode_does_not_repair_a_stale_page():
    from scripts.build_cfrp_site import build
    target = ROOT / "docs/cfrp-20261028/index.html"
    original = target.read_text()
    try:
        target.write_text("stale sentinel")
        with pytest.raises(ValueError, match="Stale CFRP"):
            build(check_only=True)
        assert target.read_text() == "stale sentinel"
    finally:
        target.write_text(original)


def test_cfrp_pages_and_frozen_clis_are_quarantined():
    from scripts.build_cfrp_site import build
    build(check_only=True)
    text = (ROOT / "docs/cfrp-20261028/index.html").read_text()
    assert "DO NOT SUBMIT" in text and "cannot waive" in text
    assert "<a download" not in text.lower()
    assert "paste into DrivenData" not in text and "cannot trigger" not in text
    for name in ("run_cfrp_experiments.py", "audit_cfrp_final.py"):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / name)], capture_output=True, text=True)
        assert run.returncode != 0 and "Archived session" in run.stderr
