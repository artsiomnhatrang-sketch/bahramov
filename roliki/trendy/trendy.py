"""Слежка за топовыми роликами ниши (блокировки Instagram/Telegram, охваты, AI-автоматизация) на YouTube (без ключей, через yt-dlp).
Ищет по запросам на английском и русском за неделю и месяц, сортирует по просмотрам,
отдельно — короткие (Shorts, до 3 мин) и длинные. По каналам из kanaly.txt ищет «выстрелы»:
ролики, набравшие в 3+ раза больше своего обычного.
Отчёт: otchety/ГГГГ-ММ-ДД.md — только темы и названия, чужие тексты не копируем.
  python3 trendy.py
"""
import json, subprocess, statistics, datetime, os, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
QUERIES = {
    'en': ['instagram account disabled', 'instagram shadowban', 'instagram reach dropped',
           'instagram account hacked recover', 'ai automation business', 'instagram dm automation'],
    'ru': ['заблокировали инстаграм', 'восстановить аккаунт инстаграм', 'взломали телеграм',
           'упали охваты инстаграм', 'теневой бан инстаграм', 'автоматизация бизнеса нейросеть',
           'чат бот для инстаграм', 'ai агент для бизнеса'],
}
PERIODS = {'неделя': 'CAMSBAgDEAE%3D', 'месяц': 'CAMSBAgEEAE%3D'}  # сортировка по просмотрам + период

def ytdlp(url, n):
    out = subprocess.run(['yt-dlp', '--flat-playlist', '--playlist-end', str(n), '-J', url],
                         capture_output=True, text=True, timeout=180).stdout
    try:
        d = json.loads(out)
        es = d.get('entries') or []
        name = (d.get('channel') or d.get('uploader') or d.get('title') or '').replace(' - Shorts', '').replace(' - Videos', '')
        for e in es:
            e.setdefault('channel', name)
            if not e.get('channel'):
                e['channel'] = name
        return es
    except Exception:
        return []

def search(q, sp, n=40):
    return ytdlp(f'https://www.youtube.com/results?search_query={urllib.parse.quote(q)}&sp={sp}', n)

def row(e):
    return {'views': e.get('view_count') or 0, 'dur': e.get('duration') or 0,
            'channel': e.get('channel') or e.get('uploader') or '', 'title': (e.get('title') or '').replace('|', '/'),
            'url': e.get('url') or f"https://www.youtube.com/watch?v={e.get('id')}",
            'curl': e.get('channel_url') or e.get('uploader_url') or ''}

def fmt(n):
    return f'{n/1e6:.1f} млн' if n >= 1e6 else f'{n/1e3:.0f} тыс' if n >= 1e3 else str(n)

def main():
    today = datetime.date.today().isoformat()
    seen, hits = set(), {('en', 's'): [], ('en', 'l'): [], ('ru', 's'): [], ('ru', 'l'): []}
    for lang, qs in QUERIES.items():
        for q in qs:
            for period, sp in PERIODS.items():
                for e in search(q, sp):
                    r = row(e)
                    if not r['dur'] or r['url'] in seen:
                        continue
                    seen.add(r['url']); r['period'] = period
                    hits[(lang, 's' if r['dur'] <= 180 else 'l')].append(r)
    L = [f'# Ниша роликов: что набирает просмотры — {today}\n',
         'YouTube, поиск по просмотрам за неделю и месяц. Берём темы и форматы, тексты пишем свои.\n']
    names = {('en', 's'): 'Зарубежные Shorts', ('ru', 's'): 'Русские Shorts',
             ('en', 'l'): 'Зарубежные длинные', ('ru', 'l'): 'Русские длинные'}
    for key, title in names.items():
        top = sorted(hits[key], key=lambda r: -r['views'])[:20]
        L.append(f'\n## {title}\n\n| Просмотры | Длина | Канал | Название |\n|---|---|---|---|')
        for r in top:
            L.append(f"| {fmt(r['views'])} | {r['dur']//60}:{r['dur']%60:02d} | {r['channel'][:28]} | [{r['title'][:80]}]({r['url']}) |")
    # Каналы: список kanaly.txt + сами нашлись в поиске (топ-8 по сумме просмотров на каждом языке).
    # Shorts поиск YouTube не отдаёт — их берём со страниц каналов.
    path = os.path.join(HERE, 'kanaly.txt')
    chans = [l.split('#')[0].strip() for l in open(path, encoding='utf-8')] if os.path.exists(path) else []
    chans = [c for c in chans if c]
    for lang in ('en', 'ru'):
        tot = {}
        for r in hits[(lang, 'l')] + hits[(lang, 's')]:
            if r['curl']:
                tot[r['curl']] = tot.get(r['curl'], 0) + r['views']
        for c, _ in sorted(tot.items(), key=lambda x: -x[1])[:8]:
            if c not in chans:
                chans.append(c)
        names_ = {r['curl']: r['channel'] for r in hits[(lang, 'l')] + hits[(lang, 's')]}
        L.append(f'\n_Каналы, найденные поиском ({lang}): ' + ', '.join(names_.get(c, c) for c, _ in sorted(tot.items(), key=lambda x: -x[1])[:8]) + '_')
    shorts_by_lang = {'en': [], 'ru': []}
    if chans:
        L.append('\n## Выстрелы на каналах из списка (в 3+ раза выше обычного)\n')
        for c in chans:
            for tab in ('shorts', 'videos'):
                es = [row(e) for e in ytdlp(f'{c.rstrip("/")}/{tab}', 30)]
                for r in es:
                    r['channel'] = r['channel'] or c.split('/')[-1]
                if tab == 'shorts':
                    lang = 'ru' if any('\u0400' <= ch <= '\u04ff' for r in es for ch in r['title']) else 'en'
                    shorts_by_lang[lang] += es
                vs = [r['views'] for r in es if r['views']]
                if len(vs) < 5:
                    continue
                med = statistics.median(vs)
                for r in sorted(es, key=lambda r: -r['views']):
                    if r['views'] >= 3 * med:
                        L.append(f"- {(es[0]['channel'] if es else c.split('/')[-1])} ({tab}, обычно {fmt(int(med))}): **{fmt(r['views'])}** — [{r['title'][:80]}]({r['url']})")
        for lang, title in (('en', 'Зарубежные Shorts с каналов'), ('ru', 'Русские Shorts с каналов')):
            top = sorted(shorts_by_lang[lang], key=lambda r: -r['views'])[:25]
            L.append(f'\n## {title} (последние 30 на канале)\n\n| Просмотры | Канал | Название |\n|---|---|---|')
            for r in top:
                L.append(f"| {fmt(r['views'])} | {r['channel'][:28]} | [{r['title'][:80]}]({r['url']}) |")
    out = os.path.join(HERE, 'otchety', f'{today}.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    json.dump({k[0] + k[1]: v for k, v in hits.items()}, open(os.path.join(HERE, 'otchety', f'{today}.json'), 'w'), ensure_ascii=False)
    print(out)

if __name__ == '__main__':
    main()
