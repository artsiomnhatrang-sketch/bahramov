#!/usr/bin/env python3
# Диагностика сайта bahramovai.com. Только чтение. Ничего не меняет.
import os, re, glob, urllib.request, urllib.error
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
files = sorted(glob.glob("*.html") + glob.glob("blog/*.html"))

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.a=[]; s.img=[]; s.h1=0; s.title=""; s._t=False
        s.canon=False; s.og=False; s.desc=False
    def handle_starttag(s,t,at):
        d=dict(at)
        if t=="a": s.a.append(d.get("href"))
        if t=="img": s.img.append(d.get("src"))
        if t=="h1": s.h1+=1
        if t=="title": s._t=True
        if t=="link" and d.get("rel")=="canonical": s.canon=True
        if t=="meta" and d.get("property")=="og:title": s.og=True
        if t=="meta" and d.get("name")=="description": s.desc=True
    def handle_endtag(s,t):
        if t=="title": s._t=False
    def handle_data(s,dt):
        if s._t: s.title+=dt

def local(h):
    if not h: return None
    h=h.strip()
    if h.startswith(("mailto:","tel:","#")): return "skip"
    if h.startswith("http"):
        if "bahramovai.com" in h: p=re.sub(r"^https?://[^/]*bahramovai\.com","",h)
        else: return "ext:"+h
    else: p=h
    p=p.split("#")[0].split("?")[0]
    if p in ("","/"): p="index.html"
    if p.endswith("/"): p+="index.html"
    return p.lstrip("/")

broken_int=[]; bad_href=[]; broken_img=[]; ext=set()
placeholders=[]; mojibake=[]; structure=[]; deadtg=[]
PLACE=[r"\(уточнить", r"\bTODO\b", r"\bFIXME\b", r"lorem ipsum",
       r"\[Заголовок", r"\[описание", r"\[плейсхолдер", r"XXXX", r"\uFFFD"]
MOJI=["Ð","Ñ‚","Ñ","â€","Ã©","Ã¤","Â "]

for f in files:
    raw=Path(f).read_text(encoding="utf-8",errors="replace")
    if "t.me/bahramovai" in raw and "t.me/bahramovai/" not in raw:
        for m in re.finditer(r"t\.me/bahramovai(?![a-z])", raw): deadtg.append(f)
    for pat in PLACE:
        if re.search(pat, raw, re.I): placeholders.append(f"{f}: {pat}")
    for m in MOJI:
        if m in raw: mojibake.append(f"{f}: '{m}'")
    p=P()
    try: p.feed(raw)
    except Exception as e: structure.append(f"{f}: parse error {e}"); continue
    if p.h1!=1: structure.append(f"{f}: H1={p.h1} (должен быть 1)")
    if not p.title.strip(): structure.append(f"{f}: пустой <title>")
    if not p.canon: structure.append(f"{f}: нет canonical")
    if not p.og: structure.append(f"{f}: нет og:title")
    if not p.desc: structure.append(f"{f}: нет meta description")
    for h in p.a:
        r=local(h)
        if r is None: bad_href.append(f"{f}: <a> без href или href пустой")
        elif r=="skip": pass
        elif isinstance(r,str) and r.startswith("ext:"): ext.add(r[4:])
        elif not os.path.isfile(r): broken_int.append(f"{f}: {h} -> нет файла {r}")
    for s in p.img:
        r=local(s)
        if isinstance(r,str) and not r.startswith("ext:") and r not in (None,"skip") and not os.path.isfile(r):
            broken_img.append(f"{f}: img {s} -> нет {r}")

# внешние ссылки
extres=[]
for u in sorted(ext):
    st=None
    for meth in ("HEAD","GET"):
        try:
            req=urllib.request.Request(u,method=meth,headers={"User-Agent":"Mozilla/5.0"})
            st=urllib.request.urlopen(req,timeout=10).status; break
        except urllib.error.HTTPError as e:
            st=e.code
            if e.code in (403,405,429): continue
            break
        except Exception as e:
            st=f"ERR:{type(e).__name__}"; continue
    extres.append((u,st))

# sitemap
sm=[]
if os.path.isfile("sitemap.xml"):
    smraw=Path("sitemap.xml").read_text(encoding="utf-8",errors="replace")
    locs=re.findall(r"<loc>(.*?)</loc>", smraw)
    smpaths={local(l) for l in locs}
    for f in files:
        if f=="blog/index.html" or "/" not in f: continue
        if f not in smpaths: sm.append(f"НЕ в sitemap: {f}")
    for l in locs:
        r=local(l)
        if r and r!="skip" and not os.path.isfile(r): sm.append(f"sitemap ссылается на несуществующий: {l}")

def sec(title, items, ok="чисто"):
    print(f"\n=== {title} ({len(items)}) ===")
    if not items: print("  ✅ "+ok)
    else:
        for i in items: print("  ❌ "+i)

print(f"Проверено файлов: {len(files)}")
sec("Битые внутренние ссылки", broken_int)
sec("Ссылки без href / пустые", bad_href)
sec("Битые картинки", broken_img)
sec("Забытые плейсхолдеры/мусор", placeholders)
sec("Кривая кодировка (mojibake)", mojibake)
sec("Проблемы структуры/SEO", structure)
sec("Мёртвая ссылка t.me/bahramovai", deadtg)
sec("Sitemap рассинхрон", sm)
print(f"\n=== Внешние ссылки ({len(extres)}) ===")
for u,st in extres:
    mark = "✅" if st==200 else ("⚠️ проверить вручную" if (isinstance(st,str) or st in (403,405,429,999)) else "❌")
    print(f"  {mark} [{st}] {u}")
print("\n--- stat-card проверка ---")
