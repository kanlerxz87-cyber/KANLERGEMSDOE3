#!/usr/bin/env bash
# Restore the shared template's SHA-pinned owner mirrors; no organizer authentication implied.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$(bash "$ROOT/scripts/bootstrap_template.sh")"
export GEMS_DATA_DIR="${GEMS_DATA_DIR:-$ROOT/.cache/gems_data}"
GROUP="${1:-core}"
case "$GROUP" in core|external|scored|all) ;; *) echo 'Use: download_competition_data.sh [core|external|scored|all]' >&2; exit 2;; esac
"${PYTHON:-python3}" "$TEMPLATE/scripts/restore_data.py" --group "$GROUP" --target-dir "$GEMS_DATA_DIR"
