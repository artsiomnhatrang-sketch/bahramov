#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreToolUse-хук: работа в Threads остановлена полностью.

08.10.2026 Артём: «останови полностью работу тредс». До этого 07.10 отключили
Facebook и @bahram.av, 08.10 - @bahramovartem, оба за мошенничество, хотя
призывов в директ в ответах уже не было. Решение: не ходим в threads.com
ни браузером, ни через API, ни скриптами. Ни ответов, ни поиска, ни замеров.

Снять запрет может только Артём в чате: тогда создаётся файл .threads-ok
в корне проекта (в git не идёт) и удаляется сразу после задачи.

Ловит: переход браузера на threads.com / threads.net, JS с location или
window.open на threads, Bash с запуском scripts/threads-*.py или curl
на graph.threads.net. Код выхода 2 = вызов отменён, причина уходит ассистенту.
"""
import json
import os
import re
import sys

TH = re.compile(r"(^|[/.@\s\"'=])(?:[a-z0-9-]+\.)?threads\.(?:com|net)", re.I)
JS_NAV = re.compile(r"location|window\.open|href\s*=", re.I)
BASH_BAD = re.compile(
    r"(^|[;&|]\s*|\bpython3?\s+)(\./)?\S*threads[-_][a-z-]+\.py"
    r"|\b(curl|wget|httpie)\b[^|;&]*threads\.(com|net)"
    r"|\bopen\s+(-a\s+\S+\s+)?['\"]?https?://\S*threads\.(com|net)",
    re.I,
)

root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
if os.path.exists(os.path.join(root, ".threads-ok")):
    sys.exit(0)

d = json.load(sys.stdin)
name = d.get("tool_name", "")
inp = d.get("tool_input", {}) or {}


def urls(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "url" and isinstance(v, str):
                yield v
            else:
                yield from urls(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from urls(v)


def js_texts(obj, tool):
    if isinstance(obj, dict):
        if tool.endswith("javascript_tool") and isinstance(obj.get("text"), str):
            yield obj["text"]
        if obj.get("name", "").endswith("javascript_tool") and isinstance(obj.get("input"), dict):
            t = obj["input"].get("text")
            if isinstance(t, str):
                yield t
        for v in obj.values():
            if isinstance(v, (dict, list)):
                yield from js_texts(v, "")
    elif isinstance(obj, list):
        for v in obj:
            yield from js_texts(v, "")


hit = None
if name == "Bash":
    cmd = inp.get("command", "")
    if BASH_BAD.search(cmd):
        hit = cmd[:120]
else:
    for u in urls(inp):
        if TH.search(u):
            hit = u
            break
    if not hit:
        for js in js_texts(inp, name):
            if JS_NAV.search(js) and TH.search(js):
                hit = js[:120]
                break

if hit:
    print("no-threads: работа в Threads остановлена полностью (решение Артёма 08.10.2026). "
          "Ни ответов, ни поиска, ни замеров, ни скриптов. Снять запрет может только он. "
          "Отменено: %s" % hit, file=sys.stderr)
    sys.exit(2)
