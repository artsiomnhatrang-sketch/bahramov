#!/usr/bin/env python3
"""Собирает список тёплых контактов из экспорта Telegram владельца.

Зачем: у Артёма в истории переписок лежат сотни людей, которые уже платили
или интересовались услугами и пропали. Это самый быстрый источник заявок -
быстрее, чем SEO и посты. Скрипт НИЧЕГО не отправляет: он только строит
список, по которому Артём пишет людям сам, руками.

Запуск (по прямому разрешению владельца от 05.09.2026):
    python3 scripts/warm-contacts.py "путь/к/result.json"

Результат: .tone/warm-contacts.md (в git не уходит, там персональные данные).
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ME = "user822151079"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tone" / "warm-contacts.md"

# о чём был разговор
TOPICS = {
    "разблокировка": r"разблок|заблокир|бан\b|апелляц|ограничен|восстанов",
    "взлом": r"взлом|угнал|украл|фишинг|мошенн",
    "продвижение": r"продвижен|охват|подписчик|скайнет|буст|трафик",
    "чат-бот": r"чат-?бот|чатплейс|chatplace|воронк|автопривет",
    "нейросети": r"нейросет|ии-агент|ai-?агент|chatgpt|аватар",
    "чистка": r"чистк|масфоллов|ботов|балласт|неактивн",
}
MONEY = r"оплат|перевёл|перевел|скинул деньги|чек|реквизит|предоплат|счёт на|счет на"
PRICE = r"\d[\d\s]{2,}\s*(?:₽|руб|тыс)|сколько стоит|стоимост|цена|прайс"


def messages(path):
    """Потоково отдаёт (чат, дата, моё ли сообщение, текст) из экспорта."""
    chat = None
    ctype = None
    date = None
    frm = None
    buf = None
    skip_entities = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if skip_entities:
                if s in ("],", "]"):
                    skip_entities = 0
                continue
            if s.startswith('"text_entities":'):
                rest = s.split(":", 1)[1].strip()
                if rest.startswith("[") and not rest.rstrip().endswith(("]", "],")):
                    skip_entities = 1
                continue
            if buf is not None:
                buf.append(line)
                if s in ("],", "]"):
                    try:
                        arr = json.loads("".join(buf).split(":", 1)[1].rstrip().rstrip(","))
                        t = "".join(p if isinstance(p, str) else p.get("text", "") for p in arr)
                    except Exception:
                        t = ""
                    if t.strip():
                        yield chat, ctype, date, frm == ME, t
                    buf = None
                continue
            if s.startswith('"name":'):
                try:
                    chat = json.loads(s.split(":", 1)[1].rstrip().rstrip(","))
                except Exception:
                    chat = None
                ctype = None
            elif s.startswith('"type":') and ctype is None:
                ctype = s.split('"')[3] if s.count('"') >= 4 else None
            elif s.startswith('"date":'):
                date = s.split('"')[3] if s.count('"') >= 4 else None
            elif s.startswith('"from_id":'):
                try:
                    frm = json.loads(s.split(":", 1)[1].rstrip().rstrip(","))
                except Exception:
                    frm = None
            elif s.startswith('"text":'):
                rest = s.split(":", 1)[1].strip()
                if rest.startswith("["):
                    buf = [line]
                    if rest.rstrip().endswith("],") or rest.rstrip().endswith("]"):
                        try:
                            arr = json.loads(rest.rstrip().rstrip(","))
                            t = "".join(p if isinstance(p, str) else p.get("text", "") for p in arr)
                        except Exception:
                            t = ""
                        if t.strip():
                            yield chat, ctype, date, frm == ME, t
                        buf = None
                else:
                    try:
                        t = json.loads(rest.rstrip().rstrip(","))
                    except Exception:
                        t = None
                    if isinstance(t, str) and t.strip():
                        yield chat, ctype, date, frm == ME, t


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if not src or not Path(src).exists():
        sys.exit("Укажите путь к result.json")

    agg = defaultdict(lambda: {
        "n": 0, "mine": 0, "first": None, "last": None,
        "topics": set(), "money": False, "price": False,
        "tail": [], "personal": False,
    })

    for chat, ctype, date, mine, text in messages(src):
        if not chat:
            continue
        c = agg[chat]
        if ctype == "personal_chat":
            c["personal"] = True
        c["n"] += 1
        c["mine"] += 1 if mine else 0
        if c["first"] is None:
            c["first"] = date
        c["last"] = date
        low = text.lower()
        for name, pat in TOPICS.items():
            if re.search(pat, low):
                c["topics"].add(name)
        if re.search(MONEY, low):
            c["money"] = True
        if re.search(PRICE, low):
            c["price"] = True
        c["tail"].append(("я" if mine else "он", text[:160]))
        if len(c["tail"]) > 4:
            c["tail"].pop(0)

    today = datetime.now()

    def days_since(d):
        try:
            return (today - datetime.fromisoformat(d)).days
        except Exception:
            return 9999

    rows = []
    for name, c in agg.items():
        if not c["personal"] or c["n"] < 4 or not c["topics"]:
            continue
        # диалог, а не монолог: человек тоже писал
        if c["mine"] == c["n"]:
            continue
        rows.append((name, c, days_since(c["last"])))

    paid = sorted([r for r in rows if r[1]["money"]], key=lambda r: r[2])
    warm = sorted([r for r in rows if not r[1]["money"] and r[1]["price"]], key=lambda r: r[2])
    talked = sorted([r for r in rows if not r[1]["money"] and not r[1]["price"]], key=lambda r: r[2])

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as o:
        o.write("# Тёплые контакты из истории Telegram\n\n")
        o.write("Собрано %s. Никому ничего не отправлялось - это список для ручной работы.\n\n"
                % today.strftime("%d.%m.%Y"))
        o.write("| группа | сколько |\n|---|---|\n")
        o.write("| платили раньше | %d |\n| спрашивали цену, не купили | %d |\n"
                "| обсуждали услуги | %d |\n\n" % (len(paid), len(warm), len(talked)))

        for title, group, hint in [
            ("Платили раньше - начинать с них", paid,
             "Знают тебя и уже отдавали деньги. Самая короткая дорога к оплате."),
            ("Спрашивали цену и пропали", warm,
             "Интерес был, сделки не случилось. Повод вернуться - новая услуга или ситуация в их нише."),
            ("Обсуждали услуги без цены", talked,
             "Разговор был, до денег не дошёл."),
        ]:
            o.write("\n## %s\n\n_%s_\n\n" % (title, hint))
            for name, c, dd in group[:120]:
                o.write("### %s\n" % name)
                o.write("- последний разговор: %s (%d дн. назад), сообщений: %d\n"
                        % ((c["last"] or "?")[:10], dd, c["n"]))
                o.write("- о чём: %s\n" % ", ".join(sorted(c["topics"])))
                o.write("- хвост переписки:\n")
                for who, txt in c["tail"]:
                    o.write("  - **%s:** %s\n" % (who, txt.replace("\n", " ")))
                o.write("\n")

    print("Личных чатов с темой услуг: %d" % len(rows))
    print("  платили раньше:            %d" % len(paid))
    print("  спрашивали цену, не купили: %d" % len(warm))
    print("  просто обсуждали услуги:    %d" % len(talked))
    print("\nСписок: %s" % OUT)


if __name__ == "__main__":
    main()
