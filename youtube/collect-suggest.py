import json, urllib.parse, urllib.request, time, sys
seeds = ["взломали телеграм","взломали телеграмм","угнали телеграм","вернуть телеграм","восстановить телеграм",
"телеграм канал взломали","заблокировали инстаграм","инстаграм заблокировал","восстановить инстаграм",
"разблокировать инстаграм","взломали инстаграм","инстаграм проверка личности","подтвердить личность инстаграм",
"аккаунт заблокирован инстаграм","нарушение целостности аккаунта","инстаграм 180 дней","инстаграм бан",
"заблокировали ватсап","не могу зайти в инстаграм","инстаграм требует селфи"]
out={}
for s in seeds:
    url="https://suggestqueries.google.com/complete/search?"+urllib.parse.urlencode(
        {"q":s,"client":"firefox","ds":"yt","hl":"ru","oe":"utf-8","ie":"utf-8"})
    try:
        raw=urllib.request.urlopen(url, timeout=10).read()
        for enc in ("utf-8","cp1251"):
            try:
                d=json.loads(raw.decode(enc)); out[s]=d[1]; break
            except Exception: continue
    except Exception as e:
        out[s]=["ОШИБКА: %s" % e]
    time.sleep(0.3)
json.dump(out, open(sys.argv[1],"w"), ensure_ascii=False, indent=1)
for k,v in out.items():
    print("=== %s" % k)
    for x in v[1:]: print("   ", x)
