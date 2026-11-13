#!/usr/bin/env python3
"""Build 384 cropfix: every Fire Code code-box picture starts on what it cites, shows the whole table, is centred on it, runs a table row's gold from the
table's left edge to its right, and joins a windowed table cleanly.

Madison, on the review PDF of 384.83 (ch66-702, county Table 105.5.22; Chapter 10's Table 1004.5 windowed): "there's that random sentence at the top, and
it's not centered right ... The table is getting cut off on the right, secondly, the yellow darker highlight doesn't run to the edge of the table on the right
side (it should because the left side does it). Ensure the cropped stuff is centered properly, whether that's a table or what ... you gotta make sure it
connects properly, not glitchy or disconnected how I see some are."

Everything is read with the owner's IFC PDF loaded the way a reader loads it (Load my IFC PDF), pdf.js served from a local copy, the app's own code path
(V.locate + V.computeClip / V.countyClip with the citation the question carries, IFC_POINTER_PATCH included), the kit's own paint (V.paint, scale 1.7 at
dpr 2 - the pixels every code box is framed from) and, for (c), the code box the app builds (buildBankNote, "Show the code" opened) in a real Drill
answer card on an iPhone 17 Pro Max (440x956 at 3x) and an iPad Pro 11" (834x1194 at 2x). Over EVERY Fire Code reference that draws a picture:
  (a) NOTHING ABOVE OR BELOW WHAT IS CITED: no ink on the picture's first or last row but a table's rules (no half line at an edge); a county picture's
      first printed line is a line of the cited excerpt (never the end of the sentence before a table: "use or handle hazardous materials in excess of
      the amounts listed in Table 105.5.22."); a book table's picture starts on its TABLE caption.
  (b) THE WHOLE TABLE: no long horizontal rule (30pt or more) of any piece of the picture runs into the piece's left or right edge (a rule that does is a
      table cut short: its border and the ends of its rules are outside the picture).
  (c) CENTRED ON WHAT IS CITED: in the code box of every picture with a ruled table, the table (its rules' extent, border to border) together with
      the cited print beside it - a county picture's lines of the excerpt (never a line outside it), a book picture's print with the book's margin
      marks (a change bar, the deletion arrow) set aside - stands as far from the box's left edge as from its right, within 2 CSS px, on the phone
      and the iPad (the print of a picture with no table is (1b) of check-b384-ifccrop, which sets the same marks aside).
  (d) A ROW'S GOLD RUNS ACROSS THE TABLE: for every table-row highlight, the strong gold's left end is the table's left edge and its right end the table's
      right edge (the rules' extent), each within 2px (one rule's width and a hair: it stops just inside the border), on the same piece.
  (e) A SPLICED TABLE IS ONE TABLE: where a picture sets two pieces of a table one under the other (a windowed book table, a county table over two
      pages), the pieces have one frame (the rules' extent, within 1px), the same uprights (border and column rules, each within 1px) on both sides of
      the join, the piece above ends on a rule that runs its whole width (the heading row's bottom rule intact), the piece below starts on one, and in
      between either nothing (one rule: the table runs on) or a band of the table whose uprights run on through every row of it, with the dots of the
      omission in it - never a doubled rule, a torn edge or a missing line.
  (f) no page errors.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-cropfix.py [--against REV] [--ids a,b] [--only a,b,c,d,e]
      --against REV serves that commit's index.html AND ifc/ifc-viewer.js. Against origin/main (384.83) (a) FAILS on the 13 county 105.5.22 / Exhibit B rows
      (ch63-702 ...: the sentence above the table; chExhB-801: the amendment's own heading), (b) on the 20 Table 1004.5 pictures and the county rows,
      (c) on the county rows, (d) on the Table 1004.5 rows and the county rows, (e) on the 1004.5 windows and the 105.5.22 / chExhB-801 splices.
OUT_JSON=<file> writes every picture's readings. The book never goes into the repo (it is public)."""
import os, sys, json, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_argv = sys.argv[:]
IDS = None
if "--ids" in _argv:
    i = _argv.index("--ids"); IDS = _argv[i + 1].split(","); _argv = _argv[:i] + _argv[i + 2:]
ONLY = None
if "--only" in _argv:
    i = _argv.index("--only"); ONLY = set(_argv[i + 1].split(",")); _argv = _argv[:i] + _argv[i + 2:]
sys.argv = _argv
src = open(os.path.join(HERE, "check-b384-ifcmarks.py"), encoding="utf-8").read().split("SPAGE = 1.7")[0]
G0 = {"__file__": os.path.join(HERE, "check-b384-ifcmarks.py"), "__name__": "b384cropfix"}
exec(src, G0)                                                  # the harness: open_app, load_book, --against (index.html + viewer), the book's path
sync_playwright = G0["sync_playwright"]; AGAINST = G0["AGAINST"]
OUT_JSON = os.environ.get("OUT_JSON", "")
def want(k): return ONLY is None or k in ONLY
passed = [True]
def chk(name, cond, info=""):
    passed[0] = passed[0] and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:2400], flush=True)

KIT = r"""async (ids) => {
  const V = await ifcViewer(); const book = await ifcEnsureBook(); const cdoc = await ifcCountyDoc(); const cache = new Map(); const out = [];
  const cn = (t) => String(t || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  for (const id of ids) {
    const rec = { id };
    try {
      const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), c = q.ifc.citation;
      rec.src = c.source === 'amendment' ? 'county' : 'ifc'; rec.label = c.label || c.section;
      let clip, doc, loc = null;
      if (c.source === 'amendment') { doc = cdoc; clip = await V.countyClip(doc, c, ifcCountyOpts); }
      else { doc = book.doc; loc = V.locate(book.index, c); if (!loc.ok) { rec.skip = 'not located'; out.push(rec); continue; } clip = await V.computeClip(book.doc, book.index, loc, c, book.opts); }
      if (!clip || !clip.ok || !clip.segments.length || clip.segments.some(sg => sg.whole || sg.figure)) { rec.skip = 'no cut picture'; out.push(rec); continue; }
      rec.kind = loc ? loc.kind : 'county';
      const box = document.createElement('div'); document.body.appendChild(box);
      await V.paint(doc, clip, box, { scale: 1.7 });
      const cv = box.querySelector('canvas'); const W = cv.width, H = cv.height, s = 1.7 * Math.min(window.devicePixelRatio || 1, 2);
      const D = cv.getContext('2d').getImageData(0, 0, W, H).data;
      const sum = (x, y) => { const i = (y * W + x) * 4; return D[i] + D[i + 1] + D[i + 2]; };
      const ink = (x, y) => D[(y * W + x) * 4] < 200;            // print and rules: the wash and the gold both keep the red channel at ~255
      const gold = (x, y) => { const i = (y * W + x) * 4; return D[i] > 200 && D[i + 1] > 150 && D[i + 2] < 120; };
      const parts = (cv._ifcParts || []).map(p => ({ ...p, c0: Math.max(0, Math.round((p.x0 - p.ox) * s)), c1: Math.min(W, Math.round((p.x1 - p.ox) * s)) }));
      rec.W = W; rec.H = H; rec.nparts = parts.length;
      // the long horizontal rules of rows [y0, y1) within columns [c0, c1): [{ y, a, b }] (b one past)
      const MIN = 30 * s;
      const rulesIn = (y0, y1, c0, c1) => { const r = []; for (let y = y0; y < y1; y++) { let run = 0; for (let x = c0; x <= c1; x++) { if (x < c1 && ink(x, y)) { run++; continue; } if (run >= MIN) r.push({ y, a: x - run, b: x }); run = 0; } } return r; };
      const groupsOf = (rs) => { const g = []; for (const r of rs.slice().sort((u, v) => u.y - v.y)) { const last = g[g.length - 1]; if (last && r.y - last.y1 <= 1 && Math.min(r.b, last.b) - Math.max(r.a, last.a) > 0) { last.y1 = r.y; last.a = Math.min(last.a, r.a); last.b = Math.max(last.b, r.b); } else g.push({ y0: r.y, y1: r.y, a: r.a, b: r.b }); } return g; };
      // (b) a rule into a piece's own side edge
      rec.cut = [];
      for (const [k, p] of parts.entries()) for (const r of rulesIn(p.row0, p.row1, p.c0, p.c1)) {
        if (r.a <= p.c0 + 1 || r.b >= p.c1 - 1) { rec.cut.push({ piece: k, y: r.y, a: r.a, b: r.b, c0: p.c0, c1: p.c1 }); break; }
      }
      const allRules = groupsOf(rulesIn(0, H, 0, W));
      rec.table = allRules.length > 0;
      if (rec.table) { rec.frame = [Math.min(...allRules.map(g => g.a)), Math.max(...allRules.map(g => g.b))]; }
      // (c) what the picture is centred on: the table (its frame) and the cited print beside it - a county picture's lines of the excerpt (a line of
      // text outside it, the sentence before a table, is not content), a book picture's print with the book's margin marks (a change bar, the
      // deletion arrow) set aside, as the app sets them aside - in kit pixels; and the ink's left edge, by which the code box's picture is found in it
      { let x0 = W; for (let y = 0; y < H; y++) for (let x = 0; x < x0; x++) if (ink(x, y)) { x0 = x; break; } rec.inkX0 = x0; }
      if (rec.table) {
        let c0 = rec.frame[0], c1 = rec.frame[1];
        if (rec.src === 'county') {
          const ex = cn((c.excerpt || '') + ' ' + (c.heading || '') + ' ' + (c.exceptionText || ''));
          for (const p of parts) {
            const top = p.oy - p.row0 / s, bot = p.oy - p.row1 / s, cc = await V.countyChars(doc, p.page, cache);
            for (const l of cc.lines) {
              if (Math.min(top, l.y + 0.66 * l.fs) - Math.max(bot, l.y - 0.18 * l.fs) <= 0.6 || l.x1 < p.x0 || l.x0 > p.x1) continue;
              const f = cn(l.text); if (!f || !(ex.includes(f) || ex.includes(f.slice(0, 20)) || ex.includes(f.slice(-20)))) continue;
              c0 = Math.min(c0, Math.round((l.x0 - p.ox) * s)); c1 = Math.max(c1, Math.round((l.x1 - p.ox) * s));
            }
          }
        } else {
          const colN = new Uint32Array(W); let y0 = -1, y1 = -1;
          for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (ink(x, y)) { colN[x]++; if (y0 < 0) y0 = y; y1 = y; }
          const side = (sd) => {
            const step = sd < 0 ? 1 : -1; let e = sd < 0 ? colN.findIndex(v => v > 0) : W - 1 - [...colN].reverse().findIndex(v => v > 0), out = e;
            for (let n = 0; n < 3; n++) {
              let x = e, w = 0; while (x >= 0 && x < W && colN[x]) { w++; x += step; if (w > 11 * s) return out; }
              let gap = 0; while (x >= 0 && x < W && !colN[x]) { gap++; x += step; }
              if (x < 0 || x >= W || !w) return out;
              const a = Math.min(e, e + step * (w - 1)), b = Math.max(e, e + step * (w - 1)); let rows = 0, solid = 0, fill = 0, r0 = -1, r1 = -1;
              for (let y = y0; y <= y1; y++) { let k2 = 0; for (let xx = a; xx <= b; xx++) if (ink(xx, y)) k2++; if (k2) { rows++; fill += k2; if (r0 < 0) r0 = y; r1 = y; if (k2 >= .8 * w) solid++; } }
              const bar = w >= 1.5 * s && w <= 6.5 * s && rows >= 6 * s && solid >= .9 * rows, tall = r1 - r0 + 1, arrow = w >= 6 * s && tall <= 8 * s && rows === tall && fill >= .5 * w * tall;
              if (!bar && !arrow && !(w <= .6 * s && tall <= .6 * s)) return out;
              if (gap >= 3.5 * s) out = x;
              e = x;
            }
            return out;
          };
          c0 = Math.min(c0, side(-1)); c1 = Math.max(c1, side(1) + 1);
        }
        rec.content = [c0, c1];
      }
      // (a) the picture's first and last rows: only a rule's ink, or an upright's (inked on the next 3 rows in too)
      const edgeInk = (y, dir) => { let n = 0; const rr = rulesIn(y, y + 1, 0, W); for (let x = 0; x < W; x++) { if (!ink(x, y) || rr.some(r => x >= r.a && x < r.b)) continue; let up = true; for (let k = 1; k <= 3; k++) { const yy = y + dir * k; if (yy < 0 || yy >= H || !ink(x, yy)) up = false; } if (!up) n++; } return n; };
      rec.edgeTop = edgeInk(0, 1); rec.edgeBot = edgeInk(H - 1, -1);
      // (a) the first printed line of the picture (page text, from the piece's own page rows)
      const p0 = parts[0];
      if (p0) {
        const top = p0.oy - p0.row0 / s, bot = p0.oy - p0.row1 / s;
        let lines = [];
        if (rec.src === 'county') { const cc = await V.countyChars(doc, p0.page, cache); lines = cc.lines.filter(l => l.x1 > p0.x0 && l.x0 < p0.x1).map(l => ({ y: l.y, h: l.fs, t: l.text })); }
        else {
          const m = await V.pageModel(book.doc, p0.page, book.opts.fontBold, book.opts.cache);
          const ls = [];
          for (const it of m.items) { if (!it.t || it.x + it.w < p0.x0 || it.x > p0.x1) continue; const l = ls.find(u => Math.abs(u.y - it.y) < 2.5); if (l) { l.t += ' ' + it.t; l.h = Math.max(l.h, it.h); } else ls.push({ y: it.y, h: it.h, t: it.t, x: it.x }); }
          lines = ls;
        }
        const shown = lines.filter(l => Math.min(top, l.y + 0.66 * l.h) - Math.max(bot, l.y - 0.18 * l.h) > 0.6).sort((u, v) => v.y - u.y);
        rec.first = shown.length ? shown[0].t : null;
        const ex = cn((c.excerpt || '') + ' ' + (c.heading || '') + ' ' + (c.section || '') + ' ' + (c.exceptionText || ''));
        // (a line of what is cited: its words are the excerpt's - the start of the line or its end, a line the excerpt begins or ends inside - or it opens with the section's number)
        if (rec.src === 'county' && rec.first) { const f = cn(rec.first), sec = cn(c.section); rec.firstIn = !f || ex.includes(f) || ex.includes(f.slice(0, 20)) || ex.includes(f.slice(-20)) || (sec.length >= 3 && f.startsWith(sec)); }
        if (rec.src !== 'county' && loc.kind === 'table') rec.firstIn = /^\s*(?:\[[A-Z]{1,3}\]\s*)?TABLE\b/.test(rec.first || '');
      }
      // (d) the gold of a table row against the table's frame (the rules of its piece)
      const rowMarks = (clip.marks || []).filter(m => m.kind === 'row' || m.tableRow);
      if (rowMarks.length && rec.table) {
        rec.gold = [];
        // each row mark's own rows in the picture (its letters' band, on the piece that shows its page), and the gold across them
        for (const m of rowMarks) {
          const mt = m.i1 != null ? m.i1 : m.y1, mb = m.i0 != null ? m.i0 : m.y0;
          const p = parts.find(q => q.page === m.page && (mt + mb) / 2 <= q.oy - q.row0 / s + 1 && (mt + mb) / 2 >= q.oy - q.row1 / s - 1);
          if (!p) { rec.gold.push({ mark: [m.page, Math.round(mt)], frame: null, why: 'not in the picture' }); continue; }
          const y0 = Math.max(p.row0, Math.round((p.oy - mt) * s)), y1 = Math.min(p.row1 - 1, Math.round((p.oy - mb) * s));
          let gx0 = W, gx1 = -1; for (let y = y0; y <= y1; y++) for (let x = 0; x < W; x++) if (gold(x, y)) { if (x < gx0) gx0 = x; if (x > gx1) gx1 = x; }
          if (gx1 < 0) { rec.gold.push({ mark: [m.page, Math.round(mt)], band: [y0, y1], frame: null, why: 'no gold' }); continue; }
          const rs = groupsOf(rulesIn(p.row0, p.row1, 0, W)).filter(g => Math.min(g.b, gx1 + 1) - Math.max(g.a, gx0) > 0.5 * (gx1 + 1 - gx0));
          if (!rs.length) { rec.gold.push({ band: [y0, y1], gx: [gx0, gx1 + 1], frame: null, why: 'no rule' }); continue; }
          const fa = Math.min(...rs.map(g => g.a)), fb = Math.max(...rs.map(g => g.b));
          // an upright (a column inked down 90% of the gold's rows) just outside each end of the gold: it ends on a rule, not on paper
          const g0 = Math.max(y0, y0 + 2), g1 = Math.min(y1, y1 - 2), up = (x) => { if (x < 0 || x >= W) return false; let n = 0; for (let y = g0; y <= g1; y++) if (ink(x, y)) n++; return n >= 0.9 * (g1 - g0 + 1); };
          const onL = [1, 2, 3].some(d => up(gx0 - d)), onR = [0, 1, 2].some(d => up(gx1 + 1 + d));
          rec.gold.push({ band: [y0, y1], gx: [gx0, gx1 + 1], frame: [fa, fb], inL: gx0 - fa, inR: fb - (gx1 + 1), onL, onR });
        }
      }
      // (e) the joins between pieces of a table
      if (parts.length > 1 && rec.table) {
        rec.joins = [];
        const uprights = (y0, y1) => { const cols = []; const h = y1 - y0 + 1; if (h < 3) return cols; for (let x = 0; x < W; x++) { let n = 0; for (let y = y0; y <= y1; y++) if (ink(x, y)) n++; if (n >= 0.95 * h) { const l = cols[cols.length - 1]; if (l && l[1] === x - 1) l[1] = x; else cols.push([x, x]); } } return cols; };
        for (let k = 1; k < parts.length; k++) {
          const q = parts[k - 1], p = parts[k];
          const rq = groupsOf(rulesIn(q.row0, q.row1, 0, W)), rp = groupsOf(rulesIn(p.row0, p.row1, 0, W));
          const j = { k, gap: p.row0 - q.row1, omit: !!(clip.segments[k] && clip.segments[k].omit) };
          if (!rp.length) { j.notes = true; }
          const fq = rq.length ? [Math.min(...rq.map(g => g.a)), Math.max(...rq.map(g => g.b))] : null, fp = rp.length ? [Math.min(...rp.map(g => g.a)), Math.max(...rp.map(g => g.b))] : null;
          j.fq = fq; j.fp = fp;
          // the rule that ends the piece above (its last rows) and the one that starts the piece below
          const lastQ = rq.length ? rq[rq.length - 1] : null, firstP = rp.length ? rp[0] : null;
          j.qEnds = !!(lastQ && q.row1 - 1 - lastQ.y1 <= 1 && fq && lastQ.a - fq[0] <= 1 && fq[1] - lastQ.b <= 1);
          j.pStarts = !!(firstP && firstP.y0 - p.row0 <= 1 && fp && firstP.a - fp[0] <= 1 && fp[1] - firstP.b <= 1);
          // the uprights of the cell above the join and the cell below it
          const prevQ = rq.length > 1 ? rq[rq.length - 2] : null;
          const uq = lastQ ? uprights(prevQ ? prevQ.y1 + 1 : Math.max(q.row0, lastQ.y0 - Math.round(12 * s)), lastQ.y0 - 1) : [];
          // (where the table runs on - one rule at the seam - the piece below starts in a cell: its first rule is the one under that cell)
          const pOnRule = !!(firstP && firstP.y0 - p.row0 <= 1), nextP = pOnRule ? (rp.length > 1 ? rp[1] : null) : firstP;
          const up = firstP ? uprights(pOnRule ? firstP.y1 + 1 : p.row0, nextP ? nextP.y0 - 1 : p.row1 - 1) : [];
          j.uq = uq; j.up = up;
          const near = (A, B) => A.every(([a, b]) => B.some(([c, d]) => Math.abs(c - a) <= 1 && Math.abs(d - b) <= 1));
          j.sameUprights = !j.notes && uq.length > 0 && near(uq, up) && near(up, uq);
          // between: the band (omitted rows) or nothing
          if (j.gap > 0) {
            const band = uprights(q.row1, p.row0 - 1 - (j.notes ? Math.round(4 * s) : 0));
            j.band = band; j.bandRuns = uq.length > 0 && near(uq, band);
            let dots = 0; for (let y = q.row1; y < p.row0; y++) for (let x = 0; x < W; x++) { const i = (y * W + x) * 4; if (D[i] < 200 && D[i + 2] < 120 && D[i] > 40 && !uq.some(([a, b]) => x >= a - 1 && x <= b + 1)) dots++; }
            j.dots = dots > 0;
          }
          // a doubled rule at the seam: two rule groups within 2pt either side of it
          const seam = groupsOf(rulesIn(Math.max(0, q.row1 - Math.round(2 * s)), Math.min(H, p.row0 + Math.round(2 * s)), 0, W));
          j.seamRules = seam.length;
          rec.joins.push(j);
        }
      }
      box.remove();
    } catch (e) { rec.err = String(e && e.message || e).slice(0, 300); }
    out.push(rec);
  }
  return out;
}"""

CARD = r"""async ([ids, info]) => {
  const wt = ms => new Promise(r => setTimeout(r, ms));
  const panel = document.querySelector('.qpanel'); const real = panel.querySelector('.ifc-ref');
  let h = document.getElementById('__cfh');
  if (!h) { h = document.createElement('div'); h.id = '__cfh'; real.after(h); real.style.display = 'none'; }
  const s = 1.7 * Math.min(window.devicePixelRatio || 1, 2), out = [];
  for (const id of ids) {
    const rec = { id };
    try {
      const item = QUESTIONS.find(q => q.ifc && q.ifc.id === id);
      ifcNodeCache.clear();
      const node = buildBankNote(item); h.replaceChildren(node);
      const d = node.querySelector('details.ifc-code'); d.open = true;
      for (let k = 0; k < 400; k++) { await wt(50); if (node.querySelector('.ifc-code-body > .ifc-links, .ifc-code-body > .ifc-note, .ifc-code-body > .ifc-locked')) break; }
      await wt(30);
      rec.pics = [];
      const cvs = [...node.querySelectorAll('.ifc-code-body .ifc-clips canvas')].filter(cv => !cv.classList.contains('ifc-page') && cv.width && cv.height);
      const I = info[id];
      if (cvs.length === 1 && I) {
        const cv = cvs[0], W = cv.width, H = cv.height;
        const D = cv.getContext('2d').getImageData(0, 0, W, H).data;
        let x0 = W; for (let y = 0; y < H; y++) for (let x = 0; x < x0; x++) if (D[(y * W + x) * 4] < 200) { x0 = x; break; }
        const ox = I.inkX0 - x0, a = I.content[0] - ox, b = I.content[1] - ox;      /* the code box's picture is the kit's, cut at ox (ifcFrameClips) */
        const fr = (cv.closest('.ifc-frame') || cv).getBoundingClientRect(), r = cv.getBoundingClientRect(), f = r.width / W;
        const L = r.left + a * f - fr.left, R = fr.right - (r.left + b * f);
        rec.pics.push({ L: Math.round(L * 100) / 100, R: Math.round(R * 100) / 100 });
      } else if (cvs.length !== 1) rec.many = cvs.length;
      h.replaceChildren();
    } catch (e) { rec.err = String(e && e.message || e).slice(0, 200); }
    out.push(rec);
  }
  return out;
}"""

DEVICES = [("iPhone 17 Pro Max", 440, 956, 3), ('iPad Pro 11"', 834, 1194, 2)]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G0["G"]["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
    ctx, pg, errs = G0["open_app"](br, 440, 956, 2)
    acc = G0["load_book"](pg)
    chk("the owner's IFC PDF is accepted by the app", acc, acc)
    ids = pg.evaluate("()=>QUESTIONS.filter(q=>q.ifc && q.ifc.citation).map(q=>q.ifc.id)")
    if IDS: ids = [i for i in ids if i in IDS]
    print("%d Fire Code references (%s)" % (len(ids), "the build under test" if AGAINST is None else "AGAINST"), flush=True)
    recs = []
    for k in range(0, len(ids), 40):
        for attempt in range(2):
            try: recs += pg.evaluate(KIT, ids[k:k + 40]); break
            except Exception as e:
                if attempt: recs += [{"id": i, "err": str(e)[:200]} for i in ids[k:k + 40]]
        if (k // 40) % 10 == 9: print("  ... %d / %d" % (min(k + 40, len(ids)), len(ids)), flush=True)
    errs_kit = list(errs)
    ctx.close()
    pics = [r for r in recs if not r.get("skip") and not r.get("err")]
    tables = [r for r in pics if r.get("table")]
    print("  %d pictures drawn (%d book, %d county), %d with a ruled table; %d not a cut picture; %d errors"
          % (len(pics), sum(r["src"] == "ifc" for r in pics), sum(r["src"] == "county" for r in pics), len(tables), sum(1 for r in recs if r.get("skip")), sum(1 for r in recs if r.get("err"))), flush=True)
    chk("every reference painted without an error", not any(r.get("err") for r in recs), [(r["id"], r["err"]) for r in recs if r.get("err")][:10])
    if want("a"):
        bad = [(r["id"], r["edgeTop"], r["edgeBot"]) for r in pics if r["edgeTop"] or r["edgeBot"]]
        chk("(a) no picture has ink on its first or last row but a table's rules (no half line at an edge): %d pictures" % len(pics), not bad, bad[:20])
        bad = [(r["id"], r["first"]) for r in pics if r["src"] == "county" and r.get("firstIn") is False]
        chk("(a) every county picture starts on a line of what it cites (no sentence before a table's title): %d" % sum(r["src"] == "county" for r in pics), not bad, bad[:20])
        bad = [(r["id"], r["first"]) for r in pics if r["src"] == "ifc" and r.get("kind") == "table" and r.get("firstIn") is False]
        chk("(a) every book table's picture starts on its TABLE caption: %d" % sum(r["src"] == "ifc" and r.get("kind") == "table" for r in pics), not bad, bad[:20])
    if want("b"):
        bad = [(r["id"], r["label"], r["cut"][0]) for r in pics if r["cut"]]
        chk("(b) no rule of any piece runs into the piece's side edge (the whole table, its border inside): %d tables" % len(tables), not bad, bad[:25])
    if want("d"):
        golds = [(r, g) for r in pics for g in (r.get("gold") or [])]
        # a row: from the left edge to the right edge, ending on the border both sides, the same inset; a row beside a label cell merged over several rows
        # (Tables 3206.2, 5003.8.3.2: mergedLabel) is gold from that cell's rule to the table's edge, and the label cell its own gold: each ends on a rule
        def ok_row(g): return g["frame"] is not None and g["onL"] and g["onR"] and 0 <= g["inL"] <= 4 and 0 <= g["inR"] <= 4 and abs(g["inL"] - g["inR"]) <= 4
        def ok_cell(g): return g["frame"] is not None and g["onL"] and g["onR"] and ((0 <= g["inL"] <= 4) or (0 <= g["inR"] <= 4))
        bad = [(r["id"], g) for r, g in golds if not ok_row(g) and not ok_cell(g)]
        cells = sorted({r["id"] for r, g in golds if not ok_row(g) and ok_cell(g)})
        worst = max([max(abs(g["inL"]), abs(g["inR"])) for r, g in golds if g["frame"] and ok_row(g)] or [0])
        chk("(d) every table row's gold runs from the table's left edge to its right edge, on the border both sides (within 2 CSS px): %d rows, worst inset %s px at dpr 2; %s with a merged label cell"
            % (len(golds), worst, cells), not bad, bad[:20])
    if want("e"):
        joins = [(r, j) for r in pics for j in (r.get("joins") or []) if j["fq"] and (j["fp"] or j.get("omit"))]      # a join of two ruled pieces (a section's text above a table is not one)
        bad = []
        for r, j in joins:
            why = []
            if j["fq"] and j["fp"] and (abs(j["fq"][0] - j["fp"][0]) > 1 or abs(j["fq"][1] - j["fp"][1]) > 1): why.append("frames %s / %s" % (j["fq"], j["fp"]))
            if not j["qEnds"]: why.append("the piece above does not end on a rule across the table")
            if not j.get("notes"):
                if j["gap"] > 0 and not j["pStarts"]: why.append("the piece below does not start on a rule across the table")
                if not j["sameUprights"]: why.append("uprights above %s below %s" % (j["uq"], j["up"]))
            if j["gap"] > 0 and not j.get("bandRuns"): why.append("the band's uprights %s do not run on (above %s)" % (j.get("band"), j["uq"]))
            if j["gap"] > 0 and not j.get("dots"): why.append("no omission dots in the band")
            if j["gap"] <= 0 and j["seamRules"] != 1: why.append("%d rules at the seam" % j["seamRules"])
            if why: bad.append((r["id"], j["k"], why))
        chk("(e) every spliced table joins as one table: %d joins in %d pictures" % (len(joins), len({r["id"] for r, j in joins})), not bad, bad[:20])
    if want("c"):
        cids = [r["id"] for r in tables]
        for name, w, h, dpr in DEVICES:
            ctx, pg, errs = G0["open_app"](br, w, h, dpr)
            G0["load_book"](pg)
            pg.evaluate("""(id)=>{ const i = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[i].topic]; beginRun([i]); }""", "ch3-053")
            pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(900)
            for _ in range(6):
                c = pg.evaluate("""()=>{ const r=correctSlot(order[pos]); const el=document.querySelector('.qpanel .choice[data-index="'+r+'"]'); if(!el) return null; el.scrollIntoView({block:'center',behavior:'instant'}); const b=el.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }""")
                if c: pg.touchscreen.tap(c[0], c[1])
                pg.wait_for_timeout(1300)
                if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-ref')"): break
            res = []
            info = {r["id"]: {"inkX0": r["inkX0"], "content": r["content"]} for r in tables if r.get("content")}
            for k in range(0, len(cids), 20): res += pg.evaluate(CARD, [cids[k:k + 20], {i: info[i] for i in cids[k:k + 20] if i in info}])
            bad = [(x["id"], p) for x in res for p in x.get("pics", []) if abs(p["L"] - p["R"]) > 2]
            worst = max([abs(p["L"] - p["R"]) for x in res for p in x.get("pics", [])] or [0])
            chk("(c) %s: every table centred in its code box (|left - right| <= 2 CSS px): %d pictures, worst %.2f px" % (name, len(res), worst), not bad and not any(x.get("err") for x in res), (bad[:20], [x for x in res if x.get("err")][:5]))
            errs_kit += errs
            ctx.close()
    chk("(f) no page errors", not errs_kit, errs_kit[:5])
    if OUT_JSON: json.dump(recs, open(OUT_JSON, "w"))
    br.close()
print("ALL PASS" if passed[0] else "SOME CHECKS FAILED")
sys.exit(0 if passed[0] else 1)
