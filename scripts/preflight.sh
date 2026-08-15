#!/bin/bash
# Все проверки сайта одной командой.
#
#   ./scripts/preflight.sh          — перед пушем: техника + контент
#   ./scripts/preflight.sh --tema "ключевые слова"  — перед новой статьёй: проверка на дубль
#
# Выход 0 — можно публиковать. Выход 1 — есть блокирующие проблемы.

set -u
cd "$(dirname "$0")/.." || exit 1

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; BOLD=$'\033[1m'; OFF=$'\033[0m'
FAIL=0

section() { printf "\n${BOLD}%s${OFF}\n" "$1"; }
ok()      { printf "  ${GREEN}✓${OFF} %s\n" "$1"; }
warn()    { printf "  ${YELLOW}!${OFF} %s\n" "$1"; }
bad()     { printf "  ${RED}✗${OFF} %s\n" "$1"; FAIL=1; }

# --- Режим проверки темы на дубль (перед написанием новой статьи) ---
if [ "${1:-}" = "--tema" ]; then
  TEMA="${2:-}"
  if [ -z "$TEMA" ]; then
    echo "Укажи тему: ./scripts/preflight.sh --tema \"ai агент instagram автоматизация\""
    exit 1
  fi
  section "Проверка темы на дубль: «$TEMA»"
  TEMA="$TEMA" python3 - <<'PY'
import os, re
from pathlib import Path

tema = [w.lower() for w in os.environ["TEMA"].split() if len(w) > 2]
rows = []
for p in sorted(Path("blog").glob("*.html")):
    if p.name == "index.html":
        continue
    html = p.read_text(encoding="utf-8")
    heads = " ".join(re.sub(r"<[^>]+>", "", h)
                     for h in re.findall(r"<h[12][^>]*>(.*?)</h[12]>", html, re.S)).lower()
    body = re.sub(r"<[^>]+>", " ", html).lower()
    in_head = sum(1 for w in tema if w in heads)
    in_body = sum(1 for w in tema if w in body)
    if in_head or in_body == len(tema):
        title = re.search(r"<title>([^<]*)</title>", html)
        rows.append((in_head, in_body, p.name, title.group(1) if title else ""))

rows.sort(reverse=True)
if not rows:
    print("  Совпадений нет — тема свободна.")
else:
    print("  Слов темы в заголовках / в тексте:")
    for in_head, in_body, name, title in rows[:10]:
        flag = "  ⚠ СИЛЬНОЕ" if in_head >= max(2, len(tema) - 1) else ""
        print(f"    {in_head}/{len(tema)} загол., {in_body}/{len(tema)} текст  {name}{flag}")
        print(f"        {title[:70]}")
    strong = [r for r in rows if r[0] >= max(2, len(tema) - 1)]
    print()
    if strong:
        print(f"  ⚠ Тема уже раскрыта в {len(strong)} стать(ях). Скорее всего нужно")
        print("    усиливать существующую, а не писать новую.")
    else:
        print("  Прямых конкурентов по заголовкам нет — тему можно брать.")
PY
  echo
  echo "  Правило: две страницы под один запрос конкурируют между собой в выдаче."
  echo "  Если тема уже раскрыта — усиливай существующую статью."
  exit 0
fi

# --- Обычный режим: полная проверка перед пушем ---
printf "${BOLD}PREFLIGHT — проверка сайта перед публикацией${OFF}\n"

section "1. Техника: ссылки, картинки, разметка, sitemap"
AUDIT=$(python3 scripts/site-audit.py 2>&1)
for check in "Битые внутренние ссылки" "Битые картинки" "Ссылки без href" "Sitemap рассинхрон" "Кривая кодировка"; do
  n=$(echo "$AUDIT" | grep -o "=== $check ([0-9]*)" | grep -o '[0-9]*')
  if [ "${n:-0}" = "0" ]; then ok "$check: чисто"; else bad "$check: $n"; fi
done

section "2. Статистические карточки"
if python3 scripts/check-stat-cards.py > /tmp/statcards.log 2>&1; then
  ok "$(tail -1 /tmp/statcards.log)"
else
  bad "$(tail -1 /tmp/statcards.log)"
fi

section "3. JSON-LD во всех страницах"
python3 - <<'PY'
import json, re, sys
from pathlib import Path
bad = 0; total = 0
for p in sorted(Path('.').glob('*.html')) + sorted(Path('blog').glob('*.html')):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', p.read_text(encoding='utf-8'), re.S):
        total += 1
        try: json.loads(m.group(1))
        except json.JSONDecodeError as e:
            bad += 1; print(f"  \033[31m✗\033[0m {p}: {e}")
print(f"  \033[32m✓\033[0m блоков разметки: {total}, битых: {bad}" if not bad else f"  битых блоков: {bad}")
sys.exit(1 if bad else 0)
PY
[ $? -ne 0 ] && FAIL=1

section "4. RSS-фид"
FEED=$(python3 scripts/seo-sync.py --check 2>&1)
echo "$FEED" | grep -q "УСТАРЕЛ" && warn "feed.xml устарел — запусти: python3 scripts/seo-sync.py" || ok "feed.xml актуален"

section "5. Повторы между статьями"
OVERLAP=$(python3 scripts/overlap-audit.py 2>&1)
PAIRS=$(echo "$OVERLAP" | grep -c "% общих тем")
if [ "$PAIRS" = "0" ]; then ok "статей-дублей нет"; else warn "пар с пересечением тем: $PAIRS (см. scripts/overlap-audit.py)"; fi

section "6. Честность контента (только изменённые статьи)"
CONTENT=$(python3 scripts/content-audit.py --changed 2>&1)
if echo "$CONTENT" | grep -q "Изменённых статей нет"; then
  ok "изменённых статей нет — проверять нечего"
else
  echo "$CONTENT" | sed -n '/СВОДКА ПО ТИПАМ/,/СТАТЬИ ПО ЧИСЛУ/p' | grep -E "✅|⚠️"
  warn "цитаты: python3 scripts/content-audit.py --changed --full"
  warn "в старых статьях цифры реальные (из практики владельца) — их не трогаем"
fi

printf "\n${BOLD}────────────────────────────${OFF}\n"
if [ $FAIL -eq 0 ]; then
  printf "${GREEN}${BOLD}Блокирующих проблем нет — можно пушить.${OFF}\n"
else
  printf "${RED}${BOLD}Есть блокирующие проблемы — исправь перед пушем.${OFF}\n"
fi
exit $FAIL
