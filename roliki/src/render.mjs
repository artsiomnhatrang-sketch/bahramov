// Сборка ролика: сценарий → озвучка по сценам (edge-tts) → кадры из template.html
// (Playwright) → mp4 1080×1920 (ffmpeg). Токены и деньги не тратит.
//   node src/render.mjs --format blokirovka [--n 0] [--date 2026-10-03] [--voice dmitry|svetlana] [--slug имя]
import { spawn, execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { FORMATS } from './formats/index.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const FPS = 30;
const VOICES = { dmitry: 'ru-RU-DmitryNeural', svetlana: 'ru-RU-SvetlanaNeural' };
const args = Object.fromEntries(process.argv.slice(2).join(' ').split('--').filter(Boolean)
  .map((a) => a.trim().split(/\s+/)).map(([k, v]) => [k, v ?? true]));
const format = args.format ?? 'blokirovka';
const date = args.date ? new Date(`${args.date}T12:00:00`) : new Date();
const n = Number(args.n ?? 0);
const VOICE = VOICES[args.voice ?? process.env.ROLIKI_VOICE ?? 'dmitry'] ?? args.voice;
const RATE = args.rate ?? '+20%';

if (!FORMATS[format]) throw new Error(`Нет формата ${format}. Есть: ${Object.keys(FORMATS).join(', ')}`);
const V = FORMATS[format](date, n);
if (args.slug) V.slug = args.slug;
const work = join(ROOT, '.work', V.slug);
mkdirSync(work, { recursive: true });
mkdirSync(join(ROOT, 'out'), { recursive: true });

const duration = (f) => Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());

// 0. Ударения: весь текст голоса — через udarenia/udarenia.py (свой словарь + ruaccent).
//    Голос читает текст со знаками ударения, субтитры остаются без них.
const acc = JSON.parse(execFileSync('python3', [join(ROOT, 'udarenia', 'udarenia.py'), '--json'],
  { input: JSON.stringify({ items: V.scenes.map((s) => s.say) }), stdio: ['pipe', 'pipe', 'inherit'] }).toString()).items;
writeFileSync(join(work, 'udarenia.txt'), acc.join('\n'));

// edge-tts (особенно Дмитрий) на некоторых фразах молча не отдаёт звук. Тогда повторяем
// с безобидными вариантами: пробел в начале, другая скорость на 1–2 %, без точки в конце.
function tts(text, out) {
  const r = parseInt(RATE, 10);
  const forms = [text, ' ' + text, text.replace(/[.]$/, ''), ' ' + text + ' '];
  const shifts = [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6];
  for (let k = 0; k < shifts.length; k++) {
    const rate = `${r + shifts[k] >= 0 ? '+' : ''}${r + shifts[k]}%`;
    try { execFileSync('edge-tts', ['--voice', VOICE, `--rate=${rate}`, '--text', forms[k % forms.length], '--write-media', out], { stdio: 'ignore' }); return; } catch {}
    execFileSync('sleep', ['1']);
  }
  throw new Error(`edge-tts не озвучил: ${text}`);
}

// 1. Озвучка по сценам — длина сцены = длина голоса + пауза, поэтому всё совпадает.
let t = 0;
V.scenes.forEach((s, i) => {
  const raw = join(work, `s${i}.mp3`);
  s.audio = join(work, `s${i}.wav`);
  tts(acc[i], raw);
  // edge-tts кладёт ~0,2 с тишины в начале и ~0,8 с в конце — срезаем, иначе ролик тянется.
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', raw, '-af',
    'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.06',
    s.audio]);
  s.voiceDur = duration(s.audio);
  s.dur = s.voiceDur + (s.pad ?? 0.08);
  s.start = t; t += s.dur;
});
const total = t;

// 2. Одна звуковая дорожка: каждая сцена добита тишиной до своей длины.
const audio = join(work, 'voice.m4a');
const inputs = V.scenes.flatMap((s) => ['-i', s.audio]);
const filter = V.scenes.map((s, i) => `[${i}:a]apad=whole_dur=${s.dur.toFixed(3)}[a${i}]`).join(';') +
  ';' + V.scenes.map((_, i) => `[a${i}]`).join('') + `concat=n=${V.scenes.length}:v=0:a=1[out]`;
execFileSync('ffmpeg', ['-v', 'error', '-y', ...inputs, '-filter_complex', filter, '-map', '[out]', '-c:a', 'aac', '-b:a', '160k', audio]);

// 3. Кадры → ffmpeg.
const out = join(ROOT, 'out', `${V.slug}.mp4`);
const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-i', audio,
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest',
  '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(ROOT, 'src', 'template.html')).href);
const scenes = V.scenes.map(({ audio: _a, ...s }) => s);
await page.evaluate(([v]) => window.init(v), [{ label: V.label, strip: V.strip, scenes }]);
await page.evaluate(async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map((im) => im.complete ? 0 : new Promise((r) => { im.onload = im.onerror = r; })));
});

const frames = Math.ceil(total * FPS);
const t0 = Date.now();
for (let f = 0; f < frames; f++) {
  await page.evaluate((tt) => window.seek(tt), f / FPS);
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
  if (f % 150 === 0) process.stdout.write(`кадр ${f}/${frames}\r`);
}
ff.stdin.end();
await browser.close();
await new Promise((r, j) => ff.on('close', (c) => (c === 0 ? r() : j(new Error(`ffmpeg ${c}`)))));

writeFileSync(join(ROOT, 'out', `${V.slug}.json`), JSON.stringify({ title: V.title, description: V.description, duration: total, voice: VOICE }, null, 2));
console.log(`\nготово: ${out} · ${total.toFixed(1)} с · ${((Date.now() - t0) / 1000).toFixed(0)} с на кадры`);
