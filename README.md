# KANLERGEMSDOE3 — evidence-first fault prediction

**Start every session here and read [the standing request](PROJECT_REQUEST.md), [research audit](docs/research.md), and [run card](docs/data/run_card.json) before changing models.**

## Executive summary / download status

**DO NOT SUBMIT. There is no new validated unique GeoTIFF in this repository.**

[Executive summary](docs/executive-summary.html) · [Nine-site table](docs/data/sites.json) · [Submission instructions](docs/submission.md) · [Scientific hypotheses and sources](docs/research.md)

The original checkout contained only this README title. No prior training code or cached stack was present. This review adds pinned upstream evidence and an honest decision dashboard; it does **not** claim to have trained a winning model or completed the requested TIFF generation.

## Local verification

```sh
python scripts/review.py
python -m unittest discover -s tests -v
python scripts/promotion_gate.py docs/data/run_card.json  # expected exit 1: blocked
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

Only the Python standard library is needed for the review. The gate is a decision-schema checker, not a geospatial evaluator or TIFF validator. Shared upstream evaluator/writer files under `evidence/upstream/` are immutable audit material, **not** a replacement runnable template. Do not execute them as an integrated pipeline without their pinned dependencies and inputs.

GitHub Actions tests the report and deploys `docs/` to Pages on main. Pages deployment requires Pages to be enabled for GitHub Actions in the repository. Publication status must be checked rather than assumed.

## Next session, in order

1. Supply/recover a single-method lane; the user request omitted it.
2. Select the canonical shared template, restore its pinned cached stack and registry, and resolve input provenance. Public owner mirrors exist but are not organizer-authenticated.
3. Verify official metric/rules against accessible organizer materials. Whole-segment buffered, visible-only hide-and-recover evaluation is mandatory.
4. Finish semantic novelty checks on the candidate hypotheses, then run at most three experiments within the lane and two-hour budget. Canaries first; uniqueness before placement and on final dots.
5. Only publish an approved download after comparable holdout improvement, complete uniqueness and saved-byte format evidence. Separate selector approval and weekly-cap verification remain necessary.

## Principles

**Maximize P(Win):** favor falsifiable experiments and trustworthy estimates over attractive, unverified claims. **Own the Outcome:** automate checks, preserve negative results, and make blockers obvious rather than silently lowering gates. Fault mapping is the competition target; geothermal interpretation is not evidence of vent discovery.
