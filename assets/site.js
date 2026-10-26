/* Public, anonymous feed. A failed request never changes the dated snapshot. */
(() => {
  const host = document.querySelector('[data-public-feed]');
  if (!host) return;
  const state = document.querySelector('[data-feed-state]');
  const scoreNode = document.querySelector('[data-feed-score]');
  const participantNode = document.querySelector('[data-feed-participant]');
  const dateNode = document.querySelector('[data-feed-date]');
  const endpoint = 'https://api.github.com/repos/kanlerxz87-cyber/KANLERGEMSDOE3/releases/tags/public-evidence-feed';
  fetch(endpoint, { headers: { Accept: 'application/vnd.github+json' }, cache: 'no-store' })
    .then((res) => { if (!res.ok) throw new Error('feed unavailable'); return res.json(); })
    .then((release) => {
      const data = JSON.parse(release.body);
      const entry = data.leaderboard;
      const timestamp = Date.parse(data.observed_utc);
      const rawValue = entry?.value;
      const value = Number(rawValue);
      const sites = ['GEMSDOE24','GEMSDOE25','GEMSDOE27','GEMSDOE28','GEMSDOE30','GEMSDOE31','GEMSDOE32','GEMSDOE33','GEMSDOE36'];
      if (data.schema !== 'gems-public-feed-v1' || entry?.rank !== 1 ||
          typeof rawValue !== 'string' || !/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(rawValue) ||
          !Number.isFinite(value) || value < 0 || value > 1 ||
          typeof data.observed_utc !== 'string' || !Number.isFinite(timestamp) || timestamp > Date.now() + 600000 ||
          typeof entry.participant !== 'string' || !entry.participant.trim() || entry.participant.length > 200 ||
          !Array.isArray(data.site_heads) || data.site_heads.length !== sites.length ||
          sites.some((site) => data.site_heads.filter((row) => row.site === site && /^[a-f0-9]{40}$/.test(row.sha)).length !== 1)) throw new Error('invalid feed');
      if (timestamp < Date.parse(host.dataset.snapshotUtc)) {
        state.textContent = 'Dated snapshot · scheduled feed is older';
        return;
      }
      scoreNode.textContent = value.toFixed(4);
      participantNode.textContent = entry.participant;
      dateNode.textContent = new Date(timestamp).toUTCString();
      const ageHours = (Date.now() - timestamp) / 3600000;
      state.textContent = ageHours > 30 ? 'Scheduled feed · stale; check source' : 'Scheduled public feed';
      document.querySelectorAll('[data-site-head]').forEach((node) => {
        const item = data.site_heads.find((row) => row.site === node.dataset.siteHead);
        if (item && /^[a-f0-9]{40}$/.test(item.sha)) {
          node.textContent = item.sha === node.dataset.reviewedCommit
            ? 'Reviewed commit current' : 'Source changed · re-audit needed';
        }
      });
    })
    .catch(() => { state.textContent = 'Dated snapshot · live feed unavailable'; });
})();
