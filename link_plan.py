#!/usr/bin/env python3
"""
Internal linking script for blog/*.html
Usage:
  python3 link_plan.py          # dry-run: shows plan without modifying files
  python3 link_plan.py --apply  # applies the links
"""
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

BLOG_DIR = Path("/Users/artem/Developer/bahramov/blog")
APPLY = "--apply" in sys.argv

# (regex_pattern, target_file, label)
# Order: most specific first. Each pattern is case-insensitive (re.I).
LINK_MAP = [
    # --- Instagram cluster ---
    (r"автоматизаци[юяией]\w* Instagram|ChatPlace",
     "chatplace-instagram-automation.html", "автоматизация Instagram/ChatPlace"),

    (r"device fingerprint\w*|цифров\w+ след\w+",
     "instagram-novyy-akkaunt-blokirovka-2026.html", "device fingerprint"),

    (r"нов\w+ аккаунт (с того же|без|от того|от другого)\b",
     "instagram-novyy-akkaunt-blokirovka-2026.html", "новый аккаунт (создание)"),

    (r"цепн\w+ блокировк\w+",
     "instagram-cepnaya-blokirovka-multiakkaunty-2026.html", "цепная блокировка"),

    (r"связку с другим заблокированным|попал в связку с",
     "instagram-cepnaya-blokirovka-multiakkaunty-2026.html", "связка с заблокированным"),

    (r"массов\w+ блокировк\w+ (Instagram|мая|в мае|2026)|волн[аеую] блокировок",
     "instagram-blokirovki-may-2026.html", "массовые блокировки"),

    (r"волна (таких )?проверок|идёт волна",
     "instagram-blokirovki-may-2026.html", "волна проверок"),

    (r"массов\w+ бан\w*|волн[аеую] бан\w+",
     "instagram-mass-ban-2026.html", "массовые баны"),

    (r"дв[а-я]+ аккаунт\w+ на одном|мультиаккаунт\w*|несколько аккаунт\w+ (на одном|Instagram)|несколько (страниц|аккаунтов)",
     "instagram-dva-akkaunta-odin-telefon-2026.html", "несколько аккаунтов"),

    (r"после разблокировк\w+|чек-лист (после|восстановлени\w+|безопасност\w+)",
     "instagram-posle-razblokirovki-cheklist-2026.html", "после разблокировки"),

    (r"просадк[аею]\w* охват\w*|упал[аи]?\w* охват\w*|recheck",
     "instagram-recheck-prosadka-ohvatov-2026.html", "просадка охватов / recheck"),

    (r"апелляци[юяей]\w* (в Meta|через|к|повторн\w+)|подать апелляцию|через апелляцию",
     "instagram-account-recovery-2026.html", "апелляция в Meta"),

    (r"восстановлени[ею]\w* (через апелляци\w+|через Meta|через официальн\w+)|апелляци[юя]\w* в Meta",
     "instagram-account-recovery-2026.html", "восстановление через Meta/апелляция"),

    (r"восстановлени[ею]\w* аккаунт\w*|разблокировк[аею]\w*|восстановить аккаунт\w*",
     "instagram-telegram-unblock.html", "восстановление аккаунта"),

    (r"блокировк\w+ нов\w+ аккаунт\w*|нов\w+ аккаунт\w* заблокировал\w*",
     "instagram-novyy-akkaunt-blokirovka-2026.html", "блокировка нового аккаунта"),

    # --- Telegram cluster ---
    (r"воронк\w+ (продаж|в Telegram|Telegram)|Telegram[- ]воронк\w+",
     "telegram-sales-funnel.html", "воронка продаж / Telegram-воронка"),

    (r"1000 подписчик\w*|тысяч[аею]\w* подписчик\w*|первые? (тысяч\w+|1000) подписчик\w*",
     "telegram-1000-subscribers.html", "1000 подписчиков"),

    # --- AI / automation cluster ---
    (r"AI[- ]стратеги[яюей]\w*|ИИ[- ]стратеги[яюей]\w*|стратеги[яюей]\w* (с AI|с ИИ|внедрения AI)",
     "ai-strategy-small-business.html", "AI-стратегия"),

    (r"виртуальн\w+ ассистент\w*",
     "virtual-assistant-cost-roi.html", "виртуальный ассистент"),

    (r"обучит[ье]\w* (AI|ИИ)[- ]?агент\w*|обучени[ею]\w* (AI|ИИ)[- ]?агент\w*|обучит[ье]\w* агент\w* (как|отвечать|правильно)",
     "train-ai-agent-like-manager.html", "обучить AI-агента"),

    (r"контент\w* (с нейросет\w+|без выгорани\w+)|выгорани[ею]\w* (от|при) контент\w*",
     "ai-content-without-burnout.html", "контент с нейросетями / выгорание"),

    (r"личн\w+ бренд\w*",
     "personal-brand-ai-strategy.html", "личный бренд"),

    (r"\b5 задач\w*|пять задач\w*|поручить (AI|ИИ)\b|делегировать (AI|ИИ)\b",
     "ai-assistant-5-tasks.html", "5 задач для AI"),

    (r"признак\w+ (что|когда) (нужен|нужн\w+) (AI|ИИ)[- ]?агент\w*|7 признак\w+",
     "7-signs-you-need-ai-agent.html", "7 признаков нужен AI-агент"),

    (r"Behavior AI|чат-бот\w+ (и|или|в) авто|чат-ботам и автопостинг",
     "ai-agents-2026.html", "Behavior AI / чат-боты"),

    (r"AI[- ]агент\w*|ИИ[- ]агент\w*",
     "ai-agents-2026.html", "AI-агенты"),
]

# Tags where we look for text to link
CONTENT_TAGS = {"p", "li"}

# Sections to skip (by class or id keywords)
SKIP_SECTION_CLASSES = {
    "related", "read-also", "cta", "nav", "footer", "header",
    "читайте", "рекомендуем", "смотрите", "breadcrumb",
}


def is_in_skip_section(tag):
    """Check if tag is inside a nav/footer/CTA/related section."""
    for parent in tag.parents:
        if parent.name in ("nav", "footer", "header"):
            return True
        cls = " ".join(parent.get("class", []))
        pid = parent.get("id", "")
        combined = (cls + " " + pid).lower()
        if any(skip in combined for skip in SKIP_SECTION_CLASSES):
            return True
    return False


def has_existing_link_to(tag, target_url):
    """Check if tag already contains an <a> pointing to the target."""
    for a in tag.find_all("a", href=True):
        if target_url in a["href"]:
            return True
    return False


def get_text_nodes_not_in_links(tag):
    """Yield NavigableString children that are NOT inside <a> tags."""
    for child in tag.descendants:
        if isinstance(child, NavigableString):
            if not any(p.name == "a" for p in child.parents if p != tag):
                yield child


def apply_link_to_string(nav_str, pattern, href, label, dry_run_record):
    """
    Find the first match of pattern in nav_str and wrap it in <a>.
    Returns True if a replacement was made.
    dry_run_record: list to append (original_phrase, context) for reporting.
    """
    text = str(nav_str)
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return False

    matched_phrase = m.group(0)
    start, end = m.start(), m.end()
    context_start = max(0, start - 25)
    context_end = min(len(text), end + 25)
    context = "…" + text[context_start:context_end].strip() + "…"

    dry_run_record.append((matched_phrase, context))

    if APPLY:
        # Build replacement: split string into before / link / after
        soup = nav_str.parent
        before = text[:start]
        after = text[end:]
        link_tag = BeautifulSoup(
            f'<a href="/blog/{href}">{matched_phrase}</a>', "html.parser"
        ).find("a")
        # Replace the NavigableString with the three parts
        nav_str.replace_with(NavigableString(before))
        # re-find where we inserted (the before string)
        # We need to insert after the before-string; use insert_after
        idx = list(soup.children).index(NavigableString(before)) if before else None
        # Simpler: rebuild via string replace on parent's string
        # Actually let's just manipulate the parent's markup directly
        # This gets tricky - use a different approach via parent decode/re-parse
        pass  # handled below in the caller

    return True


def process_file(filepath, global_link_counts, stats):
    """
    Process a single HTML file.
    global_link_counts: dict {target_url: int} across all files.
    stats: dict to accumulate per-file results.
    Returns list of (source_file, phrase, target_url, context).
    """
    html = filepath.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    filename = filepath.name

    # Track which targets have been linked in THIS file (only first occurrence)
    linked_in_file = set()
    # Max outgoing links per file
    MAX_PER_FILE = 5

    planned = []  # (phrase, target_url, label, context)

    content_tags = soup.find_all(CONTENT_TAGS)

    for tag in content_tags:
        if is_in_skip_section(tag):
            continue
        if len(linked_in_file) >= MAX_PER_FILE:
            break

        # Get raw text of tag (without inner <a> text)
        tag_text = tag.get_text()

        for pattern, target_url, label in LINK_MAP:
            # Skip self-link
            if target_url == filename:
                continue
            # Skip if already linked this target in this file
            if target_url in linked_in_file:
                continue
            # Skip if tag already has a link to this target
            if has_existing_link_to(tag, target_url):
                continue

            # Search in the raw text of the tag
            m = re.search(pattern, tag_text, re.IGNORECASE)
            if not m:
                continue

            matched_phrase = m.group(0)
            start = m.start()
            context_start = max(0, start - 30)
            context_end = min(len(tag_text), m.end() + 30)
            context = tag_text[context_start:context_end].strip().replace("\n", " ")

            planned.append((matched_phrase, target_url, label, context))
            linked_in_file.add(target_url)

            if len(linked_in_file) >= MAX_PER_FILE:
                break

    return planned


def apply_links_to_file(filepath, planned_links):
    """
    Apply planned links via raw string replacement.
    Preserves 100% of the original formatting — only the matched phrase
    is wrapped in <a href="...">, nothing else changes.
    """
    html = filepath.read_text(encoding="utf-8")

    # Tag pairs: (open_regex, close_regex) — we must NOT be inside these
    SKIP_PAIRS = [
        (r"<a[\s>]",      r"</a>"),
        (r"<script[\s>]", r"</script>"),
        (r"<style[\s>]",  r"</style>"),
        (r"<nav[\s>]",    r"</nav>"),
        (r"<footer[\s>]", r"</footer>"),
        (r"<header[\s>]", r"</header>"),
        (r"<title[\s>]",  r"</title>"),
    ]
    # We MUST be inside one of these
    CONTENT_PAIRS = [
        (r"<p[\s>]", r"</p>"),
        (r"<li[\s>]", r"</li>"),
    ]

    def context_ok(before: str) -> bool:
        for o, c in SKIP_PAIRS:
            if len(re.findall(o, before)) > len(re.findall(c, before)):
                return False
        for o, c in CONTENT_PAIRS:
            if len(re.findall(o, before)) > len(re.findall(c, before)):
                return True
        return False

    added = 0
    for phrase, target_url, label, _ctx in planned_links:
        search_from = 0
        while True:
            idx = html.find(phrase, search_from)
            if idx == -1:
                m = re.search(re.escape(phrase), html[search_from:], re.IGNORECASE)
                if not m:
                    break
                idx = search_from + m.start()

            end_idx = idx + len(phrase)
            if context_ok(html[:idx]):
                original = html[idx:end_idx]
                html = (html[:idx]
                        + f'<a href="/blog/{target_url}">{original}</a>'
                        + html[end_idx:])
                added += 1
                break
            search_from = end_idx

    return html, added


def main():
    files = sorted(
        f for f in BLOG_DIR.glob("*.html") if f.name != "index.html"
    )

    global_link_counts = {}  # target_url -> count across files
    all_planned = {}  # filename -> list of (phrase, target_url, label, context)

    for f in files:
        planned = process_file(f, global_link_counts, {})
        all_planned[f.name] = planned
        for _, target_url, _, _ in planned:
            global_link_counts[target_url] = global_link_counts.get(target_url, 0) + 1

    total = sum(len(v) for v in all_planned.values())

    if not APPLY:
        print("=" * 60)
        print(f"СТАТИСТИКА (dry-run)")
        print("=" * 60)
        print(f"\nВсего запланировано ссылок: {total}")
        print(f"Файлов с изменениями: {sum(1 for v in all_planned.values() if v)}")
        print()

        # Top files by changes
        sorted_files = sorted(all_planned.items(), key=lambda x: -len(x[1]))
        print("Файлы по убыванию изменений:")
        for i, (fn, links) in enumerate(sorted_files[:20], 1):
            if links:
                print(f"  {i:2}. {fn} — {len(links)} ссылок")

        print()
        print("=" * 60)
        print("ДЕТАЛЬНЫЙ ПЛАН")
        print("=" * 60)
        for fn, links in sorted_files:
            if not links:
                continue
            print(f"\nFILE: {fn}")
            for i, (phrase, target_url, label, context) in enumerate(links, 1):
                print(f"  [{i}] «{phrase}» → /blog/{target_url}")
                print(f"      Контекст: …{context}…")

        print()
        print("=" * 60)
        print("ПРИМЕР (первая ссылка в плане)")
        print("=" * 60)
        for fn, links in sorted_files:
            if links:
                phrase, target_url, label, context = links[0]
                print(f"\nВ статье '{fn}':")
                print(f"  фраза «{phrase}»")
                print(f"  → <a href=\"/blog/{target_url}\">{phrase}</a>")
                print(f"  контекст: …{context}…")
                break

        print()
        print("Запустите с --apply для применения изменений.")
        return

    # APPLY MODE
    print("Применяю ссылки...")
    changed = 0
    real_total = 0
    for f in files:
        planned = all_planned.get(f.name, [])
        if not planned:
            continue
        new_html, added = apply_links_to_file(f, planned)
        f.write_text(new_html, encoding="utf-8")
        print(f"  ✓ {f.name} ({added}/{len(planned)} ссылок)")
        changed += 1
        real_total += added
    print(f"\nГотово. Изменено файлов: {changed}, добавлено ссылок: {real_total} (план: {total})")


if __name__ == "__main__":
    main()
