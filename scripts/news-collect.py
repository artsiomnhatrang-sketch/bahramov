#!/usr/bin/env python3
"""Собирает горячие ИИ-новости из RSS и веб-зеркал Telegram-каналов.

Это первое звено новостного конвейера: скрипт только СОБИРАЕТ и чистит,
никаких оценок и текстов — их делает агент news-editor.

    python3 scripts/news-collect.py             # собрать за последние 36 часов
    python3 scripts/news-collect.py --hours 72  # окно пошире
    python3 scripts/news-collect.py --print     # показать в терминале

Результат — .news/YYYY-MM-DD.json (папка в .gitignore, на сайт не попадает).

Четыре потока источников:
    ai        — западные первоисточники и профильные медиа (быстрее всех)
    ru        — русскоязычные IT-медиа (готовый контекст и терминология)
    platform  — Meta / Instagram / Telegram: изменения политик и API
    tg        — русские Telegram-каналы про ИИ (самый быстрый, но шумный)

Зависимостей нет — только стандартная библиотека.
"""
import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / ".news"
UA = "Mozilla/5.0 (compatible; bahramov-newsbot/1.0)"
MAX_PER_SOURCE = 12  # потолок на источник, чтобы плодовитый Habr не забил дайджест
OLDEST = datetime.min.replace(tzinfo=timezone.utc)

# ---------------------------------------------------------------- источники

# (поток, название, url). RSS определяется по типу — t.me/s/ парсится отдельно.
FEEDS = [
    # Западные первоисточники и профильные медиа
    ("ai", "OpenAI", "https://openai.com/news/rss.xml"),
    ("ai", "Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    ("ai", "Google AI", "https://blog.google/technology/ai/rss/"),
    ("ai", "TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("ai", "The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    # Русскоязычные IT-медиа
    ("ru", "Habr / ИИ", "https://habr.com/ru/rss/hubs/artificial_intelligence/articles/?fl=ru"),
    ("ru", "vc.ru", "https://vc.ru/rss/all"),
    # Платформы: политики, блокировки, API
    ("platform", "Meta Newsroom", "https://about.fb.com/news/feed/"),
]

# Русские Telegram-каналы (читаются через веб-зеркало t.me/s/<name> — публичное,
# бот для этого не нужен и в каналы вступать не надо).
TG_CHANNELS = [
    ("tg", "@ai_newz", "ai_newz"),
    ("tg", "@data_secrets", "data_secrets"),
    ("tg", "@seeallochnaya", "seeallochnaya"),
    ("tg", "@denissexy", "denissexy"),
    ("platform", "@telegram", "telegram"),
]

# У Anthropic публичного RSS нет (проверено: /rss.xml и /news/rss.xml отдают 404),
# их анонсы приходят через TechCrunch, The Verge и каналы выше.

# ------------------------------------------------------- фильтры релевантности

# Широкие ленты (vc.ru, отчасти каналы) тащат всё подряд — прогоняем через
# ключевые слова ниши. Профильные ИИ-ленты фильтровать не нужно.
BROAD_SOURCES = {"vc.ru", "@telegram"}

KEYWORDS = [
    "нейросет", "нейронк", "chatgpt", "openai", "anthropic", "claude",
    "gemini", "агент", "автоматизац", "instagram", "инстаграм", "telegram",
    "телеграм", "whatsapp", "блокиров", "аккаунт", "модерац", "алгоритм",
    "рилс", "midjourney", "deepseek", "нейро",
]

# Короткие и многозначные ключи — только как отдельные слова, иначе «ai» ловится
# внутри «Chain», а «бан» — внутри «банк».
KEYWORDS_EXACT = [
    "ии", "ai", "gpt", "llm", "agent", "бот", "боты", "bot", "meta", "мета",
    "бан", "баны", "reels", "sora", "veo", "grok", "llama", "mistral", "qwen",
]
EXACT_RE = re.compile(
    r"(?<![a-zа-яё0-9])(" + "|".join(KEYWORDS_EXACT) + r")(?![a-zа-яё0-9])"
)

# Мусор, который регулярно лезет из общих лент
STOP_PATTERNS = [
    r"^реклама\b", r"вакансия", r"дайджест вакансий", r"^опрос\b",
    r"курс(ы)? по программированию", r"скидк[аи] \d+%",
]


def looks_relevant(title, summary, source):
    """Для широких лент — есть ли в тексте что-то из ниши."""
    text = (title + " " + summary).lower()
    for pat in STOP_PATTERNS:
        if re.search(pat, text):
            return False
    if source not in BROAD_SOURCES:
        return True
    return any(k in text for k in KEYWORDS) or bool(EXACT_RE.search(text))


# ------------------------------------------------------------------ утилиты

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def strip_tags(raw):
    """HTML → плоский текст. Внутри RSS-описаний часто лежит разметка."""
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = html.unescape(raw)
    text = re.sub(r"[ \t ]+", " ", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


def shorten(text, limit=400):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def parse_date(value):
    """RSS отдаёт RFC-822, Atom — ISO. Не распарсилось — считаем свежим."""
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt is not None and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def item_id(link, title):
    base = (link or "") + "|" + (title or "")
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]


def tag(el, *names):
    """Достаёт текст тега без привязки к namespace (RSS и Atom вперемешку)."""
    for name in names:
        for child in el:
            if child.tag.split("}")[-1] == name:
                if child.text and child.text.strip():
                    return child.text.strip()
                # У Atom ссылка лежит в атрибуте href
                href = child.get("href")
                if href:
                    return href.strip()
    return ""


# ------------------------------------------------------------------- парсеры

def parse_feed(stream, source, raw):
    root = ET.fromstring(raw)
    items = []
    for el in root.iter():
        name = el.tag.split("}")[-1]
        if name not in ("item", "entry"):
            continue
        title = strip_tags(tag(el, "title"))
        link = tag(el, "link", "guid")
        summary = strip_tags(tag(el, "description", "summary", "content"))
        published = parse_date(tag(el, "pubDate", "published", "updated"))
        if not title:
            continue
        items.append({
            "stream": stream,
            "source": source,
            "title": title,
            "link": link,
            "summary": shorten(summary),
            "published": published.isoformat() if published else None,
            "_dt": published,
        })
    return items


TG_MSG_RE = re.compile(
    r'<div class="tgme_widget_message_text[^"]*"[^>]*>(?P<body>.*?)</div>',
    re.S,
)
TG_META_RE = re.compile(
    r'<a class="tgme_widget_message_date" href="(?P<url>[^"]+)".*?'
    r'<time datetime="(?P<dt>[^"]+)"',
    re.S,
)


def parse_telegram(stream, source, channel, raw):
    """Веб-зеркало канала. Порядок сообщений и дат совпадает — идём парами."""
    page = raw.decode("utf-8", errors="replace")
    bodies = TG_MSG_RE.findall(page)
    metas = TG_META_RE.findall(page)
    items = []
    for i, body in enumerate(bodies):
        text = strip_tags(body)
        if len(text) < 60:  # односложные реплики и реакции — мимо
            continue
        url, dt_raw = ("https://t.me/s/" + channel, None)
        if i < len(metas):
            url, dt_raw = metas[i][0], metas[i][1]
        published = parse_date(dt_raw)
        title = shorten(text.split("\n")[0], 160)
        items.append({
            "stream": stream,
            "source": source,
            "title": title,
            "link": url,
            "summary": shorten(text, 600),
            "published": published.isoformat() if published else None,
            "_dt": published,
        })
    return items


# --------------------------------------------------------------------- сбор

def collect(hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items, errors, stats = [], [], {}

    def take(source, got):
        fresh = [i for i in got if i["_dt"] is None or i["_dt"] >= cutoff]
        fresh = [i for i in fresh
                 if looks_relevant(i["title"], i["summary"], source)]
        # Habr в удачный день даёт 30+ материалов и один забивает весь дайджест —
        # берём от каждого источника только самое свежее.
        fresh.sort(key=lambda i: i["_dt"] or OLDEST, reverse=True)
        stats[source] = len(fresh[:MAX_PER_SOURCE])
        items.extend(fresh[:MAX_PER_SOURCE])

    for stream, source, url in FEEDS:
        try:
            take(source, parse_feed(stream, source, fetch(url)))
        except (urllib.error.URLError, ET.ParseError, OSError, ValueError) as e:
            errors.append(f"{source}: {type(e).__name__}: {e}")
            stats[source] = None

    for stream, source, channel in TG_CHANNELS:
        try:
            raw = fetch("https://t.me/s/" + channel)
            take(source, parse_telegram(stream, source, channel, raw))
        except (urllib.error.URLError, OSError, ValueError) as e:
            errors.append(f"{source}: {type(e).__name__}: {e}")
            stats[source] = None

    # Дедуп: одна и та же новость приходит из 3-4 источников сразу.
    seen, unique = set(), []
    for item in sorted(items, key=lambda i: i["_dt"] or OLDEST, reverse=True):
        key = re.sub(r"[^a-zа-я0-9]+", "", item["title"].lower())[:60]
        if not key or key in seen:
            continue
        seen.add(key)
        item.pop("_dt", None)
        item["id"] = item_id(item["link"], item["title"])
        unique.append(item)

    return unique, stats, errors


def main():
    ap = argparse.ArgumentParser(description="Сбор ИИ-новостей в .news/")
    ap.add_argument("--hours", type=int, default=36,
                    help="окно свежести в часах (по умолчанию 36)")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="показать собранное в терминале")
    args = ap.parse_args()

    items, stats, errors = collect(args.hours)
    today = datetime.now().strftime("%Y-%m-%d")
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / (today + ".json")
    out.write_text(json.dumps({
        "date": today,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "window_hours": args.hours,
        "sources": stats,
        "errors": errors,
        "items": items,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    ok = sum(1 for v in stats.values() if v is not None)
    print(f"Собрано {len(items)} новостей из {ok}/{len(stats)} источников "
          f"за последние {args.hours} ч → {out.relative_to(ROOT)}")
    for source, n in stats.items():
        print(f"  {'✗ недоступен' if n is None else str(n).rjust(3) + ' шт'}  {source}")
    for err in errors:
        print("  ! " + err)
    if args.show:
        for i in items:
            print(f"\n[{i['stream']}] {i['source']} — {i['title']}\n  {i['link']}")
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
