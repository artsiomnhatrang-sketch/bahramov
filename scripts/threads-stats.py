#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Статистика Threads @bahram.av через официальный API.

Показывает по каждому посту показы, лайки, ответы, репосты — и сводку по профилю,
включая клики по ссылкам (переходы на сайт).

Требует прав threads_basic + threads_manage_insights в токене.

    python3 scripts/threads-stats.py            # посты + профиль
    python3 scripts/threads-stats.py --days 7   # профиль за 7 дней
    python3 scripts/threads-stats.py --posts 5  # только последние 5 постов
"""

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.threads.net/v1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POST_METRICS = "views,likes,replies,reposts,quotes,shares"
PROFILE_METRICS = "views,likes,replies,reposts,quotes,followers_count,clicks"


def load_env():
    env = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in os.environ.items():
        if k.startswith(("THREADS_", "TELEGRAM_")):
            env[k] = v          # в облаке .env нет — берём из переменных окружения
    return env


def get(path, params):
    url = "%s/%s?%s" % (API, path.lstrip("/"), urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if "threads_manage_insights" in body:
            print("Нет права threads_manage_insights в токене.\n"
                  "Добавьте право в дашборде Meta и сгенерируйте токен заново.",
                  file=sys.stderr)
        else:
            print("Ошибка API (HTTP %s):\n%s" % (e.code, body), file=sys.stderr)
        sys.exit(1)


def metrics_to_dict(data):
    out = {}
    for m in data.get("data", []):
        name = m.get("name")
        if "values" in m and m["values"]:
            out[name] = m["values"][0].get("value", 0)
        else:
            out[name] = m.get("total_value", {}).get("value", 0)
    return out


def main():
    ap = argparse.ArgumentParser(description="Статистика Threads")
    ap.add_argument("--days", type=int, default=30, help="период для профиля, дней (по умолчанию 30)")
    ap.add_argument("--posts", type=int, default=15, help="сколько последних постов показать")
    ap.add_argument("--json", action="store_true", help="выдать сырой JSON")
    args = ap.parse_args()

    env = load_env()
    token = env.get("THREADS_ACCESS_TOKEN")
    if not token:
        print("Нет THREADS_ACCESS_TOKEN в .env", file=sys.stderr)
        sys.exit(1)

    posts = get("me/threads", {
        "fields": "id,text,permalink,timestamp",
        "limit": args.posts,
        "access_token": token,
    }).get("data", [])

    rows = []
    for p in posts:
        s = metrics_to_dict(get("%s/insights" % p["id"], {
            "metric": POST_METRICS, "access_token": token,
        }))
        rows.append({
            "date": p.get("timestamp", "")[:10],
            "text": ((p.get("text") or "(без текста)").splitlines() or ["(без текста)"])[0][:46],
            "views": s.get("views", 0),
            "likes": s.get("likes", 0),
            "replies": s.get("replies", 0),
            "reposts": s.get("reposts", 0),
            "permalink": p.get("permalink", ""),
        })

    until = datetime.datetime.now()
    since = until - datetime.timedelta(days=args.days)
    profile = metrics_to_dict(get("me/threads_insights", {
        "metric": PROFILE_METRICS,
        "since": int(since.timestamp()),
        "until": int(until.timestamp()),
        "access_token": token,
    }))

    if args.json:
        print(json.dumps({"posts": rows, "profile": profile}, ensure_ascii=False, indent=2))
        return

    print("ПОСТЫ (последние %d)\n" % len(rows))
    print("%-10s %-48s %7s %6s %6s %6s" % ("дата", "начало поста", "показы", "лайки", "ответы", "репост"))
    print("-" * 88)
    for r in rows:
        print("%-10s %-48s %7s %6s %6s %6s" % (
            r["date"], r["text"], r["views"], r["likes"], r["replies"], r["reposts"]))

    if rows:
        total = sum(r["views"] for r in rows)
        print("-" * 88)
        print("%-59s %7s" % ("всего показов", total))
        best = max(rows, key=lambda r: r["views"])
        print("\nЛучший пост: %s показов — %s\n%s" % (best["views"], best["text"], best["permalink"]))

    print("\nПРОФИЛЬ за %d дней" % args.days)
    labels = [
        ("views", "показы профиля"), ("followers_count", "подписчиков"),
        ("likes", "лайки"), ("replies", "ответы"),
        ("reposts", "репосты"), ("quotes", "цитирования"), ("clicks", "клики по ссылкам"),
    ]
    for key, label in labels:
        if key in profile:
            print("  %-22s %s" % (label, profile[key]))


if __name__ == "__main__":
    main()
