#!/usr/bin/env python3
"""Очередь отложенных постов в Telegram-канал @artsiombahram.

Bot API не умеет отложенную отправку, поэтому очередь локальная:
файл .channel-queue/ГГГГ-ММ-ДДTЧЧ-ММ.txt (время по Нячангу, +07) уходит
в канал, когда время наступило, и переименовывается в .txt.sent.
В очередь кладутся ТОЛЬКО тексты, которые владелец уже одобрил.

Запускается launchd раз в 30 минут (com.bahramovai.channel-queue).
Если Mac спал, пост уйдёт при первом запуске после пробуждения.

    python3 scripts/channel-queue.py            # отправить наступившие
    python3 scripts/channel-queue.py --list     # показать очередь
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tg_api  # noqa: E402

QUEUE = tg_api.ROOT / ".channel-queue"


def due_at(path):
    try:
        return datetime.strptime(path.stem, "%Y-%m-%dT%H-%M")
    except ValueError:
        return None


def main():
    items = sorted(p for p in QUEUE.glob("*.txt") if due_at(p))
    now = datetime.now()
    if "--list" in sys.argv:
        for p in items:
            print(p.stem, "ждёт" if due_at(p) > now else "пора")
        return
    tg_api.load_env()
    for p in items:
        if due_at(p) > now:
            continue
        text = p.read_text(encoding="utf-8").rstrip("\n")
        link = tg_api.post_to_channel(text)
        p.rename(p.with_name(p.name + ".sent"))
        print("%s  %s -> %s" % (now.strftime("%Y-%m-%d %H:%M"), p.name, link))


if __name__ == "__main__":
    main()
