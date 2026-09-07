#!/usr/bin/env python3
"""Отправляет один сценарий Shorts в Telegram — по частям, чтобы копировать с телефона.

Каждая часть уходит отдельным сообщением в моноширинном блоке: в Telegram такой
блок копируется одним касанием, ничего выделять руками не нужно.

Использование:
    python3 youtube/send-scenario.py 1        # отправить сценарий №1
    python3 youtube/send-scenario.py 1 2 3    # несколько подряд
    python3 youtube/send-scenario.py --list   # показать список, ничего не слать

Токены берутся из .env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) — тот же бот,
что шлёт сценарии Reels.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "youtube", "scenarii-shorts.md")


def load_env():
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def parse():
    """Разбирает файл сценариев на словари: номер, название, части."""
    text = open(SRC, encoding="utf-8").read()
    blocks = re.split(r"\n## (\d+)\. ", text)
    out = {}
    for i in range(1, len(blocks), 2):
        num = int(blocks[i])
        body = blocks[i + 1]
        title = body.split("\n", 1)[0].strip()
        parts = {}

        say = re.search(r"\*\*Говорить:\*\*\n\n((?:> ?.*\n)+)", body)
        if say:
            lines = [re.sub(r"^> ?", "", l) for l in say.group(1).splitlines()]
            parts["Говорить"] = "\n".join(lines).strip()

        frame = re.search(r"\*\*В кадре:\*\* (.+?)\n\n", body, re.S)
        if frame:
            parts["В кадре"] = " ".join(frame.group(1).split())

        head = re.search(r"\*\*Заголовок:\*\* `(.+?)`", body)
        if head:
            parts["Заголовок"] = head.group(1)

        desc = re.search(r"\*\*Описание:\*\*\n```\n(.*?)\n```", body, re.S)
        if desc:
            parts["Описание"] = desc.group(1).strip()

        pin = re.search(r"\*\*Закреп:\*\*\n```\n(.*?)\n```", body, re.S)
        if pin:
            parts["Закреп"] = pin.group(1).strip()

        out[num] = {"title": title, "parts": parts}
    return out


def send(text, mono=True):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        sys.exit("Нет TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID — проверь .env")
    body = f"<pre>{html.escape(text)}</pre>" if mono else text
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": body[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)
        if not payload.get("ok"):
            sys.exit(f"Telegram вернул ошибку: {payload}")


def main():
    load_env()
    args = sys.argv[1:]
    data = parse()

    if not args or args[0] in ("--list", "-l"):
        for num in sorted(data):
            print(f"{num:>3}. {data[num]['title']}")
        return

    for arg in args:
        num = int(arg)
        if num not in data:
            print(f"Сценария №{num} нет в файле")
            continue
        item = data[num]
        send(f"Сценарий {num}. {item['title']}", mono=False)
        for label in ("Говорить", "В кадре", "Заголовок", "Описание", "Закреп"):
            if label in item["parts"]:
                send(f"{label}\n\n{item['parts'][label]}")
                time.sleep(0.4)
        print(f"Отправлен сценарий №{num}: {item['title']}")


if __name__ == "__main__":
    main()
