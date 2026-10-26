#!/usr/bin/env bash
# Pinned public participant mirror, NOT an organizer-authenticated download.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  echo "Create .venv and install requirements.txt first; no credentials are required." >&2
  exit 2
fi
exec "$PYTHON" scripts/restore_inputs.py "$@"
