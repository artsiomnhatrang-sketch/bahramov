#!/usr/bin/env bash
# Отдаёт Claude Code стартовый контекст проекта при открытии нового чата.
# Вызывается автоматически хуком SessionStart из .claude/settings.json.
# Печатает JSON: {"hookSpecificOutput":{"hookEventName":"SessionStart",
#                 "additionalContext":"..."}}
#
# Правило: скрипт НИКОГДА не должен падать и не должен висеть — если что-то
# пошло не так, лучше отдать пустой контекст, чем сломать старт сессии.
# Поэтому: без set -e, все git-вызовы с фолбэком, вывод строго один JSON.
#
# ВАЖНО: ничего не печатать в stdout напрямую — только через add(),
# иначе JSON будет невалидным и хук молча перестанет работать.

set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 0

CTX=""
add() { CTX="${CTX}$1"$'\n'; }
# добавить многострочный текст построчно
add_lines() { while IFS= read -r __l; do CTX="${CTX}${__l}"$'\n'; done <<< "$1"; }

add "# Контекст проекта bahramovai.com (подан автоматически при старте сессии)"
add ""
add "Это состояние на момент открытия чата. Артёму НЕ нужно пересказывать историю"
add "прошлых сессий — она уже здесь. STATUS.md и CLAUDE.md читать только если"
add "нужны детали глубже этой сводки."
add ""

# --- 1. Где остановились ----------------------------------------------------
if [ -f CONTEXT-NOW.md ]; then
  add_lines "$(cat CONTEXT-NOW.md)"
  add ""
fi

# --- 2. Фактическое состояние репозитория ----------------------------------
add "## Репозиторий сейчас (факт, а не запись в документе)"
add ""
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
DIRTY="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
if [ "${DIRTY:-0}" = "0" ]; then
  add "- Ветка \`$BRANCH\`, рабочая копия чистая, всё закоммичено."
else
  add "- Ветка \`$BRANCH\`, **незакоммиченных файлов: $DIRTY** — разобраться, что это, прежде чем браться за новое:"
  add_lines "$(git status --short 2>/dev/null | head -10 | sed 's/^/  - /')"
fi

AHEAD="$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)"
if [ "${AHEAD:-0}" != "0" ]; then
  add "- **Не запушено коммитов: $AHEAD.**"
fi

add "- Последние коммиты:"
add_lines "$(git log --oneline -5 2>/dev/null | sed 's/^/  - /')"
add ""

ARTICLES="$(ls blog/*.html 2>/dev/null | grep -v -e 'blog/index.html' -e 'usloviya-okazaniya-uslug' | wc -l | tr -d ' ')"
add "- Статей в blog/: ${ARTICLES:-?} (без листинга и юридической страницы)."
add ""

# --- 3. Постоянные правила --------------------------------------------------
add "## Правила, которые действуют всегда (Артёму не нужно их повторять)"
add ""
add "1. **Артём не работает с терминалом.** Команды выполнять за него, а не выдавать для копирования."
add "2. **«Всё ок?» = запустить \`./scripts/preflight.sh\`**, а не пересказывать документы."
add "3. **Перед пушем:** preflight -> показать дифф -> дождаться одобрения. \`publish-article.sh\` Артём запускает сам."
add "4. **Перед новой статьёй:** \`./scripts/preflight.sh --tema \"...\"\`. Тема занята -> усиливать существующую статью, а не плодить новую."
add "5. **Тон статей — нейтральный новостной.** Без разделов «правда или домысел» и разоблачений слухов."
add "6. **Не вырезать разделы из опубликованных статей молча** — показать владельцу и дать варианты."
add "7. **Все статьи — на «вы».** Не выдумывать цифры и названия систем Meta."
add "8. **Главный канал трафика — Яндекс.** Эффект правок мерить в Вебмастере (\`scripts/yandex-stats.py\`), не в Google."
add "9. **В конце сессии** — скилл \`/bahramovai-finish\`: обновит контекст, прогонит проверки, закоммитит и запушит."
add ""
add "Скиллы проекта: \`/bahramovai-finish\` (закрыть сессию), \`/bahramovai-ship\` (проверить и запушить правку),"
add "\`/bahramovai-seo\` (снять позиции в Яндексе и предложить план), \`/bahramovai-article\` (новая статья)."

python3 -c '
import json, sys
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": sys.argv[1],
    }
}, ensure_ascii=False))
' "$CTX" 2>/dev/null || echo '{}'
