"""Сверка озвучки с текстом: Whisper распознаёт каждую сцену, слова сравниваются с исходником.
Ловит сбои голоса (лишние звуки, «и краткое», проглоченные слова). Ударение на слух не проверяет:
за него отвечает udarenia.py (омографы подтверждаются вручную).
  python3 sverka.py <папка .work/ролик>   → печатает расхождения, выход 4 если они есть
"""
import json, os, re, sys, difflib, subprocess, tempfile

# числа и порядковые приводим к цифре: Whisper пишет «шаг 3» вместо «шаг третий»
NUM = {w: d for d, ws in {'1': 'один первый первая', '2': 'два второй вторая', '3': 'три третий третья',
       '4': 'четыре четвертый четвертая', '5': 'пять пятый', '10': 'десять десятый', '100': 'сто'}.items() for w in ws.split()}
def words(t):
    t = t.lower().replace('ё', 'е').replace('+', '').replace('\u0301', '').replace('%', ' процентов')
    t = t.replace('instagram', 'инстаграм').replace('telegram', 'телеграм')
    return [NUM.get(w, w) for w in re.findall(r'[а-яa-z0-9]+', t)]

work = sys.argv[1]
src = json.load(open(os.path.join(work, 'scenes.json')))
out = tempfile.mkdtemp()
wavs = [os.path.join(work, f's{i}.wav') for i in range(len(src))]
subprocess.run(['whisper', *wavs, '--model', 'small', '--language', 'ru', '--output_format', 'txt',
                '--fp16', 'False', '--output_dir', out], capture_output=True)
bad = 0
for i, say in enumerate(src):
    heard = open(os.path.join(out, f's{i}.txt'), encoding='utf-8').read()
    a, b = words(say), words(heard)
    sm = difflib.SequenceMatcher(None, a, b)
    diff = [(' '.join(a[i1:i2]), ' '.join(b[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
    # Whisper сам путает окончания безударных слогов: мелочь в 1–2 буквы не считаем
    diff = [d for d in diff if difflib.SequenceMatcher(None, *d).ratio() < 0.75]
    if diff:
        bad += 1
        print(f'сцена {i}: «{say}»\n   услышано: «{heard.strip()}»\n   расхождения: {diff}')
print('сверка голоса: чисто' if not bad else f'сверка голоса: расхождений в {bad} сценах')
sys.exit(4 if bad else 0)
