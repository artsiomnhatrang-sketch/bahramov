#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Комментарии в Threads @bahram.av: читать и отвечать через официальный API.

    python3 scripts/threads-replies.py --list          # неотвеченные комментарии
    python3 scripts/threads-replies.py --list --all    # включая уже отвеченные
    python3 scripts/threads-replies.py --reply <id> --text "..."

Отвеченное пишется в threads/replied.json, чтобы не отвечать дважды.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.threads.net/v1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLIED = os.path.join(ROOT, "threads", "replied.json")
JOURNAL = os.path.join(ROOT, "threads", "posted.json")
MAX_LEN = 500


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


def call(method, path, params):
    url = "%s/%s" % (API, path.lstrip("/"))
    data = urllib.parse.urlencode(params).encode("utf-8")
    if method == "GET":
        req = urllib.request.Request("%s?%s" % (url, data.decode("utf-8")), method="GET")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("Ошибка API (HTTP %s):\n%s" % (e.code, e.read().decode("utf-8", "replace")),
              file=sys.stderr)
        sys.exit(1)



def our_post_urls():
    """Ссылки постов, опубликованных через наш скрипт (журнал threads/posted.json).
    Автоответы идут только под ними: под личными постами Артём отвечает сам."""
    if not os.path.exists(JOURNAL):
        return set()
    try:
        return {e.get("url", "").rstrip("/") for e in json.load(open(JOURNAL, encoding="utf-8"))}
    except ValueError:
        return set()


def load_replied():
    if os.path.exists(REPLIED):
        try:
            return json.load(open(REPLIED, encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def save_replied(data):
    os.makedirs(os.path.dirname(REPLIED), exist_ok=True)
    json.dump(data, open(REPLIED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def cmd_list(env, show_all, posts_limit, only_ours):
    token = env["THREADS_ACCESS_TOKEN"]
    me = call("GET", "me", {"fields": "id,username", "access_token": token})
    replied = load_replied()

    posts = call("GET", "me/threads", {
        "fields": "id,text,permalink,timestamp",
        "limit": posts_limit, "access_token": token,
    }).get("data", [])

    ours = our_post_urls()
    if only_ours and not ours:
        print("В threads/posted.json нет наших постов — нечего проверять.")
        return

    found = 0
    for p in posts:
        if only_ours and p.get("permalink", "").rstrip("/") not in ours:
            continue
        # /conversation — вся ветка, включая ответы на ответы.
        # /replies отдаёт только верхний уровень и теряет продолжение диалога.
        convo = call("GET", "%s/conversation" % p["id"], {
            "fields": "id,text,username,timestamp,replied_to",
            "reverse": "false", "access_token": token,
        }).get("data", [])

        # На что мы уже ответили — определяем ПО САМОЙ ВЕТКЕ, а не по журналу:
        # локальный агент и облако ведут разные журналы, и на один комментарий
        # прилетело бы два ответа.
        answered_ids = set()
        for r in convo:
            if r.get("username") == me.get("username"):
                parent = (r.get("replied_to") or {}).get("id")
                if parent:
                    answered_ids.add(parent)

        mine = []
        for r in convo:
            if r.get("username") == me.get("username"):
                continue           # свои же ответы
            if not show_all and (r["id"] in answered_ids or r["id"] in replied):
                continue           # уже отвечали
            mine.append(r)

        if not mine:
            continue

        head = ((p.get("text") or "(без текста)").splitlines() or ["(без текста)"])[0][:60]
        print("\n=== ПОСТ: %s" % head)
        print("    %s" % p.get("permalink", ""))
        for r in mine:
            found += 1
            mark = " [отвечено]" if r["id"] in replied else ""
            print("  • @%s (%s)%s" % (r.get("username", "?"), r.get("timestamp", "")[:16], mark))
            print("    id: %s" % r["id"])
            for line in (r.get("text") or "(без текста)").splitlines():
                print("    %s" % line)
    if not found:
        print("Новых комментариев без ответа нет.")
    else:
        print("\nВсего: %d" % found)


def cmd_reply(env, reply_to, text):
    if len(text) > MAX_LEN:
        print("Ответ длиннее %d символов." % MAX_LEN, file=sys.stderr)
        sys.exit(1)
    token = env["THREADS_ACCESS_TOKEN"]
    uid = env.get("THREADS_USER_ID", "me")

    c = call("POST", "%s/threads" % uid, {
        "media_type": "TEXT", "text": text,
        "reply_to_id": reply_to, "access_token": token,
    })
    print("Контейнер создан, ждём 20 сек…")
    time.sleep(20)
    p = call("POST", "%s/threads_publish" % uid, {
        "creation_id": c["id"], "access_token": token,
    })
    perma = call("GET", p["id"], {"fields": "permalink", "access_token": token})

    replied = load_replied()
    replied[reply_to] = {"reply_id": p["id"], "url": perma.get("permalink", ""), "text": text}
    save_replied(replied)
    print("Ответ опубликован: %s" % perma.get("permalink", p["id"]))


def main():
    ap = argparse.ArgumentParser(description="Комментарии Threads")
    ap.add_argument("--list", action="store_true", help="показать комментарии")
    ap.add_argument("--all", action="store_true", help="включая уже отвеченные")
    ap.add_argument("--ours", action="store_true",
                    help="только под нашими постами из журнала (личные посты не трогать)")
    ap.add_argument("--posts", type=int, default=10, help="сколько последних постов смотреть")
    ap.add_argument("--reply", metavar="ID", help="id комментария, на который отвечаем")
    ap.add_argument("--text", help="текст ответа")
    args = ap.parse_args()

    env = load_env()
    if not env.get("THREADS_ACCESS_TOKEN"):
        print("Нет THREADS_ACCESS_TOKEN в .env", file=sys.stderr)
        sys.exit(1)

    if args.reply:
        if not args.text:
            print("Нужен --text", file=sys.stderr)
            sys.exit(1)
        cmd_reply(env, args.reply, args.text)
    else:
        cmd_list(env, args.all, args.posts, args.ours)


if __name__ == "__main__":
    main()
