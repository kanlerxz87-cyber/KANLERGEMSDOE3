# Project operating instructions

Before every work session, read `README.md` and the current `evidence/run-card.json`.
The README contains the standing user brief, scientific gates and parallel-run
protocol. Preserve the distinction between unverified historical claims, public
leaderboard observations, HOLDOUT-DTI with evaluator/count/CI, and organizer
submission-page receipts. Never call a projection a score.

Do not promote or upload a file on format validity alone. Do not exempt dense or
calibration references from the literal registry rule without an explicit protocol
revision. If the assigned lane, canonical cache, leakage canaries, matched holdout,
complete uniqueness audit or byte-bound validation is missing, fail closed. Never
invent a receipt, score, data access, filename, hash or a current leaderboard.
Promotion to a weekly slot is a separate selector step; this project does not
submit automatically. Preserve negative results.

Use the shared, pinned template tools rather than a private evaluator/writer
fork; record and report shared defects upstream. Keep large input data and caches
out of Git. Rebuild the site with `python scripts/build_site.py` after changing its
source evidence. Run `python -m pytest -q` and `python scripts/build_site.py --check`.
