// Desktop + mobile smoke test for the 29 Oct 2026 executive-summary desk and the updated index.
// Usage: GEMS_PREVIEW_URL=http://127.0.0.1:8011 node tests/browser_smoke_desk20261029.mjs
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const require = createRequire(path.join(root, 'tools/browser/package.json'));
const { chromium: driver } = require('playwright-core');
const browserPackage = await import(pathToFileURL(require.resolve('@sparticuz/chromium')));
const { default: binary, inflate, setupLambdaEnvironment } = browserPackage;
if (process.platform === 'linux') {
  const libraryRoot = await inflate(path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../bin/al2023.tar.br'));
  setupLambdaEnvironment(path.join(libraryRoot, 'lib'));
}
const base = (process.env.GEMS_PREVIEW_URL || 'http://127.0.0.1:8011').replace(/\/$/, '');
const browser = await driver.launch({ executablePath: await binary.executablePath(), args: binary.args.filter(arg => arg !== '--single-process'), headless: true });
const results = [];
const viewports = [['desktop', { width: 1366, height: 900 }], ['mobile', { width: 390, height: 844 }]];
for (const [label, vp] of viewports) {
  const page = await (await browser.newContext({ viewport: vp })).newPage();
  const response = await page.goto(base + '/executive-summary-20261029/index.html', { waitUntil: 'networkidle' });
  assert.equal(response.status(), 200, `${label}: desk page status`);
  const text = await page.evaluate(() => document.body.innerText);
  assert.match(text, /Download: NOT PERMITTED/, `${label}: top-of-page download decision`);
  assert.match(text, /Competition upload: NOT PERMITTED/, `${label}: top-of-page upload decision`);
  assert.doesNotMatch(text, /ready to download/i, `${label}: no download-ready claim`);
  const links = await page.evaluate(() => [...document.querySelectorAll('a[download]')].length);
  assert.equal(links, 0, `${label}: no download link while gate fails`);
  const dims = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  assert.ok(dims.scroll <= dims.viewport + 1, `${label}: horizontal overflow ${JSON.stringify(dims)}`);
  await page.screenshot({ path: `data/ui-review/desk-20261029-${label}.png`, fullPage: true });
  results.push(`${label}: decision text, no download link, no overflow`);

  await page.context().close();
}
await browser.close();
console.log(JSON.stringify({ status: 'pass', checks: results }, null, 2));
