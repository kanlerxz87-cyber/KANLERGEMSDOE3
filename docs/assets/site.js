/* Read-only participant source change detection. Never authorizes a submission. */
(() => {
  'use strict';
  const cards = [...document.querySelectorAll('[data-source-repo]')];
  if (!cards.length) return;
  const summary = document.getElementById('feed-summary');
  const button = document.getElementById('refresh-sources');
  const ttl = 60 * 60 * 1000;
  const memory = new Map();

  function cached(repo) {
    try {
      const record = JSON.parse(localStorage.getItem(`gems-source:${repo}`));
      if (record && /^[a-f0-9]{40}$/.test(record.sha) && Number.isFinite(record.time)
          && Date.now() - record.time >= 0 && Date.now() - record.time < ttl) return record;
    } catch (_) { /* Storage may be blocked; that must not suppress the feed. */ }
    const record = memory.get(repo);
    if (record && Number.isFinite(record.time)
        && Date.now() - record.time >= 0 && Date.now() - record.time < ttl) return record;
    memory.delete(repo);
    return undefined;
  }

  function save(repo, record) {
    memory.set(repo, record);
    try { localStorage.setItem(`gems-source:${repo}`, JSON.stringify(record)); }
    catch (_) { /* Private-browsing/storage restrictions are safe to ignore. */ }
  }

  async function check(card) {
    const repo = card.dataset.sourceRepo;
    const reviewed = card.dataset.reviewedSha;
    const line = card.querySelector('.freshness');
    if (!/^buffedlizard55-lab\/GEMSDOE(?:24|25|27|28|30|31|32|33|36)$/.test(repo)) {
      line.textContent = 'Unknown source; no approval inferred.';
      return 'unknown';
    }
    let record = cached(repo);
    try {
      if (!record) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);
        try {
          const response = await fetch(`https://api.github.com/repos/${repo}/commits/HEAD`, {
            signal: controller.signal, credentials: 'omit', referrerPolicy: 'no-referrer',
            headers: { Accept: 'application/vnd.github+json' },
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const data = await response.json();
          if (!/^[a-f0-9]{40}$/.test(data.sha)) throw new Error('Missing commit');
          record = { sha: data.sha, time: Date.now() };
          save(repo, record);
        } finally { clearTimeout(timeout); }
      }
      const changed = record.sha !== reviewed;
      line.className = `freshness ${changed ? 'changed' : 'unchanged'}`;
      line.textContent = changed
        ? `Changed since review · ${record.sha.slice(0, 10)}. Approval remains blocked.`
        : 'Source unchanged at latest check. Approval remains blocked.';
      line.title = `Source-only check at ${new Date(record.time).toISOString()}; cached for at most one hour.`;
      return changed ? 'changed' : 'unchanged';
    } catch (_) {
      line.className = 'freshness unavailable';
      line.textContent = 'Live status unavailable · reviewed snapshot retained. Approval remains blocked.';
      return 'unknown';
    }
  }

  async function refresh() {
    if (button) button.disabled = true;
    if (summary) summary.textContent = 'Checking participant source commits only. No model scores or approval labels are fetched.';
    const outcomes = await Promise.all(cards.map(check));
    const count = name => outcomes.filter(item => item === name).length;
    if (summary) summary.textContent = `${count('changed')} changed · ${count('unchanged')} unchanged · ${count('unknown')} unknown. Source-only observations; no submission approval changes. Successful checks are cached for up to one hour to respect public API limits.`;
    if (button) button.disabled = false;
  }
  if (button) button.addEventListener('click', refresh);
  refresh();
})();
