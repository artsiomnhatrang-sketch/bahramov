"""Время каждого слова для субтитров по слову (монтаж v2, 04.10).
Whisper (small, word_timestamps) слушает каждую сцену; его слова сопоставляются с текстом сценария,
на экран идут слова сценария (без «+»), время — из Whisper. Несопоставленные — между соседями.
  python3 slova.py <папка .work/ролик>  (stdin: JSON список текстов субтитров по сценам) → words.json
"""
import json, os, re, sys, difflib, subprocess, tempfile
import whisper

PAD = 0.5  # тишина перед сценой: без неё Whisper теряет первое слово (как в sverka.py)


def norm(w):
    w = w.lower().replace('ё', 'е')
    w = w.replace('instagram', 'инстаграм').replace('telegram', 'телеграм').replace('whatsapp', 'ватсап')
    return re.sub(r'[^а-яa-z0-9]', '', w)


work = sys.argv[1]
texts = json.load(sys.stdin)
model = whisper.load_model('small')
tmp = tempfile.mkdtemp()
out = []
for i, text in enumerate(texts):
    src = os.path.join(work, f's{i}.wav')
    w = os.path.join(tmp, f's{i}.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-t', str(PAD), '-i', 'anullsrc=r=16000:cl=mono',
                    '-i', src, '-filter_complex', '[1:a]aresample=16000,aformat=channel_layouts=mono[b];[0:a][b]concat=n=2:v=0:a=1', w], check=True)
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src]))
    r = model.transcribe(w, language='ru', word_timestamps=True, fp16=False)
    heard = [(x['word'], max(0.0, x['start'] - PAD)) for seg in r['segments'] for x in seg.get('words', [])]
    shown = [x for x in text.replace('+', '').split() if norm(x)]
    a, b = [norm(x) for x in shown], [norm(x[0]) for x in heard]
    times = [None] * len(shown)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = heard[blk.b + k][1]
    # дыры: равномерно между известными соседями
    known = [(-1, 0.0)] + [(k, t) for k, t in enumerate(times) if t is not None] + [(len(shown), dur)]
    for (k0, t0), (k1, t1) in zip(known, known[1:]):
        for k in range(k0 + 1, k1):
            times[k] = t0 + (t1 - t0) * (k - k0) / (k1 - k0)
    # время не должно идти назад
    for k in range(1, len(times)):
        times[k] = max(times[k], times[k - 1] + 0.05)
    words = [{'w': re.sub(r'[.,:;!?«»"]+$', '', x).strip('«»"'), 's': round(t, 3)} for x, t in zip(shown, times)]
    matched = sum(1 for k in range(len(a)) if a[k] in b)
    print(f'сцена {i}: слов {len(shown)}, узнано {matched}', file=sys.stderr)
    out.append(words)
json.dump(out, open(os.path.join(work, 'words.json'), 'w'), ensure_ascii=False)
