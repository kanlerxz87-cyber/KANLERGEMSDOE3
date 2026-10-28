"""Concurrent CPX archive is a saved-byte duplicate, not a slot recommendation."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.audit_cpx_archive import check_receipt

ROOT = Path(__file__).resolve().parents[1]


def receipt():
    return json.loads((ROOT / "evidence/session-cfcca804-cpx-audit.json").read_text())


def test_cpx_forensic_receipt_is_a_negative_literal_stop():
    report = receipt()
    check_receipt(report)
    assert report["geometry"]["candidate_dots"] == 37654
    assert report["geometry"]["candidate_dots_within_3px_of_lattice"] == 37648
    assert report["geometry"]["candidate_dot_overlap_fraction"] > .70
    assert report["local_profiles"]["finite-grid"]["ok"] is True
    assert report["local_profiles"]["template-mask"]["ok"] is False
    assert report["portal_acceptance_verified"] is False and report["slot_authorized"] is False


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(ok_to_submit=True),
    lambda r: r.update(full_registry_compared=True),
    lambda r: r.update(candidate_sha256="0" * 64),
    lambda r: r["geometry"].update(candidate_dots_within_3px_of_lattice=1),
    lambda r: r["geometry"].update(lattice_sha256="0" * 64),
    lambda r: r["local_profiles"]["template-mask"].update(ok=True),
])
def test_cpx_receipt_mutations_fail_closed(mutation):
    report = copy.deepcopy(receipt())
    mutation(report)
    with pytest.raises(ValueError):
        check_receipt(report)


def test_cpx_check_mode_does_not_repair_a_stale_page():
    from scripts.build_cpx_site import build
    target = ROOT / "docs/cpx-edti/index.html"
    original = target.read_text()
    try:
        target.write_text("stale sentinel")
        with pytest.raises(ValueError, match="Stale CPX"):
            build(check_only=True)
        assert target.read_text() == "stale sentinel"
    finally:
        target.write_text(original)


def test_cpx_pages_and_frozen_clis_are_quarantined():
    from scripts.build_cpx_site import build
    build(check_only=True)
    for name in ("index.html", "executive-summary.html", "submission-guide.html", "hypotheses.html"):
        text = (ROOT / "docs/cpx-edti" / name).read_text()
        assert "DO NOT SUBMIT" in text and "cannot waive" in text
        assert "<a download" not in text.lower()
        assert "NEAREST TO READY" not in text and "portal-safe" not in text
    for name in ("run_cpx_experiments.py", "build_cpx_run_card.py", "cpx_forensics.py"):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / name)], capture_output=True, text=True)
        assert run.returncode != 0 and "Archived session" in run.stderr
