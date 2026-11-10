// Renders the GSAP animation frame by frame with Playwright (headless Chromium) and encodes MP4 + GIF with ffmpeg.
// Usage: node export/render.mjs [--fps 30] [--scale 1] [--gif-width 480] [--gif-fps 12]
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { createServer } from 'node:http';
import { readFile, mkdir, rm } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { dirname, join, extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? Number(process.argv[i + 1]) : d; };
const FPS = arg('fps', 30), SCALE = arg('scale', 1), GIF_W = arg('gif-width', 480), GIF_FPS = arg('gif-fps', 12);
const OUT = join(ROOT, 'output'), FRAMES = join(OUT, 'frames');
const W = 1122, H = 1402;

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  try {
    const p = join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!p.startsWith(ROOT)) throw 0;
    res.writeHead(200, { 'content-type': MIME[extname(p)] || 'application/octet-stream' });
    res.end(await readFile(p));
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;

const run = (cmd, args) => new Promise((ok, ko) => {
  const p = spawn(cmd, args, { stdio: ['ignore', 'inherit', 'inherit'] });
  p.on('close', c => c === 0 ? ok() : ko(new Error(`${cmd} exited ${c}`)));
});

await rm(FRAMES, { recursive: true, force: true }); await mkdir(FRAMES, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE });
await page.goto(`http://127.0.0.1:${port}/index.html?export=1`);
await page.evaluate(() => window.__ready);
const duration = await page.evaluate(() => window.__duration);
const total = Math.round(duration * FPS);
console.log(`Rendering ${total} frames @${FPS}fps (${W * SCALE}x${H * SCALE})…`);
for (let i = 0; i < total; i++) {
  // last frame is rendered at exactly t = duration so it matches the original artwork
  const t = i === total - 1 ? duration : i / FPS;
  await page.evaluate(t => new Promise(r => { window.__render(t); requestAnimationFrame(() => requestAnimationFrame(r)); }), t);
  await page.screenshot({ path: join(FRAMES, `f${String(i).padStart(4, '0')}.png`), clip: { x: 0, y: 0, width: W, height: H } });
  if (i % 30 === 0) process.stdout.write(`  ${i}/${total}\r`);
}
await browser.close(); server.close();

const mp4 = join(OUT, 'convite-vicente.mp4'), gif = join(OUT, 'convite-vicente.gif');
await run('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', join(FRAMES, 'f%04d.png'),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
  '-movflags', '+faststart', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', mp4]);
await run('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', join(FRAMES, 'f%04d.png'),
  '-vf', `fps=${GIF_FPS},scale=${GIF_W}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle`,
  '-loop', '0', gif]);
await rm(FRAMES, { recursive: true, force: true });
// soundtrack (tools/make_audio.py) → MP4 with sound
const wav = join(ROOT, 'assets', 'audio', 'soundtrack.wav'), mp4s = join(OUT, 'convite-vicente-com-som.mp4');
try {
  await readFile(wav);
  await run('ffmpeg', ['-y', '-loglevel', 'error', '-i', mp4, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', mp4s]);
  console.log(`\nOK:\n  ${mp4}\n  ${mp4s}\n  ${gif}`);
} catch { console.log(`\nOK (sem trilha):\n  ${mp4}\n  ${gif}`); }
