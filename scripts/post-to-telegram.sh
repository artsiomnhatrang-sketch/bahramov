#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=../.env
  set -a; source "$ENV_FILE"; set +a
fi

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "Ошибка: TELEGRAM_BOT_TOKEN не задан (проверьте .env)" >&2
  exit 1
fi
if [[ -z "${TELEGRAM_CHANNEL:-}" ]]; then
  echo "Ошибка: TELEGRAM_CHANNEL не задан (проверьте .env)" >&2
  exit 1
fi

POST_FILE="${1:-}"
if [[ -z "$POST_FILE" ]]; then
  echo "Использование: $0 <путь_к_файлу_с_текстом>" >&2
  exit 1
fi
if [[ ! -f "$POST_FILE" ]]; then
  echo "Ошибка: файл не найден: $POST_FILE" >&2
  exit 1
fi

TEXT="$(cat "$POST_FILE")"
if [[ -z "$TEXT" ]]; then
  echo "Ошибка: файл с текстом пуст" >&2
  exit 1
fi

RESPONSE="$(curl -s -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  --data-binary "$(jq -n \
    --arg chat_id "$TELEGRAM_CHANNEL" \
    --arg text "$TEXT" \
    '{chat_id: $chat_id, text: $text, parse_mode: "HTML", disable_web_page_preview: false}'
  )"
)"

OK="$(echo "$RESPONSE" | jq -r '.ok')"
if [[ "$OK" != "true" ]]; then
  DESCRIPTION="$(echo "$RESPONSE" | jq -r '.description // "неизвестная ошибка"')"
  echo "Ошибка Telegram API: $DESCRIPTION" >&2
  exit 1
fi

echo "Пост отправлен в $TELEGRAM_CHANNEL"
