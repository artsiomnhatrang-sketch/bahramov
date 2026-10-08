#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreToolUse-хук: Claude не заходит в Instagram без разрешения Артёма.

08.10.2026 Артём увидел попытки входа в свой Instagram: чаты открывали
instagram.com, чтобы сверить профиль и статус аккаунта. Решение Артёма:
в Instagram автоматически не заходить никогда, ни браузером, ни через API.
Threads (threads.com) можно. Разрешение даёт только Артём в чате, тогда
создаётся файл .instagram-ok в корне проекта (в git не идёт) и удаляется
сразу после задачи.

Ловит: переход браузера на instagram.com (navigate, preview_start,
tabs, browser_batch), JS с location/window.open на instagram.com,
Bash с instagram.com / graph.instagram.com или запуском instagram-stats.py.
Код выхода 2 = вызов отменён, причина уходит ассистенту.
"""
import json
import os
import re
import sys

IG = re.compile(r"(^|[/.@\s\"'=])(?:[a-z0-9-]+\.)?instagram\.com|instagr\.am", re.I)
JS_NAV = re.compile(r"location|window\.open|href\s*=", re.I)
BASH_BAD = re.compile(r"(^|[;&|]\s*|\bpython3?\s+)(\./)?\S*instagram-stats\.py|\b(curl|wget|open|http|httpie)\b[^|;&]*(instagram\.com|graph\.instagram)", re.I)

root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
if os.path.exists(os.path.join(root, ".instagram-ok")):
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
        if IG.search(u):
            hit = u
            break
    if not hit:
        for js in js_texts(inp, name):
            if JS_NAV.search(js) and IG.search(js):
                hit = js[:120]
                break

if hit:
    print("no-instagram: в Instagram без разрешения Артёма не заходим (решение 08.10.2026). "
          "Threads - только threads.com, статус аккаунта - по письмам Meta в Gmail. "
          "Отменено: %s" % hit, file=sys.stderr)
    sys.exit(2)
