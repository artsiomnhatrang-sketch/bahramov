#!/usr/bin/env python3
"""Синхронизация SEO-артефактов сайта: RSS-фид и проверка sitemap.

Запуск:
    python3 scripts/seo-sync.py           # сгенерировать feed.xml + проверить sitemap
    python3 scripts/seo-sync.py --check   # ничего не писать, только отчёт

Фид собирается из blog/*.html по JSON-LD (headline / description / datePublished).
Sitemap НЕ переписывается — скрипт только сообщает о расхождениях, чтобы
ручные priority и changefreq не потерялись.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://bahramovai.com"
FEED_PATH = ROOT / "feed.xml"
SITEMAP_PATH = ROOT / "sitemap.xml"
FEED_LIMIT = 50

# Страницы блога, которые не являются статьями и в фид не идут
NOT_ARTICLES = {"index.html", "usloviya-okazaniya-uslug.html"}

ESCAPE = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}

# Article — основной тип, NewsArticle используется в новостных разборах
ARTICLE_TYPES = {"Article", "NewsArticle", "BlogPosting"}


def esc(text: str) -> str:
    for a, b in ESCAPE.items():
        text = text.replace(a, b)
    return text


def article_jsonld(html):
    """Возвращает JSON-LD блок статьи (Article / NewsArticle / BlogPosting)."""
    for m in re.finditer(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html, re.S
    ):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if data.get("@type") in ARTICLE_TYPES:
            return data
    return None


def collect_articles():
    items, problems = [], []
    for path in sorted((ROOT / "blog").glob("*.html")):
        if path.name in NOT_ARTICLES:
            continue
        html = path.read_text(encoding="utf-8")
        data = article_jsonld(html)
        if not data:
            problems.append(f"{path.name}: нет JSON-LD Article — в фид не попадёт")
            continue
        published = data.get("datePublished")
        if not published:
            problems.append(f"{path.name}: нет datePublished — в фид не попадёт")
            continue
        try:
            dt = datetime.strptime(published[:10], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            problems.append(f"{path.name}: некорректная дата {published!r}")
            continue
        items.append(
            {
                "file": path.name,
                "title": data.get("headline") or path.stem,
                "description": data.get("description", ""),
                "url": f"{DOMAIN}/blog/{path.name}",
                "date": dt,
            }
        )
    items.sort(key=lambda i: i["date"], reverse=True)
    return items, problems


def build_feed(items):
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        "    <title>Блог Артёма Бахрама — AI-агенты и автоматизация соцсетей</title>",
        f"    <link>{DOMAIN}/blog/</link>",
        "    <description>AI-агенты, автоматизация Instagram и Telegram, "
        "восстановление заблокированных аккаунтов, воронки продаж в мессенджерах.</description>",
        "    <language>ru</language>",
        f"    <lastBuildDate>{now}</lastBuildDate>",
        f'    <atom:link href="{DOMAIN}/feed.xml" rel="self" type="application/rss+xml" />',
        f"    <image>",
        f"      <url>{DOMAIN}/photo.jpg</url>",
        "      <title>Блог Артёма Бахрама</title>",
        f"      <link>{DOMAIN}/blog/</link>",
        "    </image>",
    ]
    for item in items[:FEED_LIMIT]:
        pub = item["date"].strftime("%a, %d %b %Y 09:00:00 +0000")
        parts += [
            "    <item>",
            f"      <title>{esc(item['title'])}</title>",
            f"      <link>{item['url']}</link>",
            f"      <guid isPermaLink=\"true\">{item['url']}</guid>",
            f"      <description>{esc(item['description'])}</description>",
            f"      <pubDate>{pub}</pubDate>",
            "    </item>",
        ]
    parts += ["  </channel>", "</rss>", ""]
    return "\n".join(parts)


def check_sitemap(items):
    sitemap = SITEMAP_PATH.read_text(encoding="utf-8")
    missing = [i["file"] for i in items if f"/blog/{i['file']}" not in sitemap]
    notes = [f"нет в sitemap.xml: blog/{name}" for name in missing]
    if "/feed.xml" in sitemap:
        notes.append("feed.xml указан в sitemap — это не нужно, фид не индексируется как страница")
    return notes


def main() -> int:
    check_only = "--check" in sys.argv
    items, problems = collect_articles()

    print(f"Статей для фида: {len(items)}")
    if items:
        print(f"Свежая: {items[0]['date']:%Y-%m-%d} — {items[0]['title'][:60]}")

    feed = build_feed(items)
    if check_only:
        current = FEED_PATH.read_text(encoding="utf-8") if FEED_PATH.exists() else ""
        # lastBuildDate меняется всегда — сравниваем без неё
        strip = lambda s: re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", s)
        state = "актуален" if strip(current) == strip(feed) else "УСТАРЕЛ (нужен запуск без --check)"
        print(f"feed.xml: {state}")
    else:
        FEED_PATH.write_text(feed, encoding="utf-8")
        print(f"feed.xml: записан ({len(items[:FEED_LIMIT])} записей)")

    for note in check_sitemap(items):
        print(f"  ⚠ {note}")
    for problem in problems:
        print(f"  ⚠ {problem}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
