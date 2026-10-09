// Монтаж v3 (09.10) поверх согласованных сценариев «Поиск»: текст, голос и заголовки те же (poisk.mjs),
// меняются только картинки и эффекты сцен. Сборка: --format poisk3 --n 4 --v3
//   lico: 'big'  - лицо Артёма крупно на этой фразе (одна главная фраза в середине)
//   reveal: true - раскрытие: нарастание звука перед сценой и вспышка на входе
//   stamp / badge - штамп ✕/✓ и плашка-таймер поверх сцены; vis timer / checks / path - графика под тему
import { POISK } from './poisk.mjs';

const L = 'media/lib/', S = 'media/shots/';
const video = (f, tag, o = {}) => ({ type: 'video', src: `${L}${f}.mp4`, from: 1, tag, ...o });
const shot = (f, at = 1.0, dur = 2.2) => ({ src: `${S}${f}.png`, at, dur, w: 940, y: 700, rot: -2, cap: 'bahramovai.com' });

const MEDIA = {
  // №26 «Мошенники взломали телеграмм» - путь в настройках анимированными шагами
  'poisk-3-moshenniki-vzlomali-telegram': {
    8: { pop: [], vis: { type: 'path', at: 0.6, step: 1.6, screens: [
      { t: 'Настройки', rows: ['Мой профиль', 'Устройства', 'Приватность', 'Уведомления'], tap: 1 },
      { t: 'Устройства', rows: ['Этот телефон', 'Активные сеансы', 'Завершить другие сеансы'], tap: 2 }] } },
  },
  // №28 «Мошенники пишут в телеграм» - тестовый ролик монтажа v3
  'poisk-5-moshenniki-pishut': {
    1: { reveal: true, speed: 0.85 },                                       // «Это мошенник.» - медленнее, иначе слышно «машина»
    3: { lico: 'big' },                                                     // «а поддержка сама в личку не пишет»
    4: { vis: { type: 'timer', from: 5, tick: 0.42, at: 0.3, c: 'узнать мошенника', cAt: 0.5 } }, // «за пять секунд, три признака»
    5: { vis: video('v-telefon-00', 'код или пароль'), stamp: { at: 0.75, e: 'x' } },
    6: { vis: video('v-trevoga-02', 'блокировка через час'), badge: { at: 0.85, from: 3599, tick: 0.2, cap: 'до блокировки' } },
    7: { vis: video('v-skroll-02', 'подтвердить аккаунт'), pop: [shot('ps5-a', 1.4, 2.0)] },
    8: { vis: { type: 'checks', at: 0.15, step: 0.34, items: [{ t: 'Просит код или пароль' }, { t: 'Пугает блокировкой' }, { t: 'Зовёт в бота или на сайт' }] } },
  },
};

export const POISK3 = POISK.map((T) => (MEDIA[T.key] ? { ...T, media: MEDIA[T.key] } : T));
