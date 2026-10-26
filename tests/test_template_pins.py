import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_vendored_template_byte_identical():
    pins = json.loads((ROOT / "registry" / "template_pins.json").read_text())
    for f in pins["files"]:
        p = ROOT / f["local"]
        assert p.exists(), f["local"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == f["sha256"], f["local"]
        assert p.stat().st_size == f["bytes"]

def test_note_limit():
    # Portal note in run card must respect the owner's 140-char limit (not template's 200).
    card = ROOT / "evidence" / "run_card.json"
    if card.exists():
        d = json.loads(card.read_text())
        assert len(d["submission_note"]) <= 140
