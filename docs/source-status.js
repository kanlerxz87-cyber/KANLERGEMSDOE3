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
