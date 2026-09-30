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

# Два аккаунта Threads на одной теме (с 30.09.2026): вставляемый текст не должен
# повторять ни один уже отправленный ответ любого из аккаунтов. Реестр ведёт
# scripts/threads-uniq.py sync. Сравниваем самую длинную строку внутри JS.
if name.endswith("__javascript_tool") and text:
    lits = re.findall(r"'((?:[^'\\]|\\.){60,})'|\"((?:[^\"\\]|\\.){60,})\"|`((?:[^`\\]|\\.){60,})`", text)
    cands = [x for t in lits for x in t if x and re.search(r"[а-яА-Я]", x)]
    if cands:
        body = max(cands, key=len)
        try:
            import importlib.util, os
            root = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sp = importlib.util.spec_from_file_location("tu", os.path.join(root, "scripts", "threads-uniq.py"))
            tu = importlib.util.module_from_spec(sp); sp.loader.exec_module(tu)
            for r in tu.load_reg():
                if len(tu.norm(r["text"])) >= 40 and tu.sim(body, r["text"]) >= tu.SIM_OWN:
                    print("threads-uniq: текст почти повторяет уже отправленный ответ %s: %s... "
                          "Написать заново под этого человека и прогнать "
                          "python3 scripts/threads-uniq.py check." % (tu.NAMES.get(r["account"], "?"), r["text"][:80]),
                          file=sys.stderr)
                    sys.exit(2)
        except SystemExit:
            raise
        except Exception:
            pass  # сторож не должен ломать браузер, если реестра нет
