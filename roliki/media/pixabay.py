#!/usr/bin/env python3
"""Библиотека живых картинок для роликов из Pixabay (ключ PIXABAY_API_KEY в ../../.env).

  python3 media/pixabay.py search photo "worried woman phone" --name trevoga   # 12 кандидатов + лист
  python3 media/pixabay.py search video "hacker typing" --name haker
  python3 media/pixabay.py keep trevoga 0 3 7                                   # отобранные -> lib/

Кандидаты: media/cand/<name>/NN.(jpg|mp4) и лист media/cand/<name>.jpg с номерами.
Отобранное: media/lib/<name>-NN.(jpg|mp4) + media/lib/index.json (откуда, теги).
Pixabay просит кэшировать у себя и не ставить прямые ссылки - поэтому всё скачиваем.
"""
import json, os, shutil, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CAND, LIB = HERE / 'cand', HERE / 'lib'
FONT = str(HERE.parent / 'fonts' / 'Inter.ttf')


def key():
    for line in (ROOT / '.env').read_text().splitlines():
        if line.startswith('PIXABAY_API_KEY='):
            return line.split('=', 1)[1].strip()
    sys.exit('нет PIXABAY_API_KEY в .env')


def get(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 bahramovai-roliki'})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)


def search(kind, q, name, n=12, extra=''):
    api = 'https://pixabay.com/api/' + ('videos/' if kind == 'video' else '')
    params = {'key': key(), 'q': q, 'safesearch': 'true', 'per_page': 40, 'order': 'popular'}
    if kind == 'photo':
        params.update(image_type='photo')
    for kv in filter(None, extra.split(',')):
        k, v = kv.split('=')
        params[k] = v
    req = urllib.request.Request(api + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'Mozilla/5.0 bahramovai-roliki'})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    d = CAND / name
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    meta, thumbs = [], []
    for h in data['hits']:
        if len(meta) >= n:
            break
        i = len(meta)
        if kind == 'photo':
            if h['imageWidth'] < 1200:
                continue
            f = d / f'{i:02d}.jpg'
            get(h['largeImageURL'], f)
            thumb = f
        else:
            v = h['videos'].get('small') or h['videos']['medium']
            if not v['url'] or h['duration'] < 3:
                continue
            f = d / f'{i:02d}.mp4'
            get(v['url'], f)
            thumb = d / f'{i:02d}.thumb.jpg'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1', '-i', str(f), '-frames:v', '1', str(thumb)], check=True)
        meta.append({'i': i, 'id': h['id'], 'page': h['pageURL'], 'tags': h['tags'], 'user': h['user'],
                     'w': h.get('imageWidth') or v['width'], 'h': h.get('imageHeight') or v['height'],
                     'dur': h.get('duration')})
        thumbs.append(thumb)
    (d / 'meta.json').write_text(json.dumps({'kind': kind, 'q': q, 'items': meta}, ensure_ascii=False, indent=1))
    sheet(thumbs, CAND / f'{name}.jpg')
    print(f'{name}: {len(meta)} кандидатов -> {CAND / (name + ".jpg")}')


def sheet(paths, out, cols=6, size=300):
    """Лист кандидатов: квадраты с номером в углу (PIL, у ffmpeg тут нет drawtext)."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    rows = (len(paths) + cols - 1) // cols
    im = Image.new('RGB', (cols * size, rows * size), 'black')
    font = ImageFont.truetype(FONT, 44)
    for i, p in enumerate(paths):
        t = ImageOps.fit(Image.open(p).convert('RGB'), (size, size))
        d = ImageDraw.Draw(t)
        d.rectangle([0, 0, 70, 58], fill='black')
        d.text((12, 4), str(i), font=font, fill='white')
        im.paste(t, ((i % cols) * size, (i // cols) * size))
    im.save(out, quality=85)


def keep(name, picks):
    d = CAND / name
    meta = json.loads((d / 'meta.json').read_text())
    LIB.mkdir(exist_ok=True)
    idx_f = LIB / 'index.json'
    idx = json.loads(idx_f.read_text()) if idx_f.exists() else {}
    ext = '.mp4' if meta['kind'] == 'video' else '.jpg'
    for p in picks:
        it = meta['items'][int(p)]
        dst = f'{name}-{int(p):02d}{ext}'
        shutil.copy(d / f'{int(p):02d}{ext}', LIB / dst)
        idx[dst] = {'kind': meta['kind'], 'q': meta['q'], **it}
    idx_f.write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    print(f'в библиотеке: {len(idx)}')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'search':
        extra = a[a.index('--extra') + 1] if '--extra' in a else ''
        search(a[1], a[2], a[a.index('--name') + 1], extra=extra)
    elif a and a[0] == 'keep':
        keep(a[1], a[2:])
    else:
        print(__doc__)
