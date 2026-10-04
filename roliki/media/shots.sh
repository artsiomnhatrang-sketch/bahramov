#!/bin/bash
# Скриншоты-доказательства для 13 роликов (монтаж v2, 04.10). Фразы — дословно из статей сайта.
cd "$(dirname "$0")/.."
B=../blog; S=media/shots
shot() { node media/snimok.mjs --url "$B/$1.html" --sel "$2" --to "$3" --mark "$4" --out "$S/$5.png" | tail -1; }
TG=telegram-akkaunt-ugon-fishing-2026; GEO='p[data-geo-answer]'
shot $TG h1 "$GEO" "войдите заново по своему номеру" sc02-a
shot $TG h1 "$GEO" "Поддержка принимает обращения без входа через форму telegram.org/support" sc02-b
shot $TG h1 "$GEO" "Если номер увели, сначала верните его у оператора связи, потом занимайтесь аккаунтом" sc03-a
shot $TG h1 "$GEO" "привяжите резервную почту" sc03-b
shot $TG h1 "$GEO" "Поддержка принимает обращения без входа через форму telegram.org/support" sc04-a
shot $TG h1 "$GEO" "удалённый аккаунт не восстанавливается" sc04-b
shot $TG h1 "$GEO" "вход с кода обычно вытесняет чужую сессию" sc05-a
shot $TG h1 "$GEO" "завершите все чужие сеансы, поставьте облачный пароль и привяжите резервную почту" sc05-b
shot instagram-telegram-formulirovki-uvedomleniy-2026 h1 p.lead "Текст уведомления - это и есть диагноз" sc06-a
shot blokirovka-instagram-2026-polnoe-rukovodstvo h1 p.lead "отключённый аккаунт обжалуют ровно один раз" sc06-b
shot instagram-telegram-formulirovki-uvedomleniy-2026 h1 p.lead "третье означает, что стандартный путь обжалования исчерпан" sc07-a
shot instagram-povtornaya-blokirovka-2026 h1 "$GEO" "Смена почты и номера не помогает, если остаются тот же IP и тот же телефон" sc07-b
shot instagram-account-recovery-2026 h1 "$GEO" "многие из них можно оспорить, но только через официальные каналы Meta" sc08-a
shot instagram-account-recovery-2026 h1 "$GEO" "Сохраните скриншоты, найдите резервные коды 2FA и подайте первую апелляцию как можно раньше" sc08-b
shot instagram-vzlom-akkaunta-vernut-dostup-2026 "text:Что сделать в первые часы" +ul "Письмо о смене адреса обычно содержит ссылку для отмены изменения - она действует ограниченное время" sc09-a
shot instagram-vzlom-akkaunta-vernut-dostup-2026 h1 p.lead "При взломе уведомления нет: пароль просто перестаёт подходить" sc09-b
shot instagram-vzlom-akkaunta-vernut-dostup-2026 h1 p.lead "Взлом и блокировка - это разные ситуации, и лечатся они по-разному" sc10-a
shot instagram-vzlom-akkaunta-vernut-dostup-2026 h1 p.lead "При взломе уведомления нет: пароль просто перестаёт подходить, потому что его сменил кто-то другой" sc10-b
shot whatsapp-blokirovka-biznes-2026 h1 "$GEO" "стабильный доступ во многом держится на VPN" sc11-a
shot whatsapp-blokirovka-biznes-2026 h1 "$GEO" "Для клиента без VPN бизнес в WhatsApp фактически недоступен" sc11-b
shot whatsapp-blokirovka-biznes-2026 h1 "$GEO" "выгрузить чаты и контакты, пока доступ есть" sc12-a
shot telegram-vs-max-biznes-2026 h1 "$GEO" "основной канал там, где активнее ваша аудитория, и резервный на случай ограничений" sc12-b
shot instagram-telegram-unblock h1 "$GEO" "Спам-блок в телеграме снимают через бота @SpamBot" sc13-a
shot instagram-telegram-unblock h1 "$GEO" "письмом на abuse@telegram.org, обычно за 1-7 дней" sc13-b
shot chatplace-instagram-automation h1 p.lead "она подключается к аккаунту через официальный API и сама отвечает подписчикам" avto-a
shot chatplace-instagram-automation h1 p.lead "ведёт их по воронке и собирает заявки в CRM" avto-b
