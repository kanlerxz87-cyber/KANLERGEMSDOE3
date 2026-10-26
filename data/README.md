# Input data (not committed)

`bash scripts/download_competition_data.sh` restores hash-pinned **owner mirrors** to this directory. This verifies that the downloaded bytes match the published owner manifest; it is not independent proof that the inputs are identical to those on the authenticated organizer page. The official data are available to registered participants from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ . The derived USGS caches are identified in the manifest. Bulk data, scratch files, and model caches are ignored by git.

Never train on the pixel values of `sample_submission.tif`: the inspected owner mirror contains nonzero values matching labels, although the official page describes an all-absence sample. Only use its finite-data footprint and grid. Match the inputs against authenticated originals before seeking slot approval.
