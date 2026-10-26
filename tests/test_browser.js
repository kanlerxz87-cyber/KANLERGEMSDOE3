/* Dependency-free behavior tests for the static frontend's feed boundary. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('assets/site.js', 'utf8');
const sites = ['GEMSDOE24','GEMSDOE25','GEMSDOE27','GEMSDOE28','GEMSDOE30','GEMSDOE31','GEMSDOE32','GEMSDOE33','GEMSDOE36'];
const feed = (when = new Date().toISOString()) => ({schema:'gems-public-feed-v1', observed_utc:when,
  leaderboard:{rank:1,participant:'Person <unsafe>',value:'0.4444'},
  site_heads:sites.map(site=>({site,sha:'a'.repeat(40)}))});

async function run(release, {snapshot='2026-10-26T00:00:00Z', failure=false}={}) {
  const host={dataset:{snapshotUtc:snapshot}};
  const state={textContent:'fallback'}; const score={textContent:'0.4437'};
  const participant={textContent:'old'}; const date={textContent:'old-date'};
  const changed={dataset:{siteHead:sites[0],reviewedCommit:'b'.repeat(40)},textContent:'pinned'};
  const current={dataset:{siteHead:sites[1],reviewedCommit:'a'.repeat(40)},textContent:'pinned'};
  const nodes={'[data-public-feed]':host,'[data-feed-state]':state,'[data-feed-score]':score,
               '[data-feed-participant]':participant,'[data-feed-date]':date};
  const document={querySelector:q=>nodes[q],querySelectorAll:q=>q==='[data-site-head]'?[changed,current]:[]};
  const fetch = () => failure ? Promise.reject(new Error('offline')) : Promise.resolve({ok:true,json:()=>Promise.resolve({body:JSON.stringify(release)})});
  vm.runInNewContext(source,{document,fetch,Date,Number,Array,JSON,Error});
  await new Promise(resolve=>setImmediate(resolve));
  return {state,score,participant,date,changed,current};
}

(async()=>{
  const valid=await run(feed());
  assert.equal(valid.score.textContent,'0.4444');
  assert.equal(valid.participant.textContent,'Person <unsafe>'); // textContent, not HTML
  assert.equal(valid.changed.textContent,'Source changed · re-audit needed');
  assert.equal(valid.current.textContent,'Reviewed commit current');
  assert.equal(valid.state.textContent,'Scheduled public feed');
  const stale=await run(feed('2026-10-26T01:00:00Z'));
  if (Date.now()-Date.parse('2026-10-26T01:00:00Z') > 30*3600000)
    assert.equal(stale.state.textContent,'Scheduled feed · stale; check source');
  const older=await run(feed('2026-10-25T23:00:00Z'));
  assert.equal(older.state.textContent,'Dated snapshot · scheduled feed is older');
  assert.equal(older.score.textContent,'0.4437');
  const broken=feed();broken.leaderboard.value=null;
  const invalid=await run(broken);
  assert.equal(invalid.score.textContent,'0.4437');
  assert.equal(invalid.state.textContent,'Dated snapshot · live feed unavailable');
  const missing=feed();missing.site_heads.pop();
  assert.equal((await run(missing)).score.textContent,'0.4437');
  const offline=await run(null,{failure:true});
  assert.equal(offline.state.textContent,'Dated snapshot · live feed unavailable');
  console.log('Browser feed behavior: 7 scenarios passed');
})().catch(e=>{console.error(e);process.exit(1)});
