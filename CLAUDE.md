# BahramovAI — контекст проекта для Claude Code

## ЦЕЛЬ проекта
SEO + GEO видимость bahramovai.com: ранжироваться в Google и Яндекс по запросам
про AI-агентов и автоматизацию соцсетей. Попадать в ответы нейросетей
(ChatGPT, Perplexity, Gemini, Claude) на вопросы об Артёме Бахраме и его услугах.
Стратегия: экспертный контент с реальными цифрами, тематические кластеры,
JSON-LD, внутренняя перелинковка, регулярный постинг на vc.ru/LinkedIn/Telegram/YouTube.

## СДЕЛАНО
- 21 статья в блоге (тематические кластеры: AI-агенты, Instagram-блокировки, Telegram, автоматизация)
- about.html — страница "Обо мне" с JSON-LD Person + FAQPage
- FAQ-секция на главной (index.html) с FAQPage JSON-LD
- BreadcrumbList JSON-LD добавлен во все 21 статью блога
- Внутренняя перелинковка: 41 контекстная ссылка между статьями
- llms.txt расширен: услуги, цены, кейсы
- Яндекс.Вебмастер зарегистрирован (yandex_4569c44e850f20f1.html в корне)
- Google Search Console подключён
- vc.ru: 2 опубликованные статьи (массовые блокировки IG — вторая)
- YouTube Short опубликован
- scripts/check-stat-cards.py + интеграция в publish-article.sh (pre-publish автопроверка)
- photo.webp подключён в about.html через <picture> (экономия 54 КБ / -29% для современных браузеров)

## TODO (приоритизировано)
1. Оптимизация изображений (частично сделано):
   ✅ photo.webp подключён в about.html через <picture> (20 мая)
   ⏸ photo.jpg (188 КБ) — НЕ сжимать через sips, файл уже оптимизирован (проверено: sips -s formatOptions 80 увеличивает размер до 248 КБ). Для дальнейшего сжатия нужен cwebp/jpegoptim через Homebrew (Homebrew не установлен).
   ⏳ hero-cyborg.png (943 КБ, сирота) — решить судьбу: удалить или вынести в .gitignore-папку
2. Привязать YouTube канал к artsiomnhatrang@gmail.com для связки с Google Search Console
3. Проверить FAQPage в Rich Results (через search.google.com/test/rich-results) — через 2-3 дня после публикации
4. Следующие статьи: "AI-агент vs чат-бот: что выбрать", "Сколько стоит чат-бот в 2026"
5. Продолжить дистрибуцию: vc.ru, LinkedIn, Telegram-канал, YouTube Shorts

## Кто владелец
- Имя: Артём Бахрам (Artsiom Bahram / Артём Бахрамов)
- Роль: AI-стратег, эксперт по автоматизации соцсетей
- Локация: Нячанг, Вьетнам
- Email: artsiomnhatrang@gmail.com
- Telegram: @bahramovartsiom
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
- Шрифты: Unbounded (заголовки), Inter (текст), Bebas Neue (логотип)

## SEO — что уже настроено
- robots.txt — разрешает индексацию, ссылка на sitemap
- sitemap.xml — обновлять при добавлении каждой статьи!
- llms.txt — для нейросетей (услуги, цены, кейсы)
- Google Search Console — подключён (верификация googlecd6247cb3e635c34.html)
- Яндекс.Вебмастер — подключён (верификация yandex_4569c44e850f20f1.html)
- Мета-теги: description, canonical, Open Graph, Twitter Card
- JSON-LD: Article (блог), Person + FAQPage (about.html), FAQPage (главная), BreadcrumbList (все 21 статья)

## Структура папок
~/Developer/bahramov/
├── index.html              — главная (лендинг)
├── about.html              — страница "Обо мне" (JSON-LD Person + FAQPage)
├── CNAME                   — bahramovai.com
├── robots.txt
├── sitemap.xml             — ОБНОВЛЯТЬ при каждой новой статье
├── llms.txt                — для нейросетей (услуги, цены, кейсы)
├── googlecd6247cb3e635c34.html — верификация Google
├── yandex_4569c44e850f20f1.html — верификация Яндекс.Вебмастер
├── offer.html
├── privacy.html
├── photo.jpg               — портрет (188 КБ, og:image на всех страницах + JSON-LD — не менять формат!)
├── photo.webp              — портрет WebP (134 КБ, подключён в about.html через <picture> с 20 мая)
├── robot.jpg               — декор hero (149 КБ, fallback в <picture> на index.html)
├── robot.webp              — декор hero WebP (104 КБ, <source> в <picture> на index.html)
├── hero-cyborg.jpg         — декор hero (102 КБ, fallback в <picture> на index.html)
├── hero-cyborg.webp        — декор hero WebP (69 КБ, <source> в <picture> на index.html)
├── hero-cyborg.png         — СИРОТА 943 КБ, нигде не используется (TODO: удалить)
├── scripts/
│   ├── check-stat-cards.py — pre-publish проверка статистических карточек
│   └── publish-article.sh  — скрипт публикации с автопроверкой
└── blog/
    ├── index.html          — список статей (ОБНОВЛЯТЬ при новой статье)
    └── [статьи].html

## Опубликованные статьи (21 статья)
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
3. Обновить blog/index.html — добавить карточку новой статьи СВЕРХУ
4. Обновить sitemap.xml — добавить новую страницу с lastmod=сегодняшняя дата
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
11. НЕ выдумывать названия систем Meta, НЕ подставлять цифры без источника, НЕ называть ChatPlace партнёром Meta
