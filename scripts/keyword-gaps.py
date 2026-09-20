#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ключевые слова: где мы почти выигрываем и что мешает.

Метод из схемы Sanskar Tiwari (19.09.2026) требует брать long-tail с низкой
конкуренцией и ставить точную фразу запроса в title и H1. Сложность запроса
он предлагает оценивать через KD в Ahrefs — у нас Ahrefs нет, и он не нужен:
Вебмастер отдаёт не оценку, а факт. Если по запросу нас УЖЕ показывают на
4-10 позиции, конкуренция по нему заведомо проходимая, гадать не о чем.

Скрипт тянет все запросы за период (их около 1100), считает CTR, сверяет
ожидаемый CTR для позиции с фактическим и раскладывает запросы по трём
корзинам:

  ДОЖАТЬ    - позиция 1-10, показы есть, но кликов меньше нормы для этой
              позиции. Сниппет не отвечает запросу. Лечится title и
              description, без нового контента. Самая дешёвая работа.
  ПОДТЯНУТЬ - позиция 11-30. Страница по теме есть, но не в топе.
              Лечится усилением существующей страницы.
  НЕТ СТРАНИЦЫ - показы есть, позиция ниже 30. Тема не раскрыта.

Для каждого запроса ищет страницу, где фраза стоит в title или H1 -
видно, закрыт запрос конкретной страницей или размазан по сайту.

Запуск:
    python3 scripts/keyword-gaps.py              # 30 дней, все корзины
    python3 scripts/keyword-gaps.py --days 90
    python3 scripts/keyword-gaps.py --min-shows 30
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.webmaster.yandex.net/v4"

# Ожидаемый CTR по позиции в выдаче Яндекса, доли.
# Ориентир, а не закон: нужен только чтобы отделить «сниппет не работает»
# от «позиция такая, что кликов и не должно быть много».
CTR_NORM = {
    1: 0.26, 2: 0.15, 3: 0.10, 4: 0.075, 5: 0.055,
    6: 0.042, 7: 0.035, 8: 0.028, 9: 0.024, 10: 0.020,
}


def token():
    path = os.path.join(ROOT, ".env")
    for line in open(path, encoding="utf-8"):
        if line.startswith("YANDEX_WEBMASTER_TOKEN="):
            return line.split("=", 1)[1].strip()
    sys.exit("Нет YANDEX_WEBMASTER_TOKEN в .env")


def call(path, tok, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Authorization": "OAuth " + tok})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        sys.exit("API Вебмастера: " + e.read().decode()[:300])


def fetch_queries(uid, hid, tok, days):
    """Забирает все запросы постранично: API отдаёт максимум 500 за раз."""
    date_to = date.today()
    date_from = date_to - timedelta(days=days)
    out = []
    offset = 0
    while True:
        params = [
            ("order_by", "TOTAL_SHOWS"),
            ("limit", 500),
            ("offset", offset),
            ("date_from", date_from.isoformat()),
            ("date_to", date_to.isoformat()),
            ("device_type_indicator", "ALL"),
        ]
        for ind in ("TOTAL_SHOWS", "TOTAL_CLICKS", "AVG_SHOW_POSITION"):
            params.append(("query_indicator", ind))
        data = call("/user/%s/hosts/%s/search-queries/popular" % (uid, hid), tok, params)
        batch = data.get("queries", [])
        out.extend(batch)
        if len(batch) < 500:
            break
        offset += 500
        if offset > 5000:
            break
    return out


def site_index():
    """Карта «страница -> title + h1 + description» по sitemap."""
    sm = os.path.join(ROOT, "sitemap.xml")
    pages = {}
    for loc in re.findall(r"<loc>([^<]+)</loc>", open(sm, encoding="utf-8").read()):
        rel = loc.replace("https://bahramovai.com", "")
        fname = rel.lstrip("/") or "index.html"
        if fname.endswith("/"):
            fname += "index.html"
        full = os.path.join(ROOT, fname)
        if not os.path.exists(full):
            continue
        html = open(full, encoding="utf-8").read()
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        desc = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
        clean = lambda m: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip().lower() if m else ""
        pages[rel] = {
            "title": clean(title),
            "h1": clean(h1),
            "desc": clean(desc),
        }
    return pages


def norm(s):
    return re.sub(r"[^a-zа-яё0-9 ]", " ", s.lower()).split()


def match_page(query, pages):
    """Какая страница закрывает запрос: по доле слов запроса в title и H1."""
    words = [w for w in norm(query) if len(w) > 2]
    if not words:
        return None, 0.0
    best, best_score = None, 0.0
    for rel, meta in pages.items():
        hay = meta["title"] + " " + meta["h1"]
        hit = sum(1 for w in words if w in hay)
        score = hit / float(len(words))
        # точное вхождение фразы в title весит больше россыпи слов
        if query.lower() in meta["title"]:
            score += 0.5
        if score > best_score:
            best, best_score = rel, score
    return best, best_score


def main():
    days = 30
    min_shows = 20
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    if "--min-shows" in sys.argv:
        min_shows = int(sys.argv[sys.argv.index("--min-shows") + 1])

    tok = token()
    uid = call("/user", tok)["user_id"]
    hid = call("/user/%s/hosts" % uid, tok)["hosts"][0]["host_id"]

    raw = fetch_queries(uid, hid, tok, days)
    pages = site_index()

    squeeze, pull, missing = [], [], []
    for q in raw:
        ind = q.get("indicators", {})
        shows = ind.get("TOTAL_SHOWS") or 0
        clicks = ind.get("TOTAL_CLICKS") or 0
        pos = ind.get("AVG_SHOW_POSITION") or 0
        if shows < min_shows:
            continue
        ctr = clicks / shows if shows else 0
        text = q["query_text"]
        page, score = match_page(text, pages)
        row = {
            "q": text, "shows": shows, "clicks": clicks,
            "pos": pos, "ctr": ctr, "page": page, "score": score,
        }
        if pos and pos <= 10:
            expect = CTR_NORM.get(int(round(pos)), 0.02)
            row["expect"] = expect
            row["lost"] = max(0.0, (expect - ctr) * shows)
            if ctr < expect * 0.7:
                squeeze.append(row)
        elif pos and pos <= 30:
            pull.append(row)
        elif pos:
            missing.append(row)

    squeeze.sort(key=lambda r: -r["lost"])
    pull.sort(key=lambda r: -r["shows"])
    missing.sort(key=lambda r: -r["shows"])

    print("Запросов за %d дней: %d, с показами от %d: %d"
          % (days, len(raw), min_shows, len(squeeze) + len(pull) + len(missing)))

    print("\n" + "=" * 100)
    print("ДОЖАТЬ — позиция в топ-10, но кликают меньше нормы. Правится title и description")
    print("=" * 100)
    print("%-48s %6s %6s %5s %7s %7s  %s" % ("запрос", "показы", "клики", "поз", "CTR", "норма", "теряем"))
    for r in squeeze[:25]:
        print("%-48s %6.0f %6.0f %5.1f %6.1f%% %6.1f%%  ~%.0f кликов"
              % (r["q"][:48], r["shows"], r["clicks"], r["pos"],
                 r["ctr"] * 100, r["expect"] * 100, r["lost"]))
        flag = "точное вхождение в title" if r["score"] >= 1.0 else "запрос НЕ стоит в title дословно"
        print("      -> %s  [%s]" % (r["page"], flag))

    print("\n" + "=" * 100)
    print("ПОДТЯНУТЬ — позиция 11-30. Страница есть, до топа не хватает")
    print("=" * 100)
    for r in pull[:20]:
        print("%-48s %6.0f показов  поз %.1f  -> %s"
              % (r["q"][:48], r["shows"], r["pos"], r["page"]))

    print("\n" + "=" * 100)
    print("НЕТ СТРАНИЦЫ — спрос есть, позиция ниже 30")
    print("=" * 100)
    for r in missing[:20]:
        print("%-48s %6.0f показов  поз %.1f" % (r["q"][:48], r["shows"], r["pos"]))

    total_lost = sum(r["lost"] for r in squeeze)
    print("\n" + "-" * 100)
    print("Недобор кликов по корзине ДОЖАТЬ: ~%.0f в месяц" % total_lost)


if __name__ == "__main__":
    main()
