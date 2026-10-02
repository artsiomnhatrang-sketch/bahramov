// Формат 1 «Заблокировали Instagram? Что сделать в первые 10 минут»:
// боль в первую секунду, 3–4 шага, призыв. Тексты — src/texts/blokirovka.mjs.
import { BLOKIROVKA } from '../texts/blokirovka.mjs';
import { STRIP, iso, pick, tail } from './common.mjs';

export function buildBlokirovka(date, n) {
  const T = pick(BLOKIROVKA, n);
  return {
    slug: `${T.key}-${iso(date)}`,
    label: 'Блокировка Instagram',
    strip: STRIP,
    title: T.title,
    description: `${T.hook}\n\nВ ролике: что прочитать в уведомлении, как отличить ограничение, отключение и взлом, ` +
      'почему апелляцию подают один раз.' + tail(T.tags),
    scenes: T.scenes.map((s) => ({ ...s })),
  };
}
