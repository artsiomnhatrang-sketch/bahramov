#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Не дать двум аккаунтам Threads писать одинаково.

С 30.09.2026 @bahram.av и @bahramovartem работают на одной теме
(разблокировка и восстановление аккаунтов). Чтобы Meta не склеила их
в сеть, у ответов не должно быть общих людей, общих веток и похожих текстов.
Правило держит этот скрипт, а не память ассистента.

  python3 scripts/threads-uniq.py sync
      забрать по API все ответы обоих аккаунтов в реестр threads/sent-texts.jsonl
      (запускать в начале и в конце подхода). Адресат (user, post, root) API
      отдаёт только для ответов внутри НАШИХ постов; в чужих ветках поля пустые,
      их заполняет record с тем же текстом (sync склеивает). Безадресные ответы
      за 3 дня sync печатает - дописать record, иначе check их не видит (04.10)

  python3 scripts/threads-uniq.py check --account main|ai --user NICK [--post ID] [--root НИК|ID] "текст"
      перед каждым ответом в новой ветке. Выход 1 = не отправлять
      --root      автор или ID корня ветки, если пишем вложенным ответом:
                  корень уже у другого аккаунта = СТОП (04.10, anastasia.tlk.arts)
      --followup  человек ответил нам сам: свой журнал по нику не проверяем
      --asked     человек сам спросил, как связаться: можно ответить «пишите в директ».
                  Без флага призыв в директ, личку, «напишите мне», «помогу» = СТОП
                  (07.10.2026: после бана @bahram.av ответы только рекомендации)

  python3 scripts/threads-uniq.py record --account main|ai --user NICK [--post ID] [--root НИК|ID] "текст"
      записать отправленный ответ сразу (sync потом подтянет его и по API)

  python3 scripts/threads-uniq.py stats
      сколько текстов в реестре и насколько похожи аккаунты между собой
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "threads", "sent-texts.jsonl")
LOGS = {
    "main": os.path.join(ROOT, "threads", "stalker-log.md"),
    "ai": os.path.join(ROOT, "threads", "ai", "stalker-log.md"),
}
OWN = {"bahram.av", "bahramovartem", "bahramartai"}
NAMES = {"main": "@bahram.av", "ai": "@bahramovartem"}

# пороги подобраны на ответах 07-29.09: разные ответы одного аккаунта
# дают сходство 0.02-0.12, переписанный под другого человека текст - от 0.30
SIM_OTHER = 0.22   # с текстами другого аккаунта - строже
SIM_OWN = 0.32     # со своими - чтобы не штамповать
TAIL_OTHER = 0.35  # последнее предложение (концовка) против другого аккаунта

# 07.10.2026: незнакомец приходит к человеку с баном и зовёт в директ - это
# схема мошенников «верну аккаунт», за неё @bahram.av и отключили. В ответах
# только рекомендации; в личку - если человек сам спросил (флаг --asked).
DM_CALL = re.compile(
    r"директ|direct|\bдм\b|\bdm\b|в\s+лич(ку|ке|ные|ных)|в\s+лс\b|"
    r"(напиш|пиш|скин|кин|пришл|отправ|черкн|покаж)\w*\s+(мне|сюда)|мне\s+в\s+(тг|телеграм)|"
    r"bahramov|t\.me/|обращайтесь|\bпомогу\b|могу\s+помочь|\bпомогаю\b|"
    r"разбер(у|ём|ем)(ся)?\s+(вам|ваш|под)|подскажу\s+(под|по\s+ваш)",
    re.I)


def norm(t):
    t = t.lower().replace("ё", "е")
    t = re.sub(r"[^a-zа-я0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def shingles(t, n=5):
    t = norm(t)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def sim(a, b):
    sa, sb = shingles(a), shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def tail(t):
    parts = [p for p in re.split(r"(?<=[.!?)])\s+|\s+-\s+(?=[А-ЯA-Z])", t.strip()) if p.strip()]
    return parts[-1] if parts else t


def head(t, words=3):
    return " ".join(norm(t).split()[:words])


def load_reg():
    out = []
    if os.path.exists(REG):
        for line in open(REG, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def save_reg(rows):
    with open(REG, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def nicks_in_log(acc):
    path = LOGS[acc]
    if not os.path.exists(path):
        return set()
    txt = open(path, encoding="utf-8").read()
    return {n.lower().rstrip(".") for n in re.findall(r"@([A-Za-z0-9._]{2,30})", txt)} - OWN


def posts_in_log(acc):
    path = LOGS[acc]
    if not os.path.exists(path):
        return set()
    return set(re.findall(r"/post/([A-Za-z0-9_-]{8,14})", open(path, encoding="utf-8").read())) | \
        set(re.findall(r"`([A-Za-z0-9_-]{11})`", open(path, encoding="utf-8").read()))


def load_env():
    env = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


API = "https://graph.threads.net/v1.0/"


def fetch_replies(token):
    # replied_to и root_post Meta отдаёт только в ветках, где корень наш;
    # в чужих ветках их нет (проверено 05.10 на обоих аккаунтах)
    url = API + "me/replies?" + urllib.parse.urlencode({
        "fields": "id,text,timestamp,permalink,shortcode,replied_to,root_post",
        "limit": 100, "access_token": token})
    out, pages = [], 0
    while url and pages < 30:
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
        out.extend(d.get("data", []))
        url = (d.get("paging") or {}).get("next")
        pages += 1
        time.sleep(0.5)
    return out


def media_info(token, mid, cache):
    """ник автора и shortcode поста по его ID (кэш на один прогон)"""
    if mid not in cache:
        url = API + mid + "?" + urllib.parse.urlencode({"fields": "username,shortcode", "access_token": token})
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.loads(r.read().decode("utf-8"))
            cache[mid] = ((d.get("username") or "").lower(), d.get("shortcode") or mid)
        except Exception:
            cache[mid] = ("", mid)
        time.sleep(0.2)
    return cache[mid]


def fill_target(row, rep, token, cache):
    """заполнить user/post/root из replied_to и root_post. True - что-то дописали"""
    to, root = (rep.get("replied_to") or {}).get("id"), (rep.get("root_post") or {}).get("id")
    if not to or row.get("user"):
        return False
    row["user"], row["post"] = media_info(token, to, cache)
    if root:
        row["root"] = media_info(token, root, cache)[1]
    return True


def merge_records(rows):
    """ручной record без id + строка из API с тем же текстом = одна строка с адресатом.
    Случай sara.arsenkyzy: ответ 03.10 пришёл из API без ника, ник дописали record'ом
    отдельной строкой, и check по реестру его не видел"""
    blank = {}
    for r in rows:
        if r.get("id") and not r.get("user"):
            blank.setdefault((r["account"], norm(r["text"])), []).append(r)
    out, merged = [], 0
    for r in rows:
        k = (r["account"], norm(r["text"]))
        if not r.get("id") and r.get("user") and blank.get(k):
            t = blank[k].pop(0)
            for f in ("user", "post", "root"):
                if r.get(f):
                    t[f] = r[f]
            merged += 1
            continue
        out.append(r)
    return out, merged


def cmd_sync():
    env = load_env()
    rows = load_reg()
    known = {r.get("id"): r for r in rows if r.get("id")}
    added = filled = 0
    for acc, key in (("main", "THREADS_ACCESS_TOKEN"), ("ai", "THREADS_AI_ACCESS_TOKEN")):
        tok = env.get(key)
        if not tok:
            print("нет %s - %s пропущен" % (key, NAMES[acc]))
            continue
        try:
            reps = fetch_replies(tok)
        except Exception as e:  # сеть или истёкший токен - не валим подход
            print("%s: API не ответил (%s)" % (NAMES[acc], e))
            continue
        cache = {}
        for r in reps:
            if not r.get("text"):
                continue
            if r.get("id") in known:
                filled += fill_target(known[r["id"]], r, tok, cache)  # догон старых строк
                continue
            # запись, сделанная вручную через record, получает id при sync
            match = [x for x in rows if not x.get("id") and x["account"] == acc and norm(x["text"]) == norm(r["text"])]
            if match:
                match[0]["id"] = r["id"]
                known[r["id"]] = match[0]
                fill_target(match[0], r, tok, cache)
                continue
            row = {"id": r["id"], "account": acc, "ts": r.get("timestamp", ""),
                   "text": r["text"], "user": "", "post": ""}
            fill_target(row, r, tok, cache)
            rows.append(row)
            known[r["id"]] = row
            added += 1
        print("%s: ответов по API %d" % (NAMES[acc], len(reps)))
    rows, merged = merge_records(rows)
    save_reg(rows)
    print("реестр: %d текстов, новых %d, адресат из API %d, склеено с record %d" % (len(rows), added, filled, merged))
    # чужие ветки API не раскрывает - свежие безадресные ответы показать, чтобы дописать record
    since = time.strftime("%Y-%m-%d", time.localtime(time.time() - 3 * 86400))
    lost = [r for r in rows if r.get("id") and not r.get("user") and r.get("ts", "")[:10] >= since]
    if lost:
        print("без адресата за 3 дня: %d - check их не видит, дописать record --user с тем же текстом:" % len(lost))
        for r in lost[-15:]:
            print("  %s %s: %s" % (NAMES[r["account"]], r["ts"][:16], r["text"][:70]))


def arg(name, default=""):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            v = sys.argv[i + 1]
            del sys.argv[i:i + 2]
            return v
    return default


def cmd_check(record=False):
    acc = arg("--account", "main")
    if acc not in NAMES:
        sys.exit("--account: main или ai")
    user = arg("--user").lstrip("@").lower()
    post = arg("--post")
    root = arg("--root").lstrip("@")
    followup = "--followup" in sys.argv
    asked = "--asked" in sys.argv
    rest = [a for a in sys.argv[2:] if a not in ("--followup", "--asked")]
    text = " ".join(rest).strip() or sys.stdin.read().strip()
    if not text:
        sys.exit("нет текста")
    other = "ai" if acc == "main" else "main"
    rows = load_reg()

    if record:
        rows.append({"id": "", "account": acc, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "text": text, "user": user, "post": post, "root": root})
        save_reg(rows)
        print("записано в реестр")
        return

    stop = []
    m = DM_CALL.search(text)
    if m and not asked:
        stop.append("призыв в директ или предложение помощи (%r) - с 07.10 только рекомендации, "
                    "в личку зовём, только если человек сам спросил (--asked)" % m.group())
    if user:
        if user in nicks_in_log(other) or any(r.get("user") == user for r in rows if r["account"] == other):
            stop.append("@%s уже есть у %s - второй аккаунт к этому человеку не идёт" % (user, NAMES[other]))
        if not followup and (user in nicks_in_log(acc) or any(r.get("user") == user for r in rows if r["account"] == acc)):
            stop.append("@%s уже есть в журнале %s - одному человеку дважды не пишем" % (user, NAMES[acc]))
    if post and (post in posts_in_log(other) or any(r.get("post") == post for r in rows if r["account"] == other)):
        stop.append("ветка %s уже у %s - два аккаунта в одной ветке нельзя" % (post, NAMES[other]))
    theirs = [r for r in rows if r["account"] == other]
    if post and any(r.get("root") == post for r in theirs):
        stop.append("в ветке %s уже есть вложенный ответ %s" % (post, NAMES[other]))
    if root:
        # корень можно дать ником автора или ID поста - сверяем обоими способами
        rn = root.lower()
        if rn in nicks_in_log(other) or any(r.get("user") == rn for r in theirs) \
                or root in posts_in_log(other) or any(x in (r.get("post"), r.get("root")) for r in theirs for x in (root, rn)):
            stop.append("корень ветки %s уже у %s - вложенным ответом туда тоже нельзя" % (root, NAMES[other]))

    h = head(text)
    for r in rows:
        if len(norm(r["text"])) < 40:
            continue  # спасибо, удачи и смайлы - не материал для сравнения
        s = sim(text, r["text"])
        mine = r["account"] == acc
        if s >= (SIM_OWN if mine else SIM_OTHER):
            stop.append("похоже на ответ %s (%.2f): %s..." % (NAMES[r["account"]], s, r["text"][:70]))
        if not mine:
            st = sim(tail(text), tail(r["text"]))
            if st >= TAIL_OTHER and len(norm(tail(text))) > 15:
                stop.append("хвост совпадает с %s (%.2f): %s" % (NAMES[other], st, tail(r["text"])[:70]))
            if h and len(h.split()) == 3 and head(r["text"]) == h:
                stop.append("то же начало, что у %s: %s" % (NAMES[other], h))
    if stop:
        print("СТОП threads-uniq: текст или адресат пересекается, не отправлять")
        for s in stop[:8]:
            print("  - " + s)
        sys.exit(1)
    print("ok")


def cmd_stats():
    rows = load_reg()
    a = [r for r in rows if r["account"] == "main"]
    b = [r for r in rows if r["account"] == "ai"]
    print("@bahram.av: %d, @bahramovartem: %d" % (len(a), len(b)))
    worst = []
    for x in a[-200:]:
        for y in b[-200:]:
            worst.append((sim(x["text"], y["text"]), x["text"][:60], y["text"][:60]))
    worst.sort(reverse=True)
    for s, x, y in worst[:5]:
        print("%.2f | %s | %s" % (s, x, y))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    c = sys.argv[1]
    if c == "sync":
        cmd_sync()
    elif c == "check":
        cmd_check()
    elif c == "record":
        cmd_check(record=True)
    elif c == "stats":
        cmd_stats()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
