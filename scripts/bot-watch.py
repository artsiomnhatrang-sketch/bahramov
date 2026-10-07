#!/usr/bin/env python3
"""Сторож от накрутки ботами: Метрика + Вебмастер, раз в день.

Зачем (03.10.2026): Артёму написал продавец накрутки ПФ (Seopapa). Сайту на
GitHub Pages ломать нечего, но чужие боты на наш сайт Яндекс может принять
за накрутку. Защиты от этого нет ни у кого, есть только раннее обнаружение.

Что смотрит:
  - Метрика 110081984, визиты по дням за 15 дней: всплеск визитов против
    медианы прошлых дней, доля роботов, отказы и прямые заходы;
  - Вебмастер: проблемы сайта с важностью FATAL (там же санкции, THREATS).

Тревога: сообщение Артёму в Telegram (scripts/telegram_send.py) и готовое
письмо в поддержку Яндекса в drafts/yandex-support-<дата>.md. Само письмо
НЕ отправляется: уходит наружу от имени Артёма, только по его «да».

Токены из .env: YANDEX_WEBMASTER_TOKEN; для Метрики YANDEX_METRIKA_TOKEN
(если нет, пробуется токен Вебмастера - нужен доступ metrika:read).

  python3 scripts/bot-watch.py            # проверить и при тревоге написать
  python3 scripts/bot-watch.py --report   # таблица по дням, без отправки
"""
import datetime
import json
import os
import statistics
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTER = "110081984"
STATE = ROOT / "drafts" / ".bot-watch-state.json"
WM_API = "https://api.webmaster.yandex.net/v4"
MK_API = "https://api-metrika.yandex.net/stat/v1/data"

# Пороги. Обычный день сейчас ~10-35 визитов (Метрика, сентябрь-октябрь 2026).
# 07.10 Артём: «по пустякам не тревожить» - ложная тревога от 10 роботов Яндекса
# и Bing (наши же пуши и проверки) в неполный день. Поэтому смотрим только
# законченный вчерашний день и только массовые отклонения.
SPIKE_X = 3.0        # визитов за день больше медианы в N раз
SPIKE_MIN = 40       # и прирост не меньше N визитов (защита от 3 -> 10)
ROBOT_MIN = 50       # визитов-роботов за день: Метрика их и так отсеивает, опасны только толпой
DIRECT_X = 4.0       # прямых заходов больше медианы в N раз
DIRECT_MIN = 40      # и прирост прямых не меньше N визитов
WM_SEVERITY = ("FATAL",)  # CRITICAL там - 5xx и медленный ответ, у GitHub Pages разовые сбои
MSK = datetime.timezone(datetime.timedelta(hours=3))  # часовой пояс счётчика


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def get(url, tok):
    req = urllib.request.Request(url)
    req.add_header("Authorization", "OAuth " + tok)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        return {"_error": "HTTP %s %s" % (e.code, e.read().decode(errors="replace")[:200])}
    except Exception as e:
        return {"_error": "%s %s" % (type(e).__name__, str(e)[:200])}


def metrika(tok, dims, metrics):
    q = urllib.parse.urlencode({
        "ids": COUNTER, "date1": "14daysAgo", "date2": "today",
        "dimensions": dims, "metrics": metrics, "accuracy": "full", "limit": 1000,
    })
    return get(MK_API + "?" + q, tok)


def daily(tok):
    """{дата: {visits, robots, bounce, direct, search}}"""
    r = metrika(tok, "ym:s:date",
                "ym:s:visits,ym:s:robotPercentage,ym:s:bounceRate")
    if "_error" in r:
        return None, r["_error"]
    days = {}
    for row in r.get("data", []):
        d = row["dimensions"][0]["name"]
        v, rob, bnc = row["metrics"]
        days[d] = {"visits": int(v), "robots": rob, "bounce": bnc,
                   "direct": 0, "search": 0}
    r = metrika(tok, "ym:s:date,ym:s:lastTrafficSource", "ym:s:visits")
    for row in r.get("data", []):
        d, src = row["dimensions"][0]["name"], row["dimensions"][1].get("id")
        if d in days and src in ("direct", "organic"):
            days[d]["direct" if src == "direct" else "search"] = int(row["metrics"][0])
    return days, None


def check_metrika(days):
    """Только законченные дни по Москве: неполный сегодняшний даёт ложные проценты."""
    alerts = []
    today = datetime.datetime.now(MSK).date().isoformat()
    dates = sorted(d for d in days if d < today)
    if len(dates) < 5:
        return alerts
    base = dates[:-1]
    med_v = statistics.median(days[d]["visits"] for d in base) or 1
    med_dir = statistics.median(days[d]["direct"] for d in base) or 1
    for d in dates[-1:]:  # вчера
        x = days[d]
        if x["visits"] >= med_v * SPIKE_X and x["visits"] - med_v >= SPIKE_MIN:
            alerts.append("%s: визитов %d при обычных ~%d (x%.1f), поиск %d, прямые %d, отказы %.0f%%"
                          % (d, x["visits"], med_v, x["visits"] / med_v,
                             x["search"], x["direct"], x["bounce"]))
        robots = round(x["visits"] * x["robots"] / 100)
        if robots >= ROBOT_MIN:
            alerts.append("%s: доля роботов %.0f%% (%d из %d визитов)"
                          % (d, x["robots"], robots, x["visits"]))
        if x["direct"] >= med_dir * DIRECT_X and x["direct"] - med_dir >= DIRECT_MIN:
            alerts.append("%s: прямых заходов %d при обычных ~%d" % (d, x["direct"], med_dir))
    return alerts


def check_webmaster(tok):
    u = get(WM_API + "/user", tok)
    if "_error" in u:
        return [], "Вебмастер: " + u["_error"]
    uid = u["user_id"]
    hid = None
    for h in get(WM_API + "/user/%s/hosts" % uid, tok).get("hosts", []):
        if "bahramovai.com" in h.get("unicode_host_url", ""):
            hid = h["host_id"]
    if not hid:
        return [], "Вебмастер: сайт не найден"
    r = get(WM_API + "/user/%s/hosts/%s/diagnostics" % (uid, hid), tok)
    if "_error" in r:
        return [], "Вебмастер diagnostics: " + r["_error"]
    out = []
    for code, p in (r.get("problems") or {}).items():
        if p.get("state") == "PRESENT" and p.get("severity") in WM_SEVERITY:
            out.append("Вебмастер: проблема %s (%s)" % (code, p["severity"]))
    return out, None


def support_letter(alerts, days):
    today = datetime.date.today().isoformat()
    rows = "\n".join("| %s | %d | %d | %d | %.0f%% | %.0f%% |"
                     % (d, x["visits"], x["search"], x["direct"], x["robots"], x["bounce"])
                     for d, x in sorted(days.items())) if days else "(нет данных Метрики)"
    text = """# Письмо в поддержку Яндекс.Вебмастера (черновик %s)

Куда: webmaster.yandex.ru -> Помощь -> Связаться с поддержкой (или форма
https://yandex.ru/support/webmaster/ , раздел про поведенческие факторы).
Отправлять только после «да» Артёма.

---

Здравствуйте. Сайт https://bahramovai.com, счётчик Метрики 110081984.

С %s на сайт идёт посторонний трафик, который мы не заказывали и не
покупали. Что видно в Метрике и Вебмастере:

%s

Накрутку поведенческих факторов мы не используем и никому не заказывали.
Незадолго до этого, 02.10.2026, в Telegram мне написал менеджер сервиса
накрутки ПФ с предложением вывести сайт в топ, я отказался. Прошу учесть,
что это действия третьих лиц, и не применять к сайту санкции.

Готов предоставить доступ к Метрике и любые данные.

Артём Бахрамов, владелец сайта

---

Визиты по дням (Метрика):

| Дата | Визиты | Поиск | Прямые | Роботы | Отказы |
|---|---|---|---|---|---|
%s
""" % (today, today, "\n".join("- " + a for a in alerts), rows)
    path = ROOT / "drafts" / ("yandex-support-%s.md" % today)
    path.write_text(text, encoding="utf-8")
    return path


def notify(text):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "telegram_send.py"), text],
                   cwd=ROOT, env=os.environ, check=False)


def main():
    load_env()
    wm = os.environ.get("YANDEX_WEBMASTER_TOKEN", "")
    mk = os.environ.get("YANDEX_METRIKA_TOKEN") or wm
    report = "--report" in sys.argv

    days, err_m = daily(mk)
    alerts = check_metrika(days) if days else []
    wm_alerts, err_w = check_webmaster(wm)
    alerts += wm_alerts

    if report or not alerts:
        if days:
            print("Дата        Визиты Поиск Прямые Роботы Отказы")
            for d, x in sorted(days.items()):
                print("%s %6d %5d %6d %5.0f%% %5.0f%%"
                      % (d, x["visits"], x["search"], x["direct"], x["robots"], x["bounce"]))
    for e in (err_m and "Метрика: " + err_m, err_w):
        if e:
            print("НЕ ПРОВЕРЕНО -", e)
    if not alerts:
        if err_m or err_w:
            print("тревог нет, но проверка неполная (см. НЕ ПРОВЕРЕНО)")
            return 2
        print("ok: всплесков ботов и санкций не видно")
        return 0

    print("ТРЕВОГА:\n" + "\n".join(alerts))
    if report:
        return 1
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    key = "|".join(sorted(alerts))
    if state.get("last") == key:
        print("(об этом уже писали)")
        return 1
    path = support_letter(alerts, days or {})
    notify("⚠️ bahramovai.com: похоже на ботов или санкции\n\n" + "\n".join(alerts)
           + "\n\nЧерновик письма в поддержку Яндекса готов: " + path.relative_to(ROOT).as_posix()
           + "\nОткройте чат с Claude и скажите «отправляй» - отправлю после вашего да.")
    STATE.write_text(json.dumps({"last": key, "at": datetime.datetime.now().isoformat()}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
