#!/usr/bin/env python3
"""Подбор дубля трудной фразы для клона голоса (09.10).

Клон иногда глотает «и», сливает слова («имя и» -> «имей», «три: спамбот» -> «трейспомбот»), и сверка Whisper
останавливает ролик. Этот скрипт делает N дублей того же текста (разное случайное зерно), обрабатывает их ровно
как render.mjs (срез тишины + цепочка STUDIO) и прогоняет настоящей sverka.py. Прошедший дубль кладётся в кэш
сборки с правильным ключом - слова сценария не меняются, пересборка берёт его без новой озвучки.

  python3 udarenia/dubli.py --work .work/<ролик> --scene 4 [--n 6] [--put 2] [--also .work/<ролик>-ig]

Без --put: делает дубли и печатает, какие прошли. С --put K: кладёт дубль K в s<scene>.raw.wav (+ ключ) в --work
и в каждую папку --also. Текст берётся из <work>/udarenia.txt (строка сцены, со знаками +).
"""
import argparse, json, os, re, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.environ.get('ROLIKI_GOLOS_DIR', os.path.expanduser('~/Developer/golos-artem'))
# как в render.mjs: срез тишины и студийная цепочка клона
CUT = 'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.06'
STUDIO = (',aresample=48000,highpass=f=75,afftdn=nr=6:nf=-50,equalizer=f=160:t=q:w=1:g=1.5,'
          'equalizer=f=3200:t=q:w=1.4:g=1.5,deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2')

a = argparse.ArgumentParser()
a.add_argument('--work', required=True); a.add_argument('--scene', type=int, required=True)
a.add_argument('--n', type=int, default=6); a.add_argument('--put', type=int)
a.add_argument('--also', action='append', default=[]); a.add_argument('--seed', type=int, default=300)
o = a.parse_args()
text = open(os.path.join(o.work, 'udarenia.txt'), encoding='utf-8').read().split('\n')[o.scene]
d = os.path.join(o.work, f'dubli-s{o.scene}')
raws = [os.path.join(d, f'raw{k}.wav') for k in range(o.n)]

if o.put is None:
    os.makedirs(d, exist_ok=True)
    subprocess.run([os.path.join(G, '.venv', 'bin', 'python'), os.path.join(G, 'say.py')], text=True, check=True,
                   capture_output=True, input=json.dumps({'items': [text] * o.n, 'out': raws, 'seed': o.seed}))
    for k, r in enumerate(raws):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', r, '-af', CUT + STUDIO, os.path.join(d, f's{k}.wav')], check=True)
    json.dump([text] * o.n, open(os.path.join(d, 'scenes.json'), 'w'), ensure_ascii=False)
    res = subprocess.run(['python3', os.path.join(ROOT, 'udarenia', 'sverka.py'), d], capture_output=True, text=True).stdout
    bad = {int(m) for m in re.findall(r'^сцена (\d+):', res, re.M)}
    print(res.strip())
    print(f'«{text}»\nпрошли сверку: {[k for k in range(o.n) if k not in bad]} из {o.n}. Положить: --put K')
else:
    for w in [o.work, *o.also]:
        head = open(os.path.join(w, 's0.key'), encoding='utf-8').read().split('\n')[0]  # «голос|образец»
        shutil.copy(raws[o.put], os.path.join(w, f's{o.scene}.raw.wav'))
        open(os.path.join(w, f's{o.scene}.key'), 'w', encoding='utf-8').write(f'{head}\n{text}')
        print('положен дубль', o.put, '->', w, 'сцена', o.scene)
