#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Публикация ЦЕПОЧКИ постов в Threads: первый пост, остальные — ответами к нему.
Так длинный текст читается целиком и не теряет контекст.

Файл делится на части строкой из трёх дефисов на отдельной строке.
Каждая часть должна быть не длиннее 500 символов.

    python3 scripts/threads-chain.py --file threads/queue/NN-имя.txt --dry-run
    python3 scripts/threads-chain.py --file threads/queue/NN-имя.txt --yes
"""
import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from importlib import import_module
tp = import_module("threads-post".replace("-", "_")) if False else None

# threads-post.py содержит дефис в имени, импортируем через loader
import importlib.util
spec = importlib.util.spec_from_file_location("tpost", os.path.join(HERE, "threads-post.py"))
tpost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tpost)

LIMIT = 500


def split_parts(text):
    parts = [p.strip() for p in text.split("\n---\n")]
    return [p for p in parts if p]


def publish_chain(env, parts, dry_run=False, yes=False):
    print("--- цепочка из %d частей ---" % len(parts))
    bad = False
    for i, p in enumerate(parts, 1):
        mark = "ok" if len(p) <= LIMIT else "ПРЕВЫШЕНИЕ"
        if len(p) > LIMIT:
            bad = True
        print("\n[%d/%d] %d символов — %s" % (i, len(parts), len(p), mark))
        print(p)
    print("\n--- конец ---")
    if bad:
        print("\nЕсть части длиннее %d символов, публикация отменена." % LIMIT)
        return
    if dry_run:
        return
    if not yes:
        sys.stdout.write("Публикуем цепочку? [y/N]: ")
        sys.stdout.flush()
        if input().strip().lower() not in ("y", "yes", "д", "да"):
            print("Отменено.")
            return

    uid = env["THREADS_USER_ID"]
    token = env["THREADS_ACCESS_TOKEN"]
    root_url = None
    prev_id = None

    for i, text in enumerate(parts, 1):
        payload = {"media_type": "TEXT", "text": text, "access_token": token}
        if prev_id:
            payload["reply_to_id"] = prev_id
        c = tpost.call("POST", "%s/threads" % uid, payload)
        creation_id = c.get("id")
        print("[%d/%d] контейнер %s, ждём 30 сек…" % (i, len(parts), creation_id))
        time.sleep(30)
        p = tpost.call("POST", "%s/threads_publish" % uid,
                       {"creation_id": creation_id, "access_token": token})
        prev_id = p.get("id")
        if i == 1:
            perma = tpost.call("GET", "%s" % prev_id,
                               {"fields": "permalink", "access_token": token})
            root_url = perma.get("permalink", prev_id)
            print("Первый пост: %s" % root_url)
        else:
            print("[%d/%d] опубликовано" % (i, len(parts)))
        if i < len(parts):
            time.sleep(5)

    print("\nЦепочка опубликована: %s" % root_url)
    return root_url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="файл с частями через ---")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    env = tpost.load_env()
    text = open(args.file, encoding="utf-8").read()
    parts = split_parts(text)
    if not parts:
        print("Файл пуст.")
        return
    url = publish_chain(env, parts, args.dry_run, args.yes)
    if url and not args.dry_run:
        tpost.record(args.file, url, parts[0])
        print("Записано в журнал.")


if __name__ == "__main__":
    main()
