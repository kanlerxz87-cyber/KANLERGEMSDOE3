# Pre-registration: candidate fault-discovery hypotheses

Recorded 2026-10-26 UTC **before implementing or running a new model**. These are
hypotheses, not verified discoveries or leaderboard projections. The repository was
empty apart from a README at the start of this session. “New here” does **not** mean
that exhaustive novelty across all sibling sites has been established. The assigned
method paragraph required by the parallel-run protocol was absent; therefore none
of these is represented as an authorized lane or an executed experiment.

## Qualitative ranking

| Rank / expected potential / cost | Layers and signature | Why it might recover a fault missing from the catalogue | Difference and concrete non-fault mimic |
| --- | --- | --- | --- |
| 1 · higher / medium | **Cross-flank magnetic-texture displacement.** Reuse the shared stack's total magnetic intensity and reduced-to-pole channels, plus detrended elevation. Compare oriented magnetic textures on opposing sides of a proposed narrow trace using normalized cross-correlation across multiple scales; favor consistent offsets corroborated by a terrain break. | A fault can offset a magnetic source under cover even when no mapped surface trace exists. This looks for *displacement of texture across a line*, not merely a magnetic edge. | No such implementation exists in this checkout. Sibling methods use magnetic edges, curvature and multi-physics concordance; exhaustive distinctness is unproven. A volcanic contact, a fluvial magnetic-mineral concentration, or survey stitching could mimic an apparent offset. |
| 2 · moderate / medium | **Lithology-aware magnetic–gravity discordance.** Use magnetic, isostatic-gravity and elevation bands; compare edge orientations and cross-flank polarities at two scales, limiting conclusions where an independently mapped lithological contact provides an alternative explanation. | A covered structural boundary might juxtapose contrasting rocks and yield a coherent offset across fields without a catalogue trace. | New in this checkout; related cross-field gates already exist in sibling repositories, so novelty is uncertain. Intrusive contacts and density/magnetization changes without fault displacement can produce the same pattern. An official geologic-map layer and coverage/licensing check are required before this can be a viable run. |
| 3 · moderate / medium | **Age-consistent scarp progression.** Combine shared elevation/scarp features with an independently sourced surficial geology/age map; test whether parallel scarp heights increase consistently across older adjacent surfaces, instead of using slope alone. | Repeated displacement can be preserved on successive alluvial surfaces even if a fault trace is omitted. | New in this checkout; sibling work already tests scarp persistence, dipoles and D8 drainage. Alluvial incision, shorelines and age-map errors can mimic the sequence. Coverage and age attribution must be verified before use. |
| 4 · uncertain / medium-high | **Thermal-neighborhood asymmetry under sampling-effort correction.** Use licensed INGENIOUS well/spring temperature and background/effort data together with cached magnetic and gravity features; test whether a coherent contrast in local thermal residuals aligns with a geophysical boundary. | A blind conduit may be associated with a spatially asymmetric temperature anomaly rather than a visible scarp. | New in this checkout, but sibling GDX and HVG runs already use effort-normalized thermal/geochemical features; a prior-art search and ablation are mandatory. Groundwater flow, drilling density, depth and climate can all create an apparent gradient. |

The ranking is expert judgment about mechanism and cost only; no predicted score or
performance improvement has been established. [USGS discusses magnetic-anomaly
interpretation and its non-uniqueness](https://pubs.usgs.gov/publication/70032258).
[USGS describes magnetic anomalies potentially caused by concealed faulting **or**
fluvial mineral concentration](https://pubs.usgs.gov/of/2000/of00-188/of00-188.pdf).
[USGS identifies erosion and landslides as nontectonic scarp mimics](https://www.usgs.gov/programs/earthquake-hazards/faults).
[INGENIOUS GDR record 1391](https://gdr.openei.org/submissions/1391) publicly lists
well/spring and 2-m temperature data under CC BY 4.0; its metadata was accessible to
our research tool, but the raw official-host downloads cannot be reached from the
sandbox shell's GitHub-only network. Metadata access is not proof of complete
coverage or fitness for a particular model. Record precise source, version, coverage,
license, preprocessing and SHA before any use.

## Frozen evaluation plan if the lane and stack become available

1. Limit execution to the single assigned lane; maximum three experiments or two
   hours, whichever comes first. Do not spend a competition slot in this step.
2. Reuse the template's cached stack and shared `evaluate_holdout.py` and
   `submission_writer.py`; do not create a private evaluator/writer fork. Derive any
   catalogue-dependent feature only from each fold's visible faults; withhold whole
   segments with a buffer and mask visible faults pixel-exactly.
3. Run single-feature leakage canaries before trusting an arm. AUC > 0.90 is a stop
   pending proof; unavailable or ambiguous canaries are not a pass.
4. Check exact full-footprint rank correlation before placement, then rank and
   directional within-3-pixel overlap after placement against every compatible
   refreshed registry raster. Exceeding 0.90 or 70%, respectively, is a duplicate
   stop; do not silently exclude the lattice or other dense references.
5. Compare pooled DTI, using the 300 m triangular kernel and alpha 0.2/beta 0.8,
   with the current *same-evaluator*, same-fold baseline. Report evaluator version,
   withheld positives, 95% spatial-block interval, and paired interval. A catalogue
   holdout is not an estimate of the public leaderboard.
6. Reopen the exact saved TIFF and verify type, footprint, range, CRS, shape,
   transform, SHA and note length. Format compliance does not authorize submission.
   An independent selector must separately authorize a weekly slot.

No numerical HOLDOUT-DTI is asserted for any hypothesis above: no candidate was run.
