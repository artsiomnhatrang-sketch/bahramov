#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreToolUse-хук: не даёт ввести в браузер текст с длинным тире или кавычками.

Правило голоса Артёма (скилл /human, threads/COMMENT-RULES.md) держалось
только на инструкциях, и 28.09.2026 ответы в Threads ушли с тире.
Хук ловит ввод текста (computer type, form_input) и JS, который вставляет
текст в поле (paste / insertText). JS, который только читает страницу, не трогает.
Код выхода 2 = вызов отменён, причина уходит ассистенту.
"""
import json
import re
import sys

BAD = re.compile(r"[—–«»“”„]")
INSERT_JS = re.compile(r"ClipboardEvent|DataTransfer|insertText|\.textContent\s*=|\.innerText\s*=|\.value\s*=", re.I)

d = json.load(sys.stdin)
name = d.get("tool_name", "")
inp = d.get("tool_input", {}) or {}

text = ""
if name.endswith("__computer") and inp.get("action") == "type":
    text = inp.get("text", "")
elif name.endswith("__form_input"):
    text = str(inp.get("value", ""))
elif name.endswith("__javascript_tool"):
    js = inp.get("text", "")
    if INSERT_JS.search(js):
        text = js

m = BAD.search(text)
if m:
    s = max(0, m.start() - 30)
    print("voice-guard: в тексте наружу длинное тире или кавычки (%r). "
          "Переписать по threads/COMMENT-RULES.md и проверить "
          "python3 scripts/voice-lint.py, потом вводить заново. Фрагмент: ...%s..."
          % (m.group(), text[s:m.end() + 30]), file=sys.stderr)
    sys.exit(2)
