"""Ударения для озвучки: текст → тот же текст с ударением (знак U+0301 после ударной гласной).
Порядок: свой словарь исправлений (slovar.txt, правит Артём/Claude) → ruaccent (нейросеть, различает
омографы по смыслу). Слова, где модель не уверена, выводятся в stderr «на проверку».
  python3 udarenia.py "текст"            → печатает текст с ударениями
  python3 udarenia.py --json < in.json   → {"items":[...]} → те же строки с ударениями
"""
import json, re, sys, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ACUTE = '́'
VOWELS = 'аеёиоуыэюяАЕЁИОУЫЭЮЯ'

def load_slovar():
    d = {}
    for line in open(os.path.join(HERE, 'slovar.txt'), encoding='utf-8'):
        line = line.split('#')[0].strip()
        if '+' in line:
            d[line.replace('+', '').lower()] = line.lower()
    return d

_acc = None
def model():
    global _acc
    if _acc is None:
        import io, contextlib
        from ruaccent import RUAccent
        with contextlib.redirect_stdout(io.StringIO()):
            _acc = RUAccent()
            _acc.load(omograph_model_size='turbo3.1', use_dictionary=True, tiny_mode=False)
        # совместимость версий: модели ударений нужен token_type_ids
        sess = _acc.accent_model.session
        need = {i.name for i in sess.get_inputs()}
        run = sess.run
        def patched(out, feed, *a, **k):
            if 'token_type_ids' in need and 'token_type_ids' not in feed:
                feed = dict(feed, token_type_ids=np.zeros_like(feed['input_ids']))
            return run(out, feed, *a, **k)
        sess.run = patched
    return _acc

def plus_to_acute(t):
    # «+а» (формат ruaccent и словаря) → «а́»
    return re.sub(r'\+([' + VOWELS + '])', lambda m: m.group(1) + ACUTE, t)

def accent(text, slovar):
    out = model().process_all(text)
    # словарь сильнее модели: заменяем слова целиком, сохраняя регистр первой буквы
    def fix(m):
        w = m.group(0); key = w.replace('+', '').lower()
        if key in slovar:
            r = slovar[key]
            return r[0].upper() + r[1:] if w.replace('+', '')[:1].isupper() else r
        return w
    out = re.sub(r'[\w+]+', fix, out)
    # ё всегда ударная — знак не нужен
    out = re.sub(r'\+ё', 'ё', out).replace('+Ё', 'Ё')
    # в односложных словах ударение не ставим — голос от него спотыкается
    out = re.sub(r'[\w+]+', lambda m: m.group(0).replace('+', '') if sum(c in VOWELS for c in m.group(0)) < 2 else m.group(0), out)
    out = plus_to_acute(out)
    # знак ударения перед «й» ломает голос: «второ́й» читается как «второ и краткое» — убираем
    return re.sub(ACUTE + '(?=[йЙ])', '', out)

def unsure(text_acc):
    # слова из 2+ слогов без ударения — на ручную проверку
    res = []
    for w in re.findall(r'[\ẃ]+', text_acc):
        if ACUTE in w or 'ё' in w.lower():
            continue
        if sum(c in VOWELS for c in w) >= 2:
            res.append(w)
    return res

if __name__ == '__main__':
    slovar = load_slovar()
    if sys.argv[1:2] == ['--json']:
        items = json.load(sys.stdin)['items']
        res = [accent(t, slovar) for t in items]
        bad = sorted({w for r in res for w in unsure(r)})
        if bad:
            print('на проверку (нет ударения): ' + ', '.join(bad), file=sys.stderr)
        print(json.dumps({'items': res}, ensure_ascii=False))
    else:
        r = accent(' '.join(sys.argv[1:]), slovar)
        print(r)
        b = unsure(r)
        if b:
            print('на проверку: ' + ', '.join(b), file=sys.stderr)
