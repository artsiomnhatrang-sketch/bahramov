// Общее для всех форматов: строка-призыв (видна весь ролик), хвост описания, дата.
export const STRIP = 'Разберу вашу ситуацию в <b>Telegram</b>, ссылка в профиле';
export const TG = 'https://t.me/bahramovartsiom';
export const iso = (date) => date.toISOString().slice(0, 10);
export const tail = (tags, ask = 'разберём вашу ситуацию') =>
  `\n\nНапишите мне в Telegram, ${ask}: ${TG}\nСайт с разборами: https://bahramovai.com\n\n${tags} #shorts`;

// Сцена-призыв в конце: одинаковая по смыслу, текст меняется от ролика к ролику.
export const cta = (head, say, chips) => ({ head, say, vis: { type: 'cta', ...(chips ? { chips } : {}) }, pad: 0.6 });

// Выбор варианта текста: n по кругу.
export const pick = (arr, n) => arr[((n % arr.length) + arr.length) % arr.length];

// Сборщик формата из массива текстов: { key, title, hook, about, tags, scenes } + общие label/strip.
export const makeFormat = (TEXTS, { label, strip = STRIP }) => (date, n) => {
  const T = pick(TEXTS, n);
  return {
    slug: `${T.key}-${iso(date)}`, label: T.label ?? label, strip: T.strip ?? strip, title: T.title,
    description: T.description ?? `${T.hook}\n\n${T.about}` + tail(T.tags, T.ask), // свой текст - когда в ролике один CTA (чеклист 07.10)
    scenes: T.scenes.map((s, i) => ({ ...s, ...(T.media?.[i] ?? {}) })),
    ctaIg: T.ctaIg, stripIg: T.stripIg, capIg: T.capIg, capTt: T.capTt, // 09.10: вторая концовка для Instagram (--cta ig)
  };
};
