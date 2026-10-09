// Монтаж v3 (09.10): расчёт по словам Whisper - акценты, переходы, звуки сцен (planV3) и план кружка с лицом
// (krugPlan). Отдельным модулем, чтобы кадры можно было примерить без озвучки (scripts в scratchpad, render.mjs).
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

export const LOOP = 0.4; // v3: последние 0,4 с ролик сам превращается в свой кадр 0 - повтор без шва

// v3: по словам Whisper - акценты (наезд, тряска, цвет слова, эмодзи), переходы и звуки сцен.
// Акцент сцены - первое слово, совпадающее с её заголовком (мысль кадра), иначе первая цифра.
export function planV3(V, ROOT) {
  const SFX = (n) => join(ROOT, 'zvuki', `${n}.wav`);
  if (!existsSync(SFX('bass'))) execFileSync('python3', [join(ROOT, 'zvuki', 'sint.py')], { stdio: 'inherit' });
  const norm = (w) => w.toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9]/g, '');
  const NUM = /^(\d+|один|одна|одну|одно|два|две|три|четыре|пять|шесть|семь|восемь|девять|десять|сто|тысяч\w*)$/;
  const SHAKE = /^(взлом|угн|угон|удал|навсегд|мошенн|заблок|блокир|отключ|бан$)/;
  const EMOJI = [['❌', /^(мошенн|никому|никогда|нельзя|угн|угон|взлом|удал|фальш|обман)/],
    ['✅', /^(галочк|правильн|безопасн|защит|заверш|официальн)/], ['🔥', /^(сразу|срочно|главн|важн|запомни)/]];
  const ev = [{ t: 0, f: SFX('bass'), v: 0.5, len: 1.3 }]; // удар баса на кадре 0
  const add = (t, n, v, len = 1.0, cut = false) => ev.push({ t, f: SFX(n), v, len, cut });
  const TYPES = ['zoom', 'slide', 'flash'];
  let lastEmoji = -9, prev = null;
  const used = new Set();
  V.scenes.forEach((s, i) => {
    const W = s.words ?? [], cta = s.vis?.type === 'cta', live = s.vis?.type === 'photo' || s.vis?.type === 'video';
    const stems = new Set(s.head.split(/\s+/).map(norm).filter((x) => x.length >= 4).map((x) => x.slice(0, 5)));
    const hit = (w) => { const x = norm(w); return x.length >= 4 && stems.has(x.slice(0, 5)); };
    const fx = { punch: [], shake: [], hl: [], emoji: [] };
    W.forEach((w, k) => {
      const x = norm(w.w), num = NUM.test(x) || /\d/.test(w.w);
      if (hit(w.w) || num || SHAKE.test(x)) fx.hl.push(k);
      if (cta) return;
      if (num) add(s.start + w.s, 'ding', 0.16);
      if (SHAKE.test(x)) fx.shake.push(w.s);
      const em = EMOJI.find(([, re]) => re.test(x));
      const key = em && x.slice(0, 5); // одно и то же слово - эмодзи только в первый раз за ролик
      if (em && i > 0 && !fx.emoji.length && !used.has(key) && s.start + w.s - lastEmoji > 1.5) {
        fx.emoji.push({ at: w.s, e: em[0] }); used.add(key); lastEmoji = s.start + w.s; add(s.start + w.s, 'pop', 0.22, 0.14);
      }
    });
    const acc = W.find((w) => hit(w.w)) ?? W[fx.hl[0]];
    if (acc && !cta) fx.punch.push(acc.s);
    s.fx = fx;
    // переход: раскрытие - вспышка, живая картинка - наезд с размытием, схема - сдвиг; два одинаковых подряд не ставим
    if (i > 0) {
      let tr = s.trans ?? (s.reveal ? 'flash' : live ? 'zoom' : 'slide');
      if (!s.trans && tr === prev) tr = TYPES[(TYPES.indexOf(tr) + 1) % TYPES.length];
      s.trans = prev = tr;
      if (!live) add(s.start, 'click', 0.2, 0.09); // щелчок появления текста; у живых картинок уже «вжух»
    }
    if (s.reveal) add(Math.max(0, s.start - 1.1), 'riser', 0.15, 1.1, true); // нарастание обрывается на раскрытии
    // штампы и тики графики - по тем же временам, что рисует template.html
    const v = s.vis ?? {};
    if (s.stamp) add(s.start + s.stamp.at, 'stamp', 0.35, 0.35);
    if (s.badge) add(s.start + s.badge.at, 'stamp', 0.25, 0.35);
    if (v.type === 'checks') v.items.forEach((_, k) => add(s.start + (v.at ?? 0.2) + k * (v.step ?? 0.32) + 0.12, 'stamp', 0.3, 0.35));
    if (v.type === 'timer') for (let k = 1; k <= v.from; k++) {
      const tt = (v.at ?? 0.25) + k * (v.tick ?? 0.42);
      if (tt < s.dur) add(s.start + tt, 'click', 0.14, 0.09);
    }
  });
  V.sfx3 = ev;
}

// v3: где и какого размера лицо. Крупно (место картинки сцены) на хуке и на сцене с lico:'big', на CTA - крупно над
// кнопкой «Пиши НАВИГАТОР», к последнему кадру снова как в кадре 0. Маленький кружок подпрыгивает на акцентах.
export function krugPlan(V, total, intro) {
  const BIG = [540, 945, 330], SMALL = [850, 1355, 108], CTA = [540, 860, 240];
  const keys = [[0, ...BIG], [intro, ...BIG], [intro + 0.35, ...SMALL]], big = [[0, intro + 0.35]];
  V.scenes.forEach((s, i) => {
    const end = s.start + s.dur;
    // крупно всю фразу: растёт чуть раньше начала, уменьшается уже в следующей сцене
    if (i && s.lico === 'big') { keys.push([s.start - 0.25, ...SMALL], [s.start + 0.05, ...BIG], [end - 0.02, ...BIG], [end + 0.28, ...SMALL]); big.push([s.start - 0.25, end + 0.28]); }
    if (s.vis?.type === 'cta') { keys.push([s.start, ...SMALL], [s.start + 0.35, ...CTA], [total - LOOP, ...CTA], [total, ...BIG]); big.push([s.start, total]); }
  });
  keys.sort((a, b) => a[0] - b[0]);
  const bounce = V.scenes.flatMap((s) => (s.fx?.punch ?? []).map((p) => s.start + p))
    .filter((t) => !big.some(([a, b]) => t > a - 0.1 && t < b + 0.1));
  return { keys, bounce };
}
