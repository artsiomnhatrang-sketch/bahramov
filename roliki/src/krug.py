"""Кружок с лицом Артёма поверх готового ролика (08.10).

python3 src/krug.py <ролик.mp4> <лицо.mp4> <выход.mp4> [--intro 2.6] [--cx 850 --cy 1355 --r 108]

Лицо (квадратное видео с губами под голос) делает ~/Developer/lico-artem/govori.py.
--intro N: первые N секунд (фраза-хук) лицо крупно на месте картинки сцены, потом за 0,35 с уменьшается
в кружок - живое лицо в кадре 0 держит зрителя, смена плана на хуке ещё раз цепляет взгляд.
Кружок: справа от субтитров, под картинкой сцены (её не закрывает); правее x 960 не заходим
(кнопки лайков Shorts, Reels, TikTok). Обводка оранжевая #f4672a, как на сайте.
"""
import argparse
import json
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

p = argparse.ArgumentParser()
p.add_argument('video'); p.add_argument('lico'); p.add_argument('out')
p.add_argument('--cx', type=int, default=850)
p.add_argument('--cy', type=int, default=1355)
p.add_argument('--r', type=int, default=108)
p.add_argument('--intro', type=float, default=0.0)
p.add_argument('--big', default='540,945,330', help='крупное лицо на хуке: cx,cy,r (место картинки сцены)')
p.add_argument('--plan', help='монтаж v3: JSON {keys: [[t, cx, cy, r], ...], bounce: [t, ...]} из render.mjs')
a = p.parse_args()

W, H, SHRINK = 1080, 1920, 0.35
BIG = tuple(int(v) for v in a.big.split(','))
SMALL = (a.cx, a.cy, a.r)
ORANGE = (244, 103, 42)
PLAN = json.load(open(a.plan)) if a.plan else None
BOUNCE = 0.28  # подпрыгивание кружка на акценте: вверх и чуть больше, за 0,28 с обратно


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height,r_frame_rate:format=duration', '-of', 'json', path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out); s = j['streams'][0]; n, d = s['r_frame_rate'].split('/')
    return s['width'], s['height'], int(n) / int(d), float(j['format']['duration'])


def geom_plan(t):
    """v3: между ключевыми точками плана - плавно (ease-in-out), плюс подпрыгивание маленького кружка."""
    K = PLAN['keys']
    if t <= K[0][0]:
        g = K[0][1:]
    elif t >= K[-1][0]:
        g = K[-1][1:]
    else:
        j = next(i for i in range(1, len(K)) if K[i][0] >= t)
        (t0, *g0), (t1, *g1) = K[j - 1], K[j]
        k = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
        k = 4 * k ** 3 if k < 0.5 else 1 - (-2 * k + 2) ** 3 / 2
        g = [b + (s - b) * k for b, s in zip(g0, g1)]
    cx, cy, r = g
    if r < 150:
        b = max((np.sin(np.pi * (t - tb) / BOUNCE) for tb in PLAN.get('bounce', []) if 0 <= t - tb < BOUNCE), default=0.0)
        cy -= 18 * b
        r *= 1 + 0.12 * b
    return round(cx), round(cy), round(r)


def geom(t):
    """Центр и радиус кружка в момент t: крупно на хуке, плавное уменьшение, дальше маленький."""
    if PLAN:
        return geom_plan(t)
    if t < a.intro:
        return BIG
    k = min(1.0, (t - a.intro) / SHRINK) if a.intro else 1.0
    k = 1 - (1 - k) ** 3  # ease-out
    return tuple(round(b + (s - b) * k) for b, s in zip(BIG, SMALL))


@lru_cache(maxsize=512)
def layers(r):
    """Маска лица (сглаженный край), тень и оранжевое кольцо. Кэш по радиусу."""
    ring = max(5, round(r * 0.065)); S = 4
    m = Image.new('L', (2 * r * S, 2 * r * S), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 2 * r * S - 1, 2 * r * S - 1], fill=255)
    mask = np.asarray(m.resize((2 * r, 2 * r), Image.LANCZOS), dtype=np.float32)[..., None] / 255
    pad = ring + max(12, r // 8); O = r + pad
    sh = Image.new('L', (2 * O, 2 * O), 0)
    ImageDraw.Draw(sh).ellipse([pad - ring, pad - ring + r // 18, 2 * O - pad + ring, 2 * O - pad + ring + r // 18], fill=140)
    sh = sh.filter(ImageFilter.GaussianBlur(max(6, r // 12)))
    d = Image.new('L', (2 * (r + ring) * S,) * 2, 0)
    ImageDraw.Draw(d).ellipse([0, 0, 2 * (r + ring) * S - 1, 2 * (r + ring) * S - 1], fill=255)
    d = d.resize((2 * (r + ring),) * 2, Image.LANCZOS)
    disc = Image.new('L', (2 * O, 2 * O), 0); disc.paste(d, (pad - ring, pad - ring))
    sh_a = np.asarray(sh, dtype=np.float32)[..., None] / 255
    disc_a = np.asarray(disc, dtype=np.float32)[..., None] / 255
    return mask, sh_a, disc_a, O


def blend(frame, x0, y0, rgb, alpha):
    """Наложить rgb с alpha в frame с левого верхнего угла (x0, y0), с обрезкой по краям кадра."""
    h, w = alpha.shape[:2]
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if fx0 >= fx1 or fy0 >= fy1:
        return
    sx0, sy0 = fx0 - x0, fy0 - y0
    al = alpha[sy0:sy0 + fy1 - fy0, sx0:sx0 + fx1 - fx0]
    src = rgb if np.ndim(rgb) == 1 else rgb[sy0:sy0 + fy1 - fy0, sx0:sx0 + fx1 - fx0]
    dst = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = (dst * (1 - al) + np.asarray(src, dtype=np.float32) * al).astype(np.uint8)


vw, vh, vfps, vdur = probe(a.video)
lw, lh, lfps, ldur = probe(a.lico)
assert (vw, vh) == (W, H), f'ролик {vw}x{vh}, ждём {W}x{H}'
dec_v = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.video, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
dec_l = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.lico, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(vfps), '-i', '-', '-i', a.video, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                        '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest',
                        '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
fsz, lsz = W * H * 3, lw * lh * 3
face, face_i = None, -1
i = 0
while True:
    buf = dec_v.stdout.read(fsz)
    if len(buf) < fsz:
        break
    frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    t = i / vfps
    want = int(t * lfps)
    while face_i < want:  # лицо 25 к/с, ролик 30 к/с: берём кадр лица по времени
        lb = dec_l.stdout.read(lsz)
        if len(lb) < lsz:
            break
        face, face_i = np.frombuffer(lb, np.uint8).reshape(lh, lw, 3), face_i + 1
    if face is not None and t <= ldur + 0.1:
        cx, cy, r = geom(t)
        mask, sh_a, disc_a, O = layers(r)
        blend(frame, cx - O, cy - O, np.array((0, 0, 0)), sh_a)
        blend(frame, cx - O, cy - O, np.array(ORANGE), disc_a)
        f = np.asarray(Image.fromarray(face).resize((2 * r, 2 * r), Image.LANCZOS))
        blend(frame, cx - r, cy - r, f, mask)
    enc.stdin.write(frame.tobytes())
    i += 1
enc.stdin.close(); enc.wait(); dec_v.wait(); dec_l.kill()
if enc.returncode:
    raise SystemExit(f'ffmpeg вернул {enc.returncode}')
print('кружок готов:', a.out, f'({i} кадров, хук крупно {a.intro:.2f} с)')
