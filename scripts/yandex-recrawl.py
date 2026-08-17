#!/usr/bin/env python3
"""Переобход страниц в Яндекс.Вебмастере через API. Без браузера.

Зачем: интерфейс webmaster.yandex.ru недоступен ассистенту (домен заблокирован
политикой браузера), а API — доступен. С токеном переобход делается командой,
и это можно ставить в расписание.

Разовая настройка (делается один раз владельцем):
  1. Открыть https://oauth.yandex.ru/client/new
  2. Название любое, платформа «Веб-сервисы», Redirect URI:
     https://oauth.yandex.ru/verification_code
  3. В правах (Data access) найти «Яндекс.Вебмастер» и отметить ВСЕ доступные
     пункты (обычно это один блок webmaster:*)
  4. Создать приложение, скопировать ClientID
  5. Открыть в браузере, подставив свой ClientID:
     https://oauth.yandex.ru/authorize?response_type=token&client_id=ВАШ_CLIENT_ID
  6. Разрешить доступ — в адресной строке появится access_token=...
     Скопировать значение токена
  7. Дописать в ~/Developer/bahramov/.env строку:
     YANDEX_WEBMASTER_TOKEN=вставить_токен

Дальше:
  python3 scripts/yandex-recrawl.py --check          # проверить токен и лимит
  python3 scripts/yandex-recrawl.py                  # отправить очередь по умолчанию
  python3 scripts/yandex-recrawl.py URL [URL ...]    # конкретные адреса

Лимит переобхода у Яндекса ограничен (обычно десятки URL в сутки на сайт),
поэтому скрипт печатает остаток квоты и не пытается слать больше.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.webmaster.yandex.net/v4"
SITE = "https://bahramovai.com"

# Приоритетная очередь: hub-страница кластера + материалы, которые Google
# просканировал, но не проиндексировал (список из STATUS.md на 13.08.2026)
DEFAULT_URLS = [
    f"{SITE}/",
    f"{SITE}/blog/",
    f"{SITE}/blog/blokirovka-instagram-2026-polnoe-rukovodstvo.html",
    f"{SITE}/blog/instagram-povtornaya-blokirovka-2026.html",
    f"{SITE}/blog/telegram-1000-subscribers.html",
    f"{SITE}/blog/max-messenger-biznes-2026.html",
    f"{SITE}/blog/instagram-novyy-akkaunt-blokirovka-2026.html",
    f"{SITE}/blog/chatplace-instagram-automation.html",
    f"{SITE}/blog/ai-agents-2026.html",
    f"{SITE}/blog/instagram-mass-ban-2026.html",
    f"{SITE}/blog/train-ai-agent-like-manager.html",
    f"{SITE}/blog/ai-content-without-burnout.html",
    f"{SITE}/blog/ai-assistant-5-tasks.html",
]


def token():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    t = os.environ.get("YANDEX_WEBMASTER_TOKEN")
    if not t:
        sys.exit(
            "Нет YANDEX_WEBMASTER_TOKEN в .env.\n"
            "Как его получить — в шапке этого файла (разовая настройка, ~5 минут)."
        )
    return t


def call(path, tok, method="GET", payload=None):
    url = f"{API}{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"OAuth {tok}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return {"_error": json.loads(body)}
        except json.JSONDecodeError:
            return {"_error": {"code": e.code, "body": body[:200]}}


def user_id(tok):
    r = call("/user", tok)
    if "_error" in r:
        sys.exit(f"Токен не работает: {r['_error']}")
    return r["user_id"]


def host_id(tok, uid):
    r = call(f"/user/{uid}/hosts", tok)
    if "_error" in r:
        sys.exit(f"Не читаются сайты: {r['_error']}")
    for h in r.get("hosts", []):
        if "bahramovai.com" in h.get("unicode_host_url", ""):
            return h["host_id"], h.get("verified")
    sys.exit("bahramovai.com не найден среди сайтов этого аккаунта")


def main():
    tok = token()
    uid = user_id(tok)
    hid, verified = host_id(tok, uid)
    print(f"Сайт найден: {hid} (подтверждён: {verified})")

    quota = call(f"/user/{uid}/hosts/{hid}/recrawl/quota", tok)
    if "_error" not in quota:
        remain = quota.get("quota_remainder")
        print(f"Остаток квоты переобхода на сегодня: {remain} из {quota.get('daily_quota')}")
    else:
        remain = None
        print(f"Квота недоступна: {quota['_error']}")

    if "--check" in sys.argv:
        return 0

    urls = [a for a in sys.argv[1:] if a.startswith("http")] or DEFAULT_URLS
    if isinstance(remain, int):
        urls = urls[:remain]
    print(f"\nОтправляю на переобход: {len(urls)}")

    ok = 0
    for u in urls:
        r = call(f"/user/{uid}/hosts/{hid}/recrawl/queue", tok, "POST", {"url": u})
        if "_error" in r:
            print(f"  ✗ {u.replace(SITE,'')} — {r['_error']}")
        else:
            ok += 1
            print(f"  ✓ {u.replace(SITE,'')} (task {r.get('task_id')})")
    print(f"\nПринято: {ok} из {len(urls)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
