# K3-H1 lane report — antislope-scarp grain traces (26 Oct 2026)

**Bottom line.** This lane produced one new GeoTIFF that is format-valid and measured as protocol-unique against 433 restored registry rasters. It is **not expected to beat 0.2778**: its live-ledger PROJECTION is 0.2521 vs 0.2843 for the champion under the same model, and its HOLDOUT-DTI does not beat the best control. Verdict: **negative**. You can download it and it will not trigger the portal's range error. Do not spend a weekly slot on it if your goal is a higher score.

| | |
|---|---|
| File | [`kanler3-k3h1-asgt-hybrid-48559-20261026T2226Z-7ecb7b69-zeros.tif`](downloads/kanler3-k3h1-asgt-hybrid-48559-20261026T2226Z-7ecb7b69-zeros.tif) (172,965 bytes) · [ZIP](downloads/kanler3-k3h1-asgt-hybrid-48559-20261026T2226Z-7ecb7b69-zeros.zip) |
| SHA-256 | `4a5b0b480be26df52f77b735487cbe5af192262587237b6514d520dc2698b01f` |
| Submission name | `kanler3-k3h1-asgt-hybrid-48559-7ecb7b69` |
| Note (103 chars) | `K3-H1 antislope-scarp lidar dots + ASGT-ranked H19-5 core; unique<=69.5%; PROJECTION 0.252, not >0.2778` |
| Format | PASS: all 15 shared-validator checks (`vendor/gems57/validate.py`, byte-identical to the pinned shared template) plus the official-spec check (`scripts/portal_check.py`). float32, one band, EPSG:32611, sample transform, all pixels finite, values exactly 0/1, zeros outside the footprint, no nodata tag, 0 dots on mapped faults |
| Uniqueness | PASS vs the 427 non-space-filling rasters: max forward overlap 0.695 (limit 0.70); max Spearman 0.432 on final dots and 0.146 on the pre-placement surface (limit 0.90); byte- and pixel-unique. **Literal rule: BLOCKED**, as for every non-empty file, by 6 space-filling dot rasters and by the full-footprint GEMSDOE48 witness (see §4) |
| Expected score | PROJECTION 0.2521 (live-ledger inversion; leave-one-out MAE 0.022). This is not a score. The champion projects at 0.2843 under the same model, and its OWNER-REPORT is 0.2778 |
| HOLDOUT-DTI | 0.0909, 95% CI [0.0798, 0.1018], `gems57-pooled-hide-v2`, 11,321 withheld positives. Best control C1: 0.0961 [0.0836, 0.1081]. Paired Δ −0.0052 [−0.0101, +0.0003] |
| Recommended for a slot | **No** |

Machine-readable: [K3-H1 run card](k3h1-run-card.json).

## 1. Why GEMSDOE32 `h33-h33-2-b2` scored 0.2778

Scores here are OWNER-REPORT values from GEMSDOE32's live ledger. They are not organizer receipts.

**What the file is (verified on bytes).** H33-B2 is the 44,090-dot "D2.8" file (the H19-5 network dotted at 2.8 px spacing) with all 6,436 dots at or within 2 px of a mapped fault removed. That leaves 37,654 dots, every one of them on an H19-5 network pixel. GEMSDOE19 built H19-5 (121,131 px) as the ridge centreline of a fused multi-physics score: power-law tip/relay stress, GDR thermal/geochemistry, 1 m/10 m DEM openness, and gravity/magnetic worms. Its "solid" version scored only 0.1922. The ladder H19-5 0.1922 → D1.5 0.2477 → D2.8 0.2600 → B1 0.2708 → B2 0.2778 is pure **subtraction**: no new geology after H19-5.

**The metric explains the ladder.** With binary predictions, the official distance-weighted Tversky index (α = 0.2, β = 0.8, 300 m triangular kernel k(d) = max(1 − d/300 m, 0)) reduces to

DTI = TP / (0.2·TP + 0.2·FP + 0.8·|G|),

where TP = Σ over truth pixels of the best kernel credit from any dot, and FP = Σ over dots of (1 − that dot's best credit). Adding one dot with expected credit k changes TP by +k and FP by +(1 − k). It therefore improves the score **iff k > 0.2 × DTI**, which is 0.056 at DTI = 0.2778. Every step of the ladder removes dots whose expected credit is below that break-even:

1. **Thinning (solid → 2.8 px dots).** Along a line, a truth pixel's credit falls only slowly with dot spacing s (about 1 − s/12 for s ≤ 6 px with a 3-px kernel). FP mass, by contrast, falls as 1/s. For the solid 121k-pixel network the FP term (0.2 × more than 100k uncredited pixels) outweighed the miss term (0.8 × about 18k truth pixels), so thinning raised DTI from 0.19 to 0.26. For the 37,654-dot champion the balance has flipped (0.2 × 35.1k ≈ 7.0k vs 0.8 × 18.0k ≈ 14.4k), which is why further thinning stops paying.
2. **Catalogue-proximal depletion (B1/B2).** Mapped faults are masked pixel-exactly, without a buffer ([DrivenData staff, forum 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)). So the hidden truth is *new* faults, and they are rare right next to mapped ones: in the live-ledger inversion, the fitted truth density 1–2 px from mapped faults is 1.2% of its value more than 30 px away; it is 4.5% at 2.2–3 px and 14% at 3.2–5 px, then **peaks at 5–10 px (1.10×)**. New faults sit near, but not adjacent to, mapped ones. Dots ≤2 px from the catalogue therefore earn almost no credit but still pay FP, so deleting them raises DTI. (The same fit's distance-to-H19-5 factors contain non-physical spikes, e.g. 1,398× at 1 px; this lane never optimised against them.)

**The nine focus winners confirm it quantitatively** (measured: [focus9 family evidence](data/focus9_family.json)). All nine are the same family: 97–100% of each file's scored dots lie on H19-5 pixels, and each file has ≥97.6% of its dots within 3 px of another winner. The **share of dots within 2 px of mapped faults** orders their scores almost perfectly:

| Site | Best scored file | Dots | On H19-5 | Dots ≤2 px from catalogue | OWNER-REPORT |
|---|---|---:|---:|---:|---:|
| GEMSDOE32 | h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros | 37,654 | 100% | 0.0% | 0.2778 |
| GEMSDOE36 | anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros | 38,854 | 96.9% | 0.0% | 0.2750 |
| GEMSDOE28 | h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan | 37,660 | 100% | 6.25% | 0.2710 |
| GEMSDOE31 | h27-4-solo-d28-20261004-8acb75e1-nan | 40,199 | 100% | 6.3% | 0.2708 |
| GEMSDOE33 | h33d-analog-tip-stepover-r30-20261004-cb490425926e | 41,865 | 99.7% | 9.3% | 0.2632 |
| GEMSDOE25 | dotted-h19-5-d2-8-20261002-e56ea318af89-nan | 44,090 | 100% | 14.6% | 0.2600 |
| GEMSDOE30 | d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca | 44,090 | 100% | 14.6% | 0.2600 |
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan | 60,069 | 100% | 14.6% | 0.2477 |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan | 61,328 | 98.0% | 14.5% | 0.2449 |

**Executive summary per site: which file is best to submit.** Every file below has already been submitted and scored (OWNER-REPORT). Re-uploading identical bytes cannot raise its score and only spends a weekly slot. All nine are near-duplicates of one another (≥97.6% overlap), so none is a *unique* new submission.

- **GEMSDOE32: `h33-h33-2-b2-…-zeros` (0.2778). Best of all nine.** Keep it as your final selection.
- **GEMSDOE36:** `anderson-geothermal-pinn-38854-…-zeros` (0.2750). Best at this site; 97% the same dots as the champion's family, 0.0028 lower.
- **GEMSDOE28:** `h36-1-rung30-blind-r1-…-nan` (0.2710). Best at this site; still keeps 6.25% catalogue-hugging dots.
- **GEMSDOE31:** `h27-4-solo-d28-…-nan` (0.2708). Best at this site; same pattern as GEMSDOE28. (Its sibling `csdu-stepover-…-nan` file is the one registry file with NaN inside the footprint; do not upload it.)
- **GEMSDOE33:** `h33d-analog-tip-stepover-r30-…` (0.2632). Best at this site.
- **GEMSDOE25:** `dotted-h19-5-d2-8-…-nan` (0.2600). Best at this site; the D2.8 parent of the champion.
- **GEMSDOE30:** `d28-poisson300m-offcat-44090-…` (0.2600). Best at this site, but it is a relabelled copy of GEMSDOE25's D2.8.
- **GEMSDOE24:** `h25-1-dotted-h19-5-d1-5-…-nan` (0.2477). Best at this site; too dense (1.5 px spacing).
- **GEMSDOE27:** `topo-gap-closure-t-v2-on-d1-5-…-nan` (0.2449). Best at this site; gap-closure dots fell below break-even.
- **New (this lane):** `kanler3-k3h1-asgt-hybrid-48559-…-zeros`. Unique and format-safe, but PROJECTION 0.252, so it is **not** a better choice than the champion.

GEMSDOE30's file has **exactly the same 44,090 dots** as GEMSDOE25's D2.8 file. Its name even ends in `91eae1ca`, the SHA prefix of the D2.8 file, and both scored 0.2600. The two denser files (60k dots, 1.5 px spacing) score lowest, as the break-even rule predicts.

**What it would take to beat it.** Under the live-ledger inversion (§3), the champion's dots are near-optimal *for the information in H19-5*. Projected numbers: TP ≈ 6.46k, FP ≈ 35.1k, |G| ≈ 18.0k, giving 0.2843 (the live value is 0.2778, so the model reads 0.0065 high for this file). Holding FP and |G| fixed, reaching 0.3195 needs about 16% more credited truth than the live 0.2778, and the public leader's 0.4437 needs about 66% more. That cannot come from re-thinning the same network. It needs a **new information source** whose extra dots earn more than 0.056 credit each. The protocol adds a constraint: a unique file may keep at most 70% of its dots near any one registry raster. Every unique design built so far — GEMSDOE32's H47 (0.240–0.248) and this lane's E3 (0.252) — projects about 0.03 below the champion. The uniqueness rule itself costs about 0.03 DTI unless the novel 30% is unusually good.

## 2. Hypotheses (ranked before any experiment; [pre-registration](https://github.com/kanlerxz87-cyber/KANLERGEMSDOE3/blob/main/research/preregistration-20261026.md), written 22:18:36Z, sha256 in the run card)

| Rank | Hypothesis | Layers | Physical signature | Why it might catch *uncatalogued* faults | Cost |
|---|---|---|---|---|---|
| 1 | **K3-H1 antislope-scarp grain traces (ASGT)** — tested | 1 m lidar scarp product (USGS 3DEP-derived; GEMSDOE24), visible-catalogue grain | uphill-facing step, coherent ≥300 m, parallel to local fault grain | uphill-facing scarps are almost uniquely tectonic; small lidar-only scarps are what pre-lidar compilations miss | low |
| 2 | K3-H2 hanging-wall antithetic belt | ASGT + dip side of mapped range fronts | antislope scarps 0.5–3 km into the hanging wall | antithetic faults are rarely compiled at 1:250k | medium |
| 3 | K3-H3 facing persistence | lidar facing bands + strike | facing side constant along strike for km | removes channel-bank mimics | medium |
| 4 | K3-H4 strain-gated piedmont scarps | geodetic shear/dilatation (INGENIOUS), slope | scarps in low-slope piedmonts inside high strain-rate belts | young scarps survive where deformation is active | low |
| 5 | K3-H5 radiometric offset edges | GeoDAWN K/Th/U | sharp linear K/Th contrasts cutting lithology | bedrock faults without scarps | medium |

Non-fault mimics handled by ASGT: landslide/sackung headscarps (relief veto), channel banks (cross-slope dominance), roads and berms (grain and coherence down-weighting), and lake shorelines (downhill-facing, so excluded).

## 3. Experiments (budget: 3 experiments / 2 h — used 3, in about 6 minutes wall-clock)

Every holdout number below uses the shared `gems57-pooled-hide-v2` evaluator, unchanged. Its setup:

- 20% of whole fault components withheld per label-blind quadrant, 3-px collar, 12-px fold buffer;
- catalogue features derived from visible faults only, with visible faults masked pixel-exactly;
- pooled DTI (α = 0.2, β = 0.8, 300 m kernel), 11,321 withheld positives;
- paired spatial-cluster bootstrap (157 clusters, 1,000 draws).

Projections use GEMSDOE32's archived live-ledger inversion (S3 design, 111 scored rasters; leave-one-out MAE 0.0219, q90 error 0.054), reused unchanged.

| Exp. | Question | Result | Decision |
|---|---|---|---|
| E1 | Does the ASGT mechanism recover withheld faults? | HOLDOUT-DTI ASGT 0.0922 [0.0788, 0.1042] vs upface-only ablation 0.0499 [0.0386, 0.0628]: Δ +0.0423 [+0.0330, +0.0522]. Vs C1 (champion recipe on the same folds) 0.0961: Δ −0.0039 [−0.0160, +0.0094] | mechanism **supported**; ties the incumbent on catalogue-type faults |
| E2 | Does a unique *pure* ASGT file project competitively? | 16 files (30–60k dots, 3/5 px exclusion, capped/uncapped): PROJECTION 0.066–0.118 vs champion 0.2843. ASGT dots sit about 70% off the H19-5 network, where the ledger puts little hidden truth | **no** |
| E3 | ASGT-ranked H19-5 core (≤69.5%) + ASGT novel dots (≥30.5%) | PROJECTION 0.2521 vs 0.2843. HOLDOUT-DTI 0.0909 [0.0798, 0.1018] vs C1 0.0961: Δ −0.0052 [−0.0101, +0.0003] | **negative** |

Leakage canary: max single-feature AUC 0.755 (distance to visible faults) in E1, and 0.634 for E3's added features. PASS (< 0.90). Deviation IR-K3-E3-DEV-01: E3 changed the core *selection rule*, not only the budget, because E2 showed ASGT dots fill only 28–35% of the network buffer. The verdict rules were unchanged. Caveat IR-K3-E3-LEAK-01: E3's core and control C1 both inherit H19-5, which was built with the full catalogue. Their absolute holdout values are therefore leak-advantaged, and only the paired difference is interpretable.

**Interpretation (contrarian but grounded).** Antislope scarps are a real fault signal: they ranked withheld *catalogue* faults as well as the champion recipe. But the live ledger says the hidden *new* faults sit near the H19-5 network, which ASGT mostly avoids. The expert-added faults are evidently not dominated by small lidar scarps far from existing structure. The next lane should test what predicts **where along the H19-5 network** new faults lie (credit > 0.056 per dot), rather than new places to look.

## 4. Uniqueness — measured, with the policy conflict stated plainly

Recomputed from the bytes of 433 comparable registry rasters (focus-site manifests + GEMSDOE32's scored live ledger; SHA-256 verified). Evidence: [uniqueness evidence](data/k3h1-uniqueness-summary.json).

- **Against every one of the 9 focus winners:** forward overlap 0.694–0.695 (cap enforced during placement), Spearman 0.365–0.399, Jaccard 0.23–0.25. Formally unique, but this is a *hybrid*: 69.5% of its dots re-use the H19-5 network (with our own selection and placement), and 30.5% are new antislope-scarp dots.
- **Literal rule:** six registry rasters are space-filling dot patterns whose 3-px buffers cover 53–99.9% of the footprint (5-px lattice; GEMSDOE3 pindrop ×2; GEMSDOE22, 67, 77). Our dots overlap them 71–99.9%, while Spearman is ≤ 0.164. Main's [registry-saturation certificate](data/registry_saturation.json) also pins a continuous GEMSDOE48 raster that is positive on all 5,167,373 footprint cells. Under the literal "any positive cell is a dot" rule, **no non-empty file can ever be unique**. That is a protocol contradiction, not a property of this file. Exempting information-free space-filling rasters is a decision for you (the protocol owner); this lane reports both readings and does not decide it silently.

## 5. The portal error "Predicted values must be in range [0, 1]"

The organizer's validator text is not public. The rejected bytes and receipt are not in this repo, so the exact cause of *your* error cannot be proven. What is measured:

- Among the 433 restored registry files, **no file** has finite values outside [0, 1], and **exactly one** has NaN *inside* the scored footprint: GEMSDOE31 `gemsdoe31-csdu-stepover-8cf9dc27-nan.tif`, with 2,610,312 NaN pixels. NaN fails every `0 ≤ p ≤ 1` comparison, so it is the only registry file that would plausibly produce this message.
- Other causes `scripts/portal_check.py` detects: nodata sentinels written as values (−9999, −3.4e38), float rounding just above 1.0, negative logits, percentages 0–100, and ±inf.
- **Fix:** write float32, all pixels finite, probabilities clipped to [0, 1] *before* writing, zeros (or NaN) outside the footprint only, and no nodata sentinel. The K3-H1 file follows the stricter all-finite policy used by the 0.2778 "-zeros" champion.

Check any file: `python scripts/portal_check.py your.tif` prints `ok_to_upload` and the likely cause of a range error.

**Two local validators disagree about outside-footprint pixels, and the portal accepts both.** The shared template writer/validator (`vendor/gems57`, which the protocol names as the shared tool) *requires* zeros outside the footprint and no NaN anywhere. This repo's older conservative checker `scripts/validate_submission.py` (submission-format-v2) *expects* null/NaN there, following the official wording "null/NaN outside the bounds", and therefore reports `ok: false` for this file. The live ledger shows the portal scored both encodings: the 0.2778 champion was submitted as its `-zeros` variant, and D1.5 (0.2477) as its `-nan` variant. The K3-H1 file uses exactly the champion's accepted `-zeros` encoding. `scripts/portal_check.py` encodes the spec plus that empirical acceptance: finite values in [0, 1] or NaN outside the footprint, and nothing invalid anywhere.

## 6. Irregularities

- The prompt's lane paragraph is missing (IR-K3-LANE-01); this lane was self-assigned and pre-registered.
- The prompt quotes 0.4413 and 0.3195 as leaderboard highs. On 26 Oct 2026 the official leaderboard showed 0.4437 at #1, and 0.3195 matched no visible top-50 entry. 0.2778 is below the visible top-50 cutoff (0.2826). All of these are dated snapshots.
- GEMSDOE30's 0.2600 file is a relabelled copy of GEMSDOE25's D2.8 dots (above).
- `sample_submission.tif` comes from a participant mirror, SHA-verified against that mirror. The official data page requires login, so the organizer's bytes were not compared.
- The GitHub API token was unavailable in this sandbox; plain git transport worked.

## 7. Remaining work and limitations

1. **Decide the space-filling/continuous-raster policy** (§4). Until then, the literal rule blocks every candidate, including the K3-H1 file.
2. The final selection should remain the scored 0.2778 champion unless a candidate beats it on *both* the paired holdout and the same-fit projection. Per the [Official Rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) §3.4–3.6, one final submission counts for both prize rounds, and it must be chosen without knowledge of private scores.
3. The registry covers 433 rasters from the user's sites. Other teams' files are unknowable.
4. The projection model is fitted to one family of files. It can rank, but it cannot certify gains for unseen designs: its leave-one-out error, q90 0.054, exceeds the 0.03 gap.
5. The rules require finalists to submit reproducible code, and to **disclose generative-AI use** in the narrative (§3.2). This work was produced with an AI agent.
6. Next lane suggestion: an on-network ranking signal (where along H19-5 new faults lie), tested with the same paired holdout + projection gates.

## Sources

Official sources, fetched 26 Oct 2026:

- [Problem description & metric (page 967)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [About (page 968)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/): GeoDAWN magnetics/radiometrics, 3DEP lidar
- [GEMS Prize Official Rules, NLR, Sept 2026](https://docs.nlr.gov/docs/fy26osti/96647.pdf): 3 submissions/week; one final submission for both rounds; labels from the USGS Qfault database plus new NLR/USGS expert faults; code reproducibility; AI disclosure
- [INGENIOUS Great Basin Regional Dataset (GDR 1391, CC-BY-4.0)](https://gdr.openei.org/submissions/1391): Quaternary faults v1/v2, geodetic shear/dilation, heat flow, MT conductance, gravity/magnetics, slip/dilation tendency
- [INGENIOUS project (GBCGE)](https://gbcge.org/current-projects/ingenious/): DOE GTO award DE-EE0009254, 2021–2025, play-fairway based
- [USGS GeoDAWN data release, DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- Forum: [11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) (pixel-exact known-fault mask)
- [Live leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

Participant sources (SHA-pinned; not organizer receipts):

- buffedlizard55-lab/GEMSDOE32 @ `400b60d4` (live ledger, LLI fit, shared tools)
- GEMSDOE24 @ `07345ea0` (lidar scarp product)
- the GEMSDOE data mirror @ `c0c06ac8`
- 57GEMSDOE @ `822a0ce5` (shared template; byte-identical to `vendor/gems57`)
