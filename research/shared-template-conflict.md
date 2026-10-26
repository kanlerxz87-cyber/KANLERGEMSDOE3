# Unresolved shared-writer footprint conflict

The official problem description calls for null/NaN outside the bounds. Two unchanged pinned
GEMSDOE24 versions are present: `fc2bc6f` defaults to `outside="nan"`, while `7ab1c8f` defaults
to `outside="zero"`. Both `check_variants` implementations mark `outside_is_nan_official_text` as non-hard; the CLI can therefore describe a
zero-outside file as `format_valid` while `official_format_compliant` is false. The separately
integrated `scripts/validate_submission.py` uses the template mask and rejects valid exterior zeros.
Synthetic regressions in `tests/test_shared_template.py` isolate the two packages and demonstrate
both defaults and the validator disagreement without creating a real candidate. The user's previous portal failure cannot be attributed to either case
without the actual rejected file and response.

The shared template and its pinned Git blobs are **unchanged**. The requested central repair cannot
be truthfully represented as complete on this single-repository, fixed-branch session. Do not make a
private fork or bypass the inconsistency. An authorized shared-template maintainer should reconcile
the official footprint contract with the organizer/portal, update the central writer and hard-gate
validator together, add round-trip tests for NaN/masked exterior and finite [0,1] inside, and repin
the new shared version. Until then, no local format pass authorizes a submission.
