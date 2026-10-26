# Preregistered ideas — no experiment has run

Reviewed 2026-10-26, **before** implementing a model. The checkout initially had
no geological methods at all. The proposals are new *to this checkout*, not
proven novel across the entire fleet. Rank reflects geological rationale and
implementation cost, not a measured or predicted leaderboard score. A unique
method lane was not supplied in the current prompt; these are ideas, **not an
assigned lane**. The literal registry preflight found a universal blocker, so
all model building, holdout fitting and dot placement stopped.

| Rank | Hypothesis / cost | Layers and signature | Why it might find missed faults | Difference / non-fault mimic |
|---|---|---|---|---|
| 1 | **Scale-persistent magnetic–gravity interface under cover** / moderate CPU | Cached `rtp`, `iso_grav_anom`, `depth_to_base_surf`, `cond_surf`: multi-scale gradients, axial (sign-invariant) directional agreement and persistence; test a cover-dependent gate. Check actual band semantics against official metadata before use. | A buried lithologic offset may have magnetic and gravity edges without a mapped surface trace; do not require distance to known faults. | This specific combination is unimplemented here. Other repos already use cross-gradients and magnetic continuation, so fleet-wide novelty is unproven. A depositional contact or igneous intrusion can produce the same signature; acquisition striping can mimic an edge. |
| 2 | **Scale-consistent topographic step with independent gravity corroboration** / moderate CPU | Cached `det_elev`, `det_elev_slope`, `iso_grav_anom`: opposing profile shoulders and a co-aligned subsurface gradient, compared across smoothing scales. | Low-relief or degraded lineaments with a buried density boundary could be absent from the existing catalogue. | Not implemented here; related scarp, dipole and cross-gradient methods exist in sibling repos. Fluvial terrace risers, lake shorelines and bedrock contacts can mimic it. |
| 3 | **Cover-conditioned strain transition at a persistent magnetic contact** / low–moderate CPU | `geod_shearrate`, `geod_dilaterate`, `geod_2ndinv`, `rtp` and `depth_to_base_surf`: a broad strain-transition × localized multi-scale contact, with a cover interaction. | Localized inherited structures may focus present-day deformation despite weak surface expression. Geodetic layers are coarse; this is a prior, not a fault observation. | Not implemented here; similar strain/potential-field coupling is present elsewhere in the fleet. GPS interpolation artifacts and geological contacts are plausible mimics. |
| 4 | **Shallow thermal-gradient lineament corroboration** / high; **not currently viable** | The GDR 1391 2 m temperature-probe dataset plus the cached magnetic and topographic layers: spatially robust thermal gradient aligned with a potential-field break. | Hydrothermal upflow on unmapped fractures can create a shallow anomaly. Sparse sites do not establish full-region coverage. | Not implemented here; other siblings have explored geothermal probes. Seasonal heating, soil moisture and infrastructure mimic shallow anomalies. The [official GDR record](https://gdr.openei.org/submissions/1391) offers a public, CC BY 4.0 download, but binary access/ROI coverage and usable fields were **not** verified in this network-restricted runtime; not proposed as runnable yet. |

The cache is a SHA-verified **third-party mirror**, not an authenticated
DrivenData download. The [official USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
documents magnetic/radiometric survey data; its record is CC0. The [official
3DEP page](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
reports free products without use restrictions. The [official competition
problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
describes the provided layers and requires permission to use and share external
data. These sources support data availability, not the hypotheses' validity.

## Required next experiment, once policy/lane blockers are resolved

Freeze the assigned single lane and same-evaluator baseline *before* fitting.
Reuse the pinned `gems57` cached stack, scoring module `evaluate_holdout.py`
and `submission_writer.py`. First correct and verify the shared fold builder
upstream: its current boundary erosion and 12-pixel chunks do not establish a
buffer around whole original fault segments (see [analysis](analysis.md)).
Withhold entire original segments with a spatial buffer,
recompute catalogue-derived features from visible faults only, mask visible
fault pixels exactly, and pool the official triangular-kernel DTI terms. Test
each feature separately on the held-out fold; oriented AUC above 0.90 stops the
run until provenance is audited. Calculate a paired spatial-block 95% CI and
compare to the current best measured **with the same evaluator and same folds**.
Check the entire accessible registry both before placement and on final dots;
check saved bytes and defer slot selection to a separate selector. None of these
steps has been run on a candidate in this checkout. Mapped-fault holdout is a
biased proxy for genuinely new expert labels and cannot establish a leaderboard
score.
