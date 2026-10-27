document.addEventListener('DOMContentLoaded', () => {
  const inject = document.getElementById('candidate-inject');
  if (!inject) return;
  fetch('evidence/candidate_poisson_20261027.json').then(r=>r.json()).then(cand=>{
    const zerosSha = cand.raster_sha256.zeros;
    const nanSha = cand.raster_sha256.nan;
    const zerosFile = cand.download.zeros_tif;
    const nanFile = cand.download.nan_tif;
    const name = cand.submission_name;
    // Replace hero if exists
    const heroCard = document.querySelector('aside.download-card');
    if (heroCard && heroCard.textContent.includes('No eligible TIFF yet')) {
      heroCard.style.border = '2px solid #2e7d32';
      heroCard.innerHTML = `
        <p class="eyebrow">Your competition file — NEW RESEARCH CANDIDATE</p>
        <h2>✅ Format-valid TIFF ready (research only)</h2>
        <p>Range [0,1] validated · EPSG:32611 · 37,654 off-catalogue dots · UNIQUE vs 9 focus sites (16.3% &lt;70%). <strong>Lattice block → DO NOT SUBMIT as winning entry.</strong></p>
        <a class="link-button" href="${zerosFile}" download style="background:#2e7d32;color:white;display:block;text-align:center;padding:0.8em;margin:0.5em 0">⬇ Download zeros.tif (776KB)<br><small>SHA ${zerosSha.slice(0,8)}… · finite-grid PASS</small></a>
        <a class="link-button" href="${nanFile}" download style="display:block;text-align:center;padding:0.6em;margin:0.5em 0;border:1px solid #666">⬇ Download nan.tif variant (1.5MB)</a>
        <a class="link-button" href="candidate.html" style="display:block;text-align:center;padding:0.6em">View executive table &amp; why 0.2778 →</a>
        <div class="download-meta"><div><span>Score estimate</span><strong>Not estimable</strong><br><small>HOLDOUT NOT RUN</small></div><div><span>Unique vs 9 focus</span><strong style="color:#2e7d32">YES 16.3%</strong><br><small>FAIL vs lattice 99.89%</small></div><div><span>Validator</span><strong style="color:#2e7d32">PASS [0,1]</strong><br><small>Fixes range error</small></div></div>
        <p style="margin-top:0.5em;font-size:0.85em;color:#b00"><strong>⚠️ DO NOT SUBMIT for leaderboard</strong> — lattice saturation + no holdout win. Research baseline only.</p>
      `;
    }
    // Add candidate panel after comparison table note
    const comp = document.getElementById('comparison');
    if (comp) {
      const panel = document.createElement('section');
      panel.className = 'section panel';
      panel.id = 'new-candidate';
      panel.innerHTML = `
        <p class="eyebrow">New research candidate · 27 Oct 2026</p>
        <h2>Format-valid control — not a promoted winner</h2>
        <p>A new <strong>format-valid TIFF</strong> (776KB zeros.tif, SHA ${zerosSha.slice(0,12)}…) was generated in this session. It passes all 15 validator checks (CRS EPSG:32611, 3730×3292, 100m, float32, values in [0,1], no NaN inside footprint) and fixes the prior “Predicted values must be in range [0,1]” failure. Geometry: 37,654 dots uniformly sampled >300m from catalogue, off-catalogue Poisson baseline.</p>
        <div class="table-wrap"><table><thead><tr><th>File to download</th><th>Estimate score</th><th>Unique vs 9 focus GEMSDOE?</th><th>Lattice?</th><th>Validator</th><th>Submit?</th></tr></thead><tbody><tr style="background:#e8f5e9"><td><a href="${zerosFile}" download><code>${name}</code></a><br><small>SHA ${zerosSha}</small></td><td><strong>Not estimable</strong><br><small>HOLDOUT NOT RUN; random baseline expected &lt;0.10</small></td><td><span class="tag" style="background:#4caf50;color:white">UNIQUE — max 16.3% &lt;70%</span><br><small>vs GEMSDOE27; all 9 &lt;70%</small></td><td><span class="tag negative">FAIL 99.89% &gt;70%</span><br><small>vs 13gems s5 lattice</small></td><td><span class="tag unknown">finite-grid PASS</span></td><td><span class="tag negative">NO — research only</span></td></tr></tbody></table></div>
        <p><a href="candidate.html">Full executive table (all 9 priority sites + new candidate) →</a> · <a href="evidence/candidate_poisson_20261027.json">Run-card JSON ↗</a> · <a href="evidence/candidate_poisson_20261027_validator.json">Validator receipts ↗</a></p>
        <p class="subtext"><strong>Why GEMSDOE32 0.2778?</strong> Measured deletion ladder: 44,090→40,199 (remove ≤1px annulus) →37,654 (remove 1–2px) = annulus thrift + 3px dot spacing on H19-5 field. Adding dots back (38,854) lowered score. Further thinning ≤2k dots near zero credit; next gains need better detector surface, not sparser emission. See <a href="candidate.html#why-02778">PhD analysis</a>.</p>
      `;
      comp.insertAdjacentElement('afterend', panel);
    }
    // Update notice if exists
    const notice = document.querySelector('div.notice');
    if (notice && notice.textContent.includes('historical winners duplicate')) {
      notice.style.background = '#e8f5e9';
      notice.style.borderColor = '#2e7d32';
      notice.innerHTML = `<span class="icon" aria-hidden="true" style="background:#2e7d32">✓</span><div><strong>NEW CANDIDATE AVAILABLE — READ VERDICT BEFORE DOWNLOADING</strong><p>A <strong>format-valid, range [0,1]-compliant</strong> research TIFF is now downloadable above (776KB zeros.tif). It is <strong>UNIQUE vs all 9 focus GEMSDOE sites</strong> and fixes the prior “Predicted values must be in range [0,1]” error, but <strong>fails the dense lattice (99.89%) and has no holdout DTI win</strong>, so it is <strong>negative / DO NOT SUBMIT</strong> as a competitive entry. Historical winners still duplicate (100% overlap). <a href="candidate.html" style="text-decoration:underline">See executive table with file, estimate, uniqueness →</a></p></div>`;
    }
    // Update date
    const dateEl = document.querySelector('p.date');
    if (dateEl) dateEl.textContent = '27 October 2026 · Audited evidence, not a score projection';
  }).catch(()=>{});
});
