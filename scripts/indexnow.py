#!/usr/bin/env python3
"""Отправка адресов в IndexNow (Bing, Яндекс и другие поисковики протокола).

Без аргументов - все адреса из sitemap.xml. С аргументами - только указанные.
  python3 scripts/indexnow.py
  python3 scripts/indexnow.py https://bahramovai.com/blog/x.html
  python3 scripts/indexnow.py --changed   # html, изменённые в последнем коммите

Ключ лежит в корне сайта: /<KEY>.txt, содержимое файла = сам ключ.
Ручная отправка в Bing Webmaster ограничена 10 адресами в сутки, IndexNow - нет.
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "bahramovai.com"
KEY = "560813b0a0ad84694ee5212aed63e657"
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>(.*?)</loc>", xml)


def changed_urls():
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD", "--", "*.html"],
        cwd=ROOT, capture_output=True, text=True).stdout.split()
    known = set(sitemap_urls())
    urls = []
    for f in out:
        u = f"https://{HOST}/{f}"
        if f.endswith("index.html"):
            u = u[: -len("index.html")]
        if u in known:
            urls.append(u)
    return urls


def main():
    args = sys.argv[1:]
    if args == ["--changed"]:
        urls = changed_urls()
    elif args:
        urls = args
    else:
        urls = sitemap_urls()
    if not urls:
        print("Нечего отправлять")
        return
    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls,
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: HTTP {r.status}, отправлено {len(urls)} адресов")
    except urllib.error.HTTPError as e:
        print(f"IndexNow: HTTP {e.code} {e.read().decode(errors='replace')[:300]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
