#!/usr/bin/env python3
"""Расшифровка ролика YouTube по ссылке — вместо ручного NotebookLM/Gemini Notebook.

    python3 scripts/yt-transcript.py "https://youtu.be/XXXX"
    python3 scripts/yt-transcript.py "https://youtu.be/XXXX" --force   # скачать заново

Берёт субтитры через yt-dlp (ручные, если есть, иначе автоматические на языке
ролика), чистит от повторов и тегов и кладёт в .transcripts/<id>-<слаг>.md
с шапкой (название, канал, длительность, откуда текст) и метками времени
раз в минуту. Папка .transcripts/ в .gitignore: чужой текст в публичный
репозиторий и на сайт не уходит.

Выход 0 — путь к файлу в последней строке. Выход 2 — YouTube не отдал
субтитры (нет их у ролика или временная блокировка): тогда расшифровку
читать через Chrome, порядок в скилле bahramovai-youtube.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / ".transcripts"
PARAGRAPH_SEC = 60


def fail(msg):
    print("ОШИБКА: " + msg, file=sys.stderr)
    sys.exit(2)


def run_ytdlp(args):
    try:
        return subprocess.run(["yt-dlp", "--no-warnings"] + args,
                              capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        fail("yt-dlp не установлен: pip3 install -U yt-dlp")
    except subprocess.TimeoutExpired:
        fail("yt-dlp не ответил за 3 минуты")


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    return re.sub(r"[\s_-]+", "-", text).strip("-")[:60] or "video"


def pick_track(info):
    """Лучшая дорожка: ручные на языке ролика > ручные ru/en > авто на языке ролика > авто ru/en."""
    lang = (info.get("language") or "").split("-")[0]
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    manual = {k: v for k, v in manual.items() if k != "live_chat"}

    def find(pool, codes):
        for code in codes:
            if code and code in pool:
                return code
        return None

    prefer = [lang, "ru", "en"]
    code = find(manual, prefer) or find(manual, list(manual))
    if code:
        return code, "ручные субтитры"
    # у авто-дорожек оригинал помечен -orig, остальные — машинный перевод
    code = find(auto, [lang + "-orig" if lang else "", lang] +
                [c for c in auto if c.endswith("-orig")] + ["ru", "en"])
    if code:
        return code, "автоматические субтитры YouTube (возможны ошибки в именах и терминах)"
    return None, None


def parse_json3(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        text = "".join(s.get("utf8", "") for s in segs).replace("\n", " ").strip()
        if text:
            out.append((ev.get("tStartMs", 0) / 1000.0, text))
    return out


def parse_vtt(path):
    out, start, last = [], 0.0, None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\d+):(\d\d):(\d\d)[.,](\d+)\s+-->", line)
        if m:
            h, mnt, s, _ = m.groups()
            start = int(h) * 3600 + int(mnt) * 60 + int(s)
            continue
        if not line.strip() or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        text = re.sub(r"<[^>]+>", "", line).strip()
        # автосубтитры в vtt «прокручиваются»: строка повторяется в следующем блоке
        if text and text != last:
            out.append((start, text))
            last = text
    return out


def to_paragraphs(chunks):
    paras, cur, cur_start = [], [], None
    for start, text in chunks:
        if cur_start is None:
            cur_start = start
        if start - cur_start >= PARAGRAPH_SEC and cur:
            paras.append((cur_start, " ".join(cur)))
            cur, cur_start = [], start
        cur.append(text)
    if cur:
        paras.append((cur_start, " ".join(cur)))
    return paras


def ts(sec):
    sec = int(sec)
    h, rest = divmod(sec, 3600)
    return "%d:%02d:%02d" % (h, rest // 60, rest % 60) if h else "%d:%02d" % (rest // 60, rest % 60)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("url")
    ap.add_argument("--force", action="store_true", help="скачать заново, даже если файл есть")
    args = ap.parse_args()

    meta = run_ytdlp(["-J", "--skip-download", args.url])
    if meta.returncode != 0:
        fail("YouTube не отдал данные ролика:\n" + meta.stderr.strip()[-600:])
    info = json.loads(meta.stdout)
    vid = info["id"]

    OUT_DIR.mkdir(exist_ok=True)
    existing = sorted(OUT_DIR.glob(vid + "-*.md"))
    if existing and not args.force:
        print("Уже скачано раньше:")
        print(existing[0])
        return

    code, kind = pick_track(info)
    if not code:
        fail("у ролика нет субтитров — ни ручных, ни автоматических")

    with tempfile.TemporaryDirectory() as tmp:
        res = run_ytdlp(["--skip-download", "--write-subs", "--write-auto-subs",
                         "--sub-langs", code, "--sub-format", "json3/vtt/best",
                         "-o", str(Path(tmp) / "sub"), args.url])
        files = list(Path(tmp).glob("sub.*"))
        if res.returncode != 0 or not files:
            fail("субтитры не скачались (YouTube мог временно ограничить запросы):\n"
                 + res.stderr.strip()[-600:])
        f = files[0]
        chunks = parse_json3(f) if f.suffix == ".json3" else parse_vtt(f)

    if not chunks:
        fail("файл субтитров пустой")

    paras = to_paragraphs(chunks)
    words = sum(len(t.split()) for _, t in paras)
    up = info.get("upload_date") or ""
    head = [
        "# " + info.get("title", vid),
        "",
        "- Канал: " + (info.get("channel") or info.get("uploader") or "?"),
        "- Ссылка: https://www.youtube.com/watch?v=" + vid,
        "- Опубликован: " + ("%s.%s.%s" % (up[6:8], up[4:6], up[:4]) if len(up) == 8 else "?"),
        "- Длительность: " + ts(info.get("duration") or 0),
        "- Текст: %s, язык %s, %d слов" % (kind, code, words),
        "",
        "Метки [мм:сс] — начало абзаца, по ним можно открыть ролик: &t=<секунды>.",
        "",
    ]
    body = ["[%s] %s\n" % (ts(s), t) for s, t in paras]

    out = OUT_DIR / ("%s-%s.md" % (vid, slugify(info.get("title", ""))))
    out.write_text("\n".join(head) + "\n" + "\n".join(body), encoding="utf-8")
    print("%s | %s | %d слов, %d абзацев" % (info.get("title", vid), kind, words, len(paras)))
    print(out)


if __name__ == "__main__":
    main()
