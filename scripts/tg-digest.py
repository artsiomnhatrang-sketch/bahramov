#!/usr/bin/env python3
"""Отправляет владельцу дайджест ИИ-новостей с кнопками выбора.

Второе звено конвейера: news-collect.py собрал → news-editor отобрал →
этот скрипт доставил в Telegram. Владелец жмёт номер, дальше работает
tg-watcher.py.

    python3 scripts/tg-digest.py             # отправить дайджест за сегодня
    python3 scripts/tg-digest.py --date 2026-08-17
    python3 scripts/tg-digest.py --dry-run   # показать текст, не отправляя

Читает .news/digest-<дата>.json и .txt — их пишет агент news-editor.
Ключи из .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tg_api  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NEWS = ROOT / ".news"
LOCK = NEWS / ".watcher.lock"


def watcher_alive():
    """Кнопки без watcher-а нажимаются в пустоту — предупреждаем заранее."""
    if not LOCK.exists():
        return False
    try:
        os.kill(int(LOCK.read_text().strip()), 0)
    except (ValueError, ProcessLookupError, PermissionError, OSError):
        return False
    return True


def load_digest(date):
    meta = NEWS / f"digest-{date}.json"
    text = NEWS / f"digest-{date}.txt"
    if not meta.exists():
        sys.exit(
            f"Нет {meta.relative_to(ROOT)}.\n"
            "Порядок такой:\n"
            "  1) python3 scripts/news-collect.py\n"
            "  2) claude -p --agent news-editor 'собери дайджест за сегодня'\n"
            "  3) python3 scripts/tg-digest.py"
        )
    data = json.loads(meta.read_text(encoding="utf-8"))
    body = text.read_text(encoding="utf-8").strip() if text.exists() else None
    return data, body


def fallback_text(data):
    """Если news-editor не оставил .txt — собираем текст из json сами."""
    lines = [f"Горячие ИИ-новости — {data['date']}", ""]
    for p in data["picks"]:
        lines.append(f"{p['n']}. {p['title']}")
        lines.append(f"   {p.get('source', '')} · {p.get('format', '')}")
        if p.get("angle"):
            lines.append(f"   Угол: {p['angle']}")
        if p.get("link"):
            lines.append(f"   {p['link']}")
        lines.append("")
    lines.append("Жми номер — соберу пост и сценарий рилса.")
    return "\n".join(lines)


def build_keyboard(date, picks):
    """Ряд с номерами новостей + отдельная кнопка «пропустить день»."""
    numbers = [(str(p["n"]), f"pick:{date}:{p['n']}") for p in picks]
    rows = [numbers[i:i + 5] for i in range(0, len(numbers), 5)]
    rows.append([("Пропустить сегодня", f"skip:{date}:0")])
    return tg_api.keyboard(rows)


def main():
    ap = argparse.ArgumentParser(description="Дайджест ИИ-новостей в Telegram")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true",
                    help="показать текст в терминале и не отправлять")
    args = ap.parse_args()

    data, body = load_digest(args.date)
    picks = data.get("picks", [])
    if not picks:
        print(f"В дайджесте за {args.date} нет ни одной новости — "
              f"{data.get('note', 'редактор ничего не отобрал')}")
        return 0

    text = body or fallback_text(data)

    if args.dry_run:
        print(text)
        print("\n[кнопки]", " ".join(str(p["n"]) for p in picks),
              "+ Пропустить сегодня")
        return 0

    alive = watcher_alive()
    if not alive:
        # Нажатие всё равно долетит и будет ждать в очереди Telegram,
        # но человек у телефона этого не видит — так и пишем в дайджесте.
        text += ("\n\n⚠️ Watcher сейчас не запущен: нажатие сохранится "
                 "в очереди и сработает, когда он поднимется.")

    tg_api.send(tg_api.owner_chat(), text,
                buttons=build_keyboard(args.date, picks))
    print(f"Дайджест за {args.date} отправлен: {len(picks)} новостей.")
    if alive:
        print("Watcher на связи — нажатие кнопки обработается сразу.")
    else:
        print("⚠️ Watcher НЕ запущен. Нажатия не пропадут, но и не сработают,")
        print("   пока не поднимешь его:  python3 scripts/tg-watcher.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
