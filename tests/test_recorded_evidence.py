"""Integration checks for the pinned public-mirror bytes, when restored."""
import json
from pathlib import Path
import pytest
import preflight
import audit_focus
import analyze_anchor_lineage as lineage

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/'.cache'


def available():
    return ((CACHE/'data/anchors/GEMSDOE36.tif').exists() and
            (CACHE/'data/registry_dense.tif').exists() and
            (CACHE/'template/src/gems57/uniqueness.py').exists())


@pytest.mark.skipif(not available(), reason='Run restore_workspace.py --fetch --anchors to verify real inputs')
@pytest.mark.parametrize('module,recorded', [
    (preflight,'preflight.json'),
    (audit_focus,'focus_anchor_audit.json'),
    (lineage,'anchor_lineage.json'),
])
def test_real_restored_inputs_reproduce_recorded_measurement(module, recorded):
    actual=module.run(CACHE)
    expected=json.loads((ROOT/'evidence'/recorded).read_text())
    actual.pop('created_utc'); expected.pop('created_utc')
    assert actual == expected
