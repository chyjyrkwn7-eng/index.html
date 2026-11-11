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
  const nz = s => String(s).toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9]+/g, "");
  const deepPx = (R, G, B) => R >= 235 && G < 232 && B < 95;                    // the wash is (255,245,160), the gold over it (255,215,25)
  const inkPx = (R, G, B) => R + G + B < 330;
  const GAP = 0.22;                                                              // em: a wider gap in the print than this is a space
  let V = null, doc = null;
  async function boot() { if (!V) { V = await ifcViewer(); doc = await ifcCountyDoc(); } }
  function groupsOf(col, W, gap) {
    const out = []; let a = -1, last = -1;
    for (let x = 0; x < W; x++) { if (!col[x]) continue; if (a < 0) { a = x; last = x; } else if (x - last > gap) { out.push([a, last]); a = x; last = x; } else last = x; }
    if (a >= 0) out.push([a, last]);
    return out;
  }
  // one text line's reading: its words (ink groups) and its bands (deep runs), over the rows r0..r1 of an image
  function readLine(img, W, r0, r1, em, wantInk) {
    const D = img.data, ink = new Uint8Array(W), deep = new Uint8Array(W);
    for (let y = Math.max(0, r0); y < Math.min(img.height, r1); y++) for (let x = 0, i = y * W * 4; x < W; x++, i += 4) {
      const R = D[i], G = D[i + 1], B = D[i + 2];
      if (wantInk === img && inkPx(R, G, B)) ink[x] = 1;
      if (deepPx(R, G, B)) deep[x] = 1;
    }
    return { ink, deep };
  }
  // the verdict on one line: words [a,b], bands [a,b] (px) -> violations
  function judge(words, bands, em, s, tight) {
    const bad = [], tol = Math.max(1.2, 0.3 * s), room = 0.34 * em;
    for (const [da, db] of bands) {
      const cov = words.filter(([a, b]) => b >= da - tol && a <= db + tol);
      const inside = cov.filter(([a, b]) => a >= da - tol && b <= db + tol);
      for (const w of cov) if (!inside.includes(w)) bad.push(["a word is cut by the band's edge", (w[0] < da - tol ? "left " + ((da - w[0]) / s).toFixed(1) : "right " + ((w[1] - db) / s).toFixed(1)) + "pt of a word outside"]);
      if (!inside.length) { bad.push(["a band holds no word", ((db - da) / s).toFixed(1) + "pt wide"]); continue; }
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
    async page(id, S) {
      await boot();
      const q = QUESTIONS.find(q => q.ifc && q.ifc.id === id), c = q.ifc.citation;
      const clip = await V.countyClip(doc, c, ifcCountyOpts);
      const res = { id, view: "page", bad: [], lines: 0, bands: 0, unverifiable: 0, located: null, expected: 0, missing: [], extra: [] };
      if (!clip || !clip.ok) { res.noclip = true; return res; }
      const box = document.createElement("div"); document.body.appendChild(box);
      try {
        await V.paintPages(doc, clip.pages, box, { scale: S, ...ifcCountyOpts, clip });
        const cvs = [...box.querySelectorAll("canvas.ifc-page")], p0 = c.pdfPage, p1 = c.pdfPageEnd || c.pdfPage;
        const stream = [], rowish = / \| | › /.test(String(c.highlight || ""));
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
              for (const f of judge(groups, bands, em, s, !(rowish || ln.tbl))) res.bad.push([f[0], "p" + p + " line " + li + ": " + f[1]]);
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
          const find = (seq) => { const o = []; for (let i = 0; i + seq.length <= T.length; i++) { let ok = true; for (let j = 0; j < seq.length && ok; j++) ok = T[i + j].n === seq[j]; if (ok) o.push([i, i + seq.length - 1]); } return o; };
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
              if (!e.aligned) continue;
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
    // ---- the card's picture
    async card(id) {
      await boot();
      const q = QUESTIONS.find(q => q.ifc && q.ifc.id === id), c = q.ifc.citation;
      const res = { id, view: "card", bad: [], lines: 0, bands: 0, covered: 0, tokens: 0 };
      const body = document.createElement("div"); body.style.cssText = "width:392px;position:absolute;left:0;top:0";
      document.body.appendChild(body);
      try {
        await ifcFillCode({ ifc: { citation: c } }, body, document.createElement("div"));
        const cvs = [...body.querySelectorAll("canvas")];
        if (!cvs.length) { res.notpicture = true; return res; }
        const rowish = / \| | › /.test(String(c.highlight || ""));
        const s = Math.min(window.devicePixelRatio || 1, 2) * 1.7;
        for (const cv of cvs) {
          const W = cv.width, H = cv.height, img = cv.getContext("2d").getImageData(0, 0, W, H), D = img.data;
          // the text lines: rows with print, split where a row has none
          const rowInk = new Uint8Array(H);
          for (let y = 0; y < H; y++) for (let x = 0, i = y * W * 4; x < W; x++, i += 4) if (inkPx(D[i], D[i + 1], D[i + 2])) { rowInk[y] = 1; break; }
          const lines = []; let a = -1;
          for (let y = 0; y <= H; y++) { if (y < H && rowInk[y]) { if (a < 0) a = y; } else if (a >= 0) { if (y - a >= 0.3 * 11 * s) lines.push([a, y]); a = -1; } }
          for (const [r0, r1] of lines) {
            const em = 11 * s, rd = readLine(img, W, r0, r1, em, img);
            const ink = new Uint8Array(W);
            for (let y = r0; y < r1; y++) for (let x = 0, i = y * W * 4; x < W; x++, i += 4) if (inkPx(D[i], D[i + 1], D[i + 2])) ink[x] = 1;
            const groups = groupsOf(ink, W, GAP * em), bands = groupsOf(rd.deep, W, 2);
            res.lines++;
            if (!bands.length) continue;
            res.bands += bands.length;
            for (const f of judge(groups, bands, em, s, !rowish)) res.bad.push([f[0], "line " + res.lines + ": " + f[1]]);
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
