// The structural half of tools/check-b384-hlall.py (node, headless): for EVERY distinct citation of the Fire Code bank it asks the viewer for its
// clip (the picture in the card: clip.segments; the whole page: clip.cited, else the segments) and checks it against what the PRINTED PAGE says
// the provision is, read here by a different rule than the viewer's (the viewer reads the booklet's typefaces; this reads the text and the
// spacing: a heading is a numbered line that starts a paragraph, with a paragraph's space above it).
//   args: PDFJS_DIR KIT COUNTY_PDF BANK BOOK_PDF|- OUT.json
// A citation is an OFFENDER when: the page's highlight ends before its provision / table / entry does, or runs past it (county, and the book's
// sections, definitions, banners); the card's picture ends in the middle of a sentence or a list item; the card shows lines the page does not
// highlight; the picture is two disjoint pieces; a deeper mark lies outside the soft highlight; the cited words are not in the highlight.
import fs from "fs";
const [PDFJS, KIT, COUNTY, BANK, BOOK, OUT] = process.argv.slice(2);
const pdfjs = await import(PDFJS + "/legacy/build/pdf.mjs");
const V = await import(KIT);
const bs = fs.readFileSync(BANK, "utf8"), bank = JSON.parse(bs.slice(bs.indexOf("{"), bs.lastIndexOf("}") + 1));
const open = async (f) => pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(f)), isEvalSupported: false, verbosity: 0, useSystemFonts: true, disableFontFace: true }).promise;
const res = { county: [], book: [], skipped: [] };
// the booklet's printed lines as this audit reads them (its own reader, so it measures any build's clip): baseline, ends, text
const lineCache = new Map();
async function linesOf(doc, p) {
  if (lineCache.has(p)) return lineCache.get(p);
  const tc = await (await doc.getPage(p)).getTextContent();
  const items = tc.items.filter(it => it.str && it.str.trim() && it.transform[5] >= 56 && it.transform[5] <= 735).map(it => ({ s: it.str, x: it.transform[4], y: it.transform[5], w: it.width }));
  items.sort((a, b) => b.y - a.y);
  const L = [];
  for (const it of items) { const l = L.length && L[L.length - 1].ref - it.y <= 5 ? L[L.length - 1] : null; if (l) { l.it.push(it); l.x0 = Math.min(l.x0, it.x); l.x1 = Math.max(l.x1, it.x + it.w); } else L.push({ ref: it.y, y: it.y, x0: it.x, x1: it.x + it.w, it: [it] }); }
  let right = null; for (const l of L) if (l.x1 <= 545 && (right == null || l.x1 > right)) right = l.x1;
  if (right >= 534 && right <= 541) right = 540;
  // (a number printed in pieces - "10 8 .3 Concealed work.", "SECTION 32 5" - is read whole)
  const whole = (t) => t.replace(/^[\d.\s]+(?=[A-Za-z])/, (m) => m.replace(/\s+/g, "") + " ").replace(/^((?:SECTION|CHAPTER|APPENDIX)\s+)([A-Z]?[\d\s.]+)/, (m, a, b) => a + b.replace(/\s+/g, "") + " ");
  for (const l of L) { l.it.sort((a, b) => a.x - b.x); l.text = whole(l.it.map(i => i.s).join(" ")); l.y = l.it.reduce((m, i) => (i.w > m.w ? i : m), l.it[0]).y; }
  const out = { lines: L, right }; lineCache.set(p, out); return out;
}
const nz = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, "");

// ------------------------------------------------------------------------------------------------ county
{
  const doc = await open(COUNTY), cache = new Map();
  const HEAD = /^(?:[A-Z]{0,2}\d{2,4}(?:\.\d+)+[A-Za-z]?\s+[A-Z]|SECTIONS?\s*[A-Z]{0,2}\d|CHAPTER\s*\d|APPENDIX\s*[A-Z]\b|EXHIBIT\b)/, TAB = /^(?:TABLE|Table)\s+[A-Z]?\d/;
  const seen = new Set();
  for (const q of bank.questions) {
    const c = q.citation; if (c.source !== "amendment") continue;
    const key = JSON.stringify(c); if (seen.has(key)) continue; seen.add(key);
    const kind = c.exceptionText || /^Exception/.test(c.excerpt || "") ? "exception" : / \| | › /.test(c.highlight || "") || /^(?:TABLE|Table)\b/.test(c.excerpt || "") || /^Table/i.test(c.section) ? "table" : (!c.highlight && !c.exceptionText && c.heading && nz(c.excerpt || "") === nz(c.heading)) ? "heading" : c.section === "202" ? "definition" : "section";
    const r = { id: q.id, label: q.id + " " + c.section, kind, bad: [] };
    res.county.push(r);
    let clip; try { clip = await V.countyClip(doc, c, { cache }); } catch (e) { r.bad.push(["error", String(e).slice(0, 80)]); continue; }
    if (!clip.ok) { r.bad.push(["no clip", ""]); continue; }
    const cited = clip.cited || clip.segments;
    for (const pg of new Set(clip.segments.map(s => s.page))) {
      const pt = await linesOf(doc, pg), L = pt.lines;
      const BAN = /^(?:SECTIONS?\s*[A-Z]{0,2}\d|CHAPTER\s*\d|APPENDIX\s*[A-Z]\b|EXHIBIT\b)/;
      const head = (i) => (BAN.test(L[i].text.trim()) && L[i].text.trim() === L[i].text.trim().toUpperCase()) || (HEAD.test(L[i].text.trim()) || TAB.test(L[i].text.trim())) && (i === 0 || L[i - 1].y - L[i].y > 16.5 || L[i - 1].x1 < (pt.right || 540) - 12);
      const inSeg = (segs, i) => segs.some(s => s.page === pg && L[i].y >= s.y0 && L[i].y <= s.y1);
      const card = clip.segments.filter(s => s.page === pg), cit = cited.filter(s => s.page === pg);
      const anchors = L.map((_, i) => i).filter(i => inSeg(card, i));
      if (!anchors.length) continue;
      const i0 = anchors[0], i1 = anchors[anchors.length - 1];
      // the provision as the page prints it: from the nearest heading above the first cited line (a table: from its title) to the line before the next heading
      let t = -1, lo = -1;
      for (let i = i1; i >= 0; i--) { if (TAB.test(L[i].text.trim()) && head(i)) { t = i; break; } if (HEAD.test(L[i].text.trim()) && head(i)) break; }
      const tbl = t >= 0 || (/ \| | › /.test(c.highlight || "") && !L.slice(0, i1).some((l, i) => HEAD.test(l.text.trim()) && head(i)));
      for (let i = i0; i >= 0; i--) if (HEAD.test(L[i].text.trim()) && head(i)) { lo = i; break; }
      const eLo = tbl ? Math.min(i0, t >= 0 ? t : (lo >= 0 ? i0 : 0)) : (lo >= 0 ? lo : 0);
      let skip = kind === "heading" && !L.slice(i0, i1 + 1).some(l => /^\d{2,4}(?:\.\d+)+/.test(l.text.trim()));
      let eHi = L.length - 1;
      for (let i = i1 + 1; i < L.length; i++) {
        if (head(i) && (HEAD.test(L[i].text.trim()))) { if (skip && !BAN.test(L[i].text.trim())) { skip = false; continue; } eHi = i - 1; break; }
        if (tbl && TAB.test(L[i].text.trim()) && head(i) && (t < 0 || L[i].text.trim().split(/\s+/)[1] !== L[t].text.trim().split(/\s+/)[1])) { eHi = i - 1; break; }
      }
      const early = [], late = [];
      for (let i = 0; i < L.length; i++) {
        const inCit = inSeg(cit, i), want = i >= eLo && i <= eHi;
        if (want && !inCit) early.push(i); if (!want && inCit) late.push(i);
      }
      if (early.length) r.bad.push(["page highlight ends early / misses lines", "p" + pg + " lines " + early.slice(0, 4).join(",") + " (" + L[early[0]].text.slice(0, 40) + ")"]);
      if (late.length) r.bad.push(["page highlight runs past the provision", "p" + pg + " lines " + late.slice(0, 4).join(",") + " (" + L[late[0]].text.slice(0, 40) + ")"]);
      // the picture's lines are part of the page's highlight
      const extra = anchors.filter(i => !inSeg(cit, i));
      if (extra.length) r.bad.push(["picture shows lines the page does not highlight", "p" + pg + " " + L[extra[0]].text.slice(0, 40)]);
      // the picture does not end inside a sentence or a list item
      const right = pt.right || 540, last = L[i1], nx = L[i1 + 1];
      const gapMax = (l) => l.it.reduce((m, it, k) => k ? Math.max(m, it.x - (l.it[k - 1].x + l.it[k - 1].w)) : m, 0);     // a table's cells stand apart; running text does not
      if (nx && gapMax(last) < 12 && gapMax(nx) < 12 && last.x1 >= right - 6 && nx.x1 > nx.x0 && !(HEAD.test(nx.text.trim()) && head(i1 + 1)) && !/^(?:Exceptions?\b|\d{1,2}\.\s|\(?[a-z0-9]{1,3}\)\s)/.test(nx.text.trim()) && !/[.:;?!)"”]$/.test(last.text.trim()) && Math.abs(nx.x0 - last.x0) < 3)
        r.bad.push(["picture ends inside a sentence", "p" + pg + " " + last.text.slice(-40) + " / " + nx.text.slice(0, 30)]);
      // two disjoint pieces
      const cs = card.slice().sort((a, b) => b.y1 - a.y1);
      for (let k = 1; k < cs.length; k++) if (cs[k - 1].y0 - cs[k].y1 > 30) r.bad.push(["picture is disjoint pieces", "p" + pg]);
    }
    // a deeper mark lies inside the soft highlight
    for (const m of clip.marks) {
      const y = m.i0 != null ? (m.i0 + m.i1) / 2 : (m.y0 + m.y1) / 2;
      if (!cited.some(s => s.page === m.page && y >= s.y0 - 1 && y <= s.y1 + 1 && (m.x0 + m.x1) / 2 >= s.x0 - 2 && (m.x0 + m.x1) / 2 <= s.x1 + 2)) r.bad.push(["deeper mark outside the highlight", m.kind + " p" + m.page]);
    }
    if (c.highlight && !clip.marks.some(m => m.kind === "cite" || m.kind === "row") && nz(c.highlight).length >= 6) r.bad.push(["the cited words are not marked", c.highlight.slice(0, 40)]);
    // a provision that goes on past the last cited page (information: the whole-page view shows the cited pages)
    const lastPg = Math.max(...clip.segments.map(s => s.page)), cl = cited.filter(s => s.page === lastPg).sort((a, b) => a.y0 - b.y0)[0];
    if (cl) { const pt = await linesOf(doc, lastPg), lastL = pt.lines[pt.lines.length - 1]; if (lastL && cl.y0 <= lastL.y + 1 && lastPg < doc.numPages) { const n = await linesOf(doc, lastPg + 1), f = n.lines[0]; if (f && !HEAD.test(f.text.trim()) && !TAB.test(f.text.trim())) r.runsOn = lastPg + 1; } }
  }
}

// ------------------------------------------------------------------------------------------------ the owner's book
if (BOOK && BOOK !== "-") {
  const doc = await open(BOOK), index = await V.buildIndex(doc, {}), opts = { cache: new Map(), fontBold: new Map() };
  const seen = new Set();
  const modelOf = (p) => V.pageModel(doc, p, opts.fontBold, opts.cache);
  const BODY_TOP = 735, BODY_BOTTOM = 36;
  for (const q of bank.questions) {
    const c = q.citation; if (c.source === "amendment") continue;
    const key = JSON.stringify(c); if (seen.has(key)) continue; seen.add(key);
    const r = { id: q.id, label: q.id + " " + c.section, kind: "?", bad: [] }; res.book.push(r);
    let loc; try { loc = V.locate(index, c); } catch (e) { r.bad.push(["error", String(e).slice(0, 80)]); continue; }
    r.kind = c.exception ? "exception" : loc.kind === "banner" ? (loc.lead ? "section title" : "chapter/appendix title") : loc.kind === "sec" ? "section" : loc.kind === "def" ? "definition" : loc.kind === "table" ? "table" : loc.kind === "entry" ? "referenced standard" : String(loc.kind);
    if (!loc.ok || loc.kind === "pages" || loc.kind === "figure") { if (!loc.ok) r.bad.push(["not located", ""]); continue; }
    let clip; try { clip = await V.computeClip(doc, index, loc, c, opts); } catch (e) { r.bad.push(["error", String(e).slice(0, 80)]); continue; }
    if (!clip.ok) { r.bad.push(["no clip", ""]); continue; }
    const cited = clip.cited || clip.segments;
    const covers = (segs, p, it) => segs.some(s => s.page === p && !s.whole && it.y >= s.y0 - 0.5 && it.y <= s.y1 + 0.5 && it.x + it.w / 2 >= s.x0 && it.x + it.w / 2 <= s.x1) || segs.some(s => s.page === p && s.whole);
    if (loc.kind === "sec" || loc.kind === "def" || loc.kind === "banner") {
      // every line of body text from the heading to the next heading is in the highlight (the end is where the index puts the next heading: that is the
      // reading order the viewer cuts by, checked here against the lines themselves)
      const sp = loc.start.page, wantEnd = loc.through ? loc.end : loc.fullEnd !== undefined ? loc.fullEnd : loc.end;
      const ep = wantEnd ? wantEnd.page : sp, upto = Math.min(ep, sp + 3);
      const miss = [];
      for (let p = sp; p <= upto; p++) {
        const m = await modelOf(p); if (m.rot) continue;
        const F = m.hasBody ? m.F : m.items.length;
        const a = p === sp ? loc.start.i : 0, b = wantEnd && p === wantEnd.page ? wantEnd.i : m.items.length;
        // (running text only: 10 pt; a table's cells and notes are smaller)
        for (let k = a; k < Math.min(b, F); k++) { const it = m.items[k]; if (!it.t || it.y < BODY_BOTTOM || it.y > BODY_TOP || it.h < 9.5 || it.h > 10.8) continue; if (!covers(cited, p, it)) miss.push(it.t.slice(0, 30)); }
      }
      if (miss.length) r.bad.push(["page highlight ends early / misses lines", miss.length + " items, first: " + miss[0]]);
    }
    // a table: the page tints the whole table (caption to last row and notes), whatever row the question is about
    if (loc.kind === "table" && c.row) {
      const whole = await V.computeClip(doc, index, loc, { ...c, row: undefined }, opts);
      if (whole.ok) for (const w of whole.segments) if (!w.whole && !cited.some(s => s.page === w.page && s.y0 <= w.y0 + 2 && s.y1 >= w.y1 - 2 && s.x0 <= w.x0 + 2 && s.x1 >= w.x1 - 2)) r.bad.push(["page highlight is not the whole table", "p" + w.page]);
    }
    // the card's picture shows nothing the page does not tint
    for (const sg of clip.segments) if (!sg.whole && !sg.context && !cited.some(s => s.page === sg.page && s.y0 <= sg.y0 + 2 && s.y1 >= sg.y1 - 2)) r.bad.push(["picture shows lines the page does not highlight", "p" + sg.page]);
    // the picture ends inside a sentence: its last line neither ends a sentence nor is followed by a new heading / item
    if (clip.segments.length) {
      const sg = clip.segments.filter(s => !s.whole && !s.context).slice(-1)[0];
      if (sg && !sg.table && !sg.figure) {
        const m = await modelOf(sg.page); const F = m.hasBody ? m.F : m.items.length;
        const inCol = (it) => it.t && it.y >= BODY_BOTTOM && it.y <= BODY_TOP && it.i < F && it.x + it.w / 2 >= sg.x0 && it.x + it.w / 2 <= sg.x1;
        const lastIt = m.items.filter(it => inCol(it) && it.y >= sg.y0 && it.y <= sg.y1).sort((a, b) => a.y - b.y)[0];
        const nextIt = m.items.filter(it => inCol(it) && it.y < sg.y0 && it.y > sg.y0 - 14).sort((a, b) => b.y - a.y)[0];
        if (lastIt && nextIt) {
          const lineText = m.items.filter(it => inCol(it) && Math.abs(it.y - lastIt.y) < 2).sort((a, b) => a.x - b.x).map(it => it.t).join(" ").trim();
          const nextText = m.items.filter(it => inCol(it) && Math.abs(it.y - nextIt.y) < 2).sort((a, b) => a.x - b.x).map(it => it.t).join(" ").trim();
          if (!/[.:;?!)"”\]]$/.test(lineText) && /^[a-z(]/.test(nextText) && !nextIt.b) r.bad.push(["picture ends inside a sentence", "…" + lineText.slice(-35) + " / " + nextText.slice(0, 25)]);
        }
      }
    }
    // disjoint pieces: two non-context pieces on one page, in one column, with other text between them
    const pcs = clip.segments.filter(s => !s.whole && !s.context).slice().sort((a, b) => a.page - b.page || b.y1 - a.y1);
    for (let k = 1; k < pcs.length; k++) if (pcs[k].page === pcs[k - 1].page && pcs[k].col === pcs[k - 1].col && pcs[k - 1].y0 - pcs[k].y1 > 30) r.bad.push(["picture is disjoint pieces", "p" + pcs[k].page]);
    if (clip.segments.some(s => s.context) && clip.segments.filter(s => s.context).some(cx => clip.segments.some(s => !s.context && s.page === cx.page && cx.y0 - s.y1 > 30))) r.bad.push(["picture joins a far-off heading to the entry", ""]);
    for (const m of clip.marks) {
      const y = m.i0 != null ? (m.i0 + m.i1) / 2 : (m.y0 + m.y1) / 2;
      if (!cited.some(s => s.page === m.page && (s.whole || (y >= s.y0 - 1 && y <= s.y1 + 1)))) r.bad.push(["deeper mark outside the highlight", m.kind + " p" + m.page]);
    }
  }
} else res.skipped.push("book");
fs.writeFileSync(OUT, JSON.stringify(res));
console.log(res.county.length + " county, " + res.book.length + " book citations");
