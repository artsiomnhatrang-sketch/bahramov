#!/usr/bin/env python3
"""Снимает SEO-статистику сайта из API Яндекс.Вебмастера.

Зачем: интерфейс webmaster.yandex.ru ассистенту недоступен, а API — да.
Этот скрипт отвечает на главные вопросы: что уже в поиске, что выкинуто,
по каким запросам нас показывают и где мы почти на первой странице.

    python3 scripts/yandex-stats.py            # полный отчёт
    python3 scripts/yandex-stats.py --queries  # только запросы
    python3 scripts/yandex-stats.py --urls     # только страницы (в поиске / исключённые)

Токен берётся из .env (YANDEX_WEBMASTER_TOKEN) — тот же, что у yandex-recrawl.py.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.webmaster.yandex.net/v4"


def token():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    t = os.environ.get("YANDEX_WEBMASTER_TOKEN")
    if not t:
        sys.exit("Нет YANDEX_WEBMASTER_TOKEN в .env — см. шапку scripts/yandex-recrawl.py")
    return t


def call(path, tok):
    req = urllib.request.Request(API + path, method="GET")
    req.add_header("Authorization", "OAuth " + tok)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return {"_error": json.loads(body)}
        except json.JSONDecodeError:
            return {"_error": {"code": e.code, "body": body[:300]}}
    except Exception as e:
        return {"_error": {"code": type(e).__name__, "body": str(e)[:200]}}


def ids(tok):
    r = call("/user", tok)
    if "_error" in r:
        sys.exit("Токен не работает: %s" % r["_error"])
    uid = r["user_id"]
    hosts = call("/user/%s/hosts" % uid, tok)
    if "_error" in hosts:
        sys.exit("Не читаются сайты: %s" % hosts["_error"])
    for h in hosts.get("hosts", []):
        if "bahramovai.com" in h.get("unicode_host_url", ""):
            return uid, h["host_id"]
    sys.exit("bahramovai.com не найден в этом аккаунте")


def short(url):
    """Обрезает домен, чтобы таблица читалась."""
    return url.replace("https://bahramovai.com", "") or "/"


def section(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def summary(uid, hid, tok):
    section("ОБЩЕЕ СОСТОЯНИЕ")
    s = call("/user/%s/hosts/%s/summary" % (uid, hid), tok)
    if "_error" in s:
        print("  недоступно: %s" % s["_error"])
        return
    print("  ИКС: %s" % s.get("sqi"))
    print("  Страниц в поиске: %s" % s.get("searchable_pages_count"))
    print("  Исключено из поиска: %s" % s.get("excluded_pages_count"))
    print("  Всего загружено роботом: %s" % s.get("downloaded_pages_count"))
    print("  Проблемы сайта: %s" % json.dumps(s.get("site_problems", {}), ensure_ascii=False))


def queries(uid, hid, tok, limit=40):
    section("ЗАПРОСЫ, ПО КОТОРЫМ НАС ПОКАЗЫВАЮТ (последние 30 дней)")
    date_to = datetime.utcnow().date()
    date_from = date_to - timedelta(days=30)
    params = [
        ("order_by", "TOTAL_SHOWS"),
        ("date_from", date_from.isoformat()),
        ("date_to", date_to.isoformat()),
        ("limit", str(limit)),
    ]
    for ind in ("TOTAL_SHOWS", "TOTAL_CLICKS", "AVG_SHOW_POSITION", "AVG_CLICK_POSITION"):
        params.append(("query_indicator", ind))
    path = "/user/%s/hosts/%s/search-queries/popular?%s" % (
        uid, hid, urllib.parse.urlencode(params))
    r = call(path, tok)
    if "_error" in r:
        print("  недоступно: %s" % r["_error"])
        return
    rows = r.get("queries", [])
    if not rows:
        print("  Яндекс пока не отдаёт запросы — обычно значит, что показов слишком мало.")
        return
    print("  %-46s %7s %7s %8s" % ("запрос", "показы", "клики", "позиция"))
    print("  " + "-" * 72)
    for q in rows:
        ind = q.get("indicators", {})
        print("  %-46s %7s %7s %8s" % (
            q.get("query_text", "")[:46],
            fmt(ind.get("TOTAL_SHOWS")),
            fmt(ind.get("TOTAL_CLICKS")),
            fmt(ind.get("AVG_SHOW_POSITION")),
        ))


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return "%.1f" % v
    return str(v)


def urls_in_search(uid, hid, tok):
    section("СТРАНИЦЫ В ПОИСКЕ (выборка)")
    r = call("/user/%s/hosts/%s/search-urls/in-search/samples?limit=100" % (uid, hid), tok)
    if "_error" in r:
        print("  недоступно: %s" % r["_error"])
    else:
        rows = r.get("samples", [])
        print("  Всего в выборке: %s" % len(rows))
        for s in sorted(rows, key=lambda x: x.get("url", "")):
            print("    %s" % short(s.get("url", "")))

    section("ИСКЛЮЧЁННЫЕ ИЗ ПОИСКА (выборка) — здесь ищем потери")
    r = call("/user/%s/hosts/%s/search-urls/excluded/samples?limit=100" % (uid, hid), tok)
    if "_error" in r:
        print("  недоступно: %s" % r["_error"])
        return
    rows = r.get("samples", [])
    if not rows:
        print("  Пусто — ничего не выкинуто.")
        return
    by_reason = {}
    for s in rows:
        by_reason.setdefault(s.get("status", "?"), []).append(s.get("url", ""))
    for reason, urls in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
        print("  [%s] — %s шт." % (reason, len(urls)))
        for u in sorted(urls)[:25]:
            print("      %s" % short(u))


def main():
    tok = token()
    uid, hid = ids(tok)
    print("Сайт: %s" % hid)
    only_q = "--queries" in sys.argv
    only_u = "--urls" in sys.argv
    if not only_u:
        if not only_q:
            summary(uid, hid, tok)
        queries(uid, hid, tok)
    if not only_q:
        urls_in_search(uid, hid, tok)
    return 0


if __name__ == "__main__":
    sys.exit(main())
