#!/usr/bin/env bash
# Zero-API-quota SHA-256-verified restoration of competition, external, and registry rasters.
# Stores all large rasters in .cache/gems_data/ (excluded from Git and Arena snapshots).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "${PY}" ]]; then
  PY="python3"
fi

exec "${PY}" "${ROOT}/scripts/restore_data.py" "$@"
