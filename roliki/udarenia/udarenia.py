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

# служебные односложные слова — без ударения (предлоги, союзы, частицы)
CLITICS = set('в во к ко с со у о об обо от ото из изо без до за на по под подо над про при для '
              'не ни и а но да же ли бы б то ль уж что чтоб'.split())

def accent(text, slovar, report, full=True):
    """full=True (голос Silero, по умолчанию): ударение «+» в КАЖДОМ слове из 2+ слогов, Silero
    выполняет его всегда. Источник: ручная «+» в тексте сцены → slovar.txt → словарь ruaccent
    (3 млн слов). Омографы (два ударения) и слова, которых нет в словаре, попадают в report
    и с --strict останавливают сборку, пока ударение не подтверждено вручную.
    full=False (старый режим edge-tts): знак только на омографы и slovar, без знака перед «й»."""
    m = model()
    manual = {w.replace('+', '').lower(): w.lower() for w in re.findall(r'[\w+]+', text) if '+' in w}
    for w in manual.values():
        if not re.search(r'\+[' + VOWELS + ']', w):
            sys.exit(f'Пометка «{w}»: «+» ставится ПЕРЕД ударной гласной, например плат+ите')
    out = m.process_all(text.replace('+', ''))
    def fix(mt):
        w = mt.group(0); plain = w.replace('+', ''); key = plain.lower()
        # ruaccent сам ставит ё («все» → «всё»); ручная пометка сильнее — ищем её и по написанию с «е»
        if key not in manual and key.replace('ё', 'е') in manual:
            key = key.replace('ё', 'е'); plain = plain.replace('ё', 'е').replace('Ё', 'Е')
        nv = sum(c in VOWELS for c in plain)
        if nv == 0:
            return plain
        if nv == 1:
            # Silero без «+» читает гласную как безударную («шаг» → «шъг»): односложным ставим знак,
            # кроме служебных слов, которые и в живой речи безударны
            if not full or key in CLITICS or key in manual:
                return manual.get(key, plain) if full else plain
            if 'ё' in key:
                return plain
            i = next(j for j, c in enumerate(plain) if c.lower() in VOWELS)
            return plain[:i] + '+' + plain[i:]
        if key in manual:
            r = manual[key]
        elif key in slovar:
            r = slovar[key]
        elif key in m.omographs:
            report['unsure'].setdefault(key, (w.lower(), m.omographs[key])); r = w.lower()
        elif key.replace('ё', 'е') in m.accents or 'ё' in key:
            if not full:
                return plain
            r = w.lower() if '+' in w or 'ё' in key else m.accents[key.replace('ё', 'е')]
        else:
            report['unknown'].add(key); r = w.lower()
        if not full and re.search(r'\+[' + VOWELS + r'][йЙ]', r):
            report['noacc'].add(key); r = r.replace('+', '')
        r = r.replace('+ё', 'ё')
        if full and '+' not in r and 'ё' not in r:
            report['unknown'].add(key)
        return r[0].upper() + r[1:] if plain[:1].isupper() else r
    out = re.sub(r'[\w+]+', fix, out)
    return out if full else plus_to_acute(out)

if __name__ == '__main__':
    slovar = load_slovar()
    report = {'unsure': {}, 'noacc': set(), 'unknown': set()}
    full = '--edge' not in sys.argv
    if sys.argv[1:2] == ['--json']:
        items = json.load(sys.stdin)['items']
        res = [accent(t, slovar, report, full) for t in items]
        print(json.dumps({'items': res}, ensure_ascii=False))
    else:
        print(accent(' '.join(a for a in sys.argv[1:] if not a.startswith('--')), slovar, report, full))
    if report['noacc']:
        print('без знака (перед «й» нельзя), голос ставит сам: ' + ', '.join(sorted(report['noacc'])), file=sys.stderr)
    if report['unsure']:
        print('\nОМОГРАФЫ — ударение не подтверждено. Проверьте по смыслу фразы и впишите в slovar.txt'
              ' или пометьте «+» в тексте сцены:', file=sys.stderr)
        for k, (got, variants) in sorted(report['unsure'].items()):
            print(f'  {k}: модель выбрала {got}; варианты {", ".join(variants)}', file=sys.stderr)
    if report['unknown']:
        print('\nНЕТ В СЛОВАРЕ — ударение неизвестно, впишите в slovar.txt: ' + ', '.join(sorted(report['unknown'])), file=sys.stderr)
    code = 3 if '--strict' in sys.argv and (report['unsure'] or report['unknown']) else 0
    # onnxruntime иногда падает при закрытии интерпретатора (recursive_mutex) — выходим сразу
    sys.stdout.flush(); sys.stderr.flush(); os._exit(code)
