# Executive scientific review — 26 October 2026

## Decision

**DO NOT SUBMIT. No genuinely new, scientifically qualified TIFF exists in this session.** No geological experiment or submission slot was used. The requested winning submission is not yet delivered. A negative result is preferable to a renamed historical raster or a fabricated score estimate.

This session starts from the populated review repository at `f82397e`, not from an empty checkout. The old “only data placement remains” claim is inaccurate. Data placement has now been completed from pinned participant mirrors, but independent scientific and provenance gates still fail.

## What this session actually completed

- Restored the complete core multiband input (19 bands), labels, existing-fault alias, sample template and SGMC proxy through public Git transport. Every byte stream matches the shared manifest's SHA-256 and size. This is **mirror integrity, not organizer authentication**.
- Ran the **unmodified shared** `prepare_data.py`, producing sanitized raw-band copies. The full shared 35-channel feature stack was **not** regenerated. Its source receipt exists, but its bytes and expected digest were not published in the pinned tree.
- Independently checked CRS, shape and transform of core features, labels and proxy against the sample. See [input audit](../evidence/input-integrity.json). Raw missing/sentinel values affect 3,073 footprint pixels across one or more bands; 58,171 is the count summed across bands, not the count of distinct missing pixels. They must never become negative prediction values.
- Restored and source-locked 13 unmodified shared-tool/dependency files from [GEMSDOE32 at an immutable commit](https://github.com/buffedlizard55-lab/GEMSDOE32/tree/400b60d4a6d99f425ee90504e6c4552227556dd1). No private metric or writer fork was introduced.
- Reproduced a shared evaluator bookkeeping defect using a synthetic fixture: a nonempty prediction in a zero-truth cell is recorded in that cell's FP count but omitted from pooled spatial-block FP totals. Existing [upstream issue #41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41) already tracks it; we did not open a duplicate. **This is not evidence that the historical leaderboard results were affected.** The local runner fails closed until a central repair is pinned.
- Confirmed that the shared hide-and-recover entry point binarizes nonzero soft inputs. Do not describe its output as evaluation of the original probabilities. [Existing upstream issue #37](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37).
- Refreshed immutable source-commit observations for all nine priority repositories. This feed detects source changes; it does not turn homepage approval labels into this project's approval or authenticate score claims.

## Nine-site historical comparison

The nine historical raster hashes and all 72 directed pairwise Euclidean-within-3-pixel overlaps were independently recomputed from the restored bytes. **Every winner exceeds the requested 70% stop against another winner**; even the smallest directed pairwise overlap exceeds it. These are geometric measurements, not model scores. Hash changes caused by nodata, compression or renaming do not establish semantic novelty.

The user-provided historical best is the H33 B2 file on GEMSDOE32, with the **unverified owner-reported claim** `0.2778`. There is no submission-page receipt binding this score to these bytes. No historical file is recommended for a real slot. See the site table and [machine audit](../docs/audit.json) for every exact file, hash, encoding check and overlap. Estimates remain **not estimable**, not zero.

## Why might H33 B2 have performed better?

The participant sources describe an H19-descended sparse-dot family with catalogue-distance thinning. The pinned B2 raster has 37,654 positive pixels. All of its dots are within 3 pixels of the GEMSDOE24, 25, 27, 30 and 31 reference dots; coverage against the other priority references is also extremely high. This supports shared geometric ancestry, not a new physical discovery mechanism.

The [official DTI equations](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) explain a plausible **emission-efficiency** mechanism. A truth pixel takes the maximum distance-weighted prediction credit, while uncredited prediction mass adds FP penalty. Removing redundant dots can reduce FP without losing much coverage; removing the wrong dots increases FN. The triangular kernel has zero credit exactly at its 300 m boundary. Therefore maximizing dot count, drawing thick ridges, or picking the largest magnetic gradient is not inherently optimal.

However, the historical score differences do not isolate which deleted dots mattered. They lack paired out-of-fold ablation, a score-to-file receipt and the hidden truth. The family may mostly encode the same ridges and differ in emission budget. It is not scientifically defensible to claim a causal B2 gain, reconstruct hidden labels from past scores, guarantee a result above the reported history, or project a leaderboard ceiling.

The [DrivenData Staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2) states that **existing fault pixels** are excluded in both rounds. It does not justify applying a broad exclusion collar around hidden faults. Fold-local catalogue features must be rebuilt from visible faults only; a final TIFF already zeroed with all known labels is not a legitimate hide-and-recover prediction for those withheld labels.

## Score provenance and current official observation

The [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) fetched on 26 October lists xiaofanhu first with displayed value `0.4437`. This is an **official-page observation, not a submission-page receipt** and not a forecast for any project artifact. It is not relabelled as ORGANIZER-CONFIRMED per-file evidence. The prompt's `0.3195` and `0.4413` statements should no longer be treated as verified current targets.

No new HOLDOUT-DTI result exists. No ORGANIZER-CONFIRMED submission-page receipt was obtained. Geometric overlap, input counts, source freshness and synthetic operator tests must never be presented as either score class. A future holdout result must include evaluator version, withheld-positive count and spatial-block 95% CI; promotion also needs a positive paired improvement on identical folds against a recorded incumbent.

## Correction to the earlier format verdict

The official [submission-format page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) requires a single float32 band, the EPSG:32611/100 m reference grid, confidence values in `[0,1]`, and null/NaN outside bounds. The official [reference notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb) is not the format authority: its output cell omits an explicit nodata argument and may inherit a different numeric dtype.

The previous audit overinterpreted “outside bounds” as a proven requirement to match every masked pixel of an unauthenticated sample and categorically called seven historical zero-outside files invalid. That portal-rejection conclusion was not established. Conversely, a shared writer's all-finite output is not proof that the portal accepts the bounds encoding.

The validator now reports **two named local profiles**:

1. `template-mask`: finite unmasked `[0,1]` predictions inside; null/masked/NaN outside the sample mask.
2. `finite-grid`: finite `[0,1]` values across the entire grid and zeros outside the sample mask.

The historical seven zero-outside files pass the second local profile; two NaN-outside files pass the first. Neither outcome is a portal receipt or permission to submit. A finite negative nodata sentinel can pass the mask profile while failing a portal-wide numeric scan. Infinite unmasked padding is not accepted as null/NaN. The exact bytes of the user's rejected file are absent, so its range-error cause remains unknown. Do not silently clip or repair a candidate to conceal a modelling bug.

## Geological reasoning and research limitations

The official task is missing **fault** discovery. A magnetic or thermal anomaly is not proof of a fault, and a fault is not proof of a commercially useful geothermal vent. [USGS GeoDAWN metadata](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) distinguish surface radiometric information from subsurface magnetic information and explicitly warn about variable terrain clearance. Flight geometry, levelling seams, lithologic contacts, lake shorelines and drainage evolution are serious alternative processes, not cosmetic caveats.

The ranked shortlist targets interactions and topology rather than another H19/H33 thinning pass. None is implemented or cleared as globally novel. [GDR #1391](https://gdr.openei.org/submissions/1391) is now verified as a public CC BY 4.0 resource index, including shallow probes and paleogeothermal deposits; an attempted probe ZIP fetch failed. Official source links exist, but required binary coverage, season and depth metadata are not verified. New-data variants are not called viable on that basis alone.

Hide-and-recover of mapped faults also has a population-shift limitation: mapped/exposed faults may not represent concealed faults selected by the competition experts. A good holdout result is necessary under this protocol, not a calibrated estimate of leaderboard performance. Canary AUC below the leakage threshold is not proof of no leakage; feature provenance must still be audited.

## Remaining gates / next session

1. Resolve the absent lane paragraph through the parallel coordinator; no geological method is silently claimed here.
2. Pin a centrally corrected shared evaluator after upstream issue #41 is resolved; do not patch vendor copies privately.
3. Obtain the canonical feature-stack bytes and expected digest, plus the complete submission/surface registry. A filtered priority-site manifest is not complete, even when every listed download succeeds.
4. Record the same-evaluator, same-fold incumbent; generate fold-local features after whole-segment buffered withholding; run single-feature canaries.
5. Test at most three experiments in two hours. Check surface correlation **and preview-dot overlap before writing**, then final correlations and dot overlaps. Stop on any literal duplicate threshold.
6. Only an improving, genuinely distinct candidate is written through the shared writer into a research directory; validate the saved bytes and exact hash automatically. No human raster inspector is a required gate.
7. The separate selector checks the account's actual remaining weekly cap. The official rules specify three submissions per week, but no account quota or slot has been authorized. Preserve the eventual submission-page receipt, and disclose AI assistance as required in the narrative.

Full verified-source excerpts and their limited scope are in [official claims](../evidence/official-claims-20261026.json). No claim is made that all external files, the entire rules PDF, all sibling repositories or the live account state have been verified line by line.
