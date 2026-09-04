#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Публикация текстового поста в Threads через ОФИЦИАЛЬНЫЙ Threads API (graph.threads.net).

Никакой эмуляции входа: только OAuth-токен, выданный Meta. Права токена —
threads_basic + threads_content_publish. Доступа к Instagram токен не даёт.

Ключи в .env:
    THREADS_ACCESS_TOKEN=...   # long-lived, 60 дней
    THREADS_USER_ID=...        # id профиля Threads

Использование:
    python3 scripts/threads-post.py --check                 # кто я, жив ли токен
    python3 scripts/threads-post.py --file draft.txt --dry-run
    python3 scripts/threads-post.py --file draft.txt        # публикация (спросит подтверждение)
    python3 scripts/threads-post.py --refresh-token         # продлить токен на 60 дней
"""

import argparse
import datetime
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

API = "https://graph.threads.net/v1.0"
MAX_LEN = 500          # лимит Threads на текстовый пост
DAILY_LIMIT = 250      # лимит Meta: постов на профиль за 24 часа
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    path = os.path.join(ROOT, ".env")
    env = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    env.update({k: v for k, v in os.environ.items() if k.startswith("THREADS_")})
    return env


def call(method, path, params):
    url = "%s/%s" % (API, path.lstrip("/"))
    data = urllib.parse.urlencode(params).encode("utf-8")
    if method == "GET":
        url = "%s?%s" % (url, data.decode("utf-8"))
        req = urllib.request.Request(url, method="GET")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print("Ошибка Threads API (HTTP %s):\n%s" % (e.code, body), file=sys.stderr)
        sys.exit(1)


def text_len(s):
    """Threads считает длину в UTF-8 байтах для эмодзи; для кириллицы — символы."""
    return len(s)


def cmd_check(env):
    me = call("GET", "%s" % env["THREADS_USER_ID"], {
        "fields": "id,username,threads_profile_picture_url",
        "access_token": env["THREADS_ACCESS_TOKEN"],
    })
    print("Токен живой. Профиль: @%s (id %s)" % (me.get("username", "?"), me.get("id")))
    return me



def save_token(token):
    """Пишет токен в .env вместе с датой обновления (по ней считаем возраст)."""
    today = datetime.date.today().isoformat()
    path = os.path.join(ROOT, ".env")
    lines = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    out, seen, seen_date = [], False, False
    for line in lines:
        if line.startswith("THREADS_ACCESS_TOKEN="):
            out.append("THREADS_ACCESS_TOKEN=%s" % token)
            seen = True
        elif line.startswith("THREADS_TOKEN_REFRESHED="):
            out.append("THREADS_TOKEN_REFRESHED=%s" % today)
            seen_date = True
        else:
            out.append(line)
    if not seen:
        out.append("THREADS_ACCESS_TOKEN=%s" % token)
    if not seen_date:
        out.append("THREADS_TOKEN_REFRESHED=%s" % today)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    os.chmod(path, 0o600)


def cmd_exchange(env, secret):
    """Часовой токен из генератора -> долгий на 60 дней."""
    r = call("GET", "access_token", {
        "grant_type": "th_exchange_token",
        "client_secret": secret,
        "access_token": env["THREADS_ACCESS_TOKEN"],
    })
    token = r.get("access_token")
    days = int(r.get("expires_in", 0)) // 86400
    if not token:
        print("Не пришёл длинный токен: %s" % r, file=sys.stderr)
        sys.exit(1)
    save_token(token)
    print("Получен долгий токен на %d дней, записан в .env" % days)


def cmd_refresh(env):
    r = call("GET", "refresh_access_token", {
        "grant_type": "th_refresh_token",
        "access_token": env["THREADS_ACCESS_TOKEN"],
    })
    token = r.get("access_token")
    days = int(r.get("expires_in", 0)) // 86400
    if not token:
        print("Не пришёл новый токен: %s" % r, file=sys.stderr)
        sys.exit(1)
    save_token(token)
    print("Токен продлён на %d дней и записан в .env" % days)


def publish(env, text, dry_run, assume_yes, path=None):
    n = text_len(text)
    print("--- текст поста (%d из %d символов) ---" % (n, MAX_LEN))
    print(text)
    print("--- конец ---")
    if n > MAX_LEN:
        print("СТОП: текст длиннее лимита Threads на %d символов." % (n - MAX_LEN), file=sys.stderr)
        sys.exit(1)
    if dry_run:
        print("\n[dry-run] Ничего не опубликовано.")
        return

    if not assume_yes:
        print("\nПубликуем в Threads? [y/N]: ", end="")
        if input().strip().lower() not in ("y", "yes", "д", "да"):
            print("Отменено.")
            return

    uid = env["THREADS_USER_ID"]
    token = env["THREADS_ACCESS_TOKEN"]

    c = call("POST", "%s/threads" % uid, {
        "media_type": "TEXT", "text": text, "access_token": token,
    })
    creation_id = c.get("id")
    print("Контейнер создан: %s. Ждём обработку 30 сек…" % creation_id)
    time.sleep(30)

    p = call("POST", "%s/threads_publish" % uid, {
        "creation_id": creation_id, "access_token": token,
    })
    post_id = p.get("id")
    perma = call("GET", "%s" % post_id, {
        "fields": "permalink", "access_token": token,
    })
    url = perma.get("permalink", post_id)
    record(path, url, text)
    print("Опубликовано: %s" % url)





QUEUE_DIR = os.path.join(ROOT, "threads", "queue")
POSTED_DIR = os.path.join(ROOT, "threads", "posted")
JOURNAL = os.path.join(ROOT, "threads", "posted.json")


def record(path, url, text):
    """Пишет публикацию в журнал и убирает файл из очереди."""
    entry = {
        "file": os.path.basename(path) if path else "(inline)",
        "url": url,
        "published_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "first_line": text.strip().splitlines()[0][:90],
    }
    log = []
    if os.path.exists(JOURNAL):
        try:
            log = json.load(open(JOURNAL, encoding="utf-8"))
        except ValueError:
            log = []
    log.append(entry)
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    json.dump(log, open(JOURNAL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    if path and os.path.dirname(os.path.abspath(path)) == os.path.abspath(QUEUE_DIR):
        os.makedirs(POSTED_DIR, exist_ok=True)
        os.rename(path, os.path.join(POSTED_DIR, os.path.basename(path)))
        print("Файл перенесён в threads/posted/")


def token_age_days(env):
    stamp = env.get("THREADS_TOKEN_REFRESHED")
    if not stamp:
        return None
    try:
        y, m, d = [int(x) for x in stamp.split("-")]
        return (datetime.date.today() - datetime.date(y, m, d)).days
    except ValueError:
        return None


def autorefresh(env):
    """Токен живёт 60 дней и продлевается бесконечно, пока не истёк.
    Продлеваем на 30-й день — с запасом, чтобы не зависеть от регулярности постинга."""
    age = token_age_days(env)
    if age is None:
        print("В .env нет THREADS_TOKEN_REFRESHED — возраст токена неизвестен, продлеваю на всякий случай.")
    elif age < 30:
        return
    else:
        print("Токену %d дней — продлеваю до публикации." % age)
    try:
        cmd_refresh(env)
        env.update(load_env())
    except SystemExit:
        print("Продлить не вышло. Если токен истёк — сгенерируйте новый в App Dashboard "
              "(приложение пересоздавать НЕ нужно).", file=sys.stderr)
        raise


def publish_queue(env, paths, dry_run, assume_yes, min_gap, max_gap):
    """Публикует пачку постов с паузой между ними (без пауз — машинный след)."""
    posts = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            posts.append((path, f.read().strip()))

    print("В очереди %d постов, пауза между ними %d-%d минут.\n" % (
        len(posts), min_gap // 60, max_gap // 60))
    bad = False
    for path, text in posts:
        n = text_len(text)
        mark = "OK " if n <= MAX_LEN else "ДЛИННО"
        print("[%s] %s (%d симв.)" % (mark, os.path.basename(path), n))
        if n > MAX_LEN:
            bad = True
    if bad:
        print("\nСТОП: есть посты длиннее %d символов." % MAX_LEN, file=sys.stderr)
        sys.exit(1)
    if dry_run:
        print("\n[dry-run] Ничего не опубликовано.")
        return
    if not assume_yes:
        print("\nПубликуем всю очередь? [y/N]: ", end="")
        if input().strip().lower() not in ("y", "yes", "д", "да"):
            print("Отменено.")
            return

    for i, (path, text) in enumerate(posts):
        print("\n=== %d из %d: %s ===" % (i + 1, len(posts), os.path.basename(path)))
        publish(env, text, dry_run=False, assume_yes=True, path=path)
        if i < len(posts) - 1:
            gap = random.randint(min_gap, max_gap)
            print("Пауза %d мин %d сек до следующего поста…" % (gap // 60, gap % 60))
            time.sleep(gap)
    print("\nОчередь отработана: %d постов." % len(posts))


def main():
    ap = argparse.ArgumentParser(description="Пост в Threads через официальный API")
    ap.add_argument("--file", help="файл с текстом поста")
    ap.add_argument("--text", help="текст поста строкой")
    ap.add_argument("--dry-run", action="store_true", help="показать и не публиковать")
    ap.add_argument("--yes", action="store_true", help="без вопроса о подтверждении")
    ap.add_argument("--all", action="store_true",
                    help="опубликовать всё из threads/queue по очереди")
    ap.add_argument("--queue", nargs="+", metavar="FILE",
                    help="пачка файлов: публикует по очереди с паузами")
    ap.add_argument("--gap", default="30-50", metavar="MIN-MAX",
                    help="пауза между постами очереди в минутах, по умолчанию 30-50")
    ap.add_argument("--check", action="store_true", help="проверить токен и профиль")
    ap.add_argument("--refresh-token", action="store_true", help="продлить токен на 60 дней")
    ap.add_argument("--exchange-token", metavar="APP_SECRET",
                    help="обменять часовой токен на 60-дневный (нужен Threads App Secret)")
    args = ap.parse_args()

    env = load_env()
    env.setdefault("THREADS_USER_ID", "me")
    if not env.get("THREADS_USER_ID"):
        env["THREADS_USER_ID"] = "me"
    if not env.get("THREADS_ACCESS_TOKEN") and not args.dry_run:
        print("Нет THREADS_ACCESS_TOKEN в .env.\nСначала пройдите настройку приложения Threads.",
              file=sys.stderr)
        sys.exit(1)

    if args.exchange_token:
        cmd_exchange(env, args.exchange_token); return
    if args.check:
        cmd_check(env); return
    if args.refresh_token:
        cmd_refresh(env); return

    if not args.dry_run:
        autorefresh(env)

    if args.all:
        files = sorted(os.path.join(QUEUE_DIR, f) for f in os.listdir(QUEUE_DIR)
                       if f.endswith(".txt")) if os.path.isdir(QUEUE_DIR) else []
        if not files:
            print("В threads/queue пусто — нечего публиковать.")
            return
        args.queue = files

    if args.queue:
        lo, _, hi = args.gap.partition("-")
        publish_queue(env, args.queue, args.dry_run, args.yes,
                      int(lo) * 60, int(hi or lo) * 60)
        return

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read().strip()
    elif args.text:
        text = args.text.strip()
    else:
        print("Нужен --file или --text (или --check / --refresh-token).", file=sys.stderr)
        sys.exit(1)

    publish(env, text, args.dry_run, args.yes, path=args.file)


if __name__ == "__main__":
    main()
