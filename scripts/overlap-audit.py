#!/usr/bin/env python3
"""Поиск дублирования тем между статьями блога (каннибализация выдачи).

Две проверки:
  1. Тематическое пересечение — насколько статьи про одно и то же
     (по title, H1, H2 и meta description).
  2. Дословные повторы — одинаковые куски текста, скопированные между статьями.

Запуск:
    python3 scripts/overlap-audit.py           # сводка
    python3 scripts/overlap-audit.py --full    # + все совпавшие фрагменты
"""
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
SKIP = {"index.html"}

# Порог тематической близости, выше которого стоит присмотреться
TOPIC_WARN = 0.28
# Длина фразы (в словах) для поиска дословных повторов
SHINGLE = 9

STOP = set("""
и в во не что он на я с со как а то все она так его но да ты к у же вы за бы
по только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг
ли если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя
ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без
будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой
совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем всех
никогда можно при наконец два об другой хоть после над больше тот через эти нас
про всего них какая много разве три эту моя впрочем хорошо свою этой перед иногда
лучше чуть том нельзя такой им более всегда конечно всю между это как для при
это эта эти этих также еще ещё который которые которая которых свои своих your
""".split())


def norm_words(text):
    words = re.findall(r"[а-яёa-z0-9]+", text.lower())
    return [w for w in words if len(w) > 2 and w not in STOP]


def strip_chrome(html):
    """Вырезает служебные зоны: они одинаковы во всех статьях по замыслу."""
    patterns = [
        r"<(script|style)\b.*?</\1>",
        r"<nav\b.*?</nav>",
        r"<footer\b.*?</footer>",
        r"<header\b.*?</header>",
        r'<section class="related-posts".*?</section>',
        r"<div data-hub-link.*?</div>",
        r'<div class="breadcrumb".*?</div>',
        r'<div class="cta-block".*?</div>',
    ]
    for p in patterns:
        html = re.sub(p, " ", html, flags=re.S)
    return html


def strip_tags(html):
    return re.sub(r"<[^>]+>", " ", strip_chrome(html))


def load():
    docs = {}
    for path in sorted(BLOG.glob("*.html")):
        if path.name in SKIP:
            continue
        raw = path.read_text(encoding="utf-8")
        title = re.search(r"<title>([^<]*)</title>", raw)
        desc = re.search(r'name="description" content="([^"]*)"', raw)
        html = strip_chrome(raw)
        heads = re.findall(r"<h[123][^>]*>(.*?)</h[123]>", html, re.S)
        heads = [re.sub(r"<[^>]+>", "", h) for h in heads]
        topic_src = " ".join(
            filter(None, [title.group(1) if title else "", desc.group(1) if desc else ""] + heads)
        )
        body = " ".join(strip_tags(raw).split())
        docs[path.name] = {
            "title": title.group(1) if title else path.name,
            "topic": set(norm_words(topic_src)),
            "heads": [h.strip() for h in heads if h.strip()],
            "body_words": norm_words(body),
        }
    return docs


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def shingles(words, n=SHINGLE):
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def main():
    full = "--full" in sys.argv
    docs = load()
    names = list(docs)
    print(f"Статей: {len(names)}\n")

    # --- 1. Тематическое пересечение ---
    pairs = []
    for a, b in combinations(names, 2):
        score = jaccard(docs[a]["topic"], docs[b]["topic"])
        if score >= TOPIC_WARN:
            common = docs[a]["topic"] & docs[b]["topic"]
            pairs.append((score, a, b, common))
    pairs.sort(reverse=True)

    print("=== ПАРЫ СТАТЕЙ ПРО ОДНО И ТО ЖЕ ===")
    if not pairs:
        print("  ✅ сильных пересечений нет")
    for score, a, b, common in pairs:
        print(f"\n  {score:.0%} общих тем")
        print(f"    A: {a}")
        print(f"    B: {b}")
        top = sorted(common, key=len, reverse=True)[:12]
        print(f"    общее: {', '.join(top)}")

    # --- 2. Дословные повторы ---
    print(f"\n\n=== ДОСЛОВНЫЕ ПОВТОРЫ (фразы от {SHINGLE} слов) ===")
    shs = {n: shingles(docs[n]["body_words"]) for n in names}
    dupes = []
    for a, b in combinations(names, 2):
        common = shs[a] & shs[b]
        if common:
            dupes.append((len(common), a, b, common))
    dupes.sort(reverse=True)

    if not dupes:
        print("  ✅ дословных повторов нет")
    for count, a, b, common in dupes[:12]:
        print(f"\n  {count} совпавших фраз")
        print(f"    A: {a}")
        print(f"    B: {b}")
        shown = sorted(common, key=len, reverse=True)[: (None if full else 2)]
        for frag in shown:
            print(f"      «{frag}»")

    # --- 3. Повторяющиеся заголовки ---
    print(f"\n\n=== ОДИНАКОВЫЕ ЗАГОЛОВКИ В РАЗНЫХ СТАТЬЯХ ===")
    by_head = defaultdict(list)
    for n in names:
        for h in docs[n]["heads"]:
            key = " ".join(norm_words(h))
            if len(key.split()) >= 3:
                by_head[key].append(n)
    repeated = {k: v for k, v in by_head.items() if len(set(v)) > 1}
    if not repeated:
        print("  ✅ повторяющихся заголовков нет")
    for key, files in sorted(repeated.items(), key=lambda x: -len(x[1]))[:15]:
        print(f"  «{key}» — в {len(set(files))} статьях: {', '.join(sorted(set(files))[:4])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
