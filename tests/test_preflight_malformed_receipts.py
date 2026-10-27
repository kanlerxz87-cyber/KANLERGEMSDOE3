"""Corrupt evidence must produce a negative audit, not bypass other gates."""
import json
import pytest
from scripts import preflight


@pytest.mark.parametrize("receipt", [None, [], {}, {"files": None}, {"files": [None]},
    {"files": [{"id": []}]}, {"files": [{"id": "x", "path": 5}]},
    {"files": [{"id": "x", "path": "x"}, {"id": "x", "path": "x"}]}])
def test_malformed_input_receipt_is_structured_negative(tmp_path, receipt):
    (tmp_path / "data").mkdir()
    (tmp_path / "data/input_receipt.json").write_text(json.dumps(receipt))
    registry = tmp_path / "vendor/shared-template/registry"
    registry.mkdir(parents=True)
    (registry / "data_manifest.json").write_text('{"files": []}')
    result = preflight.assess({}, root=tmp_path)
    assert result["research_ready"] is False
    assert result["submit_ready"] is False
    assert result["input_integrity"] == []
    assert any("malformed or unreadable" in f for f in result["failures"])
    assert any("Missing assigned" in f for f in result["failures"])


def test_invalid_json_audit_does_not_hide_other_failures(tmp_path):
    (tmp_path / "evidence").mkdir()
    (tmp_path / "evidence/shared_tool_audit.json").write_text('{broken')
    result = preflight.assess({}, root=tmp_path)
    assert result["research_ready"] is False
    assert any("operator audit" in f for f in result["failures"])
    assert any("Core data" in f for f in result["failures"])


def test_valid_mirror_inventory_is_not_organizer_authentication(tmp_path):
    import hashlib
    ids = ["training_features", "labels", "sample_submission", "ext_derived_sgmc_faults_100m_u8"]
    (tmp_path / "data").mkdir()
    registry = tmp_path / "vendor/shared-template/registry"
    registry.mkdir(parents=True)
    rows = []
    for key in ids:
        content = key.encode()
        path = "data/" + key
        (tmp_path / path).write_bytes(content)
        rows.append({"id": key, "path": path, "sha256": hashlib.sha256(content).hexdigest()})
    (registry / "data_manifest.json").write_text(json.dumps({"files": rows}))
    (tmp_path / "data/input_receipt.json").write_text(json.dumps({"files": rows}))
    result = preflight.assess({}, root=tmp_path)
    assert all(row["verified"] for row in result["input_integrity"])
    assert result["input_organizer_authenticated"] is False
    assert result["submit_ready"] is False
    # A late malformed row must discard the partial success inventory.
    rows.append({"id": "bad", "path": None})
    (tmp_path / "data/input_receipt.json").write_text(json.dumps({"files": rows}))
    result = preflight.assess({}, root=tmp_path)
    assert result["input_integrity"] == []
    assert not any("blocker removed" in value for value in result["resolved"])
