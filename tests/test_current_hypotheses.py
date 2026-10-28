from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ranked_hypotheses_are_planning_only_and_expose_layers_mimics_and_sources():
    rows = json.loads((ROOT / "research/hypotheses.json").read_text())
    assert [row["rank"] for row in rows] == [1, 2, 3]
    for row in rows:
        for field in ("name", "layers", "signature", "missing_fault_rationale", "difference",
                      "non_fault_mimic", "cost", "expected_improvement", "viability", "source"):
            assert row[field].strip()
        assert "HOLDOUT-DTI" in row["expected_improvement"]
        assert "no numeric" in row["expected_improvement"].lower()
        assert row["status"].startswith(("UNTESTED", "DEFERRED"))
    assert "windowed radial spectral-slope" in rows[0]["difference"].lower()
    assert "NOT CURRENTLY VIABLE" in rows[1]["viability"]
    assert "NOT CURRENTLY VIABLE" in rows[2]["viability"]
    assert "not verified" in rows[1]["viability"].lower()
    assert "not checked" in rows[2]["viability"].lower()
    markdown = (ROOT / "research/hypotheses.md").read_text()
    assert "planning hypothesis" in markdown.lower()
    assert "global novelty" in markdown.lower()
    assert "Do not select any of these as the assigned method" in markdown
