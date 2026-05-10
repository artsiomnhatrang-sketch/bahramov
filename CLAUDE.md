# BahramovAI — контекст проекта для Claude Code

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
- llms.txt — для нейросетей
- Google Search Console — подключён (верификация googlecd6247cb3e635c34.html)
- Мета-теги: description, canonical, Open Graph, Twitter Card, JSON-LD Schema.org

## Структура папок
~/Developer/bahramov/
├── index.html              — главная (лендинг)
├── CNAME                   — bahramovai.com
├── robots.txt
├── sitemap.xml             — ОБНОВЛЯТЬ при каждой новой статье
├── llms.txt
├── googlecd6247cb3e635c34.html — верификация Google
├── offer.html
├── privacy.html
└── blog/
    ├── index.html          — список статей (ОБНОВЛЯТЬ при новой статье)
    └── [статьи].html

## Опубликованные статьи (14 штук)
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

## Услуги (для контента и CTA)
- Автоматизация Instagram и Telegram
- Настройка AI-агентов и чат-ботов (ChatPlace / ELZA)
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
