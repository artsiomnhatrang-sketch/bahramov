#!/usr/bin/env python3
"""Сборщик выдачи Threads для подхода в браузере (01.10.2026).

Печатает JS, который один раз вставляется в javascript_tool на threads.com.
Он кладёт в localStorage список ников из журналов обоих аккаунтов и набор
функций. Дальше каждая функция вызывается одной строкой, без ручного разбора.

  python3 scripts/threads-collector.py          напечатать JS для вставки

После вставки (всё вызывать первой строкой, иначе CSP запрещает eval):
  await eval(localStorage.getItem('cl_collect'))   на странице поиска recent:
      4 прокрутки, свежие до 48 ч, фильтр боль + площадка, без наших ников,
      копит кандидатов в cl_cand, отвечает {added, seenSkip, total}
  eval(localStorage.getItem('cl_dump'))            вывести cl_cand в страницу,
      потом get_page_text (вывод javascript_tool режется на ~1000 знаков)
  eval(localStorage.getItem('cl_top'))             выдача Топ без фильтра:
      посты до 60 ч с пометкой SEEN, сразу в страницу для get_page_text
  await eval(localStorage.getItem('cl_harv'))      открытая ветка-сборник:
      все ответы с пометкой SEEN, копится в cl_thread
  localStorage.setItem('cl_T', текст); await eval(localStorage.getItem('cl_send'))
      открытая ветка: Развернуть конструктор, paste, сверка длины, Опубликовать
  eval(localStorage.getItem('cl_check'))           после перезагрузки ветки:
      ответ виден ровно один раз, иначе ошибка и батч останавливается.
      В длинных ветках свой ответ не виден - сверять threads-uniq.py sync

voice-lint и threads-uniq check перед отправкой всё равно обязательны.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = [ROOT / "threads/stalker-log.md", ROOT / "threads/ai/stalker-log.md"]


def seen_nicks():
    nicks = set()
    for p in LOGS:
        if p.exists():
            for m in re.findall(r"@([A-Za-z0-9_.]+)", p.read_text(encoding="utf-8")):
                nicks.add(m.rstrip("."))
    return sorted(nicks)


COLLECT = r"""(async()=>{
const seen=new Set(localStorage.getItem('cl_seen').split(' '));
const cand=JSON.parse(localStorage.getItem('cl_cand')||'{}');
const pain=/взлом|заблок|снесл|снес |удалил|удален|восстанов|не приходит|обжал|проверк|отключ|бан|блокир|угнал|украл|не могу (войти|зайти)|ограничен|спам|мошенник|селфи|деактив/i;
const plat=/акк|инст|тредс|threads|ватс|вацап|вотсап|whats|телег|тг|номер|страниц|профил|тик ?ток|tiktok/i;
const lim=Date.now()-48*3600e3; let added=0, seenSkip=0;
for(let i=0;i<4;i++){
 for(const c of document.querySelectorAll('div[data-pressable-container]')){
  const a=c.querySelector('a[href*="/post/"]'); const t=c.querySelector('time'); if(!a||!t) continue;
  const m=a.getAttribute('href').match(/\/@([^/]+)\/post\/([^/?]+)/); if(!m) continue;
  if(Date.parse(t.getAttribute('datetime'))<lim) continue;
  const txt=c.innerText.replace(/\n/g,' ').slice(0,420);
  if(!pain.test(txt)||!plat.test(txt)) continue;
  if(seen.has(m[1])){seenSkip++;continue;}
  if(!cand[m[2]]){cand[m[2]]={u:m[1],t:t.innerText,txt,q:decodeURIComponent((location.search.match(/q=([^&]+)/)||[])[1]||'')};added++;}
 }
 window.scrollBy(0,2500); await new Promise(r=>setTimeout(r,1200));
}
localStorage.setItem('cl_cand',JSON.stringify(cand));
return {added,seenSkip,total:Object.keys(cand).length};
})()"""

DUMP = r"""(()=>{const L=Object.entries(JSON.parse(localStorage.getItem('cl_cand')||'{}')).map(([id,v],i)=>i+' /@'+v.u+'/post/'+id+' ['+v.t+'|'+v.q+'] '+v.txt.slice(v.u.length,330)).join('\n\n'); document.body.innerHTML='<article><pre id=dump></pre></article>'; document.getElementById('dump').textContent=L; return L.length;})()"""

TOP = r"""(()=>{const seen=new Set(localStorage.getItem('cl_seen').split(' '));const lim=Date.now()-60*3600e3; const out=[]; for(const c of document.querySelectorAll('div[data-pressable-container]')){const a=c.querySelector('a[href*="/post/"]'); const t=c.querySelector('time'); if(!a||!t) continue; if(Date.parse(t.getAttribute('datetime'))<lim) continue; const u=a.getAttribute('href').split('/')[1].slice(1); out.push((seen.has(u)?'SEEN ':'')+a.getAttribute('href')+' ['+t.innerText+'] '+c.innerText.replace(/\n/g,' ').slice(0,260));} document.body.innerHTML='<article><pre id=dump></pre></article>'; document.getElementById('dump').textContent=out.join('\n\n'); return out.length;})()"""

HARV = r"""(async()=>{const seen=new Set(localStorage.getItem('cl_seen').split(' ')); const acc={}; for(let i=0;i<8;i++){ for(const c of document.querySelectorAll('div[data-pressable-container]')){const a=c.querySelector('a[href*="/post/"]'); const h=a?a.getAttribute('href'):''; if(!h||acc[h]) continue; const u=h.split('/')[1]?.slice(1)||''; acc[h]=(seen.has(u)?'SEEN ':'')+h+' | '+c.innerText.replace(/\n/g,' ').slice(0,220);} window.scrollBy(0,2000); await new Promise(r=>setTimeout(r,1000)); } localStorage.setItem('cl_thread', (localStorage.getItem('cl_thread')||'')+'\n\n=== '+location.pathname+'\n'+Object.values(acc).join('\n')); return Object.keys(acc).length;})()"""

SEND = r"""(async()=>{const T=localStorage.getItem('cl_T'); const bad=new RegExp('['+String.fromCharCode(8212,8211,171,187,8220,8221,8222,34)+']'); if (!T || bad.test(T) || /\.\s*$/.test(T)) throw new Error('voice-lint'); const exp=[...document.querySelectorAll('[role=button]')].find(b=>b.getAttribute('aria-label')==='Развернуть конструктор'); if(!exp) throw new Error('no composer'); exp.click(); await new Promise(r=>setTimeout(r,2000)); const dlg=document.querySelector('[role=dialog]'); const el=[...dlg.querySelectorAll('[contenteditable="true"]')].pop(); el.focus(); const dt=new DataTransfer(); dt.setData('text/plain', T); el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true})); await new Promise(r=>setTimeout(r,1200)); if(el.innerText.length!==T.length) throw new Error('len mismatch '+el.innerText.length+' vs '+T.length); const head=dlg.innerText.slice(0,70).replace(/\n/g,' '); [...dlg.querySelectorAll('[role=button],button')].find(b=>/^Опубликовать$/.test(b.innerText.trim())).click(); await new Promise(r=>setTimeout(r,5000)); localStorage.setItem('cl_probe', T.slice(0,35)); return {head, ok:true};})()"""

CHECK = r"""(()=>{const p=localStorage.getItem('cl_probe'); const n=document.body.innerText.split(p).length-1; if(n!==1) throw new Error('CHECK FAILED count='+n+' for '+p); return 'ok '+p;})()"""


def main():
    parts = {
        "cl_seen": " ".join(seen_nicks()),
        "cl_collect": COLLECT,
        "cl_dump": DUMP,
        "cl_top": TOP,
        "cl_harv": HARV,
        "cl_send": SEND,
        "cl_check": CHECK,
    }
    lines = [f"localStorage.setItem({json.dumps(k)}, {json.dumps(v, ensure_ascii=False)});"
             for k, v in parts.items()]
    lines.append("localStorage.removeItem('cl_cand'); localStorage.removeItem('cl_thread');")
    lines.append("'seen=' + localStorage.getItem('cl_seen').split(' ').length")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
