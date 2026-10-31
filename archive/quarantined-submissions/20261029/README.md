# Quarantined research artifact — not for competition use

This folder preserves the unchanged prior research raster, its ZIP, and its run card outside the published `docs/` tree. The previous repository homepage incorrectly described this file as unique and made it downloadable.

- TIFF: `kanler-geofault-propensity-20261029T031629Z-f705bdebde7e-nan.tif`
- TIFF SHA-256: `80cacf1d6a303e338cd5564b715423a60f2cd2dd569d1ab6275056cf2074279d`
- ZIP SHA-256: `bf88d825df331cab45ee85c2df52ca66b0f0d29cd4c8c08750acdca2156e3162`
- Decision: **do not download for competition and do not submit**.
- Reason: the raster contains 7,111,787 NaN cells over the full grid. Finite values are in `[0,1]`, but the exact footprint mask is not present here to verify NaN locations. Its old validator receipt is internally contradictory, there is no complete registry clearance, and the holdout is a local reimplementation rather than an organizer-confirmed score or leaderboard estimate.
- Full byte audit: [`evidence/kanler-geofault-propensity-quarantine-20261031.json`](../../../evidence/kanler-geofault-propensity-quarantine-20261031.json).

Preserving this artifact is for audit/research only; it is not a recommendation, a fresh submission, or a unique candidate.
