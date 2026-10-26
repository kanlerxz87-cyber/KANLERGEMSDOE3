import sys

import pytest

import preflight


@pytest.mark.parametrize("blocked,exit_code", [(True, 2), (False, 3)])
def test_one_witness_never_grants_a_clean_exit(monkeypatch, capsys, blocked, exit_code):
    monkeypatch.setattr(preflight, "preflight", lambda: {"stop_required": blocked})
    monkeypatch.setattr(sys, "argv", ["preflight.py"])
    assert preflight.main() == exit_code
    assert '"stop_required"' in capsys.readouterr().out
