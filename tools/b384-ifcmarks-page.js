// The page half of tools/check-b384-ifcmarks.py, run inside the APP's own page with the owner's IFC PDF loaded the way a reader loads it (Load my IFC
// PDF). For one Fire Code question it asks the app's own code path for the clipping (V.locate + V.computeClip with the citation the question
// carries, patches and all) and hands back what the clipping MARKS: the text under every gold mark (the heading, the deciding sentence / list item
// found by `find`, a table row, an exception), the text of the clipping and of the cited pages, and the keyed answer. The verdict is the gate's.
// It also paints the two views (the code box and the whole page) and reads, off the pixels, whether the gold covers a given word of the page.
(() => {
  let V = null, book = null;
  async function boot() { if (!V) { V = await ifcViewer(); book = await ifcEnsureBook(); } return !!book; }
  const centre = (it) => it.x + it.w / 2;
  const itemsIn = (model, m) => {
    // the printed runs under a mark (its rectangle, in pdf points)
    const y0 = (m.i0 != null ? m.i0 : m.y0) - 2, y1 = (m.i1 != null ? m.i1 : m.y1) + 2;
    return model.items.filter(it => it.t && it.y >= y0 && it.y <= y1 && centre(it) >= m.x0 - 1 && centre(it) <= m.x1 + 1);
  };
  const bodyText = (model) => model.items.filter(it => it.t && it.y >= 36 && it.y <= 735).map(it => it.s).join(' ');
  window.__im = {
    ids() { return QUESTIONS.filter(q => q.ifc && q.ifc.type === 'content' && q.ifc.citation.source === 'ifc').map(q => q.ifc.id); },
    async rec(id) {
      if (!(await boot())) return { id, nobook: true };
      const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), f = q.ifc, c = f.citation;
      const r = { id, unit: f.unit, kind: f.kind, stem: f.question, answer: f.answer, ans: f.options[f.answer], options: f.options, section: c.section,
                  keys: Object.keys(c).filter(k => !['source', 'section', 'heading', 'label', 'pdfPage', 'printedPage', 'pdfPageEnd', 'printedPageEnd'].includes(k)),
                  find: c.find || null, row: c.row || null, pdfPage: c.pdfPage, pdfPageEnd: c.pdfPageEnd || null, nums: V.answerNumbers(f) };
      const loc = V.locate(book.index, c);
      r.locOk = !!loc.ok; r.locKind = loc.ok ? loc.kind : null;
      if (!loc.ok || loc.kind === 'pages') {
        r.pagesText = [];
        for (const p of V.wholePages(book.index, c, 3)) { const m = await V.pageModel(book.doc, p, book.opts.fontBold, book.opts.cache); r.pagesText.push(bodyText(m)); }
        return r;
      }
      const clip = await V.computeClip(book.doc, book.index, loc, c, book.opts);
      r.clipOk = !!(clip && clip.ok && clip.segments.length);
      if (!r.clipOk) return r;
      r.truncated = !!clip.truncated; r.pages = clip.pages.slice();
      r.segs = clip.segments.map(sg => ({ page: sg.page, y0: sg.y0, y1: sg.y1, whole: !!sg.whole, omit: !!sg.omit }));      // (384.72) the pieces of the cut
      r.whole = clip.segments.some(sg => sg.whole);
      r.clipText = clip.text || '';
      r.marks = [];
      const models = {};
      for (const m of clip.marks || []) {
        if (!models[m.page]) models[m.page] = await V.pageModel(book.doc, m.page, book.opts.fontBold, book.opts.cache);
        const its = itemsIn(models[m.page], m);
        r.marks.push({ kind: m.kind, page: m.page, x0: Math.round(m.x0), x1: Math.round(m.x1), y: Math.round(((m.i0 != null ? m.i0 : m.y0) + (m.i1 != null ? m.i1 : m.y1)) / 2),
                       text: m.kind === 'cite' && m.text ? m.text : its.map(it => it.s).join(' ') });
      }
      // the text of the whole cited extent (the whole-page view washes it) and of the page(s) the clipping runs over
      r.citedText = '';
      for (const sg of clip.cited || clip.segments) {
        if (sg.whole) continue;
        if (!models[sg.page]) models[sg.page] = await V.pageModel(book.doc, sg.page, book.opts.fontBold, book.opts.cache);
        r.citedText += ' ' + models[sg.page].items.filter(it => it.t && it.y >= sg.y0 && it.y <= sg.y1 && centre(it) >= sg.x0 && centre(it) <= sg.x1).map(it => it.s).join(' ');
      }
      r.pagesText = [];
      for (const p of clip.pages) { if (!models[p]) models[p] = await V.pageModel(book.doc, p, book.opts.fontBold, book.opts.cache); r.pagesText.push(bodyText(models[p])); }
      return r;
    },
    // ---- a picture of one view as the app paints it (the licence footer at the foot of a whole page is painted over: a copy of the book must not be kept in a picture)
    async shot(id, view, scale) {
      if (!(await boot())) return { id, nobook: true };
      const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), c = q.ifc.citation;
      const loc = V.locate(book.index, c);
      const clip = await V.computeClip(book.doc, book.index, loc, c, book.opts);
      const box = document.createElement('div'); document.body.appendChild(box);
      const imgs = [];
      try {
        if (view === 'page') await V.paintPages(book.doc, clip.pages, box, { scale, ...book.opts, clip });
        else await V.paint(book.doc, clip, box, { scale });
        for (const cv of box.querySelectorAll('canvas')) {
          if (view === 'page') { const g = cv.getContext('2d'); g.fillStyle = '#ffffff'; g.fillRect(0, cv.height - 52 * scale, cv.width, 52 * scale); }
          imgs.push(cv.toDataURL('image/png'));
        }
      } catch (e) { return { id, err: String(e).slice(0, 200) }; }
      box.remove();
      return { id, imgs };
    },
    // ---- pixels: the gold of the two views against the print. `words` = [{ re, label }]: every printed run of the clipping whose text matches `re` is located in the
    // picture - the whole book page (V.paintPages) or the code box (V.paint: one sheet of the clipping's pieces, laid as paint() lays them) - and the share of the
    // run's box that is the strong gold is read off the pixels (the box's pixels that are not print). The mark that decides a question must cover the run.
    async pixels(id, words, scale, view) {
      if (!(await boot())) return { id, nobook: true };
      const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), f = q.ifc, c = f.citation;
      const loc = V.locate(book.index, c);
      const clip = await V.computeClip(book.doc, book.index, loc, c, book.opts);
      const box = document.createElement('div'); document.body.appendChild(box);
      const out = { id, view, words: [], pages: clip.pages.slice() };
      try {
        const deep = (R, G, B) => R >= 235 && G < 232 && B < 95;
        let frames;                                            // [{ cv, page, s, ox, oy, seg }]: how a point of a page lies in a picture
        if (view === 'page') {
          await V.paintPages(book.doc, clip.pages, box, { scale, ...book.opts, clip });
          const cvs = [...box.querySelectorAll('canvas')];
          frames = [];
          for (let k = 0; k < clip.pages.length; k++) { const model = await V.pageModel(book.doc, clip.pages[k], book.opts.fontBold, book.opts.cache); if (cvs[k]) frames.push({ cv: cvs[k], model, s: cvs[k].width / model.view[2], ox: 0, oy: model.view[3], seg: null }); }
        } else {
          await V.paint(book.doc, clip, box, { scale });
          const cv0 = box.querySelector('canvas'), segs = clip.segments;
          const sheet = segs.length === 1 ? { pieces: [{ i: 0, dx: 0, top: segs[0].y1, bot: segs[0].y0, gap: 0 }] }
            : (clip.sheet || { pieces: segs.map((sg, i) => ({ i, dx: 0, top: sg.y1, bot: sg.y0, gap: i ? 4 : 0 })) });
          let X0 = Infinity, X1 = -Infinity;
          for (const pc of sheet.pieces) { X0 = Math.min(X0, segs[pc.i].x0 + pc.dx); X1 = Math.max(X1, segs[pc.i].x1 + pc.dx); }
          const sc = cv0.width / (X1 - X0);
          frames = []; let yy = 0;
          if (cv0._ifcParts && cv0._ifcParts.length === sheet.pieces.length) {
            // (384.71) the app says where each piece lies (the first and the last piece's outer edges are settled to a clean row, which moves every piece after it)
            for (let k = 0; k < sheet.pieces.length; k++) {
              const pt = cv0._ifcParts[k], seg = segs[sheet.pieces[k].i];
              frames.push({ cv: cv0, model: await V.pageModel(book.doc, seg.page, book.opts.fontBold, book.opts.cache), s: pt.s, ox: pt.ox, oy: pt.oy, seg, pc: { top: pt.oy - pt.row0 / pt.s, bot: pt.oy - pt.row1 / pt.s } });
            }
          } else for (const pc of sheet.pieces) {
            yy += Math.round((pc.gap || 0) * sc);
            const seg = segs[pc.i];
            frames.push({ cv: cv0, model: await V.pageModel(book.doc, seg.page, book.opts.fontBold, book.opts.cache), s: sc, ox: X0 - pc.dx, oy: pc.top + yy / sc, seg, pc });
            yy += Math.round((pc.top - pc.bot) * sc);
          }
        }
        out.frames = frames.length;
        for (const fr of frames) {
          const { cv, model, s, ox, oy, seg } = fr;
          const D = (fr.d = fr.d || cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data);
          for (const w of words) {
            const re = new RegExp(w.re, 'i');
            for (const it of model.items) {
              if (!it.t || it.y < 36 || it.y > 735) continue;
              if (seg && !(centre(it) >= seg.x0 && centre(it) <= seg.x1 && it.y >= fr.pc.bot - 1 && it.y <= fr.pc.top + 1)) continue;
              const mm = re.exec(it.s);
              if (!mm) continue;
              // the run's box: a proportional guess inside the run (good to a few points; the words wanted are short)
              const a = it.x + it.w * mm.index / it.s.length, b = it.x + it.w * (mm.index + mm[0].length) / it.s.length;
              const px0 = Math.max(0, Math.floor((a - ox) * s)), px1 = Math.min(cv.width - 1, Math.ceil((b - ox) * s)),
                    py0 = Math.max(0, Math.floor((oy - (it.y + (it.h < 7 ? 1 : 0.7) * it.h)) * s)), py1 = Math.min(cv.height - 1, Math.ceil((oy - (it.y - (it.h < 7 ? 0.1 : 0.2) * it.h)) * s));      // (a raised or lowered small figure - a fraction's "32" - is read over its own height)
              let gold = 0, paper = 0;
              for (let y = py0; y <= py1; y++) for (let x = px0; x <= px1; x++) {
                const i = (y * cv.width + x) * 4, R = D[i], G = D[i + 1], B = D[i + 2];
                if (R + G + B < 330) continue;                         // print
                paper++; if (deep(R, G, B)) gold++;
              }
              const rec = { page: model.p, text: it.s.slice(0, 60), hit: mm[0], gold, paper, share: paper ? gold / paper : 0, label: w.label, box: [px0, px1, py0, py1] };
              // (384.71) where the gold shape that holds this run lies, and where the print inside it lies, in picture pixels: the gold's box and the ink's box
              // (a table's rules and any pixel that is not print are left out of the ink), so a mark's room on every side can be read - ch22-014's stacked 1/32
              if (w.comp && gold) {
                let seed = -1;
                for (let y = py0; y <= py1 && seed < 0; y++) for (let x = px0; x <= px1; x++) { const i = (y * cv.width + x) * 4; if (deep(D[i], D[i + 1], D[i + 2])) { seed = y * cv.width + x; break; } }
                const Wd = cv.width, Ht = cv.height, seen = new Uint8Array(Wd * Ht), st = [seed];
                let gx0 = Infinity, gx1 = -1, gy0 = Infinity, gy1 = -1; seen[seed] = 1;
                while (st.length) {
                  const q = st.pop(), x = q % Wd, y = (q - x) / Wd;
                  const qi = q * 4;
                  if (deep(D[qi], D[qi + 1], D[qi + 2])) { if (x < gx0) gx0 = x; if (x > gx1) gx1 = x; if (y < gy0) gy0 = y; if (y > gy1) gy1 = y; }
                  for (const r of [q - 1, q + 1, q - Wd, q + Wd]) {
                    if (r < 0 || r >= Wd * Ht || seen[r]) continue;
                    const rx = r % Wd; if ((r === q - 1 && x === 0) || (r === q + 1 && x === Wd - 1) || Math.abs(rx - x) > 1) continue;
                    const i = r * 4; if (deep(D[i], D[i + 1], D[i + 2]) || D[i] + D[i + 1] + D[i + 2] < 330) { seen[r] = 1; st.push(r); }
                  }
                }
                // (the flood runs through the print inside the shape - black is part of it - and stops at the paper; the gold's box is its gold pixels only; a row or a column of ink
                // across most of the box is a table's rule and not print)
                let ix0 = Infinity, ix1 = -1, iy0 = Infinity, iy1 = -1;
                const gw = gx1 - gx0 + 1, gh = gy1 - gy0 + 1;
                const inkAt = (x, y) => { const i = (y * Wd + x) * 4; return D[i] + D[i + 1] + D[i + 2] < 330; };
                const rowInk = [], colInk = [];
                for (let y = gy0; y <= gy1; y++) { let n = 0; for (let x = gx0; x <= gx1; x++) if (inkAt(x, y)) n++; rowInk.push(n); }
                for (let x = gx0; x <= gx1; x++) { let n = 0; for (let y = gy0; y <= gy1; y++) if (inkAt(x, y)) n++; colInk.push(n); }
                for (let y = gy0; y <= gy1; y++) for (let x = gx0; x <= gx1; x++) {
                  if (!seen[y * Wd + x] || !inkAt(x, y) || rowInk[y - gy0] > 0.6 * gw || colInk[x - gx0] > 0.6 * gh) continue;
                  if (x < ix0) ix0 = x; if (x > ix1) ix1 = x; if (y < iy0) iy0 = y; if (y > iy1) iy1 = y;
                }
                rec.comp = { gx0, gx1, gy0, gy1, ix0, ix1, iy0, iy1, s, fs: it.h };
              }
              out.words.push(rec);
            }
          }
        }
        out.paintOk = true;
      } catch (e) { out.err = String(e).slice(0, 200); }
      box.remove();
      return out;
    },
  };
})();
