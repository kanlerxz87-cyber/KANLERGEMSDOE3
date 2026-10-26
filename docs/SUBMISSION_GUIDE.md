# Submission and “[0, 1]” error guide

**DO NOT SUBMIT.** No approved candidate file was created. See the current
[executive HTML guide](executive-summary.html) and [run card](../evidence/run-card.json).

The exact cause of the prior range error is unknown without the rejected file and portal receipt.
Inspect the saved file for NaN/Inf, a nodata sentinel, values below 0 or above 1, wrong bands, and
metadata drift. Use one float32 band on the official sample CRS/shape/transform, finite [0,1] values
inside the footprint, and verify the bytes after reopening. The official sample/specification describes
null/NaN outside the footprint. The shared writer defaults to zero outside, but the separate strict
template-mask validator rejects those valid outside pixels; this conflict needs a central template fix
or organizer clarification before use. Do not assume either encoding explains the prior rejection,
or silently clip invalid predictions.

Before writing a submission, require a scientifically sound same-fold best-incumbent improvement,
full registry novelty, trusted/eligible data and code rights, and the unchanged shared writer. A
saved-file format pass is not a scientific pass. Only a separate selector may authorize an upload
after checking the account-specific cap. If authorized, submit the exact hash-verified file with its
≤140-character run-card note and preserve the organizer submission-page receipt. None of those
selector/receipt steps has happened here.
