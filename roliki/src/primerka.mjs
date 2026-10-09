// Примерка кадров без озвучки (09.10): тайминги и слова берутся из старой папки .work того же ролика,
// кадры в выбранные моменты - в PNG и лист. Быстро проверить вёрстку v3 до полной сборки (голос ~6 мин, лицо ~5 мин).
//   node src/primerka.mjs --format poisk3 --n 4 --work .work/<старая сборка> --out <папка> [--v3] [--fps 3]
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { FORMATS } from './formats/index.mjs';
import { LOOP, planV3 } from './v3.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const args = Object.fromEntries(process.argv.slice(2).join(' ').split('--').filter(Boolean)
  .map((a) => a.trim().split(/\s+/)).map(([k, v]) => [k, v ?? true]));
const V = FORMATS[args.format](new Date(), Number(args.n ?? 0));
const work = join(ROOT, args.work), out = args.out;
mkdirSync(out, { recursive: true });
const dur = (f) => Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());
const words = JSON.parse(readFileSync(join(work, 'words.json'), 'utf8'));
const fileUrl = (p) => pathToFileURL(p.startsWith('/') ? p : join(ROOT, p)).href;
let t = 0;
V.scenes.forEach((s, i) => {
  s.voiceDur = dur(join(work, `s${i}.wav`)); s.dur = s.voiceDur + (s.pad ?? 0.08); s.start = t; t += s.dur;
  s.words = words[i];
  const v = s.vis;
  if (v?.type === 'video') {
    const dir = join(out, `clip${i}`);
    if (!existsSync(join(dir, '0001.jpg'))) {
      mkdirSync(dir, { recursive: true });
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-stream_loop', '-1', '-ss', String(v.from ?? 0.5), '-i', join(ROOT, v.src), '-t', (s.dur + 0.2).toFixed(2),
        '-vf', 'fps=30,scale=968:680:force_original_aspect_ratio=increase,crop=968:680', '-q:v', '4', join(dir, '%04d.jpg')]);
    }
    v.nframes = Number(execFileSync('sh', ['-c', `ls "${dir}" | wc -l`]).toString().trim()); v.frames = pathToFileURL(dir).href;
  } else if (v?.type === 'photo') v.src = fileUrl(v.src);
  for (const p of s.pop ?? []) p.src = fileUrl(p.src);
});
const total = t, V3 = !!args.v3;
if (V3) planV3(V, ROOT);
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(pathToFileURL(join(ROOT, 'src', 'template.html')).href);
await page.evaluate(([v]) => window.init(v), [{ label: V.label, strip: V.strip, scenes: V.scenes, wordSubs: true, lico: true, v3: V3, total, loop: V3 ? LOOP : 0 }]);
await page.evaluate(async () => { await document.fonts.ready; });
const fps = Number(args.fps ?? 3), n = Math.ceil(total * fps);
for (let f = 0; f < n; f++) {
  const tt = Math.min(total - 0.01, f / fps);
  const w = await page.evaluate((x) => window.seek(x), tt); if (w) await w;
  await page.screenshot({ path: join(out, `${String(f).padStart(3, '0')}.jpg`), type: 'jpeg', quality: 80 });
}
await b.close();
execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '1', '-i', join(out, '%03d.jpg'), '-vf', 'scale=216:-1,tile=10x' + Math.ceil(n / 10), '-frames:v', '1', join(out, 'list.jpg')]);
console.log(`примерка: ${n} кадров по ${(1 / fps).toFixed(2)} с, ${total.toFixed(1)} с -> ${join(out, 'list.jpg')}`);
