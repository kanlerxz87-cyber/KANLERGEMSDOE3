import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems.metric import dti_score_fast, verify_organizer_worked_example

def test_organizer_worked_example():
    r = verify_organizer_worked_example()
    assert r["matches_0_60"]

def test_dti_perfect_and_empty():
    truth = np.zeros((20, 20), bool); truth[10, 5:15] = True
    valid = np.ones((20, 20), bool)
    assert dti_score_fast(truth.astype(np.uint8), truth, valid_mask=valid)["dti"] > 0.99
    assert dti_score_fast(np.zeros((20, 20), np.uint8), truth, valid_mask=valid)["dti"] == 0.0
