#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоответчик на комментарии в Threads @bahram.av.

Раз в N минут проверяет новые комментарии ПОД НАШИМИ постами (из threads/posted.json),
пишет ответ через агента (claude -p) и публикует. Личные посты не трогает.

    python3 scripts/threads-watcher.py --once --dry-run   # показать ответы, не публикуя
    python3 scripts/threads-watcher.py --once             # один проход с публикацией
    python3 scripts/threads-watcher.py --interval 5       # крутиться, проверяя раз в 5 минут

⚠ Требует авторизованного CLI: открыть Терминал, выполнить `claude`, войти.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "threads_replies", os.path.join(ROOT, "scripts", "threads-replies.py"))
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)

LOG = os.path.join(ROOT, "threads", "watcher.log")
MAX_LEN = 500
MAX_IN_THREAD = 3   # предел ответов машины одному человеку в одной ветке

PROMPT = """Ты пишешь ответ на комментарий в Threads от имени Артёма Бахрамова —
специалиста по восстановлению заблокированных аккаунтов Instagram и Telegram
и автоматизации соцсетей. Живёт в Нячанге.

ПОСТ, под которым комментарий:
{post}

КОММЕНТАРИЙ от @{username}:
{comment}

Правила ответа:
- на «вы», живым разговорным языком, без канцелярита и без «спасибо за ваш вопрос»;
- строго до 400 символов;
- по делу: если человек описывает проблему с аккаунтом — дать конкретный первый шаг;
- НЕ выдумывать цифры, сроки, механики Meta и Telegram; не обещать разбан;
- не предлагать способы обхода блокировок и не называть VPN/прокси/антидетект-сервисы;
- если это шутка или болтовня — ответить коротко и по-человечески, без продаж;
- если вопрос агрессивный или провокационный — ответить спокойно и коротко, не спорить;
- если комментарий требует личных данных или разбора конкретного аккаунта —
  пригласить в личные сообщения, без обещаний результата.

Верни ТОЛЬКО текст ответа, без кавычек и пояснений."""


def log(line):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    stamp = datetime.datetime.now().replace(microsecond=0).isoformat()
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("%s  %s\n" % (stamp, line))
    print(line)


def ask_agent(post_text, username, comment):
    """Промпт передаём ТОЛЬКО через stdin: --allowedTools съедает позиционный аргумент."""
    prompt = PROMPT.format(post=post_text[:600], username=username, comment=comment[:600])
    try:
        r = subprocess.run(["claude", "-p"], input=prompt.encode("utf-8"),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        log("Агент не ответил: %s" % e)
        return None
    out = r.stdout.decode("utf-8", "replace").strip()
    err = r.stderr.decode("utf-8", "replace").strip()
    if r.returncode != 0 or not out:
        if "authenticate" in (out + err).lower():
            log("CLI claude не авторизован. Откройте Терминал, выполните `claude` и войдите.")
        else:
            log("Агент вернул ошибку: %s" % (err or out)[:200])
        return None
    if len(out) > MAX_LEN:
        out = out[:MAX_LEN].rsplit(" ", 1)[0]
    return out


def pass_once(env, dry_run):
    token = env["THREADS_ACCESS_TOKEN"]
    me = tr.call("GET", "me", {"fields": "id,username", "access_token": token})
    ours = tr.our_post_urls()
    if not ours:
        log("В threads/posted.json нет наших постов — нечего проверять.")
        return 0

    replied = tr.load_replied()
    posts = tr.call("GET", "me/threads", {
        "fields": "id,text,permalink,timestamp", "limit": 25, "access_token": token,
    }).get("data", [])

    answered = 0
    for p in posts:
        if p.get("permalink", "").rstrip("/") not in ours:
            continue
        # вся ветка, включая ответы на наши ответы
        convo = tr.call("GET", "%s/conversation" % p["id"], {
            "fields": "id,text,username,timestamp,replied_to", "access_token": token,
        }).get("data", [])

        # сколько раз мы уже отвечали каждому в этой ветке —
        # чтобы не уйти в бесконечную переписку с одним человеком
        mine_to = {}
        by_id = {c["id"]: c for c in convo}
        for c in convo:
            if c.get("username") != me.get("username"):
                continue
            parent = by_id.get((c.get("replied_to") or {}).get("id"))
            if parent:
                u = parent.get("username")
                mine_to[u] = mine_to.get(u, 0) + 1

        for c in convo:
            if c.get("username") == me.get("username") or c["id"] in replied:
                continue
            comment = c.get("text") or ""
            if not comment.strip():
                continue
            if mine_to.get(c.get("username"), 0) >= MAX_IN_THREAD:
                log("@%s: уже %d ответа в ветке — дальше отвечает Артём сам."
                    % (c.get("username"), mine_to[c.get("username")]))
                continue

            log("Новый комментарий от @%s: %s" % (c.get("username"), comment[:80]))
            answer = ask_agent(p.get("text") or "", c.get("username", "?"), comment)
            if not answer:
                continue

            if dry_run:
                log("[dry-run] Ответ был бы такой:\n%s\n" % answer)
                continue

            tr.cmd_reply(env, c["id"], answer)
            answered += 1
            time.sleep(5)
    if answered == 0 and not dry_run:
        log("Новых комментариев нет.")
    return answered


def main():
    ap = argparse.ArgumentParser(description="Автоответчик Threads")
    ap.add_argument("--once", action="store_true", help="один проход и выход")
    ap.add_argument("--interval", type=int, default=5, help="минуты между проверками")
    ap.add_argument("--dry-run", action="store_true", help="показать ответы, не публикуя")
    args = ap.parse_args()

    env = tr.load_env()
    if not env.get("THREADS_ACCESS_TOKEN"):
        print("Нет THREADS_ACCESS_TOKEN в .env", file=sys.stderr)
        sys.exit(1)

    if args.once:
        pass_once(env, args.dry_run)
        return

    log("Автоответчик запущен, проверка раз в %d мин. Ctrl+C для остановки." % args.interval)
    while True:
        try:
            pass_once(env, args.dry_run)
        except SystemExit:
            log("Ошибка API, жду следующий круг.")
        except Exception as e:
            log("Сбой: %s" % e)
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
