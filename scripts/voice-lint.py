#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фильтр текста наружу: длинное тире, кавычки, финальная точка, машинные обороты.

Правила - из скилла /human и threads/COMMENT-RULES.md. Раньше они жили только
в инструкциях, и 28.09.2026 ответы в Threads всё равно ушли с длинным тире.
Теперь это проверка кодом: threads-replies.py, threads-post.py и
threads-chain.py вызывают её перед отправкой и отказываются публиковать.

  python3 scripts/voice-lint.py "текст"        # проверить строку
  python3 scripts/voice-lint.py --file a.txt   # проверить файл
  echo "текст" | python3 scripts/voice-lint.py # из stdin
  python3 scripts/voice-lint.py --fix "текст"  # вернуть исправленный текст

Выход 0 - чисто, 1 - есть нарушения.
"""
import re
import sys

# (шаблон, что не так) - жёсткие, публикацию блокируют
HARD = [
    (r"[—–]", "длинное тире: писать -"),
    (r"[«»“”„]", "кавычки: не ставить"),
    (r"\"", "прямые кавычки: не ставить"),
    (r"…", "многоточие одним символом"),
]

# машинные обороты - тоже блокируют, их у Артёма нет
PHRASES = [
    "важно отметить", "стоит отметить", "давайте разберёмся", "давайте разберемся",
    "в современном мире", "ключевой момент", "важно понимать", "не секрет, что",
    "в заключение", "таким образом", "кроме того", "является", "позволяет вам",
    "отличный вопрос", "хороший вопрос",
]


def check(text):
    problems = []
    for pat, why in HARD:
        for m in re.finditer(pat, text):
            s = max(0, m.start() - 20)
            problems.append("%s: ...%s..." % (why, text[s:m.end() + 20].replace("\n", " ")))
    low = text.lower()
    for ph in PHRASES:
        if ph in low:
            problems.append("машинный оборот: %s" % ph)
    last = text.rstrip()
    if last.endswith(".") and not last.endswith(".."):
        problems.append("точка в конце последней строки: убрать")
    return problems


def fix(text):
    text = re.sub(r"\s*[—–]\s*", " - ", text)
    text = re.sub(r"[«»“”„\"]", "", text)
    text = text.replace("…", "...")
    text = text.rstrip()
    if text.endswith(".") and not text.endswith(".."):
        text = text[:-1]
    return text


def guard(text):
    """Для импорта из скриптов публикации: при нарушении печатает и выходит с кодом 1."""
    problems = check(text)
    if problems:
        print("СТОП voice-lint: текст не в голосе Артёма, публикация отменена", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        sys.exit(1)


def main():
    args = sys.argv[1:]
    do_fix = "--fix" in args
    args = [a for a in args if a != "--fix"]
    if args[:1] == ["--file"]:
        text = open(args[1], encoding="utf-8").read()
    elif args:
        text = " ".join(args)
    else:
        text = sys.stdin.read()
    if do_fix:
        print(fix(text))
        return
    problems = check(text)
    if not problems:
        print("ok")
        return
    for p in problems:
        print("- " + p)
    sys.exit(1)


if __name__ == "__main__":
    main()
