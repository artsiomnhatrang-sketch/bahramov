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
import random
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

# ---------------------------------------------------------------------------
# Бережный режим. 06.09.2026 Meta заблокировала аккаунт разработчика
# с формулировкой «обнаружены необычные действия»: агент опрашивал API
# каждые 3 минуты и делал 7 запросов за проход — около 3360 запросов в сутки.
# Ниже — всё, что снижает это число и делает трафик похожим на человека.
# ---------------------------------------------------------------------------
FRESH_HOURS = 72        # опрашиваем только посты моложе трёх суток:
                        # комментарии приходят в первые дни, дальше ветка мертва
POSTS_LIMIT = 10        # было 25 — столько за раз всё равно не нужно
QUIET_FROM, QUIET_TO = 0, 7   # ночью по Нячангу не ходим в API вовсе
JITTER_MAX = 90         # случайная пауза перед стартом: не бить ровно по таймеру
PAUSE_FILE = os.path.join(ROOT, "threads", ".api-pause")
PAUSE_AFTER_ERROR_H = 2  # после ошибки API молчим два часа, а не долбим дальше
ME_CACHE = os.path.join(ROOT, "threads", ".me.json")


def in_quiet_hours():
    h = datetime.datetime.now().hour
    return QUIET_FROM <= h < QUIET_TO


def paused_until():
    """Сколько ещё молчать после ошибки API. 0 — можно работать."""
    if not os.path.exists(PAUSE_FILE):
        return 0
    try:
        until = float(open(PAUSE_FILE, encoding="utf-8").read().strip())
    except (ValueError, OSError):
        return 0
    left = until - time.time()
    return left if left > 0 else 0


def set_pause(hours=PAUSE_AFTER_ERROR_H):
    os.makedirs(os.path.dirname(PAUSE_FILE), exist_ok=True)
    with open(PAUSE_FILE, "w", encoding="utf-8") as f:
        f.write(str(time.time() + hours * 3600))


def clear_pause():
    if os.path.exists(PAUSE_FILE):
        os.remove(PAUSE_FILE)


def safe_call(method, path, params):
    """Обёртка над API: ошибка не роняет процесс, а включает паузу.

    Иначе launchd перезапускает скрипт по расписанию, и при блокировке
    получается сотня безответных запросов в сутки — ровно то, из-за чего
    аккаунт разработчика и заблокировали."""
    try:
        return tr.call(method, path, params)
    except SystemExit:
        set_pause()
        log("Ошибка API — пауза %d ч, чтобы не усугублять." % PAUSE_AFTER_ERROR_H)
        return None


def cached_me(token):
    """Профиль не меняется — незачем спрашивать его каждые полчаса."""
    if os.path.exists(ME_CACHE):
        try:
            return json.load(open(ME_CACHE, encoding="utf-8"))
        except ValueError:
            pass
    me = safe_call("GET", "me", {"fields": "id,username", "access_token": token})
    if me:
        os.makedirs(os.path.dirname(ME_CACHE), exist_ok=True)
        json.dump(me, open(ME_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return me


def is_fresh(post):
    """Пост моложе FRESH_HOURS. Старые ветки не опрашиваем вовсе."""
    ts = post.get("timestamp") or ""
    try:
        t = datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return True     # не смогли разобрать дату — лучше проверить
    age = (datetime.datetime.utcnow() - t).total_seconds() / 3600
    return age <= FRESH_HOURS

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
    me = cached_me(token)
    if me is None:
        return 0
    ours = tr.our_post_urls()
    if not ours:
        log("В threads/posted.json нет наших постов — нечего проверять.")
        return 0

    replied = tr.load_replied()
    resp = safe_call("GET", "me/threads", {
        "fields": "id,text,permalink,timestamp",
        "limit": POSTS_LIMIT, "access_token": token,
    })
    if resp is None:
        return 0
    posts = resp.get("data", [])

    answered = 0
    checked = 0
    for p in posts:
        if p.get("permalink", "").rstrip("/") not in ours:
            continue
        if not is_fresh(p):
            continue          # ветка старше трёх суток — комментариев там уже нет
        checked += 1
        # вся ветка, включая ответы на наши ответы
        convo_resp = safe_call("GET", "%s/conversation" % p["id"], {
            "fields": "id,text,username,timestamp,replied_to", "access_token": token,
        })
        if convo_resp is None:
            return answered
        convo = convo_resp.get("data", [])

        # сколько раз мы уже отвечали каждому в этой ветке —
        # чтобы не уйти в бесконечную переписку с одним человеком
        mine_to = {}
        answered_ids = set()
        by_id = {c["id"]: c for c in convo}
        for c in convo:
            if c.get("username") != me.get("username"):
                continue
            pid = (c.get("replied_to") or {}).get("id")
            if pid:
                answered_ids.add(pid)
            parent = by_id.get(pid)
            if parent:
                u = parent.get("username")
                mine_to[u] = mine_to.get(u, 0) + 1

        for c in convo:
            if c.get("username") == me.get("username") or c["id"] in replied:
                continue
            if c["id"] in answered_ids:
                continue           # ответ уже есть в ветке (мог дать облачный агент)
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
        log("Новых комментариев нет (проверено веток: %d)." % checked)
    clear_pause()      # прошли без ошибок — снимаем паузу, если она была
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
        # Три предохранителя перед единственным походом в API.
        if not args.dry_run:
            left = paused_until()
            if left:
                log("Пауза после ошибки API: ещё %d мин, в сеть не идём." % (left / 60))
                return
            if in_quiet_hours():
                log("Ночь по Нячангу (%02d:00–%02d:00) — API не трогаем."
                    % (QUIET_FROM, QUIET_TO))
                return
            # разброс во времени: ровный такт по таймеру выглядит машинно
            time.sleep(random.randint(0, JITTER_MAX))
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
