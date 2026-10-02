// Общее для всех форматов: строка-призыв (видна весь ролик), хвост описания, дата.
export const STRIP = 'Разберу вашу ситуацию в <b>Telegram</b>, ссылка в профиле';
export const TG = 'https://t.me/bahramovartsiom';
export const iso = (date) => date.toISOString().slice(0, 10);
export const tail = (tags) =>
  `\n\nНапишите мне в Telegram, разберём вашу ситуацию: ${TG}\nСайт с разборами: https://bahramovai.com\n\n${tags} #shorts`;

// Сцена-призыв в конце: одинаковая по смыслу, текст меняется от ролика к ролику.
export const cta = (head, say) => ({ head, say, vis: { type: 'cta' }, pad: 0.6 });

// Выбор варианта текста: n по кругу.
export const pick = (arr, n) => arr[((n % arr.length) + arr.length) % arr.length];
