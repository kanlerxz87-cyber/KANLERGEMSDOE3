#!/usr/bin/env bash
# Read the pinned provenance first. Does not log in to DrivenData or upload.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
"$PYTHON" scripts/restore_data.py "$@"
