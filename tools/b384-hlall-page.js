// The paint half of tools/check-b384-hlall.py, run in Chromium: the viewer's own painter draws the whole page (paintPages) and the card's picture
// (paint) of a citation, and the pixels are measured. Module code; HAVE_BOOK is declared before it.
import * as pdfjs from '/pdfjs/build/pdf.min.mjs';
import * as V from '/viewer.js';
pdfjs.GlobalWorkerOptions.workerSrc = '/pdfjs/build/pdf.worker.min.mjs';
const S = 2;                                                                   // pixels per point
const ctr = { standardFontDataUrl: '/pdfjs/standard_fonts/', cMapUrl: '/pdfjs/cmaps/', cMapPacked: true };
let bank, countyDoc, bookDoc, index;
const copts = { cache: new Map() }, bopts = { cache: new Map(), fontBold: new Map() };
(async () => {
  try {
    bank = await (await fetch('/bank.json')).json();
    countyDoc = await pdfjs.getDocument({ url: '/county.pdf', ...ctr }).promise;
    if (HAVE_BOOK) { bookDoc = await pdfjs.getDocument({ url: '/book.pdf', ...ctr }).promise; index = await V.buildIndex(bookDoc, {}); }
    window.__ready = true;
  } catch (e) { window.__failed = String(e); }
})();

// the colours: WASH multiplied on white paper, the deeper gold multiplied over it
const isSoft = (R, G, B) => R >= 252 && Math.abs(G - 245) <= 4 && Math.abs(B - 160) <= 6;
const isDeep = (R, G, B) => R >= 250 && Math.abs(G - 215) <= 6 && B <= 45;
function classify(cv) {
  const W = cv.width, H = cv.height, D = cv.getContext('2d').getImageData(0, 0, W, H).data, cls = new Uint8Array(W * H);
  for (let p = 0, i = 0; p < W * H; p++, i += 4) {
    const R = D[i], G = D[i + 1], B = D[i + 2];
    cls[p] = (R >= 250 && G >= 240 && B >= 240) ? 0 : isSoft(R, G, B) ? 1 : isDeep(R, G, B) ? 2 : (R + G + B) < 450 ? 3 : (R >= 235 && G >= 170 && B < 215 && R - B >= 25) ? 4 : 5;     // 4: some other yellow; 5: any other colour (the page's own shading)
  }
  return { W, H, D, cls };
}
// a flat area of some other colour: pixels whose whole 3x3 neighbourhood is "other" and the same colour (an edge's blends are a pixel or two wide)
function thirdTone(c) {
  const { W, H, D, cls } = c; let n = 0;
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    const p = y * W + x; if (cls[p] !== 4) continue;
    let flat = true; const i = p * 4;
    for (let dy = -1; dy <= 1 && flat; dy++) for (let dx = -1; dx <= 1; dx++) { const q = p + dy * W + dx; if (cls[q] !== 4) { flat = false; break; } const j = q * 4; if (Math.abs(D[j] - D[i]) > 2 || Math.abs(D[j + 1] - D[i + 1]) > 2 || Math.abs(D[j + 2] - D[i + 2]) > 2) { flat = false; break; } }
    if (flat) n++;
  }
  return n;
}
function bboxOf(c, x0, x1, y0, y1) {
  const { W, H, cls } = c; let bx0 = Infinity, bx1 = -1, by0 = Infinity, by1 = -1;
  x0 = Math.max(0, Math.floor(x0)); x1 = Math.min(W - 1, Math.ceil(x1)); y0 = Math.max(0, Math.floor(y0)); y1 = Math.min(H - 1, Math.ceil(y1));
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const k = cls[y * W + x]; if (k === 1 || k === 2) { if (x < bx0) bx0 = x; if (x > bx1) bx1 = x; if (y < by0) by0 = y; if (y > by1) by1 = y; } }
  return bx1 < 0 ? null : { x0: bx0, x1: bx1 + 1, y0: by0, y1: by1 + 1 };
}

async function load(id) {
  const q = bank.questions.find(q => q.id === id), c = q.citation, county = c.source === 'amendment';
  if (county) { const clip = await V.countyClip(countyDoc, c, copts); return { county, doc: countyDoc, clip, opts: copts, c }; }
  const loc = V.locate(index, c);
  if (!loc.ok || loc.kind === 'pages' || loc.kind === 'figure') return null;
  const clip = await V.computeClip(bookDoc, index, loc, c, bopts);
  return { county, doc: bookDoc, clip, opts: bopts, c, loc };
}

window.shot = async (id) => {                                                    // (debug) the whole page, painted: data URLs
  const L = await load(id); if (!L || !L.clip || !L.clip.ok) return [];
  const box = document.createElement('div'); document.body.appendChild(box);
  await V.paintPages(L.doc, L.clip.pages, box, { scale: S, ...L.opts, clip: L.clip });
  const out = [...box.querySelectorAll('canvas')].map(c => c.toDataURL('image/png')); box.remove(); return out;
};
window.measure = async (id) => {
  const L = await load(id);
  if (!L || !L.clip || !L.clip.ok) return { skip: true };
  const { county, doc, clip, opts } = L, bad = [], metrics = { 'right pad (px)': [], 'left pad (px)': [], 'top pad (px)': [], 'bottom pad (px)': [], 'heading off-centre (px)': [] };
  const box = document.createElement('div'); document.body.appendChild(box);
  try {
    // ---- the whole page
    await V.paintPages(doc, clip.pages, box, { scale: S, ...opts, clip });
    const cited = clip.cited || clip.segments;
    const cvs = [...box.querySelectorAll('canvas.ifc-page')];
    for (let k = 0; k < clip.pages.length; k++) {
      const p = clip.pages[k], cv = cvs[k]; if (!cv) { bad.push(['no page painted', 'p' + p]); continue; }
      const page = await doc.getPage(p), PH = page.view[3];
      if (Math.abs(cv.width - page.view[2] * S) > 3) continue;                    // a sideways page is turned: left whole
      const segs = cited.filter(s => s.page === p && !s.whole);
      if (!segs.length) continue;
      const c = classify(cv);
      const tc = await page.getTextContent();
      const items = tc.items.filter(it => it.str && /[A-Za-z0-9]/.test(it.str)).map(it => ({ s: it.str, x: it.transform[4], y: it.transform[5], w: it.width, h: it.height || 10 }));
      const fs = county ? 11 : 10, em = fs * S;
      const tt = thirdTone(c); if (tt > 60) bad.push(['a third tint on the page (not the one soft tint / one deeper gold)', tt + ' px, p' + p]);
      // tint outside every provision window
      let outside = 0;
      for (let y = 0; y < c.H; y++) {
        const inWin = segs.some(sg => y >= (PH - sg.y1) * S - 2.2 * em && y <= (PH - sg.y0) * S + 2.2 * em);
        if (inWin) continue;
        for (let x = 0; x < c.W; x++) { const q = c.cls[y * c.W + x]; if (q === 1 || q === 2) outside++; }
      }
      if (outside > 150) bad.push(['tint outside the provision it highlights', outside + ' px, p' + p]);
      for (const sg of segs) {
        const ytop = (PH - sg.y1) * S, ybot = (PH - sg.y0) * S;
        const bb = county ? bboxOf(c, 0, c.W, ytop - 1.6 * em, ybot + 1.6 * em) : bboxOf(c, sg.x0 * S, sg.x1 * S + 3, ytop - 1.6 * em, ybot + 1.6 * em);
        if (!bb) { bad.push(['nothing tinted on the page where the citation is', 'p' + p]); continue; }
        // the text inside this block
        const inb = items.filter(it => it.y >= sg.y0 - 1 && it.y <= sg.y1 + 1 && it.x + it.w / 2 >= sg.x0 - 2 && it.x + it.w / 2 <= sg.x1 + 2);
        if (!inb.length) continue;
        const ymax = Math.max(...inb.map(it => it.y)), ymin = Math.min(...inb.map(it => it.y));
        const topI = inb.filter(it => ymax - it.y <= 3), botI = inb.filter(it => it.y - ymin <= 3);
        const inkTop = Math.max(...topI.map(it => it.y + 0.69 * it.h)), inkBot = Math.min(...botI.map(it => it.y - 0.205 * it.h));
        // vertical: the block runs from its first line of text to its last, the same room above and below (a pad of less than nothing: the block stops
        // short of its text; far more than a line: it runs on past it)
        const tp = (PH - inkTop) * S; const dTop = tp - bb.y0, dBot = bb.y1 - (PH - inkBot) * S;
        metrics['top pad (px)'].push(dTop); metrics['bottom pad (px)'].push(dBot);
        if (dTop < -0.3 * em || dTop > 1.4 * em || dBot < -0.3 * em || dBot > 1.4 * em) bad.push(['the soft block does not run from the provision\'s first line to its last', 'p' + p + ' room above ' + Math.round(dTop) + 'px, below ' + Math.round(dBot) + 'px']);
        // horizontal: a block of text runs to the right edge of its column
        const body = (it) => county || (it.h >= 9.5 && it.h <= 10.8);
        const col = items.filter(it => body(it) && (county ? it.x + it.w <= 545 : it.x + it.w <= 600) && (county || (it.x + it.w / 2 >= sg.x0 - 2 && it.x + it.w / 2 <= sg.x1 + 2 && it.x + it.w <= sg.x1 + 2)));          // (the county's text is one column: the whole page)
        if (!col.length) continue;
        const colL = Math.min(...col.map(it => it.x)), colR = Math.max(...col.map(it => it.x + it.w));
        if (sg.xr != null && !sg.table) {                                   // (a block with a table in it runs out to the table's own rules)
          const rp = bb.x1 - colR * S; metrics['right pad (px)'].push(rp);
          if (rp < 0.2 * em || rp > 0.8 * em) bad.push(['the soft block does not end at its column\'s right edge (same room as every block)', 'p' + p + ' ' + Math.round(rp) + 'px past the column']);
          const lp = Math.min(...inb.map(it => it.x)) * S - bb.x0; metrics['left pad (px)'].push(lp);
        }
        // a centred heading sits centred in its block
        const lineW = Math.max(...topI.map(it => it.x + it.w)) - Math.min(...topI.map(it => it.x)), lineC = (Math.max(...topI.map(it => it.x + it.w)) + Math.min(...topI.map(it => it.x))) / 2;
        if (lineW < 0.75 * (colR - colL) && Math.abs(lineC - (colL + colR) / 2) <= 3 && !/^\s*(?:TABLE|Table)\b/.test(topI.slice().sort((a, b) => a.x - b.x).map(it => it.s).join(''))) {        // (a table's title is centred over the table, which the booklet does not always centre in the column)
          const off = Math.abs((bb.x0 + bb.x1) / 2 - lineC * S); metrics['heading off-centre (px)'].push(off);
          if (off > 3) bad.push(['a centred heading is not centred in its soft block', 'p' + p + ' ' + off.toFixed(1) + 'px off']);
        }
      }
    }
    // ---- the card's picture: the same two colours, nothing else
    box.replaceChildren();
    await V.paint(doc, clip, box, { scale: 1.7, ...opts });
    for (const cv of box.querySelectorAll('canvas')) {
      const c = classify(cv), tt = thirdTone(c);
      if (tt > 60) bad.push(['a third tint in the card\'s picture', tt + ' px']);
      let tint = 0, tot = c.W * c.H; for (let i = 0; i < c.cls.length; i++) if (c.cls[i] === 1 || c.cls[i] === 2) tint++;
      if (tint < 0.3 * tot) bad.push(['the card\'s picture is not washed in the one soft tint', Math.round(100 * tint / tot) + '%']);
    }
  } finally { box.remove(); }
  const m = {}; for (const [k, v] of Object.entries(metrics)) if (v.length) m[k] = v;
  return { bad, metrics: m };
};
