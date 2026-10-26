/* Real Chromium navigation, responsive layout, clipboard and download tests.
 * Run npm ci --prefix tools/browser && npm test --prefix tools/browser.
 * No external web assets or training data are needed. Results stay in .cache.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const {spawn, spawnSync} = require('node:child_process');
const puppeteer = require('puppeteer-core');
const chromium = require('@sparticuz/chromium').default;
const root = path.resolve(__dirname, '../..');
const outDir = path.join(root, '.cache/browser-tests');
const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');
const card = JSON.parse(fs.readFileSync(path.join(root, 'evidence/run_card.json')));

function htmlPages(dir, prefix = '') {
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap(e =>
    e.isDirectory() ? htmlPages(path.join(dir,e.name), `${prefix}${e.name}/`) :
      e.name.endsWith('.html') ? [`${prefix}${e.name}`] : []);
}

async function localServer() {
  const child = spawn('python3', ['-u','-m','http.server','0','--bind','0.0.0.0',
    '--directory',path.join(root,'docs')], {stdio:['ignore','pipe','pipe']});
  const url = await new Promise((resolve,reject) => {
    const timer = setTimeout(() => {child.kill(); reject(new Error('HTTP server startup timed out'));},10000);
    child.on('error',e=>{clearTimeout(timer);reject(e)});
    child.on('exit',code=>{clearTimeout(timer);reject(new Error(`HTTP server exited: ${code}`))});
    const ready = data => {
      const m = String(data).match(/port (\d+)/);
      if (m) {clearTimeout(timer);resolve(`http://127.0.0.1:${m[1]}/`)}
    };
    child.stdout.on('data',ready); child.stderr.on('data',ready);
  });
  return {child,url};
}

function provisionLibraries() {
  // The serverless binary includes its NSS/NSPR libraries. Minimal developer
  // images may not have these installed globally; no root/apt access is needed.
  const pkg = path.resolve(path.dirname(require.resolve('@sparticuz/chromium')), '..');
  const archive = path.join(outDir,'al2023.tar');
  const runtime = path.join(outDir,'runtime');
  fs.mkdirSync(runtime,{recursive:true});
  fs.writeFileSync(archive,zlib.brotliDecompressSync(fs.readFileSync(path.join(pkg,'bin/al2023.tar.br'))));
  const extract = spawnSync('tar',['-xf',archive,'-C',runtime]);
  if (extract.status !== 0) throw new Error(`Library extraction failed: ${extract.stderr}`);
  process.env.LD_LIBRARY_PATH = `${path.join(runtime,'lib')}:${process.env.LD_LIBRARY_PATH||''}`;
}

async function download(page, session, selector, directory, filename, expectedSha) {
  let timer;
  let onProgress;
  const complete = new Promise((resolve,reject) => {
    timer=setTimeout(()=>reject(new Error(`Download timed out: ${filename}`)),15000);
    onProgress = e => {
      if (e.state === 'completed') {clearTimeout(timer);resolve(e)}
      if (e.state === 'canceled') {clearTimeout(timer);reject(new Error('Download canceled'))}
    };
    session.on('Browser.downloadProgress',onProgress);
  });
  try {
    await page.click(selector);
    await complete;
    const bytes=fs.readFileSync(path.join(directory,filename));
    assert.equal(sha256(bytes),expectedSha,'The browser must download exactly the audited bytes');
    return {filename,bytes:bytes.length,sha256:expectedSha};
  } finally {
    clearTimeout(timer);session.off('Browser.downloadProgress',onProgress);
  }
}

(async()=>{
  fs.mkdirSync(outDir,{recursive:true});
  provisionLibraries();
  let server, browser;
  try {
    server=process.env.BASE_URL ? null : await localServer();
    const base=process.env.BASE_URL||server.url;
    browser=await puppeteer.launch({executablePath:await chromium.executablePath(),args:chromium.args,headless:true});
    const page=await browser.newPage();
    const jsErrors=[], badResponses=[];
    page.on('pageerror',e=>jsErrors.push(String(e)));
    page.on('response',r=>{if(r.status()>=400)badResponses.push({url:r.url(),status:r.status()})});
    const visited=[];
    await page.setViewport({width:1440,height:1080,deviceScaleFactor:1});
    for(const file of htmlPages(path.join(root,'docs'))) {
      const response=await page.goto(new URL(file,base).href,{waitUntil:'networkidle0'});
      assert.equal(response.status(),200,file);
      assert.equal(await page.$eval('html',el=>el.lang),'en');
      assert.ok(await page.$('main'),'Main landmark required');
      visited.push(file);
    }
    const responsive=[];
    for(const width of [1440,768,390,320]) {
      await page.setViewport({width,height:width>=768?1080:844,deviceScaleFactor:1});
      await page.goto(new URL('executive-summary.html',base).href,{waitUntil:'networkidle0'});
      const measured=await page.evaluate(()=>({body:document.body.scrollWidth,viewport:innerWidth,
        scrollableTables:[...document.querySelectorAll('.table-shell')].map(el=>el.scrollWidth>el.clientWidth)}));
      assert.ok(measured.body<=width,`Body overflow at ${width}px: ${measured.body}`);
      if(width===390) await page.screenshot({path:path.join(outDir,'mobile.png'),fullPage:true});
      responsive.push({width,...measured});
    }
    await page.setViewport({width:1440,height:1080,deviceScaleFactor:1});
    await page.goto(new URL('index.html',base).href,{waitUntil:'networkidle0'});
    assert.ok((await page.$eval('main',el=>el.innerText)).includes('NO AUTHORIZED SUBMISSION'));
    await page.screenshot({path:path.join(outDir,'desktop.png'),fullPage:true});
    const dir=fs.mkdtempSync(path.join(outDir,'download-'));
    const session=await browser.target().createCDPSession();
    await session.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:dir,eventsEnabled:true});
    const tif=await download(page,session,'a[download][href$="-zeros.tif"]',dir,card.downloads.tif,card.raster_sha256);
    const bundle=JSON.parse(fs.readFileSync(path.join(root,'evidence/submission_bundle.json')));
    const zip=await download(page,session,'a[download][href$="-zeros.zip"]',dir,card.downloads.zip,bundle.zeros_zip.sha256);
    await browser.defaultBrowserContext().overridePermissions(new URL(base).origin,['clipboard-read','clipboard-write','clipboard-sanitized-write']);
    await page.goto(new URL('submission-guide.html',base).href,{waitUntil:'networkidle0'});
    await page.click('[data-copy="submission-note"]');
    await page.waitForFunction(()=>document.querySelector('#copy-status').textContent.includes('Copied'));
    const note=await page.evaluate(()=>navigator.clipboard.readText());
    assert.equal(note,card.submission_note); assert.ok(note.length<=140);
    await browser.defaultBrowserContext().overridePermissions(new URL(base).origin,[]);
    await page.reload({waitUntil:'networkidle0'});
    await page.click('[data-copy="submission-note"]');
    await page.waitForFunction(()=>document.querySelector('#copy-status').textContent.includes('unavailable'));
    assert.equal(await page.$eval('#submission-note',el=>el.textContent.trim()),card.submission_note);
    assert.deepEqual(jsErrors,[]); assert.deepEqual(badResponses,[]);
    const result={status:'PASS',verified_utc:new Date().toISOString(),browser:'Chromium '+await browser.version(),
      pages_visited:visited,responsive,downloads:[tif,zip],clipboard_note_characters:note.length,clipboard_denial_fallback_tested:true,
      javascript_errors:jsErrors,failed_responses:badResponses,scientific_verdict:card.verdict,ok_to_submit:false,
      scope:'Browser delivery checks only; these cannot override a negative scientific run'};
    fs.writeFileSync(path.join(outDir,'results.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result,null,2));
  } finally {
    if(browser) await browser.close();
    if(server) server.child.kill();
  }
})().catch(e=>{console.error(e);process.exitCode=1});
