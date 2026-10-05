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
// Silero (по умолчанию): ударение «+» выполняется всегда. edge-tts — старые голоса, ударения в них ненадёжны.
const SILERO = ['aidar', 'eugene', 'baya', 'xenia', 'kseniya'];
const VOICES = { dmitry: 'ru-RU-DmitryNeural', svetlana: 'ru-RU-SvetlanaNeural' };
const args = Object.fromEntries(process.argv.slice(2).join(' ').split('--').filter(Boolean)
  .map((a) => a.trim().split(/\s+/)).map(([k, v]) => [k, v ?? true]));
const format = args.format ?? 'blokirovka';
const date = args.date ? new Date(`${args.date}T12:00:00`) : new Date();
const n = Number(args.n ?? 0);
const VOICE_ARG = args.voice ?? process.env.ROLIKI_VOICE ?? 'aidar';
const IS_SILERO = SILERO.includes(VOICE_ARG);
const VOICE = IS_SILERO ? VOICE_ARG : VOICES[VOICE_ARG] ?? VOICE_ARG;
const TEMPO = Number(args.tempo ?? 1.05); // Silero говорит неторопливо — ускоряем без смены тона
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
const acc = JSON.parse(execFileSync('python3', [join(ROOT, 'udarenia', 'udarenia.py'), '--json', '--strict', ...(IS_SILERO ? [] : ['--edge'])],
  { input: JSON.stringify({ items: V.scenes.map((s) => s.say) }), stdio: ['pipe', 'pipe', 'inherit'] }).toString()).items;
writeFileSync(join(work, 'udarenia.txt'), acc.join('\n'));
writeFileSync(join(work, 'scenes.json'), JSON.stringify(V.scenes.map((s) => s.say)));

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
if (IS_SILERO) {
  execFileSync('python3', [join(ROOT, 'udarenia', 'silero_tts.py')], { stdio: ['pipe', 'inherit', 'inherit'],
    input: JSON.stringify({ speaker: VOICE, items: acc, out: V.scenes.map((_, i) => join(work, `s${i}.raw.wav`)) }) });
}
V.scenes.forEach((s, i) => {
  const raw = join(work, IS_SILERO ? `s${i}.raw.wav` : `s${i}.mp3`);
  s.audio = join(work, `s${i}.wav`);
  if (!IS_SILERO) tts(acc[i], raw);
  // edge-tts кладёт ~0,2 с тишины в начале и ~0,8 с в конце — срезаем, иначе ролик тянется.
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', raw, '-af',
    'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.06' + (IS_SILERO ? `,atempo=${TEMPO}` : ''),
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

// 2б. Монтаж v2 (04.10): медиа сцен, кадры видео, слова субтитров, музыка и звуки.
const V2 = V.scenes.some((s) => s.vis?.type === 'photo' || s.vis?.type === 'video' || s.pop);
const fileUrl = (p) => pathToFileURL(p.startsWith('/') ? p : join(ROOT, p)).href;
const sfx = []; // моменты «вжух»: появление живой картинки и всплывающих вставок
if (V2) {
  V.scenes.forEach((s, i) => {
    const v = s.vis;
    if (v && (v.type === 'photo' || v.type === 'video')) {
      sfx.push(s.start);
      if (v.type === 'video') {
        // кадры клипа под длину сцены: 30 к/с, обрезка под карточку или весь кадр, по кругу если клип короче
        const dir = join(work, `clip${i}`);
        mkdirSync(dir, { recursive: true });
        const [w, h] = v.full ? [1080, 1920] : [968, 680];
        execFileSync('ffmpeg', ['-v', 'error', '-y', '-stream_loop', '-1', '-ss', String(v.from ?? 0.5), '-i', join(ROOT, v.src),
          '-t', (s.dur + 0.2).toFixed(2), '-vf', `fps=${FPS},scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h}`,
          '-q:v', '3', join(dir, '%04d.jpg')]);
        v.nframes = Number(execFileSync('sh', ['-c', `ls "${dir}" | wc -l`]).toString().trim());
        v.frames = pathToFileURL(dir).href;
      } else v.src = fileUrl(v.src);
    }
    for (const p of s.pop ?? []) { p.src = fileUrl(p.src); sfx.push(s.start + (p.at ?? 0.6)); }
  });
  // субтитры по слову: Whisper small даёт время каждого слова
  const words = JSON.parse((() => {
    execFileSync('python3', [join(ROOT, 'udarenia', 'slova.py'), work],
      { input: JSON.stringify(V.scenes.map((s) => s.sub ?? s.say)), stdio: ['pipe', 'inherit', 'inherit'] });
    return execFileSync('cat', [join(work, 'words.json')]).toString();
  })());
  V.scenes.forEach((s, i) => { s.words = words[i]; });

  // звук: голос (срез гула, компрессия) + музыка тихо под голосом + «вжух» на вставках, громкость -14 LUFS
  const musicName = args.music ?? (n % 2 ? 'v3-violin-aura.mp3' : 'v1-dark-trap-violin.mp3'); // выбор Артёма 05.10: скрипка 1 и 3
  const music = join(ROOT, 'muzyka', musicName);
  // с какой секунды брать трек (у многих тихое вступление) — muzyka/nastroiki.json или --musicFrom
  const MN = JSON.parse(execFileSync('cat', [join(ROOT, 'muzyka', 'nastroiki.json')]).toString());
  const mFrom = Number(args.musicFrom ?? MN[musicName]?.from ?? 0);
  const wh = [join(ROOT, 'zvuki', 'whoosh0.mp3'), join(ROOT, 'zvuki', 'whoosh2.mp3')];
  const mix = join(work, 'mix.m4a');
  const ins = ['-i', audio, '-stream_loop', '-1', '-i', music, ...sfx.flatMap((_, k) => ['-i', wh[k % 2]])];
  const f = [`[0:a]highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=1.6[vo]`,
    // музыка: с нужного места, громкость выровнена (треки бывают от -8 до -25 дБ), затем тихо под голос
    `[1:a]atrim=start=${mFrom}:duration=${(total + 0.5).toFixed(2)},asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-2,aresample=48000,volume=${args.musicVol ?? 0.2},afade=t=in:d=0.6,afade=t=out:st=${(total - 1.2).toFixed(2)}:d=1.2[mu]`,
    ...sfx.map((t, k) => `[${k + 2}:a]atrim=0:1.0,afade=t=out:st=0.7:d=0.3,volume=0.45,adelay=${Math.max(0, Math.round((t - 0.08) * 1000))}:all=1[x${k}]`),
    `[vo][mu]${sfx.map((_, k) => `[x${k}]`).join('')}amix=inputs=${sfx.length + 2}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[m]`];
  execFileSync('ffmpeg', ['-v', 'error', '-y', ...ins, '-filter_complex', f.join(';'), '-map', '[m]', '-t', total.toFixed(2),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', mix]);
  V.mix = mix;
}

// 3. Кадры → ffmpeg.
const out = join(ROOT, 'out', `${V.slug}.mp4`);
const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-i', V.mix ?? audio,
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest',
  '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(ROOT, 'src', 'template.html')).href);
const scenes = V.scenes.map(({ audio: _a, ...s }) => s);
await page.evaluate(([v]) => window.init(v), [{ label: V.label, strip: V.strip, scenes, wordSubs: V2 }]);
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

// 4. Сверка голоса с текстом (Whisper). Расхождения — ролик не отдавать, пока не разобраны.
try { execFileSync('python3', [join(ROOT, 'udarenia', 'sverka.py'), work], { stdio: 'inherit' }); }
catch { console.log('ВНИМАНИЕ: голос расходится с текстом, см. выше'); process.exitCode = 4; }

// 5. --export: готовый ролик (сверка чистая) + подпись кладём в ~/Downloads/Ролики bahramovai/
//    Оттуда Артём берёт ролики для Instagram; в корень «Загрузок» ничего не класть.
if (args.export && !process.exitCode) {
  const { copyFileSync } = await import('node:fs');
  const { homedir } = await import('node:os');
  const dir = join(homedir(), 'Downloads', 'Ролики bahramovai');
  mkdirSync(dir, { recursive: true });
  const name = typeof args.export === 'string' ? args.export : V.slug;
  copyFileSync(out, join(dir, `${name}.mp4`));
  writeFileSync(join(dir, `${name}.txt`), `НАЗВАНИЕ:\n${V.title}\n\nОПИСАНИЕ / ПОДПИСЬ:\n${V.description}\n`);
  console.log(`в папке «Ролики bahramovai»: ${name}.mp4 + ${name}.txt`);
}
