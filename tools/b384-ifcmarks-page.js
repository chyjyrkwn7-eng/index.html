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
    // ---- pixels: the gold of the two views against the print. For each wanted phrase (words as printed on the clipping's pages) the words are located in
    // the page's own text, and the pixels of that word's box are read in the picture: the share of the box's non-ink pixels that are the strong gold.
    async pixels(id, words, scale, view) {
      if (!(await boot())) return { id, nobook: true };
      const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), f = q.ifc, c = f.citation;
      const loc = V.locate(book.index, c);
      const clip = await V.computeClip(book.doc, book.index, loc, c, book.opts);
      const box = document.createElement('div'); document.body.appendChild(box);
      const out = { id, view, words: [], pages: clip.pages.slice() };
      try {
        if (view === 'page') await V.paintPages(book.doc, clip.pages, box, { scale, ...book.opts, clip });
        else await V.paint(book.doc, clip, box, { scale });
        const cvs = [...box.querySelectorAll('canvas')];
        out.canvases = cvs.length;
        // which canvas is which page: the whole-page view paints one per page; the code box one per segment (in the clip's order)
        const segPage = view === 'page' ? clip.pages : clip.segments.map(sg => sg.page);
        const deep = (R, G, B) => R >= 235 && G < 232 && B < 95;
        for (let k = 0; k < cvs.length && k < segPage.length; k++) {
          const p = segPage[k], model = await V.pageModel(book.doc, p, book.opts.fontBold, book.opts.cache), cv = cvs[k];
          const seg = view === 'page' ? null : clip.segments[k];
          const s = view === 'page' ? cv.width / model.view[2] : cv.width / (seg.x1 - seg.x0);
          const x0p = seg ? seg.x0 : 0, ytop = seg ? seg.y1 : model.view[3];
          const g = cv.getContext('2d'), img = g.getImageData(0, 0, cv.width, cv.height), D = img.data;
          for (const w of words) {
            const re = w.re ? new RegExp(w.re, 'i') : null;
            for (const it of model.items) {
              if (!it.t || it.y < 36 || it.y > 735) continue;
              if (seg && !(centre(it) >= seg.x0 && centre(it) <= seg.x1 && it.y >= seg.y0 && it.y <= seg.y1)) continue;
              const mm = re ? re.exec(it.s) : null;
              if (!mm) continue;
              // the word's box: a proportional guess inside the run (good to a few points; numbers are short)
              const a = it.x + it.w * mm.index / it.s.length, b = it.x + it.w * (mm.index + mm[0].length) / it.s.length;
              const px0 = Math.max(0, Math.floor((a - x0p) * s)), px1 = Math.min(cv.width - 1, Math.ceil((b - x0p) * s)),
                    py0 = Math.max(0, Math.floor((ytop - (it.y + 0.7 * it.h)) * s)), py1 = Math.min(cv.height - 1, Math.ceil((ytop - (it.y - 0.2 * it.h)) * s));
              let gold = 0, paper = 0;
              for (let y = py0; y <= py1; y++) for (let x = px0; x <= px1; x++) {
                const i = (y * cv.width + x) * 4, R = D[i], G = D[i + 1], B = D[i + 2];
                if (R + G + B < 330) continue;                         // ink
                paper++; if (deep(R, G, B)) gold++;
              }
              out.words.push({ page: p, text: it.s.slice(0, 60), hit: mm[0], gold, paper, share: paper ? gold / paper : 0, label: w.label });
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
