#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Статистика Instagram @bahram.av через официальный Instagram API (graph.instagram.com).

Показывает по каждой публикации показы, охват, лайки, комментарии, сохранения
и репосты, сводку по формату (Reels / фото / карусель) и профиль за период.

Требует прав instagram_business_basic + instagram_business_manage_insights.

    python3 scripts/instagram-stats.py                # 25 последних публикаций + профиль
    python3 scripts/instagram-stats.py --posts 50     # больше публикаций
    python3 scripts/instagram-stats.py --days 90      # профиль за 90 дней
    python3 scripts/instagram-stats.py --json         # сырые данные
    python3 scripts/instagram-stats.py --refresh-token  # продлить токен на 60 дней
"""

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.instagram.com/v23.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Наборы метрик пробуются по очереди: Meta регулярно меняет состав,
# поэтому при отказе сваливаемся на более скромный набор, а не падаем.
MEDIA_METRICS = {
    "REELS": [
        "views,reach,likes,comments,saved,shares,total_interactions",
        "views,reach,likes,comments,saved",
        "reach,likes,comments",
    ],
    "DEFAULT": [
        "views,reach,likes,comments,saved,shares,total_interactions,profile_visits,follows",
        "views,reach,likes,comments,saved,shares,total_interactions",
        "views,reach,likes,comments,saved",
        "reach,likes,comments",
    ],
}
PROFILE_METRICS = [
    "reach,views,profile_views,accounts_engaged,total_interactions,website_clicks",
    "reach,profile_views,accounts_engaged,total_interactions",
    "reach,profile_views",
    "reach",
]

TYPE_LABEL = {
    "REELS": "Reels",
    "FEED": "пост",
    "AD": "реклама",
    "STORY": "сторис",
    "CAROUSEL_ALBUM": "карусель",
    "IMAGE": "фото",
    "VIDEO": "видео",
}


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
        if k.startswith("INSTAGRAM_"):
            env[k] = v          # в облаке .env нет — берём из переменных окружения
    return env


def get(path, params, quiet=False):
    url = "%s/%s?%s" % (API, path.lstrip("/"), urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if quiet:
            raise
        if "instagram_business_manage_insights" in body or "insights" in body.lower():
            print("Похоже, в токене нет права instagram_business_manage_insights.\n"
                  "Добавьте право в дашборде Meta и сгенерируйте токен заново.",
                  file=sys.stderr)
        print("Ошибка API (HTTP %s):\n%s" % (e.code, body), file=sys.stderr)
        sys.exit(1)


def metrics_to_dict(data):
    out = {}
    for m in data.get("data", []):
        name = m.get("name")
        if m.get("total_value") is not None:
            out[name] = m["total_value"].get("value", 0)
        elif m.get("values"):
            out[name] = m["values"][0].get("value", 0)
    return out


def media_insights(media_id, product_type, token):
    variants = MEDIA_METRICS.get(product_type, MEDIA_METRICS["DEFAULT"])
    for metric in variants:
        try:
            return metrics_to_dict(get("%s/insights" % media_id,
                                       {"metric": metric, "access_token": token}, quiet=True))
        except urllib.error.HTTPError:
            continue
    return {}


def profile_insights(user_id, token, days):
    until = datetime.datetime.now()
    since = until - datetime.timedelta(days=min(days, 30))   # API отдаёт максимум 30 дней за раз
    for metric in PROFILE_METRICS:
        try:
            return metrics_to_dict(get("%s/insights" % user_id, {
                "metric": metric,
                "metric_type": "total_value",
                "period": "day",
                "since": int(since.timestamp()),
                "until": int(until.timestamp()),
                "access_token": token,
            }, quiet=True)), int((until - since).days)
        except urllib.error.HTTPError:
            continue
    return {}, 0


def save_token(token):
    path = os.path.join(ROOT, ".env")
    today = datetime.date.today().isoformat()
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
    out, seen_token, seen_date = [], False, False
    for line in lines:
        if line.startswith("INSTAGRAM_ACCESS_TOKEN="):
            out.append("INSTAGRAM_ACCESS_TOKEN=%s" % token); seen_token = True
        elif line.startswith("INSTAGRAM_TOKEN_REFRESHED="):
            out.append("INSTAGRAM_TOKEN_REFRESHED=%s" % today); seen_date = True
        else:
            out.append(line)
    if not seen_token:
        out.append("INSTAGRAM_ACCESS_TOKEN=%s" % token)
    if not seen_date:
        out.append("INSTAGRAM_TOKEN_REFRESHED=%s" % today)
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    os.chmod(path, 0o600)


def cmd_refresh(env):
    r = get("refresh_access_token", {
        "grant_type": "ig_refresh_token",
        "access_token": env["INSTAGRAM_ACCESS_TOKEN"],
    })
    save_token(r["access_token"])
    days = int(r.get("expires_in", 0)) // 86400
    print("Токен продлён и записан в .env" + (", действует ещё %d дней" % days if days else ""))


def first_line(caption):
    text = (caption or "(без подписи)").strip().splitlines()
    return (text[0] if text else "(без подписи)")[:44]


def main():
    ap = argparse.ArgumentParser(description="Статистика Instagram")
    ap.add_argument("--posts", type=int, default=25, help="сколько последних публикаций (по умолчанию 25)")
    ap.add_argument("--days", type=int, default=30, help="период для профиля, дней (максимум 30)")
    ap.add_argument("--json", action="store_true", help="выдать сырой JSON")
    ap.add_argument("--refresh-token", action="store_true", help="продлить токен на 60 дней")
    args = ap.parse_args()

    env = load_env()
    token = env.get("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        print("Нет INSTAGRAM_ACCESS_TOKEN в .env.\n"
              "Сначала пройдите настройку приложения Instagram в дашборде Meta.", file=sys.stderr)
        sys.exit(1)
    user_id = env.get("INSTAGRAM_USER_ID", "me")

    if args.refresh_token:
        cmd_refresh(env); return

    me = get(user_id, {
        "fields": "id,username,followers_count,media_count",
        "access_token": token,
    })

    media = get("%s/media" % user_id, {
        "fields": "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count",
        "limit": args.posts,
        "access_token": token,
    }).get("data", [])

    rows = []
    for m in media:
        product = m.get("media_product_type") or m.get("media_type") or "FEED"
        s = media_insights(m["id"], product, token)
        kind = product if product == "REELS" else (m.get("media_type") or product)
        rows.append({
            "date": (m.get("timestamp") or "")[:10],
            "kind": TYPE_LABEL.get(kind, kind.lower()),
            "text": first_line(m.get("caption")),
            "views": s.get("views", 0),
            "reach": s.get("reach", 0),
            "likes": s.get("likes", m.get("like_count", 0)),
            "comments": s.get("comments", m.get("comments_count", 0)),
            "saved": s.get("saved", 0),
            "shares": s.get("shares", 0),
            "permalink": m.get("permalink", ""),
        })

    profile, period = profile_insights(user_id, token, args.days)

    if args.json:
        print(json.dumps({"account": me, "posts": rows, "profile": profile},
                         ensure_ascii=False, indent=2))
        return

    print("АККАУНТ @%s — %s подписчиков, %s публикаций\n" % (
        me.get("username", "?"), me.get("followers_count", "?"), me.get("media_count", "?")))

    print("ПУБЛИКАЦИИ (последние %d)\n" % len(rows))
    head = "%-10s %-9s %-46s %7s %7s %6s %5s %5s"
    print(head % ("дата", "формат", "начало подписи", "показы", "охват", "лайки", "комм", "сохр"))
    print("-" * 104)
    for r in rows:
        print(head % (r["date"], r["kind"], r["text"],
                      r["views"], r["reach"], r["likes"], r["comments"], r["saved"]))

    if rows:
        print("\nПО ФОРМАТАМ (среднее на публикацию)\n")
        kinds = {}
        for r in rows:
            kinds.setdefault(r["kind"], []).append(r)
        print("%-10s %5s %9s %9s %8s %8s" % ("формат", "штук", "показы", "охват", "лайки", "сохр"))
        print("-" * 54)
        for kind, items in sorted(kinds.items(), key=lambda kv: -sum(i["views"] for i in kv[1])):
            n = len(items)
            print("%-10s %5d %9d %9d %8.1f %8.1f" % (
                kind, n,
                sum(i["views"] for i in items) // n,
                sum(i["reach"] for i in items) // n,
                sum(i["likes"] for i in items) / n,
                sum(i["saved"] for i in items) / n))

        best = max(rows, key=lambda r: r["views"])
        worst = min(rows, key=lambda r: r["views"])
        print("\nЛучшая:  %s показов (%s) — %s\n         %s" % (
            best["views"], best["kind"], best["text"], best["permalink"]))
        print("Слабая:  %s показов (%s) — %s" % (worst["views"], worst["kind"], worst["text"]))

    if profile:
        print("\nПРОФИЛЬ за %d дней\n" % period)
        labels = [
            ("views", "показы"), ("reach", "охват"), ("profile_views", "просмотры профиля"),
            ("accounts_engaged", "вовлечённых аккаунтов"), ("total_interactions", "взаимодействий"),
            ("website_clicks", "клики по ссылке в шапке"),
        ]
        for key, label in labels:
            if key in profile:
                print("  %-26s %s" % (label, profile[key]))


if __name__ == "__main__":
    main()
