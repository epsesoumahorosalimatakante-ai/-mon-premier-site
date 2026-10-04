// Rend index.html image par image → frames/ (usage: node render.mjs [fps] [t1,t2,... pour aperçu])
import { chromium } from 'playwright';
import { mkdirSync } from 'fs';
import path from 'path';
const fps = +(process.argv[2] || 30), only = process.argv[3], DUR = 51, WORKERS = 4;
const out = process.env.OUT || path.resolve('frames'); mkdirSync(out, { recursive: true });
const url = 'file://' + path.resolve('index.html') + '?render=1';
const browser = await chromium.launch();
const times = only ? only.split(',').map(Number) : Array.from({ length: Math.round(DUR * fps) }, (_, i) => i / fps);
const chunks = Array.from({ length: WORKERS }, (_, w) => times.map((t, i) => [t, i]).filter((_, i) => i % WORKERS === w));
await Promise.all(chunks.map(async chunk => {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(url); await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => [...document.images].every(i => i.complete));
  for (const [t, i] of chunk) {
    await page.evaluate(t => render(t), t);
    const name = only ? `t${t}.jpg` : `f${String(i).padStart(5, '0')}.jpg`;
    await page.screenshot({ path: path.join(out, name), type: 'jpeg', quality: 92 });
    if (!only && i % 150 === 0) console.log('frame', i);
  }
}));
await browser.close();
