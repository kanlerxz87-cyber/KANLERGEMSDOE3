"""KANLERGEMSDOE3 lane code.  Shared metric/holdout/writer/validator come from vendor/gems57
(unchanged, provenance-pinned); only lane-specific detector, allocation and gate glue live here."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "vendor",):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
