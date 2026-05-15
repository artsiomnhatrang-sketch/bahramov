#!/bin/bash
set -e

# Использование: ./publish-article.sh <относительный-url-статьи>
# Пример: ./publish-article.sh /blog/instagram-novyy-akkaunt-blokirovka-2026.html

if [ -z "$1" ]; then
  echo "Укажи путь к статье, например: /blog/article-name.html"
  exit 1
fi

ARTICLE_PATH="$1"
DOMAIN="https://bahramovai.com"
FULL_URL="${DOMAIN}${ARTICLE_PATH}"
INDEXNOW_KEY="0j0fuyj9g8pu8v1bftid0tymwhnxyxgh"

echo "→ Проверка stat-card (pre-publish)..."
python3 scripts/check-stat-cards.py || {
  echo "✗ Исправь РИСК/КРИТИЧНО и повтори publish"
  exit 1
}

echo "→ Пушу изменения в git..."
git add .
git commit -m "Publish: ${ARTICLE_PATH}" || echo "Нечего коммитить"
git push

echo "→ Жду 30 секунд, чтобы GitHub Pages успел задеплоить..."
sleep 30

echo "→ Пингую IndexNow (Bing, Yandex)..."
curl -s "https://api.indexnow.org/indexnow?url=${FULL_URL}&key=${INDEXNOW_KEY}" \
  && echo " ✓ IndexNow OK" \
  || echo " ✗ IndexNow ошибка"

echo "→ Пингую Google перечитать sitemap..."
curl -s "https://www.google.com/ping?sitemap=${DOMAIN}/sitemap.xml" \
  > /dev/null && echo " ✓ Google sitemap ping OK"

echo "→ Пингую Bing перечитать sitemap..."
curl -s "https://www.bing.com/ping?sitemap=${DOMAIN}/sitemap.xml" \
  > /dev/null && echo " ✓ Bing sitemap ping OK"

echo ""
echo "Готово! Статья опубликована: ${FULL_URL}"
echo "Индексация: Bing/Yandex — часы, Google — 1-3 дня."
