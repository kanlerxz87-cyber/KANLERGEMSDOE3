> **Historical pre-experiment snapshot:** superseded by the [current README](../README.md) and [run card](../evidence/run-card.json). Assertions about missing inputs or zero experiments describe an earlier state.

# Three-pass verification record

## Pass 1 — implementation
- Initial branch/repository checked: only a one-line README, no existing work to continue.
- Retrieved priority-site docs/READMEs, selected shared-tool/evidence snapshots, official reference README.
- Retrieved all nine pinned historical TIFFs and small template/labels mirrors; each historical SHA256 matched.
- Independently recomputed 72 directed Euclidean <=3 px overlap comparisons on identical grids.
- Built static executive summary, submission guide, four-hypothesis preregistration and continuation review.

## Pass 2 — adversarial review
- Checked directionality (overlap is not symmetric), Euclidean versus square-buffer distance and <=3 px boundary.
- Empty masks fail rather than being called unique. Grid mismatch fails rather than resampling silently.
- Format validator rejects NaN, Inf, below-zero and above-one values and mismatched CRS/transform.
- Found no cached stack or complete registry: do not claim scientific validation or candidate uniqueness.
- Environment disallowed global pip installs: used an isolated ignored virtual environment.
- Removed the hard-coded workspace path from the source refresh utility; matched requirement versions to installed ones.

## Pass 3 — original-request reconciliation
- Tests pass; site rebuilds deterministically; source bytes checked against their Git blob IDs.
- Numbers in geometric audit are not labelled as scores. No holdout or organizer result invented.
- Full continuous-surface and full-registry tests are missing, explicitly null, not marked passed.
- End run card is negative; no raster hash/name invented; comment <=140 characters; zero slots used.
- Original long prompt is condensed, not verbatim archived; explicitly labelled as such.
- Not fulfilled: new validated TIFF, high-scoring model, score estimate, assigned lane, full official-source
  verification and current feed. These cannot be honestly manufactured from this checkout and access.
- Automated CI and Pages workflow added; actual cloud deployment remains separately observable.
