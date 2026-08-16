#!/usr/bin/env python3
"""Постит новые статьи блога в Telegram-канал. Ручная работа не нужна.

Как работает: читает feed.xml, сравнивает со списком уже отправленных статей
и публикует только то, чего в канале ещё не было.

    python3 scripts/rss-to-telegram.py --init    # ПЕРВЫЙ запуск: пометить всё
                                                 # текущее как отправленное,
                                                 # ничего не публикуя
    python3 scripts/rss-to-telegram.py --dry-run # показать, что бы улетело
    python3 scripts/rss-to-telegram.py           # опубликовать новое

Состояние — scripts/.telegram-posted.json (в .gitignore). Если файла нет,
скрипт откажется работать без --init: это защита от того, чтобы случайно
вывалить в канал все 25 статей разом.

Ключи берутся из .env: TELEGRAM_BOT_TOKEN. ID канала — константа CHANNEL_ID.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed.xml"
STATE = ROOT / "scripts" / ".telegram-posted.json"
CHANNEL_ID = "-1003901787423"  # канал «AI и Безопасность» (@artsiombahram)
API = "https://api.telegram.org/bot{token}/sendMessage"


def load_env():
    env = ROOT / ".env"
    if not env.exists():
        sys.exit("Нет .env — неоткуда взять TELEGRAM_BOT_TOKEN")
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit("В .env нет TELEGRAM_BOT_TOKEN")
    return token


def feed_items():
    if not FEED.exists():
        sys.exit("Нет feed.xml — сначала: python3 scripts/seo-sync.py")
    root = ET.parse(FEED).getroot()
    items = []
    for item in root.findall(".//item"):
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "description": (item.findtext("description") or "").strip(),
            }
        )
    return items


def read_state():
    if STATE.exists():
        return set(json.loads(STATE.read_text(encoding="utf-8")).get("posted", []))
    return None


def write_state(posted):
    STATE.write_text(
        json.dumps({"posted": sorted(posted)}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


def compose(item):
    """Текст поста: заголовок, короткое описание, ссылка."""
    desc = re.sub(r"\s+", " ", item["description"]).strip()
    if len(desc) > 320:
        desc = desc[:317].rsplit(" ", 1)[0] + "…"
    return f"{item['title']}\n\n{desc}\n\n{item['link']}"


def send(token, text):
    data = urllib.parse.urlencode({"chat_id": CHANNEL_ID, "text": text}).encode()
    req = urllib.request.Request(API.format(token=token), data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def main():
    init = "--init" in sys.argv
    dry = "--dry-run" in sys.argv
    token = load_env()
    items = feed_items()
    posted = read_state()

    if posted is None:
        if not init:
            sys.exit(
                "Нет файла состояния. Первый запуск делается так:\n"
                "  python3 scripts/rss-to-telegram.py --init\n"
                "(пометит текущие статьи как отправленные, ничего не публикуя)"
            )
        write_state({i["link"] for i in items})
        print(f"Инициализация: {len(items)} статей помечены как отправленные.")
        print("Дальше в канал будут уходить только новые.")
        return 0

    fresh = [i for i in items if i["link"] not in posted]
    if not fresh:
        print("Новых статей нет.")
        return 0

    print(f"Новых статей: {len(fresh)}")
    for item in reversed(fresh):  # от старых к новым
        text = compose(item)
        if dry:
            print(f"\n--- было бы отправлено ---\n{text}")
            continue
        res = send(token, text)
        if res.get("ok"):
            mid = res["result"]["message_id"]
            print(f"  ✅ https://t.me/artsiombahram/{mid} — {item['title'][:50]}")
            posted.add(item["link"])
            write_state(posted)
        else:
            print(f"  ✗ {res.get('description')} — {item['title'][:50]}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
