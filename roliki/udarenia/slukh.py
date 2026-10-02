"""Проверка ударений «по звуку»: куда голос edge-tts САМ ставит ударение в слове.
Для слова синтезируем: (а) как есть, без подсказки; (б) по образцу с ударением на каждом слоге.
Сравниваем (а) с каждым (б) по звуку (MFCC + DTW): ближайший образец = ударение голоса.
Если оно не совпадает с правильным (словарь ruaccent / slovar.txt / пометка «+») — слово надо помечать.
Результаты кэшируются в slukh-cache.json (слово + голос), второй раз не синтезируем.
  python3 slukh.py --voice ru-RU-SvetlanaNeural слово1 слово2 ...   → печатает разбор
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np
import librosa

HERE = os.path.dirname(os.path.abspath(__file__))
ACUTE = '́'
VOWELS = 'аеёиоуыэюя'
CACHE = os.path.join(HERE, 'slukh-cache.json')
TMP = tempfile.mkdtemp()


def synth(text, voice, out):
    # Дмитрий иногда молча не отдаёт звук — повторяем с безобидными вариантами
    for t in (text, ' ' + text, text + '.', ' ' + text + '.', text, text + '!'):
        r = subprocess.run(['edge-tts', '--voice', voice, '--text', t, '--write-media', out], capture_output=True)
        if r.returncode == 0 and os.path.getsize(out) > 1000:
            return True
    return False


def feats(path):
    y, sr = librosa.load(path, sr=16000)
    y, _ = librosa.effects.trim(y, top_db=35)
    m = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20, hop_length=160)
    m = (m - m.mean(axis=1, keepdims=True)) / (m.std(axis=1, keepdims=True) + 1e-6)
    e = librosa.feature.rms(y=y, hop_length=160)  # громкость — ударный слог громче и длиннее
    return np.vstack([m, 4 * (e / (e.max() + 1e-9))])


def dist(a, b):
    D, wp = librosa.sequence.dtw(X=a, Y=b, metric='euclidean')
    return D[-1, -1] / len(wp)


def vowel_pos(w):
    return [i for i, c in enumerate(w) if c in VOWELS]


def voice_stress(word, voice, cache):
    """Номер слога (0..), на который голос ставит ударение сам, и уверенность."""
    key = f'{voice}|{word}'
    if key in cache:
        return cache[key]
    pos = vowel_pos(word)
    base = os.path.join(TMP, 'base.mp3')
    if not synth(word, voice, base):
        return None
    fb = feats(base)
    ds = []
    for k, p in enumerate(pos):
        if 'ё' in word and word[p] != 'ё':
            ds.append(9e9); continue
        v = word[:p + 1] + ACUTE + word[p + 1:]
        f = os.path.join(TMP, f'v{k}.mp3')
        ds.append(dist(fb, feats(f)) if synth(v, voice, f) else 9e9)
    order = sorted(range(len(ds)), key=lambda i: ds[i])
    best = order[0]
    # уверенность: насколько ближайший образец ближе второго
    conf = 1 - ds[best] / ds[order[1]] if len(order) > 1 and ds[order[1]] < 9e9 else 1.0
    res = {'syl': best, 'conf': round(float(conf), 3), 'd': [round(float(x), 3) for x in ds]}
    cache[key] = res
    return res


def load_cache():
    try:
        return json.load(open(CACHE, encoding='utf-8'))
    except Exception:
        return {}


def save_cache(c):
    json.dump(c, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    voice = 'ru-RU-SvetlanaNeural'
    if args[:1] == ['--voice']:
        voice, args = args[1], args[2:]
    cache = load_cache()
    for w in args:
        r = voice_stress(w.lower(), voice, cache)
        if r is None:
            print(w, 'не озвучилось'); continue
        p = vowel_pos(w.lower())[r['syl']]
        print(f"{w}: голос ставит на «{w[p]}» → {w[:p]}{w[p].upper()}{w[p+1:]}  уверенность {r['conf']}  {r['d']}")
    save_cache(cache)
