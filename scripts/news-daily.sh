#!/usr/bin/env bash
# Ежедневный новостной цикл: собрать → отобрать → прислать в Telegram.
#
#   ./scripts/news-daily.sh            # полный цикл
#   ./scripts/news-daily.sh --dry-run  # всё то же, но дайджест не отправляется
#
# Что происходит:
#   1. news-collect.py тянет новости из RSS и веб-зеркал Telegram-каналов
#   2. агент news-editor отбирает 5 штук и пишет угол подачи под нишу
#   3. tg-digest.py присылает дайджест с кнопками
#
# После этого нужен работающий tg-watcher.py — он поймает нажатие кнопки.
# Публикацию в канал watcher делает только по отдельному подтверждению.

set -euo pipefail
cd "$(dirname "$0")/.."

DATE=$(date +%Y-%m-%d)
DRY=""
[ "${1:-}" = "--dry-run" ] && DRY="--dry-run"

echo "▶ 1/3 Собираю новости"
python3 scripts/news-collect.py --hours 36

echo
echo "▶ 2/3 Редактор отбирает темы"
# Статическая часть задания идёт первой, дата и пути — в хвосте:
# правило префикс-кэша, .claude/rules/prompt-caching.md
if ! printf '%s\n\n%s\n' \
  "Собери дайджест по правилам своей роли: прочитай сырьё за указанный день и запиши оба выходных файла — json и txt. Пути даны ниже." \
  "Дата: $DATE. Сырьё: .news/$DATE.json. Выход: .news/digest-$DATE.json и .news/digest-$DATE.txt" \
  | claude -p --agent news-editor --permission-mode acceptEdits \
      --allowedTools "Read Write WebSearch WebFetch" 2>&1 | tee /tmp/news-editor.log
then
  echo "✗ Редактор не отработал — подробности выше" >&2
  exit 1
fi

if grep -q "Failed to authenticate\|OAuth session expired" /tmp/news-editor.log; then
  echo >&2
  echo "✗ CLI claude не авторизован." >&2
  echo "  Открой Терминал, выполни 'claude', войди в аккаунт — и запусти снова." >&2
  exit 1
fi

if [ ! -f ".news/digest-$DATE.json" ]; then
  echo "✗ Редактор не создал .news/digest-$DATE.json" >&2
  exit 1
fi

echo
echo "▶ 3/3 Отправляю дайджест"
python3 scripts/tg-digest.py --date "$DATE" $DRY

echo
echo "Готово. Чтобы поймать нажатие кнопки, должен быть запущен watcher:"
echo "  python3 scripts/tg-watcher.py"
