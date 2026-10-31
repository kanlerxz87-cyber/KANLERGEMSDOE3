// UI regression tests only. Never a geological experiment or a submission.
// npm ci --prefix tools/browser; node tests/browser_smoke.mjs
import assert from 'node:assert/strict';
import http from 'node:http';
import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const require = createRequire(path.join(root, 'tools/browser/package.json'));
const { chromium: driver } = require('playwright-core');
const browserPackage = await import(pathToFileURL(require.resolve('@sparticuz/chromium')));
const { default: binary, inflate, setupLambdaEnvironment } = browserPackage;
// The sandbox lacks NSS/NSPR. Use the libraries bundled in the npm package;
// no system package install or external browser download is required.
if (process.platform === 'linux') {
  const libraryRoot = await inflate(path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../bin/al2023.tar.br'));
  setupLambdaEnvironment(path.join(libraryRoot, 'lib'));
}
const base = process.env.GEMS_PREVIEW_URL || 'http://127.0.0.1:8000'; // Test runner only, never browser application code.
const feed = JSON.parse(await fs.readFile(path.join(root, 'docs/data/focus-feed.json'), 'utf8'));
const hashes = Object.fromEntries(feed.rows.map(row => [row.repository, row.commit]));
const output = path.join(root, 'data/ui-review');
await fs.mkdir(output, { recursive: true });
const checks = [];
let browser;
let server;

async function context(mode = 'unchanged', width = 1440, height = 1000, blockStorage = false) {
  const context = await browser.newContext({ viewport: { width, height } });
  if (blockStorage) await context.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', { get() { throw new Error('Storage disabled in regression fixture'); } });
  });
  context.gemsRequestCount = 0;
  await context.route('https://api.github.com/**', async route => {
    context.gemsRequestCount += 1;
    const url = new URL(route.request().url());
    const repo = url.pathname.split('/').slice(2, 4).join('/');
    if (mode === 'unavailable') return route.fulfill({ status: 403, contentType: 'application/json', body: '{"message":"Rate limited fixture"}' });
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ sha: mode === 'changed' ? 'f'.repeat(40) : hashes[repo] }) });
  });
  return context;
}

async function noGlobalOverflow(page, label) {
  const dimensions = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  assert.ok(dimensions.scroll <= dimensions.viewport + 1, `${label}: global overflow ${JSON.stringify(dimensions)}`);
  checks.push(`${label}: no global horizontal overflow`);
}

try {
  if (process.argv.includes('--serve')) {
    const docs = path.join(root, 'docs');
    const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json' };
    server = http.createServer(async (request, response) => {
      try {
        let pathname = decodeURIComponent(new URL(request.url, 'http://test.invalid').pathname);
        if (pathname.endsWith('/')) pathname += 'index.html';
        const target = path.resolve(docs, '.' + pathname);
        if (!target.startsWith(docs + path.sep)) throw new Error('Unsafe path');
        const body = await fs.readFile(target);
        response.writeHead(200, { 'Content-Type': types[path.extname(target)] || 'text/plain' });
        response.end(body);
      } catch (_) { response.writeHead(404); response.end('Not found'); }
    });
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(Number(new URL(base).port || 8000), '0.0.0.0', resolve);
    });
  }
  browser = await driver.launch({ executablePath: await binary.executablePath(), args: binary.args.filter(arg => arg !== '--single-process'), headless: true });
  const desktop = await context();
  const page = await desktop.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const response = await page.goto(base + '/index.html', { waitUntil: 'networkidle' });
  assert.equal(response.status(), 200);
  await page.locator('#feed-summary').filter({ hasText: '9 unchanged' }).waitFor();
  assert.equal(await page.locator('#comparison tbody tr').count(), 9);
  assert.match(await page.locator('#comparison tbody tr').first().innerText(), /GEMSDOE32/);
  assert.equal(await page.locator('a[download]').count(), 0);
  const concurrentArtifacts = await page.locator('#concurrent-main-artifacts').innerText();
  assert.match(concurrentArtifacts, /HOLDOUT-DTI.*0\.300267|0\.300267 HOLDOUT-DTI/s);
  assert.match(concurrentArtifacts, /PR #48.*promote|promote.*ok_to_upload:false/s);
  assert.match(concurrentArtifacts, /QUARANTINED/);
  assert.match(concurrentArtifacts, /Earlier geofault candidate/i);
  assert.match(concurrentArtifacts, /conflicting archived validation and holdout records/);
  assert.equal(await page.locator('#concurrent-main-artifacts a[href*="downloads/"]').count(), 0);
  assert.match(await page.locator('.file-unavailable').innerText(), /DO NOT SUBMIT/);
  assert.equal(await page.locator('.hypothesis').count(), 4);
  await page.locator('#cadg-submod-study-link').waitFor();
  const archivedLink = await page.locator('#cadg-submod-study-link').innerText();
  assert.match(archivedLink, /DO NOT SUBMIT/);
  assert.doesNotMatch(archivedLink, /0\.155510/); // no unscoped prior holdout in the link
  assert.ok(await page.evaluate(() => {
    const warning = document.querySelector('.notice');
    const archived = document.querySelector('#cadg-submod-study-link');
    return !!(warning.compareDocumentPosition(archived) & Node.DOCUMENT_POSITION_FOLLOWING);
  }), 'Historical study links must not precede the primary no-submit warning');
  assert.match(await page.locator('main').innerText(), /6,436 dots/);
  assert.match(await page.locator('#parallel-control').innerText(), /DO NOT SUBMIT|not a submission/i);
  assert.match(await page.locator('#kpl36-conflict').innerText(), /99\.17%/);
  assert.match(await page.locator('#s2d36-audit').innerText(), /99\.48%/);
  assert.match(await page.locator('#cadg-submod-study-link').innerText(), /99\.94%/);
  assert.equal(await page.locator('#changed-peer-audit tbody tr').count(), 9);
  assert.match(await page.locator('#changed-peer-audit').innerText(), /29 changed raster files fail one reference/);
  assert.match(await page.locator('#changed-peer-audit').innerText(), /not.*a count of independent models/i);
  checks.push('primary warning precedes historical-study links and peer duplicate checks remain visible');
  await noGlobalOverflow(page, 'desktop summary');
  await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: true });
  checks.push('desktop: nine sites, four hypotheses, historical ranking and no approved download');
  await page.locator('details').last().evaluate(element => { element.open = true; });
  for (const name of ['executive-summary.html', 'submission.html', 'research.html', 'hypotheses.html', 'summary.html', 'sources.html', 'parallel-research.html', 'parallel-gpc-dashboard.html', 'parallel-gpc-submission-guide.html', 'k3h1.html', 'candidate.html', ...feed.rows.map(row => `sites/${row.site}.html`)]) {
    const result = await page.goto(base + '/' + name, { waitUntil: 'networkidle' });
    assert.equal(result.status(), 200, name);
    assert.equal(await page.locator('h1').count(), 1, name);
    await noGlobalOverflow(page, 'desktop ' + name);
  }
  await page.goto(base + '/candidate.html', { waitUntil: 'networkidle' });
  assert.match(await page.locator('.notice').innerText(), /DO NOT SUBMIT/);
  assert.equal(await page.locator('a[download]').count(), 4); // research archive only
  assert.match(await page.locator('main').innerText(), /rejected file was not provided/);
  assert.match(await page.locator('main').innerText(), /superseded claims/);
  checks.push('parallel TIFF downloads stay quarantined with corrected uncertainty');
  for (const name of ['parallel-gpc-dashboard.html', 'parallel-gpc-submission-guide.html']) {
    await page.goto(base + '/' + name, { waitUntil: 'networkidle' });
    const text = await page.locator('main').innerText();
    assert.match(text, /DO NOT SUBMIT/);
    assert.match(text, /selector cannot waive/i);
    assert.doesNotMatch(text, /Download the unique GPC|Scored historical files prove the zeros encoding is accepted|NaN outside the footprint triggers/);
    if (await page.locator('a[download]').count()) assert.match(text, /research.only/i);
  }
  for (const name of ['cadg-submod/index.html', 'cadg-submod/executive-summary.html']) {
    const result = await page.goto(base + '/' + name, { waitUntil: 'networkidle' });
    assert.equal(result.status(), 200, name);
    assert.equal(await page.locator('h1').count(), 1, name);
    const body = await page.locator('body').innerText();
    assert.match(body, /DO NOT SUBMIT/);
    assert.match(body, /99\.94%/);
    assert.match(body, /99\.95%/);
    assert.match(body, /99\.73%/);
    assert.match(body, /cannot (override|waive|change)/i);
    assert.match(body, /rejected upload was not supplied/i);
    assert.match(body, /unverified/i);
    assert.doesNotMatch(body, /prevents.*Predicted values/i);
    assert.equal(await page.locator('a[download]').count(), 0);
    await noGlobalOverflow(page, 'desktop ' + name);
  }
  checks.push('CADG pages quarantine both encodings and reject selector override or portal guarantees');
  for (const name of ['atsc-submod/index.html', 'atsc-submod/executive-summary.html', 'atsc-submod/hypotheses.html']) {
    const result = await page.goto(base + '/' + name, { waitUntil: 'networkidle' });
    assert.equal(result.status(), 200, name);
    assert.equal(await page.locator('h1').count(), 1, name);
    const body = await page.locator('body').innerText();
    assert.match(body, /DO NOT SUBMIT/);
    assert.match(body, /cannot waive/i);
    assert.match(body, /22 Stage-2 corridor features/i);
    assert.doesNotMatch(body, /excising them gave|Three Live-Leaderboard Physical Laws/);
    assert.equal(await page.locator('a[download]').count(), 0, name);
    if (name !== 'atsc-submod/hypotheses.html') assert.match(body, /unverified/i);
    await noGlobalOverflow(page, 'desktop ' + name);
  }
  checks.push('ATSC pages quarantine downloads, expose missing canaries and preserve the literal duplicate stop');
  await page.goto(base + '/cfrp-20261028/index.html', { waitUntil: 'networkidle' });
  const cfrp = await page.locator('body').innerText();
  assert.match(cfrp, /DO NOT SUBMIT/);
  assert.match(cfrp, /44,090 \/ 44,090/);
  assert.match(cfrp, /cannot waive/i);
  assert.doesNotMatch(cfrp, /paste into DrivenData|cannot trigger/i);
  assert.equal(await page.locator('a[download]').count(), 0);
  await noGlobalOverflow(page, 'desktop CFRP archive');
  checks.push('CFRP archive exposes the saved-byte stop without portal guarantees or upload links');
  for (const name of ['cpx-edti/index.html', 'cpx-edti/executive-summary.html', 'cpx-edti/submission-guide.html', 'cpx-edti/hypotheses.html']) {
    await page.goto(base + '/' + name, { waitUntil: 'networkidle' });
    const body = await page.locator('body').innerText();
    assert.match(body, /DO NOT SUBMIT/);
    assert.match(body, /37,648 \/ 37,654/);
    assert.match(body, /cannot waive/i);
    assert.doesNotMatch(body, /NEAREST TO READY|portal-safe/i);
    assert.equal(await page.locator('a[download]').count(), 0, name);
    await noGlobalOverflow(page, 'desktop ' + name);
  }
  checks.push('CPX archive withdraws selector-waiver and portal-safety claims');
  assert.deepEqual(errors, []);
  checks.push('desktop: no JavaScript exceptions across every active page');
  await desktop.close();

  const mobile = await context('unchanged', 390, 844);
  const mobilePage = await mobile.newPage();
  await mobilePage.goto(base + '/', { waitUntil: 'networkidle' });
  await noGlobalOverflow(mobilePage, 'mobile summary');
  const table = await mobilePage.locator('#comparison .table-wrap').evaluate(element => ({ client: element.clientWidth, scroll: element.scrollWidth }));
  assert.ok(table.scroll > table.client, 'The wide table must scroll locally on mobile');
  await mobilePage.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
  for (const name of ['executive-summary.html', 'sources.html', 'research.html', 'parallel-research.html', 'parallel-gpc-dashboard.html', 'k3h1.html', 'candidate.html', 'sites/GEMSDOE32.html', 'sites/GEMSDOE36.html', 'cadg-submod/index.html', 'cadg-submod/executive-summary.html', 'atsc-submod/index.html', 'atsc-submod/executive-summary.html', 'atsc-submod/hypotheses.html', 'cfrp-20261028/index.html', 'cpx-edti/index.html', 'cpx-edti/submission-guide.html']) {
    await mobilePage.goto(base + '/' + name, { waitUntil: 'networkidle' });
    await noGlobalOverflow(mobilePage, 'mobile ' + name);
  }
  checks.push('mobile: table scroll is local; all required controls readable');
  await mobile.close();

  for (const mode of ['changed', 'unavailable']) {
    const isolated = await context(mode);
    const current = await isolated.newPage();
    await current.goto(base + '/', { waitUntil: 'networkidle' });
    await current.locator('#feed-summary').filter({ hasText: mode === 'changed' ? '9 changed' : '9 unknown' }).waitFor();
    assert.equal(await current.locator('a[download]').count(), 0);
    assert.match(await current.locator('.file-unavailable').innerText(), /DO NOT SUBMIT/);
    checks.push(`${mode} source feed never authorizes an upload`);
    if (mode === 'unavailable') {
      await current.locator('#refresh-sources').click();
      await current.waitForFunction(() => !document.getElementById('refresh-sources').disabled);
      assert.equal(isolated.gemsRequestCount, 9, 'Failed requests must back off instead of exhausting the public quota');
      await current.reload({ waitUntil: 'networkidle' });
      await current.locator('#feed-summary').filter({ hasText: '9 unknown' }).waitFor();
      assert.equal(isolated.gemsRequestCount, 9, 'A reload must not bypass the failure backoff');
      checks.push('unavailable source retries and reloads are backed off for one hour');
    }
    await isolated.close();
  }

  const blockedStorage = await context('unchanged', 1440, 1000, true);
  const storagePage = await blockedStorage.newPage();
  await storagePage.goto(base + '/', { waitUntil: 'networkidle' });
  await storagePage.locator('#feed-summary').filter({ hasText: '9 unchanged' }).waitFor();
  checks.push('source feed works when localStorage is unavailable');
  assert.equal(blockedStorage.gemsRequestCount, 9);
  await storagePage.locator('#refresh-sources').click();
  await storagePage.waitForFunction(() => !document.getElementById('refresh-sources').disabled);
  assert.equal(blockedStorage.gemsRequestCount, 9, 'fresh in-memory results must respect the API cache');
  await storagePage.evaluate(() => { const now = Date.now(); Date.now = () => now + 3600001; });
  await storagePage.locator('#refresh-sources').click();
  await storagePage.waitForFunction(() => !document.getElementById('refresh-sources').disabled);
  assert.equal(blockedStorage.gemsRequestCount, 18, 'expired memory cache must be refreshed even when storage is disabled');
  checks.push('source cache expires after one hour, including storage-disabled fallback');
  await blockedStorage.close();

  const timed = await context();
  const timedPage = await timed.newPage();
  await timedPage.clock.install({ time: new Date('2026-10-26T12:00:00Z') });
  await timedPage.goto(base + '/', { waitUntil: 'networkidle' });
  await timedPage.locator('#feed-summary').filter({ hasText: '9 unchanged' }).waitFor();
  const before = await timedPage.locator('.freshness').evaluateAll(elements => elements.map(el => el.title));
  assert.equal(timed.gemsRequestCount, 9);
  await timedPage.clock.fastForward(3602000);
  await timedPage.waitForFunction(previous => [...document.querySelectorAll('.freshness')].every((el, index) => el.title !== previous[index]), before);
  assert.equal(timed.gemsRequestCount, 18);
  assert.equal(await timedPage.locator('a[download]').count(), 0);
  checks.push('visible pages automatically refresh at cache expiry without manual input or approval');
  await timed.close();

  const report = { kind: 'BROWSER_UI_TEST_NOT_MODEL_RESULT', status: 'PASS', checks, source_network: 'GitHub API mocked to exercise unchanged, changed, quota failure and disabled storage; not a live score verification', screenshots: 'data/ui-review (ignored; not submission files)' };
  await fs.writeFile(path.join(output, 'browser-checks.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
}
