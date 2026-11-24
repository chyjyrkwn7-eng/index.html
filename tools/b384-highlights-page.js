// The page half of tools/check-b384-highlights.py, run inside the APP's own page (so the pictures are the ones a phone gets): for one county
// citation it draws (1) the card's picture exactly as the app does (ifcFillCode: the kit's cut, then the column reflow, then the frame) and
// (2) the whole page as "Show the whole page" does (V.paintPages), and reads the DARKER GOLD band of each line off the pixels, against the
// print under it. Nothing here reads the kit's marks: only the pictures.
//
// For every line of a highlight, in both views:
//   * no word of the print is cut by the band's edge (a band that ends inside "apart." and leaves its full stop out cuts the word "apart.");
//   * the band starts at the first glyph of the first word it covers and ends at the last glyph of the last (no more than the marker's own
//     room - 0.14 em plus the letter's side bearing - beyond them), so there is no gap before a full stop or after a closing quote;
//   * (the whole page) the words the bands cover are exactly the words of the cited text (found in the page's own text by words), none left
//     outside a band and none marked that are not cited.
// A word is a run of print columns; a gap wider than 0.22 em starts the next one. Table rows (cell | cell) run rule to rule on purpose: only
// the first check is made on them.
(() => {
  const nz = s => String(s).replace(/\u00b2/g, "2").replace(/\u00b3/g, "3").replace(/\u00b9/g, "1").toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9]+/g, "");
  const deepPx = (R, G, B) => R >= 235 && G < 232 && B < 95;                    // the wash is (255,245,160), the gold over it (255,215,25)
  const inkPx = (R, G, B) => R + G + B < 330;
  const CARD_GAP = 0.2;                                                           // (the card's reflow sets its spaces a little narrower)
  const GAP = 0.22;                                                              // em: a wider gap in the print than this is a space
  // a citation inside a table: a cell or a row ("cell | cell"), a TABLE's rows, or the short lines of a table's continuation page ("Toxic materials / Gases / See Section ...")
  const tabular = (c) => {
    if (c.source === "ifc" && (c.row || /^table/i.test(String(c.section || "")))) return true;      // (the IFC leg) a table's clipping: its rows run rule to rule
    const ex = String(c.excerpt || ""), ls = ex.split("\n");
    return / \| | \u203a /.test(String(c.highlight || "")) || /\bTABLE\b/.test(ex) || (ls.length >= 4 && ls.filter(l => l.length < 34).length >= 0.75 * ls.length);
  };
  let V = null, doc = null;
  async function boot() { if (!V) { V = await ifcViewer(); doc = await ifcCountyDoc(); } }
  function groupsOf(col, W, gap) {
    const out = []; let a = -1, last = -1;
    for (let x = 0; x < W; x++) { if (!col[x]) continue; if (a < 0) { a = x; last = x; } else if (x - last > gap) { out.push([a, last]); a = x; last = x; } else last = x; }
    if (a >= 0) out.push([a, last]);
    return out;
  }
  // one text line's reading over the rows r0..r1 of an image: its print's columns (a table's rules left out: a row of ink as long as 8 em, a column of it
  // that fills the rows) and the columns that hold the darker gold
  function readLine(img, W, r0, r1, em, wantInk) {
    const D = img.data, deep = new Uint8Array(W);
    r0 = Math.max(0, r0); r1 = Math.min(img.height, r1);
    const cnt = new Uint16Array(W);
    for (let y = r0; y < r1; y++) {
      let run = 0, best = 0;
      const dark = [];
      for (let x = 0, i = y * W * 4; x < W; x++, i += 4) {
        const R = D[i], G = D[i + 1], B = D[i + 2];
        if (deepPx(R, G, B)) deep[x] = 1;
        const k = wantInk === img && inkPx(R, G, B);
        dark.push(k);
        if (k) { run++; if (run > best) best = run; } else run = 0;
      }
      if (wantInk === img && best < 8 * em) for (let x = 0; x < W; x++) if (dark[x]) cnt[x]++;
    }
    const ink = new Uint8Array(W), rows = Math.max(1, r1 - r0);
    for (let x = 0; x < W; x++) if (cnt[x] && cnt[x] < 0.88 * rows) ink[x] = 1;
    return { ink, deep };
  }
  // the verdict on one line: words [a,b], bands [a,b] (px) -> violations
  function judge(words, bands, em, s, tight, loose, roomEm) {
    const bad = [], tol = Math.max(1.2, (loose ? 4.2 : 0.3) * s), room = (roomEm || 0.34) * em;
    for (const [da, db] of bands) {
      const cov = words.filter(([a, b]) => b >= da - tol && a <= db + tol);
      const inside = cov.filter(([a, b]) => a >= da - tol && b <= db + tol);
      // (in a table the rows are set so close that a word of the next row can fall in a line's rows: a cut longer than 6pt there is another row's word)
      for (const w of cov) if (!inside.includes(w) && !(loose && Math.max(da - w[0], w[1] - db) > 6 * s)) bad.push(["a word is cut by the band's edge", (w[0] < da - tol ? "left " + ((da - w[0]) / s).toFixed(1) : "right " + ((w[1] - db) / s).toFixed(1)) + "pt of a word outside"]);
      if (!inside.length) { if (!loose) bad.push(["a band holds no word", ((db - da) / s).toFixed(1) + "pt wide"]); continue; }
      if (tight) {
        const gl = inside[0][0] - da, gr = db - inside[inside.length - 1][1];
        if (gl > room) bad.push(["the band starts before its first glyph", (gl / s).toFixed(1) + "pt early"]);
        if (gr > room) bad.push(["the band ends after its last glyph", (gr / s).toFixed(1) + "pt late"]);
      }
    }
    return bad;
  }
  function wordsOfLine(ln) {
    let text = "", end = null;
    for (const it of ln.items) { if (end != null && it.x - end > 0.12 * ln.fs) text += " "; text += it.s; end = end == null ? it.x + it.w : Math.max(end, it.x + it.w); }
    return text.split(/\s+/).filter(Boolean);
  }
  async function rawImage(page, s) {
    const vp = page.getViewport({ scale: s }), cv = document.createElement("canvas");
    cv.width = Math.ceil(vp.width); cv.height = Math.ceil(vp.height);
    const g = cv.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, cv.width, cv.height);
    await page.render({ canvasContext: g, viewport: vp }).promise;
    const img = g.getImageData(0, 0, cv.width, cv.height); cv.width = 0; cv.height = 0; return img;
  }
  window.__hl = {
    // ---- the whole page
    async page(id, S, dump) {
      await boot();
      const q = QUESTIONS.find(q => q.ifc && q.ifc.id === id), c = q.ifc.citation;
      const clip = await V.countyClip(doc, c, ifcCountyOpts);
      const res = { id, view: "page", bad: [], lines: 0, bands: 0, unverifiable: 0, located: null, expected: 0, missing: [], extra: [] };
      if (!clip || !clip.ok) { res.noclip = true; return res; }
      const box = document.createElement("div"); document.body.appendChild(box);
      try {
        await V.paintPages(doc, clip.pages, box, { scale: S, ...ifcCountyOpts, clip });
        const cvs = [...box.querySelectorAll("canvas.ifc-page")], p0 = c.pdfPage, p1 = c.pdfPageEnd || c.pdfPage;
        if (dump) res.img = cvs.map(cv => cv.toDataURL("image/png"));
        const stream = [], rowish = / \| | › /.test(String(c.highlight || "")) || tabular(c);      // (a cell of a table: its band runs to the table's rules)
        const covered = new Set();
        for (let k = 0; k < clip.pages.length; k++) {
          const p = clip.pages[k], cv = cvs[k]; if (!cv) continue;
          const page = await doc.getPage(p), s = cv.width / page.view[2], PH = page.view[3], cc = await V.countyChars(doc, p, ifcCountyOpts.cache);
          const hi = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height), raw = await rawImage(page, s);
          cc.lines.forEach((ln, li) => {
            const words = wordsOfLine(ln), base = (PH - ln.y) * s, em = ln.fs * s;
            const r0 = Math.round(base - 0.78 * em), r1 = Math.round(base + 0.28 * em);
            const a = readLine(raw, cv.width, r0, r1, em, raw), b = readLine(hi, cv.width, r0, r1, em, null);
            const groups = groupsOf(a.ink, cv.width, GAP * em), bands = groupsOf(b.deep, cv.width, 2);
            res.lines++;
            if (bands.length) {
              res.bands += bands.length;
              for (const f of judge(groups, bands, em, s, !(rowish || ln.tbl), rowish || ln.tbl)) res.bad.push([f[0], "p" + p + " line " + li + ": " + f[1]]);
            }
            const aligned = groups.length === words.length;
            if (p >= p0 && p <= p1) words.forEach((w, wi) => stream.push({ p, li, wi, n: nz(w), g: aligned ? groups[wi] : null, bands, aligned }));
            if (bands.length && !aligned) res.unverifiable++;
            if (aligned) groups.forEach((g, wi) => { if (bands.some(([da, db]) => g[0] >= da - 1.5 && g[1] <= db + 1.5)) covered.add(p + ":" + li + ":" + wi); });
          });
        }
        // the cited words, found in the page's own text
        const toks = String(c.highlight || "").split(/\s+/).map(nz).filter(Boolean);
        if (toks.length && !rowish) {
          const T = stream.filter(e => e.n), occ = [];
          // (by letters, so a word the book breaks over two lines - "I-" / "3" - is found: a hit starts and ends on a word's edge)
          const starts = [], ends = []; let acc = 0, joined = "";
          T.forEach(e => { starts.push(acc); acc += e.n.length; ends.push(acc); joined += e.n; });
          const find = (seq) => {
            const o = [], key = seq.join("");
            for (let at = joined.indexOf(key); at >= 0; at = joined.indexOf(key, at + 1)) {
              const i = starts.indexOf(at), j = ends.indexOf(at + key.length);
              if (i >= 0 && j >= i) o.push([i, j]);
            }
            return o;
          };
          let hits = find(toks);
          if (!hits.length && toks.length > 8) {                                  // a piece that skips a few words: its first and its last
            const h = find(toks.slice(0, 4)), t = find(toks.slice(-4));
            hits = h.flatMap(x => t.filter(y => y[0] >= x[0]).slice(0, 1).map(y => [x[0], y[1]]));
          }
          // the occurrence the page marks
          let best = null, bs = -1;
          for (const [i, j] of hits) {
            const set = stream.slice(stream.indexOf(T[i]), stream.indexOf(T[j]) + 1);
            const sc = set.filter(e => covered.has(e.p + ":" + e.li + ":" + e.wi)).length;
            if (sc > bs) { bs = sc; best = set; }
          }
          res.located = !!best;
          if (best) {
            res.expected = best.length;
            for (const e of best) {
              if (!e.aligned || !e.n) continue;
              if (!covered.has(e.p + ":" + e.li + ":" + e.wi)) res.missing.push("p" + e.p + " line " + e.li + " word " + e.wi + " (" + e.n + ")");
            }
            const exp = new Set(best.map(e => e.p + ":" + e.li + ":" + e.wi));
            for (const k of covered) if (!exp.has(k)) res.extra.push(k);
            if (res.missing.length) res.bad.push(["a cited word is left outside the band", res.missing.slice(0, 3).join(", ")]);
            if (res.extra.length) res.bad.push(["a word that is not cited is inside the band", res.extra.slice(0, 3).join(", ")]);
          } else res.bad.push(["the cited words are not found in the page's text", toks.slice(0, 4).join(" ")]);
        }
      } finally { box.remove(); }
      return res;
    },
    // ---- (384.56) the IFC leg. The owner's own book; the clipping the app cuts for the question (its citation, patches and all), painted as the two views paint it
    // ("page": V.paintPages, "Show the whole book page"; "box": V.paint, the code box). For every highlighted sentence or list item (a `find` mark, kind cite) and
    // table row (kind row) the PIXELS are read, as for the county: the print's word columns on the marked line (from the page drawn without marks) against the
    // darker gold's columns (from the picture) -
    //   (1) no word of the marked line is cut by an edge of the band,
    //   (2) a sentence's band begins at the first glyph of its first word and ends at the last glyph of its last (the full stop included, no more than the marker's
    //       own room beyond it); a row runs rule to rule on purpose: (1) only.
    // The kit's marks say only WHICH lines to look at and between which x a sentence runs (it may begin or end inside a line); what is gold and what is printed is
    // read off the pictures. Everything is worked in pdf points. The code box is one sheet of the clipping's pieces set one under another (paint(): clip.sheet), so
    // a point of the page is found in it through that layout.
    async ifcEnds(id, S, view, dump) {
      await boot();
      const book = await ifcEnsureBook();
      const q = QUESTIONS.find(q => q.ifc && q.ifc.id === id), c = q.ifc.citation;
      const res = { id, view, bad: [], checked: 0, marks: 0 };
      if (!book) { res.nobook = true; return res; }
      const loc = V.locate(book.index, c);
      if (!loc.ok || loc.kind === "pages") { res.noclip = true; return res; }
      const clip = await V.computeClip(book.doc, book.index, loc, c, book.opts);
      if (!clip.ok || !clip.segments.length) { res.noclip = true; return res; }
      const box = document.createElement("div"); document.body.appendChild(box);
      try {
        let cvs, frameOf;
        if (view === "page") {
          await V.paintPages(book.doc, clip.pages, box, { scale: S, ...book.opts, clip });
          cvs = [...box.querySelectorAll("canvas.ifc-page")];
          frameOf = async (m) => {
            const cv = cvs[clip.pages.indexOf(m.page)]; if (!cv) return null;
            const page = await book.doc.getPage(m.page);
            return { cv, page, s: cv.width / page.view[2], ox: 0, oy: page.view[3] };
          };
        } else {
          await V.paint(book.doc, clip, box, { scale: S });
          cvs = [...box.querySelectorAll("canvas")];
          const segs = clip.segments, sheet = segs.length === 1 ? { pieces: [{ i: 0, dx: 0, top: segs[0].y1, bot: segs[0].y0, gap: 0 }] }
            : (clip.sheet || { pieces: segs.map((sg, i) => ({ i, dx: 0, top: sg.y1, bot: sg.y0, gap: i ? 4 : 0 })) });
          const cv0 = cvs[0];
          let X0 = Infinity, X1 = -Infinity;
          for (const pc of sheet.pieces) { X0 = Math.min(X0, segs[pc.i].x0 + pc.dx); X1 = Math.max(X1, segs[pc.i].x1 + pc.dx); }
          const sc = cv0 ? cv0.width / (X1 - X0) : 1;
          let yy = 0; const placed = [];
          for (const pc of sheet.pieces) { yy += Math.round((pc.gap || 0) * sc); placed.push({ pc, seg: segs[pc.i], y: yy }); yy += Math.round((pc.top - pc.bot) * sc); }
          frameOf = async (m) => {
            const my = (m.i0 + m.i1) / 2, mx = (m.x0 + m.x1) / 2;
            const pl = placed.find(q => q.seg.page === m.page && mx >= q.seg.x0 - 2 && mx <= q.seg.x1 + 2 && my <= q.pc.top + 6 && my >= q.pc.bot - 6);
            if (!pl || !cv0) return null;
            // pdf x -> sheet x: (x + dx - X0) * sc;  pdf y -> sheet y: the piece's top (pc.top) is at pl.y
            return { cv: cv0, page: await book.doc.getPage(m.page), s: sc, ox: X0 - pl.pc.dx, oy: pl.pc.top + pl.y / sc };
          };
        }
        if (dump) res.img = cvs.map(cv => cv.toDataURL("image/png"));
        const raws = new Map(), his = new Map();
        const groupsPts = (pts, gap) => { const out = []; let a = null, l = null; for (const v of pts) { if (a == null) { a = v; l = v; } else if (v - l > gap) { out.push([a, l]); a = v; l = v; } else l = v; } if (a != null) out.push([a, l]); return out; };
        for (const m of clip.marks || []) {
          if (m.kind !== "cite" && m.kind !== "row") continue;
          const f = await frameOf(m);
          if (!f) { res.bad.push(["a mark is not inside any picture", m.kind + " p" + m.page + " x" + Math.round(m.x0) + "-" + Math.round(m.x1) + " y" + Math.round(m.i0) + "-" + Math.round(m.i1)]); continue; }
          const { cv, page, s, ox, oy } = f, PH = page.view[3];
          const rk = m.page + ":" + s;
          if (!raws.has(rk)) raws.set(rk, await rawImage(page, s));
          if (!his.has(cv)) his.set(cv, cv.getContext("2d").getImageData(0, 0, cv.width, cv.height));
          const raw = raws.get(rk), hi = his.get(cv);
          const ink0 = m.i0 != null ? m.i0 : m.y0, ink1 = m.i1 != null ? m.i1 : m.y1, fs = m.fs || 10, shrink = 0.14 * (ink1 - ink0);
          const em = fs * s;
          // rows: the mark's own line, a little inside its ink extent (the band of a line above or below is one outline with this one)
          const rr0 = Math.round((PH - (ink1 - shrink)) * s), rr1 = Math.round((PH - (ink0 + shrink)) * s);      // in the raw page
          const hr0 = Math.round((oy - (ink1 - shrink)) * s), hr1 = Math.round((oy - (ink0 + shrink)) * s);       // in the picture
          if (hr0 < 1.1 * em || hr1 > cv.height - 1.1 * em) { res.edge = (res.edge || 0) + 1; continue; }                           // (the code box trims its first and last piece to a clean row: a line within a line of its top or bottom edge is read in the whole-page view only)
          const ink = readLine(raw, raw.width, rr0, rr1, em, raw).ink, deep = readLine(hi, cv.width, hr0, hr1, em, null).deep;
          const inkPts = [], deepPts = [];
          for (let x = Math.floor((m.x0 - 3) * s); x <= Math.ceil((m.x1 + 3) * s); x++) if (x >= 0 && x < raw.width && ink[x]) inkPts.push(x / s);
          for (let x = Math.floor((m.x0 - 8 - ox) * s); x <= Math.ceil((m.x1 + 8 - ox) * s); x++) if (x >= 0 && x < cv.width && deep[x]) deepPts.push(x / s + ox);
          const words = groupsPts(inkPts, GAP * fs).filter(([a, b]) => (a + b) / 2 >= m.x0 + 1 && (a + b) / 2 <= m.x1 - 1);
          const bands = groupsPts(deepPts, Math.max(2 / s, 0.22 * fs));      // (a hairline hole in the gold at a word space is not an edge)
          const where = "p" + m.page + " y" + Math.round((ink0 + ink1) / 2) + " x" + Math.round(m.x0);
          res.marks++;
          if (!bands.length) { res.bad.push(["no gold under a mark", m.kind + " " + where]); continue; }
          if (!words.length) continue;
          res.checked++;
          const tol = 0.6 + 0.6 / s, room = (fs >= 9 ? 0.34 : 0.55) * fs + 0.8;      // (a table cell is set at 7 to 9 pt and its marker is a whole cell wide)
          const band = bands.find(([a, b]) => words.some(([wa, wb]) => wb >= a - tol && wa <= b + tol));
          if (!band) { res.bad.push(["the marked words are outside every band", where]); continue; }
          // (a word may stand in another band of the same line: a table row's cells are cut by the rules between them)
          const holds = ([wa, wb]) => bands.some(([a, b]) => wa >= a - tol && wb <= b + tol);
          for (const w of words) if (!holds(w)) res.bad.push(["a word is cut by the band's edge", "word " + w.map(v => v.toFixed(1)) + " bands " + JSON.stringify(bands.map(b => b.map(v => +v.toFixed(1)))) + ", " + where]);
          if (m.kind === "cite") {
            const gl = words[0][0] - band[0], gr = band[1] - words[words.length - 1][1];
            if (gl > room) res.bad.push(["the band starts before its first glyph", gl.toFixed(1) + "pt early, " + where]);
            if (gr > room) res.bad.push(["the band ends after its last glyph", gr.toFixed(1) + "pt late, " + where]);
          }
        }
      } finally { box.remove(); }
      return res;
    },
    // ---- the card's picture
    async card(id, S, dump) {
      await boot();
      const q = QUESTIONS.find(q => q.ifc && q.ifc.id === id), c = q.ifc.citation;
      const res = { id, view: "card", bad: [], lines: 0, bands: 0, covered: 0, tokens: 0 };
      const body = document.createElement("div"); body.style.cssText = "width:392px;position:absolute;left:0;top:0";
      document.body.appendChild(body);
      try {
        await ifcFillCode({ ifc: { citation: c } }, body, document.createElement("div"));
        const cvs = [...body.querySelectorAll("canvas")];
        if (dump) res.img = cvs.map(cv => cv.toDataURL("image/png"));
        if (!cvs.length) { res.notpicture = true; return res; }
        const rowish = / \| | › /.test(String(c.highlight || "")) || tabular(c);
        const s = Math.min(window.devicePixelRatio || 1, 2) * 1.7;
        for (const cv of cvs) {
          const W = cv.width, H = cv.height, img = cv.getContext("2d").getImageData(0, 0, W, H), D = img.data;
          // the text lines: rows with print, split where a row has none
          const em0 = 11 * s, lines = [];
          // (384 cropfix) a table's uprights are not print: inked in every row of the table, they left no empty row between its lines, so the split below
          // fell wherever a tie of minima put it - once a table's right border came into the picture, through the middle of a label's first line
          const rule = new Uint8Array(W * H);
          for (let x = 0; x < W; x++) for (let y = 0; y < H;) {
            const i = (y * W + x) * 4; if (!inkPx(D[i], D[i + 1], D[i + 2])) { y++; continue; }
            let e = y; while (e < H) { const j = (e * W + x) * 4; if (!inkPx(D[j], D[j + 1], D[j + 2])) break; e++; }
            if (e - y >= 1.5 * em0) for (let k = y; k < e; k++) rule[k * W + x] = 1;
            y = e;
          }
          const rowInk = new Uint16Array(H);                                      // print pixels in each row
          for (let y = 0; y < H; y++) for (let x = 0, i = y * W * 4; x < W; x++, i += 4) if (!rule[y * W + x] && inkPx(D[i], D[i + 1], D[i + 2])) rowInk[y]++;
          // a cluster of rows with print is one line, or (lines set close, a descender in the next ascender's rows) several: split at the row with least print
          const split = (r0, r1) => {
            // (taller than one line: split at the row between two humps of print, where it falls to under a third of the lower hump)
            if (r1 - r0 > 1.05 * em0) {
              let best = -1, bv = Infinity;
              for (let y = Math.ceil(r0 + 0.4 * em0); y <= Math.floor(r1 - 0.4 * em0); y++) if (rowInk[y] < bv) { bv = rowInk[y]; best = y; }
              if (best > 0) {
                let ml = 0, mr = 0;
                for (let y = r0; y < best; y++) ml = Math.max(ml, rowInk[y]);
                for (let y = best; y < r1; y++) mr = Math.max(mr, rowInk[y]);
                if (bv <= 0.34 * Math.min(ml, mr) || r1 - r0 > 1.65 * em0) { split(r0, best); split(best, r1); return; }
              }
            }
            if (r1 - r0 >= 0.3 * em0) lines.push([r0, r1]);
          };
          let a = -1;
          for (let y = 0; y <= H; y++) { if (y < H && rowInk[y]) { if (a < 0) a = y; } else if (a >= 0) { split(a, y); a = -1; } }
          for (const [r0, r1] of lines) {
            const em = 11 * s, rd = readLine(img, W, Math.round(r0 - 0.06 * em), Math.round(r1 + 0.06 * em), em, img);       // (rows a hair past the print: a line of capitals and ascenders only has a stem in every row of its own)
            const groups = groupsOf(rd.ink, W, CARD_GAP * em), bands = groupsOf(rd.deep, W, 2);
            res.lines++;
            if (dump) (res.dbg = res.dbg || []).push({ r: [r0, r1], g: groups.map(g => g.map(v => Math.round(v / s * 10) / 10)), b: bands.map(g => g.map(v => Math.round(v / s * 10) / 10)) });
            if (!bands.length) continue;
            res.bands += bands.length;
            for (const f of judge(groups, bands, em, s, !rowish, rowish, 0.65)) res.bad.push([f[0], "line " + res.lines + ": " + f[1]]);
            for (const g of groups) if (bands.some(([da, db]) => g[0] >= da - 1.5 && g[1] <= db + 1.5)) res.covered++;
          }
        }
        res.tokens = String(c.highlight || "").split(/\s+/).map(nz).filter(Boolean).length;
        if (!res.bands && c.highlight) res.bad.push(["no gold band in the picture", ""]);
      } finally { body.remove(); }
      return res;
    },
  };
})();
