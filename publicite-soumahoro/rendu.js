// Rend pub.html image par image (30 i/s, 1080x1920) et assemble la vidéo avec ffmpeg.
// Usage : node rendu.js   (nécessite playwright, ffmpeg et musique.wav)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const FPS = 30, DUREE = 35;
const dir = __dirname;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('Erreur page :', e.message));
  await page.goto('file://' + path.join(dir, 'pub.html') + '?render=1');
  await page.evaluate(() => window.ready);

  const ff = spawn('ffmpeg', ['-y', '-v', 'error',
    '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', '-',
    '-i', path.join(dir, 'musique.wav'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
    path.join(dir, 'soumahoro-transport-pub.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });

  const total = FPS * DUREE;
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.render(t), i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`image ${i}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('Vidéo : soumahoro-transport-pub.mp4');
})();
