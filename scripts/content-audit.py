#!/usr/bin/env python3
"""Аудит честности и актуальности контента блога bahramovai.com.

Ищет то, на чём статьи уже ловились: цифры без источника, обещания результата,
категоричные утверждения о механиках платформ, устаревшие факты.

Запуск:
    python3 scripts/content-audit.py --changed  # только новые и изменённые статьи (для preflight)
    python3 scripts/content-audit.py            # сводка по всем статьям
    python3 scripts/content-audit.py --full     # с цитатами каждого срабатывания
    python3 scripts/content-audit.py <файл>     # разбор одной статьи

ВАЖНО про цифры. В уже опубликованных статьях цифры взяты из практики владельца —
они реальные, их НЕ нужно вычищать. Проверка нужна для НОВЫХ текстов: там цифру
надо либо атрибутировать («по моим клиентам», «по опыту работы»), либо дать
источник — иначе гейт reviewer завернёт статью.

Часть срабатываний всегда ложные: статьи, которые сами развенчивают миф
(«никто не даст 100% гарантии») или предупреждают против обхода правил.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
SKIP = {"index.html"}

# Слова рядом с цифрой, которые означают честную атрибуцию
ATTRIBUTION = re.compile(
    r"по (моим|моей|нашим|опыту|практике|наблюдени)|из практики|"
    r"по опыту|наблюдени|примерно|порядка|ориентир|около|"
    r"источник|по данным (Meta|Instagram|Telegram|Роскомнадзор)|"
    # результат конкретного клиента — допустимая атрибуция по правилам проекта,
    # если рядом сказано, чья это оценка, и это не подано как обещание
    r"по словам клиента|клиент (оцен|назв|сообщ)|у клиента|со слов клиента",
    re.I,
)

CHECKS = [
    (
        "Цифры без источника",
        re.compile(r"\b\d{1,3}\s?%|\b[×x]\s?\d[.,]?\d*\b|\+\d{2,3}\s?%"),
        "процент или кратность — нужен источник либо атрибуция «по моим клиентам»",
    ),
    (
        "«По данным исследований»",
        re.compile(r"по данным исследовани|исследования показыва|учёные|статистика показыва", re.I),
        "ссылка на безымянные исследования — либо назвать источник, либо убрать",
    ),
    (
        "Обещание результата",
        re.compile(
            r"раз и навсегда|гарантиру|100\s?%|обязательно (получ|верн|сработ)|"
            r"результат[ы]? (видны|будут) уже|точно (верн|получ|сработ)|"
            r"в течение \d+ дн[еяй]+ (верн|разбан)",
            re.I,
        ),
        "обещание гарантированного результата — против правил честности",
    ),
    (
        "Категоричность о платформе",
        re.compile(
            r"никаких рисков|полностью безопасн|никогда не (забан|заблокиру)|"
            r"на 100% защит|исключает блокировк",
            re.I,
        ),
        "категоричное утверждение о поведении платформы",
    ),
    (
        "Советы по обходу",
        re.compile(
            r"антидетект|эмулятор|Parallel Space|Island|Shelter|"
            r"мобильн(ый|ые) прокси|обойти (детект|систему|проверку)|"
            r"накрут|серые схемы работают",
            re.I,
        ),
        "нормализация обхода защиты платформы — запрещено правилами проекта",
    ),
    (
        "Мифы про fingerprinting",
        re.compile(r"Apple ID|IMEI|MAC-адрес|серийн(ый|ого) номер", re.I),
        "проверить: Instagram не читает эти данные (позиция кластера от 10.08)",
    ),
    (
        "Возможно устаревшее",
        re.compile(
            r"Facebook Business Manager|привязан к Facebook-странице|"
            r"на базе ChatGPT|Google[- ]?ping|sitemap[- ]?ping",
            re.I,
        ),
        "факт мог устареть — проверить актуальность",
    ),
    (
        "Выдуманный кейс?",
        re.compile(r"<div class=\"example-label\">\s*Кейс[:\s]", re.I),
        "реальных кейса три: @eldarmurakov, @a.platonovva, «AI-агент заменил 3 менеджеров»",
    ),
]


def jsonld_text(html):
    """Человекочитаемые строки из JSON-LD.

    Разметку читают Google и нейросети, поэтому врать в ней нельзя так же,
    как в тексте. Раньше проверки её не видели: text_of вырезал <script>
    целиком, и выдуманное название системы Meta внутри FAQPage проходило
    мимо гейта честности.
    """
    out = []
    fields = ("name", "text", "description", "headline", "articleBody", "about")
    blocks = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, flags=re.S
    )

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in fields and isinstance(v, str):
                    out.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for block in blocks:
        try:
            walk(json.loads(block))
        except json.JSONDecodeError:
            continue  # битую разметку ловит preflight, здесь она не наша забота
    return " ".join(out)


def text_of(html):
    """Видимый текст плюс строки из JSON-LD, без script/style."""
    ld = jsonld_text(html)
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html) + " " + ld


def context(text, match, width=90):
    start = max(0, match.start() - width)
    end = min(len(text), match.end() + width)
    frag = " ".join(text[start:end].split())
    return frag


def audit(path, full=False):
    html = path.read_text(encoding="utf-8")
    body = text_of(html)
    hits = defaultdict(list)

    for name, pattern, _why in CHECKS:
        target = html if name == "Выдуманный кейс?" else body
        for m in pattern.finditer(target):
            frag = context(target if name == "Выдуманный кейс?" else body, m)
            # цифры с атрибуцией рядом — не считаем нарушением
            if name == "Цифры без источника" and ATTRIBUTION.search(frag):
                continue
            hits[name].append(frag)
    return hits


def changed_articles():
    """Статьи, изменённые относительно HEAD (незакоммиченные + новые)."""
    import subprocess

    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    ).stdout
    files = []
    for line in out.splitlines():
        rel = line[3:].strip().strip('"')
        if rel.startswith("blog/") and rel.endswith(".html"):
            name = Path(rel).name
            if name not in SKIP:
                files.append(ROOT / rel)
    return files


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full = "--full" in sys.argv

    if "--changed" in sys.argv:
        files = changed_articles()
        if not files:
            print("Изменённых статей нет — проверять нечего.")
            return 0
        print(f"Режим --changed: только новые и изменённые статьи\n")
    elif args:
        files = [Path(args[0])]
    else:
        files = sorted(p for p in BLOG.glob("*.html") if p.name not in SKIP)

    totals = defaultdict(int)
    ranked = []

    for path in files:
        hits = audit(path, full)
        count = sum(len(v) for v in hits.values())
        if count:
            ranked.append((count, path.name, hits))
        for k, v in hits.items():
            totals[k] += len(v)

    ranked.sort(reverse=True)

    print(f"Проверено статей: {len(files)}\n")
    print("=== СВОДКА ПО ТИПАМ ===")
    for name, pattern, why in CHECKS:
        n = totals.get(name, 0)
        mark = "✅" if n == 0 else "⚠️"
        print(f"  {mark} {name}: {n}")
        if n:
            print(f"      └ {why}")

    print(f"\n=== СТАТЬИ ПО ЧИСЛУ СРАБАТЫВАНИЙ (топ-15) ===")
    for count, name, hits in ranked[:15]:
        kinds = ", ".join(f"{k} ×{len(v)}" for k, v in sorted(hits.items()))
        print(f"  {count:3}  {name}")
        print(f"       {kinds}")

    if full:
        print(f"\n=== ЦИТАТЫ ===")
        for count, name, hits in ranked:
            print(f"\n── {name} ──")
            for kind, frags in sorted(hits.items()):
                for f in frags:
                    print(f"  [{kind}] …{f}…")

    print(f"\nСтатей без замечаний: {len(files) - len(ranked)} из {len(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
