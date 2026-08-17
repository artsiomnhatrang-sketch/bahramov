# BahramovAI — контекст проекта для Claude Code

## ЦЕЛЬ проекта
SEO + GEO видимость bahramovai.com: ранжироваться в Google и Яндекс по запросам
про AI-агентов и автоматизацию соцсетей. Попадать в ответы нейросетей
(ChatGPT, Perplexity, Gemini, Claude) на вопросы об Артёме Бахраме и его услугах.
Стратегия: экспертный контент с реальными цифрами, тематические кластеры,
JSON-LD, внутренняя перелинковка, регулярный постинг на vc.ru/LinkedIn/Telegram/YouTube.

## СДЕЛАНО
- 33 статьи в блоге (тематические кластеры: AI-агенты, Instagram-блокировки, Telegram, мессенджеры, автоматизация)
- about.html — страница "Обо мне" с JSON-LD Person + FAQPage
- FAQ-секция на главной (index.html) с FAQPage JSON-LD
- BreadcrumbList JSON-LD добавлен во все 27 статей блога
- Внутренняя перелинковка: 41 контекстная ссылка между статьями
- llms.txt расширен: услуги, цены, кейсы
- Яндекс.Вебмастер: сайт добавлен и подтверждён в аккаунте artsiomnhatrang@gmail.com
  (user_id 2361319964, host_id `https:bahramovai.com:443`) — 17.08.2026 через API.
  Подтверждение прошло по META_TAG в index.html (`yandex-verification`), HTML_FILE
  дважды падал с PAGE_UNAVAILABLE — робот Яндекса не достучался до GitHub Pages,
  хотя файл отдавался 200. Мета-тег и файл yandex_9f34d5d30546d08a.html не удалять.
  Старый файл yandex_4569c44e850f20f1.html — от другого аккаунта, оставлен как есть
- Google Search Console подключён
- Внешние публикации: 3 живых материала (vc.ru ×2, Т-Бизнес секреты) — все залинкованы на about.html в секции «Публикации». Статья на Sostav удалена изданием (404), из списка живых исключена
- YouTube Short опубликован
- scripts/check-stat-cards.py + интеграция в publish-article.sh (pre-publish автопроверка)
- photo.webp подключён в about.html через <picture> (экономия 54 КБ / -29% для современных браузеров)
- 07.07.2026: статья №25 (instagram-celostnost-akkaunta-2026.html) дополнена — новый H2 «Боты и массовые рассылки», новый пошаговый H2 «Если вы уже в круге банов — как выйти по шагам» (9 шагов), абзац про смену среды в 2024–2025, кросс-линк на №26 (povtornaya-blokirovka) в теле + 4-я карточка «Читайте также». Новый файл НЕ создавался, счётчик статей и index.html не менялись.
- 07.07.2026: №25 — редакторская вычитка (дедуп интро, уточнение Account Integrity, убран CIB-англицизм и self-impersonation, формулировки апелляции/сервисов, сведён повтор про поведение после разбана, meta-description×3, dateModified, время чтения 10 мин).
- 13.08.2026: техническая SEO-сессия (без новых статей):
  - **Обратные ссылки на hub**: во все 15 статей кластера «Блокировки Instagram» добавлен блок-указатель `<div data-hub-link>` со ссылкой на статью №37. Было: у хаба 1 входящая внутренняя ссылка (только из листинга). Стало: 16. Блок вставлен в начало тела статьи, стили inline (в `<style>` статей не лезли). Атрибут `data-hub-link` — маркер идемпотентности, по нему же блок можно найти/массово поправить.
  - **RSS-фид** `/feed.xml` (25 последних статей) + `<link rel="alternate">` во всех 44 страницах. Генерится `scripts/seo-sync.py` из JSON-LD статей; вызов встроен в publish-article.sh.
  - **404.html** — кастомная страница ошибки в дизайне сайта (GitHub Pages подхватывает автоматически), noindex, 4 карточки популярных статей. Canonical намеренно отсутствует.
  - **index.html**: секция «Свежее в блоге» (4 карточки, 2×2 на десктопе, 1 колонка на мобиле) перед FAQ. До этого с главной не было ни одной ссылки на конкретные статьи.
  - **llms.txt**: hub-статья добавлена первой в раздел «Блокировки» с пометкой «начинать с неё» + RSS в контактах.
  - **publish-article.sh**: убраны мёртвые sitemap-ping'и Google и Bing (Google отключил ping в июне 2023), IndexNow теперь пингует статью + листинг блога, в конце печатается прямая ссылка на «Проверку URL» в Search Console.
  - **sitemap.xml**: lastmod обновлён ТОЛЬКО у 15 статей с реальной правкой контента. Осознанно не трогали lastmod у страниц, где менялся только `<head>` — иначе ложный сигнал свежести по всему сайту.

## Внешние публикации (выполнено)
Все живые материалы залинкованы на about.html в секции «Публикации» (карточки .link-card).
- vc.ru — «AI-агент заменил 3 менеджеров»: https://vc.ru/marketing/2888231-kak-ai-agent-zamenil-3-menedzherov
- vc.ru — «Массовые блокировки Instagram в мае 2026»: https://vc.ru/marketing/2918649-massovye-blokirovki-instagram-v-mae-2026
- Т-Бизнес секреты (медиа Т-Банка), 14.07.2026 — «Геймификация в премиум-нише: кейс роста архитектора без рекламы»: https://secrets.tbank.ru/blogi-kompanij/gejmifikaciya-v-premium-nishe/ — кейс клиента @eldarmurakov, редакция сменила заголовок (ждали «Как архитектор набрал 7000 подписчиков за неделю без рекламы»). Осталось: анонс в @artsiombahram через scripts/post-to-telegram.sh.
- ❌ Sostav — «AI-агент vs чат-бот» (https://www.sostav.ru/blogs/291225/90685): УДАЛЕНА изданием, 404, блог автора на Sostav пуст — восстановлению не подлежит (проверено 17.07.2026). На about.html не добавлялась; битая ссылка убрана из blog/7-signs-you-need-ai-agent.html 17.07.2026 — заменена на внутреннюю на /blog/ai-agent-vs-chatbot-2026.html (та же тема), упоминание Sostav из текста убрано. Задача закрыта, действий не требует.

## TODO (приоритизировано)
1. Оптимизация изображений (частично сделано):
   ✅ photo.webp подключён в about.html через <picture> (20 мая)
   ⏸ photo.jpg (188 КБ) — НЕ сжимать через sips, файл уже оптимизирован (проверено: sips -s formatOptions 80 увеличивает размер до 248 КБ). Для дальнейшего сжатия нужен cwebp/jpegoptim через Homebrew (Homebrew не установлен).
   ✅ hero-cyborg.png — убран из репо 13.08.2026 (в .gitignore), файл остался локально на диске
2. Привязать YouTube канал к artsiomnhatrang@gmail.com для связки с Google Search Console
3. Проверить FAQPage в Rich Results (через search.google.com/test/rich-results) — через 2-3 дня после публикации
4. Следующие статьи (кандидаты, проверять на дубль перед написанием):
   - ✅ СДЕЛАНО 12.08.2026: Полное руководство по блокировкам Instagram 2026 — hub-страница кластера (статья №37)
   - AI-агент для Instagram и мессенджеров: автоматизация без бана
5. Продолжить дистрибуцию: vc.ru, LinkedIn, Telegram-канал, YouTube Shorts

## Кто владелец
- Имя: Артём Бахрам (Artsiom Bahram / Артём Бахрамов)
- Роль: AI-стратег, эксперт по автоматизации соцсетей
- Локация: Нячанг, Вьетнам
- Email: artsiomnhatrang@gmail.com
- Telegram: @bahramovartsiom
- YouTube: **@bahramovai** — рабочий канал, только его указывать в sameAs/llms.txt/разметке.
  Второй канал @bahramav тоже принадлежит владельцу, но НЕ ведётся — на сайте не упоминать.
- Сайт: https://bahramovai.com

## Технические детали сайта
- Домен: bahramovai.com (Porkbun, оплачен до 25 апреля 2027)
- Хостинг: GitHub Pages
- Репозиторий: https://github.com/artsiomnhatrang-sketch/bahramov
- Ветка: main
- Локальная папка: ~/Developer/bahramov/
- DNS: 4 A-записи на GitHub Pages IP (185.199.108-111.153) + CNAME www → artsiomnhatrang-sketch.github.io
- HTTPS: включён

## Дизайн (соблюдать во всех статьях)
- Фон: #000000 (чёрный)
- Акцент: #f4672a (оранжевый)
- Шрифты: Unbounded (заголовки и логотип nav-logo), Inter (текст)

## SEO — что уже настроено
- robots.txt — разрешает индексацию, ссылка на sitemap
- sitemap.xml — обновлять при добавлении каждой статьи!
- llms.txt — для нейросетей (услуги, цены, кейсы)
- Google Search Console — подключён (верификация googlecd6247cb3e635c34.html)
- Яндекс.Вебмастер — подключён (верификация yandex_4569c44e850f20f1.html)
- Мета-теги: description, canonical, Open Graph, Twitter Card
- JSON-LD: Article (блог), Person + FAQPage (about.html), FAQPage (главная), BreadcrumbList (все 27 статей)

## Структура папок
~/Developer/bahramov/
├── index.html              — главная (лендинг)
├── about.html              — страница "Обо мне" (JSON-LD Person + FAQPage)
├── CNAME                   — bahramovai.com
├── robots.txt
├── sitemap.xml             — ОБНОВЛЯТЬ при каждой новой статье
├── feed.xml                — RSS блога, НЕ править руками: генерится scripts/seo-sync.py
├── 404.html                — кастомная страница ошибки (GitHub Pages подхватывает сам), noindex
├── llms.txt                — для нейросетей (услуги, цены, кейсы)
├── googlecd6247cb3e635c34.html — верификация Google
├── yandex_4569c44e850f20f1.html — верификация Яндекс.Вебмастер
├── offer.html
├── privacy.html
├── photo.jpg               — портрет-робот (188 КБ, ТОЛЬКО og:image/twitter/JSON-LD превью на всех страницах — не менять формат, не удалять!)
├── photo.webp              — портрет-робот WebP (134 КБ, больше НЕ в hero about.html — заменён на me.webp; оставлен как запасной)
├── me.jpg                  — видимое фото в hero about.html (живое фото Артёма, 1200×1200, 264 КБ, src в <img class="hero-photo">)
├── me.webp                 — то же WebP (196 КБ, <source> в <picture> на about.html); photo.jpg остаётся только как og:image превью
├── robot.jpg               — декор hero (149 КБ, fallback в <picture> на index.html)
├── robot.webp              — декор hero WebP (104 КБ, <source> в <picture> на index.html)
├── hero-cyborg.jpg         — декор hero (102 КБ, fallback в <picture> на index.html)
├── hero-cyborg.webp        — декор hero WebP (69 КБ, <source> в <picture> на index.html)
├── publish-article.sh      — скрипт публикации с автопроверкой
├── NEXT-SESSION.md         — точка входа для нового чата: приоритеты и границы
├── scripts/
│   ├── preflight.sh        — ГЛАВНЫЙ: все проверки одной командой + режим --tema
│   ├── check-stat-cards.py — pre-publish проверка статистических карточек
│   ├── site-audit.py       — аудит: битые ссылки, картинки, SEO-структура, sitemap
│   ├── seo-sync.py         — генерит feed.xml из статей + сверяет sitemap (--check = только отчёт)
│   ├── overlap-audit.py    — повторы между статьями: дубли тем, копипаст, одинаковые заголовки
│   └── content-audit.py    — честность текста: цифры без атрибуции, обещания результата (--changed)
├── unblock/index.html      — короткая редирект-ссылка для Instagram bio → /blog/instagram-telegram-unblock.html (noindex)
├── ig/index.html           — короткая редирект-ссылка для Instagram bio → главная с UTM (noindex)
└── blog/
    ├── index.html          — список статей (ОБНОВЛЯТЬ при новой статье)
    └── [статьи].html

## Опубликованные статьи (37 статей)
1. 7-signs-you-need-ai-agent.html — 7 признаков, что бизнесу нужен AI-агент
2. ai-agents-2026.html — AI-агенты в 2026: что это, зачем бизнесу и как внедрить
3. ai-assistant-5-tasks.html — 5 задач для AI-ассистента
4. ai-content-without-burnout.html — Нейросети для контента без выгорания
5. ai-strategy-small-business.html — AI-стратегия для малого бизнеса
6. chatplace-instagram-automation.html — Автоматизация Instagram с ChatPlace
7. instagram-mass-ban-2026.html — Массовые баны Instagram 2026
8. instagram-telegram-unblock.html — Восстановление Instagram и Telegram
9. personal-brand-ai-strategy.html — Личный бренд + AI-стратегия
10. telegram-1000-subscribers.html — Telegram: первая 1000 подписчиков
11. telegram-sales-funnel.html — Воронка продаж в Telegram
12. virtual-assistant-cost-roi.html — Виртуальный ассистент: стоимость и окупаемость
13. train-ai-agent-like-manager.html — Как обучить AI-агента отвечать как менеджер: пошаговый гайд
14. instagram-account-recovery-2026.html — Почему Instagram блокирует аккаунты в 2026 и как восстановить доступ легально
15. instagram-novyy-akkaunt-blokirovka-2026.html — Почему Instagram блокирует новые аккаунты сразу после регистрации — и как обойти device fingerprinting в 2026
16. instagram-blokirovki-may-2026.html — Массовые блокировки Instagram в мае 2026: когда закончится волна и как сохранить свой аккаунт
17. instagram-posle-razblokirovki-cheklist-2026.html — Что делать после разблокировки Instagram: чек-лист 2026
18. instagram-cepnaya-blokirovka-multiakkaunty-2026.html — Цепная блокировка Instagram: как защитить несколько аккаунтов в 2026
19. instagram-dva-akkaunta-odin-telefon-2026.html — Два аккаунта Instagram на одном телефоне: как не получить бан в 2026
20. instagram-recheck-prosadka-ohvatov-2026.html — Recheck Instagram 2026: почему просели охваты и что делать
21. ai-agent-vs-chatbot-2026.html — Чат-бот мёртв. AI-агент vs чат-бот в 2026
22. chatgpt-dlya-biznesa-10-scenariev.html — ChatGPT для бизнеса в 2026: 10 рабочих сценариев
23. instagram-kommercheskiy-kontent-bez-bana.html — Коммерческий контент в Instagram без бана: как работать с партнёрками и магазинами легально
24. instagram-registraciya-progrev-2026.html — Регистрация и прогрев нового Instagram-аккаунта: пошаговая инструкция на 2026 год
25. instagram-celostnost-akkaunta-2026.html — Нарушение целостности аккаунта Instagram: почему блокируют и как вернуть доступ
26. instagram-povtornaya-blokirovka-2026.html — Повторная блокировка Instagram 2026: почему банит снова и как завести аккаунт, который выживет
27. chatbot-cost-2026.html — Сколько стоит чат-бот для бизнеса в 2026 году: уровни решений, факторы цены и окупаемость
28. max-messenger-biznes-2026.html — Мессенджер MAX для бизнеса в 2026: стоит ли заводить чат-бота
29. telegram-zamedlenie-biznes-2026.html — Замедление Telegram в России: риски для бизнеса и план действий в 2026
30. whatsapp-blokirovka-biznes-2026.html — Блокировка WhatsApp в России: риски для бизнеса и план действий в 2026
31. telegram-vs-max-biznes-2026.html — Telegram или MAX: куда переносить бизнес в 2026 (сравнение мессенджеров)
32. telegram-akkaunt-ugon-fishing-2026.html — Как в 2026 угоняют аккаунты в Telegram: схемы фишинга и как защититься
33. instagram-bezopasnyy-zapusk-posle-blokirovki-2026.html — Безопасный запуск Instagram после блокировки: новый или переупакованный аккаунт (телефон, поведение, фото, связи)
34. telegram-ai-agenty-konstruktor-2026.html — Нативные AI-агенты в Telegram: стоит ли бизнесу отказываться от внешних платформ в 2026 (Managed Bots и встроенный AI-редактор — когда нативного агента хватает, а когда нужна внешняя платформа под продажи)
35. instagram-prodvizhenie-skynet-ii-vzaimodeystvie-2026.html — Продвижение Instagram «СКАЙНЕТ»: конверсионный оффер пакета (вывод в поиск, продвижение постов/рилс, ИИ-взаимодействие с ЦА, автоворонка, Close Friends, сопровождение). Цена: первый месяц 17 000 ₽, далее 15 000 ₽/мес. Результат подан как ориентир (+15к охвата/мес, ×2–3 посещений), без «маслукинга». По просьбе владельца тема риска/безопасности из статьи убрана целиком (нет ни хеджа, ни гарантий). ChatPlace указан как официальный партнёр Meta (офиц. интеграция с Instagram API) — прежнее правило «ChatPlace не партнёр Meta» устарело, владелец подтвердил офиц. интеграцию.
36. instagram-usloviya-ispolzovaniya-kto-mozhet-2026.html — Право на аккаунт Instagram: условия использования (ветка банов «не за контент, а за право иметь аккаунт»): возраст <13, обход удалённого аккаунта, отказ/провал проверки возраста, разбор формулировок «по-прежнему нарушает» / «повторная проверка недоступна». Article+Breadcrumb+FAQPage. Создана 10.08.2026 в рамках аудита кластера разбанов.
37. blokirovka-instagram-2026-polnoe-rukovodstvo.html — Блокировка Instagram в 2026: что делать — полный разбор по ситуациям. HUB-СТРАНИЦА (pillar page) кластера «Блокировки Instagram»: точка входа, разбор по ситуациям (ограничение действий, проверка личности, отключение аккаунта, повторные баны, просадка охватов) со ссылками на все 15 статей кластера. Опубликована 12.08.2026, priority 0.9 в sitemap (выше обычных статей). Прошла гейт reviewer.

Юридическая страница (НЕ статья, в счётчик не входит): blog/usloviya-okazaniya-uslug.html — границы ответственности исполнителя (только юр. условия, без техсоветов, без обещаний гарантированного разбана и сроков). Только BreadcrumbList. В листинг блога НЕ добавлена, sitemap priority 0.3. Ссылается из чек-листа после разблокировки и статьи №36.

### Аудит кластера разбанов Instagram (10.08.2026)
4 статьи приведены к единой позиции (устранены мифы и противоречия): постоянство сети важнее её смены (убраны «серверы США»); Instagram не читает Apple ID/IMEI/MAC/серийник (связывание — по поведению, соцграфу, контенту, общим контактным данным); несколько аккаунтов на одном устройстве официально разрешены (риск — от зеркальности/массовых действий); Accounts Center: объединять если аккаунты открыто твои, разъединять только при страйке (и это не рвёт связь у Meta); Instagram сам вырезает EXIF, чистка метаданных не защищает, дубли ловятся перцептивным хэшем (убран online-metadata.com); полная тишина после бана не защищает и роняет охваты (убрана «нулевая активность 48ч») — снижать нужно исходящую массовую активность; аватар/имя/юзернейм не менять первые 2 недели; пароль менять сразу только при подозрении на взлом + 2FA; хэштеги дают меньше охвата чем ключи в тексте, блок из 30 одинаковых хэштегов = спам-сигнал (убрано «хэштеги вовсе не работают»); Trust Score и «речек раз в 3-4 месяца» — поданы как наблюдение из практики, не механика Meta; убраны все советы по обходу детекта (Parallel Space/Island/Shelter, эмуляторы, мобильные прокси под рассылки/автоматизацию). Файлы: instagram-posle-razblokirovki-cheklist-2026, instagram-cepnaya-blokirovka-multiakkaunty-2026, instagram-dva-akkaunta-odin-telefon-2026, instagram-recheck-prosadka-ohvatov-2026. Расширение аудита (по просьбе владельца): в instagram-novyy-akkaunt-blokirovka-2026.html убран миф про Apple ID/MAC как факторы device fingerprinting, снята нормализация «антидетектов/эмуляторов», а раздел про распознавание лиц приведён к аккуратной формулировке povtornaya (нет публично подтверждённого механизма автобана по лицу; в ЕС/UK не развёрнуто). Файл instagram-bezopasnyy-zapusk-posle-blokirovki-2026.html по прямой просьбе владельца НЕ трогали (там осталось операционное упоминание Apple ID). В povtornaya-blokirovka-2026.html упоминание «нового Apple ID» оставлено намеренно — это операционный совет при сбросе устройства, а не миф «IG читает Apple ID».

## Контент-фабрика на агентах (собрана 31.07.2026)
Слой агентов Claude Code поверх сайта. Роли в `.claude/agents/` (локально, gitignored):
editor, writer, reviewer, publisher, scriptwriter, scout. Единый свод правил для них —
`PROJECT-BLUEPRINT.md` (раздел 5 = правила честности).
- **Статьи:** editor → writer → reviewer (гейт честности) → publisher (готовит коммит,
  обновляет листинг/sitemap/счётчик). `git push` / `publish-article.sh` — ТОЛЬКО вручную
  владельцем. Гейт не обходить даже по просьбе «сделай всё сам».
- **Reels:** scriptwriter → личка Telegram через `scripts/telegram_send.py`. Отдельный
  бот **@bahramov_reels_bot** (НЕ боевой @bahramovartem_bot, тот завязан на ChatPlace/CTA).
- **Тренды:** scout собирает дайджест (ниша топ-5 + блок «на радаре»). Ежедневно 09:00 ICT
  через ОБЛАЧНУЮ routine `trig_01R7fpXFLf4iz5bjQyT4XGTi` (claude.ai/code/routines).
  Облако НЕ видит `.env`/`.claude/` — промпт routine самодостаточен, токены вшиты в него.
  Источники: Wordstat + веб + vc/Habr рабочие; Reddit (анти-бот) и Google Trends (404) пока нет.
- **Автопостинг в канал.** Бот **@bahramov_reels_bot** добавлен админом в канал
  @artsiombahram (id `-1003901787423`) с единственным правом — публикация
  сообщений. `scripts/rss-to-telegram.py` берёт новые статьи из `feed.xml` и
  постит их в канал; вызов встроен в publish-article.sh. Состояние (что уже
  отправлено) — `scripts/.telegram-posted.json`, в gitignore. При переустановке
  на новой машине сначала `--init`, иначе в канал улетят все статьи разом.
- **Яндекс OAuth-приложение** (для API Вебмастера): ClientID `146e45f36e154497900ae5492d37e824`,
  права `webmaster:hostinfo` + `webmaster:verify`, создано 17.08.2026 в аккаунте
  artsiomnhatrang@gmail.com. Токен лежит в `.env` как `YANDEX_WEBMASTER_TOKEN`.
  Токены Яндекса живут около года — когда `yandex-recrawl.py` начнёт отвечать
  «Токен не работает», перевыпустить по ссылке (приложение пересоздавать НЕ нужно):
  `https://oauth.yandex.ru/authorize?response_type=token&client_id=146e45f36e154497900ae5492d37e824`
  → «Разрешить» → скопировать `access_token=` из адресной строки → заменить строку в `.env`.
- **Секреты** в `.env` (gitignored, chmod 600): `TELEGRAM_BOT_TOKEN` (reels-бот),
  `TELEGRAM_CHAT_ID`, `WORDSTAT_TOKEN`. Wordstat: `POST https://api.wordstat.yandex.net/v1/topRequests`,
  `Authorization: Bearer`. С Mac Артёма (Нячанг) Яндекс недоступен по TLS — Wordstat дёргать
  только из облака.
- ⚠️ Два источника правды: `.claude/agents/scout.md` (локально) и промпт облачной routine —
  при изменениях синхронить ОБА вручную.

## Услуги (для контента и CTA)
- Автоматизация Instagram и Telegram
- Настройка AI-агентов и чат-ботов (ChatPlace)
- Контент-стратегии с нейросетями
- Восстановление заблокированных аккаунтов
- Воронки продаж в мессенджерах
- Флагманский пакет "СИСТЕМА" — 39 900 ₽

## Как добавить новую статью (workflow)
1. Создать blog/[имя-файла].html в дизайне сайта
2. SEO: description (155-160 символов), canonical, Open Graph, JSON-LD Article
3. Обновить blog/index.html — блог разбит на 4 раздела (id: #razblokirovki, #messengery, #prodvizhenie, #ai-assistenty). Добавлять карточку СВЕРХУ нужного раздела (внутри его .posts-grid) и увеличить счётчик «N статей» в .cat-title этого раздела. Юрстраница usloviya-okazaniya-uslug.html в листинг НЕ входит.
4. Обновить sitemap.xml — добавить новую страницу с lastmod=сегодняшняя дата
4a. В <head> статьи должна быть строка `<link rel="alternate" type="application/rss+xml" ...>` (копируется из шаблона) + запустить `python3 scripts/seo-sync.py`, чтобы статья попала в RSS
4b. Если статья входит в кластер «Блокировки Instagram» — добавить в начало тела блок `<div data-hub-link>` со ссылкой на hub-страницу (скопировать из любой статьи кластера) и поставить ссылку на новую статью в самом hub'е
5. git add . && git commit -m "описание" && git push
6. После пуша — открыть DISTRIBUTION-PLAN.md и пройтись по чеклисту распространения
7. ОБЯЗАТЕЛЬНО обновить CLAUDE.md — добавить новую статью в раздел "Опубликованные статьи" с актуальным номером и обновить счётчик в заголовке. Это нужно делать в КАЖДОЙ публикации, чтобы контекст оставался актуальным.

## Команда для пуша
cd ~/Developer/bahramov && git add . && git commit -m "описание изменений" && git push

## Если push не проходит (просрочен токен)
1. Создать новый на github.com/settings/tokens (classic, repo scope)
2. git remote set-url origin https://НОВЫЙ_ТОКЕН@github.com/artsiomnhatrang-sketch/bahramov.git
3. git push

## Ключевые слова для SEO
AI-агенты, ИИ-агенты, виртуальные ассистенты, автоматизация бизнеса, чат-боты для бизнеса, автоматизация Instagram, автоматизация соцсетей, ChatPlace, воронка продаж Instagram/Telegram, AI-стратегия, восстановление аккаунтов, личный бренд AI

## ШАБЛОН СОЗДАНИЯ НОВОЙ СТАТЬИ

При создании любой новой статьи для блога ОБЯЗАТЕЛЬНО:

1. ШАБЛОН: Бери за основу blog/train-ai-agent-like-manager.html — копируй header, footer, шрифты, CSS-переменные, структуру <head>. НЕ придумывай свой шаблон.
2. FAQ-секция: Копируй стили <details>/<summary> из index.html. НЕ пиши свой CSS для FAQ.
3. blog/index.html: Смотри формат существующих карточек. Вставляй новую В ТОМ ЖЕ ФОРМАТЕ сверху списка. Используй str_replace, НЕ переписывай файл.
4. sitemap.xml: Смотри формат существующих <url>. Вставляй новый В ТОМ ЖЕ ФОРМАТЕ. Используй str_replace, НЕ переписывай файл.
5. Внутренние ссылки: Перед вставкой проверь ls blog/ что целевой файл существует. Если нет — пропусти ссылку.
6. CSS кнопок: Если есть .article-body a { color: ... }, добавь после: .article-body .btn-primary, .article-body .cta-button { color: #fff !important; }
7. Telegram-ссылки: CTA и кнопка в конце → https://t.me/bahramovartsiom | Кнопка 🎁 Бонусы → https://t.me/bahramovartem_bot | НЕ путать!
8. После создания: запусти python3 scripts/check-stat-cards.py
9. Stat-card: только короткие значения (2-3 слова макс). CSS-страховка обязательна: clamp(20px, 4vw, 32px) + word-break: break-word + overflow-wrap: anywhere
10. JSON-LD: три блока — Article + BreadcrumbList + FAQPage
11. НЕ выдумывать названия систем Meta, НЕ подставлять цифры без источника. ChatPlace — официальный партнёр Meta (офиц. интеграция с Instagram API), называть партнёром МОЖНО

## В конце сессии
В конце каждой сессии выполнять инструкцию из SESSION-END.md (обновить STATUS.md).

## ИНСТРУМЕНТЫ ПРОВЕРКИ (запускать без напоминаний)

Всё лежит в `scripts/`. Ассистент запускает их САМ в нужный момент — Артёму
не нужно об этом просить.

| Команда | Когда запускать |
|---|---|
| `./scripts/preflight.sh` | **Перед каждым пушем.** Гоняет всё сразу: битые ссылки, картинки, sitemap, stat-card, JSON-LD, RSS, повторы, честность изменённых статей. Выход 1 = не пушить |
| `./scripts/preflight.sh --tema "слова темы"` | **Перед новой статьёй.** Показывает, в каких статьях тема уже раскрыта. «⚠ СИЛЬНОЕ» = писать новую нельзя, надо усиливать существующую |
| `python3 scripts/overlap-audit.py` | Карта пересечений между всеми статьями: дубли тем, дословные повторы, одинаковые заголовки |
| `python3 scripts/content-audit.py --changed` | Честность только новых/изменённых текстов: цифры без атрибуции, обещания результата, советы по обходу |
| `python3 scripts/seo-sync.py` | Пересобрать `feed.xml` после новой статьи (вызывается и из publish-article.sh) |
| `python3 scripts/yandex-recrawl.py` | Переобход страниц в Яндекс.Вебмастере через API (интерфейс ассистенту заблокирован, API — нет). `--check` покажет остаток суточной квоты (150/сутки) |
| `python3 scripts/rss-to-telegram.py` | Публикует новые статьи из RSS в канал @artsiombahram. Вызывается из publish-article.sh, руками не нужен. `--dry-run` — посмотреть текст без отправки |
| `python3 scripts/site-audit.py` | Подробный технический аудит, если preflight что-то нашёл |
| `python3 scripts/check-stat-cards.py` | Отдельная проверка карточек со статистикой |

**Про цифры в статьях:** в уже опубликованных материалах цифры реальные, из
практики Артёма. Их НЕ вычищать. Проверка честности нужна для НОВЫХ текстов:
там цифру надо атрибутировать («по моим клиентам») или дать источник, иначе
reviewer завернёт.

**Автопроверка при пуше.** В репозитории настроен git-хук `.githooks/pre-push`
(включён через `git config core.hooksPath .githooks`). Он сам гоняет
`preflight.sh --fast` при каждом `git push` и блокирует пуш, если сломаны
ссылки, разметка или sitemap. Быстрый режим пропускает только проверку внешних
ссылок (единственная сетевая часть). Обойти в крайнем случае: `git push --no-verify`.

Если хук не срабатывает после клонирования репозитория заново — включить одной
командой: `git config core.hooksPath .githooks`

## Правила работы с Claude в чате
1. Любую команду для терминала Claude в чате даёт готовым блоком кода для копирования, никогда не пересказывает словами.
2. Начало сессии: если Артём просит продолжить — первым делом блок «Прочитай STATUS.md — на чём остановились и что дальше».
3. Конец сессии (после публикации последней статьи): напомнить блоком «Выполни инструкцию из SESSION-END.md».
4. Перед новой статьёй: `./scripts/preflight.sh --tema "..."` (сверка на дубль) + фактчек по быстрым темам (Telegram/WhatsApp/Meta/регуляторка). Если тема занята — предложить усиление существующей статьи, а не новый файл.
5. Дифф перед пушем — Артём одобряет. publish-article.sh Артём запускает вручную сам. Перед тем как показывать дифф — прогнать `./scripts/preflight.sh`.
6. Артём не обязан помнить про скрипты и правила. Ассистент сам открывает нужный файл контекста и сам запускает проверки. Если Артём спрашивает «всё ли ок» — это запрос на preflight, а не на пересказ.
7. Отвечать по-русски, командами готовыми блоками. Не сваливать на Артёма то, что можно проверить самому.
