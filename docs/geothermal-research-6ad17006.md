# Geothermal discovery: source audit and conditional hypothesis queue

**Observed 27 October 2026 (UTC).** This is research, not a model result, probability
of finding a vent, or a leaderboard forecast. Public source text below was retrieved
through the page-retrieval tool; the sandbox itself cannot download binaries from the
USGS, GDR, S3 or DrivenData hosts. The fetched pages and the linked metadata are not a
substitute for obtaining and verifying the actual datasets. No new geological experiment
was run. The user-requested parallel method paragraph was not present, so no hypothesis
was assigned as this session's lane.

## Primary-source ledger

| Source | Directly supported observation | Implication / limit |
|---|---|---|
| [DOE/NLR official rules, §§3.2–3.6](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | One single-layer, 100 m fault-prediction GeoTIFF is required; automated feedback is limited to up to three entries per week as specified on the competition site; one final entry is chosen for both prize rounds. Private and subsequently expert-revised labels are separate from the public leaderboard. | A good public score alone does not establish a winning private result. Account-specific remaining capacity was not accessed. The local technical/novelty checks can be automated; the organizer's later expert-review process is outside this project's control. |
| [DOE/NLR rules, §3.2 and Appendix A.5](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Generative-AI use must be described in the narrative; competitors are responsible for accuracy and authorship. Third-party material requires appropriate rights and disclosure. | Document AI assistance and verify rights for participant-derived caches and code before a final entry. A hash match is not permission or an organizer provenance certificate. |
| [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Aeromagnetics inform subsurface geology; radiometrics inform surface geology/soil. Area 2 used nominal east–west flight lines 400 m apart, with terrain-dependent flight clearance; both products underwent corrections and leveling. The release is marked CC0. | Surface soil/lithology, topography, flight clearance and residual acquisition/processing patterns are plausible confounders. A 100 m output grid does **not** establish independent 100 m geophysical observations; test directional artifacts and spatially correlated errors. Do not assume an anomaly is a fault or vent. |
| [USGS Surprise Valley paper](https://www.usgs.gov/publications/influence-pre-existing-structures-geothermal-springs-inferences-potential-field) | The authors interpret a long intra-basin magnetic high as a buried dike swarm and report spring locations at breaks/bends. | This supports considering concealed structures away from range fronts, but a **dike/intrusive contact is a concrete non-fault mimic**. The observed local association does not validate this project's predictions. |
| [GDR INGENIOUS compilation](https://gdr.openei.org/submissions/1391) | The public index lists 2 m probes, wells/springs, fault maps, seismicity and other layers under CC BY 4.0 with attribution. It says Quaternary faults v2 supersedes v1. | The specific [2 m probes archive](https://gdr.openei.org/files/1391/2m_temperature_probe_INGENIOUS_regional_data.zip) was attempted through the page retriever and returned HTTP 500; bytes, coverage, dates and suitability remain unverified. Independent fault datasets can contain withheld labels and must not leak into any fold. |
| [USGS ScienceBase GeoDAWN metadata](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7?format=json) | The index lists `22103_area1_tiffs.zip` and `22103_area2_tiffs.zip`, their sizes and catalog MD5s. | The index was readable, but neither archive was downloaded or checksum-verified here. The participant radiometric derivatives and their licenses are not authenticated by the official metadata. |
| [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) and [National Map 1 m query](https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Digital%20Elevation%20Model%20%28DEM%29%201%20meter&bbox=-119.0%2C39.5%2C-118.8%2C39.7&outputFormat=JSON&max=2) | USGS states 3DEP products are free and without use restrictions. The query lists 1 m DEM tiles `USGS_1M_11_x32y438_NV_WestCentral_EarthMRI_2020_D20.tif` and `...x32y439...` with download URLs and extents. | The query is inside the **bounding rectangle** of the participant-mirror template, not proof that either tile intersects its valid footprint. Tile bytes, full coverage, seam behavior and alignment were not verified; a 1 m model is not yet executable here. |
| [Official reference solution README at pinned commit](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) | The reference solution documents both GPU and CPU-only environments, and says GPU training is much faster. | The old statement that a GPU is strictly required is too strong. Feasibility and runtime for this project's future model were not benchmarked. |

## Four untried proposals, ranked qualitatively

This refines the earlier cross-scale/drainage/alteration/thermal alternative queue.
A concurrently merged session preserved a different four-proposal queue in
[`research/hypotheses.json`](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/research/hypotheses.json);
neither queue assigns this session's lane. The ranking is a **hypothesis about
relative potential**, not an estimated DTI gain or a score. No proposal is eligible
to run until the assigned lane and shared prerequisites are resolved. These
transformations are differentiated from the inspected local code, not certified novel
against every participant repository or the geological literature.

| Relative DTI-improvement priority / cost | Layers and proposed physical signature | Why it might reveal a catalogue-missing structure | Contrast with inspected local code and named non-fault mimic | Actual availability |
|---|---|---|---|---|
| 1 · medium | TMI/RTP and GeoDAWN K/Th/U: persistent magnetic edge combined with **signed cross-edge radiometric derivative reversal/termination** across scales. | A buried structural boundary might persist magnetically while changing shallow surface composition across an unmapped segment. Do not use distance from the full catalogue as a positive label. | [`gpc.py`](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/0df42aa31dbf501a61adee44db2d874ee913abed/src/kanler3/gpc.py) uses RTP/gravity/depth/elevation orientation, not this radiometric signed-normal termination; [`h1_dcap_lhc.py`](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/0df42aa31dbf501a61adee44db2d874ee913abed/src/kanler_gems/h1_dcap_lhc.py) multiplies magnetic contact by K/Th/hydro context, not this proposed derivative interaction. Mimics: intrusive lithologic contact, soil contrast or survey seam. | **Not viable yet:** official archives listed but bytes not obtained; shared derived cache/digest absent. |
| 2 · high | USGS 3DEP 1 m DEM (optionally 100 m detrended elevation): construct tributary networks and test **repeated signed channel displacement** along a candidate transverse line. | Coherent offsets in multiple independent channels could reveal a trace without a continuous scarp. | Existing [`features.py`](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/0df42aa31dbf501a61adee44db2d874ee913abed/src/kanlergems3/features.py) includes chi/terrain and scarp features; repeated paired channel-displacement graph inference was not found in the inspected local methods. Mimics: stream capture, alluvial-fan avulsion, shoreline reworking or DEM seams. | **Not viable yet:** only tile metadata listed; byte access, valid-footprint coverage and 1 m alignment not established. |
| 3 · medium | GeoDAWN K/Th/U or ratios plus magnetic edge: seek **paired, opposing along-strike alteration-front terminations** rather than merely high anomaly values. | An unmapped cross-structure might compartmentalize or terminate a shallow alteration pattern. | The local [`features.py`](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/0df42aa31dbf501a61adee44db2d874ee913abed/src/kanlergems3/features.py) computes a smoothed K halo; the paired endpoint topology is different in definition, not yet empirically unique. Mimics: stratigraphic contacts, erosion, soil or moisture contrasts. | **Not viable yet:** exact source-band meaning, bytes, radiometric sensitivity and cache provenance remain unresolved. |
| 4 · high | Official GDR well/spring and 2 m temperature observations plus DEM/aspect and drainage: model **terrain/season-corrected cross-line residual sign consistency**. | Correlated thermal residuals could corroborate a concealed permeable structure, not prove its presence or productivity. | The local feature builder smooths probe and spring/well proxies; it does not establish the proposed residual sign test. Mimics: groundwater advection, seasonality, pumping and land use. | **Not viable yet:** the attempted official probe ZIP returned HTTP 500; representative coverage and sampling dates were not checked. |

## Falsification and evaluation when prerequisites exist

1. Freeze the assigned single lane, layer provenance, feature list, non-fault controls,
   experiment ledger and fixed deadline. Reuse the authenticated shared feature stack;
   do not recreate it privately.
2. Use buffered whole-segment spatial holdouts; recompute every catalogue-derived
   feature from visible faults only and mask visible fault pixels exactly. Test every
   feature alone on the same holdout; AUC greater than 0.90 is a leakage alarm.
3. Once a **centrally repaired and pinned** evaluator passes synthetic conservation
   tests, compare the candidate to the same-fold incumbent using pooled HOLDOUT-DTI
   (alpha 0.2, beta 0.8, triangular 300 m), reporting version, withheld positives and a
   spatial-block 95% CI. A paired interval should support improvement; this is not a
   calibrated organizer score.
4. Compare the saved pre-placement surface **and preview dots** to the complete
   registry, then compare the exact final dot raster again. Stop and log any signed
   rank correlation >0.90 or directed dot overlap within 3 pixels >70%; never exempt
   the dense lattice or guess dots from a soft diagnostic. Freshness and inventory
   completeness must be independently established.
5. Reopen the exact TIFF against an organizer-authenticated template and run both the
   shared and local saved-byte checks. The actual earlier rejected TIFF is absent, so
   no local profile proves what caused its range error or guarantees portal acceptance.
   Only a separate selector can consider a slot and current account cap.
