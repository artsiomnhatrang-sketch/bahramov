"""Озвучка голосом Silero (локально, бесплатно). Ударение «+» перед гласной выполняется всегда.
  echo '{"speaker":"aidar","items":["Текст с удар+ением", ...],"out":["/путь/s0.wav", ...]}' | python3 silero_tts.py
Голоса: aidar, eugene (мужские), baya, xenia, kseniya (женские). Модель v5_ru, кэш ~/.cache/torch/hub.
"""
import json, os, sys, warnings
warnings.filterwarnings('ignore')
import torch, soundfile as sf

job = json.load(sys.stdin)
m, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language='ru',
                      speaker='v5_ru', trust_repo=True, verbose=False)
for text, out in zip(job['items'], job['out']):
    # put_accent/put_yo выключены: ударения уже расставлены и проверены udarenia.py
    a = m.apply_tts(text=text, speaker=job['speaker'], sample_rate=48000, put_accent=False, put_yo=False)
    sf.write(out, a.numpy(), 48000)
sys.stdout.flush(); os._exit(0)
