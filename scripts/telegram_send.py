#!/usr/bin/env python3
"""Отправляет текст (сценарий Reels) тебе в Telegram.

Использование:
    python scripts/telegram_send.py "текст сообщения"
    echo "текст" | python scripts/telegram_send.py

Нужны переменные окружения (положи в .env, не коммить):
    TELEGRAM_BOT_TOKEN  — токен бота от @BotFather
    TELEGRAM_CHAT_ID    — твой chat id (узнать: напиши боту, потом открой
                          https://api.telegram.org/bot<TOKEN>/getUpdates )

Зависимостей нет — только стандартная библиотека.
"""
import json
import os
import sys
import urllib.parse
import urllib.request


def send(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        sys.exit("Нет TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в окружении.")

    # Telegram ограничивает сообщение 4096 символами — режем на части.
    for i in range(0, len(text), 4000):
        chunk = text[i:i + 4000]
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
        }).encode()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as resp:
            payload = json.load(resp)
            if not payload.get("ok"):
                sys.exit(f"Telegram вернул ошибку: {payload}")
    print("Отправлено в Telegram.")


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]).strip() or sys.stdin.read().strip()
    if not msg:
        sys.exit("Нечего отправлять: передай текст аргументом или через stdin.")
    send(msg)
