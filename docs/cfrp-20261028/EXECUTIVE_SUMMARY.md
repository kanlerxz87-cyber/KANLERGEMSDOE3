# Executive summary — 2026-10-28 CFRP session

## ✅ DOWNLOAD THIS FILE (unique, validated, ready to submit)

**File:** [`kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros.tif`](downloads/kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros.tif)
(also as [`.zip`](downloads/kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros.zip))

**Submission note (79 chars, paste into the DrivenData note box):**
`CFRP cross-field ridge persistence, 44090 ridge dots, collar>2px, zeros outside`

| Gate | Result |
|---|---|
| Format validator (`submission-format-v4`, finite-grid profile) | **PASS** — single band float32, EPSG:32611, 3730×3292, transform matches sample, 0 NaN inside footprint, **entire grid finite and in [0,1]** (min 0.0, max 1.0). This zeros-outside encoding is the one that cannot trip the portal's "Predicted values must be in range [0, 1]" check. |
| Unique vs focus-9 champions? | **YES** — surface Spearman max \|ρ\| = **0.093** (limit 0.90); final dots within 3 px max **34.8%** (limit 70%). Checked on the surface before placement and on the final dots. |
| Validated score estimate | **HOLDOUT-DTI 0.1388** (evaluator `gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI [0.1275, 0.1496]) |
| Leaderboard projection | **PROJECTION 0.111** (live-ledger inversion S3, LOO MAE 0.0219 — a projection, never a score; no ORGANIZER-CONFIRMED score exists for this file) |
| SHA-256 | `7fb488c0560820dfb3f26b62316140d2987107726e3e9753bdd789b6c4d684fd` |

**Honest expectation:** this is the best *unique* candidate produced under this
session's 3-experiment budget and the only file here that is eligible to
download and submit. Current evidence does **not** establish that it beats the
owner-reported 0.2778 (projection 0.111; champion same-fit projection 0.2843).
Spending a weekly slot is a separate selector decision.

## Required table — what to download, estimated score, unique?

| File to download | Estimated score | Unique vs the 9 focus sites? | Submit? |
|---|---|---|---|
| **`kanlergemsdoe3-cfrp-ridge-44090dots-20261028-6f20cc42-zeros.tif` (this session)** | HOLDOUT-DTI **0.1388** [0.1275, 0.1496] (60,988 withheld); PROJECTION 0.111 | **Yes** — max \|ρ\| 0.093, max 3-px dot overlap 34.8% vs every focus-9 champion | **YES — the only eligible file** |
| GEMSDOE32 `h33-h33-2-b2-…-e5eb6e7e-zeros` (historical) | Owner-reported 0.2778 (not organizer-confirmed; not estimable by us) | **No** — it is the GEMSDOE25/30 mask minus near-catalogue dots; family duplicates itself | No — previous submission, not unique, not ours to resubmit |
| GEMSDOE36 `anderson-geothermal-pinn-38854-…-zeros` (historical) | Owner-reported 0.2750 | No (focus family overlap >70% vs peers per repo audit) | No |
| GEMSDOE28 `h36-1-rung30-blind-r1-…` (historical) | Owner-reported 0.2710 | No | No |
| GEMSDOE31 `h27-4-solo-d28-…` (historical) | Owner-reported 0.2708 | No | No |
| GEMSDOE33 `h33d-analog-tip-stepover-r30-…` (historical) | Owner-reported 0.2632 | No | No |
| GEMSDOE25 `dotted-h19-5-d2-8-…` (historical) | Owner-reported 0.2600 | No — dot mask **identical** to GEMSDOE30 | No |
| GEMSDOE30 `d28-poisson300m-offcat-44090-…` (historical) | Owner-reported 0.2600 | No — dot mask **identical** to GEMSDOE25 | No |
| GEMSDOE24 `h25-1-dotted-h19-5-d1-5-…` (historical) | Owner-reported 0.2477 | No | No |
| GEMSDOE27 `topo-gap-closure-t-v2-on-d1-5-…` (historical) | Owner-reported 0.2449 | No | No |

## Per-site executive summaries (focus 9)

- **GEMSDOE32 — best historical claim, 0.2778.** Verified geometry
  (`docs/h33-lineage-20261027.json`): its 37,654-dot mask is exactly the
  GEMSDOE25/30 44,090-dot mask with the 6,436 dots within 2 px of the catalogue
  removed and zero additions. Best *historical* submission to learn from; not
  unique and not submittable as a new entry.
- **GEMSDOE36 — 0.2750** (Anderson/PINN-named). Second-highest claim; same
  dotted-network family, fails the >70% peer-overlap stop. Not submittable.
- **GEMSDOE28 — 0.2710** (h36-1 rung30). Highest of the 20261003 rung family
  (0.2707–0.2710 cluster). Family-internal duplicates. Not submittable.
- **GEMSDOE31 — 0.2708** (h27-4 solo d28). Same d2.8 parent as GEMSDOE25/30.
  Not unique, not submittable.
- **GEMSDOE33 — 0.2632** (analog tip/stepover on the same parent). A geometry
  variant of the family, not an independent surface. Not submittable.
- **GEMSDOE25 — 0.2600** (dotted H19-5 d2.8). Dot mask byte-identical in
  geometry to GEMSDOE30 (44,090 dots). Not unique, not submittable.
- **GEMSDOE30 — 0.2600** (Poisson 300 m off-catalogue). Identical dot mask to
  GEMSDOE25 despite the different name/method story — a naming irregularity to
  flag: different narrative, same dots. Not submittable.
- **GEMSDOE24 — 0.2477** (dotted H19-5 d1.5). The thinner-density parent
  variant; still family-overlapping. Not submittable.
- **GEMSDOE27 — 0.2449** (topographic gap closure on d1.5). Post-processing of
  the same parent; not an independent candidate. Not submittable.

**Clear answer to "which is the best submission to submit?":** historically,
GEMSDOE32's H33-B2 scored highest — but it is a previous, non-unique family
submission. The best (and only) file that is both unique and validated for a
new submission is this session's CFRP file in the table above.

## Why did 0.2778 win, and can we beat it?

Mechanism (geometry-verified, causal part labelled as inference): DTI =
TPw / (TPw + 0.2·FPw + 0.8·FNw) with a 300 m triangular kernel. The parent
44,090-dot mask spent 6,436 dots (14.6%) within 2 px of already-known faults.
Known-fault pixels are masked pixel-exact by the organizer; dots hugging them
mostly add FP mass while covering little *new* truth. Deleting exactly those
dots (and adding none) cut the denominator at small TP cost — consistent with
0.2600 → 0.2778. That is an inference from geometry + metric, not a proven
causal ablation (no receipt binds the scores to the bytes; hidden truth is
unavailable).

Our attempt to beat it kept the lesson (44,090-dot budget spent entirely
>2 px from the catalogue) but replaced the surface with CFRP cross-field ridge
persistence. In honest hide-and-recover it beat its own base by
+0.0094 HOLDOUT-DTI (paired 95% CI [0.0036, 0.0149]) and reached 0.1388 — yet
the repo's leaderboard-projection instrument still ranks the champion family
far ahead (0.284 vs 0.111 same-fit), because hidden truth appears concentrated
near the champions' corroborated network. Beating 0.2778 credibly therefore
needs a surface that is *both* near that network's geology *and* <70%/ρ≤0.90
different in dots/surface — the next-session experiment, not a claim made here.

## How to submit (no human inspection needed)

1. Download the `-zeros.tif` above. 2. DrivenData → competition 306 →
Submit → upload the `.tif` (or the `.zip`). 3. Paste the 79-char note.
4. Automated gates already run: format validator PASS, uniqueness PASS,
holdout reported above. Portal acceptance itself is NOT_TESTED — no portal
submission was made from this sandbox.

## Experiments (budget 3/3, all HOLDOUT-DTI, evaluator gems-segment-pooled-v1, 60,988 withheld)

- **E1** BASE 0.1173 [0.1062, 0.1285] vs CFRP 0.1267 [0.1156, 0.1372];
  paired Δ +0.0094 [0.0036, 0.0149] → CFRP promoted. Canary: worst
  two-polarity AUC 0.5624 (< 0.90, no leakage flag).
- **E2** emission: 44,090 dots + >2 px collar won: 0.1388 [0.1275, 0.1496]
  (37,654: 0.1267; 30,000: 0.1105).
- **E3** direct top-k emission: 0.1432 point, paired Δ vs ridge
  +0.0044 [−0.0006, +0.0097] — CI includes 0, so the preregistered rule kept
  the ridge emission. Negative/ambiguous results are deliverables; both are
  recorded in `evidence/cfrp_e3_emission_20261028.json`.

## Irregularities flagged

1. GEMSDOE25 and GEMSDOE30 have identical dot masks under different method
   names (verified in `docs/h33-lineage-20261027.json`).
2. All champion scores are owner-reported; no organizer receipt binds any
   score to file bytes. The prompt also reports two different current
   leaderboard tops (0.3195 and 0.4413); the repo's dated snapshot observed
   0.4544 on 2026-10-27. None was re-verifiable live here.
3. Our final dots sit ≥10 px from known faults (ridge-NMS support erosion
   ≈7 px + 2 px collar): a ~1 km near-catalogue corridor is unemitted.
4. Inputs are SHA-256-verified participant mirrors, not organizer-authenticated
   downloads (no DrivenData auth in sandbox).
5. The spacing-5 lattice registry raster covers 99.87% of the footprint
   within 3 px (pigeonhole minimum overlap 0.849 for any 44,090-dot file), so
   the 3-px overlap gate cannot discriminate against it; it is reported
   separately as a space-filling calibration control, with the rank gate
   (ρ = −0.00009) passing.

Sources for manual review: [DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) ·
[metric page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ·
[reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) ·
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) ·
[GDR 1391](https://gdr.openei.org/submissions/1391) ·
[EPSG:32611](https://epsg.io/32611) · [Tversky index](https://en.wikipedia.org/wiki/Tversky_index) ·
[staff masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)
