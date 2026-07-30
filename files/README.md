# Контент-фабрика на агентах Claude Code — под bahramovai.com

Агентный слой поверх уже существующей системы сайта (GitHub Pages, чистый HTML,
publish-article.sh, check-stat-cards.py, правила честности). Ничего из рабочего
пайплайна не заменяет — только добавляет генерацию и проверку контента.

## Куда класть

    .claude/agents/   → в репозиторий сайта (Claude Code подхватит роли сам)
      editor.md         редактор: отбор тем, ТЗ, дирижёр
      writer.md         пишет статью в HTML по дизайн-системе и правилам честности
      reviewer.md       гейт: честность, факты, SEO, прогон check-stat-cards.py
      publisher.md      кладёт HTML в blog/, обновляет листинг/sitemap/счётчик, коммит
      scriptwriter.md   сценарии Reels
      scout.md          разведчик трендов (подключать последним)
    scripts/
      telegram_send.py  ЛИЧНАЯ отправка сценариев Reels тебе в ЛС
                        (это НЕ post-to-telegram.sh — тот анонсит статьи в канал)

## Что НЕ дублируется (у тебя уже есть)

- publish-article.sh — публикация + IndexNow. Запускаешь ТОЛЬКО ты. publisher-агент
  его не трогает: он лишь готовит коммит и показывает дифф, дальше твой гейт.
- check-stat-cards.py — reviewer обязан его прогнать (exit 0 = ок).
- CLAUDE.md / STATUS.md / SESSION-END.md — оркестрационная память, остаётся как есть.

## Порядок сборки

1. Хребет: editor → writer → reviewer → publisher. Прогони на теме, заданной руками.
   Проверь, что HTML совпадает с образцом из blog/ и качество тебя устраивает.
2. Заявка на Wordstat API (одобрение ~сутки): https://yandex.ru/dev/wordstat/
3. scriptwriter + telegram_send.py.
4. В конце — scout на живые данные.

## Запуск цикла статьи (вручную, на старте)

В Claude Code, стоя в репозитории:

    Тема дня: "<тема>". Позови writer, чтобы написать статью по образцу blog/.
    Затем reviewer для проверки. Если REJECTED — верни правки writer и повтори.
    Когда APPROVED — позови publisher: подготовить файл, листинг, sitemap, счётчик,
    коммит, показать дифф. publish-article.sh НЕ запускать — запущу сам.

## Секреты (.env, в .gitignore)

    TELEGRAM_BOT_TOKEN=...   TELEGRAM_CHAT_ID=...   # для личной отправки Reels
    WORDSTAT_TOKEN=...                              # после одобрения заявки
