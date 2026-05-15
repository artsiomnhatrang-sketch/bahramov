#!/usr/bin/env python3
"""
Pre-publish check: stat-card / metric-value overflow risk.
Exit 0 = all clear. Exit 1 = РИСК or КРИТИЧНО found — publish aborted.
"""
import re, sys
from pathlib import Path

BLOG = Path(__file__).parent.parent / "blog"

BIG_CLS = re.compile(
    r'<(?:span|div|p)\s+class="(stat-number|metric-value)"[^>]*>(.*?)</(?:span|div|p)>',
    re.DOTALL | re.I
)

def css_insured(html, cls):
    m = re.search(rf'\.{re.escape(cls)}\s*\{{([^}}]+)\}}', html)
    if not m: return False
    b = m.group(1)
    return "clamp(" in b and "word-break" in b and "overflow-wrap" in b

problems, rows = [], []
for f in sorted(BLOG.glob("*.html")):
    if f.name == "index.html": continue
    html = f.read_text("utf-8")
    for cls, raw in BIG_CLS.findall(html):
        text = re.sub(r"<[^>]+>", "", raw).strip()
        text = text.replace("&lt;","<").replace("&nbsp;"," ").replace("&amp;","&")
        n = len(text)
        insured = css_insured(html, cls)
        if n > 15:
            verdict = "КРИТИЧНО" if not insured else "РИСК"
        elif n > 8:
            verdict = "РИСК" if not insured else "OK"
        else:
            verdict = "OK"
        rows.append((f.name, cls, text, n, insured, verdict))
        if verdict != "OK":
            problems.append((f.name, cls, text, n, verdict))

ok = sum(1 for r in rows if r[5] == "OK")
print(f"stat-card check: {len(rows)} карточек — {ok} OK, {len(problems)} проблем")
for fn, cls, text, n, v in problems:
    print(f"  {v}: {fn} .{cls} «{text}» ({n} симв)")

sys.exit(1 if problems else 0)
