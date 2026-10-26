#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "${PY}" ]]; then
  PY="python3"
fi
"${PY}" "${ROOT}/vendor/gems57/prepare_data.py" --fetch --cache-bands
"${PY}" "${ROOT}/scripts/download_competition_data.py"
