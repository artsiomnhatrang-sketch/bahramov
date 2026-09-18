#!/usr/bin/env python3
"""Ссылка должна вести туда, как она подписана.

Прецедент 18.09.2026: на consent.html и privacy.html четыре ссылки были
подписаны @bahramovartem_bot, а вели в личные сообщения t.me/bahramovartsiom.
Битой ссылкой это не считается — адрес живой, поэтому preflight молчал.
Ловим именно расхождение подписи и адреса.
"""
import pathlib, re, sys

LINK = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.S | re.I)
HREF = re.compile(r'href="([^"]+)"', re.I)
TAGS = re.compile(r'<[^>]+>')

BOT   = 'bahramovartem_bot'
DM    = 'bahramovartsiom'

def check(text, href):
    """Возвращает описание проблемы или None."""
    t = TAGS.sub('', text).strip().lower()
    h = href.lower()
    if not t:
        return None
    if BOT in t and BOT not in h:
        return f'подписана как бот, ведёт на {href}'
    if DM in t and BOT in h:
        return f'подписана как личный аккаунт, ведёт в бота'
    if t in ('max', 'написать в max') and 'max.ru' not in h:
        return f'подписана MAX, ведёт на {href}'
    if re.fullmatch(r'[\w.+-]+@[\w-]+\.[\w.]+', t) and not h.startswith('mailto:'):
        return f'подписана почтой, ведёт на {href}'
    if t == 'почта' and not h.startswith('mailto:'):
        return f'подписана «Почта», ведёт на {href}'
    return None

def main():
    root = pathlib.Path('.')
    files = sorted(set(root.glob('*.html')) | set(root.glob('blog/*.html')) | set(root.glob('uslugi/*.html')))
    bad = []
    for f in files:
        s = f.read_text(encoding='utf-8')
        for m in LINK.finditer(s):
            hm = HREF.search(m.group(1))
            if not hm:
                continue
            problem = check(m.group(2), hm.group(1))
            if problem:
                line = s[:m.start()].count('\n') + 1
                bad.append(f'{f}:{line} — {problem}')
    if bad:
        print(f'  ✗ Подпись ссылки не совпадает с адресом: {len(bad)}')
        for b in bad[:15]:
            print(f'      {b}')
        return 1
    print(f'  ✓ Подписи ссылок совпадают с адресами ({len(files)} страниц)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
