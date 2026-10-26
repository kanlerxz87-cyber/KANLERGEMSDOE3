# Executive scientific review — 2026-10-26

## What was actually found

The initial repository at d795e4e contained only `README.md` with one heading. There were no previous-session
next-step scripts, data, GPU training pipeline, cached features, holdout splits, registry or deployed site.
The claimed “single remaining blocker is data placement” does not describe this repository.

Nine sibling READMEs and docs homepages and selected GEMSDOE32 evidence were fetched through GitHub.
`sources/retrieval.json` records successful/failed paths and Git blob IDs. These snapshots are third-party
project claims, not official competition verification. Missing CSV paths are not evidence that a site
has no score ledger elsewhere.

For forensic learning only (not as submissions), `scripts/restore_audit_data.py` restored nine pinned historical TIFFs plus an owner-mirrored sample template/labels into ignored `data/`. `scripts/audit_rasters.py` recomputed and verified each TIFF SHA-256 against the pinned manifest, checked the shared grid, and independently recomputed all 72 directed dot-overlap pairs. Every historical winner exceeds the 70% duplicate stop; the minimum is 86.718954%. These are **geometric audit numbers, not scores**. Exact masks can match despite different compression, nodata handling or byte hashes. Therefore none of these historical files satisfies the requested uniqueness rule. Continuous surfaces were not restored and their rank correlation remains unknown; final-dot overlap alone is enough to stop them.

A second, stricter byte-format check against the pinned **owner-mirror** sample template found that 7/9 historical files use finite zeros outside the sample footprint and fail the official null/nodata-outside schema implemented by `scripts/validate_submission.py`; GEMSDOE30 and GEMSDOE33 use outside nodata and pass this local schema check. This is not a portal test and the owner mirror is not organizer-authenticated. Inside-footprint values for all nine are finite in `[0,1]`; the format failure is the outside-mask encoding, not the model's in-footprint range. Earlier audit code reported whole-array range/finiteness rather than this strict mask comparison; that defect is now corrected and tests cover it.

No candidate was placed, generated or promoted; scientific experiment count is zero. No previous TIF was used as a candidate; retrieval was solely for documented historical forensics.

## Why the reported H33 B2 result might be better

The pinned participant analysis attributes the reported 0.2778 to a sparse H19-5 descendant with near-catalogue thinning, and the listed H33 B2 raster contains 37,654 positive dots. Our local forensic comparison shows that every H33 B2 dot is within 3 px of the GEMSDOE24, 25, 27, 30 and 31 winner dots; H33-to-GEMSDOE28 coverage is 99.875%, to GEMSDOE33 99.984%, and to GEMSDOE36 100%. Conversely, the peer masks cover 86.72%–97.40% of H33 dots within 3 px. These are directed geometric overlaps, not scores.

Lower uncredited prediction mass can improve a precision/recall-style metric, because the official DTI penalizes false positives and false negatives asymmetrically (α=.2, β=.8), while the 300 m triangular kernel rewards nearby predictions. But aggressive thinning can also destroy recall. A plausible mechanism is therefore balancing dot budget, spatial coverage, and catalogue proximity; the audited shared geometry means the 0.2778 claim does not identify a unique geological signal or a causal B2 gain. Score-to-hash receipt and private truth are absent. There is no basis to guarantee a higher score, reverse-engineer hidden labels, or infer that matching past dot budgets generalizes. The sibling explicitly withdrew earlier hidden-truth inversion and score-ceiling calculations.

The prompt provides conflicting leader targets (0.3195 and 0.4413). Neither is a verified current
leaderboard result here. Do not optimize against either as a known current threshold. The source
snapshot's later leaderboard claim is also not independently confirmed in this checkout.

## Mutable peer-site status spot check — 26 October 2026

The nine current Pages sites were fetched for review. These are owner-maintained statements, not
organizer receipts; their holdout figures use different evaluators/folds and are not pooled here.
They demonstrate why the historical list is not a current promotion queue:

- [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) says its current research candidate is not approved; a later point-best does not inherit an upload slot.
- [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) says no eligible competition TIFF is available and its current research artifact failed gates.
- [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) has an H31-1 section labelled approved under its own selector, but that does not override this prompt's literal registry stop.
- [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) reports multiple current research-only/negative outcomes; historic sections differ in registry scope.
- [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) explicitly labels its current GDX-1 experiment negative and no new upload.
- [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) contains conflicting selector sections, including a purported approval and text that literal broad-registry uniqueness fails.
- [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) says no new file is authorized and describes 0.2778 as an owner report without a receipt binding score to hash.
- [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) contains several current research artifacts with negative/no-slot decisions.
- [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) labels current artifacts research-only and documents failures under a broader registry check.

Do not accept a peer site's “OK to submit” label as this project's selector decision. The exact pinned historical raster comparison above independently shows every supplied winner fails the 70% cross-winner dot-overlap stop. Current slot status remains **none**.

## High-scoring validation is separate from valid file format

A finite [0,1] single-band file on the template grid may pass format checks while performing poorly.
The exact uploaded bytes were not supplied, so the cause of the reported portal range error is unknown. A finite negative nodata sentinel or a NaN included in the portal's range check could cause it; changing outside-mask encoding may also interact with validation. The local validator verifies finite `[0,1]` values inside the sample footprint and null/nodata outside; it never clips. Follow the official sample/schema, retain the exact output hash, and treat portal acceptance as unverified until the actual portal receipt exists. A score estimate is unavailable until a compliant paired spatial holdout is run. Do not extrapolate leaderboard scores from historical reports or proxy measurements.

## Limitations and exact continuation

1. Identify the missing single-method lane before a parallel scientific run. The shortlist is not lane allocation.
2. Recover the canonical shared template and cached features. The fetched writer/evaluator import
   `gems32`; copying those two scripts alone is not an executable pipeline. No private evaluator was made.
3. The sibling data manifest exposes pinned GitHub mirror parts, including a roughly 419 MB numerical
   feature stack. This is a possible autonomous recovery route, **not a verified official download**.
   Small template/labels and nine historical rasters were recovered locally; feature stack and full
   registry were not. Raw data remain gitignored. Check organizer data-use rules/provenance before training.
4. The official DrivenData task and About pages, USGS GeoDAWN release page, EPSG record, and reference README were fetched through the research page tool on 2026-10-26. The official DrivenData data tab redirected to login; no authenticated session is available. The live leaderboard, account-specific receipt/quota, GDR page, NLR PDF, and Dropbox mirrors were not fetched. No official competition raster was downloaded.
5. Restore full-registry surfaces and dots, not only nine winners. A dense lattice may make the overlap
   rule extremely restrictive; report that conflict rather than weakening the gate.
6. Execute the preregistered canary/holdout comparison; record version, positive count, CI, hash, and
   complete registry comparisons. Only a separate selector may authorize a weekly slot after checking
   the current submission-page cap. No automatic contest submission is implemented or attempted.
7. Preserve the exact submitted hash and official submission receipt. Without them, use “unverified
   historical report,” not ORGANIZER-CONFIRMED. A research metric must be labelled HOLDOUT-DTI.

## Sources and trust boundaries

- Official organizer code actually retrieved: https://github.com/drivendataorg/gems-prize-reference-solution
  (`sources/gems-prize-reference-solution/README.md`). It explicitly supports CPU-only operation;
  GPU is advantageous, not an absolute prerequisite.
- Official task, feature list, DTI parameters, and submission schema: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ — fetched 2026-10-26; one-band float32 EPSG:32611, 100 m, same grid/bounds, predictions `[0,1]`, null/NaN outside, DTI α=.2/β=.8 and triangular support 300 m.
- Official About/data context: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/ — fetched 2026-10-26.
- Official competition data tab: https://www.drivendata.org/competitions/306/competition-doe-gems/data/ — fetched 2026-10-26; redirected to DrivenData login. No credentials or bypass used.
- Official leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ — not checked; current value unknown.
- Official USGS GeoDAWN data release: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and and DOI https://doi.org/10.5066/P93LGLVQ — fetched; describes magnetic/radiometric grids and GeoTIFF products, cites CC0 1.0; actual raster bytes/coverage not retrieved.
- EPSG:32611: https://epsg.io/32611 — fetched; UTM 11N / metre units. It does not replace checking sample-template dimensions/affine transform.
- GDR: https://gdr.openei.org/submissions/1391 — not fetched.
- Official format report PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf — not retrieved; no claims are attributed to it.
- Third-party corrected explanation: https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/research/why-02778-analysis-20261025.md
- Third-party pinned raster inventory: https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/evidence/focus_site_winner_overlap_20261026.json

All external scientific mechanisms in the shortlist are hypotheses, not literature-verified findings.
