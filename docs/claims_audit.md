# Historical claim audit

The requested values are **USER/OWNER-REPORTED, UNVERIFIED**, not
ORGANIZER-CONFIRMED submission scores. The pinned
[GEMSDOE32 portfolio](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/07806249f4ed3efe70b4fbf866183c32392b7853/docs/index.html)
repeats the nine named filename/value pairs as owner reports; it is a secondary
community source, not a file-specific receipt and not an exhaustive review of
all submissions. The [nine-site TIFF inventory](../config/focus_anchors.json)
pins the precise bytes we audited. The [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
contains rank/participant/score but no mapping to those files.

| Site / reported value | Assessment |
|---|---|
| GEMSDOE24 / 0.2477 | Listed in the portfolio, no inspected receipt. |
| GEMSDOE25 / 0.2600 | A [peer irregularity record](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/776bf4668a8c10631908c9bba9443a8f11ce5036/registry/irregularities.json) says an owner mirror marked D2.8 unscored. The exact score-to-file link remains unresolved. |
| GEMSDOE27 / 0.2449 | Listed in the portfolio, no inspected receipt. |
| GEMSDOE28 / 0.2710 | An [earlier H36-1 irregularity record](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/2c839d10f57ec9b074829e93c84bc39935f52896/registry/irregularities.json) calls its initial b531dae0a36f note unscored/not slot-approved. Later submission timing and score-to-file identity are not established. |
| GEMSDOE30 / 0.2600 | Listed in the portfolio, no inspected receipt. Its support matches the selected GEMSDOE25 anchor within the footprint; this does not prove byte-identical files or score attribution. |
| GEMSDOE31 / 0.2708 | A [peer irregularity record](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/776bf4668a8c10631908c9bba9443a8f11ce5036/registry/irregularities.json) cites an unscored GEMSDOE28 H27-4 with the same experiment-name suffix but says byte identity was not proven. Attribution remains unresolved. |
| GEMSDOE32 / 0.2778 | Repeated as owner-reported; the [submission manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/07806249f4ed3efe70b4fbf866183c32392b7853/docs/downloads/submissions_manifest.json) has `receipt: null` for the B2 reference. That does not prove no score exists. |
| GEMSDOE33 / 0.2632 | Listed in the portfolio, no inspected receipt. |
| GEMSDOE36 / 0.2750 | Listed in the portfolio, no inspected receipt. |

Several peer dashboards also publish **projections** or interpret uniqueness
with relaxed rules. Neither is an organizer score or an authorization under the
literal shared positive-support gate. All historical TIFFs in this audit are
research references, not candidates to resubmit.
