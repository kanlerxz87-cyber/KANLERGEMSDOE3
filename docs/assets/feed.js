/* Public observations only. This feed cannot approve or submit an artifact. */
(() => {
  const valueNode = document.getElementById("leaderboard-value");
  const statusNode = document.getElementById("leaderboard-status");
  const peersNode = document.getElementById("peer-status");
  if (!valueNode || !statusNode || !peersNode) return;
  fetch("data/feed.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error("feed unavailable");
      return response.json();
    })
    .then((feed) => {
      const lb = feed.leaderboard || {};
      if (typeof lb.value === "number" && Number.isFinite(lb.value) && lb.value >= 0 && lb.value <= 1) {
        valueNode.textContent = lb.value.toFixed(4);
        const observed = Date.parse(lb.observed_at_utc);
        const age = Date.now() - observed;
        const stale = lb.status !== "current_at_fetch" || !Number.isFinite(observed) || age < 0 || age > 36 * 60 * 60 * 1000;
        statusNode.textContent = `${stale ? "Snapshot / may be stale" : "Observed"} · ${lb.observed_at_utc || "time unknown"}`;
      } else {
        valueNode.textContent = "Unavailable";
        statusNode.textContent = "No verified public observation";
      }
      const peer = feed.peer_heads || {};
      const sites = Array.isArray(peer.sites) ? peer.sites : [];
      if (!sites.length) return;
      const changed = sites.filter((site) => site.changed_since_audit === true).length;
      const unavailable = sites.filter((site) => site.status !== "checked").length;
      peersNode.textContent = `${changed} of ${sites.length} peer heads changed; ${unavailable} unavailable. Head checks do not re-audit TIFFs.`;
    })
    .catch(() => {
      statusNode.textContent = "Snapshot / refresh unavailable · 26 Oct 2026";
      peersNode.textContent = "Peer-head refresh unavailable; pinned audit may be stale.";
    });
})();
