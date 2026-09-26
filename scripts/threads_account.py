# -*- coding: utf-8 -*-
"""
Какой аккаунт Threads обслуживает скрипт.

По умолчанию — @bahram.av (разбаны): ключи THREADS_* в .env, журналы в threads/.
Второй аккаунт @bahramovartem (AI-агенты и трафик) включается ключом
`--account ai` или переменной THREADS_ACCOUNT=ai: ключи THREADS_AI_* в .env,
журналы в threads/ai/. Скрипты внутри всё равно читают THREADS_ACCESS_TOKEN
и THREADS_USER_ID — подмена делается здесь, в одном месте.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pick():
    if "--account" in sys.argv:
        i = sys.argv.index("--account")
        if i + 1 < len(sys.argv):
            os.environ["THREADS_ACCOUNT"] = sys.argv[i + 1]
            del sys.argv[i:i + 2]
    return os.environ.get("THREADS_ACCOUNT", "").strip().lower()


ACCOUNT = _pick()
PREFIX = "THREADS_%s_" % ACCOUNT.upper() if ACCOUNT else "THREADS_"
DATA = os.path.join(ROOT, "threads", ACCOUNT) if ACCOUNT else os.path.join(ROOT, "threads")
if ACCOUNT:
    os.makedirs(DATA, exist_ok=True)


def remap(env):
    """THREADS_AI_ACCESS_TOKEN -> THREADS_ACCESS_TOKEN для выбранного аккаунта."""
    if not ACCOUNT:
        return env
    for k in [k for k in env if k.startswith(PREFIX)]:
        env["THREADS_" + k[len(PREFIX):]] = env[k]
    if PREFIX + "ACCESS_TOKEN" not in env:
        # без своего токена нельзя молча работать от имени первого аккаунта
        env.pop("THREADS_ACCESS_TOKEN", None)
        env.pop("THREADS_USER_ID", None)
    return env
