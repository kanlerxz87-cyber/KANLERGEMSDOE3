# Nine-site review register

The following URLs are the nine requested project pages. They are useful for locating the owners' project histories, but are **not official competition score receipts**. The figures in [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) came from the user-provided historical list and are explicitly unverified. This review does not assert current page contents or current leaderboard rank. The distinct file path, byte hash, receipt, complete registry comparison, holdout metric and submitted note were not available in this checkout.

| Site | User-provided highest historical score claim | History item | Current audit status |
|---|---:|---|---|
| [24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | 0.2477 | H25-1 dotted H19-5 d1.5 | Owner claim only; bytes/receipt/novelty not inspected |
| [25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | 0.2600 | Dotted H19-5 d2.8 | Owner claim only; bytes/receipt/novelty not inspected |
| [27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | 0.2449 | Topographic gap closure | Owner claim only; bytes/receipt/novelty not inspected |
| [28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | 0.2710 | H36-1 rung30 blind r1 | Owner claim only; bytes/receipt/novelty not inspected |
| [30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | 0.2600 | D28 Poisson 300 m off-catalogue | Owner claim only; bytes/receipt/novelty not inspected |
| [31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | 0.2708 | H27-4 solo D28 | Owner claim only; bytes/receipt/novelty not inspected |
| [32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | 0.2778 | H33/H33-2 B2 | Owner claim only; bytes/receipt/novelty not inspected |
| [33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | 0.2632 | Analog tip/stepover r30 | Owner claim only; bytes/receipt/novelty not inspected |
| [36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | 0.2750 | Anderson geothermal PINN | Owner claim only; bytes/receipt/novelty not inspected |

## Interpretation limits

- The scores are not labelled `HOLDOUT-DTI` because no controlled holdout evaluator, withheld-positive count, or 95% confidence interval accompanied them in this checkout.
- They are not labelled `ORGANIZER-CONFIRMED` because no submission-page receipt was available.
- Comparisons between related submissions can be informative only if data splits, evaluator version, file bytes, probability calibration, and scoring protocol match. Names like “blind,” “PINN,” “zeros,” or “unique” do not prove those properties.
- The input prompt also lists other leader figures (0.3195 and 0.4413); these conflict and were not verified. No “current leader” assertion is made.
- Pixel-level uniqueness is **unknown for every row**. Do not state that a submission is unique based only on names, claims, site separation, or hash difference.

## What would make this register decision-grade

For every artifact, capture immutable file URL and SHA-256; organizer receipt binding the score to that file; exact evaluator and test version; feature/surface lineage; full pairwise surface correlation and final-dot 3-pixel overlap against every registry raster; and the same spatial hide-and-recover DTI evaluation. Until then the table is a research index, not an upload recommendation.
