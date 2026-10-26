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

const BODY_TOP = 735, BODY_BOTTOM = 36;      // items above / below are running headers, page labels and the licence footer
const BODY_H = 9.5;                           // body text is 10 pt; table cells are 9 pt or smaller
const COL_L = 28, COL_R = 584;                // left / right edge used for clippings

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
  return x0 === seg.x0 && x1 === seg.x1 ? seg : { ...seg, x0, x1 };
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
    const ends = (sp) => /[.;:!?]["”')\]]*$/.test(sp.it.s.trim());
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
    if (!spans.slice(lo, hi + 1).some(rowLike)) {
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
      const last = bands[bands.length - 1];
      if (last && Math.abs((last.y0 + last.y1) / 2 - (r.y0 + r.y1) / 2) < 5 && r.x0 >= last.x0 && r.x0 - last.x1 <= 20) {
        last.x1 = Math.max(last.x1, r.x1); last.y0 = Math.min(last.y0, r.y0); last.y1 = Math.max(last.y1, r.y1); last.text += ' ' + text; last.cl = last.cl || cl; last.cr = last.cr || cr;
      } else bands.push({ ...r, text, cl, cr });
    }
    for (const b of bands) out.push({ page: model.p, ...b, kind: 'cite' });
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
const headMark = (p, r) => ({ page: p, x0: r.x - 2, x1: r.x + r.w + 2, y0: r.y - 0.35 * r.h, y1: r.y + 1.0 * r.h, kind: 'heading' });

// -> { ok, segments:[{page,x0,x1,y0,y1,col}], marks:[{page,x0,x1,y0,y1,kind}], text, pages:[...], truncated }
// segment coordinates are pdf points (origin bottom-left); col -1 = full width, 0 / 1 = left / right column, -2 = whole page.
export async function computeClip(doc, index, loc, ptr, opts = {}) {
  if (!loc.ok) return { ok: false };
  const fontBold = opts.fontBold || (opts.fontBold = new Map());
  const cache = opts.cache || (opts.cache = new Map());
  if (loc.kind === 'table') return tableClip(doc, index, loc, ptr, opts, fontBold, cache);
  if (loc.kind === 'entry') return entryClip(doc, index, loc, ptr, opts, fontBold, cache);
  if (loc.kind === 'figure') return figureClip(doc, index, loc, ptr, fontBold, cache);
  const r = await flowClip(doc, index, loc, ptr, opts, fontBold, cache);
  if (r.ok && ptr && ptr.blur) { try { const h = await hideInfo(doc, loc, fontBold, cache); if (h) { r.hide = h.hide; r.hiddenText = h.hiddenText; } } catch (e) { /* shown unblurred is never a leak: without the rectangles nothing is hidden, so the app must check clip.hide before it shows the picture */ } }
  // The clipping stops above an exception (or a table) the question is not about; the whole-page view highlights the whole section, so the
  // full extent is cut once more, without marks, and handed over as `cited` (see highlightPage).
  if (r.ok && (loc.stoppedAtException || loc.stoppedAtTable) && loc.fullEnd !== undefined) {
    try {
      const full = await flowClip(doc, index, { ...loc, end: loc.fullEnd, stoppedAtException: false, stoppedAtTable: false }, { ...ptr, find: null, exception: null }, opts, fontBold, cache);
      if (full.ok && !full.segments.some(sg => sg.whole)) r.cited = full.segments;
    } catch (e) { /* the whole-page view then highlights the clipping only */ }
  }
  return r;
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
  const last = Math.min(ep, sp + maxPages - 1, index.numPages);
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
    const slice = [];
    for (let k = a; k < Math.min(b, mainEnd); k++) { const it = items[k]; if (it.t && inBody(it)) slice.push(it); }
    if (!slice.length) continue;
    const endHere = loc.end && p === ep ? loc.end : null;
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
    for (const s of segs) segments.push(trimEdges(model, s));
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
        if (it.b && EXC.test(it.t)) { marks.push({ page: p, ...rectOf(it), kind: 'exception' }); seenExc = true; }
        else if (seenExc && num && it.t === num + '.') { marks.push({ page: p, ...rectOf(it), kind: 'exceptionNumber' }); seenExc = false; }
      }
    }
  }
  return { ok: true, segments, marks, text: textParts.join(' '), pages, truncated: last < ep };
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
    if (p === loc.start.page) marks.push({ page: p, x0: loc.start.x - 2, x1: loc.start.x + loc.start.w + 2, y0: loc.start.y - 0.35 * loc.start.h, y1: loc.start.y + 1.0 * loc.start.h, kind: 'heading' });
  }
  // optional `row`: the question is about one row (or a few) of the table: show the caption and column headings, the rows around it and the notes,
  // from the one page that holds the row, with the row marked
  const rows = [].concat(ptr && ptr.row ? ptr.row : []);
  if (rows.length && segments.length) {
    for (const p of pages) {
      const model = await pageModel(doc, p, fontBold, cache);
      if (model.rot) continue;
      const rowClip = await tableRowClip(model, segments.filter(sg => sg.page === p && !sg.whole), headsOn(p).filter(h => h.token === loc.token), rows);
      if (rowClip) return { ok: true, ...rowClip, pages: [p], truncated: false };
    }
  }
  return { ok: true, segments, marks, text: textParts.join(' '), pages, truncated };
}

// the row label (and its factor, on the same line) inside a table rectangle
function findRow(model, want, rect) {
  let L = null;
  for (const it of model.items) {
    if (!it.t || !inBody(it)) continue;
    const c = centre(it);
    if (c < rect.x0 || c > rect.x1 || it.y < rect.y0 || it.y > rect.y1) continue;
    const n = norm(it.t);
    if (n && (n === want || (n.length >= 12 && want.startsWith(n)) || (want.length >= 6 && n.startsWith(want)))) { L = it; break; }
  }
  if (!L) return null;
  let F = null;
  for (const it of model.items) {
    if (!it.t || !inBody(it) || it === L || it.x < L.x + L.w - 1) continue;
    const c = centre(it);
    if (c < rect.x0 || c > rect.x1) continue;
    const dy = Math.abs(it.y - L.y);
    if (dy <= 6 && (!F || dy < Math.abs(F.y - L.y))) F = it;
  }
  const a = rectOf(L), b = F ? rectOf(F) : a;
  return { L, F, x0: Math.min(a.x0, b.x0) - 2, x1: Math.max(a.x1, b.x1) + 2, y0: Math.min(a.y0, b.y0) - 0.5, y1: Math.max(a.y1, b.y1) + 0.5 };
}

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
    const snapUp = (y) => breaks.filter(b => b >= y).reduce((m, b) => Math.min(m, b), yHead);
    const snapDown = (y) => breaks.filter(b => b <= y).reduce((m, b) => Math.max(m, b), seg.y0);
    // pieces, top to bottom: caption + headings, the rows around the one asked about (five lines each way), the notes;
    // pieces that touch (or nearly) are joined
    const pieces = [[yHead, seg.y1], [snapDown(rBot - 72), snapUp(rTop + 72)]];
    if (notes.length) pieces.push([Math.max(Math.min(...notes.map(it => bottom(it))) - 2, seg.y0), Math.max(...notes.map(it => top(it))) + 2]);
    const merged = [];
    for (const [y0, y1] of pieces) {
      const last = merged[merged.length - 1];
      if (last && last[0] - y1 <= 14) last[0] = Math.min(last[0], y0);
      else merged.push([y0, y1]);
    }
    const out = merged.map(([y0, y1]) => ({ page: seg.page, x0: seg.x0, x1: seg.x1, y0, y1, col: seg.col, context: true }));
    const marks = [];
    if (cap) marks.push(headMark(seg.page, cap));
    for (const h of hits) marks.push({ page: seg.page, x0: h.x0, x1: h.x1, y0: h.y0, y1: h.y1, kind: 'row' });
    const cited = hits.map(h => ({ page: seg.page, x0: seg.x0, x1: seg.x1, y0: h.y0 - 1, y1: h.y1 + 1 }));
    return { segments: out, marks, cited, text: textIn(model, out) };
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
      segments.push({ page: p, x0: COL_L, x1: COL_R, y0: o.y0, y1: o.y1 + 2, col: -1 });
      textParts.push(textIn(model, [segments[0]]));
    }
    segments.push({ page: p, x0: COL_L, x1: COL_R, y0: Math.max(r.y0 - 2, BODY_BOTTOM), y1: line.y + 0.8 * line.h + 1.5, col: -1 });
    textParts.push(textIn(model, [segments[segments.length - 1]]));
    marks.push({ page: p, x0: line.x - 2, x1: line.x + line.w + 2, y0: line.y - 0.35 * line.h, y1: line.y + 1.0 * line.h, kind: 'heading' });
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
        const seg = { page: p + 1, x0: COL_L, x1: COL_R, y0: Math.max(q.y0 - 3, BODY_BOTTOM), y1: q.y1 + 2, col: -1 };
        segments.push(seg); pages.push(p + 1); textParts.push(textIn(m2, [seg]));
      }
    }
    return { ok: true, segments, marks, text: textParts.join(' '), pages, truncated: false };
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
async function countyChars(doc, p, cache) {
  const key = 'c' + p;
  if (cache && cache.has(key)) return cache.get(key);
  const page = await doc.getPage(p);
  const tc = await page.getTextContent();
  const items = tc.items.filter(it => it.str && it.str.trim() && it.transform[5] >= C_BOTTOM && it.transform[5] <= C_TOP)
    .map(it => ({ s: it.str, x: it.transform[4], y: it.transform[5], w: it.width, h: it.height || 11 }));
  items.sort((a, b) => b.y - a.y);
  const lines = [];                           // superscripts ("m2", footnote marks) stand a few points higher than their line: one line = items within 5 pt
  for (const it of items) {
    const ln = lines.length && lines[lines.length - 1].ref - it.y <= 5 ? lines[lines.length - 1] : null;
    if (ln) { ln.items.push(it); ln.x0 = Math.min(ln.x0, it.x); ln.x1 = Math.max(ln.x1, it.x + it.w); }
    else lines.push({ p, ref: it.y, y: it.y, x0: it.x, x1: it.x + it.w, items: [it] });
  }
  for (const ln of lines) {
    ln.items.sort((a, b) => a.x - b.x);
    ln.y = ln.items.reduce((m, it) => (it.w > m.w ? it : m), ln.items[0]).y;
  }
  const chars = [];                           // letters and digits only, with the x range each one covers on its line
  lines.forEach((ln, li) => {
    ln.y0 = ln.y - 3; ln.y1 = ln.y + 9.5;
    for (const it of ln.items) {
      const ws = Array.from(it.s, c => TNR[c] || 500), tot = ws.reduce((a, b) => a + b, 0) || 1;
      let acc = 0, k = 0;
      for (const c of it.s) {
        const w = ws[k++], a = it.x + it.w * acc / tot; acc += w;
        const n = cnorm(c);
        if (n) chars.push({ c: n, li, x0: a, x1: it.x + it.w * acc / tot });
      }
    }
  });
  const out = { p, lines, chars };
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
  const nearest = (w, key, c) => { let best = -1; for (let j = w.indexOf(key); j >= 0; j = w.indexOf(key, j + 1)) if (best < 0 || Math.abs(j - c) < Math.abs(best - c)) best = j; return best; };
  const findPiece = (text, from) => {
    const E = cnorm(text);
    if (E.length < 6) return null;
    const i = N.indexOf(E, from);
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
    for (const piece of String(ptr.exceptionText).split('\n')) { const r = findPiece(piece, xp); if (r) { ranges.push(r); b = Math.max(b, r[1]); xp = r[1]; } }
  }
  // lines of the booklet that hold the pieces; a gap of up to three lines between two pieces is closed (no point in a cut that skips a line or two)
  const segments = [], marks = [], texts = [], pages = [];
  for (const pt of parts) {
    const used = new Set();
    for (const [x, y] of ranges) for (let k = x; k < y; k++) if (all[k].pt === pt) used.add(all[k].li);
    if (!used.size) continue;
    const idx = [...used].sort((u, v) => u - v);
    const runs = [];
    for (const li of idx) {
      const last = runs[runs.length - 1];
      if (last && li - last[last.length - 1] <= 4) { for (let g = last[last.length - 1] + 1; g <= li; g++) last.push(g); }
      else runs.push([li]);
    }
    for (const run of runs) {
      const ls = run.map(i => pt.lines[i]);
      const x0 = Math.max(0, Math.min(...ls.map(l => l.x0)) - 4), x1 = Math.min(612, Math.max(...ls.map(l => l.x1)) + 4);
      // keep clear of the neighbouring lines (a table row printed just above or below must not show as a half line)
      const top = Math.max(...ls.map(l => l.y1)), bottom = Math.min(...ls.map(l => l.y0));
      const prev = pt.lines[run[0] - 1], next = pt.lines[run[run.length - 1] + 1];
      const y1 = prev ? Math.max(top, Math.min(top + 2, prev.y - 3)) : top + 2;
      const y0 = next ? Math.min(bottom, Math.max(bottom - 2, next.y + 10)) : bottom - 2;
      segments.push({ page: pt.p, x0, x1, y0, y1, col: -1 });
      texts.push(ls.map(l => l.items.map(i => i.s).join(' ')).join(' '));
    }
    pages.push(pt.p);
  }
  const markRange = (from, to, kind) => {
    const byLine = new Map();
    for (let k = from; k < to; k++) {
      const ch = all[k], key = ch.pt.p + ':' + ch.li;
      const m = byLine.get(key);
      if (m) { m.x0 = Math.min(m.x0, ch.x0); m.x1 = Math.max(m.x1, ch.x1); }
      else byLine.set(key, { page: ch.pt.p, x0: ch.x0, x1: ch.x1, y0: ch.pt.lines[ch.li].y0, y1: ch.pt.lines[ch.li].y1, kind });
    }
    for (const m of byLine.values()) marks.push(m);
  };
  if (ptr.highlight) { const h = findPiece(ptr.highlight, a); if (h && h[1] <= b) markRange(h[0], h[1], 'cite'); }
  const T = cnorm((ptr.section || '') + (ptr.heading || ''));
  if (T.length >= 4 && N.startsWith(T, a)) markRange(a, a + T.length, 'heading');
  // The whole-page view highlights the whole provision: when exceptions are printed after the cut (and the question is not about them), they are cited code too.
  const cited = segments.slice();
  const lastPt = parts[parts.length - 1];
  let lastLi = -1;
  for (const [x, y] of ranges) for (let k = x; k < y; k++) if (all[k].pt === lastPt) lastLi = Math.max(lastLi, all[k].li);
  if (lastLi >= 0) {
    const NEWSEC = /^(?:\d{2,4}(?:\.\d+)+[A-Za-z]?\b|SECTION\b|CHAPTER\b|TABLE\b|Table\b|APPENDIX\b)/;
    let end = -1, sawExc = false;
    for (let li = lastLi + 1; li < lastPt.lines.length; li++) {
      const first = (lastPt.lines[li].items[0] || { s: '' }).s.trim();
      if (NEWSEC.test(first)) break;
      if (/^Exceptions?\b/.test(first)) sawExc = true;
      end = li;
    }
    if (sawExc && end > lastLi) {
      const ls = lastPt.lines.slice(lastLi + 1, end + 1);
      const x0 = Math.max(0, Math.min(...ls.map(l => l.x0)) - 4), x1 = Math.min(612, Math.max(...ls.map(l => l.x1)) + 4);
      const top = lastPt.lines[lastLi].y0 - 0.5, bottom = Math.min(...ls.map(l => l.y0));
      cited.push({ page: lastPt.p, x0, x1, y0: bottom - 1, y1: top, col: -1 });
    }
  }
  return { ok: true, segments, marks, text: texts.join(' '), pages, truncated: false, cited };
}

// ------------------------------------------------------------------------------------------------ painting (browser only)
// container: an element; the clipping is appended as one canvas per segment, in reading order.
// Highlighting (owner, 2026-10-25): the whole cited section is washed pale yellow, and the sentence / table row / deciding words are a clearly stronger gold on top of it.
// A section whose deciding sentence is known (a 'cite' or 'row' mark) does not also get a strong heading; one without it keeps the strong heading as the fallback.
const WASH = 'rgb(255, 245, 160)', STRONG = 'rgb(255, 224, 40)', EXCPT = 'rgb(255, 150, 70)';   // all drawn with 'multiply': the paper is coloured, the print stays black
const hasKeyMark = (marks) => marks.some(m => m.kind === 'cite' || m.kind === 'row');
function markFill(m, keyed) {
  if (m.kind === 'cite' || m.kind === 'row') return STRONG;
  if (m.kind === 'heading') return keyed ? null : STRONG;
  return EXCPT;
}
export async function paint(doc, clip, container, opts = {}) {
  const scale = opts.scale || 1.6;
  const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
  const s = scale * Math.min(dpr, 2);
  for (const seg of clip.segments) {
    const page = await doc.getPage(seg.page);
    if (seg.whole) { await paintWhole(page, seg.rotation || 0, container, s, dpr); continue; }
    const vp = page.getViewport({ scale: s });
    const H = page.view[3];
    const px0 = seg.x0 * s, px1 = seg.x1 * s;
    const py0 = (H - seg.y1) * s, py1 = (H - seg.y0) * s;
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.ceil(px1 - px0)); canvas.height = Math.max(1, Math.ceil(py1 - py0));
    canvas.style.width = (canvas.width / Math.min(dpr, 2)) + 'px';
    canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
    canvas.className = 'ifc-clip';
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    await page.render({ canvasContext: ctx, viewport: vp, transform: [1, 0, 0, 1, -px0, -py0] }).promise;
    if (!opts.blur) {                                                // the whole cited section: a pale wash (the print stays black), the picture of a hidden name carries none
      ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = WASH; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore();
    }
    const keyed = hasKeyMark(clip.marks.filter(m => m.page === seg.page));
    const paths = new Map();                                         // one path per colour, filled once: stripes that touch or overlap are not painted twice
    for (const m of clip.marks) {
      if (m.page !== seg.page || opts.blur) continue;                // the picture of a hidden name carries no marks
      const mx0 = m.x0 * s - px0, mx1 = m.x1 * s - px0, my0 = (H - m.y1) * s - py0, my1 = (H - m.y0) * s - py0;
      if (mx1 < 0 || mx0 > canvas.width || my1 < 0 || my0 > canvas.height) continue;
      const fill = markFill(m, keyed); if (!fill) continue;
      if (!paths.has(fill)) paths.set(fill, new Path2D());
      paths.get(fill).rect(mx0, my0, mx1 - mx0, my1 - my0);
    }
    for (const [fill, path] of paths) { ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = fill; ctx.fill(path, 'nonzero'); ctx.restore(); }
    if (opts.blur && clip.hide) for (const h of clip.hide) if (h.page === seg.page) {
      let r = null;
      if (h.snap) { try { r = snapRect(ctx, h, s, px0, py0, H); } catch (e) { r = null; } }
      if (r) blurRect(ctx, r.x, r.y, r.w, r.h);
      else blurRect(ctx, h.x0 * s - px0, (H - h.y1) * s - py0, (h.x1 - h.x0) * s, (h.y1 - h.y0) * s);
    }
    container.appendChild(canvas);
  }
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

async function paintWhole(page, rotation, container, s, dpr, hl) {
  const vp = page.getViewport({ scale: s, rotation: ((page.rotate || 0) + rotation) % 360 });
  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(vp.width); canvas.height = Math.ceil(vp.height);
  canvas.style.width = (canvas.width / Math.min(dpr, 2)) + 'px'; canvas.style.maxWidth = '100%'; canvas.style.height = 'auto';
  canvas.className = 'ifc-clip ifc-page';
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
  await page.render({ canvasContext: ctx, viewport: vp }).promise;
  if (hl && (hl.segments.length || hl.marks.length)) highlightPage(ctx, vp, hl, s);
  container.appendChild(canvas);
}

// On a whole page the cited code is highlighted like with a marker: a pale yellow wash over the lines the clipping is cut from, and the
// same yellow (heading, table row, deciding words) / orange (exception) marks as in the clipping drawn on top. No frame, no other colour.
// Rectangles are in pdf points; the viewport converts them.
function highlightPage(ctx, vp, hl, s) {
  const box = (r) => {
    const q = vp.convertToViewportRectangle([r.x0, r.y0, r.x1, r.y1]);
    return { x: Math.min(q[0], q[2]), y: Math.min(q[1], q[3]), w: Math.abs(q[2] - q[0]), h: Math.abs(q[3] - q[1]) };
  };
  ctx.save();
  ctx.globalCompositeOperation = 'multiply';                     // the wash colours the paper, the print stays black
  ctx.fillStyle = WASH;
  for (const sg of hl.segments) { const b = box(sg); ctx.fillRect(b.x, b.y, b.w, b.h); }
  ctx.restore();
  const keyed = hasKeyMark(hl.marks);
  const paths = new Map();
  for (const m of hl.marks) {
    const b = box(m);
    const fill = markFill(m, keyed); if (!fill) continue;
    if (!paths.has(fill)) paths.set(fill, new Path2D());
    paths.get(fill).rect(b.x, b.y, b.w, b.h);
  }
  for (const [fill, path] of paths) { ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = fill; ctx.fill(path, 'nonzero'); ctx.restore(); }
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
  for (const p of pages) {
    const model = await pageModel(doc, p, fontBold, cache);
    const page = await doc.getPage(p);
    const cited = clip ? (clip.cited || clip.segments.filter(sg => !sg.whole)) : [];
    const hl = clip ? { segments: cited.filter(sg => sg.page === p), marks: clip.marks.filter(m => m.page === p) } : null;
    await paintWhole(page, model.rot || 0, container, s, dpr, hl);
  }
}
