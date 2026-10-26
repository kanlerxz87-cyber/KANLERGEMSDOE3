#!/usr/bin/env bash
# Recover exact legacy instruments only; no checkout or raster-bearing archive.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
exec "$PYTHON" "$ROOT/scripts/restore_instruments.py" --profile legacy32
