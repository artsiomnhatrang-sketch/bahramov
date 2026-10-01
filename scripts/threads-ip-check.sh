#!/bin/zsh
# Проверка, не режет ли Threads наш IP (HTTP 429). Решение Артёма 02.10.2026:
# при 429 подход останавливается сразу, максимальная безопасность аккаунтов.
# Выход 0 - можно работать, 1 - 429 или сбой: стоп, в браузер не заходить.
code=$(curl -s -o /dev/null -m 15 -w "%{http_code}" \
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36" \
  https://www.threads.com/)
if [[ "$code" == "200" ]]; then
  echo "threads IP: ok ($code)"; exit 0
fi
echo "threads IP: СТОП ($code) - подход не начинать / прекратить, Артёму сказать сразу"; exit 1
