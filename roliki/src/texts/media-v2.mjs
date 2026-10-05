// Монтаж v2 (04.10): какие живые картинки стоят в сценах роликов. Тексты сцен не меняются —
// здесь только замены картинки (vis) и всплывающие вставки (pop) по номеру сцены.
// Библиотека: media/lib (Pixabay, отобрано вручную), скриншоты статей: media/shots (media/shots.sh).
const L = 'media/lib/', S = 'media/shots/';

// живая картинка крупной карточкой: фото или видео; tag — плашка в углу, joke — надпись поверх
const P = (f, tag, o = {}) => ({ vis: { type: 'photo', src: `${L}${f}.jpg`, tag, ...o } });
const V = (f, tag, o = {}) => ({ vis: { type: 'video', src: `${L}${f}.mp4`, tag, from: 1, ...o } });
// всплывающий скриншот статьи и маленькое фото в правом верхнем углу
const shot = (id, at = 1.4) => ({ src: `${S}${id}.png`, at, dur: 2.4, w: 940, y: 690, rot: 2, cap: 'bahramovai.com' });
const mini = (f, at = 1.2) => ({ src: `${L}${f}.jpg`, at, dur: 1.7, w: 260, x: 760, y: 545, rot: 5 });
const pop = (...p) => ({ pop: p });
const both = (a, b) => ({ ...a, ...b });

// scenarii: номер сценария → { номер сцены: замена }
export const MEDIA_SCENARII = {
  2: { 0: V('v-trevoga-05', null, { joke: 'Не удаётся войти' }), 1: pop(mini('trevoga-01', 2.0)),
    2: P('noutbuk-04', 'забыли пароль'), 3: V('v-haker-06', 'внутри чужой'), 4: pop(shot('sc02-a', 1.6)),
    5: P('zamok-02', 'ограничила платформа'), 6: pop(shot('sc02-b', 1.8)), 7: pop(mini('haker-00', 0.9)) },
  3: { 0: V('v-trevoga-02', null, { joke: 'Номер недоступен' }), 1: pop(mini('shok-03', 1.0)),
    2: pop(mini('trevoga-03', 2.0)), 3: both(P('biznes-00', 'к оператору'), pop(shot('sc03-a', 1.3))),
    4: V('v-haker-06', 'сначала номер', { from: 6 }), 5: pop(shot('sc03-b', 1.8)) },
  4: { 0: V('v-haker-00', null, { joke: 'Кто-то вошёл в ваш аккаунт' }), 1: pop(mini('bloger-08', 1.0)),
    2: both(P('noutbuk-00', 'поддержка, админы, боты'), pop(shot('sc04-a', 1.8))), 3: pop(mini('shok-09', 1.0)),
    4: V('v-radost-06', 'утром аккаунт вернули'), 5: pop(shot('sc04-b', 2.0)), 6: pop(mini('trevoga-03', 1.6)) },
  5: { 0: V('v-radost-09', 'доступ вернули'), 1: pop(shot('sc05-a', 1.0)), 2: pop(mini('noch-05', 0.9)),
    3: V('v-skroll-00', 'завершить сеансы'), 4: P('zamok-00', 'свой облачный пароль'), 5: pop(shot('sc05-b', 1.6)),
    6: pop(mini('trevoga-09', 0.9)) },
  6: { 0: V('v-zlost-10', null, { joke: 'Аккаунт отключён' }), 1: pop(shot('sc06-a', 0.9)),
    2: P('shok-03', 'ограничили аккаунт'), 3: P('noutbuk-09', 'подтвердите личность'), 4: pop(mini('shok-09', 1.0)),
    5: V('v-stress-10', 'обжаловать везде подряд'), 6: pop(shot('sc06-b', 2.0)) },
  7: { 0: V('v-trevoga-09', null, { joke: 'Отключён навсегда' }), 1: pop(mini('radost-11', 1.0)),
    2: P('noutbuk-08', 'ошибка автоматики'), 3: pop(shot('sc07-a', 1.4)), 4: V('v-skroll-02', 'текст и письмо'),
    5: pop(shot('sc07-b', 1.5)), 6: P('biznes-07', 'ваша аудитория') },
  8: { 0: V('v-stress-03', null, { joke: 'Аккаунт отключён' }), 1: V('v-skroll-11', 'скриншоты всех экранов'),
    2: pop(shot('sc08-b', 0.9)), 3: P('noutbuk-00', 'почта и спам'), 4: pop(mini('biznes-03', 1.6)),
    5: pop(shot('sc08-a', 1.3)) },
  9: { 0: V('v-trevoga-11', null, { full: true, joke: 'Код не приходит' }), 1: P('trevoga-03', 'почта и спам'),
    2: pop(shot('sc09-a', 1.6)), 3: both(V('v-haker-06', 'код уходит чужому', { from: 10 }), pop(shot('sc09-b', 0.9))),
    4: pop(mini('shok-07', 1.0)), 5: P('noch-07', 'ссылка действует недолго'), 6: pop(mini('zlost-01', 1.4)) },
  10: { 0: V('v-haker-09', null, { full: true, joke: 'Пароль не подходит' }), 1: pop(shot('sc10-a', 0.6)),
    2: pop(mini('shok-11', 1.4)), 3: pop(shot('sc10-b', 1.3)), 4: both(P('haker-04', 'чужой аватар'), pop(mini('trevoga-01', 2.6))),
    5: pop(mini('haker-02', 1.0)), 6: P('radost-04', 'восстановление доступа') },
  11: { 0: V('v-stress-10', null, { joke: 'Сообщение не доставлено', from: 4 }), 1: P('shok-07', 'дело не в телефоне'),
    2: pop(shot('sc11-a', 1.5)), 3: pop(mini('biznes-03', 1.2)), 4: V('v-zlost-08', 'клиент ушёл к другим'),
    5: pop(shot('sc11-b', 1.2)) },
  12: { 0: P('biznes-03', 'всё в ватсапе'), 1: V('v-stress-04', 'опасно', { from: 4 }), 2: pop(mini('shok-00', 1.2)),
    3: pop(shot('sc12-a', 1.3)), 4: P('noutbuk-09', 'выгрузить контакты'), 5: pop(shot('sc12-b', 1.5)),
    6: P('radost-02', 'клиенты с вами') },
  13: { 0: V('v-trevoga-02', null, { joke: 'Вы не можете писать', from: 6 }), 1: pop(mini('radost-08', 1.0)),
    2: pop(shot('sc13-a', 1.4)), 3: V('v-skroll-02', 'срок ограничения', { from: 6 }), 4: P('noutbuk-08', 'кнопка оспорить'),
    5: pop(shot('sc13-b', 1.5)), 6: P('zlost-06', 'на английском, с номером'), 7: pop(mini('haker-00', 1.0)),
    8: V('v-haker-06', 'посредников нет', { from: 14 }) },
  // 14-20 (05.10): новые темы, кадр 0 - живое видео с текстом уведомления
  14: { 0: V('v-nerv-04', null, { joke: 'Нарушение правил сообщества' }), 1: pop(mini('razdr-03', 1.2)),
    2: P('razdr-00', 'решает автоматика'), 3: pop(shot('sc14-a', 1.5)), 4: V('v-telefon-04', 'тот же телефон'),
    5: pop(mini('pishet-07', 1.4)), 6: P('pishet-02', 'конкретно, без шаблона'), 7: pop(shot('sc14-b', 1.2)),
    8: P('razdr-02', 'связей в Meta нет') },
  15: { 0: V('v-nerv-10', null, { joke: 'Your account has been disabled' }), 1: pop(mini('razdr-09', 1.3)),
    2: V('v-telefon-00', 'экран блокировки'), 3: pop(shot('sc15-a', 1.2)), 4: P('pishet-10', 'через Facebook'),
    5: pop(mini('biznes-03', 1.2)), 6: P('pishet-09', 'спокойно и по делу'), 7: pop(shot('sc15-b', 1.0)),
    8: P('noch-07', 'от суток до 3 недель') },
  16: { 0: V('v-nerv-02', null, { joke: 'Аккаунт заблокирован' }), 1: pop(mini('dva-09', 1.0)),
    2: P('dva-04', 'связанная сеть'), 3: pop(mini('shok-03', 1.6)), 4: V('v-telefon-07', 'один телефон на всех'),
    5: pop(shot('sc16-a', 1.4)), 6: P('razdr-01', '4 из 5 за ночь'), 7: pop(shot('sc16-b', 0.9)),
    8: P('razdr-03', 'не разгонять активность') },
  17: { 0: V('v-stress-03', null, { joke: 'Нарушение целостности аккаунта' }), 1: pop(shot('sc17-a', 1.2)),
    2: P('razdr-09', 'удалять нечего'), 3: pop(mini('noutbuk-02', 1.2)), 4: V('v-skroll-02', 'сетка профилей', { from: 4 }),
    5: pop(shot('sc17-b', 1.0)), 6: P('reg-10', 'один главный аккаунт'), 7: pop(mini('dva-06', 1.2)),
    8: P('radost-11', 'видеоселфи - хороший знак') },
  18: { 0: V('v-telefon-04', null, { joke: 'Создать новый аккаунт' }), 1: pop(mini('reg-01', 1.0)),
    2: both(P('reg-02', 'почта вместо номера'), pop({ src: `${S}reg-01-phone.png`, at: 1.0, dur: 2.2, w: 600, y: 700, rot: -2, cap: 'instagram.com' })),
    3: pop({ src: `${S}reg-02-email.png`, at: 0.8, dur: 2.4, w: 600, y: 700, rot: 2, cap: 'instagram.com' }),
    4: P('pishet-07', 'настоящая дата рождения'), 5: pop(mini('razdr-00', 1.3)), 6: both(P('reg-04', 'создать и выйти'), pop(shot('sc18-a', 2.0))),
    7: pop(shot('sc18-b', 1.0)) },
  19: { 0: V('v-trevoga-11', null, { full: true, joke: 'Создание учётной записи заблокировано' }), 1: pop(shot('sc19-a', 1.4)),
    2: P('razdr-02', 'телефон, где был бан'), 3: pop(mini('haker-01', 1.4)), 4: V('v-nerv-04', '5 попыток за вечер', { from: 3 }),
    5: pop(shot('sc19-b', 0.8)), 6: P('dva-04', 'другой телефон'), 7: pop(mini('zamok-03', 1.0)),
    8: P('reg-10', 'пауза в несколько дней') },
  20: { 0: V('v-telefon-07', null, { joke: 'Личный и рабочий. Заблокируют?' }), 1: pop(shot('sc20-a', 0.6)),
    2: P('dva-09', 'до 5 аккаунтов'), 3: pop(mini('razdr-03', 1.4)), 4: P('dva-06', 'соавторство'),
    5: pop(mini('pishet-10', 1.2)), 6: both(P('razdr-01', 'по 20 раз в час'), pop(shot('sc20-b', 1.6))),
    7: P('pishet-02', 'сессии по 30-40 минут') },
};

// формат avtomatizaciya (ролик 03)
export const MEDIA_AVTO = {
  0: V('v-stress-04', null, { joke: 'Сколько стоит? Сколько стоит?' }), 1: pop(mini('zlost-01', 1.4)),
  2: P('noch-05', 'вопрос в 23:40'), 3: pop(mini('bloger-00', 1.4)), 4: V('v-skroll-00', 'бот пишет в директ', { from: 5 }),
  5: pop(shot('avto-b', 0.9)), 6: both(P('radost-11', 'бот отвечает 24/7'), pop(mini('radost-02', 2.8))), 7: pop(shot('avto-a', 1.0)),
  8: P('biznes-03', 'пару раз в неделю'),
};

// применить замены к сценам
export const applyMedia = (scenes, M) => scenes.map((s, i) => (M?.[i] ? { ...s, ...M[i] } : s));
