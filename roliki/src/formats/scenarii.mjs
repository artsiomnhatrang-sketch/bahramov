// 13 роликов по youtube/scenarii-shorts.md: --format scenarii --n 0..12 (n = номер сценария − 1).
// Название и описание — из того же файла (scenarii-meta.json); закреп дописан в описание,
// потому что у ролика по расписанию закрепить комментарий нельзя.
import { readFileSync } from 'node:fs';
import { SCENARII } from '../texts/scenarii.mjs';
import { STRIP, pick } from './common.mjs';

const META = JSON.parse(readFileSync(new URL('../texts/scenarii-meta.json', import.meta.url), 'utf8'));

const unwrap = (t) => t.replace(/([^\n])\n(?![\n→#]|Сайт:|Dear|Полная|Артём|Шаблон|Разбор|Инструкция)/g, '$1 ');

export function buildScenarii(date, n) {
  const T = pick(SCENARII, n);
  const M = META.find((m) => m.n === T.n);
  const pinned = M.pinned ? `\n\n${M.pinned.replace(/utm_medium=pinned/g, 'utm_medium=description')}` : '';
  return {
    slug: `sc${String(T.n).padStart(2, '0')}`,
    label: T.label, strip: T.strip ?? STRIP,
    title: T.title ?? M.title,
    // в файле абзацы перенесены по ширине — склеиваем, ссылки и служебные строки оставляем отдельными
    description: unwrap(M.description).replace(/\n\nАртём Бахрамов/, `${unwrap(pinned)}\n\nАртём Бахрамов`),
    scenes: T.scenes.map((s) => ({ ...s })),
  };
}
