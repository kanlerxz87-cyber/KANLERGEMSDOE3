/* A failed or stale refresh is visible; no cross-origin scraping in the browser. */
(async function () {
  const value = document.getElementById('leader-value');
  const status = document.getElementById('feed-status');
  if (!value || !status) return;
  try {
    const response = await fetch('data/live_feed.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('feed unavailable');
    const feed = await response.json();
    const score = String(feed.public_leader ?? '');
    if (!/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(score)) throw new Error('invalid leader');
    if (typeof feed.last_success_utc !== 'string' || !feed.last_success_utc) throw new Error('missing observation time');
    const when = new Date(feed.last_success_utc);
    if (Number.isNaN(when.getTime())) throw new Error('missing observation time');
    value.textContent = score;
    const stamp = when.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
    const age = Date.now() - when.getTime();
    if (feed.status === 'fresh' && age >= 0 && age < 48 * 60 * 60 * 1000) {
      status.textContent = 'Organizer-published · checked ' + stamp;
    } else if (feed.status === 'error') {
      status.textContent = 'Refresh failed · last observed ' + stamp;
    } else {
      status.textContent = 'Snapshot, not live · observed ' + stamp;
    }
  } catch (_) {
    status.textContent = 'Feed unavailable · showing dated snapshot';
  }
}());

(async function () {
  const status = document.getElementById('peer-freshness');
  if (!status) return;
  try {
    const response = await fetch('data/peer_feed.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('feed unavailable');
    const feed = await response.json();
    const when = new Date(feed.checked_utc);
    const age = Date.now() - when.getTime();
    if (feed.status !== 'fresh' || !Number.isInteger(feed.changed_count) ||
        Number.isNaN(when.getTime()) || age < 0 || age >= 48 * 60 * 60 * 1000) {
      status.textContent = 'Peer-head check incomplete or stale · review freshness unknown';
    } else {
      const stamp = when.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
      status.textContent = feed.changed_count + ' peer heads changed since review · not a raster re-audit · checked ' + stamp;
    }
  } catch (_) {
    status.textContent = 'Peer freshness feed unavailable · review freshness unknown';
  }
}());
