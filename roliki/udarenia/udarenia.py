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

def accent(text, slovar, report):
    """Знак ударения ставим ТОЛЬКО там, где голос сам может ошибиться:
    1) ручная пометка «+» прямо в тексте сцены (сильнее всего, учитывает смысл фразы);
    2) слово из slovar.txt (проверено вручную);
    3) омограф (у слова два ударения: пл+атите / плат+ите) — берём выбор ruaccent, но слово
       попадает в report['unsure'], и сборка остановится, пока ударение не подтвердят в slovar.txt
       или пометкой «+» в тексте.
    Остальные слова голос читает правильно сам, а лишний знак портит звук
    (проверено 02.10: «уведомле́ние» → «у ведом линии», «пода́йте» → «подойте»)."""
    m = model()
    # ruaccent не понимает наши «+», поэтому размечаем текст без них и возвращаем ручные пометки
    manual = {w.replace('+', '').lower(): w.lower() for w in re.findall(r'[\w+]+', text) if '+' in w}
    for w in manual.values():
        if not re.search(r'\+[' + VOWELS + ']', w):
            sys.exit(f'Пометка «{w}»: «+» ставится ПЕРЕД ударной гласной, например плат+ите')
    out = m.process_all(text.replace('+', ''))
    def fix(mt):
        w = mt.group(0); plain = w.replace('+', ''); key = plain.lower()
        if sum(c in VOWELS for c in plain) < 2:
            return plain  # односложные без знака
        if key in manual:
            r = manual[key]
        elif key in slovar:
            r = slovar[key]
        elif key in m.omographs:
            report['unsure'].setdefault(key, (w.lower(), m.omographs[key]))
            r = w.lower()
        else:
            return plain  # обычное слово — голос справится сам
        if '+' in r and re.search(r'\+[' + VOWELS + r'][йЙ]', r):
            report['noacc'].add(key)  # знак перед «й» ломает голос — оставляем без знака
            r = r.replace('+', '')
        r = r.replace('+ё', 'ё')
        return r[0].upper() + r[1:] if plain[:1].isupper() else r
    out = re.sub(r'[\w+]+', fix, out)
    return plus_to_acute(out)

if __name__ == '__main__':
    slovar = load_slovar()
    report = {'unsure': {}, 'noacc': set()}
    if sys.argv[1:2] == ['--json']:
        items = json.load(sys.stdin)['items']
        res = [accent(t, slovar, report) for t in items]
        print(json.dumps({'items': res}, ensure_ascii=False))
    else:
        print(accent(' '.join(a for a in sys.argv[1:] if a != '--strict'), slovar, report))
    if report['noacc']:
        print('без знака (перед «й» нельзя), голос ставит сам: ' + ', '.join(sorted(report['noacc'])), file=sys.stderr)
    if report['unsure']:
        print('\nОМОГРАФЫ — ударение не подтверждено. Проверьте по смыслу фразы и впишите в slovar.txt'
              ' или пометьте «+» в тексте сцены:', file=sys.stderr)
        for k, (got, variants) in sorted(report['unsure'].items()):
            print(f'  {k}: модель выбрала {got}; варианты {", ".join(variants)}', file=sys.stderr)
        if '--strict' in sys.argv:
            sys.exit(3)
