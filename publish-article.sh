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

echo "→ Обновляю RSS-фид..."
python3 scripts/seo-sync.py

echo "→ Пушу изменения в git..."
git add .
git commit -m "Publish: ${ARTICLE_PATH}" || echo "Нечего коммитить"
git push

echo "→ Жду 30 секунд, чтобы GitHub Pages успел задеплоить..."
sleep 30

echo "→ Пингую IndexNow (Bing, Yandex) — статья + листинг блога..."
for URL in "${FULL_URL}" "${DOMAIN}/blog/"; do
  curl -s -o /dev/null -w "%{http_code}" \
    "https://api.indexnow.org/indexnow?url=${URL}&key=${INDEXNOW_KEY}" \
    | xargs -I{} echo "   {} ← ${URL}"
done

# Google отключил sitemap-ping в июне 2023, Bing — вслед за ним.
# Единственный рабочий путь ускорить Google — «Проверка URL» в Search Console.

echo "→ Публикую анонс в Telegram-канал…"
python3 scripts/rss-to-telegram.py

echo ""
echo "Готово! Статья опубликована: ${FULL_URL}"
echo "Индексация: Bing/Yandex — часы (IndexNow)."
echo "Google: запроси индексацию вручную в Search Console →"
echo "  https://search.google.com/search-console/inspect?resource_id=sc-domain:bahramovai.com&id=${FULL_URL}"
