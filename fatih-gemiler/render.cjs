// Kare kare render: node render.cjs [--fps 30] [--pr 1] [--from 0] [--to 45.6] [--out frames] [--stills 1,5,9]
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? a.concat([[v.slice(2), arr[i + 1]]]) : a), []));
const FPS = +(args.fps || 30), PR = +(args.pr || 1);
const OUT = path.resolve(args.out || 'frames');
const ROOT = __dirname;

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mp3': 'audio/mpeg', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(`http://localhost:${port}/${args.page || 'index.html'}?render=1&pr=${PR}`);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 300000 });
  console.log('timeline', JSON.stringify(await page.evaluate(() => window.TIMELINE)));
  fs.mkdirSync(OUT, { recursive: true });

  let times;
  if (args.stills) times = args.stills.split(',').map(Number);
  else {
    const dur = await page.evaluate(() => window.DURATION);
    const from = +(args.from || 0), to = Math.min(+(args.to || dur), dur);
    times = [];
    for (let f = Math.round(from * FPS); f < Math.round(to * FPS); f++) times.push(f / FPS);
  }
  const t0 = Date.now();
  for (let i = 0; i < times.length; i++) {
    const t = times[i];
    await page.evaluate(tt => window.renderFrame(tt), t);
    const name = args.stills ? `still_${t.toFixed(2)}.jpg` : `f_${String(Math.round(t * FPS)).padStart(5, '0')}.jpg`;
    await page.screenshot({ path: path.join(OUT, name), type: 'jpeg', quality: 92 });
    if (i % 50 === 0) console.log(`kare ${i + 1}/${times.length}  t=${t.toFixed(2)}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await browser.close();
  server.close();
})();
