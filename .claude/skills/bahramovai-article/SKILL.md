---
name: bahramovai-article-writer
description: Используется когда пользователь просит написать новую статью для блога bahramovai.com
triggers:
  - создай статью
  - напиши статью
  - новая статья для блога
  - статья для bahramovai
  - статья для сайта
  - напиши пост для блога
  - create article
  - write blog post
  - new article for bahramovai
  - write article for site
  - new blog post
---

# Skill: написание статьи для блога bahramovai.com

## ЦЕЛЬ
Создать SEO + GEO-оптимизированную статью для сайта Артёма Бахрама (bahramovai.com).
Статья должна: ранжироваться в Google/Яндекс по целевым запросам об AI-агентах и
автоматизации соцсетей, попадать в ответы нейросетей (ChatGPT, Perplexity, Gemini, Claude)
на вопросы об Артёме и его услугах.

---

## Стандарт HTML структуры

Статья — полноценная HTML-страница. Обязательные элементы:

**Header (навигация) — стандартный для всего сайта:**
```html
<header class="header">
  <nav class="nav container">
    <a href="/" class="logo">BahramovAI</a>
    <div class="nav-links">
      <a href="/blog/">Блог</a>
      <a href="/about.html">Обо мне</a>
      <a href="https://t.me/bahramovartem_bot" target="_blank">🎁 Бонусы</a>
      <a href="https://t.me/bahramovartsiom" class="btn-cta" target="_blank">Получить бесплатный аудит</a>
    </div>
  </nav>
</header>
```

**Breadcrumbs (сразу после хедера):**
```html
<nav class="breadcrumbs" aria-label="Навигация">
  <ol>
    <li><a href="/">Главная</a></li>
    <li><a href="/blog/">Блог</a></li>
    <li aria-current="page">Название статьи</li>
  </ol>
</nav>
```

**Один H1 на страницу** — точное совпадение с og:title (или близкое).

**CTA в конце статьи:**
```html
<div class="article-cta">
  <p>Остались вопросы или хотите внедрить это в своём бизнесе?</p>
  <a href="https://t.me/bahramovartsiom" class="btn-primary" target="_blank">
    Написать в Telegram
  </a>
</div>
```

**Footer — стандартный для всего сайта.**

---

## Обязательные SEO-теги в <head>

```html
<!-- Title: 50-60 символов, ключевик + бренд -->
<title>Ключевой запрос | Артём Бахрам / BahramovAI</title>

<!-- Description: 140-160 символов -->
<meta name="description" content="..." />

<!-- Canonical -->
<link rel="canonical" href="https://bahramovai.com/blog/имя-файла.html" />

<!-- Open Graph -->
<meta property="og:title" content="..." />
<meta property="og:description" content="..." />
<meta property="og:image" content="https://bahramovai.com/photo.jpg" />
<meta property="og:url" content="https://bahramovai.com/blog/имя-файла.html" />
<meta property="og:type" content="article" />
<meta property="og:locale" content="ru_RU" />

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="..." />
<meta name="twitter:description" content="..." />
<meta name="twitter:image" content="https://bahramovai.com/photo.jpg" />

<!-- JSON-LD Article -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "...",
  "description": "...",
  "image": "https://bahramovai.com/photo.jpg",
  "datePublished": "YYYY-MM-DD",
  "author": {
    "@type": "Person",
    "name": "Артём Бахрамов",
    "url": "https://bahramovai.com/about.html"
  },
  "publisher": {
    "@type": "Organization",
    "name": "BahramovAI",
    "url": "https://bahramovai.com"
  }
}
</script>

<!-- JSON-LD BreadcrumbList -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Главная", "item": "https://bahramovai.com/"},
    {"@type": "ListItem", "position": 2, "name": "Блог", "item": "https://bahramovai.com/blog/"},
    {"@type": "ListItem", "position": 3, "name": "Название статьи", "item": "https://bahramovai.com/blog/имя.html"}
  ]
}
</script>
```

---

## Дизайн

- Фон: `#000000`, акцент: `#f4672a`
- Шрифты: **Unbounded** (заголовки), **Inter** (текст)
- Использовать CSS-переменные: `var(--text)`, `var(--orange)`, `var(--muted)`, `var(--bg)`, `var(--bg3)`
- **НЕ hardcode hex**, кроме `#000` и `#fff`

---

## Stat-card блок (если используется)

Если в статье есть блоки с цифрами/статистикой:

```css
.stat-number {
  font-size: clamp(20px, 4vw, 32px);
  word-break: break-word;
  overflow-wrap: anywhere;
  hyphens: auto;
}
```

**Содержимое `.stat-number` — ТОЛЬКО короткие цифры/символы:**
- ✅ Разрешено: `78%`, `×3`, `3-5 ч`, `от 8 тыс`, `+400%`
- ❌ Запрещено: длинные фразы (`"значительный рост"`, `"часто несколько часов"`)

**Перед публикацией** автоматически прогоняется `scripts/check-stat-cards.py` — это часть `./publish-article.sh`. Если скрипт выдал КРИТИЧНО/РИСК — исправить до пуша.

---

## Длина и структура

- **1500–2000 слов** (оптимально для SEO без «воды»)
- Структура: H2-секции → абзацы → маркированные списки → блоки внимания (`.callout`, `.warning`)
- Один H1, H2 для разделов, H3 для подразделов
- Первый абзац — краткий ответ на запрос пользователя (Google snippet)

---

## Правила честности контента (КРИТИЧНО)

**НЕ выдумывать:**
- Названия систем/обновлений Meta, Instagram, Telegram, OpenAI
  (пример галлюцинации: "Global Trust & Safety v3", "ContentShield v3" — задокументировано 4 мая 2026)
- Конкретные цифры без источника ("78% бизнесов", "McKinsey: 25-40%")
- Топы продуктов с ранжированием
- Кейсы клиентов (только реальные ниже)

**Реальные кейсы Артёма (можно использовать):**
- Архитектурная студия @eldarmurakov: с 212К до 219К подписчиков, +400% охваты, +70% вовлечённость за 7 дней
- Таролог @a.platonovva: рост с 300 до 165К подписчиков (×487)
- AI-агент заменил 3 менеджеров: −150 000 ₽/мес

**Разрешённые формулировки без источника:**
«по большинству исследований», «значительная часть», «большинство», «часто»

---

## Услуги и цены Артёма (для CTA и упоминаний в тексте)

| Услуга | Цена |
|---|---|
| СИСТЕМА (флагман) | 39 900 ₽ |
| AI-агент под ключ | от 30 000 ₽ |
| Разблокировка IG/Telegram | от 10 000 ₽ |
| Чистка от ботов | 16 000 ₽ |
| Трафик + Воронка | 15 000 ₽/мес |

---

## Telegram-ссылки — куда что ведёт

| Контекст | Ссылка | Назначение |
|---|---|---|
| CTA "Получить аудит", "Написать", "Задать вопрос" | @bahramovartsiom | Личка, продажа |
| Кнопка "🎁 Бонусы" в хедере | @bahramovartem_bot | Бот с бонусами |
| Карточка "Telegram-канал" на /about | @artsiombahram | Публичный канал |

---

## Внутренняя перелинковка

- **Минимум 2-3** контекстные ссылки на другие статьи блога
- Формат: `<a href="/blog/имя.html">естественный якорный текст</a>`
- Якорный текст — естественный, не «нажмите сюда», не «читать здесь»
- **Только первое вхождение** фразы линкуем, остальные — обычный текст
- **Не self-ссылаться** (не ссылаться на саму создаваемую статью)

### Существующие статьи для перелинковки (20 статей, проверено ls)

1. `/blog/7-signs-you-need-ai-agent.html` — 7 признаков, что бизнесу нужен AI-агент
2. `/blog/ai-agents-2026.html` — AI-агенты в 2026: что это, зачем бизнесу и как внедрить
3. `/blog/ai-assistant-5-tasks.html` — 5 задач для AI-ассистента
4. `/blog/ai-content-without-burnout.html` — Нейросети для контента без выгорания
5. `/blog/ai-strategy-small-business.html` — AI-стратегия для малого бизнеса
6. `/blog/chatplace-instagram-automation.html` — Автоматизация Instagram с ChatPlace
7. `/blog/instagram-account-recovery-2026.html` — Почему Instagram блокирует аккаунты в 2026 и как восстановить доступ легально
8. `/blog/instagram-blokirovki-may-2026.html` — Массовые блокировки Instagram в мае 2026
9. `/blog/instagram-cepnaya-blokirovka-multiakkaunty-2026.html` — Цепная блокировка Instagram: как защитить несколько аккаунтов в 2026
10. `/blog/instagram-dva-akkaunta-odin-telefon-2026.html` — Два аккаунта Instagram на одном телефоне: как не получить бан в 2026
11. `/blog/instagram-mass-ban-2026.html` — Массовые баны Instagram 2026
12. `/blog/instagram-novyy-akkaunt-blokirovka-2026.html` — Почему Instagram блокирует новые аккаунты: device fingerprinting в 2026
13. `/blog/instagram-posle-razblokirovki-cheklist-2026.html` — Что делать после разблокировки Instagram: чек-лист 2026
14. `/blog/instagram-recheck-prosadka-ohvatov-2026.html` — Recheck Instagram 2026: почему просели охваты и что делать
15. `/blog/instagram-telegram-unblock.html` — Восстановление Instagram и Telegram
16. `/blog/personal-brand-ai-strategy.html` — Личный бренд + AI-стратегия
17. `/blog/telegram-1000-subscribers.html` — Telegram: первая 1000 подписчиков
18. `/blog/telegram-sales-funnel.html` — Воронка продаж в Telegram
19. `/blog/train-ai-agent-like-manager.html` — Как обучить AI-агента отвечать как менеджер
20. `/blog/virtual-assistant-cost-roi.html` — Виртуальный ассистент: стоимость и окупаемость

---

## Workflow после создания HTML

1. Сохранить файл в `blog/имя-статьи.html`
2. Обновить `blog/index.html` — добавить карточку новой статьи **сверху** списка
3. Обновить `sitemap.xml` — добавить URL с `lastmod` = сегодняшняя дата
4. Обновить `CLAUDE.md` (`~/Developer/bahramov/CLAUDE.md`):
   - В разделе **СДЕЛАНО** изменить счётчик статей (например: 20 статей → 21 статья)
   - В разделе **Опубликованные статьи** добавить запись:
     `N+1. имя-файла.html — Заголовок статьи`
   - Не трогать другие разделы
5. Запустить `./publish-article.sh /blog/имя.html`
   (автоматически: проверит stat-card → коммит → push → IndexNow → sitemap ping)

---

## Что НЕ делаем

- Накрутка подписчиков/просмотров
- Спам-комментарии на сторонних ресурсах
- Покупка ссылок
- Копипаст одной статьи на все площадки (vc.ru — только адаптация с новым углом)
- Google Indexing API для статей блога
