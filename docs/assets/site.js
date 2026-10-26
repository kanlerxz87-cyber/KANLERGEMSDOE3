/* Read-only participant source change detection. Never authorizes a submission. */
(() => {
  'use strict';
  const cards = [...document.querySelectorAll('[data-source-repo]')];
  if (!cards.length) return;
  const summary = document.getElementById('feed-summary');
  const button = document.getElementById('refresh-sources');
  const ttl = 60 * 60 * 1000;
  const memory = new Map();
  const attempts = new Map();
  let busy = false;
  let timer;

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

  function attempted(repo) {
    let last = attempts.get(repo);
    try {
      const stored = Number(localStorage.getItem(`gems-source-attempt:${repo}`));
      if (Number.isFinite(stored) && stored > 0 && stored <= Date.now()
          && (!Number.isFinite(last) || stored > last)) last = stored;
    } catch (_) { /* The per-page fallback still backs off blocked storage. */ }
    return last;
  }

  function markAttempt(repo) {
    const now = Date.now();
    attempts.set(repo, now);
    try { localStorage.setItem(`gems-source-attempt:${repo}`, String(now)); }
    catch (_) { /* A failed storage API never disables the safe live check. */ }
  }

  async function check(card) {
    const repo = card.dataset.sourceRepo;
    const reviewed = card.dataset.reviewedSha;
    const line = card.querySelector('.freshness');
    if (!line) return 'unknown';
    if (!/^buffedlizard55-lab\/GEMSDOE(?:24|25|27|28|30|31|32|33|36)$/.test(repo)) {
      line.textContent = 'Unknown source; no approval inferred.';
      return 'unknown';
    }
    let record = cached(repo);
    try {
      if (!record) {
        const last = attempted(repo);
        if (Number.isFinite(last) && Date.now() - last >= 0 && Date.now() - last < ttl) throw new Error("Retry backed off");
        markAttempt(repo);
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

  function schedule() {
    clearTimeout(timer);
    const expiry = cards.map(card => {
      const repo = card.dataset.sourceRepo;
      return (cached(repo)?.time ?? attempted(repo) ?? Date.now()) + ttl;
    });
    const delay = Math.max(1000, Math.min(...expiry) - Date.now() + 100);
    timer = setTimeout(() => {
      if (document.visibilityState !== 'hidden') refresh();
    }, delay);
  }

  async function refresh() {
    if (busy) return;
    busy = true;
    clearTimeout(timer);
    if (button) button.disabled = true;
    try {
      if (summary) summary.textContent = 'Checking participant source commits only. No model scores or approval labels are fetched.';
      const outcomes = await Promise.all(cards.map(check));
      const count = name => outcomes.filter(item => item === name).length;
      if (summary) summary.textContent = `${count('changed')} changed · ${count('unchanged')} unchanged · ${count('unknown')} unknown. Source-only observations; no submission approval changes. Visible pages refresh automatically at cache expiry; checks/retries are limited to once an hour per repository.`;
    } finally {
      busy = false;
      if (button) button.disabled = false;
      schedule();
    }
  }
  if (button) button.addEventListener('click', refresh);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') refresh();
  });
  refresh();
})();
