/* Optional source freshness: GitHub's documented public API only. Never poll DrivenData. */
(() => {
  const el = document.querySelector('[data-github-status]');
  if (!el || typeof fetch !== 'function') return;
  const url = 'https://api.github.com/repos/buffedlizard55-lab/GEMSDOE32/commits/main';
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 8000);
  fetch(url, {signal: controller.signal, headers: {'Accept': 'application/vnd.github+json'}})
    .then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
    .then(data => {
      if (!data.sha || !/^[a-f0-9]{40}$/.test(data.sha)) throw new Error('unexpected GitHub response');
      el.textContent = `GEMSDOE32 public main: ${data.sha.slice(0, 8)} · checked ${new Date().toUTCString()}. This is source freshness, not a leaderboard update.`;
    })
    .catch(() => { el.textContent = 'GitHub source freshness could not be checked. The evidence and leaderboard snapshot may be stale.'; })
    .finally(() => window.clearTimeout(timeout));
})();

/* Parallel-safe SSP1 entry point: leave the other lane's generated HTML intact. */
(() => {
  const scriptURL = document.currentScript ? document.currentScript.src : window.location.href;
  const mount = () => {
    const main = document.querySelector('main');
    if (!main || document.getElementById('ssp1-study-link')) return;
    const section = document.createElement('section');
    section.id = 'ssp1-study-link';
    section.className = 'wrap';
    section.setAttribute('aria-label', 'SSP1 research result and strict all-registry gate');
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.style.padding = '20px';
    panel.style.marginTop = '20px';
    const title = document.createElement('h2');
    const link = document.createElement('a');
    link.href = new URL('ssp1/executive-summary.html', scriptURL).href;
    link.textContent = 'Prior SSP1 TIFF: research download only · DO NOT SUBMIT';
    title.append(link);
    const note = document.createElement('p');
    note.textContent = 'Independently generated pixels, but 99.8752% registered-lattice overlap. Detector-only uniqueness passes below do not satisfy the mandatory all-registry rule. Open the nine-site review, audited download and negative run card.';
    panel.append(title, note);
    section.append(panel);
    main.append(section);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();

/* Parallel-safe L-K3-CADG-SUBMOD entry point: isolated under docs/cadg-submod/. */
(() => {
  const scriptURL = document.currentScript ? document.currentScript.src : window.location.href;
  const mount = () => {
    const main = document.querySelector('main');
    if (!main || document.getElementById('cadg-submod-study-link')) return;
    const section = document.createElement('section');
    section.id = 'cadg-submod-study-link';
    section.className = 'wrap';
    section.setAttribute('aria-label', 'L-K3-CADG-SUBMOD 8-fold OOF research result and selector hold');
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.style.padding = '20px';
    panel.style.marginTop = '20px';
    const title = document.createElement('h2');
    const link = document.createElement('a');
    link.href = new URL('cadg-submod/index.html', scriptURL).href;
    link.textContent = 'Prior L-K3-CADG-SUBMOD study · DO NOT SUBMIT';
    title.append(link);
    const note = document.createElement('p');
    note.textContent = 'This prior research artifact failed the literal all-registry lattice rule. Detector-only comparisons and format checks do not authorize a competition slot. See the study for scoped evaluator, confidence interval and provenance. ';
    const guide = document.createElement('a');
    guide.href = new URL('cadg-submod/executive-summary.html', scriptURL).href;
    guide.textContent = 'Research-only forensic archive ->';
    note.append(guide);
    panel.append(title, note);
    section.append(panel);
    main.append(section);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();

/* Parallel-safe L-K3-ATSC-SUBMOD entry point: isolated under docs/atsc-submod/. */
(() => {
  const scriptURL = document.currentScript ? document.currentScript.src : window.location.href;
  const mount = () => {
    const main = document.querySelector('main');
    if (!main || document.getElementById('atsc-submod-study-link')) return;
    const section = document.createElement('section');
    section.id = 'atsc-submod-study-link';
    section.className = 'wrap';
    section.setAttribute('aria-label', 'L-K3-ATSC-SUBMOD 8-fold OOF research result and literal gate');
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.style.padding = '20px';
    panel.style.marginTop = '20px';
    const title = document.createElement('h2');
    const link = document.createElement('a');
    link.href = new URL('atsc-submod/index.html', scriptURL).href;
    link.textContent = 'Latest L-K3-ATSC-SUBMOD study (Exp-ATSC-2): research only · DO NOT SUBMIT';
    title.append(link);
    const note = document.createElement('p');
    note.textContent = 'Scoped participant-mirror HOLDOUT-DTI 0.163715 (95% CI [0.153314, 0.174809], gems-segment-pooled-v1, 60,988 withheld positives; +66.4 bps vs prior CADG; 87/87 genuine fault detectors <=57.14%). Fails the literal all-registry 207k lattice rule (99.99% unfiltered / 99.77% off-catalogue; verdict=negative, slot_authorized=false; selector cannot waive). ';
    const guide = document.createElement('a');
    guide.href = new URL('atsc-submod/executive-summary.html', scriptURL).href;
    guide.textContent = 'Executive summary, encoding reference & research-only GeoTIFFs ->';
    note.append(guide);
    panel.append(title, note);
    section.append(panel);
    main.append(section);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();
