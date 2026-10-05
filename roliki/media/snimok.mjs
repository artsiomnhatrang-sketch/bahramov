// Скриншот-доказательство для ролика: кусок реальной страницы с подсвеченной фразой.
//   node media/snimok.mjs --url <адрес или путь к html> --sel "h1" [--to "p[data-geo-answer]"]
//        [--mark "Обычно проверка проходит за 1-3 недели"] --out media/shots/<имя>.png [--w 820]
// --sel — первый блок, --to — последний (снимается всё между ними), --mark — фраза, которую подсветить.
// Факты на скриншоте реальные: снимаем существующую страницу, текст не правим.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const a = Object.fromEntries(process.argv.slice(2).join('\u0000').split('--').filter(Boolean)
  .map((x) => x.split('\u0000').filter(Boolean)).map(([k, ...v]) => [k.trim(), v.join(' ').trim() || true]));
const url = /^https?:/.test(a.url) ? a.url : pathToFileURL(resolve(a.url)).href;
const W = Number(a.w ?? 820);
mkdirSync(dirname(a.out), { recursive: true });

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: W, height: 1600 }, deviceScaleFactor: 2 });
await p.goto(url, { waitUntil: 'networkidle' }).catch(() => {});
await p.evaluate(() => document.fonts.ready);
const box = await p.evaluate(([sel, to, mark]) => {
  // шапка, липкие кнопки и баннеры поверх текста не нужны
  for (const e of document.querySelectorAll('body *')) {
    const ps = getComputedStyle(e).position;
    if (ps === 'fixed' || ps === 'sticky') e.style.display = 'none';
  }
  // sel вида «text:Что сделать» — заголовок по тексту; to вида «+ul» — ближайший следующий соседний блок
  let A = sel.startsWith('text:')
    ? [...document.querySelectorAll('h1,h2,h3')].find((h) => h.textContent.includes(sel.slice(5)))
    : document.querySelector(sel);
  let B = A;
  // to вида «~p» — только блок после заголовка, в котором стоит mark (когда фраза не в первом абзаце)
  if (to && to.startsWith('~')) {
    B = [...document.querySelectorAll(to.slice(1))].find((e) => (A.compareDocumentPosition(e) & 4) && e.textContent.includes(mark));
    A = B;
  } else if (to && to.startsWith('+')) { B = A?.nextElementSibling; while (B && !B.matches(to.slice(1))) B = B.nextElementSibling; }
  else if (to) B = document.querySelector(to);
  if (!A || !B) return null;
  if (mark) {
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n; (n = walk.nextNode());) {
      const i = n.data.indexOf(mark);
      if (i < 0) continue;
      const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + mark.length);
      const m = document.createElement('mark');
      m.style.cssText = 'background:#f4672a;color:#000;padding:0 4px;border-radius:4px';
      r.surroundContents(m); break;
    }
  }
  A.scrollIntoView();
  const ra = A.getBoundingClientRect(), rb = B.getBoundingClientRect();
  return { x: 0, y: ra.top + scrollY - 10, width: innerWidth, height: rb.bottom - ra.top + 24 };
}, [a.sel ?? 'h1', a.to, a.mark]);
if (!box) throw new Error('не нашёл блок ' + a.sel);
await p.screenshot({ path: a.out, clip: box, fullPage: true });
await b.close();
console.log('скриншот:', a.out, Math.round(box.width), '×', Math.round(box.height));
