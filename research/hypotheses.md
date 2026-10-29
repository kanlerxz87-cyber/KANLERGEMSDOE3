# Conditional geological hypotheses — session 12817d00

These are **unimplemented research proposals**, not assigned lanes, scores, projections, unique candidates or submission recommendations. Their ranking is qualitative information value versus cost. The top proposal was not run because mandatory protocol prerequisites fail before experiment one.

| Rank | Hypothesis | Specific layers | Physical signature / transform | Why it may find an uncatalogued fault | Difference from this repo | Non-fault mimic | Cost / viability |
|---:|---|---|---|---|---|---|---|
| 1 | **Cross-field Morse–Smale junction persistence** | RTP/TMI (bands 2, 14), TMI gradients (3, 9), isostatic gravity + gradients (13, 18, 11) | Signed scale-space fields → Morse–Smale ridge/saddle graphs → cross-field persistent junctions | Concealed relays/intersections can perturb independent potential-field topology without a strong surface trace or single ridge | No local Morse–Smale complex, saddle persistence or cross-field topological matching; local methods use Hessian ridges, phase, texture or pointwise classifiers | Intrusive/lithologic intersections, levelling seams, basin-fill contacts | **Medium; rank 1.** No extra external dataset is required in principle, but official core bytes are not present/authenticated here; execution is blocked by lane/evaluator/cache/registry prerequisites |
| 2 | **Two-sided directional-fabric entropy break** | RTP/TMI/gravity (2, 14, 13); elevation/slope (12, 19) as confounder controls | Opposing-side structure-tensor orientation distributions → Jensen–Shannon divergence | Buried fault juxtaposition can rotate structural grain where amplitude and scarp continuity are weak | Local code has pixel coherence/orientation, not two-sided distribution divergence or entropy across an axis | Angular unconformity, intrusive contact, survey blocks, cultural alignment | **Medium; rank 2.** No extra external data is required in principle; official core bytes are not locally authenticated; blocked |
| 3 | **Signed edge-migration stability under continuation** | TMI/RTP (14, 2), TMI gradients (3, 9), depth-to-base (15) | Track signed zero crossings through a fixed continuation/scale ladder; reward location stability as shallow responses decay | A deep fault-related source contrast may remain spatially stable beneath cover; the depth-to-conductive-base band is not automatically basement depth | Local multiscale ridges/phase do not track signed edge trajectories; peer Fourier-continuation work requires a direct novelty check | Deep lithologic contacts, basin margins, boundary artifacts | **Low; rank 3.** Cheapest falsifiable pilot, but official core bytes/cache, lane, evaluator and registry prerequisites are unavailable |
| 4 | **Hydrochemical geothermometer residual corridors** | GDR 1391 chemistry/temperature, elevation/slope, independent magnetic axes | Lithology/elevation-conditioned geothermometer residuals → coherent terminating/aligned corridors | Deep-fluid ascent can reveal permeable concealed structures away from mapped traces | No local chemistry-conditioned residual model; prior thermal features are proximity/temperature/halo based | Mixing, evaporation, groundwater advection, seasonality, pumping, batch effects | **High; rank 4; not viable yet.** Exact official chemistry bytes, fields, coverage and dates are unverified |

## Source and claim limits

- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and): official survey context for magnetic/radiometric layers; it does not validate any transform above.
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): official public code reference; it does not establish that signed edge migration improves DTI.
- [GDR submission 1391](https://gdr.openei.org/submissions/1391): official resource index for INGENIOUS-related data; index availability does not establish that the required chemistry table has been obtained or is spatially adequate.

## Required evaluation contract

Test every feature alone and treat two-sided AUC above 0.90 as leakage until disproved. Hide whole fault segments with a buffer, derive every catalogue feature from visible faults only and mask visible faults pixel-exactly. Use a centrally repaired pooled HOLDOUT-DTI evaluator with alpha 0.2, beta 0.8 and a 300 m triangular kernel. Report evaluator version, withheld positives, 95% spatial CI and paired CI versus a same-fold incumbent.

Before placement, compare the continuous surface **and explicit preview dots** with every registry entry. After writing, compare exact final dots. Rank correlation above 0.90 or more than 70% of candidate dots within Euclidean three pixels of any reference means duplicate and stops the lane. The registered spacing-5 lattice makes a 37,654-dot design mathematically unable to pass this literal stop; it cannot be silently exempted.

## 29 October 2026 expected-benefit and data-availability recheck

This dated addendum makes the qualitative DTI expectation and source status explicit. The ordering is **relative, conditional potential before implementation**, not an observed lift, calibrated probability, numeric score estimate, or assignment of a method lane. There is no defensible numeric expected DTI gain for any proposal.

| Rank | Qualitative expected DTI benefit | Why ranked here | Cost / confidence |
|---:|---|---|---|
| 1 | **Moderate-to-high conditional potential; unmeasured.** | Cross-field persistent junctions could combine independent magnetic and gravity evidence at concealed relays/intersections rather than depend on one high-amplitude ridge. | Medium cost; low confidence until leakage canaries and spatial holdout. |
| 2 | **Moderate conditional potential; unmeasured.** | A two-sided fabric change could expose fault juxtaposition missed by single-pixel strength, but orientation changes have many non-fault causes. | Medium cost; low-to-moderate confidence. |
| 3 | **Low-to-moderate conditional potential; unmeasured.** | Signed edge trajectories may reject shallow/noisy responses, but depth and continuation assumptions are uncertain and related peer work exists. | Low-to-medium cost; low confidence. |
| 4 | **Not estimable for this run.** Geological potential may be meaningful, but unavailable/unverified source fields make a usable expected benefit impossible to rank honestly. | Would add independent chemistry/temperature evidence if the needed measurements and coverage were confirmed. | High cost; blocked on archive bytes, fields, dates and coverage. |

| Proposal | Additional official external layer needed? | Verified availability now |
|---|---|---|
| Cross-field Morse–Smale | No, in principle; it uses competition magnetic/gravity layers. | Official competition data page redirects to login; the relevant core rasters are absent/authentication is false in this checkout. The restore script uses a public participant mirror, not an organizer download. |
| Two-sided directional fabric | No, in principle; it uses competition potential-field layers, with terrain only as a confounder control. | Same as above; no authenticated local data or canonical cache. |
| Signed edge migration | No, in principle; it uses competition potential-field layers and an optional internal depth-to-base band. | Same as above; no authenticated local data or canonical cache. |
| Hydrochemical residual corridors | Yes: exact chemistry/temperature observations and usable spatial/date metadata. | [GDR 1391](https://gdr.openei.org/submissions/1391) is a reachable public index with a CC BY 4.0 statement, but direct archive fetches returned HTTP 500. Exact archive bytes, fields, coverage and dates remain unverified; treat as unavailable for experiment design. |

The official [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [structural-discontinuities paper](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa) provide context, not measured support for a candidate's DTI gain. No hypothesis was implemented or tested in the 29 October continuation.
