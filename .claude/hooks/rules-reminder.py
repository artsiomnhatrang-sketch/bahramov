#!/usr/bin/env python3
"""UserPromptSubmit-хук: по словам сообщения Артёма подкладывает в контекст
подробные правила из docs/rules-details.md, чтобы короткий CLAUDE.md
не приводил к забытому правилу.

Разделы ищутся по началу заголовка, а не по номерам строк, поэтому
дописывание новых разделов в docs/rules-details.md ничего не ломает.
Срабатывает только при совпадении темы; иначе молчит и токенов не тратит.
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DETAILS = ROOT / "docs" / "rules-details.md"
LIMIT = 7000  # символов текста; остальное отдаём ссылкой на раздел

TOPICS = [
    (r"стать|блог|тайтл|title|faq|geo", [
        "ШАБЛОН СОЗДАНИЯ", "Статья под ответы", "Цены в статьях",
        "Даты при массовых", "Ключевые слова: метод", "CTR мерить",
        "Как добавить новую статью", "Выдача Яндекса перед",
    ]),
    (r"в[её]рст|мобил|телефон|375|отступ|кнопк|дизайн|шапк|футер|полос|съехал|рендер|всё ли в порядке|все ли в порядке", [
        "«Финальная проверка»", "Аудит вёрстки", "Ленивые картинки",
        "Шапка: оранжевые", "Ссылки-действия", "Футерная перелинковка",
        "Карточки статистики",
    ]),
    (r"seo|сео|позици|яндекс|вебмастер|google|гугл|индекс|ctr|запрос|bing|нейросет", [
        "Ключевые слова: метод", "CTR мерить", "Внешняя SEO-схема",
        "IndexNow", "Даты при массовых",
    ]),
    (r"метрик|счётчик|счетчик|визит", [
        "Метрика в браузерной", "Счётчик Метрики",
    ]),
    (r"threads|тредс|тредз|публикуй|поехали|работаем|коммент|ветк|директ|bahram\.av|bahramovartem", [
        "Threads: оба аккаунта", "Threads: узкое место", "Комментарии в Threads",
        "Threads: только комментинг", "Два аккаунта Threads",
    ]),
    (r"цен|стоимост|сколько стоит|услуг|прайс", [
        "Цены в статьях",
    ]),
    (r"модел|fable|фейбл|opus|опус|сложн|переключ", [
        "Выбор модели",
    ]),
]


def sections(text):
    """{заголовок: текст раздела} по заголовкам второго уровня."""
    out, title, buf = {}, None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if title:
                out[title] = "\n".join(buf).strip()
            title, buf = line[3:].strip(), [line]
        elif title:
            buf.append(line)
    if title:
        out[title] = "\n".join(buf).strip()
    return out


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    prompt = data.get("prompt", "").lower()
    # Один раздел — один раз за чат: повтор на каждом сообщении жжёт токены.
    seen_file = Path(tempfile.gettempdir()) / f"rules-reminder-{data.get('session_id', 'x')}.json"
    try:
        seen = set(json.loads(seen_file.read_text()))
    except Exception:
        seen = set()
    if not prompt or not DETAILS.exists():
        return

    wanted = []
    for pattern, heads in TOPICS:
        if re.search(pattern, prompt):
            wanted += [h for h in heads if h not in wanted]
    if not wanted:
        return

    secs = sections(DETAILS.read_text(encoding="utf-8"))
    body, links, used = [], [], 0
    for head in wanted:
        title = next((t for t in secs if t.startswith(head)), None)
        if not title or title in seen:
            continue
        seen.add(title)
        chunk = secs[title]
        if used + len(chunk) <= LIMIT:
            body.append(chunk)
            used += len(chunk)
        else:
            links.append(f"«{title}»")
    if not body and not links:
        return
    try:
        seen_file.write_text(json.dumps(sorted(seen), ensure_ascii=False))
    except Exception:
        pass

    msg = ["Подробные правила по теме сообщения (docs/rules-details.md). "
           "Соблюдать; не пересказывать Артёму."]
    msg += body
    if links:
        msg.append("Ещё по теме, прочитать перед правкой: " + ", ".join(links)
                   + " — `grep -n '^## ' docs/rules-details.md`, затем Read с offset.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "\n\n".join(msg),
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
