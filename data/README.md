# Input data (not committed)

`bash scripts/download_bilateral_data.sh` restores six hash-pinned **owner mirrors** to this
directory. SHA-256 proves consistency with the owner-published manifest, not identity with the
[authenticated organizer data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/).
The cached LiDAR and K/Th GeoDAWN products were actual model inputs; the 19-band training stack was
validated but not used as a predictor. Bulk data, scratch files and model caches are ignored by Git.

Never train on pixel values in `sample_submission.tif`: the mirrored sample contains positive pixels
exactly matching the labels, although the official page describes an all-absence sample. Use only its
finite-data mask and spatial grid.

The underlying [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
claims CC0 1.0, and [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
products are free and without use restrictions. These facts do **not** authenticate the mirror,
identify every source tile, or establish a license for the owner's derived caches and processing code.
Recheck rights and shareability before competition use; see [source register](../docs/SOURCES.md).
