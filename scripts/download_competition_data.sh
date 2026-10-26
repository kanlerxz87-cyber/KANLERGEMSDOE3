#!/usr/bin/env bash
# Restore SHA-pinned competition inputs, external layers, or full KANLER-H1 stack.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GROUP="${1:-kanler-h1}"
if [[ "$GROUP" == "kanler-h1" || "$GROUP" == "--kanler-h1" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PY="$ROOT/.venv/bin/python"
  else
    PY="${PYTHON:-python3}"
  fi
  exec "$PY" "$ROOT/scripts/download_competition_data.py" "${@:2}"
fi
TEMPLATE="$(bash "$ROOT/scripts/bootstrap_template.sh")"
export GEMS_DATA_DIR="${GEMS_DATA_DIR:-$ROOT/.cache/gems_data}"
case "$GROUP" in core|external|scored|all) ;; *) echo 'Use: download_competition_data.sh [kanler-h1|core|external|scored|all]' >&2; exit 2;; esac
"${PYTHON:-python3}" "$TEMPLATE/scripts/restore_data.py" --group "$GROUP" --target-dir "$GEMS_DATA_DIR"
