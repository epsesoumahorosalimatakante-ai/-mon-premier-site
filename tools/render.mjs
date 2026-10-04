// Exporte index.html en vidéo MP4 (1920x1080, 30 i/s), image par image.
// Usage : node tools/render.mjs [sortie.mp4] [fps]
import { createRequire } from 'node:module';
import { execSync, spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(execSync('npm root -g').toString().trim(), 'playwright'))); }

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const out = process.argv[2] || path.join(root, 'video', 'artchille-design-pub.mp4');
const fps = Number(process.argv[3] || 30);
const audio = path.join(root, 'video', 'musique.m4a');

const types = { '.html': 'text/html', '.png': 'image/png', '.woff2': 'font/woff2', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const f = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(`http://localhost:${port}/index.html?render`);
await page.evaluate(() => document.fonts.ready);
await page.waitForLoadState('networkidle');
const total = await page.evaluate(() => window.TOTAL);
const frames = Math.round(total * fps);

fs.mkdirSync(path.dirname(out), { recursive: true });
const args = ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-'];
if (fs.existsSync(audio)) args.push('-i', audio, '-shortest', '-c:a', 'aac', '-b:a', '192k');
args.push('-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out);
const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });

for (let i = 0; i < frames; i++) {
  await page.evaluate(t => window.seek(t), i / fps);
  const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % fps === 0) process.stdout.write(`\r${(i / fps).toFixed(0)}s / ${total}s`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
server.close();
console.log(`\nVidéo exportée : ${out}`);
