// ifc-viewer.js: show the IFC code a question points to, taken from the reader's OWN copy of the 2021 IFC PDF.
//
// Nothing here knows any IFC wording. A question carries only a pointer:
//   { section, heading, pdfPage, pdfPageEnd?, printedPage, printedPageEnd?, exception?, through?, stopAtException? }
//   exception        the question is about that exception ("Exception 2"): it is marked in the clipping
//   through          show the section from its heading through the end of that subsection (the deciding words sit in child sections)
//   stopAtException  n: the question is not about an exception, so the clipping ends just above the n-th "Exception" heading
//                    (locate() sets loc.stoppedAtException; pass the pointer with stopAtException: null to show the exceptions too)
//   stopAtTable      n: the question is not about the table inside the section: the clipping ends just above the n-th table caption
//   find             (sections and definitions) one to eight words of the clipping, or an array of such phrases: the DECIDING words of a long passage.
//                    The sentence or list item that carries the phrase is highlighted like the heading (mark kind 'cite'); a phrase that is not found marks nothing
//   row              (tables) the label of the table row the question is about, as printed in the first column ("Classroom area"), or an
//                    array of labels: those rows are marked and the clipping shows the caption, the rows around them and the notes
//   entry, org       (chapter 80, section "80") the designation of the referenced standard ("25—20") and, for display only, its organisation ("NFPA")
//   figure, box      (drawings, signs, forms) `figure` is the caption printed under the picture ("FIGURE D103.1"), `box` = [x0, y0, x1, y1] in pdf points
//                    (origin bottom-left) the part of page `pdfPage` to show. The caption must be on that page of the reader's copy, else nothing is cut.
//                    A question's `picture` is such a pointer too (figure, box, pdfPage, printedPage): the drawing the question shows, without its label.
// The reader loads their licensed PDF once (it stays on their device, nothing is uploaded). This module
//   1. reads the PDF with pdf.js and builds a small index of where every section / table / definition starts,
//   2. locates the pointer in that index (by section number + title, nearest to the pdfPage hint),
//   3. works out which rectangles of which pages make up that section (column aware),
//   4. paints those rectangles ("a clipping of the book page") with the section heading marked.
// If anything fails, the caller shows the whole cited page(s) instead (see wholePages()).
//
// ES module; no dependencies. Pass the pdf.js "doc" (PDFDocumentProxy) in. Steps 1 to 3 also run in Node (tests).
//
// How the 2021 IFC PDF is laid out (found by inspecting it; the code relies on exactly this):
//   * page 612 x 792 pt, two text columns, running header above y=735, page label and licence footer below y=36;
//   * body text is 10 pt; table cells are 9 pt, table column headings 7 pt, table notes 8 pt;
//   * headings are bold text items that start with the section number ("1015.3 Height."), sometimes split
//     over several items; chapter 2 definitions are bold UPPERCASE terms that end with a period;
//   * pdf.js returns the text of the two columns first (in reading order) and the cells of every table
//     LAST ("floats"), so a table body is found by position, not by stream order;
//   * a few pages (the big hazardous-materials tables) are typeset sideways: those are shown as whole pages.

export const INDEX_VERSION = 5;

const SEC = /^(?:\[[A-Z]{1,3}\]\s*)?((?:[A-Z]{1,2})?\d{2,4}(?:\.\d+)+[A-Za-z]?)\.?(?:\s+(\S.*))?$/;
const TABLE = /^(?:\[[A-Z]{1,3}\]\s*)?TABLE\s+((?:[A-Z]{1,2})?\d{2,4}(?:\.\d+)*(?:\(\d+\))?)(.*)$/;
const BANNER = /^(SECTION|CHAPTER|APPENDIX)\s+([A-Z]?\d{1,4}|[A-N])\b/;
const EXC = /^Exceptions?:?\s*$/;
const LABEL = /^(?:[A-N]-|\d{1,2}-)\d{1,3}$/;
const DEFTERM = /^(?:\[[A-Z]{1,3}\]\s*)?([A-Z0-9][A-Z0-9’'\-\/ ,&()]{1,80})\.$/;     // top-level definition: no lowercase letters
const SUBTERM = /^(?:\[[A-Z]{1,3}\]\s*)?([A-Za-z0-9][A-Za-z0-9’'\-\/ ,&()]{2,80})\.$/;  // nested definition ("Level 1 aerosol products.")
const NEWHEAD = /^(?:\[[A-Z]{1,3}\]\s*)?(?:(?:[A-Z]{1,2})?\d{2,4}(?:\.\d+)+|TABLE\s|SECTION\s|CHAPTER\s|APPENDIX\s|Exceptions?\b)/;

const LEAD_LINES = 7;                         // lines of a section shown under its banner when the banner alone is cited (locate, flowClip)
const BODY_TOP = 735, BODY_BOTTOM = 36;      // items above / below are running headers, page labels and the licence footer
const BODY_H = 9.5;                           // body text is 10 pt; table cells are 9 pt or smaller
const COL_L = 28, COL_R = 584;                // left / right edge used for clippings
const COL_STEP = 261;                          // from the left column's text to the right column's (243pt column + 18pt gutter)

export function norm(s) {
  return String(s).toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9]+/g, '');
}

const inBody = (it) => it.y >= BODY_BOTTOM && it.y <= BODY_TOP;
const isBodySize = (it) => it.h >= BODY_H && it.h <= 10.8;

// ------------------------------------------------------------------------------------------------ reading a page
// A page model: items in pdf.js stream order (i = position), plus
//   F    first stream position of the "floats" (table cells), which pdf.js lists after the two text columns
//   g    x of the gutter between the two text columns (null when the page is not two-column)
//   rot  0, or 90 / 270 when the page is typeset sideways (then the page is shown whole, rotated to read)
export async function pageModel(doc, p, fontBold, cache) {
  if (cache && cache.has(p)) return cache.get(p);
  const page = await doc.getPage(p);
  const tc = await page.getTextContent();
  let need = false;
  for (const it of tc.items) {
    if (it.str && it.str.trim() && !fontBold.has(it.fontName)) { need = true; break; }
  }
  if (need) {                                   // font names are per document; learn which are bold from the operator list once
    try { await page.getOperatorList(); } catch (e) { /* ignore */ }
    for (const it of tc.items) {
      if (!it.fontName || fontBold.has(it.fontName)) continue;
      let b = false;
      try { const o = page.commonObjs.get(it.fontName); b = /bold|black|heavy/i.test(o && o.name || '') || !!(o && o.bold); } catch (e) { /* not resolved on this page */ }
      fontBold.set(it.fontName, b);
    }
  }
  const items = tc.items.map((it, i) => {
    const s = it.str || '', tr = it.transform;
    // the margin marks that show what changed since the last edition are symbol-font glyphs (private-use characters): not text
    // (and the asterisks printed in the left margin of three pages: also not text of the code)
    const mark = /^[\uE000-\uF8FF\s]+$/.test(s) || (/^\*{1,3}$/.test(s.trim()) && tr[4] < 40);
    return { i, s, t: mark ? '' : s.trim(), x: tr[4], y: tr[5], w: it.width, h: it.height || Math.abs(tr[3]) || 10, b: !!fontBold.get(it.fontName),
             r: (Math.abs(tr[1]) > 0.01 || Math.abs(tr[2]) > 0.01) ? (tr[1] > 0 ? 90 : 270) : 0 };
  });
  const text = items.filter(it => it.t);
  const sideways = text.filter(it => it.r);
  const rot = sideways.length > 0.3 * text.length ? (sideways.filter(it => it.r === 90).length >= sideways.length / 2 ? 90 : 270) : 0;
  // floats = the maximal tail of the stream made of small items (header and footer items do not count)
  let F = items.length, hasBody = false;
  for (let k = items.length - 1; k >= 0; k--) {
    const it = items[k];
    if (!it.t || !inBody(it)) continue;
    if (isBodySize(it) || it.h > 10.8) { F = k + 1; hasBody = true; break; }
    F = k;
  }
  if (!hasBody) F = items.length;
  const model = { p, items, view: page.view, F, hasBody, rot, g: rot ? null : gutterOf(items, F, hasBody) };
  if (cache) cache.set(p, model);
  return model;
}

// The gutter of a page is the widest nearly empty vertical band near the middle of the body text (body-size text of the
// two columns only: banners, captions and table cells are ignored). "Nearly": a few full-width lines (an italic intro under a
// title, a centred note) cross the gutter on some pages, so a band may be crossed by up to three such lines (or a seventh of the
// lines that cross the busiest spot of the window).
function gutterOf(items, F, hasBody) {
  const src = items.filter(it => it.t && inBody(it) && (hasBody ? (it.i < F && isBodySize(it)) : it.h < 10.8));
  if (src.length < 12) return null;
  const lo = 255, hi = 355;
  const cover = new Uint16Array(hi - lo);
  for (const it of src) {
    for (let x = Math.max(lo, Math.floor(it.x)); x < Math.min(hi, Math.ceil(it.x + it.w)); x++) cover[x - lo]++;
  }
  let peak = 0;
  for (let x = 0; x < hi - lo; x++) if (cover[x] > peak) peak = cover[x];
  const thr = Math.max(3, Math.floor(0.15 * peak));
  let best = null, start = -1;
  for (let x = 0; x <= hi - lo; x++) {
    const empty = x < hi - lo && cover[x] <= thr;
    if (empty && start < 0) start = x;
    if (!empty && start >= 0) {
      const w = x - start;
      if (!best || w > best.w) best = { w, x0: lo + start, x1: lo + x };
      start = -1;
    }
  }
  if (!best || best.w < 8) return null;
  return (best.x0 + best.x1) / 2;
}

// ------------------------------------------------------------------------------------------------ index
// A bold run: consecutive bold items on one baseline (spaces do not break it), plus continuation lines when wanted.
function boldRun(items, k, withLines) {
  const a = items[k];
  const n = items.length;
  let j = k, last = k, text1 = '', xEnd = a.x + a.w;
  for (; j < n; j++) {
    const it = items[j];
    if (j > k) {
      if (!it.t) { if (Math.abs(it.y - a.y) < 2.5) { text1 += it.s; last = j; continue; } break; }
      if (!it.b || Math.abs(it.y - a.y) > 2.5) break;
    }
    text1 += it.s; last = j; xEnd = Math.max(xEnd, it.x + it.w);
  }
  let all = text1;
  let y = a.y;
  for (let more = 0; withLines && more < 2; more++) {          // a heading or term may wrap onto a second / third bold line
    let m = last + 1;
    while (m < n && !items[m].t) m++;
    if (m >= n) break;
    const it = items[m];
    const dy = y - it.y;
    if (!(it.b && dy >= 6 && dy <= 16 && it.x <= a.x + 2 && inBody(it))) break;
    const sub = boldRun(items, m, false);
    const t = sub.text1.replace(/\s+/g, ' ').trim();
    if (NEWHEAD.test(t)) break;
    all += ' ' + sub.text1; last = sub.last; y = it.y;
  }
  return { text1: text1.replace(/\s+/g, ' ').trim(), text: all.replace(/\s+/g, ' ').trim(), x: a.x, y: a.y, w: xEnd - a.x, h: a.h, last };
}

// heads: [page, itemIndex, kind, token, text, x, y, w, h]   kind: sec | table | banner | exc | def | sub
export async function buildIndex(doc, opts = {}) {
  const fontBold = new Map();
  const heads = [];
  const labels = {};
  const rotPages = {};
  const hdr = { n: 0, hit: 0 };
  let ch2 = null, ch3 = null;
  for (let p = 1; p <= doc.numPages; p++) {
    const model = await pageModel(doc, p, fontBold, null);
    const { items } = model;
    let seen = false;
    for (const it of items) {
      if (!it.t || inBody(it)) continue;
      if (LABEL.test(it.t)) labels[p] = it.t;
      if (/^2021 INTERNATIONAL FIRE CODE/.test(it.t)) seen = true;
    }
    hdr.n++; if (seen) hdr.hit++;
    if (model.rot) rotPages[p] = model.rot;
    for (let k = 0; k < items.length; k++) {
      const it = items[k];
      if (!it.t || !inBody(it)) continue;
      let m;
      if ((m = TABLE.exec(it.t))) {
        heads.push([p, k, 'table', m[1], (m[2] || '').trim().slice(0, 90), it.x, it.y, it.w, it.h]);
        continue;
      }
      if (!it.b) continue;
      const inDefs = ch2 != null && ch3 == null;
      const run = boldRun(items, k, true);
      const t1 = run.text1;
      if ((m = SEC.exec(t1)) && run.h >= BODY_H) {
        heads.push([p, k, 'sec', m[1], (m[2] ? run.text.slice(run.text.indexOf(m[2])) : '').slice(0, opts.titleMax || 90), run.x, run.y, run.w, run.h]);
      } else if ((m = BANNER.exec(t1))) {
        heads.push([p, k, 'banner', m[1] + ' ' + m[2], t1.slice(0, 90), run.x, run.y, run.w, run.h]);
        if (m[1] === 'CHAPTER' && m[2] === '2' && ch2 == null && p > 30) ch2 = p;
        if (m[1] === 'CHAPTER' && m[2] === '3' && ch3 == null && p > 30) ch3 = p;
      } else if (EXC.test(t1)) {
        heads.push([p, k, 'exc', t1.replace(/:/, ''), '', run.x, run.y, run.w, run.h]);
      } else if (inDefs && run.text.length > 3 && !/^Exceptions?\b/.test(run.text)) {
        if ((m = DEFTERM.exec(run.text))) heads.push([p, k, 'def', '202', m[1], run.x, run.y, run.w, run.h]);
        else if ((m = SUBTERM.exec(run.text1))) heads.push([p, k, 'sub', '202', m[1], run.x, run.y, run.w, run.h]);
      }
      k = Math.max(k, run.last);
    }
    if (opts.onProgress && p % 20 === 0) opts.onProgress(p, doc.numPages);
  }
  return { v: INDEX_VERSION, numPages: doc.numPages, labels, heads, hdr, ch2, ch3, rotPages };
}

// Is this the 2021 IFC? (cheap checks on the index; the app shows the reason when it says no)
export function checkEdition(index) {
  const sec = index.heads.filter(h => h[2] === 'sec').length;
  const okPages = index.numPages >= 650 && index.numPages <= 760;
  const okHdr = index.hdr.n > 0 && index.hdr.hit / index.hdr.n >= 0.6;
  const okSec = sec > 3000;
  const okLabels = Object.keys(index.labels).length > index.numPages * 0.5;
  if (okPages && okHdr && okSec) return { ok: true, labelsFound: okLabels };
  const why = [];
  if (!okPages) why.push('the PDF has ' + index.numPages + ' pages (the 2021 IFC has about 697)');
  if (!okHdr) why.push('the running header "2021 INTERNATIONAL FIRE CODE" was not found on most pages');
  if (!okSec) why.push('too few numbered sections were found (' + sec + ')');
  return { ok: false, reason: why.join('; ') };
}

// ------------------------------------------------------------------------------------------------ is it the right book?
// checkEdition() only looks at the SHAPE of the PDF (page count, running header, number of headings): another edition of the code
// has the same shape. verifyCopy() asks the real question: is this the very book the questions were written from? It holds the
// reader's copy against the question bank itself, three ways:
//   1. structure  every section, table, definition and chapter the bank points to must be found, by number AND title, on the page the bank names;
//   2. labels     the page label printed on each cited page ("10-14") must be the one the bank expects;
//   3. text       for a spread sample of questions, the decisive words (the `find` phrase, the table row, the standard's designation, the figure
//                 caption) and the numbers of the keyed answer must be printed on the cited page(s) of this copy.
// Nothing here knows any IFC wording: the words and numbers come from the bank. A different edition, a different book or a shifted page range fails
// all three at once. A near copy (a later printing with a few corrected pages) fails a few references: those ids come back in `badIds`, so the app can
// keep exactly those references locked instead of showing a clipping that may say something else.
//   verifyCopy(doc, index, bank.questions, { sample: 150, onProgress, cache, fontBold })
//     -> { ok, level: 'exact' | 'close' | 'different', reason?, summary, scores: { structure, labels, words, numbers }, counts, differences: [ids], badIds: [ids] }
//   level 'exact': this is the book; badIds is empty (a stray difference is listed in `differences` only). 'close': usable, but keep the badIds references locked.
//   level 'different': refuse the PDF and show `reason`.
// `sample` = how many questions get the text check (default 150, about 1 to 2 seconds on a desktop; Infinity = all). Pass the same cache / fontBold
// maps you use for painting, so the pages read here are not read twice.
const NUMTOK = /\d+(?:\.\d+)?/g;
const numbersIn = (s) => String(s).replace(/(\d),(?=\d{3}(?!\d))/g, '$1').match(NUMTOK) || [];
const pageBodyText = (model) => model.items.filter(it => it.t && inBody(it)).map(it => it.s).join(' ');
// the book sometimes spells a number out ("Ten feet", "Twenty-five feet"): that counts as the same number (10 to 99 and 100 are handled; the words are
// compared without spaces or hyphens, like all text here)
const ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'];
const TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];
const wordOf = (n) => { n = Number(n); return n >= 100 && n % 100 === 0 && n <= 900 ? ONES[n / 100] + 'hundred' : n >= 10 && n < 20 ? ONES[n] : n >= 20 && n < 100 ? TENS[Math.floor(n / 10)] + ONES[n % 10] : null; };

function evidenceOf(q) {
  const c = q.citation || {}, phrases = [], nums = [];
  for (const f of [].concat(c.find || [])) if (f) phrases.push(f);
  for (const r of [].concat(c.row || [])) if (r) phrases.push(r);
  if (c.entry) phrases.push(c.entry);
  if (c.figure) phrases.push(c.figure);
  // the keyed answer's numbers, but only for a question whose stem has no number of its own (a worked example computes its answer: nothing printed to find)
  if (q.type === 'content' && q.kind !== 'definition' && q.options && q.options[q.answer] && !/\d/.test(q.question || '')) {
    for (const n of numbersIn(q.options[q.answer])) if (n.includes('.') || Number(n) >= 10) nums.push(n);       // small whole numbers occur on every page: no evidence
  }
  return { phrases, nums };
}

export async function verifyCopy(doc, index, questions, opts = {}) {
  const ed = checkEdition(index);
  if (!ed.ok) return { ok: false, level: 'different', reason: ed.reason, summary: ed.reason, scores: {}, counts: {}, badIds: [] };
  const cache = opts.cache || new Map(), fontBold = opts.fontBold || new Map();
  const bad = new Set();
  const cnt = { refs: 0, structure: 0, structureOk: 0, labels: 0, labelsOk: 0, words: 0, wordsOk: 0, numbers: 0, numbersOk: 0 };
  const hasLabels = Object.keys(index.labels).length > index.numPages * 0.5;
  const ifc = (questions || []).filter(q => q.citation && q.citation.source === 'ifc');
  cnt.refs = ifc.length;
  // 1 + 2: the whole bank, index only (no page is read again)
  for (const q of ifc) {
    const c = q.citation;
    if (hasLabels && c.printedPage && index.labels[c.pdfPage]) {
      cnt.labels++;
      if (index.labels[c.pdfPage] === c.printedPage) cnt.labelsOk++; else bad.add(q.id);
    }
    if (c.figure || c.entry || String(c.section).trim() === '80') continue;          // checked by the words step (caption / designation)
    let loc;
    try { loc = locate(index, c); } catch (e) { loc = { ok: false }; }
    cnt.structure++;
    // a table is found at its caption; the cited row may sit on a later page of the same table
    const there = loc.ok && loc.start && (loc.kind === 'table' ? (c.pdfPage >= loc.start.page && c.pdfPage <= loc.start.page + 3) : loc.start.page === c.pdfPage);
    if (there && loc.exact !== false) cnt.structureOk++; else bad.add(q.id);
  }
  // 3: words and numbers on the cited pages, for a spread sample
  const pool = ifc.map(q => ({ q, ev: evidenceOf(q) })).filter(x => x.ev.phrases.length || x.ev.nums.length)
    .sort((a, b) => a.q.citation.pdfPage - b.q.citation.pdfPage);
  const want = Math.min(pool.length, opts.sample == null ? 150 : opts.sample);
  const chosen = want >= pool.length ? pool : Array.from({ length: want }, (_, k) => pool[Math.floor(k * pool.length / want)]);
  const pages = new Map();                                                           // page -> { norm: letters+digits only, nums: Set }
  const pageInfo = async (p) => {
    if (pages.has(p)) return pages.get(p);
    const model = await pageModel(doc, p, fontBold, cache);
    const txt = pageBodyText(model);
    const info = { norm: norm(txt), nums: new Set(numbersIn(txt)) };
    pages.set(p, info); return info;
  };
  let done = 0;
  for (const { q, ev } of chosen) {
    const c = q.citation, a = c.pdfPage, b = Math.min(Math.max(c.pdfPageEnd || a, a + 1), a + 2, index.numPages);
    const infos = [];
    for (let p = a; p <= b; p++) infos.push(await pageInfo(p));
    if (ev.phrases.length) {
      cnt.words++;
      if (ev.phrases.every(ph => { const n = norm(ph); return !n || infos.some(i => i.norm.includes(n)); })) cnt.wordsOk++; else bad.add(q.id);
    }
    if (ev.nums.length) {
      cnt.numbers++;
      if (ev.nums.every(n => infos.some(i => i.nums.has(n) || (!n.includes('.') && wordOf(n) && i.norm.includes(wordOf(n)))))) cnt.numbersOk++; else bad.add(q.id);
    }
    if (opts.onProgress && ++done % 25 === 0) opts.onProgress(done, chosen.length);
  }
  const rate = (ok, n) => n ? ok / n : null;
  const scores = { structure: rate(cnt.structureOk, cnt.structure), labels: rate(cnt.labelsOk, cnt.labels), words: rate(cnt.wordsOk, cnt.words), numbers: rate(cnt.numbersOk, cnt.numbers) };
  const atLeast = (v, t) => v == null || v >= t;                                      // a check that had nothing to look at does not fail the copy
  const pct = (v) => v == null ? 'n/a' : Math.round(v * 1000) / 10 + '%';
  const summary = 'sections on the expected page ' + cnt.structureOk + ' of ' + cnt.structure + ' (' + pct(scores.structure) + '); page labels ' + cnt.labelsOk + ' of ' + cnt.labels +
                  ' (' + pct(scores.labels) + '); decisive words ' + cnt.wordsOk + ' of ' + cnt.words + ' (' + pct(scores.words) + '); numbers ' + cnt.numbersOk + ' of ' + cnt.numbers + ' (' + pct(scores.numbers) + ')';
  const exact = atLeast(scores.structure, 0.985) && atLeast(scores.labels, 0.985) && atLeast(scores.words, 0.97) && atLeast(scores.numbers, 0.9);
  const close = atLeast(scores.structure, 0.9) && atLeast(scores.labels, 0.9) && atLeast(scores.words, 0.85) && atLeast(scores.numbers, 0.7);
  if (exact || close) return { ok: true, level: exact ? 'exact' : 'close', summary, scores, counts: cnt, differences: [...bad], badIds: exact ? [] : [...bad] };
  const why = [];
  if (!atLeast(scores.structure, 0.9)) why.push('only ' + pct(scores.structure) + ' of the sections the questions point to are on the expected page');
  if (!atLeast(scores.labels, 0.9)) why.push('only ' + pct(scores.labels) + ' of the page labels match');
  if (!atLeast(scores.words, 0.85)) why.push('only ' + pct(scores.words) + ' of the decisive words were found on the cited pages');
  if (!atLeast(scores.numbers, 0.7)) why.push('only ' + pct(scores.numbers) + ' of the answer numbers were found on the cited pages');
  return { ok: false, level: 'different', reason: why.join('; ') + ' (this looks like a different edition or book)', summary, scores, counts: cnt, differences: [...bad], badIds: [...bad] };
}

// ------------------------------------------------------------------------------------------------ locating a pointer
function titleMatches(headText, want) {
  const a = norm(headText), b = norm(want);
  if (!b) return true;
  if (!a) return false;
  const n = Math.min(a.length, b.length, 14);
  return a.slice(0, n) === b.slice(0, n);
}

export function locate(index, ptr) {
  const heads = index.heads;
  // a figure (a drawing, a sign, a form printed in the book): found by its caption on the cited page, see figureClip
  if (ptr.figure) return { ok: true, kind: 'figure', token: String(ptr.figure), start: { page: ptr.pdfPage }, exact: true };
  const raw = String(ptr.section).trim();
  const hint = ptr.pdfPage || 1;
  // best candidate = nearest to the page hint; a title that does not match costs 3 pages
  const pick = (arr, want) => {
    const score = (k) => Math.abs(heads[k][0] - hint) + (titleMatches(heads[k][4], want) ? 0 : 3);
    return arr.slice().sort((a, b) => score(a) - score(b) || a - b)[0];
  };
  const ids = (kind, f) => heads.map((h, k) => k).filter(k => heads[k][2] === kind && (!f || f(heads[k])));
  let kind, cands = [], token = null, want = ptr.heading;
  let m;
  if (raw === '80') {                                             // Referenced Standards: one entry of the list, or (no `entry`) whole pages
    if (ptr.entry) return { ok: true, kind: 'entry', token: String(ptr.entry), start: { page: ptr.pdfPage }, exact: true };
    return { ok: true, kind: 'pages', note: 'referenced standards: whole pages' };
  }
  if (raw === '202') {
    kind = 'def';
    const w = norm(ptr.heading);
    cands = ids('def', h => norm(h[4]) === w);
    if (!cands.length) cands = ids('sub', h => norm(h[4]) === w);
    if (!cands.length) cands = ids('def', h => w.length >= 6 && norm(h[4]).length >= 6 && (norm(h[4]).startsWith(w) || w.startsWith(norm(h[4]))));
    if (!cands.length) cands = ids('sub', h => w.length >= 6 && norm(h[4]).length >= 6 && (norm(h[4]).startsWith(w) || w.startsWith(norm(h[4]))));
  } else if (/^table\s/i.test(raw)) {
    kind = 'table'; want = '';
    token = raw.replace(/^table\s+/i, '');
    cands = ids('table', h => h[3] === token && !/continued/i.test(h[4]));
    if (!cands.length) cands = ids('table', h => h[3] === token);
  } else if ((m = /^chapter\s+(\d{1,2})$/i.exec(raw))) {
    kind = 'banner'; want = ''; token = 'CHAPTER ' + m[1];
    cands = ids('banner', h => h[3] === token && h[0] > 30);
  } else if ((m = /^appendix\s+([A-N])$/i.exec(raw))) {
    kind = 'banner'; want = ''; token = 'APPENDIX ' + m[1].toUpperCase();
    cands = ids('banner', h => h[3] === token && h[0] > 40);
  } else if ((m = /^(?:section\s+)?(\d{2,4})$/i.exec(raw))) {
    kind = 'banner'; want = ''; token = 'SECTION ' + m[1];
    cands = ids('banner', h => h[3] === token);
  } else {
    kind = 'sec';
    const toks = raw.match(/(?:[A-Z]{1,2})?\d{2,4}(?:\.\d+)+[A-Za-z]?/g) || [raw];
    token = toks[0];
    cands = ids('sec', h => h[3] === token);
    if (toks.length > 1) {                                   // "2703.1.1 and 2703.1.2": from the first to the end of the last
      const lastLoc = locate(index, { ...ptr, section: toks[toks.length - 1] });
      const firstLoc = locate(index, { ...ptr, section: toks[0] });
      if (firstLoc.ok && lastLoc.ok && lastLoc.start.page >= firstLoc.start.page) return { ...firstLoc, end: lastLoc.end, composite: toks.length };
      return firstLoc;
    }
  }
  if (!cands.length) return { ok: false, kind, note: 'section not found in this PDF' };
  const k = pick(cands, want);
  const h = heads[k];
  const start = { page: h[0], i: h[1], x: h[5], y: h[6], w: h[7], h: h[8] };
  const out = { ok: true, kind, token, start, headIndex: k, distance: Math.abs(h[0] - hint),
                exact: (kind === 'table' || kind === 'banner') ? true : titleMatches(h[4], ptr.heading), rot: !!(index.rotPages && index.rotPages[h[0]]) };
  if (kind === 'table') return out;                           // a table is found by position (see tableClip)
  // the section ends at the next heading (any level) in reading order
  let e = null;
  for (let j = k + 1; j < heads.length; j++) {
    const hk = heads[j][2];
    if (hk === 'exc') continue;
    if ((kind === 'sec' || kind === 'banner') && hk === 'table') continue;          // a table inside a section belongs to it
    if ((kind === 'sec' || kind === 'banner') && (hk === 'def' || hk === 'sub')) continue;
    if (kind === 'def' && hk !== 'def' && hk !== 'banner' && !(h[2] === 'sub' && hk === 'sub')) continue;
    if (kind === 'banner' && hk === 'banner' && /^SECTION/.test(heads[j][3]) && /^SECTION/.test(token) === false && false) continue;
    e = j; break;
  }
  out.end = e == null ? null : { page: heads[e][0], i: heads[e][1], x: heads[e][5], y: heads[e][6], w: heads[e][7], h: heads[e][8] };
  // A section's banner alone ("SECTION 312 VEHICLE IMPACT PROTECTION": the next heading is the section's first subsection, set right under it)
  // is cut with the start of the section, as a chapter's title is cut with its note: the clipping runs on through that first subsection,
  // and flowClip keeps the banner and at most LEAD_LINES lines under it, in the banner's column, on its page (see `lead` there).
  if (kind === 'banner' && /^SECTION /.test(token) && !ptr.blur && e != null && heads[e][2] === 'sec' && heads[e][0] === h[0]) {
    let e2 = null;
    for (let j = e + 1; j < heads.length; j++) { const hk = heads[j][2]; if (hk === 'exc' || hk === 'table' || hk === 'def' || hk === 'sub') continue; e2 = j; break; }
    out.end = e2 == null ? null : { page: heads[e2][0], i: heads[e2][1], x: heads[e2][5], y: heads[e2][6], w: heads[e2][7], h: heads[e2][8] };
    out.lead = LEAD_LINES;
  }
  const fullEnd = out.end;                                  // where the whole section ends (the whole-page view highlights all of it, exceptions and tables included)
  // optional "stopAtException": n  - the question is not about an exception, so the clipping ends just above the n-th "Exception(s):" heading of this section
  // (counted from the section heading). Not found (another copy of the book laid out differently): the section is shown whole, nothing is lost.
  if (kind === 'sec' && ptr.stopAtException > 0 && !ptr.exception && !ptr.through) {
    let n = 0;
    for (let j = k + 1; j < (e == null ? heads.length : e); j++) {
      if (heads[j][2] === 'exc' && ++n === ptr.stopAtException) {
        out.end = { page: heads[j][0], i: heads[j][1], x: heads[j][5], y: heads[j][6], w: heads[j][7], h: heads[j][8] };
        out.stoppedAtException = true;
        break;
      }
    }
  }
  // optional "stopAtTable": n  - the question is not about the table that sits inside this section: the clipping ends just above its n-th table caption
  if (kind === 'sec' && ptr.stopAtTable > 0 && !ptr.through) {
    let n = 0;
    for (let j = k + 1; j < (e == null ? heads.length : e); j++) {
      if (heads[j][2] === 'table' && ++n === ptr.stopAtTable) {
        out.end = { page: heads[j][0], i: heads[j][1], x: heads[j][5], y: heads[j][6], w: heads[j][7], h: heads[j][8] };
        out.stoppedAtTable = true;
        break;
      }
    }
  }
  if (out.stoppedAtException || out.stoppedAtTable) out.fullEnd = fullEnd;
  // optional "through": show this section from its heading to the end of the named subsection (the answer sits further down than the first subsection)
  if (kind === 'sec' && ptr.through && ptr.through !== token) {
    const t = locate(index, { ...ptr, section: ptr.through, through: null, exception: null, heading: '', pdfPage: ptr.pdfPageEnd || ptr.pdfPage });
    if (t.ok && t.kind === 'sec' && (t.start.page > h[0] || (t.start.page === h[0] && t.start.i > h[1]))) {
      out.end = t.end; out.through = ptr.through;
    }
  }
  return out;
}

export function wholePages(index, ptr, maxPages = 3) {
  const a = ptr.pdfPage, b = Math.min(ptr.pdfPageEnd || a, a + maxPages - 1);
  const out = [];
  for (let p = a; p <= b && p <= index.numPages; p++) out.push(p);
  return out;
}

// ------------------------------------------------------------------------------------------------ geometry
const top = (it) => it.y + 0.95 * it.h;
const bottom = (it) => it.y - 0.3 * it.h;
function rectOf(it) { return { x0: it.x, x1: it.x + it.w, y0: bottom(it), y1: top(it) }; }
// (384 one picture) WHERE A LINE'S INK IS. A mark carries the ink of the words it covers - i0..i1, from the baseline: the tallest
// letters (ASC) above it and the descenders (DSC) below, in ems - and the size of its type (fs). Measured on the rendered pages
// (pdf.js, both sources): the book's Times 0.68-0.69 / 0.21, the county booklet's Calibri 0.69 / 0.18-0.19. The marker is laid
// on that ink with the same room above and below (paint), not on the item's box, which reached 0.95 em up and 0.3 down: the gold
// rode high on its words. y0..y1 stay the marker's band (the ink and an even pad) for anything that reads the rectangle.
const ASC = 0.69, DSC = 0.205, DSC_COUNTY = 0.19;
export const MARK_INK = { asc: ASC, dsc: DSC, county: { asc: ASC, dsc: DSC_COUNTY } };
function inkMark(m, base, fs, dsc) {
  m.i0 = base - (dsc || DSC) * fs; m.i1 = base + ASC * fs; m.fs = fs;
  m.y0 = m.i0 - 0.12 * fs; m.y1 = m.i1 + 0.12 * fs;
  return m;
}
function union(r, q) {
  return r ? { x0: Math.min(r.x0, q.x0), x1: Math.max(r.x1, q.x1), y0: Math.min(r.y0, q.y0), y1: Math.max(r.y1, q.y1) } : { ...q };
}
const centre = (it) => it.x + it.w / 2;

// The gutter between the two columns for a stretch of rows (yBot..yTop): the empty vertical band nearest to the page's gutter g, looking at
// every text item of those rows, table cells included. A table that sticks a little over the page's gutter (or a column that does not reach it)
// moves the band; null when nothing is empty there (a table or a line runs across both columns).
function gutterNear(model, yTop, yBot, g) {
  const lo = Math.max(200, Math.floor(g - 40)), hi = Math.min(420, Math.ceil(g + 40));
  const cover = new Uint16Array(hi - lo);
  for (const it of model.items) {
    if (!it.t || !inBody(it) || it.y > yTop || it.y < yBot) continue;
    for (let x = Math.max(lo, Math.floor(it.x)); x < Math.min(hi, Math.ceil(it.x + it.w)); x++) cover[x - lo]++;
  }
  let best = null, start = -1;
  for (let x = 0; x <= hi - lo; x++) {
    const empty = x < hi - lo && cover[x] === 0;
    if (empty && start < 0) start = x;
    if (!empty && start >= 0) {
      const w = x - start, c = lo + start + w / 2;
      if (w >= 6 && (!best || Math.abs(c - g) < Math.abs(best.c - g))) best = { c, w };
      start = -1;
    }
  }
  return best ? best.c : null;
}

// A cut made in the gutter (g +- 4) can leave the first millimetre of the other column's letters inside the picture on pages where that column
// starts just left of g + 4, and a mark printed in the page margin (an asterisk beside a heading) can reach a little way into a cut made at the
// column edge: a thin sliver of a letter at the picture's edge. When such an item (its centre outside the cut) overlaps the cut by under 4 pt, the
// cut moves to just short of it, provided no item whose centre is inside the cut is touched by the move; items whose centre is outside the cut
// stay out of the picture either way, so the clipping's text does not change.
function trimEdges(model, seg) {
  if (seg.whole || seg.figure || seg.x0 == null) return seg;
  const rows = model.items.filter(it => it.s && it.s.trim() && inBody(it) && it.y <= seg.y1 && it.y >= seg.y0);   // any printed mark, not only words
  const inside = rows.filter(it => centre(it) >= seg.x0 && centre(it) <= seg.x1);
  let x0 = seg.x0, x1 = seg.x1;
  for (const it of rows) {
    const c = centre(it);
    if (c > seg.x1 && it.x < seg.x1 && seg.x1 - it.x < 4) x1 = Math.min(x1, it.x - 0.4);
    if (c < seg.x0 && it.x + it.w > seg.x0 && it.x + it.w - seg.x0 < 4) x0 = Math.max(x0, it.x + it.w + 0.4);
  }
  if (x1 < seg.x1 && inside.some(it => it.x + it.w > x1 + 0.2)) x1 = seg.x1;
  if (x0 > seg.x0 && inside.some(it => it.x < x0 - 0.2)) x0 = seg.x0;
  // (384 final check) THE GUTTER SIDE HUGS THE COLUMN'S OWN TEXT. The trim above only sees the other column's LETTERS, and only
  // ones that reach under 4pt into the cut; a ruler's ticks or a tick mark printed by the gutter is not a letter at all, and a
  // few letters reached further - four cuts kept a sliver of the neighbouring column at their edge (ch10-168, ch12-033,
  // ch63-005, ch9b-050). A cut of running text in one column (col 0 or 1, no table cell in it - a table's borders run past its
  // text) now ends 2.5pt past its widest line on the side facing the other column, so nothing from that column fits in; the
  // outer side (change bars, margin marks) is left as it was.
  const words = inside.filter(it => it.t);
  const fl = model.F == null ? Infinity : model.F;
  if ((seg.col === 0 || seg.col === 1) && model.g != null && words.length && !words.some(it => it.i >= fl)) {
    if (seg.col === 0) { const r = Math.max(...words.map(it => it.x + it.w)) + 2.5; if (r < x1 && r > model.g - 30) x1 = r; }
    else { const l = Math.min(...words.map(it => it.x)) - 2.5; if (l > x0 && l < model.g + 30) x0 = l; }
  }
  return x0 === seg.x0 && x1 === seg.x1 ? seg : { ...seg, x0, x1 };
}

// ---- (384 one picture) ONE PICTURE PER CITATION. Madison: "why would there be two cropped images? That should be one cropped image ...
// If it's going across the left side of the page and continuing to the right side of the page, don't do two crops, just make it look
// like it's one cropped. Just make it cohesive and make it look like how the code book has it". A citation's segments are cut where
// the book prints them; when there are several (a section that runs from the foot of one column to the head of the next, or onto the
// next page; a text and the full-width table under both columns; a standard's organisation heading and its entry), paint() sets them
// in ONE picture, one under the other, as one column of the book reads: each piece's column moved so its left margin is the first
// piece's, and each piece's first line set under the last line of the piece above at the book's own line pitch (plus its paragraph
// space when the piece starts a new paragraph - a heading, an indented or numbered line, a table, after a short line). The seam is cut
// halfway between the two lines' ink, so nothing of either is lost and nothing from the page between them shows. The layout is
// clip.sheet = { pieces: [{ i, dx, top, bot, gap }] } in pdf points: segment i shown from page y `top` down to `bot`, moved right by dx,
// `gap` points of paper above it. (Pieces cut from one column of one page with lines between are not stitched: the cut runs through
// the lines between - see tableRowClip and countyClip.)
// The lines of a set of text items: baseline, size, ends, whether it starts bold. A superscript stands a little above its line.
function linesIn(items) {
  const ls = [];
  for (const it of items) {
    let l = ls.find(q => Math.abs(q.y - it.y) < 0.45 * Math.max(q.fs, it.h));
    if (!l) { ls.push({ y: it.y, fs: it.h, x0: it.x, x1: it.x + it.w, b: !!it.b }); continue; }
    if (it.h > l.fs) { l.y = it.y; l.fs = it.h; }
    if (it.x < l.x0) { l.x0 = it.x; l.b = !!it.b; }
    l.x1 = Math.max(l.x1, it.x + it.w);
  }
  return ls.sort((a, b) => b.y - a.y);
}
// a column's rhythm on its page: its left margin (where most lines start), its right edge, the pitch of its lines and the extra
// space between paragraphs
function rhythmOf(lines) {
  const out = { margin: null, right: null, pitch: null, para: null };
  if (!lines.length) return out;
  // the left margin: the leftmost place two or more lines start (indented lists and subsections start further in)
  const n = new Map(); for (const l of lines) { const x = Math.round(l.x0); n.set(x, (n.get(x) || 0) + 1); }
  out.margin = Math.min(...[...n].filter(([, c]) => c >= 2).map(([x]) => x).concat([Infinity]));
  if (!isFinite(out.margin)) out.margin = Math.min(...lines.map(l => l.x0));
  const r = lines.map(l => l.x1).sort((a, b) => a - b); out.right = r[Math.floor(0.9 * (r.length - 1))];
  const fs = lines.map(l => l.fs).sort((a, b) => a - b)[lines.length >> 1];
  const d = []; for (let k = 1; k < lines.length; k++) d.push(lines[k - 1].y - lines[k].y);
  const reg = d.filter(v => v >= 0.95 * fs && v <= 1.6 * fs).sort((a, b) => a - b);
  if (reg.length) {
    const lo = reg[0], near = reg.filter(v => v <= lo + 0.6);
    out.pitch = near[near.length >> 1];
    const big = d.filter(v => v > out.pitch + 0.12 * fs && v < 2.3 * out.pitch).sort((a, b) => a - b);
    if (big.length) out.para = big[big.length >> 1] - out.pitch;
  }
  return out;
}
// pageOf(p) -> { items: [{x, y, w, h, b}] (the page's text), g: the gutter or null }
function sheetOf(segs, pageOf) {
  if (segs.length < 2 || segs.some(sg => sg.whole)) return null;
  const P = segs.map(sg => {
    const pg = pageOf(sg.page);
    const lines = linesIn(pg.items.filter(it => centre(it) >= sg.x0 && centre(it) <= sg.x1 && it.y >= sg.y0 && it.y <= sg.y1));
    const col = sg.col === 1 ? 1 : 0;                    // a full-width piece starts where the left column does
    // a column's rhythm from its running text (the book's body type, not a table's cells, set later in the page's stream)
    const inCol = (c) => (it) => (pg.g == null ? it.h >= 7.5 : it.body) && (pg.g == null || (centre(it) < pg.g ? 0 : 1) === c);
    const r = rhythmOf(linesIn(pg.items.filter(inCol(col))));
    // where this piece's column starts on its page. The book is set on one grid: the right column starts 261pt right of the left
    // (243pt of column and 18 of gutter), and the left column's start moves between facing pages. A column whose lines are all
    // indented (subsections, a list) does not show where it starts, so the page's two columns are read together: the left edge is
    // the leftmost start either column shows, the right column's taken back by the grid's step.
    if (pg.g == null) r.colLeft = r.margin;
    else {
      const m0 = rhythmOf(linesIn(pg.items.filter(inCol(0)))).margin, m1 = rhythmOf(linesIn(pg.items.filter(inCol(1)))).margin;
      const step = m0 != null && m1 != null && Math.abs(m1 - m0 - COL_STEP) < 3 ? m1 - m0 : COL_STEP;
      const L = Math.min(m0 == null ? Infinity : m0, m1 == null ? Infinity : m1 - step);
      r.colLeft = isFinite(L) ? (col === 1 ? L + step : L) : r.margin;
    }
    return { sg, lines, ...r };
  });
  // (384.72) a table that runs over two booklet pages (a county table's title and headings on one, the row on the next) is set where the pages print it: a
  // table's rows are not running text, and lining up the left edge of the lines of the two pieces moved the row out of its table (chExhB-801)
  const dxOf = (Q) => (segs.some(sg => sg.tbl) || Q.colLeft == null || P[0].colLeft == null ? 0 : P[0].colLeft - Q.colLeft);
  const pieces = [{ i: 0, dx: dxOf(P[0]), top: segs[0].y1, bot: segs[0].y0, gap: 0 }];
  for (let k = 1; k < P.length; k++) {
    const A = P[k - 1], B = P[k], pa = pieces[k - 1];
    const pb = { i: k, dx: dxOf(B), top: B.sg.y1, bot: B.sg.y0, gap: 0 };
    const a = A.lines[A.lines.length - 1], b = B.lines[0];
    if (B.sg.omit) { pb.dx = 0; pb.gap = OMIT_GAP; pb.omit = true; }       // (384.72) rows of a table left out between two pieces: a gap that says so, the cuts as made
    else if (B.sg.cont) { pb.dx = 0; pb.gap = 0; pb.cont = true; }          // (384 cropfix) the same table on the next page, nothing left out: the painter joins them on one rule
    else if (a && b) {
      const fs = Math.max(a.fs, b.fs);
      const d = [];
      for (const ls of [A.lines.slice(-6), B.lines.slice(0, 6)]) for (let j = 1; j < ls.length; j++) { const v = ls[j - 1].y - ls[j].y; if (v >= 0.95 * fs && v <= 1.6 * fs) d.push(v); }
      const pitch = d.length ? Math.min(...d) : (A.pitch || B.pitch || 1.1 * fs);
      const afresh = b.b || (B.margin != null && b.x0 > B.margin + 2) || (A.right != null && a.x1 < A.right - 1.2 * a.fs) || !!B.sg.table || (B.sg.col === -1 && A.sg.col !== -1);
      const g = pitch + (afresh ? (A.para != null ? A.para : B.para != null ? B.para : 0.4 * fs) : 0);
      // the seam: halfway between a's descenders and b's tallest letters (a table's last row keeps its rule: its piece is shown whole)
      const h = (DSC * a.fs + g - ASC * b.fs) / 2;
      pa.bot = a.fs < 9.4 ? A.sg.y0 : Math.max(A.sg.y0, a.y - h);
      const want = g - (a.y - pa.bot);
      pb.top = Math.min(B.sg.y1, b.y + Math.max(want, (ASC + 0.15) * b.fs));
      pb.gap = Math.max(0, want - (pb.top - b.y));
    } else pb.gap = 4;
    pieces.push(pb);
  }
  return { pieces };
}
// the pitch of the lines around a mark (its paragraph's): what the marker's room above and below is measured against
function pitchAt(items, m) {
  if (!m.fs) return null;
  const base = m.i1 - ASC * m.fs;
  let best = null;
  for (const it of items) {
    if (it.x > m.x1 || it.x + it.w < m.x0) continue;
    const d = Math.abs(it.y - base);
    if (d >= 0.9 * m.fs && d <= 2.2 * m.fs && (best == null || d < best)) best = d;
  }
  return best == null ? 1.15 * m.fs : best;
}
// after a clip is cut: each mark's line pitch, and the sheet that sets several pieces as one picture
function finishClip(r, pageOf) {
  if (!r || !r.ok) return r;
  for (const m of r.marks || []) if (m.fs && !m.lp) m.lp = pitchAt(pageOf(m.page).items, m);
  const sheet = sheetOf(r.segments, pageOf);
  if (sheet) r.sheet = sheet;
  return r;
}
async function bookPages(doc, r, fontBold, cache) {
  const map = new Map();
  for (const p of new Set([...(r.segments || []).map(sg => sg.page), ...(r.marks || []).map(m => m.page)])) {
    const model = await pageModel(doc, p, fontBold, cache);
    const F = model.hasBody ? model.F : model.items.length;
    map.set(p, { items: model.items.filter(it => it.t && inBody(it)).map(it => ({ ...it, body: isBodySize(it) && it.i < F })), g: model.g });
  }
  return (p) => map.get(p) || { items: [], g: null };
}

function textIn(model, segs, onlyMain) {
  // the words a segment shows, in stream order (main flow first, then floats)
  const out = [];
  for (const it of model.items) {
    if (!it.t || !inBody(it)) continue;
    for (const s of segs) {
      const cx = centre(it);
      if (cx >= s.x0 && cx <= s.x1 && it.y >= s.y0 && it.y <= s.y1) { out.push(it.s); break; }
    }
  }
  return out.join(' ');
}

// `find`: one to eight words of the clipping (as printed, capitals and punctuation do not matter) that name the DECIDING words of a long
// passage. The sentence or list item that carries the phrase is highlighted like the heading (mark kind 'cite'), from its first to its last word
// (a line that holds the end of one sentence and the start of the next is painted only up to, or from, the boundary).
// The phrase is searched in the words the clipping shows, in reading order, and must stand on word boundaries; the first match is used.
// Several phrases may be given as an array (use one per page when the sentence runs over a page break). A phrase that is not found marks nothing.
const normFind = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

// The code is set in Times New Roman, which the PDF does not embed, so every glyph advances by the font's standard width (1/1000 em). That is enough to
// say where, inside one line of text, a given character stands: the line's own width carries the extra space of a justified line.
const TNR = {" ":250,"!":333,"\"":408,"#":500,"$":500,"%":833,"&":778,"'":180,"(":333,")":333,"*":500,"+":564,",":250,"-":333,".":250,"/":278,"0":500,"1":500,"2":500,"3":500,"4":500,"5":500,"6":500,"7":500,"8":500,"9":500,":":278,";":278,"<":564,"=":564,">":564,"?":444,"@":921,"A":722,"B":667,"C":667,"D":722,"E":611,"F":556,"G":722,"H":722,"I":333,"J":389,"K":722,"L":611,"M":889,"N":722,"O":722,"P":556,"Q":722,"R":667,"S":556,"T":611,"U":722,"V":722,"W":944,"X":722,"Y":722,"Z":611,"[":333,"\\":278,"]":333,"^":469,"_":500,"`":333,"a":444,"b":500,"c":444,"d":500,"e":444,"f":333,"g":500,"h":500,"i":278,"j":278,"k":500,"l":278,"m":778,"n":500,"o":500,"p":500,"q":500,"r":333,"s":389,"t":278,"u":500,"v":500,"w":722,"x":500,"y":500,"z":444,"{":480,"|":200,"}":480,"~":541,"\u2019":333,"\u2018":333,"\u201c":444,"\u201d":444,"\u2013":500,"\u2014":1000,"\u00b0":400,"\u00bd":750,"\u00bc":750,"\u00be":750,"\u00d7":564,"\u00b1":549,"\u00b2":300,"\u00b3":300,"\u00b5":576,"\u00a7":500,"\u00ae":760,"\u00a9":760,"\u2122":980,"\u2022":350,"\u2026":1000,"\u00a0":250,"\u2212":564,"\u00b7":333};
const TNR_B = Object.assign({}, TNR, {"\"":555,"%":1000,"&":833,"'":278,"+":570,":":333,";":333,"<":570,"=":570,">":570,"?":500,"@":930,"C":722,"E":667,"F":611,"G":778,"H":778,"I":389,"J":500,"K":778,"L":667,"M":944,"O":778,"P":611,"Q":778,"R":722,"T":667,"W":1000,"Z":667,"^":581,"a":500,"b":556,"d":556,"h":556,"j":333,"k":556,"m":833,"n":556,"p":556,"q":556,"r":444,"t":333,"u":556,"{":394,"|":220,"}":394,"~":520,"\u201c":500,"\u201d":500,"\u00d7":570,"\u00ae":747,"\u00a9":747,"\u2122":1000,"\u2212":570});
function glyphXs(it) {
  const s = it.s, size = it.h, tab = it.b ? TNR_B : TNR;
  let nat = 0, sp = 0;
  for (let i = 0; i < s.length; i++) { nat += size * (tab[s[i]] || 500) / 1000; if (s[i] === ' ') sp++; }
  const base = 1.0045;                                             // the PDF's glyphs run a little wider than the nominal widths
  const extra = it.w - nat * base;
  const per = extra > 0.6 && sp > 0 ? extra / sp : 0;              // a justified line spreads the rest over its spaces
  const k = per ? base : (nat > 0 ? it.w / nat : 1);
  const xs = [];
  let x = it.x;
  for (let i = 0; i < s.length; i++) { xs.push(x); x += size * (tab[s[i]] || 500) / 1000 * k + (s[i] === ' ' ? per : 0); }
  xs.push(x);
  return xs;
}
// Where one sentence stops and the next starts inside one run of text: [{ end, start }] (end = just after the closing punctuation, start = first
// character of the next sentence). A list number ("5." / "2.1." / "a.") begins an item and is not the end of a sentence.
const SENT = /[.;:!?]["”')\]]*(\s+)(?=[A-Z“"(]|\d+\.\s)/g;
const NOT_END = /(?:^|\s)(?:U\.S|No|Nos|Fig|Figs|Inc|Co|Ltd|vs|St|Dr|Mr|Mrs)\.$/;
function sentBounds(s) {
  const out = [];
  SENT.lastIndex = 0;
  for (let m; (m = SENT.exec(s));) {
    const start = m.index + m[0].length, end = start - m[1].length;
    const head = s.slice(0, end), tokAt = head.search(/\S+$/), tok = head.slice(tokAt);
    if (/^\(?(?:\d{1,2}(?:\.\d{1,2})*|[a-z])[.)]$/.test(tok) && (head.slice(0, tokAt).trim() === '' || (out.length && out[out.length - 1].start === tokAt))) continue;      // ("903.3.1.1." is a section number, not a list number)
    if (NOT_END.test(head)) continue;
    out.push({ end, start });
  }
  return out;
}
const LABEL_START = /^\s*(?:\d{1,2}(?:\.\d{1,2})*\.|\([a-z0-9]{1,3}\)|[a-z]\.)\s/;       // a line that opens with a list number ("5.", "2.1.", "(a)") starts a new item
function findMarks(model, segs, find) {
  const arr = [];
  for (const it of model.items) {
    if (!it.t || !inBody(it)) continue;
    const cx = centre(it);
    if (segs.some(s => cx >= s.x0 && cx <= s.x1 && it.y >= s.y0 && it.y <= s.y1)) arr.push(it);
  }
  let stream = '';
  const spans = [];
  for (const it of arr) {
    const n = normFind(it.s);
    if (!n) { spans.push({ it, a: stream.length, b: stream.length, empty: true }); continue; }       // a lone full stop or comma: no words, but it can end a sentence
    if (stream) stream += ' ';
    spans.push({ it, a: stream.length, b: stream.length + n.length });
    stream += n;
  }
  const toks = (it) => { const t = [], re = /[a-z0-9]+/g, low = it.s.toLowerCase(); for (let m; (m = re.exec(low));) t.push([m.index, m.index + m[0].length]); return t; };
  const spaces = (str) => { let n = 0; for (let i = 0; i < str.length; i++) if (str[i] === ' ') n++; return n; };
  const out = [];
  for (const ph of [].concat(find)) {
   try {                                                              // a highlight is a help: whatever goes wrong with it, the clipping itself is shown as before
    const q = normFind(ph);
    if (!q) continue;
    // a word the book breaks over two lines ("occu-" / "pied") stands in the stream as two words: any word of the phrase may match its two halves
    const alt = (w) => { const a = [w]; for (let k = 2; k <= w.length - 2; k++) a.push(w.slice(0, k) + ' ' + w.slice(k)); return a.join('|'); };
    const mm = new RegExp('(?:^| )((?:' + q.split(' ').map(alt).join(') (?:') + '))(?= |$)').exec(stream);
    if (!mm) continue;
    const at = mm.index + (mm[0][0] === ' ' && mm[0] !== mm[1] ? 1 : 0), ql = mm[1].length;
    let lo = -1, hi = -1;
    spans.forEach((sp, k) => { if (!sp.empty && sp.a < at + ql && sp.b > at) { if (lo < 0) lo = k; hi = k; } });
    // where the phrase starts and stops inside the text of its first and last run
    const rs = toks(spans[lo].it)[spaces(stream.slice(spans[lo].a, at))][0];
    const re = toks(spans[hi].it)[spaces(stream.slice(spans[hi].a, at + ql))][1];
    // the whole sentence or list item: a line that stops without closing punctuation runs on into the next line (up to seven lines each way)
    const ends = (sp) => /[.;:!?]["”')\]]*$/.test(sp.it.s.trim()) || short(sp);
    // (384.72) A LINE THAT STOPS SHORT OF THE COLUMN'S EDGE ENDS ITS ITEM. The book's running text is justified: every line but the last of an item runs to the
    // right edge, so a line that is more than an em short of it (and is the last on its baseline) is the end of a list item, whatever its last character is -
    // the items of a list of short names ("Baskets", "Belting: canvas and leather", "Beverages over 16-percent alcohol content") carry no full stop, and the
    // rule that a line without one runs on into the next marked up to fourteen items for one (ch2-618), or three neighbours with it (ch2-610)
    const short = (sp) => {
      const seg = segs.find(g => centre(sp.it) >= g.x0 && centre(sp.it) <= g.x1 && sp.it.y >= g.y0 && sp.it.y <= g.y1);
      if (!seg) return false;
      const here = arr.filter(o => o.s.trim() && centre(o) >= seg.x0 && centre(o) <= seg.x1 && o.y >= seg.y0 && o.y <= seg.y1);
      const hs = here.map(o => o.h).sort((a, b) => a - b), med = hs[hs.length >> 1];
      if (!(sp.it.h >= 0.9 * med)) return false;                       // a raised or lowered figure ("m 2") is not the end of a line
      let right = -Infinity, last = true;
      for (const o of here) {
        if (o.h < 0.9 * med) continue;
        right = Math.max(right, o.x + o.w);
        if (Math.abs(o.y - sp.it.y) < 2.5 && o.x > sp.it.x + 0.5) last = false;
      }
      return last && right - (sp.it.x + sp.it.w) > 1.0 * sp.it.h;
    };
    const below = (a, b) => (a.it.y - b.it.y > -5 && a.it.y - b.it.y <= 22)     // b follows a: further along the same line (a superscript may sit a little higher), or the next line under it (same column)
      || (b.it.x > a.it.x + a.it.w && b.it.y - a.it.y > 150);                    // or the first line of the next column (to the right, far higher up the page)
    // a line of a table (a label and its value far apart on the same baseline) is a row, not running text: it never runs on into the next line.
    // Justified running text also has wide gaps, but then every gap in the line is wide; a table row has one dominant gap.
    const rowLike = (sp) => {
      const seg = segs.find(g => centre(sp.it) >= g.x0 && centre(sp.it) <= g.x1 && sp.it.y >= g.y0 && sp.it.y <= g.y1);
      const mates = arr.filter(o => o.s.trim() && Math.abs(o.y - sp.it.y) < 2.5 && (!seg || (centre(o) >= seg.x0 && centre(o) <= seg.x1))).sort((a, b) => a.x - b.x);
      const gaps = [];
      for (let k = 1; k < mates.length; k++) gaps.push(mates[k].x - (mates[k - 1].x + mates[k - 1].w));
      gaps.sort((a, b) => b - a);
      return gaps.length > 0 && (gaps[0] >= 24 || (gaps[0] >= 14 && gaps.length > 1 && gaps[1] < 0.5 * gaps[0]));
    };
    let cutL = null, cutH = null;                                  // the boundary (inside one run) where the sentence starts / stops
    // (384.56) nor is a CELL of a table (a float, set at 9 pt: "1 month") running text: it is the cell and no more - the sentence rules would run it on into the next row's label
    const cellLike = (sp) => model.hasBody && sp.it.i >= model.F && sp.it.h >= 8.6;
    if (!spans.slice(lo, hi + 1).some(sp => rowLike(sp) || cellLike(sp))) {
      // (the limits count lines, not runs: a justified line is cut into one run per word)
      const bl = sentBounds(spans[lo].it.s).filter(x => x.start <= rs).pop();
      if (bl) cutL = { k: lo, b: bl };
      else {
        for (let n = 0, lines = 0; n < 160 && lo > 0 && !ends(spans[lo - 1]) && below(spans[lo - 1], spans[lo]); n++) {
          const newLine = Math.abs(spans[lo - 1].it.y - spans[lo].it.y) >= 5;
          if (newLine && (LABEL_START.test(spans[lo].it.s) || ++lines > 7)) break;
          lo--;
          const bs = sentBounds(spans[lo].it.s);
          if (bs.length) { cutL = { k: lo, b: bs[bs.length - 1] }; break; }
        }
      }
      const bh = sentBounds(spans[hi].it.s).find(x => x.end >= re);
      if (bh) cutH = { k: hi, b: bh };
      else if (!ends(spans[hi])) {
        for (let n = 0, lines = 0; n < 160 && hi + 1 < spans.length && below(spans[hi], spans[hi + 1]); n++) {
          const newLine = Math.abs(spans[hi + 1].it.y - spans[hi].it.y) >= 5;
          if (newLine && (LABEL_START.test(spans[hi + 1].it.s) || ++lines > 7)) break;
          hi++;
          const bs = sentBounds(spans[hi].it.s);
          if (bs.length) { cutH = { k: hi, b: bs[0] }; break; }
          if (ends(spans[hi])) break;
        }
      }
    }
    // one band per line: the runs of a line are joined (a justified line is cut into one run per word, and the spaces between them must be marked too)
    const bands = [];
    for (let k = lo; k <= hi; k++) {
      const it = spans[k].it, r = rectOf(it);
      let xs = null, a = 0, b = it.s.length;
      const mid = (bd) => { xs = xs || glyphXs(it); return (xs[bd.end] + xs[bd.start]) / 2; };   // the middle of the space between two sentences
      if (cutL && cutL.k === k) { r.x0 = mid(cutL.b); a = cutL.b.start; }
      if (cutH && cutH.k === k) { r.x1 = mid(cutH.b); b = cutH.b.end; }
      const text = it.s.slice(a, b);
      const cl = !!(cutL && cutL.k === k), cr = !!(cutH && cutH.k === k);        // (cl / cr: this edge is a cut inside a line, not the end of the line)
      inkMark(r, it.y, it.h);
      const last = bands[bands.length - 1];
      // (384.71) A STACKED FRACTION IS ONE RUN OF THE LINE. The raised numerator, the slash and the lowered denominator ("1" / "/" / "32", the figures 0.6 of
      // the slash's size, the first 3.6 pt up and the last 2.2 pt down) stand more than 5 pt apart by their middles, so the test below split the lowered
      // figures off as a band of their own - which then took a descender's room under them (the room a letter's tail would have) and the gold stood 1 pt
      // low round the fraction (ch22-014's 1/32). A small figure that touches the run before it and overlaps its height is part of that run.
      const small = (a, b) => Math.min(a, b) < 0.8 * Math.max(a, b);
      const stacked = !!last && r.x0 >= last.x0 && r.x0 - last.x1 <= 1.5 && small(r.fs, last.fmax) && r.y0 < last.y1 && r.y1 > last.y0;
      if (last && ((Math.abs((last.i0 + last.i1) / 2 - (r.i0 + r.i1) / 2) < 5 && r.x0 >= last.x0 && r.x0 - last.x1 <= 20) || stacked)) {
        last.x1 = Math.max(last.x1, r.x1); last.y0 = Math.min(last.y0, r.y0); last.y1 = Math.max(last.y1, r.y1); last.text += ' ' + text; last.cl = last.cl || cl; last.cr = last.cr || cr;
        last.fmax = Math.max(last.fmax, r.fs);
        last.its.push(it);
      } else bands.push({ ...r, text, cl, cr, its: [it], fmax: r.fs });
    }
    // a line's ink: its text's - a raised or lowered small figure ("1 1/4", "m 2") reaches only as far as its own figures, from its
    // own baseline up, so it does not stretch the line's marker
    for (const b of bands) {
      const H = Math.max(...b.its.map(it => it.h));
      let i0 = Infinity, i1 = -Infinity;
      for (const it of b.its) {
        const small = it.h < 0.8 * H;
        i0 = Math.min(i0, small ? it.y : it.y - DSC * it.h); i1 = Math.max(i1, it.y + ASC * it.h);
      }
      b.i0 = i0; b.i1 = i1; b.fs = H; b.y0 = i0 - 0.12 * H; b.y1 = i1 + 0.12 * H;
      delete b.its; delete b.fmax;
    }
    const cell = spans.slice(lo, hi + 1).every(cellLike);             // (384 cropfix) the phrase is a table cell (or cells): cellRows can make it its row
    for (const b of bands) out.push({ page: model.p, ...b, kind: 'cite', ...(cell ? { cell: true } : {}) });
   } catch (e) { /* no highlight for this phrase */ }
  }
  // two phrases that fall on the same line (or touch) are one painted band: no stripe is painted twice
  const merged = [];
  for (const m of out) {
    const hit = merged.find(o => Math.abs((o.y0 + o.y1) / 2 - (m.y0 + m.y1) / 2) < 5 && m.x0 <= o.x1 + 3 && m.x1 >= o.x0 - 3);
    if (!hit) { merged.push({ ...m }); continue; }
    const before = m.x0 < hit.x0;
    if (before) hit.cl = m.cl; else if (m.x0 === hit.x0) hit.cl = hit.cl && m.cl;
    if (m.x1 > hit.x1) hit.cr = m.cr; else if (m.x1 === hit.x1) hit.cr = hit.cr && m.cr;
    hit.x0 = Math.min(hit.x0, m.x0); hit.x1 = Math.max(hit.x1, m.x1); hit.y0 = Math.min(hit.y0, m.y0); hit.y1 = Math.max(hit.y1, m.y1);
    hit.i0 = Math.min(hit.i0, m.i0); hit.i1 = Math.max(hit.i1, m.i1); hit.fs = Math.max(hit.fs, m.fs); hit.cell = !!(hit.cell && m.cell);
    if (!hit.text.includes(m.text)) hit.text = before ? m.text + ' ' + hit.text : hit.text + ' ' + m.text;
  }
  return merged;
}

function allText(model) {
  return model.items.filter(it => it.t && inBody(it)).map(it => it.s).join(' ');
}

function wholePageSeg(model) {
  return { page: model.p, x0: 0, x1: model.view ? model.view[2] : 612, y0: 0, y1: model.view ? model.view[3] : 792, col: -2, whole: true, rotation: model.rot };
}

// A banner heading ("CHAPTER 10", "APPENDIX B", "SECTION 3304") is centred and carries its NAME on the bold line(s) right under it
// ("MEANS OF EGRESS"), centred on the same axis. The reader looks for the name, so the whole block is what gets marked:
// -> [{x, y, w, h}], one rectangle per line, the banner line first.
function bannerLines(items, k0) {
  const a = items[k0];
  const lines = [{ x: a.x, y: a.y, w: a.w, h: a.h }];
  const cx = centre(a);
  for (let k = k0 + 1, n = 0; k < items.length && n < 16 && lines.length < 4; k++, n++) {
    const it = items[k];
    if (!it.t) continue;
    if (!it.b || !inBody(it)) break;
    const last = lines[lines.length - 1];
    if (Math.abs(it.y - last.y) < 2.5) {                       // same baseline: more of the same line
      const x0 = Math.min(last.x, it.x), x1 = Math.max(last.x + last.w, it.x + it.w);
      last.x = x0; last.w = x1 - x0; last.h = Math.max(last.h, it.h);
      continue;
    }
    const dy = last.y - it.y;
    if (dy < 6 || dy > 30 || Math.abs(centre(it) - cx) > 6 || NEWHEAD.test(it.t)) break;
    lines.push({ x: it.x, y: it.y, w: it.w, h: it.h });
  }
  return lines;
}
// ---- hidden names (optional pointer key `blur`): the picture of a definition (without its term) or of a chapter opening (without its number and name).
// computeClip returns clip.hide = [{page,x0,x1,y0,y1}] and clip.hiddenText = the words under those rectangles; paint(..., { blur: true }) pixelates the
// rectangles; paint() without the option shows the page as printed (after the student has answered).
function termLines(items, k) {                                   // the bold term of a definition: the first line and up to two wrapped bold lines
  const a = items[k];
  const lines = [];
  let x1 = a.x + a.w, last = k;
  for (let j = k + 1; j < items.length; j++) {
    const it = items[j];
    if (!it.t) { if (Math.abs(it.y - a.y) < 2.5) continue; break; }
    if (!it.b || Math.abs(it.y - a.y) > 2.5) break;
    x1 = Math.max(x1, it.x + it.w); last = j;
  }
  lines.push({ x: a.x, y: a.y, w: x1 - a.x, h: a.h });
  let y = a.y;
  for (let more = 0; more < 2; more++) {
    let m = last + 1;
    while (m < items.length && !items[m].t) m++;
    if (m >= items.length) break;
    const it = items[m], dy = y - it.y;
    if (!(it.b && dy >= 6 && dy <= 16 && it.x <= a.x + 2 && inBody(it))) break;
    let e = it.x + it.w, l2 = m;
    for (let j = m + 1; j < items.length; j++) {
      const u = items[j];
      if (!u.t) { if (Math.abs(u.y - it.y) < 2.5) continue; break; }
      if (!u.b || Math.abs(u.y - it.y) > 2.5) break;
      e = Math.max(e, u.x + u.w); l2 = j;
    }
    if (NEWHEAD.test(it.t)) break;
    lines.push({ x: it.x, y: it.y, w: e - it.x, h: it.h }); last = l2; y = it.y;
  }
  return lines;
}
async function hideInfo(doc, loc, fontBold, cache) {
  if (!loc.start || (loc.kind !== 'def' && loc.kind !== 'banner')) return null;
  const model = await pageModel(doc, loc.start.page, fontBold, cache);
  if (model.rot) return null;
  const items = model.items, k = loc.start.i;
  if (!items[k]) return null;
  const lines = loc.kind === 'banner' ? bannerLines(items, k) : termLines(items, k);
  const hide = [], hiddenText = [];
  for (const ln of lines) {
    const r = { page: loc.start.page, x0: ln.x - 2, x1: ln.x + ln.w + 2, y0: ln.y - 0.4 * ln.h, y1: ln.y + 1.05 * ln.h };
    hide.push(r);
    for (const it of items) if (it.t && it.y >= r.y0 - 1 && it.y <= r.y1 && centre(it) >= r.x0 && centre(it) <= r.x1) hiddenText.push(it.t);
  }
  return { hide, hiddenText };
}
// ---- the hint picture (optional, for a question whose keyed answer is a number printed in the cited code): the same clipping with every printed
// copy of that number blurred, so the reader sees the code around the answer but not the answer.
// answerNumbers(q) -> the numbers of the keyed option as digit strings ([] when the question has no such answer: a name, a group such as "A-2", a count that is not printed).
// hideAnswer(doc, clip, nums, opts) -> { hide:[{page,x0,x1,y0,y1}], hiddenText:[...] } or null. null = the number cannot be hidden with certainty (it is spelled across two
// text runs, the clipping is a whole page, there are too many copies, or one stays readable) and then NO hint is offered. It checks its own work: after the
// rectangles are laid, the text that stays visible is searched again for the number, as digits and as words.
const HINT_UNITS = new Set(('feet foot inches inch gallons gallon square cubic hours hour minutes minute seconds second days day months month years year percent pounds pound per to by and '
  + 'watt psi gpm ppm volts tons fluid ounces quart footcandle footcandles stories net times wide long at least no more than up the past l lbs ft').split(' '));
export function answerNumbers(q) {
  if (!q || q.type !== 'content' || !q.options || !q.options[q.answer]) return [];
  const o = String(q.options[q.answer]);
  if (q.kind === 'definition') return [];                               // the answer is a term, not a quantity
  if (/\b[A-Za-z]{1,2}[-–]\d/.test(o)) return [];                       // "Group A-2", "R-3": the number is part of a name
  // only a plain quantity ("18 inches", "at least 90 minutes", "$200 to $500", "25 percent"): every word that is not a number is a unit or a connecting word
  const left = o.toLowerCase().replace(/°\s*[fc]\b/g, ' ').replace(/[\d.,/$%–()-]+/g, ' ').split(/\s+/).filter(Boolean);
  if (left.length > 6 || !left.every(w => HINT_UNITS.has(w))) return [];
  const nums = (o.replace(/(\d),(?=\d{3}(?!\d))/g, '$1').match(/\d+(?:\.\d+)?/g) || []).filter((n, i, a) => a.indexOf(n) === i);
  return nums.length <= 3 ? nums : [];
}
const HINT_ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
function numberPatterns(n) {
  const pats = [];
  if (/^\d+$/.test(n)) {
    const grouped = n.length > 3 ? n.replace(/\B(?=(\d{3})+$)/g, ',?') : n;
    pats.push('(?<![\\d.,])' + grouped + '(?!\\d|[.,]\\d)');
    const v = Number(n);
    let w = null;
    if (v >= 1 && v < 10) w = HINT_ONES[v];
    else if (v >= 10 && v < 20) w = ONES[v];
    else if (v >= 20 && v < 100) w = TENS[Math.floor(v / 10)] + (v % 10 ? '[-\\s]*' + ONES[v % 10] : '');
    else if (v >= 100 && v <= 900 && v % 100 === 0) w = ONES[v / 100] + '[-\\s]*hundred';
    if (w) pats.push('(?<![A-Za-z])' + w + '(?![A-Za-z])');
  } else pats.push('(?<![\\d.,])' + n.replace('.', '\\.') + '(?!\\d)');
  return pats.map(s => new RegExp(s, 'gi'));
}
export async function hideAnswer(doc, clip, nums, opts = {}) {
  if (!clip || !clip.ok || !nums || !nums.length) return null;
  if (clip.segments.some(sg => sg.whole)) return null;
  const res = nums.flatMap(numberPatterns);
  const hide = [], hiddenText = [];
  const rest = [];
  const pages = [...new Set(clip.segments.map(sg => sg.page))];
  for (const pg of pages) {
    const page = await doc.getPage(pg);
    const tc = await page.getTextContent();
    const its = tc.items.filter(it => it.str && it.str.trim()).map(it => ({ s: it.str, x: it.transform[4], y: it.transform[5], w: it.width, h: it.height || Math.abs(it.transform[3]) || 10 }));
    for (const it of its) {
      if (!clip.segments.some(g => g.page === pg && centre(it) >= g.x0 && centre(it) <= g.x1 && it.y >= g.y0 && it.y <= g.y1)) continue;
      const hit = [];
      for (const re of res) { re.lastIndex = 0; for (let m; (m = re.exec(it.s));) { hit.push([m.index, m.index + m[0].length]); if (!m[0].length) re.lastIndex++; } }
      hit.sort((a, b) => a[0] - b[0]);
      const spans = [];                                              // widen each copy to its whole word ("48-inch", "(48)") so a small drift in the glyph positions cannot leave a digit showing
      for (const [a0, b0] of hit) {
        let a = a0, b = b0;
        while (a > 0 && !/\s/.test(it.s[a - 1])) a--;
        while (b < it.s.length && !/\s/.test(it.s[b])) b++;
        if (spans.length && a <= spans[spans.length - 1][1]) spans[spans.length - 1][1] = Math.max(spans[spans.length - 1][1], b); else spans.push([a, b]);
      }
      if (spans.length) {
        const xs = glyphXs({ ...it, b: false });
        for (const [a, b] of spans) {
          const words = [...it.s.matchAll(/\S+/g)];
          const w0 = words.findIndex(m => m.index <= a && m.index + m[0].length > a), w1 = words.findIndex(m => m.index < b && m.index + m[0].length >= b);
          // snap: where the run stands on the page and which of its words are hidden; paint() finds the real ink of those words and blurs exactly that
          hide.push({ page: pg, x0: xs[a] - 2, x1: xs[b] + 2, y0: it.y - 0.4 * it.h, y1: it.y + 1.05 * it.h, snap: { ix0: it.x, ix1: it.x + it.w, nw: words.length, w0, w1, fs: it.h } });
          hiddenText.push(it.s.slice(a, b));
        }
      }
      let left = '', at = 0;
      for (const [a, b] of spans) { left += it.s.slice(at, a) + ' '; at = b; }
      rest.push(left + it.s.slice(at));
    }
  }
  if (!hide.length || hide.length > 14) return null;
  const seen = rest.join(' ');
  for (const re of res) { re.lastIndex = 0; if (re.test(seen)) return null; }
  return { hide, hiddenText };
}
const headMark = (p, r) => inkMark({ page: p, x0: r.x, x1: r.x + r.w, kind: 'heading' }, r.y, r.h);

// -> { ok, segments:[{page,x0,x1,y0,y1,col}], marks:[{page,x0,x1,y0,y1,kind}], text, pages:[...], truncated }
// segment coordinates are pdf points (origin bottom-left); col -1 = full width, 0 / 1 = left / right column, -2 = whole page.
export async function computeClip(doc, index, loc, ptr, opts = {}) {
  if (!loc.ok) return { ok: false };
  const fontBold = opts.fontBold || (opts.fontBold = new Map());
  const cache = opts.cache || (opts.cache = new Map());
  const done = async (r) => {
    if (r && r.ok && ptr && ptr.rows) await cellRows(doc, r, fontBold, cache);
    return r && r.ok ? finishClip(r, await bookPages(doc, r, fontBold, cache)) : r;
  };
  if (loc.kind === 'table') return done(await tableClip(doc, index, loc, ptr, opts, fontBold, cache));
  if (loc.kind === 'entry') return done(await entryClip(doc, index, loc, ptr, opts, fontBold, cache));
  if (loc.kind === 'figure') return done(await figureClip(doc, index, loc, ptr, fontBold, cache));
  const r = await flowClip(doc, index, loc, ptr, opts, fontBold, cache);
  if (r.ok && ptr && ptr.blur) { try { const h = await hideInfo(doc, loc, fontBold, cache); if (h) { r.hide = h.hide; r.hiddenText = h.hiddenText; } } catch (e) { /* shown unblurred is never a leak: without the rectangles nothing is hidden, so the app must check clip.hide before it shows the picture */ } }
  // (r15) A section's banner cited alone is cut with the start of what it heads, but the whole-page view highlights all of it: the banner and its
  // first subsection through the last of its sub-items and exceptions.
  if (r.ok && loc.lead) {
    try {
      const full = await flowClip(doc, index, { ...loc, lead: 0 }, ptr, opts, fontBold, cache);
      if (full.ok && !full.segments.some(sg => sg.whole)) r.cited = full.segments;
    } catch (e) { /* the whole-page view then highlights the clipping only */ }
  }
  // The clipping stops above an exception (or a table) the question is not about; the whole-page view highlights the whole section, so the
  // full extent is cut once more, without marks, and handed over as `cited` (see highlightPage).
  if (r.ok && (loc.stoppedAtException || loc.stoppedAtTable) && loc.fullEnd !== undefined) {
    try {
      const full = await flowClip(doc, index, { ...loc, end: loc.fullEnd, stoppedAtException: false, stoppedAtTable: false }, { ...ptr, find: null, exception: null }, opts, fontBold, cache);
      if (full.ok && !full.segments.some(sg => sg.whole)) r.cited = full.segments;
    } catch (e) { /* the whole-page view then highlights the clipping only */ }
  }
  return done(r);
}

// ---- figures
// `figure` is the caption as printed under the drawing ("FIGURE D103.1"), `box` = [x0, y0, x1, y1] in pdf points (origin bottom-left) is the part of
// the cited page to show: the whole figure with its caption for a reference, or one drawing without the words that name it for a question's picture.
// The caption has to be on the cited page of the reader's copy: another printing, laid out differently, would be cut at the wrong place, so then nothing
// is cut. Without `box` (or on a sideways page) the page is shown whole with the caption marked.
async function figureClip(doc, index, loc, ptr, fontBold, cache) {
  const p = loc.start.page;
  if (!(p >= 1 && p <= index.numPages)) return { ok: false };
  const model = await pageModel(doc, p, fontBold, cache);
  const want = norm(ptr.figure);
  const cap = model.items.find(it => it.t && it.b && inBody(it) && norm(it.t) === want);
  if (!cap) return { ok: false };
  const box = ptr.box;
  if (model.rot || !Array.isArray(box) || box.length !== 4 || !box.every(Number.isFinite) || !(box[2] > box[0] && box[3] > box[1])) {
    return { ok: true, segments: [wholePageSeg(model)], marks: model.rot ? [] : [headMark(p, cap)], text: allText(model), pages: [p], truncated: false };
  }
  const seg = { page: p, x0: box[0], x1: box[2], y0: box[1], y1: box[3], col: -1, figure: true };
  return { ok: true, segments: [seg], marks: [], cited: [seg], text: textIn(model, [seg]), pages: [p], truncated: false };
}

// ---- sections and definitions: the text from the heading to the next heading, column by column
async function flowClip(doc, index, loc, ptr, opts, fontBold, cache) {
  const maxPages = opts.maxPages || 4;
  const sp = loc.start.page;
  const ep = loc.end ? loc.end.page : sp;
  const last = loc.lead ? sp : Math.min(ep, sp + maxPages - 1, index.numPages);
  const segments = [], marks = [], textParts = [], pages = [];
  for (let p = sp; p <= last; p++) {
    const model = await pageModel(doc, p, fontBold, cache);
    if (model.rot) { segments.push(wholePageSeg(model)); pages.push(p); textParts.push(allText(model)); continue; }
    // a page of nothing but a table belongs to this section only when its caption carries this section's number
    // (the typesetter may park another section's table after this section's last lines)
    if (p > sp && !model.hasBody && loc.kind === 'sec' && loc.token && !loc.composite) {
      const cap = model.items.find(it => it.t && inBody(it) && TABLE.test(it.t));
      const ct = cap ? TABLE.exec(cap.t)[1] : null;
      if (ct && !(ct === loc.token || ct.startsWith(loc.token + '.') || ct.startsWith(loc.token + '('))) continue;
    }
    const { items, g } = model;
    const mainEnd = model.hasBody ? model.F : items.length;
    const a = p === sp ? loc.start.i : 0;
    const b = loc.end && p === ep ? loc.end.i : items.length;
    let slice = [];
    for (let k = a; k < Math.min(b, mainEnd); k++) { const it = items[k]; if (it.t && inBody(it)) slice.push(it); }
    if (!slice.length) continue;
    // `lead` (a banner cited alone, see locate): the banner and the first loc.lead lines under it in the banner's column - ending on a sentence's
    // end where one ends from the third line on (or within three lines past the limit). Cut short, the clipping ends at its last line, not at
    // the next heading.
    let leadCut = false;
    if (loc.lead && p === sp) {
      const side = g == null ? -1 : (centre(loc.start) < g ? 0 : 1);
      const same = (it) => side < 0 || (centre(it) < g ? 0 : 1) === side;
      const floor = Math.min(...bannerLines(items, loc.start.i).map(l => l.y)) - 2;
      const rows = [];                                                     // the lines under the banner: baseline, right end, the words there
      for (const it of slice) {
        if (it.y >= floor || !same(it)) continue;
        const r = rows.find(q => Math.abs(q.y - it.y) < 2.5);
        if (!r) rows.push({ y: it.y, x1: it.x + it.w, end: it.t });
        else if (it.x + it.w > r.x1) { r.x1 = it.x + it.w; r.end = it.t; }
      }
      rows.sort((u, v) => v.y - u.y);
      let n = Math.min(rows.length, loc.lead);
      if (n < rows.length) {                                              // a sentence's end: the last within the limit, else one just past it
        const ends = (k) => /\.$/.test(rows[k - 1].end);
        let k = n; while (k >= 3 && !ends(k)) k--;
        if (k >= 3) n = k;
        else { let found = false; for (k = n + 1; k <= Math.min(rows.length, loc.lead + 3); k++) if (ends(k)) { n = k; found = true; break; }
          // (r15) a picture never ends inside a sentence: on past the limit, to the first line that ends one (the paragraph's end)
          if (!found) for (k = loc.lead + 4; k <= Math.min(rows.length, loc.lead + 14); k++) if (ends(k)) { n = k; break; } }
      }
      if (n < rows.length || slice.some(it => !same(it))) {
        const cut = n ? rows[n - 1].y - 0.5 : floor;
        slice = slice.filter(it => same(it) && it.y >= cut);
        leadCut = true;
      }
    }
    const endHere = loc.end && p === ep && !leadCut ? loc.end : null;
    let mode = 'mixed';
    const cols = [[], []];
    if (g != null) {
      mode = 'columns';
      for (const it of slice) {
        if (it.x < g - 2 && it.x + it.w > g + 2 && isBodySize(it)) { mode = 'mixed'; break; }
        cols[centre(it) < g ? 0 : 1].push(it);
      }
      // a banner that straddles the gutter ("CHAPTER 10", "APPENDIX B") opens a page whose top is full width
      // (title, user note); cutting it into two columns would split the heading and every line of the note in half
      if (loc.kind === 'banner' && p === sp && loc.start.x < g - 2 && loc.start.x + loc.start.w > g + 2) mode = 'mixed';
    }
    const floats = items.filter(it => it.i >= mainEnd && it.t && inBody(it));
    const segs = [];
    if (mode === 'columns') {
      // The tables of this page that lie in the clipping's range. A table that belongs to the section (its caption number is the section's, or a
      // sub-number of it) is shown with the section; a table of another section, parked on the page by the typesetter, is left out. A table
      // that runs across both columns is cut out of the page as one full-width piece (cutting it by column would show half of it).
      const capsHere = index.heads.filter(h => h[0] === p && h[2] === 'table').map(h => ({ page: h[0], i: h[1], token: h[3], x: h[5], y: h[6], w: h[7], h: h[8] }));
      const inRange = (h) => (p !== sp || h.i > loc.start.i) && !(loc.end && p === ep && h.i >= loc.end.i);
      const mineTok = (tok) => !!loc.token && (tok === loc.token || tok.startsWith(loc.token + '.') || tok.startsWith(loc.token + '('));
      const wide = [], foreign = [], ownCol = [];
      for (const h of capsHere) {
        const rt = tableRect(model, h, capsHere, capsHere);
        const stop = loc.stoppedAtTable && endHere && h.i === endHere.i;     // stopAtTable: this table is the one the clipping stops above
        // a full-width table is typeset below both columns, so its caption comes after every column heading in the stream: on the page where
        // the section ends it still counts as the section's by its number; every table that is not the section's is left out wherever it sits
        const own = !stop && mineTok(h.token) && (inRange(h) || (p === ep && rt.col === -1));
        if (rt.col === -1) wide.push({ r: rt, own }); else if (own) ownCol.push(rt); else foreign.push(rt);
      }
      const within = (it, r) => centre(it) >= r.x0 && centre(it) <= r.x1 && it.y <= r.y1 + 1 && it.y >= r.y0 - 1;
      const skipFloat = (it) => wide.some(w => within(it, w.r)) || foreign.some(r => within(it, r));
      cols.forEach((arr, c) => {
        if (!arr.length) return;
        let r = null;
        for (const it of arr) r = union(r, rectOf(it));
        let x0 = c === 0 ? COL_L : g - 4, x1 = c === 0 ? g + 4 : COL_R;
        let y0 = r.y0, y1 = r.y1;
        // the end heading sits in this column: the section reaches up to it (tables between are part of it)
        const endCol = endHere ? (centre(endHere) < g ? 0 : 1) : -1;
        if (endHere && endCol === c && !loc.stoppedAtTable) y0 = Math.min(y0, top(endHere) + 2);
        else {                                                // otherwise: also the table cells that hang below the last line
          const fl = floats.filter(it => centre(it) >= x0 && centre(it) <= x1 && it.y <= y0 + 1 && !skipFloat(it) && ownCol.some(r => within(it, r)) && !(p === sp && it.y > loc.start.y && centre(loc.start) >= x0 && centre(loc.start) <= x1));
          for (const it of fl) y0 = Math.min(y0, bottom(it) - 1);
        }
        // the cut between the columns is made in the empty band of these rows (a table of the other column may reach over the page's gutter)
        const yLo = Math.max(y0 - 2, BODY_BOTTOM), yHi = y1 + 2, xb = c === 0 ? x1 : x0;
        if (items.some(it => it.t && inBody(it) && it.y <= yHi && it.y >= yLo && it.x < xb - 1 && it.x + it.w > xb + 1)) {
          const gl = gutterNear(model, yHi, yLo, g);
          if (gl != null) { x0 = c === 0 ? COL_L : gl - 4; x1 = c === 0 ? gl + 4 : COL_R; }
        }
        segs.push({ page: p, x0, x1, y0: Math.max(y0 - 2, BODY_BOTTOM), y1: y1 + 2, col: c });
      });
      // a table of the section that runs across both columns and lies below its text: one more piece, full width
      const textBottom = Math.min(...segs.map(sg => sg.y0));
      for (const w of wide) {
        if (!w.own) continue;
        if (p === sp && w.r.y1 > loc.start.y) continue;                                   // above the section's heading: not part of it
        if (w.r.y1 > textBottom + 3) continue;                                           // inside the text, not below it: left as it was
        segs.push({ page: p, x0: w.r.x0, x1: w.r.x1, y0: w.r.y0, y1: w.r.y1, col: -1, table: true });
      }
    } else {
      let r = null;
      for (const it of slice) r = union(r, rectOf(it));
      segs.push({ page: p, x0: COL_L, x1: COL_R, y0: Math.max(r.y0 - 2, BODY_BOTTOM), y1: r.y1 + 2, col: -1 });
    }
    // (r15) a block of running text is highlighted to its column's right edge, whatever its last line holds (see highlightPage)
    const mainRight = (sg) => { let r = null; for (const it of items) if (it.t && inBody(it) && isBodySize(it) && it.i < mainEnd && centre(it) >= sg.x0 && centre(it) <= sg.x1 && it.x + it.w <= sg.x1 + 2 && (r == null || it.x + it.w > r)) r = it.x + it.w; return r; };
    for (const s of segs) { const t = trimEdges(model, s); if (!s.table) { const xr = mainRight(t); if (xr != null) t.xr = xr; } segments.push(t); }
    textParts.push(textIn(model, segs));
    pages.push(p);
    if (ptr && ptr.find) for (const m of findMarks(model, segs, ptr.find)) marks.push(m);
    if (p === sp) {
      if (loc.kind === 'banner') for (const ln of bannerLines(items, loc.start.i)) marks.push(headMark(p, ln));   // banner and name
      else marks.push(headMark(p, loc.start));
    }
    if (ptr && ptr.exception) {
      const num = (String(ptr.exception).match(/\d+/) || [])[0];
      let seenExc = false;
      for (const it of slice) {
        if (it.b && EXC.test(it.t)) { marks.push(inkMark({ page: p, ...rectOf(it), kind: 'exception' }, it.y, it.h)); seenExc = true; }
        else if (seenExc && num && it.t === num + '.') { marks.push(inkMark({ page: p, ...rectOf(it), kind: 'exceptionNumber' }, it.y, it.h)); seenExc = false; }
      }
    }
  }
  return { ok: true, segments, marks, text: textParts.join(' '), pages, truncated: !loc.lead && last < ep };
}

// ---- tables: found by position. The caption is in the text; the cells are floats listed at the end of the page.
function bandOf(model, cap) {
  const g = model.g, cx = centre(cap);
  if (g == null) return 'full';
  if (cx < g - 40) return 'left';
  if (cx > g + 40) return 'right';
  return 'full';
}

function tableRect(model, cap, capsOnPage, headsOnPage) {
  const { items, g } = model;
  const band = bandOf(model, cap);
  const T = top(cap) + 2;
  // the caption's title lines (bold, small) follow it in the stream
  let titleBottom = bottom(cap);
  for (let k = cap.i + 1, n = 0; k < items.length && n < 10; k++) {
    const it = items[k];
    if (!it.t) continue;
    if (!it.b || it.h > 8.6 || it.h < 7.5 || it.y > cap.y + 2 || it.y < cap.y - 55 || TABLE.test(it.t)) break;
    titleBottom = Math.min(titleBottom, bottom(it)); n++;
  }
  let B = BODY_BOTTOM - 1;
  // the next table caption below (same column band) ends this table
  for (const h of capsOnPage) {
    if (h.i === cap.i || h.y >= cap.y - 6) continue;
    const hb = bandOf(model, h);
    if (hb !== band && hb !== 'full' && band !== 'full') continue;
    B = Math.max(B, top(h) + 2);
  }
  // a table of one column may reach a little over the page's gutter (and the other column's tables may too): the cut is made in the
  // empty band between the two columns for these rows, not at the page's average gutter
  let gl = g;
  if (band !== 'full' && g != null) {
    const xb = band === 'right' ? g - 4 : g + 4;
    const straddles = items.some(it => it.t && inBody(it) && it.y <= T && it.y >= B && it.x < xb - 1 && it.x + it.w > xb + 1);
    if (straddles) { const g2 = gutterNear(model, T, B, g); if (g2 != null) gl = g2; }
  }
  const x0 = band === 'right' ? gl - 4 : COL_L, x1 = band === 'left' ? gl + 4 : COL_R;
  // so does the first body-size text line below the table in the band (the text that resumes under it)
  for (const it of items) {
    if (!it.t || !inBody(it) || !isBodySize(it) || it.i >= (model.hasBody ? model.F : items.length)) continue;
    if (it.y >= cap.y - 8) continue;
    const c = centre(it);
    if (c < x0 || c > x1) continue;
    B = Math.max(B, top(it) + 1);
  }
  // members: everything in the rectangle (cells, headings, notes); the rectangle is cut to the lowest member
  let lowest = titleBottom;
  for (const it of items) {
    if (!it.t || !inBody(it)) continue;
    const c = centre(it);
    if (c < x0 || c > x1 || it.y > T || it.y < B) continue;
    if (isBodySize(it) && it.i < (model.hasBody ? model.F : items.length)) continue;
    lowest = Math.min(lowest, bottom(it));
  }
  return { page: model.p, x0, x1, y0: Math.max(lowest - 3, BODY_BOTTOM), y1: T, col: band === 'left' ? 0 : band === 'right' ? 1 : -1 };
}

async function tableClip(doc, index, loc, ptr, opts, fontBold, cache) {
  const maxPages = opts.maxPages || 4;
  const segments = [], marks = [], textParts = [], pages = [];
  const headsOn = (p) => index.heads.filter(h => h[0] === p && h[2] === 'table').map(h => ({ page: h[0], i: h[1], token: h[3], x: h[5], y: h[6], w: h[7], h: h[8] }));
  let truncated = false;
  for (let p = loc.start.page, n = 0; p <= index.numPages; p++, n++) {
    const onPage = headsOn(p);
    const mine = p === loc.start.page ? onPage.filter(h => h.i === loc.start.i) : onPage.filter(h => h.token === loc.token);
    // the question's evidence runs onto the page after the last page that has the caption: show that one page whole
    const wanted = ptr && ptr.pdfPageEnd && p <= ptr.pdfPageEnd && n > 0 && pages.length === n;
    if (!mine.length && !wanted) break;                       // the table does not continue on this page
    if (n >= maxPages) { truncated = true; break; }
    const model = await pageModel(doc, p, fontBold, cache);
    if (!mine.length) { segments.push(wholePageSeg(model)); pages.push(p); textParts.push(allText(model)); continue; }
    if (model.rot) { segments.push(wholePageSeg(model)); pages.push(p); textParts.push(allText(model)); continue; }
    const segs = [];
    for (const cap of mine) segs.push(tableRect(model, cap, onPage, onPage));
    for (const s of segs) segments.push(trimEdges(model, s));
    textParts.push(textIn(model, segs));
    pages.push(p);
    if (p === loc.start.page) marks.push(headMark(p, loc.start));
  }
  // optional `row`: the question is about one row (or a few) of the table: show the caption and column headings, the rows around it and the notes,
  // from the one page that holds the row, with the row marked
  const rows = [].concat(ptr && ptr.row ? ptr.row : []);
  if (rows.length && segments.length) {
    for (const p of pages) {
      const model = await pageModel(doc, p, fontBold, cache);
      if (model.rot) continue;
      const rowClip = await tableRowClip(model, segments.filter(sg => sg.page === p && !sg.whole), headsOn(p).filter(h => h.token === loc.token), rows);
      // (r15) the picture is cut from the page that holds the row; the whole-page view shows - and tints - the whole table, on every page it runs over
      if (rowClip) {
        await tableFindMarks(rowClip.segments, rowClip.marks, ptr, fontBold, cache);
        return { ok: true, ...rowClip, cited: segments.filter(sg => !sg.whole && !sg.figure).map(sg => ({ ...sg, table: true })), pages: pages.slice(), truncated: false };
      }
    }
  }
  await tableFindMarks(segments, marks, ptr, fontBold, cache);
  return { ok: true, segments, marks, text: textParts.join(' '), pages, truncated };

  // (384.56) `find` in a table: the deciding words are a footnote of the table ("f. A 50-percent spacing increase shall be permitted where ...") or a cell, not the
  // caption. They are looked for in what the clipping shows (the notes are inside it: the cut runs on through them) and marked like a section's: the sentence
  // or note that holds them, to its full stop - alone, or beside a marked `row`. A phrase that is not found marks nothing, as for a section.
  async function tableFindMarks(segs, into, ptr, fontBold, cache) {
    if (!ptr || !ptr.find) return;
    for (const p of [...new Set(segs.filter(sg => !sg.whole).map(sg => sg.page))]) {
      const model = await pageModel(doc, p, fontBold, cache);
      if (model.rot) continue;
      for (const m of findMarks(model, segs.filter(sg => sg.page === p && !sg.whole), ptr.find)) into.push(m);
    }
  }
}

// (384 cropfix) A ROW, NOT A CELL. Madison: "Yes, highlight entire rows but ensure it's accurate." A pointer with `rows: true` (IFC_POINTER_PATCH) has each
// `find` phrase that is a table cell (a float of the cells' size: cellLike in findMarks) marked as the whole row the cell is in - from the table's left
// border to its right, the full height of the row (rowFromLabel: a label set on several lines, a value centred beside them) - as a `row` pointer's row is.
// The row is found from the cell: its label is the print furthest left in the table whose middle stands within 0.8 em of the cell's, taken up to the
// label's first line where it wraps (a wrapped line is indented under its first). Two cells of one row (its label and its value) are one row.
// Opt-in per pointer, so a cell that is the answer of a whole column (ch61-022, "regardless of quantity") or of two rows stays a cell.
function labelOfCell(model, m, rect) {
  const fs = Math.max(m.fs || 9, 8.6), cy = (m.i0 + m.i1) / 2;
  let L = null;
  for (const it of model.items) {
    if (!it.t || !inBody(it) || it.h < 0.85 * fs || it.h > 1.3 * fs) continue;
    const c = centre(it);
    if (c < rect.x0 || c > rect.x1 || it.y < rect.y0 || it.y > rect.y1) continue;
    if (Math.abs(it.y + 0.25 * it.h - cy) > 0.8 * fs) continue;
    if (!L || it.x < L.x - 2 || (Math.abs(it.x - L.x) <= 2 && it.y > L.y)) L = it;
  }
  for (let n = 0; L && n < 4; n++) {
    let u = null;
    for (const it of model.items) {
      if (!it.t || !inBody(it) || Math.abs(it.h - L.h) > 0.2 * L.h) continue;
      const c = centre(it);
      if (c < rect.x0 || c > rect.x1 || it.y > rect.y1) continue;
      const dy = it.y - L.y;
      if (dy > 0.5 * L.h && dy <= 1.35 * L.h && it.x < L.x - 1 && it.x >= L.x - 2.4 * L.h && (!u || dy < u.y - L.y)) u = it;
    }
    if (!u) break;
    L = u;
  }
  return L;
}
async function cellRows(doc, r, fontBold, cache) {
  const out = [], done = new Set();
  for (const m of r.marks || []) {
    if (!m.cell) { out.push(m); continue; }
    const cx = (m.x0 + m.x1) / 2, cy = (m.i0 + m.i1) / 2;
    const seg = (r.segments || []).find(sg => !sg.whole && sg.page === m.page && cx >= sg.x0 && cx <= sg.x1 && cy >= sg.y0 && cy <= sg.y1);
    const model = seg ? await pageModel(doc, m.page, fontBold, cache) : null;
    const L = model ? labelOfCell(model, m, seg) : null;
    const h = L ? rowFromLabel(model, L, seg) : null;
    if (!h) { out.push(m); continue; }
    const key = m.page + ':' + L.i;
    if (done.has(key)) continue;
    done.add(key);
    const row = { page: m.page, x0: h.x0, x1: h.x1, i0: h.i0, i1: h.i1, fs: h.fs, kind: 'row', lt: h.lt, lb: h.lb, fromCell: true };
    row.y0 = h.i0 - 0.12 * h.fs; row.y1 = h.i1 + 0.12 * h.fs;
    out.push(row);
  }
  // a mark of something inside a row that is now gold whole (ch22-014's stacked 1/32: its figures are smaller than a cell's, so not a cell) is part of
  // that row: it is not kept as a band of its own beside it
  const rows = out.filter(m => m.fromCell);
  r.marks = out.filter(m => m.fromCell || m.kind !== 'cite' || !rows.some(w => w.page === m.page && (m.x0 + m.x1) / 2 >= w.x0 && (m.x0 + m.x1) / 2 <= w.x1
    && (m.i0 + m.i1) / 2 >= Math.min(w.i0, w.lb != null ? w.lb : w.i0) && (m.i0 + m.i1) / 2 <= Math.max(w.i1, w.lt != null ? w.lt : w.i1)));
}

// the row label (and its factor, on the same line) inside a table rectangle
function findRow(model, want, rect) {
  // (384) THE ROW'S OWN LABEL. A footnote letter raised against a value can spell a short label ("B" and the "b" in "250 b", a row
  // above it): of the matches, the larger print wins (a raised letter is a few points smaller than the cells), then the one further
  // left by more than a little (a row's label is in the first column); otherwise the first in reading order, as before.
  let L = null;
  for (const it of model.items) {
    if (!it.t || !inBody(it)) continue;
    const c = centre(it);
    if (c < rect.x0 || c > rect.x1 || it.y < rect.y0 || it.y > rect.y1) continue;
    const n = norm(it.t);
    if (n && (n === want || (n.length >= 12 && want.startsWith(n)) || (want.length >= 6 && n.startsWith(want)))) {
      if (!L || it.h > L.h + 0.5 || (Math.abs(it.h - L.h) <= 0.5 && it.x < L.x - 2)) L = it;
    }
  }
  if (!L) return null;
  return rowFromLabel(model, L, rect);
}
// a row of a table from its label's first line L (findRow, and a cell found by `find` turned into its row: cellRows)
function rowFromLabel(model, L, rect) {
  let F = null;
  for (const it of model.items) {
    if (!it.t || !inBody(it) || it === L || it.x < L.x + L.w - 1) continue;
    const c = centre(it);
    if (c < rect.x0 || c > rect.x1) continue;
    const dy = Math.abs(it.y - L.y);
    if (dy <= 6 && (!F || dy < Math.abs(F.y - L.y))) F = it;
  }
  const a = rectOf(L), b = F ? rectOf(F) : a;
  const G = F || L;
  // (384 one picture) a footnote letter printed against the label or the value ("50 a, b") is part of the row: the mark takes it in
  let x1 = Math.max(a.x1, b.x1);
  for (const it of model.items) {
    if (!it.t || !inBody(it) || it.h >= 0.8 * G.h) continue;
    for (const o of [L, G]) if (it.x >= o.x + o.w - 0.5 && it.x - (o.x + o.w) <= 3 && it.y > o.y - 0.2 * o.h && it.y < o.y + 0.7 * o.h) x1 = Math.max(x1, it.x + it.w);
  }
  let i0 = Math.min(L.y - DSC * L.h, G.y - DSC * G.h), i1 = Math.max(L.y + ASC * L.h, G.y + ASC * G.h);
  // (384.56) A LABEL SET ON SEVERAL LINES IS ALL OF THE ROW'S LABEL. "Maximum distance of" / "travel to" / "extinguisher" stands on three lines and its
  // value ("75 feet") is centred on the middle one, a whole line below the line the label was found by: the gold then covered the label alone and the row's
  // value stood outside it. The wrapped lines of the label - set a hanging indent in, one line's pitch apart (1.1 em; the next row starts 2.5 em down) - are
  // part of the row's band, so the cells beside any of them are taken in by the pass below. (A label that is centred in its cell is not read this way:
  // the rows of a centred column are the same width, and a line of the next row cannot be told from a line of this one.)
  for (let cur = L, n = 0; n < 4; n++) {
    let nx = null;
    for (const it of model.items) {
      if (!it.t || !inBody(it) || it === cur || it.h < 0.8 * L.h || it.h > 1.2 * L.h) continue;
      const c = centre(it);
      if (c < rect.x0 || c > rect.x1) continue;
      const wrapped = it.x > L.x + 3 && it.x <= L.x + 2.4 * L.h;                  // indented under the label's first line
      const dy = cur.y - it.y;
      if (wrapped && dy > 0.5 * L.h && dy <= 1.35 * L.h && (!nx || dy < cur.y - nx.y)) nx = it;
    }
    if (!nx) break;
    i0 = Math.min(i0, nx.y - DSC * nx.h); cur = nx;
  }
  const x0 = Math.min(a.x0, b.x0);
  // (384) THE WHOLE ROW. The gold ran from the label to the one cell nearest it, so in a table of four columns half the row asked
  // about was marked and half was not. It runs on to the row's last cell now: every line of print to the right of the label whose
  // letters stand a third or more inside the row's band (a row's cells, a value set midway down a row of two lines; the next row's
  // lines lie outside it), with a note letter raised against it. The passes below then take in the rest of a cell of two lines.
  for (const it of model.items) {
    if (!it.t || !inBody(it) || it.x < L.x) continue;
    const c = centre(it);
    if (c < rect.x0 || c > rect.x1) continue;
    const a0 = it.y - DSC * it.h, a1 = it.y + ASC * it.h, ov = Math.min(a1, i1) - Math.max(a0, i0);
    if (ov >= 0.3 * (a1 - a0)) x1 = Math.max(x1, it.x + it.w);
  }
  // (384 one picture) a cell of the row set on two half-lines beside it ("Less than or equal" / "to 6,000" beside "Protected above-")
  // is in the row: a line of print inside the mark's width whose letters stand a third or more within the mark's height is taken in
  // whole, so the gold never slices a word
  for (let pass = 0; pass < 2; pass++) for (const it of model.items) {
    if (!it.t || !inBody(it) || it.x < x0 - 1 || it.x + it.w > x1 + 1) continue;
    const a0 = it.y - DSC * it.h, a1 = it.y + ASC * it.h, ov = Math.min(a1, i1) - Math.max(a0, i0);
    if (ov > 0 && ov >= 0.3 * (a1 - a0) && (a0 < i0 || a1 > i1)) { i0 = Math.min(i0, a0); i1 = Math.max(i1, a1); }
  }
  // (384) HOW FAR THE ROW CAN REACH. A row of two or three lines (a wrapped label, a cell set on three lines beside a label centred on
  // the middle one) is ruled above and below its whole height, and the gold fills it to those rules (ruleBand) - but never past the
  // next row's start: a line in the label's column beginning where the label begins (or centred where it is centred; a wrapped label's
  // second line is indented, so it is not one). The table's own edge where there is no row beyond.
  // A line starting where the label starts is looked for first; a line merely centred where it is centred only where there is none
  // on that side (a wrapped label's indented, shorter second line can be centred on the first: "Maximum floor area" / "per unit of A").
  const reach = (same) => {
    let u = null, d = null;
    for (const it of model.items) {
      if (!it.t || !inBody(it) || it === L || it.h < 0.8 * L.h || !same(it)) continue;
      const c = centre(it);
      if (c < rect.x0 || c > rect.x1 || it.y < rect.y0 || it.y > rect.y1) continue;
      if (it.y > L.y + 0.5 * L.h && (!u || it.y < u.y)) u = it;
      if (it.y < L.y - 0.5 * L.h && (!d || it.y > d.y)) d = it;
    }
    return [u, d];
  };
  const [ux, dx] = reach(it => Math.abs(it.x - L.x) <= 2), [uc, dc] = reach(it => Math.abs(centre(it) - centre(L)) <= 2 && it.x <= L.x + 2);
  const up = ux || uc, down = dx || dc;
  const lt = up ? up.y - DSC * up.h : rect.y1, lb = down ? down.y + ASC * down.h : rect.y0;
  return { L, F, x0, x1, y0: Math.min(a.y0, b.y0) - 0.5, y1: Math.max(a.y1, b.y1) + 0.5, i0, i1, fs: Math.max(L.h, G.h), lt, lb };
}

const TABLE_JOIN = 4;                                             // (384 cropfix) lines of a table between two county cuts of it that are taken in rather than left out (countyClip)
const OMIT_GAP = 12;                                              // (384.72) points of paper, with the dots of an omission in it, between two pieces of a table
const TABLE_ROWS = 30;                                            // (384.72) ... and only a table of this many printed lines (a short table with long notes - 1017.2 - is shown whole)
const TABLE_SAVE = 0.6;                                           // (384.72) ... and only when the pieces are under this share of the whole cut
const TABLE_TALL = 450;                                           // (384.72) points: a row clip taller than this is windowed (tableRowClip)
async function tableRowClip(model, segs, caps, rows) {
  for (const seg of segs) {
    const hits = rows.map(r => findRow(model, norm(r), seg)).filter(Boolean);
    if (!hits.length) continue;
    const cap = caps[0];
    // column headings: the bold small lines right under the caption
    let hb = cap ? bottom(cap) : seg.y1 - 20;
    if (cap) {
      for (const it of model.items) {
        if (!it.t || !it.b || it.h > 8.6 || centre(it) < seg.x0 || centre(it) > seg.x1) continue;
        if (it.y <= cap.y + 2 && it.y >= cap.y - 50) hb = Math.min(hb, bottom(it));
      }
    }
    const yHead = Math.max(hb - 2, seg.y0);
    // notes under the table (small, not bold): the lowest lines of the rectangle
    const inBand = (it) => it.t && inBody(it) && centre(it) >= seg.x0 && centre(it) <= seg.x1 && it.y > seg.y0;
    const bodyRows = model.items.filter(it => inBand(it) && !it.b && it.h >= 8.9 && it.y < yHead);
    const lastRow = bodyRows.length ? Math.min(...bodyRows.map(it => bottom(it))) : seg.y0;
    const notes = model.items.filter(it => inBand(it) && !it.b && it.h < 8.6 && it.y < lastRow);
    const rTop = Math.max(...hits.map(h => h.y1)), rBot = Math.min(...hits.map(h => h.y0));
    // where one row ends and the next begins: a gap between lines wider than the spacing of a row's own wrapped lines.
    // The window around the cited row starts and ends on such a gap, so it never cuts a row in half.
    const lines = [];
    for (const it of model.items) {
      if (!it.t || !inBody(it) || it.h < 8.6 || centre(it) < seg.x0 || centre(it) > seg.x1 || it.y >= yHead || it.y <= seg.y0) continue;
      const g = lines.find(l => Math.abs(l.y - it.y) < 2.5);
      if (g) { g.top = Math.max(g.top, top(it)); g.bot = Math.min(g.bot, bottom(it)); }
      else lines.push({ y: it.y, top: top(it), bot: bottom(it), h: it.h });
    }
    lines.sort((a, b) => b.y - a.y);
    const breaks = [];
    for (let k = 1; k < lines.length; k++) {
      if (lines[k - 1].y - lines[k].y >= 1.3 * lines[k].h) breaks.push((lines[k - 1].bot + lines[k].top) / 2);
    }
    const snapDown = (y) => breaks.filter(b => b <= y).reduce((m, b) => Math.max(m, b), seg.y0);
    // (384 one picture) ONE CUT, as the book prints it: from the caption and column headings down through the row asked about and
    // the rows around it (five lines under it), every row between included, and on through the table's notes where it has them
    // (a note's letter is on the column heading: "OCCUPANT LOAD FACTOR a"). It used to be cut in pieces - the caption, a window of
    // rows, the notes - and shown as two or three pictures.
    let y0 = snapDown(rBot - 72);
    if (notes.length) y0 = Math.min(y0, Math.max(Math.min(...notes.map(it => bottom(it))) - 2, seg.y0));
    let out = [{ page: seg.page, x0: seg.x0, x1: seg.x1, y0: Math.max(y0, seg.y0), y1: seg.y1, col: seg.col, context: true }];
    // (384.72) A TABLE TOO TALL TO READ AT A GLANCE IS SHOWN AS ITS TITLE AND HEADINGS, THE ROWS AROUND THE ONE ASKED ABOUT, AND ITS NOTES - one picture. The cut
    // above runs from the caption to the notes, so a row near the bottom of Table 1004.5 (40 rows) was a picture 1.2 phone screens tall with the row somewhere
    // inside it (the audit's "very tall"). Past TABLE_TALL points the caption and column headings are one piece, the rows from four lines above the row to
    // four below it another, and the notes a third; the pieces are set one under the other on one sheet (as a section's are, see sheetOf) and a piece that
    // would start within a few lines of the one above is joined to it. Every row of the window is whole (a cut is made between rows).
    if (out[0].y1 - out[0].y0 > TABLE_TALL && lines.length >= TABLE_ROWS) {
      const snapUp = (y) => breaks.filter(b => b >= y).reduce((m, b) => Math.min(m, b), seg.y1);
      const first = lines[0], headBot = Math.min(first.top + 1.5, seg.y1);
      const tail = notes.length ? Math.max(Math.min(...notes.map(it => bottom(it))) - 2, seg.y0) : null;
      const noteTop = notes.length ? snapUp(Math.max(...notes.map(it => top(it))) + 1) : null;
      const winTop = snapUp(rTop + 48), winBot = Math.max(snapDown(rBot - 48), seg.y0);
      const piece = (a, b) => ({ page: seg.page, x0: seg.x0, x1: seg.x1, y0: b, y1: a, col: seg.col, context: true });
      const parts = winTop >= headBot - 14 ? [[seg.y1, winBot]] : [[seg.y1, headBot], [winTop, winBot]];
      if (tail != null && noteTop != null) {
        const last = parts[parts.length - 1];
        if (last[1] <= noteTop + 14) last[1] = tail; else parts.push([noteTop, tail]);
      }
      const made = parts.map(([a, b], i) => Object.assign(piece(a, b), i ? { omit: true } : {}));      // omit: rows of the table are left out above this piece (sheetOf marks it)
      // a window that saves little (Table 3206.2: its notes are as tall as its rows, its class labels are cells of several rows) is not worth the gaps: the table is shown whole
      const full = out[0].y1 - out[0].y0, shown = made.reduce((t, m) => t + m.y1 - m.y0, 0);
      if (shown < TABLE_SAVE * full) out = made;
    }
    const marks = [];
    if (cap) marks.push(headMark(seg.page, cap));
    for (const h of hits) { const m = { page: seg.page, x0: h.x0, x1: h.x1, i0: h.i0, i1: h.i1, fs: h.fs, kind: 'row', lt: h.lt, lb: h.lb }; m.y0 = h.i0 - 0.12 * h.fs; m.y1 = h.i1 + 0.12 * h.fs; marks.push(m); }
    // (r15) the whole page washes the WHOLE TABLE - caption to last row and notes - with the row in the stronger gold; the picture shows the cut
    return { segments: out, marks, cited: [{ page: seg.page, x0: seg.x0, x1: seg.x1, y0: seg.y0, y1: seg.y1, col: seg.col, table: true }], text: textIn(model, out) };
  }
  return null;
}

// ---- Referenced Standards (chapter 80): one entry of the list
// An entry is its designation line ("25—20: Standard for ...", bold; a long title wraps onto bold lines that are indented a little) followed
// by the code sections that refer to it (plain text), up to the next designation. The organisation it belongs to ("NFPA") is shown above it:
// its heading when it is on this page, otherwise the "NFPA—continued" line at the top of the page.
const dsig = (s) => String(s).toLowerCase().replace(/[—–]/g, '-').replace(/\s+/g, ' ').trim();
const designatorOf = (text) => { const i = text.indexOf(':'); return dsig(i < 0 ? text : text.slice(0, i)); };

function findEntry(model, want) {
  const { items } = model;
  for (let k = 0; k < items.length; k++) {
    const it = items[k];
    if (!it.t || !it.b || !inBody(it) || it.h < 8.5 || it.h > 9.6) continue;
    const line = boldRun(items, k, false);
    const d = designatorOf(line.text1);
    if (d === want || d.startsWith(want + ',') || d.startsWith(want + ' ')) return { k, line };
    k = Math.max(k, line.last);
  }
  return null;
}

async function entryClip(doc, index, loc, ptr, opts, fontBold, cache) {
  const want = dsig(loc.token);
  const hint = ptr.pdfPage || 1;
  for (const p of [hint, hint - 1, hint + 1]) {                  // the cited page first; a copy paged one off is still found
    if (p < 1 || p > index.numPages) continue;
    const model = await pageModel(doc, p, fontBold, cache);
    if (model.rot) continue;
    const hit = findEntry(model, want);
    if (!hit) continue;
    const { items } = model, { line } = hit;
    let r = { x0: line.x, x1: line.x + line.w, y0: line.y - 0.3 * line.h, y1: line.y + 0.95 * line.h };
    let ended = false;
    for (let k = line.last + 1; k < items.length; k++) {
      const it = items[k];
      if (!it.t) continue;
      if (!inBody(it)) { ended = true; break; }
      if (it.b && it.h > 9.6) { ended = true; break; }                               // the next organisation
      if (it.b && it.x < line.x + 5 && it.y < line.y - 2) { ended = true; break; }    // the next designation
      r = union(r, rectOf(it));
    }
    const segments = [], marks = [], textParts = [], pages = [p];
    const band = { x0: Math.max(COL_L - 8, r.x0 - 8), x1: Math.min(COL_R + 8, r.x1 + 8) };
    // the organisation: its heading above the entry on this page, else the "—continued" line at the top
    let org = null;
    for (const it of items) {
      if (!it.t || !it.b || !inBody(it) || it.y <= line.y) continue;
      if (it.h > 12 && (!org || it.y < org.y)) org = it;
    }
    if (!org) org = items.find(it => it.t && it.b && inBody(it) && /[—–-]\s*continued\s*$/i.test(it.t) && it.y > line.y) || null;
    if (org) {                                                  // the heading, with the address lines that sit beside it
      let o = { x0: org.x, x1: org.x + org.w, y0: org.y - 0.22 * org.h, y1: org.y + 0.9 * org.h };
      for (let k = org.i + 1; k < items.length; k++) {
        const it = items[k];
        if (!it.t) continue;
        if (!inBody(it) || it.b) break;
        o = union(o, { x0: it.x, x1: it.x + it.w, y0: it.y - 0.22 * it.h, y1: it.y + 0.9 * it.h });
      }
      // (r15) the organisation is context, not the cited thing: it is shown (not highlighted) only when it stands right above the entry; a heading
      // far up the page, joined to the entry in one picture under a gap, made a sliver of two unrelated pieces
      if (o.y0 - (line.y + 0.8 * line.h) <= 24) { segments.push({ page: p, ...band, y0: o.y0, y1: o.y1 + 2, col: -1, context: true }); textParts.push(textIn(model, [segments[0]])); }
    }
    // (r15) the entry's own width: a picture of one entry is cut to where its lines run, not to the whole page width (a strip of print at half the size)
    const entrySeg = { page: p, ...band, y0: Math.max(r.y0 - 2, BODY_BOTTOM), y1: line.y + 0.8 * line.h + 1.5, col: -1 };
    segments.push(entrySeg);
    textParts.push(textIn(model, [entrySeg]));
    marks.push(headMark(p, line));
    // the list of code sections may run onto the next page (above that page's first designation)
    if (!ended && p < index.numPages) {
      const m2 = await pageModel(doc, p + 1, fontBold, cache);
      let q = null;
      for (const it of m2.items) {
        if (!it.t || !inBody(it)) continue;
        if (it.b) { if (/continued\s*$/i.test(it.t)) continue; break; }
        q = union(q, rectOf(it));
      }
      if (q) {
        const seg = { page: p + 1, ...band, y0: Math.max(q.y0 - 3, BODY_BOTTOM), y1: q.y1 + 2, col: -1 };
        segments.push(seg); pages.push(p + 1); textParts.push(textIn(m2, [seg]));
      }
    }
    return { ok: true, segments, marks, cited: segments.filter(sg => !sg.context), text: textParts.join(' '), pages, truncated: false };
  }
  return { ok: false };
}

// ------------------------------------------------------------------------------------------------ county amendments
// The Harris County booklet is a single column of Word text (running header at the top, page footer at the bottom). A county reference carries the
// exact words (`excerpt`, `highlight`) and the booklet page(s) (`pdfPage`, `pdfPageEnd`); this finds those words in the booklet, cuts the lines that
// hold them (full text width, from the first to the last line of the excerpt) and marks the heading and the deciding sentence. The result has the
// same shape as computeClip's, so paint() and paintPages() draw it. `doc` is the booklet; it is the county's own public text, so the app ships it.
// opts.cache: a Map shared between calls.
const C_TOP = 735, C_BOTTOM = 56;
const cnorm = (s) => norm(String(s).replace(/\u00b2/g, '2').replace(/\u00b3/g, '3').replace(/\u00b9/g, '1'));   // m\u00b2 is printed as m and a raised 2
// WHERE EACH LETTER OF THE BOOKLET REALLY STANDS. getTextContent gives a run's start and width, not its letters, and the old reading spread a
// run's width over its letters by Times' proportions - but the booklet is set in Calibri, and a justified line is one long run with wide
// spaces, so a letter's place could be four points out by the middle of a line (a highlight ended in the middle of "apart."). The page's own
// drawing says it exactly: pdf.js draws each letter with one fillText at its origin, so the page is drawn once into a 1 px canvas whose
// fillText is watched, and every origin and advance is kept in page points. (No canvas - a headless reader - gives null: the old reading stays.)
async function glyphOrigins(page) {
  try {
    if (typeof document === 'undefined') return null;
    const cv = document.createElement('canvas'); cv.width = 1; cv.height = 1;
    const ctx = cv.getContext('2d');
    if (!ctx || !ctx.getTransform) return null;
    const vp = page.getViewport({ scale: 1 }), out = [], orig = ctx.fillText;
    ctx.fillText = function (str, x, y) {
      try {
        const t = ctx.getTransform(), p = vp.convertToPdfPoint(t.a * x + t.c * y + t.e, t.b * x + t.d * y + t.f);
        out.push({ x: p[0], y: p[1], w: ctx.measureText(str).width * Math.hypot(t.a, t.b) / vp.scale });
      } catch (e) { /* this letter keeps the old reading */ }
      return orig.apply(this, arguments);
    };
    await page.render({ canvasContext: ctx, viewport: vp }).promise;
    cv.width = 0; cv.height = 0;
    return out.length ? out : null;
  } catch (e) { return null; }
}
// one run's letters: [{ x0, x1 } | null for a space] when the page drew exactly as many letters as the run has (else null)
function runGlyphs(it, recs) {
  if (!recs) return null;
  const cs = Array.from(it.s), ns = [];
  cs.forEach((c, k) => { if (!/\s/.test(c)) ns.push(k); });
  const mine = recs.filter(r => Math.abs(r.y - it.y) < 0.6 && r.x >= it.x - 0.2 && r.x < it.x + it.w - 0.05).sort((a, b) => a.x - b.x).filter((r, i, a) => !i || r.x - a[i - 1].x > 0.05);     // (a letter drawn twice for weight is one)
  if (!ns.length || mine.length > ns.length) return null;
  // the font draws "fi", "fl", "ff", "ft", "tf", "tt", "ti" (and "ffi", "ffl", "tti") as one glyph each: the text has two or three letters where the page drew one.
  // They are joined when the count says so, and only when it says so for certain (as many places as it needs); the glyph is shared out between its letters
  const LIGS = [['ffi', 'ffl', 'tti', 'ff', 'fi', 'fl', 'ft', 'tf', 'tt', 'ti'], ['ffi', 'ffl', 'ff', 'fi', 'fl', 'ft', 'tf', 'tt', 'ti'], ['ffi', 'ffl', 'ff', 'fi', 'fl', 'ft', 'tf', 'tt', 'ti', 'Th'], ['ffi', 'ffl', 'ff', 'fi', 'fl']], units = [];
  const need = ns.length - mine.length;
  if (need) {
    let lig = null;
    for (const LIG of LIGS) {
      const at = [];
      for (let q = 0; q < ns.length; q++) {
        const k = ns[q];
        for (const l of LIG) if (q + l.length <= ns.length && ns[q + l.length - 1] === k + l.length - 1 && cs.slice(k, k + l.length).join('') === l) { at.push([q, l.length]); q += l.length - 1; break; }
      }
      if (at.reduce((a, [, l]) => a + l - 1, 0) === need) { lig = new Map(at); break; }
    }
    if (!lig) return null;
    for (let q = 0; q < ns.length;) { const l = lig.get(q) || 1; units.push(ns.slice(q, q + l)); q += l; }
  } else for (const k of ns) units.push([k]);
  if (units.length !== mine.length) return null;
  const out = cs.map(() => null);
  units.forEach((u, i) => {
    const r = mine[i], last = u[u.length - 1], nextCh = last + 1 < cs.length && !/\s/.test(cs[last + 1]);
    const x0 = r.x, x1 = nextCh && mine[i + 1] ? mine[i + 1].x : (last === cs.length - 1 ? it.x + it.w : r.x + Math.min(r.w, Math.max(0.5, it.x + it.w - r.x)));
    u.forEach((k, m) => { out[k] = { x0: x0 + (x1 - x0) * m / u.length, x1: x0 + (x1 - x0) * (m + 1) / u.length }; });
  });
  return out;
}
export async function countyChars(doc, p, cache) {
  const key = 'c' + p;
  if (cache && cache.has(key)) return cache.get(key);
  const page = await doc.getPage(p);
  const tc = await page.getTextContent();
  const recs = await glyphOrigins(page);
  const items = tc.items.filter(it => it.str && it.str.trim() && it.transform[5] >= C_BOTTOM && it.transform[5] <= C_TOP)
    .map(it => ({ s: it.str, x: it.transform[4], y: it.transform[5], w: it.width, h: it.height || 11, f: it.fontName }));
  items.sort((a, b) => b.y - a.y);
  const lines = [];                           // superscripts ("m2", footnote marks) stand a few points higher than their line: one line = items within 5 pt
  for (const it of items) {
    const ln = lines.length && lines[lines.length - 1].ref - it.y <= 5 ? lines[lines.length - 1] : null;
    if (ln) { ln.items.push(it); ln.x0 = Math.min(ln.x0, it.x); ln.x1 = Math.max(ln.x1, it.x + it.w); }
    else lines.push({ p, ref: it.y, y: it.y, x0: it.x, x1: it.x + it.w, items: [it] });
  }
  // (384 table side cells) a table cell centred between the two lines of its neighbour ("100 ft." between the two lines of "Motor vehicles
  // fuel-dispensing ... / dispensing station dispenser") sorts between them and cut the neighbour's sentence in two, so the row's first
  // cell was found as its first line alone. A line that stands right of both its neighbours and between them is read after them.
  for (let i = 1; i < lines.length - 1; i++) {
    const L = lines[i], a = lines[i - 1], b = lines[i + 1];
    if (L.x0 >= Math.max(a.x1, b.x1) - 2 && a.ref - L.ref <= 9 && L.ref - b.ref <= 9) { lines[i] = b; lines[i + 1] = L; i++; }
  }
  for (const ln of lines) {
    ln.items.sort((a, b) => a.x - b.x);
    const wide = ln.items.reduce((m, it) => (it.w > m.w ? it : m), ln.items[0]);
    ln.y = wide.y; ln.fs = wide.h || 11;
  }
  // (r15 whole provision) What each printed line IS, read from its type: the booklet sets a heading ("322.1 General.", "SECTION 322", "TABLE 112.4.2")
  // in a bold face of its own and everything else in the body face, so a wrapped line that merely starts with a section number
  // ("112.4.2. Court costs are ...") is not mistaken for one. Where a provision ends, where a table ends, and the text column's edges,
  // are all decided from this.
  // A numbered line is a heading when its number and title are set in a face of their own - followed on the line by running text in another face
  // ("322.1 General. The storage ..."), or alone in a face that the page's headings are set in ("5609.2 Definitions."): a wrapped line that
  // merely starts with a section number ("112.4.2. Court costs ..."), a table cell and a footnote are all one face to the end of the line.
  const fchars = new Map(), headFonts = new Set(), bodyFonts = new Set();
  for (const it of items) fchars.set(it.f, (fchars.get(it.f) || 0) + it.s.length);
  const lead = (ln) => { const it0 = ln.items[0]; let t = '', k = 0; for (const it of ln.items) { if (it.f !== it0.f) break; t += it.s; k++; } return { f: it0.f, t: t.replace(/\s+/g, ' ').trim(), later: k < ln.items.length ? ln.items[k].f : null }; };
  const SECH = /^[A-Z]{0,2}\d{2,4}(?:\.\s?\d+)+[A-Za-z]?\s*[A-Z]/;
  for (const ln of lines) { const l = lead(ln); if (l.later && SECH.test(l.t)) { headFonts.add(l.f); bodyFonts.add(l.later); } }
  if (!bodyFonts.size) { let bf = null; for (const [f, n] of fchars) if (bf == null || n > fchars.get(bf)) bf = f; bodyFonts.add(bf); }
  // (a heading some paragraphs set in the running face - "611.2.4 Labeling. Emergency ..." - is read by where it starts: a numbered line whose
  // title and text follow the number, after a line that ended its paragraph or a paragraph's space)
  let right0 = 0; for (const ln of lines) if (ln.x1 <= 545 && ln.x1 > right0) right0 = ln.x1;
  const startsPara = (i) => i === 0 || lines[i - 1].ref - lines[i].ref > 16.5 || lines[i - 1].x1 < right0 - 12;
  let inTable = false;
  for (const [i, ln] of lines.entries()) {
    const l = lead(ln); ln.head = null;
    if (SECH.test(l.t) && (l.later || headFonts.has(l.f) || startsPara(i))) ln.head = 'sec';
    else if (/^(?:SECTIONS?\s*[A-Z]{0,2}\d|CHAPTER\s*\d|APPENDIX\s*[A-Z]\b|EXHIBIT\b)/.test(l.t) && l.t === l.t.toUpperCase()) ln.head = 'banner';
    else if (/^(?:TABLE|Table)\s+[A-Z]?\d/.test(l.t) && !bodyFonts.has(l.f)) ln.head = 'table';
    if (ln.head === 'table') inTable = true; else if (ln.head) inTable = false;
    ln.text = ln.items.map(i => i.s).join(' ');
    ln.tbl = inTable;                                                          // a line of a table (its cells and notes), not running text
    ln.body = !inTable;
  }
  // the text column: its right edge is where the lines of text stop (the furthest right end of a line), its left edge the leftmost line of body text
  let left = Infinity;
  for (const ln of lines) if (ln.body || ln.head) left = Math.min(left, ln.x0);
  let right = null; for (const ln of lines) if (ln.x1 <= 545 && (right == null || ln.x1 > right)) right = ln.x1;
  if (right != null && right >= 534 && right <= 541) right = 540;                 // the booklet's text runs from 72 to 540 on every page (a 1 inch margin)
  if (left >= 70 && left <= 74) left = 72;
  const chars = [];                           // letters and digits only, with the x range each one covers on its line
  lines.forEach((ln, li) => {
    // (384 one picture) a heading set larger than the body (an Exhibit's title) has a taller box: it was cut through its capitals
    ln.y0 = ln.y - Math.max(3, 0.3 * ln.fs); ln.y1 = ln.y + Math.max(9.5, 0.95 * ln.fs);
    // the line's letters in reading order: { n (the letter, '' for punctuation), x0, x1, sp (a space stands before it), ex (placed by the page's own drawing) }
    const seq = [];
    let prev = null;
    for (const it of ln.items) {
      const ws = Array.from(it.s, c => TNR[c] || 500), tot = ws.reduce((a, b) => a + b, 0) || 1, gl = runGlyphs(it, recs);
      let acc = 0, k = 0, sp = !prev || (it.x - prev.x1 > 0.12 * ln.fs);               // (a run that starts a hair after the last one's end goes on with its word)
      for (const c of it.s) {
        const w = ws[k], a = it.x + it.w * acc / tot; acc += w;
        const g = gl ? gl[k] : null; k++;
        if (/\s/.test(c)) { sp = true; continue; }
        const e = { n: cnorm(c), x0: g ? g.x0 : a, x1: g ? g.x1 : it.x + it.w * acc / tot, sp, ex: !!g };
        seq.push(e); prev = e; sp = false;
      }
    }
    seq.forEach((e, i) => {
      if (!e.n) return;
      // the punctuation that goes with this letter's word: after it up to the next space ("apart." / "NAME”,"), before it back to the last one ("(a" / "“NO")
      const pre = [], post = [];
      for (let j = i + 1; j < seq.length && !seq[j].sp && !seq[j].n; j++) post.push(seq[j]);
      if (!e.sp) for (let j = i - 1; j >= 0 && !seq[j].n; j--) { pre.push(seq[j]); if (seq[j].sp) break; }
      chars.push({ c: e.n, li, x0: e.x0, x1: e.x1, ex: e.ex && post.every(q => q.ex) && pre.every(q => q.ex), pre: pre.length ? Math.min(...pre.map(q => q.x0)) : null, post: post.length ? Math.max(...post.map(q => q.x1)) : null });
    });
  });
  const out = { p, lines, chars, left: Number.isFinite(left) ? left : null, right };
  if (cache) cache.set(key, out);
  return out;
}

export async function countyClip(doc, ptr, opts = {}) {
  const cache = opts.cache || (opts.cache = new Map());
  const p0 = ptr.pdfPage, p1 = ptr.pdfPageEnd || ptr.pdfPage;
  if (!doc || !p0 || p0 < 1 || p1 > doc.numPages) return { ok: false };
  const parts = [];
  for (let p = p0; p <= p1; p++) parts.push(await countyChars(doc, p, cache));
  const all = [];                                              // one flat list over the pages
  for (const pt of parts) for (const ch of pt.chars) all.push({ ...ch, pt });
  const N = all.map(a => a.c).join('');
  // Where a piece stands in the booklet text N. A table row of the question file is written "cell | cell" (or "group › kind | amount"): the cells are
  // found one after the other, near each other.
  // (384 one picture) the cell of a row nearest the anchor's LINE first (a row's cells are printed side by side; the row above can be
  // nearer in the text order - "Corrosive ... 200" just before "Flammable (except ..." - and its value is not this row's), then the
  // nearest in the text
  const yAt = (k) => { const a = all[Math.max(0, Math.min(all.length - 1, k))]; return a.pt.p * 10000 - a.pt.lines[a.li].y; };
  let nearBase = 0;
  const nearest = (w, key, c) => {
    let best = -1, bd = Infinity;
    for (let j = w.indexOf(key); j >= 0; j = w.indexOf(key, j + 1)) {
      const d = Math.abs(yAt(nearBase + j) - yAt(nearBase + c)) * 1000 + Math.abs(j - c);
      if (d < bd) { bd = d; best = j; }
    }
    return best;
  };
  // (384 cropfix) A TABLE'S TITLE IS ITS OWN TITLE LINE. "TABLE 105.5.22" is also the last words of the sentence that introduces the table ("... in
  // excess of the amounts listed in Table 105.5.22."), and that sentence comes first in the text: the cut began a line above the table, on a sentence
  // fragment, and the fragment (wider than the table) set the picture off centre. A piece that is a table's title is matched where a title line of
  // the booklet is that title, whole (else where a table heading line starts with it; else anywhere, as before).
  const lineHead = (k) => k === 0 || all[k - 1].pt !== all[k].pt || all[k - 1].li !== all[k].li;
  const lineLen = (k) => { let n = 0; while (k + n < all.length && all[k + n].pt === all[k].pt && all[k + n].li === all[k].li) n++; return n; };
  const titleAt = (E, from) => {
    let start = -1;
    for (let j = N.indexOf(E, from); j >= 0; j = N.indexOf(E, j + 1)) {
      if (!lineHead(j) || all[j].pt.lines[all[j].li].head !== 'table') continue;
      if (lineLen(j) === E.length) return j;
      if (start < 0) start = j;
    }
    return start;
  };
  const findPiece = (text, from) => {
    const E = cnorm(text);
    if (E.length < 6) return null;
    const t = /^\s*(?:TABLE|Table)\s+[A-Z]?\d/.test(String(text)) ? titleAt(E, from) : -1;
    if (t >= 0) return [t, t + E.length];
    const i = N.indexOf(E, from);
    // (384 cropfix) a piece that is a line of its own ("Toxic materials", a table's group) found first inside another line ("Highly toxic
    // materials", the group before it) is the line that IS it, where the booklet prints one after it
    if (i >= 0 && !lineHead(i)) { for (let j = N.indexOf(E, i + 1); j >= 0; j = N.indexOf(E, j + 1)) if (lineHead(j) && lineLen(j) === E.length) return [j, j + E.length]; }
    if (i >= 0) return [i, i + E.length];
    const cells = String(text).split(/ \| | › /).map(cnorm).filter(Boolean);
    if (cells.length > 1) {
      for (let at = N.indexOf(cells[0], from); at >= 0; at = N.indexOf(cells[0], at + 1)) {
        let pos = at + cells[0].length, ok = true;
        for (let c = 1; c < cells.length && ok; c++) {
          const j = N.indexOf(cells[c], pos);
          if (j < 0 || j - pos > 160) ok = false; else pos = j + cells[c].length;
        }
        if (ok) return [at, pos];
      }
      // a wrapped cell is printed a line above or below its row: anchor on the longest cell, look for the others in a window around it
      const raw = String(text).split(/ \| | › /).filter(c => cnorm(c));
      const longest = cells.reduce((m, c) => (c.length > m.length ? c : m), ''), anchor = longest.length > 16 ? longest.slice(0, 14) : longest;
      for (let at = N.indexOf(anchor, from); at >= 0; at = N.indexOf(anchor, at + 1)) {
        let lo = at, hi = at + anchor.length, ok = true;
        const base = Math.max(from, at - 140), w = N.slice(base, at + anchor.length + 200);
        nearBase = base;
        // (384 one picture) the anchor cell's own end, where it wraps onto a line of its own ("Four per school year, two per" /
        // "semester"): the row is cut and marked to its end
        if (anchor !== longest) { const t = nearest(w, longest.slice(-8), at - base); if (t >= 0 && base + t > at) hi = Math.max(hi, base + t + 8); }
        for (let ci = 0; ci < cells.length && ok; ci++) {
          const cell = cells[ci];
          if (cell === longest) continue;
          const key = cell.length > 16 ? cell.slice(0, 14) : cell, j = nearest(w, key, at - base);
          if (j >= 0) {
            lo = Math.min(lo, base + j); hi = Math.max(hi, base + j + key.length);
            if (key !== cell) { const t = nearest(w, cell.slice(-8), at - base); if (t >= 0) hi = Math.max(hi, base + t + 8); }   // the rest of a cell that wraps
          } else {                                                                              // "109.6, 114.2": printed one above and one below the row's middle line
            const parts = raw[ci].split(/,\s*/).map(cnorm).filter(x => x.length >= 3);
            if (parts.length < 2) { ok = false; break; }
            for (const pt of parts) {
              const jj = nearest(w, pt, at - base);
              if (jj < 0) { ok = false; break; }
              lo = Math.min(lo, base + jj); hi = Math.max(hi, base + jj + pt.length);
            }
          }
        }
        if (ok) return [lo, hi];
      }
    }
    if (E.length > 60) {                                        // a piece that skips a few words: its first and its last words
      const h = N.indexOf(E.slice(0, 40), from), t = h < 0 ? -1 : N.indexOf(E.slice(-40), h);
      if (h >= 0 && t >= 0) return [h, t + 40];
    }
    return null;
  };
  // the excerpt is one or more pieces (one per line of its text); the booklet may print more between them
  const ranges = [];
  let pos = 0;
  for (const piece of String(ptr.excerpt || '').split('\n')) {
    const r = findPiece(piece, pos);
    if (r) { ranges.push(r); pos = r[1]; }
  }
  if (!ranges.length) return { ok: false };
  const a = ranges[0][0];
  let b = ranges[ranges.length - 1][1];
  // the exception that a reference is about is printed after the excerpt: the cut runs to its end
  if (ptr.exceptionText) {
    let xp = ranges[ranges.length - 1][1];
    // (an excerpt may quote a line the booklet prints after the exceptions: the exception is then looked for from the excerpt's start)
    for (const piece of String(ptr.exceptionText).split('\n')) { const r = findPiece(piece, xp) || findPiece(piece, a); if (r) { ranges.push(r); b = Math.max(b, r[1]); xp = r[1]; } }
  }
  // A reference that is only a heading ("SECTION 322 BATTERY STORAGE", "CHAPTER 1 SCOPE AND ADMINISTRATION": no deciding words) is cut with the start of
  // what it heads, as a chapter title of the book is cut with its note: the headings set under it, then the first paragraph of running text (to its end,
  // or LEAD_MAX lines), on the heading's own page; never a table, nor the exceptions or list under that paragraph. The heading is marked (below); the lines
  // under it carry the wash only.
  const LEADSEC = /^(?:\d{2,4}(?:\.\d+)+[A-Za-z]?\b|SECTION\b|CHAPTER\b|TABLE\b|Table\b|APPENDIX\b)/;
  const lead = new Map();                                      // page part -> the lines added under the heading
  const headOnly = !ptr.highlight && !ptr.exceptionText && !!ptr.heading && cnorm(ptr.excerpt || '') === cnorm(ptr.heading);
  if (headOnly) {
    const LEAD_MAX = 7;
    const pt = all[b - 1].pt, add = [];
    let body = false;
    for (let li = all[b - 1].li + 1; li < pt.lines.length && add.length < LEAD_MAX; li++) {
      const ln = pt.lines[li], prev = pt.lines[li - 1];
      const words = ln.items.map(i => i.s).join(' '), first = (ln.items[0] || { s: '' }).s.trim();
      if (body) { if (prev.y - ln.y > 16 || LEADSEC.test(first) || /^Exceptions?\b/.test(first) || /^\d{1,2}\.(?:\s|$)/.test(first)) break; }
      else if (/^(?:TABLE|Table)\b/.test(first)) break;
      else if (/[a-z]/.test(words)) body = true;           // the first line of running text: its paragraph is the one shown
      add.push(li);
    }
    if (add.length) lead.set(pt, add);
  }
  // The deciding words: where the excerpt's own lines carry them, there (a table repeats a cell's words - "Any Amount" - and the first one in
  // the booklet after the excerpt's start can be another row's, on a line the cut does not show); else their first place in the excerpt's
  // span, whose lines are then cut too, so the mark is always in the picture.
  let hl = null;
  if (ptr.highlight) {
    const lineOf = (k) => all[k].pt.p + ':' + all[k].li, cut = new Set();
    for (const [x, y] of ranges) for (let k = x; k < y; k++) cut.add(lineOf(k));
    for (const [pt, add] of lead) for (const li of add) cut.add(pt.p + ':' + li);
    const E = cnorm(ptr.highlight);
    // (384 cropfix) a row ("Toxic | Any Amount") is the row whose line starts with it: found first inside another row ("Highly toxic Any Amount", the
    // row above it in Table 105.5.9), the gold went on the wrong row (ch60-514)
    const rowWanted = / \| | › /.test(String(ptr.highlight));
    let firstOn = null;
    if (E.length >= 6) for (let at = N.indexOf(E, a); at >= 0 && at + E.length <= b && !hl; at = N.indexOf(E, at + 1)) {
      let on = true; for (let k = at; k < at + E.length && on; k++) on = cut.has(lineOf(k));
      if (on && (!rowWanted || lineHead(at))) hl = [at, at + E.length];
      else if (on && !firstOn) firstOn = [at, at + E.length];
    }
    if (!hl && firstOn) hl = firstOn;
    if (!hl) { const h = findPiece(ptr.highlight, a); if (h && h[1] <= b) { hl = h; ranges.push(h); } }
  }
  // the lines of the booklet that hold the pieces. (384 one picture) ONE CUT A PAGE: from the first line of the first piece to the last
  // line of the last, every line between included - the section's lead, the exceptions or list items before the one the question is
  // about, the table rows between its heading and the row - as the booklet prints them. A gap of more than three lines used to start
  // a second cut, shown as a second picture.
  const segments = [], marks = [], texts = [], pages = [], spans = [];
  const rowCiteCut = / \| | › /.test(String(ptr.highlight || ''));
  for (const pt of parts) {
    const used = new Set(lead.get(pt) || []);
    for (const [x, y] of ranges) for (let k = x; k < y; k++) if (all[k].pt === pt) used.add(all[k].li);
    if (!used.size) continue;
    const idx = [...used].sort((u, v) => u - v);
    let lo = idx[0], hi = idx[idx.length - 1];
    // a line whose letters reach into the cut's top or bottom (a table cell set on two half-lines beside a one-line cell:
    // "Four per school year, two per" / "Group E" / "semester") is part of it - the cut never shows half a line
    const iTop = (l) => l.y + 0.75 * l.fs, iBot = (l) => l.y - 0.25 * l.fs;
    for (let grew = true; grew;) {
      grew = false;
      const p = pt.lines[lo - 1], n = pt.lines[hi + 1];
      const top = Math.max(...pt.lines.slice(lo, hi + 1).map(iTop)), bot = Math.min(...pt.lines.slice(lo, hi + 1).map(iBot));
      if (p && iBot(p) < top) { lo--; grew = true; }
      if (n && iTop(n) > bot) { hi++; grew = true; }
    }
    // (r15) a cut never ends inside a sentence or a list item: a last line that runs the full width of the column and is followed by a
    // line that goes on with it (no heading, no new list item, no exception) takes those lines in, to the end of the sentence
    for (let n = 0; n < 14 && hi + 1 < pt.lines.length && pt.right; n++) {
      const cur = pt.lines[hi], nx = pt.lines[hi + 1];
      if (/[.:;?!)"\u201d]\s*$/.test(cur.text.trim())) break;                       // the last line ends a sentence
      if (!(cur.body && cur.x1 >= pt.right - 6 && nx.body && !nx.head && !/^(?:Exceptions?\b|\d{1,2}\.\s|\(?[a-z0-9]{1,3}\)\s)/.test(nx.text) && nx.x0 >= cur.x0 - 2)) break;
      hi++; used.add(hi);
    }
    spans.push({ pt, lo, hi });
  }
  // (384 cropfix) A TABLE THAT RUNS ONTO THE NEXT PAGE IS ONE TABLE IN THE PICTURE. A row cited from a table whose title and headings are on the page
  // before (Table 105.5.22: title on PDF page 17, rows on 18; Exhibit B's Table 1004.5: 90 and 91) was two cuts set one under the other with nothing
  // between them, the rows the booklet prints between them left out unsaid - and the second cut narrower than the first (its own words' width): the
  // table's right-hand border and the end of every rule were cut off. Where only a few lines of the table stand between the two cuts (TABLE_JOIN)
  // they are taken in, so the table runs on unbroken from one page to the next (the seam is one rule: `cont`); where more do, the second cut says
  // rows are left out (`omit`: the same gap with dots as a windowed book table, see tableRowClip / paintSheet). The width is the table's own: the
  // painter takes each cut out to the table's border (paintSheet, tableFrame).
  if (rowCiteCut && spans.length > 1) {
    for (let k = 1; k < spans.length; k++) {
      const A = spans[k - 1], B = spans[k];
      if (B.pt.p !== A.pt.p + 1) continue;
      let end = A.hi;
      while (end + 1 < A.pt.lines.length && A.pt.lines[end + 1].tbl) end++;
      const between = (end - A.hi) + B.lo;
      if (between <= TABLE_JOIN) { A.hi = end; B.lo = 0; B.cont = true; }
      else B.omit = true;
    }
  }
  for (const { pt, lo, hi, cont, omit } of spans) {
    const runs = [[]];
    for (let g = lo; g <= hi; g++) runs[0].push(g);
    for (const run of runs) {
      const ls = run.map(i => pt.lines[i]);
      const x0 = Math.max(0, Math.min(...ls.map(l => l.x0)) - 4), x1 = Math.min(612, Math.max(...ls.map(l => l.x1)) + 4);
      // keep clear of the neighbouring lines (a table row printed just above or below must not show as a half line)
      const top = Math.max(...ls.map(l => l.y1)), bottom = Math.min(...ls.map(l => l.y0));
      const prev = pt.lines[run[0] - 1], next = pt.lines[run[run.length - 1] + 1];
      const y1 = prev ? Math.max(top, Math.min(top + 2, prev.y - 3)) : top + 2;
      const y0 = next ? Math.min(bottom, Math.max(bottom - 2, next.y + 10)) : bottom - 2;
      segments.push(Object.assign({ page: pt.p, x0, x1, y0, y1, col: -1 }, cont ? { cont: true } : {}, omit ? { omit: true } : {}));
      texts.push(ls.map(l => l.items.map(i => i.s).join(' ')).join(' '));
    }
    pages.push(pt.p);
  }
  const markRange = (from, to, kind) => {
    const byLine = new Map();
    for (let k = from; k < to; k++) {
      const ch = all[k], key = ch.pt.p + ':' + ch.li;
      const m = byLine.get(key);
      // (a line's first letter takes the punctuation that is part of its word, a quote or bracket before it; its last letter the full stop, comma
      // or closing quote after it - a mark reaches the end of its words, to the last glyph of the cited text and not a letter short of it)
      const lo = ch.pre != null ? Math.min(ch.x0, ch.pre) : ch.x0, hi = ch.post != null ? Math.max(ch.x1, ch.post) : ch.x1;
      if (m) { m.x0 = Math.min(m.x0, lo); m.x1 = Math.max(m.x1, hi); m.exact = m.exact && !!ch.ex; }
      else {
        const ln = ch.pt.lines[ch.li], nb = [ch.pt.lines[ch.li - 1], ch.pt.lines[ch.li + 1]].filter(Boolean).map(o => Math.abs(o.y - ln.y)).filter(d => d >= 0.9 * ln.fs && d <= 2.2 * ln.fs);
        // (snap: where the letters are placed from Times widths on a booklet set in Calibri - the painter moves its ends onto the words it covers;
        // exact: the page's own drawing placed every letter, so the ends stand where the letters do and nothing is moved)
        byLine.set(key, inkMark({ page: ch.pt.p, x0: lo, x1: hi, kind, snap: true, exact: !!ch.ex, lp:nb.length ? Math.min(...nb) : 1.25 * ln.fs }, ln.y, ln.fs, DSC_COUNTY));
      }
    }
    for (const m of byLine.values()) marks.push(m);
  };
  if (hl) {
    const n0 = marks.length;
    markRange(hl[0], hl[1], 'cite');
    // (384 one picture) a table row ("cell | cell | cell") is marked as one block over its cells and their wrapped lines - not one
    // band per printed line, which stepped up and down across the row
    const rowHl = / \| | › /.test(String(ptr.highlight));
    if (rowHl) for (let k = n0; k < marks.length; k++) marks[k].tableRow = true;
    if (rowHl && marks.length - n0 > 1) {
      const rows = marks.splice(n0);
      for (const pg of new Set(rows.map(m => m.page))) {
        const rs = rows.filter(m => m.page === pg);
        const m = { ...rs[0], x0: Math.min(...rs.map(r => r.x0)), x1: Math.max(...rs.map(r => r.x1)), i0: Math.min(...rs.map(r => r.i0)), i1: Math.max(...rs.map(r => r.i1)), fs: Math.max(...rs.map(r => r.fs)) };
        m.y0 = m.i0 - 0.12 * m.fs; m.y1 = m.i1 + 0.12 * m.fs; m.lp = m.i1 - m.i0; m.tableRow = true; m.exact = rs.every(r => r.exact);
        marks.push(m);
      }
    }
  }
  const T = cnorm((ptr.section || '') + (ptr.heading || ''));
  if (T.length >= 4 && N.startsWith(T, a)) markRange(a, a + T.length, 'heading');
  else if (headOnly) markRange(a, b, 'heading');               // a heading given whole ("SECTION 322 BATTERY STORAGE") carries its own number
  // THE WHOLE PAGE HIGHLIGHTS THE WHOLE PROVISION (r15): from its heading to the last of its sub-items and exceptions, the whole table from its
  // title to its last row and notes, as far as the page the question cites goes - not just the lines the picture shows. A provision ends at the next
  // heading (a numbered section, a SECTION / CHAPTER banner); a table at the next heading or at another table's title. A heading cited alone
  // takes the first provision under it. The block runs the width of the text column (xr; a table's own rules decide its width), centred headings
  // sitting in the middle of it (sym).
  const cited = [];
  const rowCite = / \| | › /.test(String(ptr.highlight || ''));
  const citedLines = new Map();
  for (const pt of parts) { const u = new Set(lead.get(pt) || []); for (const [x, y] of ranges) for (let k = x; k < y; k++) if (all[k].pt === pt) u.add(all[k].li); citedLines.set(pt, u); }
  let carry = false;                                          // the provision is still running at the foot of the page before
  for (const [pi, pt] of parts.entries()) {
    const L = pt.lines, u = citedLines.get(pt);
    let lo, hi;
    if (u.size) {
      const i0 = Math.min(...u), i1 = Math.max(...u);
      let t = -1, head = -1;
      for (let i = i1; i >= 0; i--) { if (L[i].head === 'table') { t = i; break; } if (L[i].head) { head = i; break; } }
      const tbl = t >= 0 || (rowCite && head < 0);
      lo = i0;
      if (tbl) { if (t >= 0) lo = Math.min(lo, t); else if (head < 0) lo = 0; }          // a table that begins on the page before: from the page's first line
      else { let h = -1; for (let i = i0; i >= 0; i--) if (L[i].head === 'sec' || L[i].head === 'banner') { h = i; break; } lo = h >= 0 ? Math.min(lo, h) : (pi === 0 && i0 > 0 && !L[i0].head ? Math.min(lo, 0) : lo); }
      if (pi > 0) lo = 0;
      const title = t >= 0 ? (/^(?:TABLE|Table)\s+([A-Z]?[\d.]+)/.exec(L[t].text) || [])[1] : null;
      let skip = headOnly && pi === 0 && !L.slice(i0, i1 + 1).some(l => l.head === 'sec');
      hi = L.length - 1;
      for (let i = i1 + 1; i < L.length; i++) {
        const h = L[i].head;
        if (h === 'sec' || h === 'banner') { if (skip && h === 'sec') { skip = false; continue; } hi = i - 1; break; }
        if (h === 'table' && tbl) { const n = (/^(?:TABLE|Table)\s+([A-Z]?[\d.]+)/.exec(L[i].text) || [])[1]; if (!title || n !== title) { hi = i - 1; break; } }
      }
      carry = hi === L.length - 1;
    } else if (carry) {
      lo = 0; hi = L.length - 1;
      for (let i = 0; i < L.length; i++) { const h = L[i].head; if (h === 'sec' || h === 'banner') { hi = i - 1; carry = false; break; } }
      if (hi < 0) continue;
    } else continue;
    const ls = L.slice(lo, hi + 1);
    if (!ls.length) continue;
    const x0 = Math.max(0, Math.min(...ls.map(l => l.x0)) - 4), x1 = Math.min(612, Math.max(...ls.map(l => l.x1)) + 4);
    const prose = ls.some(l => l.head === 'sec' || l.head === 'banner'), mid = pt.left != null && pt.right ? (pt.left + pt.right) / 2 : null;
    cited.push({ page: pt.p, x0, x1, y0: Math.min(...ls.map(l => l.y0)) - 0.5, y1: Math.max(...ls.map(l => l.y1)), col: -1, lines: [lo, hi],
                 table: ls.some(l => l.head === 'table') || undefined,
                 xr: prose && pt.right ? pt.right : undefined,                                                       // a block of text runs to the column's right edge; a table's own rules end it
                 sym: mid != null && ls.some(l => l.head === 'banner' && Math.abs((l.x0 + l.x1) / 2 - mid) <= 4) ? mid : undefined });   // a centred heading sits centred in its block
  }
  if (!cited.length) for (const sg of segments) cited.push(sg);
  const byPage = new Map(parts.map(pt => [pt.p, { items: pt.lines.flatMap(ln => ln.items.map(it => ({ ...it, b: false }))), g: null }]));
  if (/ \| | › /.test(String(ptr.highlight || ''))) for (const sg of segments) sg.tbl = true;      // (384.72) see sheetOf
  return finishClip({ ok: true, segments, marks, text: texts.join(' '), pages, truncated: false, cited }, (p) => byPage.get(p) || { items: [], g: null });
}

// ------------------------------------------------------------------------------------------------ painting (browser only)
// container: an element. (384 one picture) The clipping is appended as ONE canvas: its pieces set one under the other as one column
// of the book reads (clip.sheet, see sheetOf). Only where a segment is a whole page (a sideways page) is each segment its own canvas.
// TWO TONES (owner, 2026-10-25, and 384: "Should really only ever be two tones"): the cited code is washed pale yellow and the words
// that decide the answer - the sentence, the table row, a heading cited alone - are ONE stronger gold on top of it. Nothing else: the
// exception's orange mark is gone (every exception question's deciding words are its 'cite' mark, the darker gold), each tone is one
// shape filled once (marks that overlap or touch never darken further), and on the whole page the wash runs under every gold mark,
// so the gold is always the same gold. Both are drawn with 'multiply': the paper is coloured, the print stays black.
const WASH = 'rgb(255, 245, 160)', STRONG = 'rgb(255, 224, 40)';
export const TONES = { wash: [255, 245, 160], strong: [255, 224, 40] };
const hasKeyMark = (marks) => marks.some(m => m.kind === 'cite' || m.kind === 'row');
// the darker gold: the deciding words; a heading (or an exception's label) only where nothing more precise is marked
const isDark = (m, keyed) => m.kind === 'cite' || m.kind === 'row' || (!keyed && (m.kind === 'heading' || m.kind === 'exception' || m.kind === 'exceptionNumber'));

// A closed outline through pts (corners of an outline made of horizontal and vertical edges), each corner rounded by r (less where an
// edge is short): convex and concave corners alike, so a highlight over several lines reads as one soft-cornered shape.
function roundedPoly(path, pts, r) {
  const q = [];
  for (const p of pts) { const l = q[q.length - 1]; if (!l || Math.abs(l[0] - p[0]) > 0.01 || Math.abs(l[1] - p[1]) > 0.01) q.push(p); }
  while (q.length > 1 && Math.abs(q[0][0] - q[q.length - 1][0]) <= 0.01 && Math.abs(q[0][1] - q[q.length - 1][1]) <= 0.01) q.pop();
  for (let again = true; again && q.length > 4;) {                    // a corner on a straight edge is no corner
    again = false;
    for (let i = 0; i < q.length; i++) {
      const a = q[(i - 1 + q.length) % q.length], b = q[i], c = q[(i + 1) % q.length];
      if ((Math.abs(a[0] - b[0]) < 0.01 && Math.abs(b[0] - c[0]) < 0.01) || (Math.abs(a[1] - b[1]) < 0.01 && Math.abs(b[1] - c[1]) < 0.01)) { q.splice(i, 1); again = true; break; }
    }
  }
  const n = q.length;
  if (n < 3) return;
  const len = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const a0 = q[n - 1], b0 = q[0];
  path.moveTo((a0[0] + b0[0]) / 2, (a0[1] + b0[1]) / 2);
  for (let i = 0; i < n; i++) {
    const p = q[i], prev = q[(i - 1 + n) % n], next = q[(i + 1) % n];
    path.arcTo(p[0], p[1], next[0], next[1], Math.max(0, Math.min(r, len(prev, p) / 2, len(p, next) / 2)));
  }
  path.closePath();
}

// THE MARKER, DRAWN ONCE ("the highlighting is perfectly ... not like weirdly highlighted ... where it goes slightly above the word ...
// The edges of the highlight need to be nice as well and cohesive"). bands: one per marked line, in picture pixels: x0..x1 the words,
// t..b their ink (the tallest letters to the descenders), em the type size, lp the pitch of the lines there, cl / cr an end that is a
// cut between two sentences (no extra room there). Each line gets the same room above and below its ink - half the space between two
// lines of its paragraph, 0.08-0.2 em - and 0.14 em past its first and last letters; lines that follow one another meet halfway
// between them (no gap, no overlap); lines that touch and overlap sideways are ONE shape whose corners are all rounded alike.
// The outline of a union of rectangles ({x0, x1, t, b}): its boundary loops, corners in order - each outer loop clockwise on the
// screen and each hole the other way, so a nonzero fill leaves the holes open. For a group of marks that is not a simple stack of
// lines (two marks on one line under one above): one outline, so every corner can be rounded alike and no seam shows where they meet.
function unionLoops(rects) {
  const xs = [...new Set(rects.flatMap(r => [r.x0, r.x1]))].sort((a, b) => a - b);
  const ys = [...new Set(rects.flatMap(r => [r.t, r.b]))].sort((a, b) => a - b);
  const nx = xs.length - 1, ny = ys.length - 1;
  if (nx < 1 || ny < 1) return [];
  const cov = new Uint8Array(nx * ny);
  for (const r of rects) {
    const i0 = xs.indexOf(r.x0), i1 = xs.indexOf(r.x1), j0 = ys.indexOf(r.t), j1 = ys.indexOf(r.b);
    for (let j = j0; j < j1; j++) for (let i = i0; i < i1; i++) cov[j * nx + i] = 1;
  }
  const at = (i, j) => i >= 0 && j >= 0 && i < nx && j < ny && cov[j * nx + i] === 1;
  const next = new Map(), key = (i, j) => i + ',' + j;
  const add = (a, b) => { const k = key(a[0], a[1]); if (!next.has(k)) next.set(k, []); next.get(k).push(b); };
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    if (!at(i, j)) continue;
    if (!at(i, j - 1)) add([i, j], [i + 1, j]);
    if (!at(i + 1, j)) add([i + 1, j], [i + 1, j + 1]);
    if (!at(i, j + 1)) add([i + 1, j + 1], [i, j + 1]);
    if (!at(i - 1, j)) add([i, j + 1], [i, j]);
  }
  const loops = [];
  for (const [k0, list] of next) {
    while (list.length) {
      const start = k0.split(',').map(Number), loop = [start];
      let cur = list.pop();
      for (let guard = 0; guard < 100000; guard++) {
        const kk = key(cur[0], cur[1]);
        if (kk === k0) break;
        loop.push(cur);
        const nl = next.get(kk);
        if (!nl || !nl.length) break;
        cur = nl.pop();
      }
      if (loop.length >= 4) loops.push(loop.map(([i, j]) => [xs[i], ys[j]]));
    }
  }
  return loops;
}

export function markerPath(bands) {
  if (!bands || !bands.length) return null;
  let N = bands.filter(b => b && b.x1 > b.x0 && b.b > b.t).map(b => {
    const em = b.em || 10, lp = b.lp || 1.15 * em;
    const pad = Math.min(0.2 * em, Math.max(0.08 * em, (lp - (b.b - b.t)) / 2)), px = 0.14 * em;
    return { t: b.top != null ? b.top : b.t - pad, b: b.bot != null ? b.bot : b.b + pad, c: (b.t + b.b) / 2, em, x0: b.x0 - (b.cl ? 0 : px), x1: b.x1 + (b.cr ? 0 : px),
             it: b.t, ib: b.b, pad, rt: b.top != null, rb: b.bot != null, ruled: b.top != null || b.bot != null, ra: b.ruleAbove, rbl: b.ruleBelow };
  }).sort((u, v) => u.c - v.c || u.x0 - v.x0);
  if (!N.length) return null;
  const sameLine = (u, v) => Math.abs(u.c - v.c) < 0.33 * Math.min(u.em, v.em);
  // marks on one line that touch are one
  for (let again = true; again;) {
    again = false;
    for (let i = 0; i < N.length && !again; i++) for (let j = i + 1; j < N.length && !again; j++) {
      const u = N[i], v = N[j];
      if (sameLine(u, v) && v.x0 <= u.x1 + 0.3 * u.em && u.x0 <= v.x1 + 0.3 * u.em) {
        u.x0 = Math.min(u.x0, v.x0); u.x1 = Math.max(u.x1, v.x1); u.t = Math.min(u.t, v.t); u.b = Math.max(u.b, v.b); u.em = Math.max(u.em, v.em);
        u.it = Math.min(u.it, v.it); u.ib = Math.max(u.ib, v.ib); u.pad = Math.min(u.pad, v.pad); u.rt = u.rt || v.rt; u.rb = u.rb || v.rb; u.ruled = u.ruled || v.ruled;
        if (v.ra != null) u.ra = u.ra == null ? v.ra : Math.max(u.ra, v.ra);
        if (v.rbl != null) u.rbl = u.rbl == null ? v.rbl : Math.min(u.rbl, v.rbl);
        N.splice(j, 1); again = true;
      }
    }
  }
  N.sort((u, v) => u.c - v.c || u.x0 - v.x0);
  // the next line down meets this one halfway
  const parent = N.map((_, i) => i), find = (i) => (parent[i] === i ? i : (parent[i] = find(parent[i])));
  const below = N.map(() => []);
  for (let i = 0; i < N.length; i++) {
    const u = N[i];
    const next = N.filter(v => v.c - u.c >= 0.33 * u.em && v.c - u.c <= 1.9 * u.em && Math.min(u.x1, v.x1) - Math.max(u.x0, v.x0) > 0.5);
    if (!next.length) continue;
    const c0 = Math.min(...next.map(v => v.c));
    for (const v of next.filter(w => sameLine(w, { c: c0, em: w.em }))) {
      if (v.t - u.b >= 0.6 * Math.min(u.em, v.em)) continue;
      if ((u.rbl != null && u.rbl < v.it) || (v.ra != null && v.ra > u.ib)) continue;   // a rule between them: two rows, not one passage
      if (!u.ruled && !v.ruled) { const mid = (u.b + v.t) / 2; u.b = mid; v.t = mid; } else if (v.t > u.b) continue;
      below[i].push(N.indexOf(v)); parent[find(i)] = find(N.indexOf(v));
    }
  }
  const groups = new Map();
  N.forEach((u, i) => { const r = find(i); if (!groups.has(r)) groups.set(r, []); groups.get(r).push(u); });
  const path = new Path2D();
  for (const g of groups.values()) {
    g.sort((u, v) => u.c - v.c);
    // one shape, one room: its top and bottom edges stand as far off its letters as each other (the tightest line's room - a
    // passage of list items set wide apart would otherwise take more room under its last line than over its first)
    const P = Math.min(...g.map(u => u.pad));
    for (const u of g) {
      if (!u.rt && !g.some(v => v !== u && Math.abs(v.b - u.t) < 0.5 && Math.min(u.x1, v.x1) - Math.max(u.x0, v.x0) > 0.5)) u.t = u.it - P;
      if (!u.rb && !g.some(v => v !== u && Math.abs(v.t - u.b) < 0.5 && Math.min(u.x1, v.x1) - Math.max(u.x0, v.x0) > 0.5)) u.b = u.ib + P;
    }
    const chain = g.every((u, k) => k === 0 || (!sameLine(u, g[k - 1]) && Math.abs(u.t - g[k - 1].b) < 0.5));
    const R = 0.2 * Math.min(...g.map(u => u.em));
    if (!chain) { for (const loop of unionLoops(g)) roundedPoly(path, loop, R); continue; }
    // the ends of lines that are nearly level are made level (a justified column's lines end a hair apart): a clean edge, no notches
    for (const side of ['x0', 'x1']) for (let k = 1; k < g.length; k++) {
      if (Math.abs(g[k][side] - g[k - 1][side]) < 0.2 * g[k].em) {
        const v = side === 'x0' ? Math.min(g[k][side], g[k - 1][side]) : Math.max(g[k][side], g[k - 1][side]);
        for (let j = k; j >= 0 && Math.abs(g[j][side] - v) < 0.2 * g[k].em; j--) g[j][side] = v;
        g[k][side] = v;
      }
    }
    const pts = [];
    for (const u of g) pts.push([u.x1, u.t], [u.x1, u.b]);
    for (let k = g.length - 1; k >= 0; k--) pts.push([g[k].x0, g[k].b], [g[k].x0, g[k].t]);
    roundedPoly(path, pts, R);
  }
  return path;
}
export function fillMarker(ctx, bands, color) {
  const path = markerPath(bands);
  if (!path) return;
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = color || STRONG; ctx.fill(path, 'nonzero'); ctx.restore();
}
// A county mark is placed from Times widths on a booklet set in Calibri, so on a long line it can stop inside a word ("the la|ne") or
// reach into the next. Its ends are moved onto the words it covers, read off the picture's own pixels (before the gold is laid): the
// line's letters, a space being a gap wider than a letter's; a word is marked when the mark covers at least half of it (the rule the
// column picture uses too).
function snapBand(ctx, b) {
  const W = ctx.canvas.width, H = ctx.canvas.height, em = b.em;
  const X0 = Math.max(0, Math.floor(b.x0 - 1.5 * em)), X1 = Math.min(W, Math.ceil(b.x1 + 1.5 * em));
  const Y0 = Math.max(0, Math.floor(b.t + 0.1 * em)), Y1 = Math.min(H, Math.ceil(b.b - 0.05 * em));
  if (X1 - X0 < 4 || Y1 - Y0 < 3) return;
  let D; try { D = ctx.getImageData(X0, Y0, X1 - X0, Y1 - Y0).data; } catch (e) { return; }
  const w = X1 - X0, h = Y1 - Y0, ink = new Uint8Array(w);
  for (let x = 0; x < w; x++) for (let y = 0; y < h; y++) { const i = (y * w + x) * 4; if (D[i] + D[i + 1] + D[i + 2] < 330) { ink[x] = 1; break; } }
  const gap = Math.max(2, 0.16 * em), words = [];
  let s0 = -1, last = -1;
  for (let x = 0; x < w; x++) { if (!ink[x]) continue; if (s0 < 0) s0 = x; else if (x - last > gap) { words.push([s0, last]); s0 = x; } last = x; }
  if (s0 >= 0) words.push([s0, last]);
  const on = words.filter(([a, z]) => Math.min(z + 1, b.x1 - X0) - Math.max(a, b.x0 - X0) >= 0.5 * (z + 1 - a));
  if (!on.length) return;
  const nx0 = X0 + on[0][0], nx1 = X0 + on[on.length - 1][1] + 1;
  if (Math.abs(nx0 - b.x0) < 1.5 * em && Math.abs(nx1 - b.x1) < 1.5 * em) { b.x0 = nx0; b.x1 = nx1; }
}

// AN OUTER EDGE CUTS NOTHING. A cut is made 2pt or more clear of its lines' letters, but a mark printed in the margin beside the line
// above or below - the book's deletion arrow, a change bar's end - can reach across it and showed as a sliver on the picture's top or
// bottom edge. The edge is moved to the nearest row with nothing on it (an upright table rule that runs on through the edge does not
// count): inward up to 3.6pt (the cut's own lines stand 3.9pt or more inside it: a clean row is never in a letter), else outward up to EDGE_ROOM, so the mark is
// either left out whole or taken in whole. D: the piece's pixels; r: its first row shown (dir 1) or one past its last (dir -1).
const EDGE_ROOM = 9;
function settleEdge(D, W, H, r, dir, s, inwardOnly) {
  const ink = (x, y) => { const i = (y * W + x) * 4; return D[i] + D[i + 1] + D[i + 2] < 600; };
  const edge = dir > 0 ? r : r - 1;
  if (edge < 0 || edge >= H) return r;
  const L = Math.round(2.5 * s), rule = new Uint8Array(W);
  for (let x = 0; x < W; x++) { let all = true; for (let k = -L; k <= L && all; k++) { const y = edge + k; if (y >= 0 && y < H && !ink(x, y)) all = false; } rule[x] = all ? 1 : 0; }
  const clean = (y) => { for (let x = 0; x < W; x++) if (!rule[x] && ink(x, y)) return false; return true; };
  if (clean(edge)) return r;
  for (let k = 1; k <= Math.round(3.6 * s); k++) { const y = edge + dir * k; if (y < 0 || y >= H) break; if (clean(y)) return dir > 0 ? y : y + 1; }
  if (inwardOnly) return r;
  for (let k = 1; k <= Math.round((EDGE_ROOM - 0.2) * s); k++) { const y = edge - dir * k; if (y < 0 || y >= H) break; if (clean(y)) return dir > 0 ? y : y + 1; }
  return r;
}

// A TABLE ROW'S GOLD FILLS ITS ROW. A row is ruled above and below; the marker's even room around the words reached a hair past a
// rule (a gold sliver under the line, in the next row's cell) or stopped a hair short of it. A row's band (b.row) takes its edge from
// the rule where there is one within 0.45 em of its letters - just inside it - and keeps its even room where there is none.
function ruleBand(ctx, b, clampOnly) {
  const W = ctx.canvas.width, H = ctx.canvas.height, em = b.em;
  const X0 = Math.max(0, Math.floor(b.x0)), X1 = Math.min(W, Math.ceil(b.x1)), w = X1 - X0;
  // (384) a table row looks for its rules as far as its reach (the next row's start, findRow): a row of two or three lines is filled to
  // the rules round all of it, not only round the line its label is on; an ordinary band looks 0.45 em out, as before
  const far = !clampOnly && b.row;
  const Y0 = Math.max(0, Math.floor(far && b.lt != null ? Math.min(b.t - 0.45 * em, b.lt) : b.t - 0.45 * em));
  const Y1 = Math.min(H, Math.ceil(far && b.lb != null ? Math.max(b.b + 0.45 * em, b.lb) : b.b + 0.45 * em));
  if (w < 8 || Y1 - Y0 < 4) return;
  let D; try { D = ctx.getImageData(X0, Y0, w, Y1 - Y0).data; } catch (e) { return; }
  // a rule: a level run of ink (its faint anti-aliased edge row counts) across half the band or more
  const need = Math.max(0.5 * w, 2.5 * em);         // (and long in its own right: a dash or a letter's bar beside a short word is not a rule)
  const ruled = (y) => { let run = 0, best = 0; for (let x = 0; x < w; x++) { const i = ((y - Y0) * w + x) * 4; if (D[i] + D[i + 1] + D[i + 2] < 600) { run++; if (run > best) best = run; } else run = 0; } return best >= need; };
  // (a tight table's rule can lie inside its descenders' room: the search down starts just under the baseline)
  const base = b.b - (DSC / (ASC + DSC)) * Math.min(b.b - b.t, 0.9 * em);
  // an ordinary band (clampOnly) keeps its even room and only stops at a rule that lies inside that room
  const pad = Math.min(0.2 * em, Math.max(0.08 * em, ((b.lp || 1.15 * em) - (b.b - b.t)) / 2));
  // (the rules found are kept, so the marker never joins two lines across a rule)
  for (let y = Math.floor(b.t) - 1; y >= Y0; y--) if (ruled(y)) { b.ruleAbove = y; if (!clampOnly || y + 1 > b.t - pad) b.top = y + 1; break; }
  for (let y = Math.ceil(base) + 1; y < Y1; y++) if (ruled(y)) { b.ruleBelow = y; if (!clampOnly || y < b.b + pad) b.bot = y; break; }
  if (far) { sideRules(ctx, b); mergedLabel(ctx, b); }
}
// (384) A LABEL CELL MERGED ACROSS ROWS ("Protected above- / ground tanks" beside "Less than or equal to 6,000" and "Greater than 6,000")
// has no rule where the row asked about ends, so the row's gold, ending on that rule, cut through the label's second line. Where the
// rule above or below the row does not run through its first cell, the row's gold starts at that cell's right-hand rule, and the label
// is marked on its own: its lines of print in that cell, with the marker's even room, never sliced.
function mergedLabel(ctx, b) {
  const W = ctx.canvas.width, H = ctx.canvas.height, em = b.em;
  const top = b.top != null ? b.top : b.t, bot = b.bot != null ? b.bot : b.b;
  const y0 = Math.max(0, Math.ceil(top + 1)), y1 = Math.min(H, Math.floor(bot - 1)), h = y1 - y0;
  if (h < 4 || (b.ruleAbove == null && b.ruleBelow == null)) return;
  const X0 = Math.max(0, Math.floor(b.x0)), X1 = Math.min(W, Math.ceil(b.x1)), w = X1 - X0;
  if (w < 8) return;
  const span = Math.round(6 * em), Y0 = Math.max(0, y0 - span), Y1 = Math.min(H, y1 + span), hh = Y1 - Y0;
  let D; try { D = ctx.getImageData(X0, Y0, w, hh).data; } catch (e) { return; }
  const ink = (x, y) => { const i = ((y - Y0) * w + (x - X0)) * 4; return D[i] + D[i + 1] + D[i + 2] < 600; };
  // the first cell's right-hand rule: the first column of ink the row's whole height, right of the label
  let cx = -1;
  for (let x = X0 + 2; x < X1 - 2 && cx < 0; x++) { let n = 0; for (let y = y0; y < y1; y++) if (ink(x, y)) n++; if (n >= 0.95 * h) cx = x; }
  if (cx < 0 || cx - X0 < 1.5 * em) return;
  const across = (y) => { if (y == null || y < Y0 || y >= Y1) return true; let n = 0; for (let x = X0 + 2; x < cx - 1; x++) if (ink(x, y)) n++; return n >= 0.8 * (cx - 1 - X0 - 2); };
  if (across(b.ruleAbove) && across(b.ruleBelow)) return;                       // the rules run through the first cell: an ordinary row
  // the label's own lines: rows of ink in the first cell, from the row's top down (or up) to the cell's own rules
  const level = (y) => { let n = 0; for (let x = X0 + 2; x < cx - 1; x++) if (ink(x, y)) n++; return n >= 0.8 * (cx - 1 - X0 - 2); };
  let ct = Y0, cb = Y1 - 1;
  for (let y = y0; y >= Y0; y--) if (level(y)) { ct = y + 1; break; }
  for (let y = y1; y < Y1; y++) if (level(y)) { cb = y - 1; break; }
  let it = -1, ib = -1;
  for (let y = ct; y <= cb; y++) { let any = false; for (let x = X0 + 2; x < cx - 1 && !any; x++) if (ink(x, y)) any = true; if (any) { if (it < 0) it = y; ib = y; } }
  if (it < 0) return;
  b.extra = { x0: b.x0, x1: cx, t: it, b: ib + 1, em, lp: null, cl: true, cr: true, snap: false, row: false };
  b.x0 = cx + 1; b.cl = true;
}
// (384) A ROW'S GOLD RUNS FROM RULE TO RULE ACROSS THE TABLE. It ran from the label's first letter to the last cell's last letter, so a
// value centred in its cell left a pale strip before the table's edge and an indented label a pale step at its start. Each side goes
// out to the nearest upright rule (a column of ink the whole height of the row, inside the rules above and below) within 8 em, just
// inside it; where there is none it stays where it was.
function sideRules(ctx, b) {
  const W = ctx.canvas.width, H = ctx.canvas.height, em = b.em;
  const top = b.top != null ? b.top : b.t, bot = b.bot != null ? b.bot : b.b;
  const y0 = Math.max(0, Math.ceil(top + 1)), y1 = Math.min(H, Math.floor(bot - 1)), h = y1 - y0;
  if (h < 4) return;
  const L = Math.max(0, Math.floor(b.x0 - 8 * em)), R = Math.min(W, Math.ceil(b.x1 + 8 * em));
  let D; try { D = ctx.getImageData(L, y0, R - L, h).data; } catch (e) { return; }
  const w = R - L;
  const upright = (x) => { let n = 0; for (let y = 0; y < h; y++) { const i = (y * w + (x - L)) * 4; if (D[i] + D[i + 1] + D[i + 2] < 600) n++; } return n >= 0.95 * h; };
  // (an edge on a rule takes no marker's room past it: cl / cr)
  for (let x = Math.ceil(b.x1); x < R; x++) if (upright(x)) { b.x1 = x; b.cr = true; break; }
  for (let x = Math.floor(b.x0) - 1; x >= L; x--) if (upright(x)) { b.x0 = x + 1; b.cl = true; break; }
  // (384 cropfix) a value centred in a wide last column (a county table's right-hand cell, 100pt and more of paper past its words) is further from
  // the border than 8 em: the row runs on over paper to the first upright, however far - and stops if any print stands in the way
  if (!b.cr || !b.cl) {
    let F; try { F = ctx.getImageData(0, y0, W, h).data; } catch (e) { F = null; }
    if (F) {
      const col = (x) => { let n = 0; for (let y = 0; y < h; y++) { const i = (y * W + x) * 4; if (F[i] + F[i + 1] + F[i + 2] < 600) n++; } return n; };
      if (!b.cr) for (let x = Math.ceil(b.x1); x < W; x++) { const n = col(x); if (n >= 0.95 * h) { b.x1 = x; b.cr = true; break; } if (n) break; }
      if (!b.cl) for (let x = Math.floor(b.x0) - 1; x >= 0; x--) { const n = col(x); if (n >= 0.95 * h) { b.x0 = x + 1; b.cl = true; break; } if (n) break; }
    }
  }
  // (384 county tables) the county booklet's tables have no outer upright rules: the table ends where its horizontal rules end. A county
  // row (snap) with no upright rule on a side runs out to the end of the rule above or below it, just inside it.
  if (b.snap && (!b.cr || !b.cl) && (b.ruleAbove != null || b.ruleBelow != null)) {
    const ry = b.ruleAbove != null ? b.ruleAbove : b.ruleBelow;
    let R2; try { R2 = ctx.getImageData(0, Math.max(0, ry - 1), W, Math.min(3, H - Math.max(0, ry - 1))).data; } catch (e) { return; }
    const rows = R2.length / (W * 4);
    const onRule = (x) => { for (let r = 0; r < rows; r++) { const i = (r * W + x) * 4; if (R2[i] + R2[i + 1] + R2[i + 2] < 600) return true; } return false; };
    const mid = Math.floor((b.x0 + b.x1) / 2);
    if (onRule(mid)) {
      if (!b.cr) { let x = Math.ceil(b.x1); while (x < W && onRule(x)) x++; if (x - 1 > b.x1 && x - 1 - b.x1 < 12 * em) { b.x1 = x - 1; b.cr = true; } }
      if (!b.cl) { let x = Math.floor(b.x0); while (x >= 0 && onRule(x)) x--; if (x + 1 < b.x0 && b.x0 - (x + 1) < 12 * em) { b.x0 = x + 1; b.cl = true; } }
    }
  }
}

// What is left on an outer edge that no clean row could clear - a fragment of the line above or below, or of a mark in the margin
// beside it (the book's deletion arrow sits half in the next line's room) - is not the citation's: the cut stands clear of the
// citation's own letters, so nothing touching the edge within 3.6pt of it belongs to them. Such a fragment (ink joined to the edge
// that ends inside that strip) is painted out with the paper; anything that runs on further in (a change bar, a table's rule, a
// letter that reaches the edge) is left as printed, and an upright bar running through the strip is kept whole.
function clearEdge(ctx, W, H, r, dir, s) {
  const e = dir > 0 ? r : r - 1, Z = Math.round(3.6 * s);
  const y0 = dir > 0 ? e : Math.max(0, e - Z), y1 = dir > 0 ? Math.min(H - 1, e + Z) : e, h = y1 - y0 + 1;
  if (e < 0 || e >= H || h < 2) return;
  let img; try { img = ctx.getImageData(0, y0, W, h); } catch (err) { return; }
  const D0 = img.data, ink0 = (x, y) => { const i = (y * W + x) * 4; return D0[i] + D0[i + 1] + D0[i + 2] < 600; };
  // an upright bar or rule running through the strip (a change bar beside the lines) is not part of any fragment beside it
  const bar = new Uint8Array(W);
  for (let x = 0; x < W; x++) { let all = true; for (let y = 0; y < h && all; y++) if (!ink0(x, y)) all = false; bar[x] = all ? 1 : 0; }
  const D = D0, ink = (x, y) => !bar[x] && ink0(x, y);
  const er = e - y0, far = dir > 0 ? h - 1 : 0, seen = new Uint8Array(W * h);
  let changed = false;
  for (let x = 0; x < W; x++) {
    if (seen[er * W + x] || !ink(x, er)) continue;
    const st = [er * W + x], blob = []; seen[er * W + x] = 1; let deep = false;
    while (st.length) {
      const q = st.pop(), qx = q % W, qy = (q - qx) / W; blob.push(q);
      if (qy === far) deep = true;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = qx + dx, ny = qy + dy;
        if (nx < 0 || nx >= W || ny < 0 || ny >= h) continue;
        const k = ny * W + nx; if (seen[k] || !ink(nx, ny)) continue;
        seen[k] = 1; st.push(k);
      }
    }
    if (deep) continue;
    for (const q of blob) { const i = q * 4; D[i] = 255; D[i + 1] = 255; D[i + 2] = 255; }
    changed = true;
  }
  if (changed) ctx.putImageData(img, 0, y0);
}

export async function paint(doc, clip, container, opts = {}) {
  const scale = opts.scale || 1.6;
  const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
  const s = scale * Math.min(dpr, 2);
  const segs = clip.segments || [];
  if (!segs.length) return;
  const one = (i) => ({ pieces: [{ i, dx: 0, top: segs[i].y1, bot: segs[i].y0, gap: 0 }] });
  if (segs.some(sg => sg.whole)) {                                  // a whole page among them: each segment its own canvas
    for (let i = 0; i < segs.length; i++) {
      if (segs[i].whole) await paintWhole(await doc.getPage(segs[i].page), segs[i].rotation || 0, container, s, dpr);
      else container.appendChild(await paintSheet(doc, clip, one(i), s, dpr, opts));
    }
    return;
  }
  const sheet = segs.length === 1 ? one(0) : (clip.sheet || { pieces: segs.map((sg, i) => ({ i, dx: 0, top: sg.y1, bot: sg.y0, gap: i ? 4 : 0 })) });
  container.appendChild(await paintSheet(doc, clip, sheet, s, dpr, opts));
}
// (384 cropfix) A TABLE IS SHOWN TO ITS OWN BORDERS. A cut is made from the words it holds (a county cut: its lines' ends; a book table: its
// column, to the gutter), and a table's border and the ends of its rules can stand outside that: Table 1004.5 of the book runs 5pt over the
// gutter, so its right-hand border and the right end of every rule were cut off, and the row's gold, which runs out to the border it finds
// (sideRules), stopped at the value's last letter; a county table's border stands 20-45pt beyond its cells' words. Each piece is rendered
// FRAME_ROOM points wider on both sides and taken out to the end of the long horizontal rules that cross its cut (with the border at their
// end and a hair of paper), where nothing but those rules and the table's uprights stands in what is added - so the other column's words
// never come in. A piece with no rule crossing its edge is cut exactly as before.
const FRAME_ROOM = 64;
const inkPx = (D, W, x, y) => { const i = (y * W + x) * 4; return D[i] + D[i + 1] + D[i + 2] < 600; };
// the long horizontal rules: runs of ink along one pixel row, minLen or longer -> [{ y, x0, x1 }] (x1 one past the run)
function hRuleRuns(D, W, H, minLen, ya = 0, yb = H) {
  const out = [];
  for (let y = Math.max(0, ya); y < Math.min(H, yb); y++) {
    let run = 0;
    for (let x = 0; x <= W; x++) {
      if (x < W && inkPx(D, W, x, y)) { run++; continue; }
      if (run >= minLen) out.push({ y, x0: x - run, x1: x });
      run = 0;
    }
  }
  return out;
}
// a long horizontal rule that runs into the left or right side of a cut (W x H): the cut stops inside a table
function ruleAtSide(ctx, W, H, s, ra, rb) {
  let D; try { D = ctx.getImageData(0, 0, W, H).data; } catch (e) { return false; }
  const L = Math.min(W, Math.round(20 * s));
  for (let y = Math.max(0, Math.floor(ra - 1.5 * s)); y < Math.min(H, Math.ceil(rb + 1.5 * s)); y++) {
    if (inkPx(D, W, 0, y)) { let x = 0; while (x < L && inkPx(D, W, x, y)) x++; if (x >= L) return true; }
    if (inkPx(D, W, W - 1, y)) { let x = W - 1; while (W - 1 - x < L && inkPx(D, W, x, y)) x--; if (W - 1 - x >= L) return true; }
  }
  return false;
}
// cut [a, b) of a wide render (D, W x H), rows [ra, rb) shown -> the columns to show [na, nb)
function tableFrame(D, W, H, a, b, s, ra, rb) {
  const need = Math.min(20 * s, (b - a) / 2);
  let FL = Infinity, FR = -Infinity;
  // (the rules of the cut's own rows, and a hair either side: a rule of what is printed above or below the cut - another table's - is not this one's)
  for (const r of hRuleRuns(D, W, H, 30 * s, Math.floor(ra - 1.5 * s), Math.ceil(rb + 1.5 * s))) {
    if (Math.min(r.x1, b) - Math.max(r.x0, a) < need) continue;
    FL = Math.min(FL, r.x0); FR = Math.max(FR, r.x1);
  }
  if (!isFinite(FL)) return [a, b];
  const hair = Math.round(2 * s), hmin = 14 * s, vmin = 11 * s;
  const hrun = (x, y) => { let l = x, r = x; while (l > 0 && inkPx(D, W, l - 1, y) && x - l < hmin) l--; while (r < W - 1 && inkPx(D, W, r + 1, y) && r - x < hmin) r++; return r - l + 1; };
  // nothing in columns [c0, c1) but rules: a pixel of ink is on a long horizontal run, on a long upright run, or in the border's own columns
  const ya = Math.max(0, Math.floor(ra - s)), yb = Math.min(H, Math.ceil(rb + s));
  const onlyRules = (c0, c1, border) => {
    for (let x = c0; x < c1; x++) {
      if (Math.abs(x - border) <= 1) continue;
      let y = ya;
      while (y < yb) {
        if (!inkPx(D, W, x, y)) { y++; continue; }
        let e = y; while (e < yb && inkPx(D, W, x, e)) e++;
        if (e - y < vmin) for (let yy = y; yy < e; yy++) if (hrun(x, yy) < hmin) return false;
        y = e;
      }
    }
    return true;
  };
  // or: the frame's end is the table's border - an upright down most of the piece at the rules' end - and nothing but rules stands past it: what is
  // between the cut and the border is the table's own (a cell's words the cut sliced: "See Section 402.8.2" in Table 1004.5 reaches its border)
  const border = (x) => { let n = 0; for (let y = ya; y < yb; y++) if (inkPx(D, W, x, y) || (x > 0 && inkPx(D, W, x - 1, y)) || (x + 1 < W && inkPx(D, W, x + 1, y))) n++; return n >= 0.5 * (yb - ya); };
  let na = a, nb = b;
  if (FR > b) { const e = Math.min(W, FR + hair); if (onlyRules(b, e, FR - 1) || (FR < W && border(FR - 1) && onlyRules(FR + 1, e, FR - 1))) nb = e; }
  if (FL < a) { const e = Math.max(0, FL - hair); if (onlyRules(e, a, FL) || (FL > 0 && border(FL) && onlyRules(e, FL - 1, FL))) na = e; }
  return [na, nb];
}
// a horizontal rule of a piece within R rows of row r: [first row, last row] of the run of rule rows whose middle is nearest r, or null
function ruleNear(cv, r, R, s) {
  const W = cv.width, H = cv.height, ya = Math.max(0, Math.floor(r - R)), yb = Math.min(H, Math.ceil(r + R) + 1);
  if (yb <= ya) return null;
  let D; try { D = cv.getContext('2d').getImageData(0, ya, W, yb - ya).data; } catch (e) { return null; }
  const need = Math.max(30 * s, 0.5 * W), rows = [];
  for (let y = 0; y < yb - ya; y++) { let run = 0, best = 0; for (let x = 0; x < W; x++) { if (inkPx(D, W, x, y)) { run++; if (run > best) best = run; } else run = 0; } rows.push(best >= need); }
  let best = null;
  for (let y = 0; y < rows.length; y++) {
    if (!rows[y]) continue;
    let e = y; while (e + 1 < rows.length && rows[e + 1]) e++;
    const g = [ya + y, ya + e], d = Math.abs((g[0] + g[1]) / 2 - r);
    if (!best || d < best.d) best = { g, d };
    y = e;
  }
  return best && best.g;
}
// a rule at a seam is the rule alone: a letter of the row beyond it that touches its faint edge (a descender of the line above, cut away) left a
// fleck on it. Each row of the rule is set to its own middle tone along the rule's run (an upright crossing it is left as printed).
function evenRule(cv, g) {
  const W = cv.width, H = cv.height, ctx = cv.getContext('2d');
  const ya = Math.max(0, g[0] - 2), yb = Math.min(H - 1, g[1] + 2);
  let img; try { img = ctx.getImageData(0, ya, W, yb - ya + 1); } catch (e) { return; }
  const D = img.data, v = (x, y) => { const i = ((y - ya) * W + x) * 4; return D[i] + D[i + 1] + D[i + 2]; };
  const upright = (x) => ya < g[0] && yb > g[1] && v(x, ya) < 600 && v(x, yb) < 600;
  for (let y = g[0]; y <= g[1]; y++) {
    let a = -1, best = [0, -1];
    for (let x = 0; x <= W; x++) { const on = x < W && v(x, y) < 600; if (on && a < 0) a = x; if (!on && a >= 0) { if (x - a > best[1] - best[0] + 1) best = [a, x - 1]; a = -1; } }
    if (best[1] - best[0] < 30) continue;
    const run = []; for (let x = best[0]; x <= best[1]; x++) if (!upright(x)) run.push([v(x, y), x]);
    if (!run.length) continue;
    run.sort((p, q) => p[0] - q[0]);
    const [m, mx] = run[run.length >> 1], im = ((y - ya) * W + mx) * 4;
    for (const [val, x] of run) {
      if (Math.abs(val - m) < 40) continue;
      const i = ((y - ya) * W + x) * 4; D[i] = D[im]; D[i + 1] = D[im + 1]; D[i + 2] = D[im + 2];
    }
  }
  ctx.putImageData(img, 0, ya);
}
// (384 cropfix) a table's outer edge ends on its rule: a cut made a hair above a group's closing rule (a county table's cells end 2-3pt over it)
// showed the table open at the foot. dir -1: the picture's top row r (the rule above it is taken in); 1: one past its last row. Only paper and
// the table's uprights may stand between the cut and the rule.
function closeOnRule(cv, r, dir, s) {
  const W = cv.width, H = cv.height, R = Math.round(3.5 * s);
  const ya = dir > 0 ? r : Math.max(0, r - R), yb = dir > 0 ? Math.min(H, r + R) : r;
  if (yb - ya < 1) return r;
  let D; try { D = cv.getContext('2d').getImageData(0, ya, W, yb - ya).data; } catch (e) { return r; }
  const h = yb - ya, ink = (x, y) => { const i = (y * W + x) * 4; return D[i] + D[i + 1] + D[i + 2] < 600; };
  const need = Math.max(30 * s, 0.5 * W);
  const ruled = (y) => { let run = 0; for (let x = 0; x < W; x++) { if (ink(x, y)) { if (++run >= need) return true; } else run = 0; } return false; };
  const order = []; for (let k = 0; k < h; k++) order.push(dir > 0 ? k : h - 1 - k);
  const at = order.findIndex(ruled);
  if (at < 0) return r;
  const between = order.slice(0, at);
  if (between.length) {
    const col = new Uint8Array(W); for (let x = 0; x < W; x++) { let all = true; for (const y of between) if (!ink(x, y)) { all = false; break; } col[x] = all ? 1 : 0; }
    for (const y of between) for (let x = 0; x < W; x++) if (ink(x, y) && !col[x] && !(col[x - 1] || col[x + 1])) return r;
  }
  let e = at; while (e + 1 < h && ruled(order[e + 1])) e++;
  return dir > 0 ? ya + order[e] + 1 : ya + order[e];
}
// the table's uprights in the cell beside a rule (dir -1: the cell above the rule's first row `edge`; 1: below its last row): the columns inked
// down the whole cell (to the next rule, or `lim`) -> { cols: [[x0, x1] ...], row } (row: a row of that cell to copy them from), or null
function uprightsBeside(cv, edge, dir, lim, s) {
  const W = cv.width, H = cv.height;
  let D; try { D = cv.getContext('2d').getImageData(0, 0, W, H).data; } catch (e) { return null; }
  const need = Math.max(30 * s, 0.5 * W);
  const ruled = (y) => { let run = 0; for (let x = 0; x < W; x++) { if (inkPx(D, W, x, y)) { if (++run >= need) return true; } else run = 0; } return false; };
  const a = edge + dir;
  let b = a;
  const inside = (v) => v >= 0 && v < H && (dir < 0 ? v >= lim : v < lim);
  if (!inside(a)) return null;
  while (inside(b + dir) && !ruled(b + dir) && Math.abs(b - a) < 60 * s) b += dir;
  const y0 = Math.min(a, b), y1 = Math.max(a, b), h = y1 - y0 + 1;
  if (h < 3) return null;
  const cols = [];
  for (let x = 0; x < W; x++) {
    let n = 0; for (let y = y0; y <= y1; y++) if (inkPx(D, W, x, y)) n++;
    if (n >= 0.95 * h) { if (cols.length && cols[cols.length - 1][1] === x - 1) cols[cols.length - 1][1] = x; else cols.push([x, x]); }
  }
  return cols.length ? { cols, row: Math.round((y0 + y1) / 2) } : null;
}
// one picture: each piece rendered as it lies on its page, then set in place on one canvas (rows and columns copied whole, so the
// print is not resampled); then the wash over all of it and the marker over the deciding words, in the picture's own pixels.
// opts.keepPlain: the picture before the marker is kept on the canvas (canvas._ifcPlain), for a caller that sets the words again.
async function paintSheet(doc, clip, sheet, s, dpr, opts) {
  const segs = clip.segments, parts = [];
  let y = 0;
  const last = sheet.pieces.length - 1;
  // (384 cropfix) the pieces of one table joined on a seam (rows left out between them, or the table running on over a page) are rendered on one
  // pixel grid, so the table's uprights fall in the same columns in every piece
  const joined = sheet.pieces.some(pc => pc.omit || pc.cont);
  for (const [k, pc] of sheet.pieces.entries()) {
    let seg = segs[pc.i];
    if (joined) seg = { ...seg, x0: Math.floor(seg.x0 * s) / s };
    const page = await doc.getPage(seg.page);
    const vp = page.getViewport({ scale: s });
    const H = page.view[3];
    // rendered with a little of the page above and below the cut, so an outer edge can be settled (see settleEdge)
    const rTop = Math.min(H, seg.y1 + EDGE_ROOM), rBot = Math.max(0, seg.y0 - EDGE_ROOM);
    const px0 = seg.x0 * s, py0 = (H - rTop) * s;
    // (384 cropfix) and FRAME_ROOM wider each side, where the table's border is looked for (a blurred picture is cut as the kit cut it)
    // (a rule that runs on past that room - a county table 50pt or more wider than its words - has the piece rendered again the page's width out)
    const cw = Math.max(1, Math.ceil((seg.x1 - seg.x0) * s)), ch = Math.max(1, Math.ceil((rTop - rBot) * s));
    // first as cut; only where a long rule runs into a side of the cut is it rendered again, wider (pass 1: FRAME_ROOM; pass 2: the page's width)
    let RX = 0, cv = null, ctx = null, na = 0, nb = cw;
    for (let pass = 0; pass < 3; pass++) {
      if (cv) { cv.width = 0; cv.height = 0; }
      cv = document.createElement('canvas');
      cv.width = cw + 2 * RX; cv.height = ch;
      ctx = cv.getContext('2d');
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, cv.width, cv.height);
      await page.render({ canvasContext: ctx, viewport: vp, transform: [1, 0, 0, 1, -(px0 - RX), -py0] }).promise;
      if (opts.blur) break;
      const ra = Math.round((rTop - pc.top) * s), rb = Math.round((rTop - pc.bot) * s);
      if (!pass) { if (!ruleAtSide(ctx, cw, ch, s, ra, rb)) break; RX = Math.round(FRAME_ROOM * s); continue; }
      na = RX; nb = RX + cw;
      try { [na, nb] = tableFrame(ctx.getImageData(0, 0, cv.width, cv.height).data, cv.width, cv.height, RX, RX + cw, s, ra, rb); } catch (e) { na = RX; nb = RX + cw; }
      const wide = Math.ceil(Math.max(seg.x0, page.view[2] - seg.x1) * s) + Math.round(2 * s);
      if (pass === 2 || (na > 0 && nb < cv.width) || wide <= RX) break;
      RX = wide;
    }
    if (RX) {
      const c2 = document.createElement('canvas'); c2.width = nb - na; c2.height = cv.height;
      const g2 = c2.getContext('2d'); g2.drawImage(cv, na, 0, nb - na, cv.height, 0, 0, nb - na, cv.height);
      cv.width = 0; cv.height = 0; cv = c2; ctx = g2;
      if (na !== RX || nb !== RX + cw) seg = { ...seg, x0: seg.x0 + (na - RX) / s, x1: seg.x0 + (nb - RX) / s, framed: true };
    }
    if (opts.blur && clip.hide) for (const h of clip.hide) if (h.page === seg.page) {
      let r = null;
      if (h.snap) { try { r = snapRect(ctx, h, s, px0, py0, H); } catch (e) { r = null; } }
      if (r) blurRect(ctx, r.x, r.y, r.w, r.h);
      else blurRect(ctx, h.x0 * s - px0, (H - h.y1) * s - py0, (h.x1 - h.x0) * s, (h.y1 - h.y0) * s);
    }
    let r0 = Math.max(0, Math.min(cv.height, Math.round((rTop - pc.top) * s)));
    let r1 = Math.max(r0, Math.min(cv.height, Math.round((rTop - pc.bot) * s)));
    if (k === 0 || k === last) {
      let D = null; try { D = ctx.getImageData(0, 0, cv.width, cv.height).data; } catch (e) { D = null; }
      if (D) {
        // (a picture with something hidden - a definition's term, the Hint's number - is never taken further out than its cut)
        if (k === 0) r0 = settleEdge(D, cv.width, cv.height, r0, 1, s, !!opts.blur);
        if (k === last) r1 = settleEdge(D, cv.width, cv.height, r1, -1, s, !!opts.blur);
        if (k === 0) clearEdge(ctx, cv.width, cv.height, r0, 1, s);
        if (k === last) clearEdge(ctx, cv.width, cv.height, r1, -1, s);
      }
    }
    if (seg.framed && !opts.blur) {
      if (k === last) r1 = Math.max(r0 + 1, closeOnRule(cv, r1, 1, s));
      if (k === 0) r0 = Math.min(r1 - 1, closeOnRule(cv, r0, -1, s));
    }
    parts.push({ seg, pc, cv, r0, r1, ry: rTop });
  }
  // (384 cropfix) THE SEAMS OF A TABLE. Where rows are left out (omit) the piece above ends on its own rule (the heading row's bottom rule, or a
  // row's) and the piece below starts on its rule, and the gap between them is a band of the table: its uprights - the border and the column
  // rules both pieces share - run on through it, with the dots of the omission in a cell of it (a piece below that is not the table - its notes
  // - closes the band with the table's rule). Where the table runs on over a page with nothing left out (cont), the two meet on ONE rule: the
  // piece above keeps its bottom rule and the piece below starts under its own top rule. A cut is moved to the rule found within 3.5pt of it.
  for (let k = 1; k < parts.length; k++) {
    const p = parts[k], q = parts[k - 1];
    if (!p.pc.omit && !p.pc.cont) continue;
    const rq = ruleNear(q.cv, q.r1, 3.5 * s, s), rp = ruleNear(p.cv, p.r0, 3.5 * s, s);
    if (rq) { q.r1 = Math.max(q.r0 + 1, rq[1] + 1); evenRule(q.cv, rq); }
    if (rp) { p.r0 = Math.min(p.r1 - 1, p.pc.cont && rq ? rp[1] + 1 : rp[0]); if (!(p.pc.cont && rq)) evenRule(p.cv, rp); }
    if (p.pc.omit) p.band = { up: uprightsBeside(q.cv, rq ? rq[0] : q.r1, -1, q.r0, s), down: rp ? uprightsBeside(p.cv, rp[1], 1, p.r1, s) : null, rule: rq };
  }
  let X0 = Infinity, X1 = -Infinity;
  for (const p of parts) { X0 = Math.min(X0, p.seg.x0 + p.pc.dx); X1 = Math.max(X1, p.seg.x1 + p.pc.dx); }
  for (const p of parts) {
    const gapAt = y;
    y += Math.round((p.pc.gap || 0) * s);
    p.x = Math.round((p.seg.x0 + p.pc.dx - X0) * s); p.y = y; p.omit = p.pc.omit ? [gapAt, y] : null;
    y += p.r1 - p.r0;
  }
  let canvas;
  if (parts.length === 1 && parts[0].r0 === 0 && parts[0].r1 === parts[0].cv.height && parts[0].x === 0 && parts[0].y === 0) canvas = parts[0].cv;
  else {
    canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.ceil((X1 - X0) * s), ...parts.map(p => p.x + p.cv.width)); canvas.height = Math.max(1, y);
    const g = canvas.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, canvas.width, canvas.height);
    for (const p of parts) if (p.r1 > p.r0) g.drawImage(p.cv, 0, p.r0, p.cv.width, p.r1 - p.r0, p.x, p.y, p.cv.width, p.r1 - p.r0);
    // (384.72) rows of a table left out: three dots in the middle of the gap, the way an omission is set; (384 cropfix) in a band of the table
    g.imageSmoothingEnabled = false;
    for (const [k, p] of parts.entries()) if (p.omit) {
      const q = parts[k - 1], B = p.band || {}, gy0 = p.omit[0], gy1 = p.omit[1];
      // the uprights both pieces share (in the picture's columns; a piece below with none - the notes - takes the ones above, and the band is closed)
      let cols = B.up ? B.up.cols.map(([a, b]) => [a + q.x, b + q.x]) : [];
      const below = B.down ? B.down.cols.map(([a, b]) => [a + p.x, b + p.x]) : null;
      if (below) cols = cols.filter(([a, b]) => below.some(([c, d]) => Math.abs(c - a) <= 1 && Math.abs(d - b) <= 1));
      const close = !below && B.rule && cols.length ? B.rule : null;
      const ruleH = close ? close[1] - close[0] + 1 : 0, room = Math.round(3 * s);
      const vy1 = close ? Math.max(gy0 + 1, gy1 - room - ruleH) : gy1;
      if (B.up) for (const [a, b] of cols) for (let x = a - 1; x <= b + 1; x++) {
        if (x < q.x || x >= q.x + q.cv.width) continue;
        g.drawImage(q.cv, x - q.x, B.up.row, 1, 1, x, gy0, 1, vy1 - gy0);
      }
      if (close) g.drawImage(q.cv, 0, close[0], q.cv.width, ruleH, q.x, vy1, q.cv.width, ruleH);
      // the dots: in the middle of the table's band, or of its widest cell where an upright stands there
      const L = cols.length ? cols[0][0] : p.x, R = cols.length ? cols[cols.length - 1][1] : p.x + p.cv.width;
      let cx = (L + R) / 2;
      const half = 5 * s + Math.max(1.2, 0.9 * s) + 3 * s;
      if (cols.some(([a, b]) => b >= cx - half && a <= cx + half)) {
        let w = -1;
        for (let j = 1; j < cols.length; j++) { const a = cols[j - 1][1], b = cols[j][0]; if (b - a > w) { w = b - a; cx = (a + b) / 2; } }
      }
      const cy = (gy0 + vy1) / 2, r = Math.max(1.2, 0.9 * s);
      g.fillStyle = '#6b6330';
      for (const dx of [-1, 0, 1]) { g.beginPath(); g.arc(cx + dx * 5 * s, cy, r, 0, 2 * Math.PI); g.fill(); }
    }
    for (const p of parts) { p.cv.width = 0; p.cv.height = 0; }
  }
  canvas.style.width = (canvas.width / Math.min(dpr, 2)) + 'px';
  canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
  canvas.className = 'ifc-clip';
  // where a one-piece picture lies on its page: page point (x, y) is picture pixel ((x - x0) * s, (top - y) * s)
  if (parts.length === 1) canvas._ifcAt = { page: parts[0].seg.page, x0: parts[0].seg.x0 - parts[0].x / s, top: parts[0].ry - parts[0].r0 / s, s };
  // (384.71) where every piece of a sheet lies on the picture, in page points: piece k's page point (x, y) is picture pixel ((x - ox) * s, (oy - y) * s) between its rows
  // y0..y1 (the first and the last piece's outer edges are settled to a clean row - settleEdge - so a piece does not start where its cut says); read by the gates' pixel checks only
  canvas._ifcParts = parts.map(p => ({ page: p.seg.page, ox: p.seg.x0 - p.x / s, oy: p.ry + (p.y - p.r0) / s, s, x0: p.seg.x0, x1: p.seg.x1, y0: p.seg.y0, y1: p.seg.y1, row0: p.y, row1: p.y + (p.r1 - p.r0) }));
  if (opts.blur) return canvas;                                      // the picture of a hidden name carries no wash and no marks
  const ctx = canvas.getContext('2d');
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = WASH; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore();
  if (opts.keepPlain) { const pl = document.createElement('canvas'); pl.width = canvas.width; pl.height = canvas.height; pl.getContext('2d').drawImage(canvas, 0, 0); canvas._ifcPlain = pl; }
  const keyed = hasKeyMark(clip.marks || []), bands = [];
  for (const m of clip.marks || []) {
    if (!isDark(m, keyed)) continue;
    const cx = (m.x0 + m.x1) / 2, cy = m.i0 != null ? (m.i0 + m.i1) / 2 : (m.y0 + m.y1) / 2;
    const p = parts.find(q => q.seg.page === m.page && cx >= q.seg.x0 - 2 && cx <= q.seg.x1 + 2 && cy <= q.pc.top + 1 && cy >= q.pc.bot - 1);
    if (!p) continue;
    const X = (v) => (v - p.seg.x0) * s + p.x, Y = (v) => (p.ry - v) * s - p.r0 + p.y;
    bands.push({ x0: X(m.x0), x1: X(m.x1), t: Y(m.i1 != null ? m.i1 : m.y1), b: Y(m.i0 != null ? m.i0 : m.y0), em: (m.fs || 10) * s, lp: m.lp ? m.lp * s : null, cl: m.cl, cr: m.cr, snap: m.snap, exact: m.exact, row: m.kind === 'row' || m.tableRow,
                 lt: m.lt != null ? Y(m.lt) : null, lb: m.lb != null ? Y(m.lb) : null });
  }
  for (const b of bands) { if (b.snap && !b.exact) snapBand(ctx, b); ruleBand(ctx, b, !b.row); }
  for (const b of bands.slice()) if (b.extra) bands.push(b.extra);
  fillMarker(ctx, bands);
  return canvas;
}

// The hidden words are placed from font-width estimates, which can drift a few points on a long line set in another typeface (the county booklet). Here the
// picture itself is used: the dark columns of the run are grouped into words (a gap wider than a letter space starts a new word) and, when the number of groups
// equals the number of words of the run, the hidden words' own ink box is blurred. When the count does not match, the estimated box is widened on both sides.
export const snapStats = { exact: 0, widened: 0, log: [] };
function snapRect(ctx, h, s, px0, py0, H) {
  const sn = h.snap, fpx = sn.fs * s;
  const X0 = Math.max(0, Math.floor(sn.ix0 * s - px0 - 1)), X1 = Math.min(ctx.canvas.width, Math.ceil(sn.ix1 * s - px0 + 1));
  const base = (H - (h.y0 + 0.4 * sn.fs)) * s - py0;                       // baseline, in picture pixels
  const Y0 = Math.max(0, Math.floor(base - 0.8 * fpx)), Y1 = Math.min(ctx.canvas.height, Math.ceil(base + 0.2 * fpx));
  const wid = X1 - X0, hgt = Y1 - Y0;
  const top = (H - h.y1) * s - py0, hh = (h.y1 - h.y0) * s;
  const widen = () => { snapStats.widened++; const pad = 1.6 * fpx; return { x: h.x0 * s - px0 - pad, y: top, w: (h.x1 - h.x0) * s + 2 * pad, h: hh }; };
  if (wid < 4 || hgt < 4) return widen();
  const d = ctx.getImageData(X0, Y0, wid, hgt).data;
  const ink = new Uint8Array(wid);
  for (let x = 0; x < wid; x++) for (let y = 0; y < hgt; y++) { const i = (y * wid + x) * 4; if (d[i] + d[i + 1] + d[i + 2] < 690) { ink[x] = 1; break; } }
  const group = (gap) => {
    const out = [];
    let start = -1, last = -1;
    for (let x = 0; x < wid; x++) {
      if (!ink[x]) continue;
      if (start < 0) { start = x; last = x; } else if (x - last > gap) { out.push([start, last]); start = x; last = x; } else last = x;
    }
    if (start >= 0) out.push([start, last]);
    return out;
  };
  let groups = [], gap = 0;
  for (const f of [0.19, 0.15, 0.23, 0.12, 0.27]) {                 // the first letter-space width that gives exactly one group per word
    gap = Math.max(2, f * fpx); groups = group(gap);
    if (groups.length === sn.nw) break;
  }
  if (groups.length !== sn.nw || sn.w0 < 0 || sn.w1 < sn.w0) { if (snapStats.log.length < 40) snapStats.log.push({ nw: sn.nw, g: groups.length, fpx: Math.round(fpx), wid, hgt, w0: sn.w0 }); return widen(); }
  snapStats.exact++;
  const a = groups[sn.w0][0], b = groups[sn.w1][1];
  return { x: X0 + a - 2, y: top, w: b - a + 5, h: hh };
}
// A heavy mosaic (blocks about a third of the line height) with a grey wash: the words under it cannot be read.
function blurRect(ctx, x, y, w, h) {
  x = Math.max(0, Math.floor(x)); y = Math.max(0, Math.floor(y)); w = Math.min(ctx.canvas.width - x, Math.ceil(w)); h = Math.min(ctx.canvas.height - y, Math.ceil(h));
  if (w < 2 || h < 2) return;
  const block = Math.max(6, Math.round(h / 2.2));
  const bw = Math.max(1, Math.round(w / block)), bh = Math.max(1, Math.round(h / block));
  const tmp = document.createElement('canvas'); tmp.width = bw; tmp.height = bh;
  const t = tmp.getContext('2d');
  t.imageSmoothingEnabled = true; t.drawImage(ctx.canvas, x, y, w, h, 0, 0, bw, bh);
  ctx.save();
  ctx.imageSmoothingEnabled = false; ctx.drawImage(tmp, 0, 0, bw, bh, x, y, w, h);
  ctx.fillStyle = 'rgba(120, 120, 130, 0.35)'; ctx.fillRect(x, y, w, h);
  ctx.restore();
}

async function paintWhole(page, rotation, container, s, dpr, hl, model, keyed) {
  const vp = page.getViewport({ scale: s, rotation: ((page.rotate || 0) + rotation) % 360 });
  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(vp.width); canvas.height = Math.ceil(vp.height);
  canvas.style.width = (canvas.width / Math.min(dpr, 2)) + 'px'; canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
  canvas.className = 'ifc-clip ifc-page';
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
  await page.render({ canvasContext: ctx, viewport: vp }).promise;
  if (hl && (hl.segments.length || hl.marks.length)) highlightPage(ctx, vp, hl, s, model, keyed);
  container.appendChild(canvas);
}

// On a whole page the cited code is highlighted like with a marker, in the picture's two tones: a pale wash over each block of the
// cited code - hugging its lines, the same room on every side, the corners rounded (one block per column: the section's lines, its
// exceptions, a table's rows, as one rectangle, not a ragged edge where the cut pieces were) - and the darker gold (the same
// marker as the picture's) over the deciding words, the wash always under it. No frame, no other colour. Marks are in pdf points.
function highlightPage(ctx, vp, hl, s, model, keyed) {
  const P = (x, y) => vp.convertToViewportPoint(x, y);
  const box = (x0, y0, x1, y1) => { const a = P(x0, y0), b = P(x1, y1); return { x0: Math.min(a[0], b[0]), x1: Math.max(a[0], b[0]), y0: Math.min(a[1], b[1]), y1: Math.max(a[1], b[1]) }; };
  if (keyed == null) keyed = hasKeyMark(hl.marks);
  const upright = !((vp.rotation || 0) % 360);
  const items = model ? model.items.filter(it => it.t && /[A-Za-z0-9]/.test(it.t) && inBody(it)) : [];      // (a lone mark - the book's change asterisk - does not stretch a block)
  const bands = [];
  for (const m of hl.marks) {
    if (!isDark(m, keyed)) continue;
    const r = box(m.x0, m.i0 != null ? m.i0 : m.y0, m.x1, m.i1 != null ? m.i1 : m.y1);
    bands.push({ x0: r.x0, x1: r.x1, t: r.y0, b: r.y1, em: (m.fs || 10) * s, lp: m.lp ? m.lp * s : null, cl: m.cl, cr: m.cr, snap: m.snap, exact: m.exact, row: m.kind === 'row' || m.tableRow,
                 lt: m.lt != null ? P(m.x0, m.lt)[1] : null, lb: m.lb != null ? P(m.x0, m.lb)[1] : null });
  }
  const rects = [], W = ctx.canvas.width;
  for (const sg of hl.segments) {
    const ins = upright ? items.filter(it => centre(it) >= sg.x0 && centre(it) <= sg.x1 && it.y >= sg.y0 && it.y <= sg.y1) : [];
    let r, fs = 10;
    if (ins.length) {
      const hs = ins.map(it => it.h).sort((a, b) => a - b); fs = hs[hs.length >> 1];
      const pad = 0.45 * fs;
      let L = Math.min(...ins.map(it => it.x)), R = Math.max(...ins.map(it => it.x + it.w));
      let Bt = Math.min(...ins.map(it => it.y - DSC * it.h)), Tp = Math.max(...ins.map(it => it.y + ASC * it.h));
      // the block's room stops halfway to the print around it that is not cited (the line above, the line below, the next column)
      let top = Tp + pad, bot = Bt - pad, lft = L - pad, rgt = R + pad;
      const inSet = new Set(ins);
      for (const it of items) {
        if (inSet.has(it)) continue;
        const i0 = it.y - DSC * it.h, i1 = it.y + ASC * it.h;
        const sideways = it.x < R + pad && it.x + it.w > L - pad, level = i1 > Bt - pad && i0 < Tp + pad;
        if (sideways && i0 >= Tp - 0.5) top = Math.min(top, (Tp + i0) / 2);
        if (sideways && i1 <= Bt + 0.5) bot = Math.max(bot, (Bt + i1) / 2);
        if (level && it.x >= R - 0.5) rgt = Math.min(rgt, (R + it.x) / 2);
        if (level && it.x + it.w <= L + 0.5) lft = Math.max(lft, (L + it.x + it.w) / 2);
      }
      // (r15) a block of text runs the width of its column and a centred heading sits in the middle of it: the same block whatever its last line holds
      if (sg.xr != null) rgt = Math.max(rgt, sg.xr + pad);
      if (sg.sym != null) { lft = Math.min(lft, 2 * sg.sym - rgt); rgt = Math.max(rgt, 2 * sg.sym - lft); }
      r = box(lft, bot, rgt, top);
      // a table's rules reach past its text: the block takes in the rules ruled across these lines (a long level run of ink)
      try {
        const sx = model && model.g != null ? box(sg.x0, sg.y0, sg.x1, sg.y1) : { x0: 0, x1: W };
        const X0 = Math.max(0, Math.floor(sx.x0)), X1 = Math.min(W, Math.ceil(sx.x1)), Y0 = Math.max(0, Math.floor(r.y0)), Y1 = Math.min(ctx.canvas.height, Math.ceil(r.y1));
        if (X1 - X0 > 8 && Y1 - Y0 > 2) {
          const D = ctx.getImageData(X0, Y0, X1 - X0, Y1 - Y0).data, w = X1 - X0, need = Math.max(0.25 * (r.x1 - r.x0), 12 * s);
          let a0 = Infinity, a1 = -Infinity;
          for (let y = 0; y < Y1 - Y0; y++) {
            let run = 0;
            for (let x = 0; x <= w; x++) {
              const i = (y * w + x) * 4, dk = x < w && D[i] + D[i + 1] + D[i + 2] < 480;
              if (dk) { run++; continue; }
              if (run >= need) { a0 = Math.min(a0, X0 + x - run); a1 = Math.max(a1, X0 + x); }
              run = 0;
            }
          }
          if (a1 > a0) { const e = 0.45 * fs * s; r.x0 = Math.min(r.x0, a0 - e); r.x1 = Math.max(r.x1, a1 + e); }
        }
      } catch (e) { /* the block hugs the text */ }
    } else r = box(sg.x0, sg.y0, sg.x1, sg.y1);
    rects.push({ ...r, em: fs * s });
  }
  for (const b of bands) { if (b.snap && !b.exact && upright) snapBand(ctx, b); if (upright) ruleBand(ctx, b, !b.row); }
  for (const b of bands.slice()) if (b.extra) bands.push(b.extra);
  // the wash is under every gold mark: a mark is part of the block it sits in (or a block of its own), the marker's own extent
  for (const b of bands) {
    const pad = Math.min(0.2 * b.em, Math.max(0.08 * b.em, ((b.lp || 1.15 * b.em) - (b.b - b.t)) / 2)), px = 0.14 * b.em;
    rects.push({ x0: b.x0 - px, x1: b.x1 + px, y0: b.top != null ? b.top : b.t - pad, y1: b.bot != null ? b.bot : b.b + pad, em: b.em });
  }
  // one block per run of a column: rectangles that overlap sideways and follow one another down the page are one (their outline)
  for (let again = true; again;) {
    again = false;
    for (let i = 0; i < rects.length && !again; i++) for (let j = i + 1; j < rects.length && !again; j++) {
      const a = rects[i], b = rects[j];
      const ov = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0), gy = Math.max(a.y0, b.y0) - Math.min(a.y1, b.y1);
      if (ov > 0.3 * Math.min(a.x1 - a.x0, b.x1 - b.x0) && gy < 1.2 * Math.max(a.em, b.em)) {
        a.x0 = Math.min(a.x0, b.x0); a.x1 = Math.max(a.x1, b.x1); a.y0 = Math.min(a.y0, b.y0); a.y1 = Math.max(a.y1, b.y1); a.em = Math.max(a.em, b.em);
        rects.splice(j, 1); again = true;
      }
    }
  }
  const wash = new Path2D();
  for (const r of rects) roundedPoly(wash, [[r.x0, r.y0], [r.x1, r.y0], [r.x1, r.y1], [r.x0, r.y1]], 0.35 * r.em);
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = WASH; ctx.fill(wash, 'nonzero'); ctx.restore();
  fillMarker(ctx, bands);
}

// Whole pages (sideways pages are turned so that they read normally): the "show the whole book page" view and the fallback.
// opts.clip = the result of computeClip for the same pointer: the cited code is then highlighted on the pages (see highlightPage).
export async function paintPages(doc, pages, container, opts = {}) {
  const scale = opts.scale || 1.4;
  const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
  const s = scale * Math.min(dpr, 2);
  const fontBold = opts.fontBold || (opts.fontBold = new Map());
  const cache = opts.cache || (opts.cache = new Map());
  const clip = opts.clip && opts.clip.ok ? opts.clip : null;
  const keyed = clip ? hasKeyMark(clip.marks || []) : false;
  for (const p of pages) {
    const model = await pageModel(doc, p, fontBold, cache);
    const page = await doc.getPage(p);
    const cited = clip ? (clip.cited || clip.segments.filter(sg => !sg.whole)) : [];
    const hl = clip ? { segments: cited.filter(sg => sg.page === p), marks: clip.marks.filter(m => m.page === p) } : null;
    await paintWhole(page, model.rot || 0, container, s, dpr, hl, model, keyed);
  }
}
