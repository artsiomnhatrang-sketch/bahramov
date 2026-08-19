#!/usr/bin/env python3
"""Тонкая обёртка над Telegram Bot API. Общая для новостного конвейера.

Отдельный модуль, чтобы tg-digest.py и tg-watcher.py не дублировали одно и то же.
Самостоятельно ничего не делает — только импортируется.

Зависимостей нет — только стандартная библиотека.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANNEL_ID = "-1003901787423"  # канал «AI и Безопасность» (@artsiombahram)
CHANNEL_NAME = "artsiombahram"
API = "https://api.telegram.org/bot{token}/{method}"

_token = None


def load_env():
    """Подтягивает .env в окружение и возвращает токен бота."""
    global _token
    if _token:
        return _token
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    _token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not _token:
        sys.exit("Нет TELEGRAM_BOT_TOKEN — положи его в .env")
    return _token


def owner_chat():
    load_env()
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat:
        sys.exit("Нет TELEGRAM_CHAT_ID в .env — некому слать дайджест")
    return chat


def call(method, http_timeout=30, **params):
    """Вызов метода API. Возвращает result или бросает RuntimeError.

    `http_timeout` — таймаут сокета, не параметр Telegram. У getUpdates есть
    свой `timeout` для длинного опроса, он уходит в params как обычное поле.
    """
    token = load_env()
    payload = {}
    for k, v in params.items():
        if v is None:
            continue
        payload[k] = json.dumps(v, ensure_ascii=False) if isinstance(
            v, (dict, list)) else v
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API.format(token=token, method=method),
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=http_timeout) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
    if not body.get("ok"):
        raise RuntimeError(f"{method}: {body.get('description')}")
    return body.get("result")


def keyboard(rows):
    """rows — список рядов, ряд — список пар (подпись, callback_data)."""
    return {"inline_keyboard": [
        [{"text": text, "callback_data": data} for text, data in row]
        for row in rows
    ]}


def send(chat_id, text, buttons=None, preview=False):
    """Шлёт текст, при необходимости режет на куски по лимиту Telegram.

    Кнопки вешаются только на последний кусок — иначе они уедут вверх.
    """
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or [""]
    result = None
    for n, chunk in enumerate(chunks):
        last = n == len(chunks) - 1
        result = call(
            "sendMessage",
            chat_id=chat_id,
            text=chunk,
            reply_markup=buttons if (last and buttons) else None,
            link_preview_options={"is_disabled": not preview},
        )
    return result


def answer(callback_id, text=None):
    """Гасит «часики» на кнопке. Без этого Telegram крутит спиннер 30 секунд."""
    try:
        call("answerCallbackQuery", callback_query_id=callback_id, text=text)
    except RuntimeError:
        pass  # просроченный callback — не повод падать


def drop_buttons(chat_id, message_id):
    """Убирает клавиатуру у уже отправленного сообщения."""
    try:
        call("editMessageReplyMarkup", chat_id=chat_id,
             message_id=message_id, reply_markup={"inline_keyboard": []})
    except RuntimeError:
        pass


def get_updates(offset, wait=25):
    """Длинный опрос: висим на соединении `wait` секунд и ждём событие.

    HTTP-таймаут держим заведомо больше, чем ждёт сам Telegram, иначе
    соединение рвётся раньше ответа.
    """
    return call("getUpdates", http_timeout=wait + 10, timeout=wait,
                offset=offset,
                allowed_updates=["message", "callback_query"])


def post_to_channel(text):
    """Публикация в канал. Вызывается ТОЛЬКО после подтверждения владельцем."""
    res = call("sendMessage", chat_id=CHANNEL_ID, text=text,
               link_preview_options={"is_disabled": False})
    return f"https://t.me/{CHANNEL_NAME}/{res['message_id']}"
