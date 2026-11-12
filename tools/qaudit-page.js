// The page half of tools/qaudit-render.py: run inside the APP's own page, with the owner's IFC PDF loaded the way a reader loads it.
// For one Fire Code question it asks the app's own code path for the clipping (V.locate + V.computeClip, or V.countyClip for the
// county booklet) and returns: what the clipping MARKS (the text under every gold mark), the text of the cited extent and of the
// cited page(s), the pointer / page lines the card prints, and (shot) the pictures: the card's own picture (buildIfcRef opened) and
// the whole page(s) painted with the same marks. Nothing of the book is kept in the repo: the pictures go to the audit's scratch folder.
(() => {
  let V = null, book = null, cdoc = null;
  async function boot() {
    if (!V) { V = await ifcViewer(); book = await ifcEnsureBook(); cdoc = await ifcCountyDoc(); }
    return !!book && !!cdoc;
  }
  const centre = (it) => it.x + it.w / 2;
  const itemsIn = (model, m) => {
    const y0 = (m.i0 != null ? m.i0 : m.y0) - 2, y1 = (m.i1 != null ? m.i1 : m.y1) + 2;
    return model.items.filter(it => it.t && it.y >= y0 && it.y <= y1 && centre(it) >= m.x0 - 1 && centre(it) <= m.x1 + 1);
  };
  const bodyText = (model) => model.items.filter(it => it.t && it.y >= 36 && it.y <= 735).map(it => it.s).join(' ');
  const find = (id) => QUESTIONS.find(x => x.ifc && x.ifc.id === id);
  async function getClip(f) {
    const c = f.citation, county = c.source === 'amendment';
    const doc = county ? cdoc : book.doc, opts = county ? ifcCountyOpts : book.opts;
    if (county) {
      const clip = await V.countyClip(doc, c, ifcCountyOpts);
      return { county, doc, opts, loc: { ok: !!(clip && clip.ok), kind: 'county' }, clip };
    }
    const loc = V.locate(book.index, c);
    if (!loc.ok || loc.kind === 'pages') return { county, doc, opts, loc, clip: null };
    return { county, doc, opts, loc, clip: await V.computeClip(book.doc, book.index, loc, c, book.opts) };
  }
  window.__qa = {
    ids() { return QUESTIONS.filter(q => q.ifc).map(q => q.ifc.id); },
    async rec(id) {
      if (!(await boot())) return { id, nobook: true };
      const q = find(id), f = q.ifc, c = f.citation;
      const r = { id, unit: f.unit, type: f.type, kind: f.kind, source: c.source, stem: f.question, answer: f.answer, ans: f.options[f.answer], options: f.options,
                  section: c.section, nums: V.answerNumbers(f), ptr: ifcPointerLine(c), pageLine: ifcPageLine(c) };
      let g;
      try { g = await getClip(f); } catch (e) { r.error = 'clip: ' + String(e).slice(0, 160); return r; }
      r.locOk = !!g.loc.ok; r.locKind = g.loc.ok ? g.loc.kind : null;
      const clip = g.clip;
      r.clipOk = !!(clip && clip.ok && clip.segments && clip.segments.length);
      if (!r.clipOk) {
        r.pagesText = [];
        try { for (const p of V.wholePages(g.county ? null : book.index, c, 3)) { const m = await V.pageModel(g.doc, p, g.opts.fontBold, g.opts.cache); r.pagesText.push(bodyText(m)); } } catch (e) {}
        return r;
      }
      r.truncated = !!clip.truncated; r.pages = clip.pages.slice();
      r.whole = clip.segments.some(sg => sg.whole);
      r.clipText = clip.text || '';
      r.marks = [];
      const models = {};
      const model = async (p) => models[p] || (models[p] = await V.pageModel(g.doc, p, g.opts.fontBold, g.opts.cache));
      for (const m of clip.marks || []) {
        const mm = await model(m.page); const its = itemsIn(mm, m);
        r.marks.push({ kind: m.kind, page: m.page, x0: Math.round(m.x0), x1: Math.round(m.x1), y: Math.round(((m.i0 != null ? m.i0 : m.y0) + (m.i1 != null ? m.i1 : m.y1)) / 2),
                       text: m.kind === 'cite' && m.text ? m.text : its.map(it => it.s).join(' ') });
      }
      r.citedText = '';
      for (const sg of clip.cited || clip.segments) {
        if (sg.whole) continue;
        const mm = await model(sg.page);
        r.citedText += ' ' + mm.items.filter(it => it.t && it.y >= sg.y0 && it.y <= sg.y1 && centre(it) >= sg.x0 && centre(it) <= sg.x1).map(it => it.s).join(' ');
      }
      r.pagesText = [];
      for (const p of clip.pages) r.pagesText.push(bodyText(await model(p)));
      return r;
    },
    // the card's own picture: buildIfcRef opened, drawn by the app (framing, the county column fit, everything), left in the page for an element screenshot
    async card(id) {
      if (!(await boot())) return { id, nobook: true };
      const item = find(id);
      ifcNodeCache.clear();
      let host = document.getElementById('qa-host');
      if (!host) {
        host = document.createElement('div'); host.id = 'qa-host';
        const st = document.getElementById('stage') || document.body;
        host.style.cssText = 'position:absolute;left:0;top:0;width:100%;z-index:9999;background:var(--bg,#0a0a0a);padding:0';
        document.body.appendChild(host);
      }
      host.replaceChildren();
      const wrap = document.createElement('div'); wrap.className = 'qpanel'; wrap.style.cssText = 'padding:8px 20px';
      ifcCodeOpenSet(true);                                   // the reader's own "remember it open": every box opens by itself, as for a reader who has opened one
      const ref = buildIfcRef(item); wrap.appendChild(ref); host.appendChild(wrap);
      const det = ref.querySelector('details');
      for (let k = 0; k < 40 && det && !det.open; k++) await new Promise(r => setTimeout(r, 50));
      const t0 = performance.now();
      while (performance.now() - t0 < 60000) {
        if (ref.querySelector('.ifc-clips canvas') && !ref.querySelector('.ifc-busy')) break;
        if (ref.querySelector('.ifc-note, .ifc-locked, .ifc-county-text')) break;
        await new Promise(r => setTimeout(r, 60));
      }
      for (let k = 0; k < 80 && det && (det.style.height || det._slideRaf); k++) await new Promise(r => setTimeout(r, 50));
      await new Promise(r => setTimeout(r, 250));
      return { id, ok: !!ref.querySelector('.ifc-clips canvas'), text: !!ref.querySelector('.ifc-county-text'), note: (ref.querySelector('.ifc-note, .ifc-locked') || {}).textContent || null,
               foot: (ref.querySelector('.ifc-foot') || {}).textContent || '', ptr: (ref.querySelector('.ifc-ptr') || {}).textContent || '', pageLine: (ref.querySelector('.ifc-pages') || {}).textContent || '' };
    },
    // the whole page(s) the viewer's "Show the whole page" paints, as data URLs (the licence footer painted over: a copy of the book must not be kept in a picture)
    async pages(id, scale) {
      if (!(await boot())) return { id, nobook: true };
      const f = find(id).ifc; let g;
      try { g = await getClip(f); } catch (e) { return { id, err: String(e).slice(0, 160) }; }
      const box = document.createElement('div'); box.style.cssText = 'position:absolute;left:-9999px;top:0'; document.body.appendChild(box);
      const imgs = [];
      try {
        let pgs;
        if (g.county) pgs = g.clip && g.clip.pages && g.clip.pages.length ? g.clip.pages : [f.citation.pdfPage];
        else pgs = g.clip && g.clip.pages && g.clip.pages.length ? g.clip.pages : V.wholePages(book.index, f.citation, 2);
        await V.paintPages(g.doc, pgs, box, { scale, ...g.opts, clip: g.clip && g.clip.ok ? g.clip : null });
        for (const cv of box.querySelectorAll('canvas')) {
          if (!g.county) { const x = cv.getContext('2d'); x.fillStyle = '#ffffff'; x.fillRect(0, cv.height - 52 * scale, cv.width, 52 * scale); }
          imgs.push({ w: cv.width, h: cv.height, url: cv.toDataURL('image/jpeg', 0.6) });
        }
        return { id, imgs, pages: pgs };
      } catch (e) { return { id, err: String(e).slice(0, 200) }; }
      finally { box.remove(); }
    },
  };
})();
