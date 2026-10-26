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
    link.textContent = 'New SSP1 TIFF: research download YES · submit NO';
    title.append(link);
    const note = document.createElement('p');
    note.textContent = 'Independently generated pixels, but 99.8752% registered-lattice overlap. Detector-only uniqueness passes below do not satisfy the mandatory all-registry rule. Open the nine-site review, audited download and negative run card.';
    panel.append(title, note);
    section.append(panel);
    main.prepend(section);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();
