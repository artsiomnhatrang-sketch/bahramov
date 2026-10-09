// Сборка ролика: сценарий → озвучка по сценам (edge-tts) → кадры из template.html
// (Playwright) → mp4 1080×1920 (ffmpeg). Токены и деньги не тратит.
//   node src/render.mjs --format blokirovka [--n 0] [--date 2026-10-03] [--voice artem|aidar|dmitry] [--slug имя]
import { spawn, spawnSync, execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, openSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { FORMATS } from './formats/index.mjs';
import { LOOP, planV3, krugPlan } from './v3.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const FPS = 30;
// Silero (по умолчанию): ударение «+» выполняется всегда. edge-tts — старые голоса, ударения в них ненадёжны.
const SILERO = ['aidar', 'eugene', 'baya', 'xenia', 'kseniya'];
const VOICES = { dmitry: 'ru-RU-DmitryNeural', svetlana: 'ru-RU-SvetlanaNeural' };
// Голос Артёма (с 06.10, по умолчанию): клон ESpeech-TTS по образцу, ударение «+» как у Silero.
// Модель и образцы - вне репозитория (он открыт всем): ~/Developer/golos-artem, см. там say.py и golos.json.
const CLONES = { artem: process.env.ROLIKI_GOLOS_DIR ?? join(homedir(), 'Developer', 'golos-artem') };
const args = Object.fromEntries(process.argv.slice(2).join(' ').split('--').filter(Boolean)
  .map((a) => a.trim().split(/\s+/)).map(([k, v]) => [k, v ?? true]));
const format = args.format ?? 'blokirovka';
const date = args.date ? new Date(`${args.date}T12:00:00`) : new Date();
const n = Number(args.n ?? 0);
const VOICE_ARG = args.voice ?? process.env.ROLIKI_VOICE ?? 'artem';
const IS_SILERO = SILERO.includes(VOICE_ARG);
const IS_CLONE = VOICE_ARG in CLONES;
const PLUS = IS_SILERO || IS_CLONE; // голос понимает «+» перед ударной гласной
const VOICE = IS_SILERO ? VOICE_ARG : VOICES[VOICE_ARG] ?? VOICE_ARG;
const TEMPO = Number(args.tempo ?? (IS_CLONE ? 1.0 : 1.05)); // Silero говорит неторопливо — ускоряем без смены тона; клон говорит в темпе Артёма
const RATE = args.rate ?? '+20%';
// Монтаж v3 (09.10): наезды и тряска на акцентах, цветные слова и эмодзи в субтитрах, звуки (бас, щелчки, дзынь,
// нарастание, ducking), таймер/крестики/галочки, полоска прогресса, разные переходы, лицо крупно на CTA и в середине,
// петля. Стандарт с 09.10 («да» Артёма); --v2 - собрать по-старому.
const V3 = !args.v2;

if (!FORMATS[format]) throw new Error(`Нет формата ${format}. Есть: ${Object.keys(FORMATS).join(', ')}`);
const V = FORMATS[format](date, n);
if (args.slug) V.slug = args.slug;
// 09.10: концовка для Instagram (НАВИГАТОР) вместо основной (комментарий + Telegram) - меняется только последняя сцена
if (args.cta === 'ig') {
  if (!V.ctaIg) throw new Error('у формата нет концовки для Instagram (ctaIg)');
  V.scenes[V.scenes.length - 1] = { ...V.ctaIg };
  if (V.stripIg) V.strip = V.stripIg;
}
const work = join(ROOT, '.work', V.slug);
mkdirSync(work, { recursive: true });
mkdirSync(join(ROOT, 'out'), { recursive: true });

const duration = (f) => Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());

// 0. Ударения: весь текст голоса — через udarenia/udarenia.py (свой словарь + ruaccent).
//    Голос читает текст со знаками ударения, субтитры остаются без них.
const acc = JSON.parse(execFileSync('python3', [join(ROOT, 'udarenia', 'udarenia.py'), '--json', '--strict', ...(PLUS ? [] : ['--edge'])],
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

// Студийная обработка клона (08.10, «голос студийный»): срез гула, мягкая чистка, тело и разборчивость,
// приглушить «с»/«ш», ровная громкость. --raw отключает.
const STUDIO = ',aresample=48000,highpass=f=75,afftdn=nr=6:nf=-50,equalizer=f=160:t=q:w=1:g=1.5,'
  + 'equalizer=f=3200:t=q:w=1.4:g=1.5,deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2';

// 1. Озвучка по сценам — длина сцены = длина голоса + пауза, поэтому всё совпадает.
let t = 0;
if (IS_SILERO) {
  execFileSync('python3', [join(ROOT, 'udarenia', 'silero_tts.py')], { stdio: ['pipe', 'inherit', 'inherit'],
    input: JSON.stringify({ speaker: VOICE, items: acc, out: V.scenes.map((_, i) => join(work, `s${i}.raw.wav`)) }) });
}
if (IS_CLONE) { // ~28 с на фразу на Маке (MPS); фразу с тем же текстом и голосом не озвучиваем заново
  const dir = CLONES[VOICE_ARG];
  const ref = JSON.parse(readFileSync(join(dir, process.env.GOLOS_JSON ?? 'golos.json'), 'utf8')).ref;
  // другой образец голоса = другая озвучка, старая не подхватится. speed у сцены (09.10): короткую фразу клон
  // проглатывает («Это мошенник» Whisper слышал «Это машина») - на 0.85 читается чётко, такие сцены озвучиваются отдельно
  const sp = (i) => V.scenes[i].speed ?? 1;
  const key = (i) => `${VOICE_ARG}|${ref}${sp(i) !== 1 ? `|${sp(i)}` : ''}\n${acc[i]}`;
  const todo = acc.map((_, i) => i).filter((i) => !existsSync(join(work, `s${i}.raw.wav`)) || !existsSync(join(work, `s${i}.key`))
    || readFileSync(join(work, `s${i}.key`), 'utf8') !== key(i));
  for (const speed of [...new Set(todo.map(sp))]) {
    const part = todo.filter((i) => sp(i) === speed);
    execFileSync(join(dir, '.venv', 'bin', 'python'), [join(dir, 'say.py')], { stdio: ['pipe', 'inherit', 'inherit'],
      input: JSON.stringify({ items: part.map((i) => acc[i]), out: part.map((i) => join(work, `s${i}.raw.wav`)), ...(speed !== 1 ? { speed } : {}) }) });
  }
  todo.forEach((i) => writeFileSync(join(work, `s${i}.key`), key(i)));
}
V.scenes.forEach((s, i) => {
  const raw = join(work, PLUS ? `s${i}.raw.wav` : `s${i}.mp3`);
  s.audio = join(work, `s${i}.wav`);
  if (!PLUS) tts(acc[i], raw);
  // edge-tts кладёт ~0,2 с тишины в начале и ~0,8 с в конце — срезаем, иначе ролик тянется.
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', raw, '-af',
    'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.06' + (PLUS && TEMPO !== 1 ? `,atempo=${TEMPO}` : '') + (IS_CLONE && !args.raw ? STUDIO : ''),
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
const sfx = []; // моменты «вжух»: появление живой картинки и всплывающих вставок; громкость 0.12 (08.10: при 0.3 было громко)
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
  if (V3) planV3(V, ROOT);

  // звук: голос (срез гула, компрессия) + музыка тихо под голосом + «вжух» на вставках, громкость -14 LUFS
  const musicName = args.music ?? (n % 2 ? 'v3-violin-aura.mp3' : 'v1-dark-trap-violin.mp3'); // выбор Артёма 05.10: скрипка 1 и 3
  const music = join(ROOT, 'muzyka', musicName);
  // с какой секунды брать трек (у многих тихое вступление) — muzyka/nastroiki.json или --musicFrom
  const MN = JSON.parse(execFileSync('cat', [join(ROOT, 'muzyka', 'nastroiki.json')]).toString());
  const mFrom = Number(args.musicFrom ?? MN[musicName]?.from ?? 0);
  const wh = [join(ROOT, 'zvuki', 'whoosh0.mp3'), join(ROOT, 'zvuki', 'whoosh2.mp3')];
  const mix = join(work, 'mix.m4a');
  // Голос к одной громкости (-18,7 LUFS, как был aidar; под неё подобраны музыка и «вжух»). Клон Артёма
  // выходит на ~4 дБ тише, без выравнивания «вжух» перекрывал голос (жалоба Артёма 06.10).
  const lufs = Number(/I:\s+(-?[\d.]+) LUFS/.exec(spawnSync('ffmpeg', ['-v', 'info', '-i', audio, '-af', 'ebur128', '-f', 'null', '-'],
    { encoding: 'utf8' }).stderr.split('Summary:').pop())?.[1] ?? -18.7);
  const voiceGain = Math.max(-12, Math.min(12, -18.7 - lufs)).toFixed(1);
  // события звука: «вжух» (как в v2) + в v3 бас, щелчки, дзынь, нарастание, штампы, поп (planV3 -> V.sfx3)
  const ev = [...sfx.map((t, k) => ({ t: t - 0.08, f: wh[k % 2], v: Number(args.sfxVol ?? 0.12), len: 1.0 })), ...(V.sfx3 ?? [])]
    .filter((e) => e.t < total - 0.05);
  const ins = ['-i', audio, '-stream_loop', '-1', '-i', music, ...ev.flatMap((e) => ['-i', e.f])];
  // v3: музыка с первого кадра (без медленного вступления), под голосом приглушается (ducking), в паузах громче;
  // в конце короткий спад - ролик зациклен, конец переходит в начало
  const [mVol, fIn, fOut] = V3 ? [args.musicVol ?? 0.3, 0.03, 0.35] : [args.musicVol ?? 0.2, 0.6, 1.2];
  const f = [`[0:a]volume=${voiceGain}dB,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=1.6${V3 ? ',aformat=channel_layouts=stereo,asplit=2[vo][vk]' : '[vo]'}`, // v3: стерео (раньше всё сводилось в моно)
    // музыка: с нужного места, громкость выровнена (треки бывают от -8 до -25 дБ), затем тихо под голос
    `[1:a]atrim=start=${mFrom}:duration=${(total + 0.5).toFixed(2)},asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-2,aresample=48000,volume=${mVol},afade=t=in:d=${fIn},afade=t=out:st=${(total - fOut).toFixed(2)}:d=${fOut}${V3 ? '[m0]' : '[mu]'}`,
    ...(V3 ? ['[m0][vk]sidechaincompress=threshold=0.02:ratio=5:attack=12:release=300:makeup=1[mu]'] : []),
    ...ev.map((e, k) => `[${k + 2}:a]aformat=channel_layouts=stereo,aresample=48000,atrim=0:${e.len},afade=t=out:st=${Math.max(0, e.len - (e.cut ? 0.02 : 0.3)).toFixed(2)}:d=${e.cut ? 0.02 : 0.3},volume=${e.v},adelay=${Math.max(0, Math.round(e.t * 1000))}:all=1[x${k}]`),
    `[vo][mu]${ev.map((_, k) => `[x${k}]`).join('')}amix=inputs=${ev.length + 2}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[m]`];
  execFileSync('ffmpeg', ['-v', 'error', '-y', ...ins, '-filter_complex', f.join(';'), '-map', '[m]', '-t', total.toFixed(2),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', mix]);
  V.mix = mix;
}

// 3. Кадры → ffmpeg.
const out = join(ROOT, 'out', `${V.slug}.mp4`);
const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-i', V.mix ?? audio,
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest',
  '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
// ждать закрытия ffmpeg подписываемся сразу: если он закроется раньше, чем дойдём до await, событие не потеряется (08.10)
const ffDone = new Promise((r, j) => ff.on('close', (c) => (c === 0 ? r() : j(new Error(`ffmpeg ${c}`)))));

// 3а. Кружок с лицом Артёма (08.10). Губы под голос рисует MuseTalk вне репозитория
//     (~/Developer/lico-artem, лицо в открытый репозиторий не кладём), параллельно кадрам.
const LICO_DIR = process.env.ROLIKI_LICO_DIR ?? join(homedir(), 'Developer', 'lico-artem');
const licoOut = join(work, 'lico.mp4');
// тот же голос и то же лицо = готовое видео лица из прошлой сборки (губы рисуются ~5 мин)
// По умолчанию у голоса Артёма кружок с лицом (09.10): artem3 (IMG_4681) и artem4 (IMG_4682) по очереди, как музыка -
// чётный n artem3, нечётный artem4. Старое artem (IMG_4658, 08.10) - запасное, только --lico artem. --lico none - без кружка.
const LICO = args.lico === 'none' ? null : typeof args.lico === 'string' ? args.lico : (args.lico || IS_CLONE) ? (n % 2 ? 'artem4' : 'artem3') : null;
const licoKey = LICO ? `${LICO}\n${createHash('md5').update(readFileSync(audio)).digest('hex')}` : '';
const licoCached = LICO && existsSync(licoOut) && existsSync(join(work, 'lico.key')) && readFileSync(join(work, 'lico.key'), 'utf8') === licoKey;
const licoDone = licoCached ? Promise.resolve() : LICO ? new Promise((r, j) => spawn(join(LICO_DIR, '.venv', 'bin', 'python'),
  [join(LICO_DIR, 'govori.py'), audio, licoOut, LICO], { stdio: ['ignore', 'ignore', openSync(join(work, 'lico.log'), 'w')] })
  .on('close', (c) => (c === 0 ? (writeFileSync(join(work, 'lico.key'), licoKey), r()) : j(new Error(`лицо не собрано (код ${c}), см. ${join(work, 'lico.log')}`))))) : null;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(ROOT, 'src', 'template.html')).href);
const scenes = V.scenes.map(({ audio: _a, ...s }) => s);
await page.evaluate(([v]) => window.init(v), [{ label: V.label, strip: V.strip, scenes, wordSubs: V2, lico: !!LICO, v3: V3, total, loop: V3 ? LOOP : 0 }]);
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
await ffDone;
if (licoDone) {
  console.log('\nждём лицо (MuseTalk)…');
  await licoDone;
  // хук: лицо крупно всю первую фразу, кроме ~0,7 с в конце - на последних словах уходит в кружок и открывает картинку
  const intro = Math.max(1.5, V.scenes[0].dur - 0.7);
  // v3: план кружка - крупно на хуке, на сцене с lico:'big' в середине и на CTA, к последнему кадру снова как в кадре 0
  // (петля); на акцентах маленький кружок подпрыгивает
  const plan = V3 ? join(work, 'krug-plan.json') : null;
  if (plan) writeFileSync(plan, JSON.stringify(krugPlan(V, total, intro)));
  execFileSync('python3', [join(ROOT, 'src', 'krug.py'), out, licoOut, join(work, 'krug.mp4'), '--intro', intro.toFixed(2),
    ...(plan ? ['--plan', plan] : [])], { stdio: 'inherit' });
  renameSync(join(work, 'krug.mp4'), out);
}

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
