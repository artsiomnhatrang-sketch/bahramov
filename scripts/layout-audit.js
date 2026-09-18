/**
 * Аудит вёрстки bahramovai.com. ES-модуль, работает В БРАУЗЕРЕ.
 *
 * Зачем: preflight ловит ссылки и разметку, но не видит пустых полос,
 * вылезающих за край блоков и одиноких слов в переносах. Это правило
 * «финальная проверка — это рендер» из CLAUDE.md, доведённое до кода.
 *
 * Как запускать (вкладка на http://localhost:8099/ — тот же origin):
 *   const m = await import('/scripts/layout-audit.js?v=' + Date.now());
 *   await m.run(m.SITEMAP, [375, 768, 1280]);
 *
 * Возвращает только находки: страницы без проблем в отчёт не попадают.
 */

const BLUE = /^rgba?\(\s*(0|[1-9]\d?|1\d\d)\s*,\s*(0|[1-9]\d?|1\d\d)\s*,\s*(2[0-9]\d|1[6-9]\d)\s*[,)]/;

function lineBoxes(doc, el) {
  const rg = doc.createRange();
  rg.selectNodeContents(el);
  const lines = [];
  for (const r of rg.getClientRects()) {
    if (r.height <= 0 || r.width <= 0) continue;
    const L = lines.find(x => Math.abs(x.top - r.top) < 4);
    if (L) { L.left = Math.min(L.left, r.left); L.right = Math.max(L.right, r.right); }
    else lines.push({ top: r.top, left: r.left, right: r.right });
  }
  lines.sort((a, b) => a.top - b.top);
  return lines.map(l => Math.round(l.right - l.left));
}

function name(el) {
  const c = String(el.className || '').split(' ').filter(Boolean)[0] || '';
  return (el.tagName.toLowerCase() + (c ? '.' + c : '')).slice(0, 34);
}

function scrollableAncestor(el, doc, win) {
  let a = el.parentElement;
  while (a && a !== doc.body) {
    if (/auto|scroll|hidden/.test(win.getComputedStyle(a).overflowX)) return true;
    a = a.parentElement;
  }
  return false;
}

/** Всё, что реально рисует контент: текстовые строки, картинки, линии. */
function contentBoxes(doc, win) {
  const boxes = [];
  const walk = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    if (!n.nodeValue.trim()) continue;
    const p = n.parentElement;
    if (!p || p.closest('script,style,noscript,template,.mobile-cta')) continue;
    const cs = win.getComputedStyle(p);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const rg = doc.createRange();
    rg.selectNodeContents(n);
    for (const r of rg.getClientRects()) {
      if (r.height > 0 && r.width > 0) boxes.push([Math.round(r.top), Math.round(r.bottom)]);
    }
  }
  doc.querySelectorAll('img,svg,canvas,iframe,video,hr').forEach(e => {
    if (e.closest('.mobile-cta')) return;
    const cs = win.getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const r = e.getBoundingClientRect();
    if (r.height > 2 && r.width > 2) boxes.push([Math.round(r.top), Math.round(r.bottom)]);
  });
  return boxes.sort((a, b) => a[0] - b[0]);
}

export function audit(doc, win, W) {
  const out = {};
  const push = (k, v) => { (out[k] = out[k] || []).push(v); };

  // 1. Страница едет вбок
  const sw = Math.max(doc.documentElement.scrollWidth, doc.body.scrollWidth);
  if (sw > W + 1) out.pageOverflow = sw - W;

  // 2. Блоки за правым краем без прокручиваемого родителя
  doc.querySelectorAll('body *').forEach(e => {
    if (e.closest('script,style,noscript,.mobile-cta')) return;
    const cs = win.getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.position === 'fixed') return;
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return;
    if (r.right > W + 1 && !scrollableAncestor(e, doc, win)) push('wide', name(e) + '@' + Math.round(r.right));
  });

  // 3. Мёртвое место в конце страницы и большие пустоты
  const boxes = contentBoxes(doc, win);
  let cur = 0, maxGap = 0, gaps = 0;
  for (const [t, b] of boxes) {
    const g = t - cur;
    if (g >= 130) { gaps++; if (g > maxGap) maxGap = g; }
    if (b > cur) cur = b;
  }
  const tail = doc.documentElement.scrollHeight - cur;
  if (tail > 60) out.tail = tail;
  if (gaps) { out.gaps = gaps; out.maxGap = maxGap; }

  // 4. Одинокое слово в последней строке
  doc.querySelectorAll('p,li,h1,h2,h3,h4,figcaption,summary').forEach(e => {
    if (e.closest('script,style,noscript')) return;
    const cs = win.getComputedStyle(e);
    if (cs.display === 'none' || !e.textContent.trim()) return;
    if (/flex|grid/.test(cs.display)) return;
    const w = lineBoxes(doc, e);
    if (w.length < 2) return;
    const last = w[w.length - 1], widest = Math.max(...w);
    if (last < 70 && last < widest * 0.3) push('orphan', name(e) + '|' + w.join(','));
  });

  // 5. Синие ссылки — правило 21 из CLAUDE.md
  doc.querySelectorAll('a').forEach(a => {
    if (!a.textContent.trim()) return;
    const c = win.getComputedStyle(a).color;
    if (BLUE.test(c)) push('blueLink', name(a) + '|' + c);
  });

  // 6. Слишком мелкий текст
  doc.querySelectorAll('p,li,span,a,div,td,th,figcaption').forEach(e => {
    if (e.children.length || !e.textContent.trim()) return;
    const cs = win.getComputedStyle(e);
    if (cs.display === 'none') return;
    if (parseFloat(cs.fontSize) < 10) push('tiny', name(e) + '|' + cs.fontSize);
  });

  // 7. Видимые пустые блоки
  doc.querySelectorAll('p,li,h1,h2,h3,h4,section,div').forEach(e => {
    if (e.children.length || e.textContent.trim()) return;
    const cs = win.getComputedStyle(e);
    if (cs.display === 'none') return;
    if (cs.backgroundImage !== 'none' || parseFloat(cs.borderTopWidth) > 0) return;
    if (e.getBoundingClientRect().height >= 14) push('empty', name(e));
  });

  // 8. Кнопки и ссылки-цели мельче 40 px по высоте
  doc.querySelectorAll('a[class*=btn],button,a[class*=cta]').forEach(e => {
    const cs = win.getComputedStyle(e);
    if (cs.display === 'none' || !e.textContent.trim()) return;
    const h = e.getBoundingClientRect().height;
    if (h > 0 && h < 34) push('smallTarget', name(e) + '|' + Math.round(h));
  });

  // 9. Картинки без размеров — прыжок вёрстки при загрузке
  doc.querySelectorAll('img').forEach(e => {
    if (!e.getAttribute('width') || !e.getAttribute('height')) push('imgNoDim', e.getAttribute('src') || '?');
  });

  // сворачиваем списки до счётчика и трёх примеров
  for (const k of Object.keys(out)) {
    if (Array.isArray(out[k])) {
      const uniq = [...new Set(out[k])];
      out[k] = { n: out[k].length, ex: uniq.slice(0, 3) };
    }
  }
  return out;
}

export async function run(urls, widths = [375, 1280], settle = 320) {
  const bust = '?_a=' + Date.now();
  const report = [];
  for (const W of widths) {
    for (const u of urls) {
      const ifr = document.createElement('iframe');
      ifr.style.cssText = `position:fixed;left:-9999px;top:0;width:${W}px;height:812px;border:0;`;
      document.body.appendChild(ifr);
      await new Promise(r => { ifr.onload = r; ifr.onerror = r; ifr.src = u + bust; });
      await new Promise(r => setTimeout(r, settle));
      let res;
      try { res = audit(ifr.contentDocument, ifr.contentWindow, W); }
      catch (e) { res = { err: String(e).slice(0, 80) }; }
      ifr.remove();
      if (Object.keys(res).length) report.push({ u, W, ...res });
    }
  }
  return report;
}

export const SITEMAP = ['/', '/uslugi/', '/uslugi/vzlom-telegram-vosstanovlenie.html',
  '/uslugi/razblokirovka-instagram.html', '/uslugi/ai-agent.html', '/about.html',
  '/offer.html', '/privacy.html', '/consent.html', '/404.html', '/blog/'];

/** Все статьи блога — берутся из sitemap.xml, чтобы список не расходился. */
export async function articles() {
  const xml = await fetch('/sitemap.xml').then(r => r.text());
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)]
    .map(m => m[1].replace('https://bahramovai.com', ''))
    .filter(u => u.startsWith('/blog/') && u.endsWith('.html'));
}
