#!/usr/bin/env python3
"""Голос в статьях: длинное тире и кавычки в видимом тексте.

Правило 19 CLAUDE.md и скилл /human: в текстах наружу короткое тире (-),
кавычек нет. Для Threads это держит voice-lint.py, для статей до 03.10.2026
проверки не было: тире вычищены, но «» в видимом тексте 1616 штук на 45 статьях.
Артём статьи не перечитывает, поэтому проверка кодом.

  python3 scripts/article-voice.py            # новые и изменённые статьи (git status)
  python3 scripts/article-voice.py --all      # все статьи, сводка
  python3 scripts/article-voice.py FILE ...   # конкретные файлы

Новая статья с тире или кавычками - выход 1 (preflight не пустит).
Изменённая старая - только предупреждение: старые чистятся отдельным решением.
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BAD = [("—", "длинное тире"), ("–", "среднее тире"), ("«", "кавычки"), ("»", "кавычки"),
       ("“", "кавычки"), ("”", "кавычки"), ("„", "кавычки")]


def visible(path):
    t = path.read_text(encoding="utf-8")
    m = re.search(r"<article[^>]*>(.*?)</article>", t, re.S) or re.search(r"<main[^>]*>(.*?)</main>", t, re.S)
    body = m.group(1) if m else t
    body = re.sub(r"<(script|style|code|pre)[^>]*>.*?</\1>", " ", body, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    title = re.search(r"<title>(.*?)</title>", t, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', t)
    head = " ".join(html.unescape(x.group(1)) for x in (title, desc) if x)
    return head + "\n" + text


def problems(path):
    s = visible(path)
    out = []
    for i, line in enumerate(s.splitlines()):
        for ch, name in BAD:
            for m in re.finditer(re.escape(ch), line):
                frag = line[max(0, m.start() - 35):m.end() + 35].strip()
                out.append((name, re.sub(r"\s+", " ", frag)))
    return out


def changed():
    st = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                        capture_output=True, text=True).stdout
    res = []
    for line in st.splitlines():
        code, rel = line[:2], line[3:].strip().strip('"')
        if rel.startswith("blog/") and rel.endswith(".html") and rel != "blog/index.html":
            res.append((ROOT / rel, code.strip() in ("??", "A")))
    return res


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        files = [(p, False) for p in sorted((ROOT / "blog").glob("*.html")) if p.name != "index.html"]
    elif args:
        files = [(Path(a).resolve(), True) for a in args]
    else:
        files = changed()
    if not files:
        print("  ✓ новых и изменённых статей нет")
        return 0
    fail = 0
    total = 0
    for path, is_new in files:
        pr = problems(path)
        total += len(pr)
        rel = path.relative_to(ROOT)
        if not pr:
            print("  ✓ %s: тире и кавычек нет" % rel)
            continue
        mark = "✗" if is_new else "⚠"
        print("  %s %s: %d (%s)" % (mark, rel, len(pr), ", ".join(sorted({n for n, _ in pr}))))
        if is_new or len(sys.argv) > 1 and "--all" not in sys.argv:
            for name, frag in pr[:5]:
                print("      %s: ...%s..." % (name, frag))
        fail |= is_new
    if "--all" in sys.argv:
        print("  всего: %d в %d статьях" % (total, sum(1 for p, _ in files if problems(p))))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
