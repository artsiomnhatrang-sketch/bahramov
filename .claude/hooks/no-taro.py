#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreToolUse-хук: в проекте bahramov нет таро.

08.10.2026 Артём: в этом проекте только разблокировки, взломы, восстановление
аккаунтов и автоматизация из базы знаний; ролики и посты - только в каналы
@bahramovai (YouTube), @bahram.av (TikTok), bahramovai (Дзен). Таро «Карты скажут»
(kartyskazhut, @taroitochkabot) - отдельный проект ~/Developer/apps/taro со своими
каналами, оттуда сюда ничего не берём и туда отсюда ничего не грузим.

Ловит: переход браузера на адреса таро и загрузку файлов из папок таро.
Разовое разрешение - файл .taro-ok в корне проекта (в git не идёт), удалить после задачи.
Код выхода 2 = вызов отменён, причина уходит ассистенту.
"""
import json
import os
import re
import sys
import unicodedata

TARO_URL = re.compile(r"kartyskazhut|taroitochkabot|карты\s*скажут", re.I)
TARO_PATH = re.compile(r"/apps/taro/|/Downloads/Таро/|/Загрузки/Таро/", re.I)
JS_NAV = re.compile(r"location|window\.open|href\s*=", re.I)

root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
if os.path.exists(os.path.join(root, ".taro-ok")):
    sys.exit(0)

try:
    d = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
name = d.get("tool_name", "")
inp = d.get("tool_input", {}) or {}


def strings(obj, key=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v, key)
    elif isinstance(obj, str):
        yield key, unicodedata.normalize("NFC", obj)


hit = None
for key, s in strings(inp):
    if key in ("url", "text") or name.endswith(("navigate", "tabs_create_mcp", "preview_start")):
        if key == "text" and not (name.endswith("javascript_tool") or JS_NAV.search(s)):
            continue
        if TARO_URL.search(s) and (key == "url" or JS_NAV.search(s)):
            hit = s[:120]
            break
    if TARO_PATH.search(s):
        hit = s[:120]
        break

if hit:
    print("no-taro: в проекте bahramov только разблокировки и автоматизация, таро - отдельный "
          "проект ~/Developer/apps/taro (решение Артёма 08.10.2026). Каналы здесь: YouTube @bahramovai, "
          "TikTok @bahram.av, Дзен bahramovai. Если открылся канал таро - уйти на свой, ничего не "
          "загружать. Отменено: %s" % hit, file=sys.stderr)
    sys.exit(2)
