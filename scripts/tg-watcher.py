#!/usr/bin/env python3
"""Ловит нажатия кнопок в Telegram и запускает агентов Claude Code.

Третье звено конвейера. Владельцу пришёл дайджест с кнопками — этот скрипт
ждёт нажатие и по нему:

    [номер новости]  → smm-copywriter пишет пост, scriptwriter — сценарий рилса,
                       оба черновика уходят владельцу
    [Опубликовать]   → пост уходит в канал @artsiombahram
    [Переписать]     → копирайтер делает другой заход
    [Отмена]         → ничего не происходит

    python3 scripts/tg-watcher.py           # висеть и слушать (Ctrl+C — выход)
    python3 scripts/tg-watcher.py --once    # разобрать накопившееся и выйти
    python3 scripts/tg-watcher.py --reset   # забыть старые события в очереди

Ничего не публикует без явного нажатия владельца. Чужие сообщения игнорирует:
работает только с TELEGRAM_CHAT_ID из .env.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tg_api  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NEWS = ROOT / ".news"
STATE = NEWS / ".watcher-state.json"
LOCK = NEWS / ".watcher.lock"
AGENT_TIMEOUT = 900  # 15 минут на один прогон агента

CLAUDE_TOOLS = "Read Write WebSearch WebFetch"


# ------------------------------------------------------------------ состояние

def read_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"offset": 0}


def write_state(state):
    NEWS.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                     encoding="utf-8")


def acquire_lock():
    """Два watcher-а одновременно ломают getUpdates — Telegram отдаёт 409."""
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip())
            os.kill(pid, 0)
        except (ValueError, ProcessLookupError, PermissionError):
            pass  # процесс умер, замок протух
        else:
            sys.exit(f"Watcher уже запущен (pid {pid}). "
                     f"Если это не так — удали {LOCK.relative_to(ROOT)}")
    NEWS.mkdir(exist_ok=True)
    LOCK.write_text(str(os.getpid()))


def release_lock():
    if LOCK.exists():
        LOCK.unlink()


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------------- агенты

def run_agent(agent, prompt):
    """Headless-прогон Claude Code. Возвращает (успех, текст ошибки)."""
    # Промпт идёт через stdin: --allowedTools принимает список значений и
    # съедает позиционный аргумент, если писать промпт после него.
    cmd = [
        "claude", "-p",
        "--agent", agent,
        "--permission-mode", "acceptEdits",
        "--allowedTools", CLAUDE_TOOLS,
    ]
    log(f"агент {agent} — старт")
    try:
        res = subprocess.run(cmd, cwd=str(ROOT), input=prompt,
                             capture_output=True, text=True,
                             timeout=AGENT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return False, f"агент {agent} не уложился в {AGENT_TIMEOUT // 60} мин"
    except FileNotFoundError:
        return False, "CLI claude не найден в PATH"
    out = ((res.stdout or "") + (res.stderr or "")).strip()
    # CLI отдаёт код 0 даже когда не смог залогиниться — ловим по тексту.
    if "Failed to authenticate" in out or "OAuth session expired" in out:
        return False, ("CLI claude не авторизован. Открой Терминал, выполни "
                       "`claude` и войди в аккаунт — headless-запуск берёт "
                       "тот же логин.")
    if res.returncode != 0:
        return False, f"агент {agent} упал: {out[-400:]}"
    log(f"агент {agent} — готово")
    return True, ""


def pick_meta(date, n):
    """Достаёт новость №n из дайджеста — для заголовков сообщений."""
    path = NEWS / f"digest-{date}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    for p in data.get("picks", []):
        if int(p.get("n", 0)) == int(n):
            return p
    return None


def post_path(date, n):
    return NEWS / f"post-{date}-{n}.txt"


def reels_path(date, n):
    return NEWS / f"reels-{date}-{n}.txt"


# ------------------------------------------------------------------ сценарии

def make_drafts(chat, date, n, redo=False):
    """Запускает копирайтера и сценариста, присылает оба черновика владельцу."""
    meta = pick_meta(date, n)
    if not meta:
        tg_api.send(chat, f"Не нашёл новость №{n} в дайджесте за {date}. "
                          f"Возможно, дайджест перезаписан.")
        return

    title = meta.get("title", "")
    tg_api.send(chat, ("Переписываю пост" if redo else f"Взял новость №{n}")
                + f": {title}\n\nСобираю — это пара минут.")

    extra = ("\n\nПредыдущий вариант владельцу не подошёл. Зайди с другого угла: "
             "другой крючок, другая структура, другой акцент. Не переставляй "
             "слова в старом тексте.") if redo else ""

    ok, err = run_agent("smm-copywriter", (
        f"Возьми новость №{n} из файла .news/digest-{date}.json "
        f"(поля title, source, link, angle, why_now). "
        f"Напиши по ней пост для канала по правилам своей роли. "
        f"Запиши готовый пост в файл .news/post-{date}-{n}.txt — "
        f"только текст поста, без заголовков и комментариев. "
        f"В канал ничего не отправляй.{extra}"
    ))
    if not ok:
        tg_api.send(chat, f"Пост не собрался.\n{err}")
        return

    path = post_path(date, n)
    if not path.exists():
        tg_api.send(chat, "Агент отработал, но файл поста не появился. "
                          "Загляни в терминал watcher-а.")
        return

    text = path.read_text(encoding="utf-8").strip()
    tg_api.send(
        chat,
        f"ПОСТ В КАНАЛ (новость №{n})\n\n{text}",
        buttons=tg_api.keyboard([[
            ("Опубликовать", f"pub:{date}:{n}"),
            ("Переписать", f"redo:{date}:{n}"),
            ("Отмена", f"drop:{date}:{n}"),
        ]]),
    )

    if redo:
        return  # сценарий рилса переписывать не просили

    ok, err = run_agent("scriptwriter", (
        f"Возьми новость №{n} из файла .news/digest-{date}.json "
        f"(поля title, link, angle, why_now). Напиши по ней сценарий "
        f"вертикального видео на 20–45 секунд по правилам своей роли. "
        f"Особое внимание хуку в первые 3 секунды — новость свежая, "
        f"на ней можно поймать внимание. "
        f"Запиши сценарий в файл .news/reels-{date}-{n}.txt. "
        f"Никуда его не отправляй — доставку сделает скрипт."
    ))
    if not ok:
        tg_api.send(chat, f"Сценарий рилса не собрался.\n{err}")
        return

    rpath = reels_path(date, n)
    if rpath.exists():
        tg_api.send(chat, "СЦЕНАРИЙ РИЛСА (новость №"
                    + str(n) + ")\n\n"
                    + rpath.read_text(encoding="utf-8").strip())


def publish(chat, date, n, callback_msg):
    path = post_path(date, n)
    if not path.exists():
        tg_api.send(chat, f"Файл поста {path.name} пропал — публиковать нечего.")
        return
    text = path.read_text(encoding="utf-8").strip()
    try:
        url = tg_api.post_to_channel(text)
    except RuntimeError as e:
        tg_api.send(chat, f"Telegram не принял пост: {e}")
        return
    if callback_msg:
        tg_api.drop_buttons(chat, callback_msg)
    tg_api.send(chat, f"Опубликовано в канале:\n{url}", preview=True)
    log(f"опубликовано {url}")


# ------------------------------------------------------------------ разбор

def handle_callback(cb, owner):
    chat = str(cb["message"]["chat"]["id"])
    if chat != owner:
        tg_api.answer(cb["id"], "Не для тебя.")
        return
    data = cb.get("data", "")
    msg_id = cb["message"]["message_id"]
    parts = data.split(":")
    if len(parts) != 3:
        tg_api.answer(cb["id"])
        return
    action, date, n = parts

    if action == "pick":
        tg_api.answer(cb["id"], "Взял в работу")
        tg_api.drop_buttons(chat, msg_id)  # чтобы не запустить дважды
        make_drafts(chat, date, n)
    elif action == "redo":
        tg_api.answer(cb["id"], "Переписываю")
        tg_api.drop_buttons(chat, msg_id)
        make_drafts(chat, date, n, redo=True)
    elif action == "pub":
        tg_api.answer(cb["id"], "Публикую")
        publish(chat, date, n, msg_id)
    elif action == "drop":
        tg_api.answer(cb["id"], "Отменил")
        tg_api.drop_buttons(chat, msg_id)
        tg_api.send(chat, "Ок, этот пост никуда не пошёл.")
    elif action == "skip":
        tg_api.answer(cb["id"], "Пропускаем")
        tg_api.drop_buttons(chat, msg_id)
        tg_api.send(chat, "Ок, сегодня без новостного поста.")
    else:
        tg_api.answer(cb["id"])


def handle_message(msg, owner):
    """Поддержка ответа цифрой — если жать кнопки неудобно."""
    chat = str(msg["chat"]["id"])
    if chat != owner:
        return
    text = (msg.get("text") or "").strip()
    if not text.isdigit():
        return
    date = datetime.now().strftime("%Y-%m-%d")
    if not (NEWS / f"digest-{date}.json").exists():
        tg_api.send(chat, "Дайджеста за сегодня ещё нет.")
        return
    make_drafts(chat, date, text)


def process(updates, owner, state):
    for upd in updates:
        state["offset"] = upd["update_id"] + 1
        write_state(state)
        try:
            if "callback_query" in upd:
                handle_callback(upd["callback_query"], owner)
            elif "message" in upd:
                handle_message(upd["message"], owner)
        except RuntimeError as e:
            log(f"ошибка обработки: {e}")


def selftest():
    """Проверяет всё, что нужно конвейеру, ничего никуда не отправляя."""
    ok = True

    def line(good, label, detail=""):
        print(f"  {'✅' if good else '❌'} {label}" + (f" — {detail}" if detail else ""))
        return good

    print("Проверка новостного конвейера:")

    try:
        me = tg_api.call("getMe")
        line(True, "бот отвечает", "@" + me["username"])
    except (RuntimeError, OSError) as e:
        ok = line(False, "бот не отвечает", str(e)) and ok

    try:
        chat = tg_api.owner_chat()
        line(True, "TELEGRAM_CHAT_ID на месте", chat)
    except SystemExit as e:
        ok = line(False, "нет TELEGRAM_CHAT_ID", str(e)) and ok

    try:
        member = tg_api.call("getChatMember", chat_id=tg_api.CHANNEL_ID,
                             user_id=tg_api.call("getMe")["id"])
        can = member.get("can_post_messages") or member.get("status") == "creator"
        ok = line(bool(can), "бот может писать в канал",
                  member.get("status", "")) and ok
    except (RuntimeError, OSError) as e:
        ok = line(False, "канал недоступен", str(e)) and ok

    agents = ROOT / ".claude" / "agents"
    for name in ("news-editor", "smm-copywriter", "scriptwriter"):
        ok = line((agents / f"{name}.md").exists(), f"агент {name}") and ok

    good, err = run_agent("news-editor", "Ответь одним словом: готов")
    ok = line(good, "headless-запуск Claude Code", err) and ok

    print("\nВсё готово." if ok else "\nЕсть незакрытые пункты — см. выше.")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Слушает кнопки в Telegram")
    ap.add_argument("--once", action="store_true",
                    help="разобрать накопившееся и выйти")
    ap.add_argument("--reset", action="store_true",
                    help="пропустить всё, что накопилось в очереди")
    ap.add_argument("--selftest", action="store_true",
                    help="проверить бота, канал, агентов и авторизацию CLI")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    owner = tg_api.owner_chat()
    state = read_state()

    if args.reset:
        pending = tg_api.get_updates(state.get("offset", 0), wait=0)
        if pending:
            state["offset"] = pending[-1]["update_id"] + 1
            write_state(state)
        print(f"Очередь очищена ({len(pending)} событий пропущено).")
        return 0

    acquire_lock()
    try:
        log("watcher слушает. Ctrl+C — выход.")
        while True:
            try:
                updates = tg_api.get_updates(state.get("offset", 0),
                                             wait=0 if args.once else 25)
            except (RuntimeError, OSError) as e:
                log(f"сеть молчит ({e}) — жду 15 с")
                time.sleep(15)
                continue
            if updates:
                log(f"событий: {len(updates)}")
                process(updates, owner, state)
            if args.once:
                log("режим --once, выхожу.")
                return 0
    except KeyboardInterrupt:
        log("остановлен вручную.")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
