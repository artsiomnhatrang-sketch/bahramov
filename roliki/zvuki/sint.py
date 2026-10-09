#!/usr/bin/env python3
"""Звуки монтажа v3 (09.10): синтезируем сами - ни прав, ни Content ID, бесплатно.

python3 zvuki/sint.py  ->  zvuki/{bass,click,ding,riser,stamp,pop}.wav (48 кГц, моно)

bass   - удар баса на хуке (кадр 0): саб-удар 110 -> 38 Гц + щелчок атаки
click  - щелчок появления текста (заголовок сцены)
ding   - «дзынь» на цифрах
riser  - нарастание 1,1 с перед раскрытием (шум с поднимающимся фильтром + свип), обрывается на ударе
stamp  - глухой штамп под крестик/галочку
pop    - короткий «поп» под всплывающий эмодзи
Громкость подбирается в render.mjs (SFX), здесь всё нормировано к пику -1 дБ.
"""
import wave
from pathlib import Path

import numpy as np

SR = 48000
HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(9)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(x, a=0.003, k=8.0):
    """Атака a секунд, дальше экспонента с коэффициентом k."""
    tt = np.arange(len(x)) / SR
    return x * np.minimum(1, tt / a) * np.exp(-k * tt)


def sweep(f0, f1, d, curve=3.0):
    """Синус с частотой от f0 к f1 (экспоненциально), фаза интегрируется."""
    tt = t(d)
    f = f1 + (f0 - f1) * np.exp(-curve * tt / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def bandnoise(d, lo, hi):
    n = rng.standard_normal(int(SR * d))
    sp = np.fft.rfft(n)
    fr = np.fft.rfftfreq(len(n), 1 / SR)
    sp[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(sp, len(n))


def save(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89  # -1 дБ
    fade = int(SR * 0.004)
    x[-fade:] *= np.linspace(1, 0, fade)
    with wave.open(str(HERE / f'{name}.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


# удар баса: саб с падающей частотой, длинный хвост + короткий щелчок атаки
d = 1.3
bass = env(sweep(110, 38, d, 5), a=0.002, k=3.2)
bass += 0.35 * env(bandnoise(d, 1500, 6000), a=0.0005, k=90)
bass += 0.25 * env(np.tanh(3 * sweep(220, 80, d, 6)), a=0.001, k=14)  # «тело» удара
save('bass', bass)

# щелчок: очень короткий шумовой импульс + блик 2,4 кГц
d = 0.09
click = 0.8 * env(bandnoise(d, 2500, 9000), a=0.0003, k=160) + 0.5 * env(np.sin(2 * np.pi * 2400 * t(d)), a=0.0005, k=110)
save('click', click)

# дзынь: колокольчик (основной тон + негармонические обертоны)
d = 1.1
ding = sum(g * env(np.sin(2 * np.pi * f * t(d)), a=0.002, k=k) for f, g, k in
           [(1760, 1.0, 4.5), (2640, 0.45, 6.5), (4416, 0.22, 9), (5280, 0.12, 12)])
save('ding', ding)

# нарастание: шум с поднимающейся полосой + свип вверх, громкость растёт к концу и обрывается
d = 1.1
n = int(SR * d)
seg, hop = 4096, 1024  # куски с перекрытием и окном Ханна - без щелчков на стыках
noise = np.zeros(n + seg)
win = np.hanning(seg)
for i in range(0, n, hop):
    k = i / n
    lo, hi = 300 + 2500 * k ** 2, 1200 + 9000 * k ** 2
    noise[i:i + seg] += bandnoise(seg / SR, lo, hi) * win
noise = noise[:n]
tone = np.sin(2 * np.pi * np.cumsum(220 + 1100 * (t(d) / d) ** 2) / SR)
riser = (0.7 * noise + 0.35 * tone) * (t(d) / d) ** 2.2
save('riser', riser)

# штамп: глухой удар 70 Гц + короткий шум
d = 0.35
stamp = env(sweep(140, 60, d, 6), a=0.001, k=16) + 0.5 * env(bandnoise(d, 200, 3000), a=0.0005, k=45)
save('stamp', stamp)

# поп: короткий свип вверх
d = 0.14
pop = env(sweep(500, 1300, d, 4), a=0.002, k=30)
save('pop', pop)

print('звуки готовы:', ', '.join(f'{x}.wav' for x in ['bass', 'click', 'ding', 'riser', 'stamp', 'pop']))
