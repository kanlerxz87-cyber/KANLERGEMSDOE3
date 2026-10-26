#!/usr/bin/env bash
# Competition data is login-walled on DrivenData (no auth in this sandbox).
# This repo restores SHA-256-pinned mirrors from GitHub instead; the manual
# route on an unrestricted machine is:
#   1. Log in at https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#   2. Download training_features.tif, labels.tif, sample_submission.tif into data/raw/
#   3. Verify: sha256 must match registry/data_manifest.json pins.
# Automated mirror route used here:
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python scripts/restore_data.py --group core
.venv/bin/python scripts/restore_data.py --group external
.venv/bin/python scripts/prepare_data.py
echo "Data ready in data/raw/ (mirror copies, NOT organizer-authenticated; see IR-04)."
