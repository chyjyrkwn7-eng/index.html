/* The measuring half of tools/check-centering.py (build 384), injected into the page.
   It finds every "content inside a shape" element on the screen (a pill, button, chip, tag, badge, round icon
   button, segmented item, medal or number disc), says where its shape is, what its content is and whether the
   layout means the content to be centred; check-centering.py then hides the content (CZ.hide), screenshots the
   page as drawn and with the content gone, and the difference is the ink. Nothing here changes layout. */
(() => {
  if (window.__cz) return;
  const CZ = window.__cz = { cands: [], saved: new Map(), sig: new Map() };
  CZ.reset = () => { CZ.sig = new Map(); document.querySelectorAll('[data-czdone]').forEach(n => n.removeAttribute('data-czdone')); };
  const px = v => parseFloat(v) || 0;
  const alphaOf = c => {
    if (!c || c === 'transparent') return 0;
    const m = c.match(/[\d.]+/g) || [];
    if (/^rgba|\/ /.test(c)) return +m[m.length - 1];
    if (/^color\(/.test(c)) return m.length > 3 ? +m[3] : 1;
    return m.length >= 3 ? 1 : 0;
  };
  const rimOf = cs => ['Top', 'Right', 'Bottom', 'Left'].every(s => px(cs['border' + s + 'Width']) > 0 && alphaOf(cs['border' + s + 'Color']) > .03);
  const paints = cs => !/text/.test(cs.backgroundClip || '') && !/text/.test(cs.webkitBackgroundClip || '') && (alphaOf(cs.backgroundColor) > .03 || (cs.backgroundImage && cs.backgroundImage !== 'none') || rimOf(cs) ||
    ((cs.backdropFilter || cs.webkitBackdropFilter || 'none') !== 'none'));
  const SKIP_TAGS = /^(INPUT|TEXTAREA|SELECT|OPTION|IMG|CANVAS|VIDEO|IFRAME|svg|SCRIPT|STYLE|BR|HR|LABEL)$/;
  /* pictures, not glyphs: a character, a planet, a rank's emblem, a badge's coin. Their box stands in for their ink
     (an illustration is not symmetric by design). Read by colour count, not by name. */
  const isArt = n => {
    if (/^(IMG|CANVAS|VIDEO)$/.test(n.tagName)) return true;
    if (n.tagName !== 'svg') return false;
    if (n.querySelector('image, foreignObject')) return true;
    const cols = new Set();
    for (const s of n.querySelectorAll('path, circle, ellipse, rect, polygon, polyline, line, text, use')) {
      const c = getComputedStyle(s);
      for (const v of [c.fill, c.stroke]) {
        if (!v || v === 'none') continue;
        if (/url\(/.test(v)) { cols.add('grad:' + v); continue; }
        if (alphaOf(v) > .05) cols.add(v.replace(/\s+/g, ''));
      }
      if (cols.size > 3) return true;
    }
    return cols.size > 3;
  };
  /* a pseudo-element that is a glyph: words, a masked or pictured icon, or a chevron drawn with two borders - not a
     painted knob (a switch's) or a glow */
  const pseudoIsIcon = (ps, kr) => /^["']\s*[^"'\s]/.test(ps.content) || (ps.webkitMaskImage && ps.webkitMaskImage !== 'none') || (ps.maskImage && ps.maskImage !== 'none') ||
    /url\(/.test(ps.backgroundImage) || /url\(/.test(ps.content) ||
    (['Top', 'Right', 'Bottom', 'Left'].filter(s => px(ps['border' + s + 'Width']) > 0 && alphaOf(ps['border' + s + 'Color']) > .1).length === 2 && alphaOf(ps.backgroundColor) < .05 && px(ps.width) < .5 * kr.width);
  const lookOf = el => [el, ...el.querySelectorAll('*')].map(n => { const r = n.getBoundingClientRect(); const cs = getComputedStyle(n); return cs.display === 'none' ? '-' : [Math.round(r.left * 4), Math.round(r.top * 4), Math.round(r.width * 4), Math.round(r.height * 4), cs.visibility, cs.opacity].join(','); }).join('|') + (el.textContent || '');
  /* what can be seen of a picture: its box, cut by whatever clips it on the way up to the candidate, and by the shape */
  const visibleBox = (d, el, S) => {
    const r = d.getBoundingClientRect(); let b = { l: r.left, t: r.top, r: r.right, b: r.bottom };
    for (let a = d.parentElement; a && a !== el.parentElement; a = a.parentElement) {
      const cs = getComputedStyle(a); if (!/hidden|clip/.test(cs.overflow) && (!cs.clipPath || cs.clipPath === 'none')) continue;
      const q = a.getBoundingClientRect(); b = { l: Math.max(b.l, q.left), t: Math.max(b.t, q.top), r: Math.min(b.r, q.right), b: Math.min(b.b, q.bottom) };
    }
    b = { l: Math.max(b.l, S.l), t: Math.max(b.t, S.t), r: Math.min(b.r, S.r), b: Math.min(b.b, S.b) };
    return b.r - b.l > 1 && b.b - b.t > 1 ? b : null;
  };
  const effOpacity =el => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
  const R = r => ({ l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height });
  const canvas = document.createElement('canvas').getContext('2d');
  /* the font's ascent (canvas) and its capital height - by CSS's own 1cap on a probe in the words' own element (the
     canvas rounds glyph extents to whole pixels) */
  const capCache = new Map();
  const fontMetrics = (cs, host) => {
    canvas.font = [cs.fontStyle, cs.fontWeight, cs.fontSize, cs.fontFamily].join(' ');
    const m = canvas.measureText('Hxgy');
    const key = canvas.font;
    if (!capCache.has(key)) {
      const pr = document.createElement('span'); pr.style.cssText = 'position:absolute;visibility:hidden;display:block;width:0;height:1cap;padding:0;border:0;margin:0';
      host.appendChild(pr); const ch = pr.getBoundingClientRect().height; pr.remove();
      /* a font without a capital height in its tables (some system fonts) gives 0: the canvas's H is the fallback */
      capCache.set(key, ch > 1 ? ch : canvas.measureText('H').actualBoundingBoxAscent);
    }
    return { asc: m.fontBoundingBoxAscent, cap: capCache.get(key) };
  };
  /* where the shape is: the element's own paint (inside a visible rim), or a pseudo-element that draws it */
  function shapeOf(el, cs, r) {
    if (paints(cs)) {
      const s = R(r); let inset = { t: 0, r: 0, b: 0, l: 0 };
      if (rimOf(cs) || /padding-box|content-box/.test(cs.backgroundClip))
        inset = { t: px(cs.borderTopWidth), r: px(cs.borderRightWidth), b: px(cs.borderBottomWidth), l: px(cs.borderLeftWidth) };
      if (/content-box/.test(cs.backgroundClip)) { inset.t += px(cs.paddingTop); inset.r += px(cs.paddingRight); inset.b += px(cs.paddingBottom); inset.l += px(cs.paddingLeft); }
      return { kind: 'own', l: s.l + inset.l, t: s.t + inset.t, r: s.r - inset.r, b: s.b - inset.b };
    }
    for (const p of ['::before', '::after']) {
      const ps = getComputedStyle(el, p);
      if (ps.content === 'none' || ps.content === 'normal' || ps.display === 'none' || !/absolute|fixed/.test(ps.position) || !paints(ps)) continue;
      if (+ps.opacity < .3 || ps.visibility === 'hidden') continue;
      const w = px(ps.width) + px(ps.paddingLeft) + px(ps.paddingRight) + px(ps.borderLeftWidth) + px(ps.borderRightWidth);
      const h = px(ps.height) + px(ps.paddingTop) + px(ps.paddingBottom) + px(ps.borderTopWidth) + px(ps.borderBottomWidth);
      if (w < .8 * r.width || h < .8 * r.height || ps.transform !== 'none') continue;
      const pl = r.left + px(cs.borderLeftWidth), pt = r.top + px(cs.borderTopWidth);
      const pw = r.width - px(cs.borderLeftWidth) - px(cs.borderRightWidth), ph = r.height - px(cs.borderTopWidth) - px(cs.borderBottomWidth);
      const l = ps.left !== 'auto' ? pl + px(ps.left) : pl + pw - px(ps.right) - w;
      const t = ps.top !== 'auto' ? pt + px(ps.top) : pt + ph - px(ps.bottom) - h;
      const ins = rimOf(ps) ? { t: px(ps.borderTopWidth), r: px(ps.borderRightWidth), b: px(ps.borderBottomWidth), l: px(ps.borderLeftWidth) } : { t: 0, r: 0, b: 0, l: 0 };
      return { kind: p, l: l + ins.l, t: t + ins.t, r: l + w - ins.r, b: t + h - ins.b };
    }
    return null;
  }
  /* a shape that paints nothing of its own but is still a shape the content must sit in the middle of:
     a tab in the tab bar (the slider comes to it), a segment of a segmented control */
  const VIRTUAL = '.bottomtab';
  /* drawn ornaments that look like a shape with something in it but are pictures: the badge case's latches */
  /* and the planets on Home's and Welcome's orbits (pictures of galaxies, turning as they go round) */
  /* elements another piece of work owns right now: still measured and listed under "owned by other work", but not
     failed unless --strict. Add { 'selector': 'what owns it' } while a session redoes them; empty it when that lands.
     (Build 384: the Fire Code code pictures' IFC / AMENDMENTS / HINT tags, Show the code and Enlarge were listed here
     while another session redid them; that landed (c72a33a) and all pass but the tags on an iPad - left to that work.) */
  const OWNED = { '.ifc-ref .ifc-tag': 'the Fire Code code pictures\' tag pills (their own session: c72a33a centred them; AMENDMENTS on an iPad still measures off - left to them)' };
  const ownedBy = el => { for (const k in OWNED) if (el.matches(k)) return OWNED[k]; return ''; };
  /* (384 r4) the badge case's slots: a picture (a badge's coin with its glow and contact shadow, or its empty recess lit from the
     top left with a lip) whose ink is not its shape - the colour count passes a grey recess as an "icon" and measured its
     shadow. Where the SHAPE sits is asserted off the outline itself (check-behaviour check_b320c_case / check_b321d_badges:
     every one of the units' badges within .5px of its slot's middle, front and back). */
  /* (384 r4) Customize's banner and effect tiles are scenes (pictures: their ink is the art's), and the theme tile that is on wears a
     tick on its ring like a character's - a badge on the picture, not part of it */
  const NOT_A_CONTROL = '.nova-case-latch, .cosmic-hero .cosmic-icon-badge, .cosmic-welcome .cosmic-icon-badge, .badge-tile-art, .banner-opt-art, .hfx-opt-art, .hfx-opt-art .hfx-stage, .screen-customize .swatch.on, .screen-customize .swatch-cell';
  /* a character (Customize's, the tab's, a board's, the hero's): drawn on purpose off-symmetric, and placed per character */
  const CHARACTER = 'svg.avatarchar-svg, .char-live img, .char-live svg, [class*=avatar] img, [class*=char-flip] img, [class*=char-flip] svg';
  const nameOf = el => {
    const c = String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').trim().split(/\s+/).filter(x => x && !/^(is-|has-)/.test(x)).slice(0, 2).join('.');
    return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (c ? '.' + c : '');
  };
  const pathOf = el => { const out = []; for (let e = el.parentElement; e && e !== document.body && out.length < 3; e = e.parentElement) { if (e.id) { out.unshift('#' + e.id); break; } const c = String(e.className || '').trim().split(/\s+/)[0]; if (c && typeof e.className === 'string') out.unshift('.' + c); } return out.join(' '); };
  const textAlignCentre = cs => /center/.test(cs.textAlign);
  const cssCentre = (el, cs) => {
    const d = cs.display, row = !/column/.test(cs.flexDirection);
    if (/flex/.test(d)) return { h: row ? /center|space-around|space-evenly/.test(cs.justifyContent) : /center/.test(cs.alignItems),
                                  v: row ? /center/.test(cs.alignItems) : /center|space-around|space-evenly/.test(cs.justifyContent) };
    if (/grid/.test(d)) return { h: /center/.test(cs.justifyItems) || /center/.test(cs.justifyContent), v: /center/.test(cs.alignItems) || /center/.test(cs.alignContent) };
    return { h: textAlignCentre(cs), v: false };
  };
  CZ.collect = (opts) => {
    opts = opts || {}; const why = CZ.why = [];
    document.querySelectorAll('[data-czid]').forEach(n => n.removeAttribute('data-czid'));
    const pe = document.createElement('style'); pe.id = 'cz-pe'; pe.textContent = '*{pointer-events:auto!important}'; document.head.appendChild(pe);
    const VW = innerWidth, VH = innerHeight;
    const out = []; CZ.cands = [];
    const all = [...document.querySelectorAll('body *')];
    const shapes = new Map();
    for (const el of all) {
      if (SKIP_TAGS.test(el.tagName) || (el.closest('svg'))) continue;
      if (el.closest('#__statusbar, [data-czskip]') || el.matches(NOT_A_CONTROL)) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 12 || r.height < 12 || r.width > 640 || r.height > 170) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      let S = shapeOf(el, cs, r);
      if (!S && el.matches(VIRTUAL)) S = Object.assign({ kind: 'virtual' }, { l: r.left, t: r.top, r: r.right, b: r.bottom });
      if (!S) continue;
      if (S.r - S.l < 10 || S.b - S.t < 10) continue;
      shapes.set(el, { S, r, cs });
    }
    let n = 0;
    for (const [el, { S, r, cs }] of shapes) {
      if (el.dataset.czdone && !opts.again) continue;
      /* one shape inside another the same size is the same shape (keep the outer) */
      let dup = false;
      for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
        const o = shapes.get(a); if (!o) continue;
        if ((S.r - S.l) >= .9 * (o.S.r - o.S.l) && (S.b - S.t) >= .9 * (o.S.b - o.S.t)) { dup = true; } break;
      }
      if (dup) { why.push(['dup', nameOf(el)]); continue; }
      const W = S.r - S.l, H = S.b - S.t;
      /* fully on screen */
      if (S.l < -0.5 || S.t < -0.5 || S.r > VW + .5 || S.b > VH + .5) { why.push(['offscreen', nameOf(el)]); continue; }
      if (effOpacity(el) < .6) { why.push(['opacity', nameOf(el)]); continue; }
      /* turned (not just moved or scaled) by its own transform or an ancestor's: its box is not its shape */
      let turned = false;
      for (let a = el; a && a !== document.body && !turned; a = a.parentElement) { const tr = getComputedStyle(a).transform; if (!tr || tr === 'none') continue;
        const m = tr.match(/matrix(3d)?\(([^)]+)\)/); if (!m) { turned = true; break; } const v = m[2].split(',').map(Number);
        if (m[1] ? (Math.abs(v[1]) > .001 || Math.abs(v[4]) > .001) : (Math.abs(v[1]) > .001 || Math.abs(v[2]) > .001)) turned = true; }
      if (turned) { why.push(['turned', nameOf(el)]); continue; }
      /* the pieces inside: decorations (a corner badge, a count, a "new" dot, an arrow placed in the padding - placed
         away from the middle on purpose), layers of the shape itself (as big as it), ornaments (painted bits with
         nothing in them: a glow, a latch), pictures (art: their box stands in for their ink), icons and words */
      const deco = new Set(), shapeKids = new Set(), orn = new Set(), art = [], icons = [], pics = [], parts = [];
      const desc = [...el.querySelectorAll('*')].filter(d => d.tagName === 'svg' || !d.closest('svg'));
      if (desc.length > 80) { why.push(['big', nameOf(el)]); continue; }
      /* a track that holds several controls (a tab bar, a segmented control) is not a pill: its controls are measured one by one */
      if (desc.filter(d => d.matches('button, a[href], [role=button], [role=tab], input:not([type=checkbox]):not(.nova-hsw)') && d.getBoundingClientRect().width > 0).length >= 2) { why.push(['track', nameOf(el)]); continue; }
      const within = (set, d) => { for (const x of set) if (x.contains(d)) return true; return false; };
      if (desc.some(d => d.matches('button, a[href], [role=button], [role=switch], select') && shapes.has(d))) { why.push(['container', nameOf(el)]); continue; }
      const hasContent = d => {
        if ([...d.querySelectorAll('svg, img, canvas, video')].some(x => x.getBoundingClientRect().width > 3)) return true;
        const w = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let x; while ((x = w.nextNode())) if (x.nodeValue.trim()) return true;
        for (const k of [d, ...d.querySelectorAll('*')]) { const kc = getComputedStyle(k); if (/url\(/.test(kc.backgroundImage) || (kc.maskImage && kc.maskImage !== 'none') || (kc.webkitMaskImage && kc.webkitMaskImage !== 'none')) return true;
          for (const p of ['::before', '::after']) { const ps = getComputedStyle(k, p); if (ps.content !== 'none' && ps.content !== 'normal' && (/^["']\s*[^"'\s]/.test(ps.content) || (ps.maskImage && ps.maskImage !== 'none') || (ps.webkitMaskImage && ps.webkitMaskImage !== 'none') || /url\(/.test(ps.backgroundImage) || /url\(/.test(ps.content))) return true; } }
        return false; };
      let bad = false;
      for (const d of desc) {
        if (within(deco, d) || within(orn, d) || parts.some(x => x.contains(d))) continue;
        const dc = getComputedStyle(d); if (dc.display === 'none') continue;
        if (/^(INPUT|TEXTAREA|SELECT)$/.test(d.tagName)) { const ir = d.getBoundingClientRect(); if (+dc.opacity > .05 && dc.visibility !== 'hidden' && ir.width > 20 && ir.height > 14 && d.type !== 'checkbox') { bad = true; break; } continue; }
        const dr = d.getBoundingClientRect(); if (!dr.width || !dr.height) continue;
        const covers = dr.width >= .85 * W && dr.height >= .85 * H;
        if (/absolute|fixed/.test(dc.position)) {
          const cx = (dr.left + dr.right) / 2, cy = (dr.top + dr.bottom) / 2;
          const off = Math.abs(cx - (S.l + S.r) / 2) > .2 * W || Math.abs(cy - (S.t + S.b) / 2) > .2 * H;
          const out = dr.left < S.l - 1 || dr.right > S.r + 1 || dr.top < S.t - 1 || dr.bottom > S.b + 1;
          /* and a badge sticking out of the piece it sits on (a medal's crown) is that piece's decoration */
          const pr = d.parentElement !== el ? d.parentElement.getBoundingClientRect() : null;
          const outHost = pr && (dr.top < pr.top - .25 * dr.height || dr.bottom > pr.bottom + .25 * dr.height || dr.left < pr.left - .25 * dr.width || dr.right > pr.right + .25 * dr.width);
          if ((off || out || outHost) && !covers) { deco.add(d); continue; }
        }
        if (/^(svg|IMG|CANVAS|VIDEO)$/.test(d.tagName)) {
          if (+dc.opacity < .05 || dc.visibility === 'hidden') continue;
          if (d.matches(CHARACTER) || isArt(d)) art.push(d); else icons.push(d);
          continue;
        }
        if (covers) { shapeKids.add(d); continue; }
        if (!hasContent(d)) { if (paints(dc)) { orn.add(d); if (!/absolute|fixed/.test(dc.position)) parts.push(d); } continue; }
        if (/url\(/.test(dc.backgroundImage) || (dc.webkitMaskImage && dc.webkitMaskImage !== 'none')) pics.push(d);
      }
      if (bad) { why.push(['input', nameOf(el)]); continue; }
      /* the words: lines and baselines (words hidden for screen readers only, or sized away, are not ink) */
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let t; const runs = [];
      while ((t = tw.nextNode())) {
        const v = t.nodeValue; if (!v || !v.trim()) continue;
        const p = t.parentElement; if (!p || p.closest('svg')) continue;
        if (within(deco, p)) continue;
        const pc = getComputedStyle(p); if (pc.visibility === 'hidden' || +pc.opacity < .05 || px(pc.fontSize) < 3 || alphaOf(pc.webkitTextFillColor || pc.color) < .05) continue;
        let gone = false;
        for (let e = p; e && e !== el.parentElement; e = e.parentElement) { const ec = getComputedStyle(e); const er = e.getBoundingClientRect();
          if (+ec.opacity < .05 || (ec.clipPath && ec.clipPath !== 'none') || (ec.clip && ec.clip !== 'auto') || (/hidden|clip/.test(ec.overflow) && (er.width < 3 || er.height < 3))) { gone = true; break; } }
        if (gone) continue;
        const rg = document.createRange(); rg.selectNodeContents(t);
        const fm = fontMetrics(pc, p);
        for (const rr of rg.getClientRects()) { if (rr.width < .5 || rr.right < S.l || rr.left > S.r || rr.bottom < S.t || rr.top > S.b) continue; runs.push({ l: rr.left, t: rr.top, r: rr.right, b: rr.bottom, base: rr.top + fm.asc, cap: fm.cap, txt: pc.textTransform === 'uppercase' ? v.trim().toUpperCase() : pc.textTransform === 'lowercase' ? v.trim().toLowerCase() : v.trim() }); }
      }
      const txt = runs.map(q => q.txt).join(' ').replace(/\s+/g, ' ');
      const pseudoIcon = [el, ...shapeKids].some(k => ['::before', '::after'].some(p => { const ps = getComputedStyle(k, p); const kr = k.getBoundingClientRect(); return ps.content !== 'none' && ps.content !== 'normal' && ps.display !== 'none' && !(/absolute|fixed/.test(ps.position) && px(ps.width) >= .8 * kr.width && px(ps.height) >= .8 * kr.height) && pseudoIsIcon(ps, kr); }));
      if (!runs.length && !icons.length && !art.length && !pics.length && !pseudoIcon) { why.push([parts.length ? 'drawing' : 'nocontent', nameOf(el)]); continue; }
      if (txt.length > 60) { why.push(['long', nameOf(el)]); continue; }
      const lines = [];
      for (const q of runs.sort((a, b) => a.t - b.t)) {
        const L = lines.find(L => Math.min(L.b, q.b) - Math.max(L.t, q.t) > .5 * Math.min(L.b - L.t, q.b - q.t));
        if (L) { L.l = Math.min(L.l, q.l); L.r = Math.max(L.r, q.r); L.t = Math.min(L.t, q.t); L.b = Math.max(L.b, q.b); L.base = Math.max(L.base, q.base); L.cap = Math.max(L.cap, q.cap); L.txt += ' ' + q.txt; }
        else lines.push(Object.assign({}, q));
      }
      if (lines.length > 2) { why.push(['lines', nameOf(el)]); continue; }
      /* intent: does the layout mean the content to sit in the middle? A list row (a tile at its left, a chevron at
         its right, words between) is laid out from its edges: its pieces are spread apart, so it is not asked. */
      const cb = { l: r.left + px(cs.borderLeftWidth) + px(cs.paddingLeft), r: r.right - px(cs.borderRightWidth) - px(cs.paddingRight),
                   t: r.top + px(cs.borderTopWidth) + px(cs.paddingTop), b: r.bottom - px(cs.borderBottomWidth) - px(cs.paddingBottom) };
      const atoms = runs.map(q => ({ l: q.l, r: q.r, t: q.t, b: q.b })).concat(icons.concat(art, pics, parts).map(d => R(d.getBoundingClientRect())));
      let ext = null; for (const a of atoms) ext = ext ? { l: Math.min(ext.l, a.l), r: Math.max(ext.r, a.r), t: Math.min(ext.t, a.t), b: Math.max(ext.b, a.b) } : { l: a.l, r: a.r, t: a.t, b: a.b };
      const spread = (lo, hi, span) => { const iv = atoms.map(a => [a[lo], a[hi]]).sort((a, b) => a[0] - b[0]); let gaps = 0, end = -1e9;
        for (const [a0, a1] of iv) { if (end > -1e9 && a0 - end > Math.max(14, .12 * span)) gaps++; end = Math.max(end, a1); } return gaps > 0; };
      let css = cssCentre(el, cs);
      const kids = [...el.children].filter(k => !deco.has(k) && getComputedStyle(k).display !== 'none' && !/absolute|fixed/.test(getComputedStyle(k).position));
      if (kids.length === 1 && !/^(svg|IMG)$/.test(kids[0].tagName)) { const k2 = cssCentre(kids[0], getComputedStyle(kids[0])); css = { h: css.h || k2.h, v: css.v || k2.v }; }
      const grows = /flex/.test(cs.display) && kids.some(k => +getComputedStyle(k).flexGrow > 0);
      const layH = ext ? Math.abs((ext.l - cb.l) - (cb.r - ext.r)) : 0, layV = ext ? Math.abs((ext.t - cb.t) - (cb.b - ext.b)) : 0;
      const row = !/column/.test(cs.flexDirection) || !/flex/.test(cs.display);
      const spreadH = !!ext && (spread('l', 'r', W) || (grows && row) || (/space-between/.test(cs.justifyContent) && row));
      const spreadV = !!ext && (spread('t', 'b', H) || (grows && !row) || (/space-between/.test(cs.justifyContent) && !row));
      let hIntent = !ext || (!spreadH && (css.h || layH <= 2));
      let vIntent = !ext || (!spreadV && (css.v || layV <= Math.max(3, .15 * H)));
      /* the tab bar: the lit tab's content is asked to sit in the middle of the slider's pill, every tab's in its own box -
         across only: the tabs' words share one line by design and their icons differ in height (the Profile tab's
         character is the tallest), so a tab's icon-and-word is not asked to centre up and down */
      if (S.kind === 'virtual') vIntent = false;
      /* two lines of words set from the left (a stat tile, a gauge's caption) are a card's text, not a label in a pill;
         and a list row with a picture in it (a board's row: medal, character, name, number) has each piece centred by
         the row's own layout - the picture's box is not its drawing, so the row as a whole is not asked up and down */
      if (lines.length >= 2 && !hIntent) vIntent = false;
      if (spreadH && art.length) vIntent = false;
      if (el.matches('.bottomtab.active')) { const sl = document.getElementById('bottomtabs-slider'); const sr = sl && sl.getBoundingClientRect();
        if (sr && sr.width > 10 && Math.abs((sr.left + sr.right) / 2 - (r.left + r.right) / 2) < 1.5) { S.l = sr.left; S.t = sr.top; S.r = sr.right; S.b = sr.bottom; S.kind = 'slider'; vIntent = false; } }
      if (!hIntent && !vIntent) { why.push(['intent', nameOf(el)]); continue; }
      /* (384 final check) a ROUND back button's chevron is set 3% of the circle left of its middle, as iOS sets it - a "<"
         centred by its box reads right-heavy, its two open ends carrying the weight - so that is the centre it is held to */
      const opticalDx = (el.matches('.back-link, .settings-nav-back') && !runs.length && Math.abs(r.width - r.height) < 2 && r.width <= 64) ? -.03 * r.width : 0;
      /* not under anything (a header's glass, the tab bar, a sheet): every probe point lands on it or inside it */
      const probes = [[.5, .5], [.25, .3], [.75, .3], [.25, .7], [.75, .7]];
      let hidden = false;
      for (const [fx, fy] of probes) {
        const x = S.l + fx * (S.r - S.l), y = S.t + fy * (S.b - S.t);
        const stack = document.elementsFromPoint(x, y); const i = stack.indexOf(el);
        if (i < 0 && S.kind !== 'slider') { hidden = true; break; }
        for (const a of stack.slice(0, Math.max(0, i))) { if (el.contains(a)) continue; const ac = getComputedStyle(a); if (paints(ac) || /^(svg|IMG|CANVAS|VIDEO)$/.test(a.tagName) || [...a.childNodes].some(c => c.nodeType === 3 && c.nodeValue.trim())) { if (ac.visibility !== 'hidden' && effOpacity(a) > .02) { hidden = true; CZ.why.push(['under', nameOf(el), nameOf(a)]); break; } } }
        if (hidden) break;
      }
      if (hidden) { why.push(['covered', nameOf(el)]); continue; }
      /* the same element over and over (a list's flag buttons): twice is enough */
      /* the same: the same kind of element with the same drawing inside (digits aside), the same size */
      const inner = el.innerHTML.replace(/\s(style|data-[\w-]+|id|aria-[\w-]+|tabindex)="[^"]*"/g, '').replace(/>([^<]*)</g, (m, t) => '>' + t.replace(/\d/g, '#') + '<');
      let hsh = 0; for (let i = 0; i < inner.length; i++) hsh = (hsh * 31 + inner.charCodeAt(i)) | 0;
      const sig = nameOf(el) + '|' + hsh + '|' + Math.round(S.r - S.l) + 'x' + Math.round(S.b - S.t);
      const seen = CZ.sig.get(sig) || 0; if (seen >= 2) { why.push(['repeat', nameOf(el)]); continue; } CZ.sig.set(sig, seen + 1);
      const id = n++;
      el.dataset.czid = String(id);
      /* words with a capital, a digit or an ascender reach the capital height; words of symbols only (a hidden code's
         dots) have no capitals and no baseline to go by, so their ink is taken as it is */
      const tall = /[A-Z0-9bdfhklt!?#$%&@'"()\[\]\/\\|{}À-ɏͰ-῿　-￿]/.test(txt);
      const letters = /[\p{L}\p{N}]/u.test(txt);
      /* a word with a capital AND something reaching higher than it (an ascender, an i's dot): measured on its
         capitals (numbers alone are measured by their own ink - a figure is a capital's height) */
      const caps = /\p{Lu}/u.test(txt) && /[bdfhijklt!?'"]/.test(txt);
      const descender = /[gjpqyQJ,;()\[\]{}|_@$]/.test(txt);
      /* a picture stands in by its box (what can be seen of it): a character is drawn off-symmetric on purpose and placed
         per character, a flare's glow reaches past its orb. In the tab bar a character is the tab's icon over its word, and
         its box is larger than the drawing, so there it is measured by its ink like any icon. */
      if (art.length && el.matches('.bottomtab') && runs.length) { icons.push(...art); art.length = 0; }
      const keep = new Set([...deco, ...orn, ...art]);
      CZ.cands[id] = { el, keep, shapeKids, look: lookOf(el) };
      out.push({ id, name: nameOf(el), path: pathOf(el), txt: txt.slice(0, 40), S: { l: S.l, t: S.t, r: S.r, b: S.b }, kind: S.kind, owned: ownedBy(el),
        lines: letters ? lines.map(L => ({ l: L.l, r: L.r, base: L.base, cap: L.cap, desc: /[gjpqyQJ,;()\[\]{}|_@$]/.test(L.txt) })) : [], tall, caps, desc: descender, icons: icons.length + pics.length + (pseudoIcon ? 1 : 0),
        /* an <svg> or <img> is drawn at its box rounded to the nearest device pixel (as on a phone): where it lands
           depends on where the element happens to sit, up to a sixth of a pixel at 3x; that rounding is taken back
           out so a centred icon does not read off-centre at one place and centred at another */
        snap: (() => { const k = window.devicePixelRatio || 1; const v = icons.filter(d => /^(svg|IMG)$/.test(d.tagName)).map(d => { const q = d.getBoundingClientRect();
            let tx = 0, ty = 0;
            for (let a = d; a && a !== el; a = a.parentElement) { const t = (getComputedStyle(a).translate || 'none').match(/-?[\d.]+/g) || []; tx += +(t[0] || 0); ty += +(t[1] || 0); }
            const l = q.left - tx, tp = q.top - ty; return [Math.round(l * k) / k - l, Math.round(tp * k) / k - tp]; });
          return v.length ? [v.reduce((a, b) => a + b[0], 0) / v.length, v.reduce((a, b) => a + b[1], 0) / v.length] : [0, 0]; })(),
        art: art.concat(parts).map(d => visibleBox(d, el, S)).filter(Boolean),
        /* words beside anything that is not words (an icon, a picture, a chip or disc with a letter in it): the words are
           measured on their own (by their baseline) and the rest by its ink */
        mixed: runs.length > 0 && (icons.length + pics.length > 0 || pseudoIcon ||
          desc.some(d => !deco.has(d) && !shapeKids.has(d) && !within(deco, d) && !d.closest('svg') && paints(getComputedStyle(d)) && d.getBoundingClientRect().width > 0)),
        hIntent, vIntent, opticalDx, layH: +layH.toFixed(2), layV: +layV.toFixed(2), cssH: css.h, cssV: css.v });
    }
    pe.remove();
    return out;
  };
  /* hiding: mode 't' makes the words transparent (and only the words); mode 'a' hides every piece of content too.
     Every change is an inline !important style, saved and put back by CZ.restore(). */
  const save = n => { if (!CZ.saved.has(n)) CZ.saved.set(n, n.getAttribute('style')); };
  const set = (n, k, v) => { save(n); n.style.setProperty(k, v, 'important'); };
  const pseudoKind = (n, p) => { const ps = getComputedStyle(n, p); if (ps.content === 'none' || ps.content === 'normal' || ps.display === 'none') return '';
    const r = n.getBoundingClientRect(); if (/absolute|fixed/.test(ps.position) && px(ps.width) >= .8 * r.width && px(ps.height) >= .8 * r.height) return '';
    return /^["']\s*[^"'\s]/.test(ps.content) ? 'text' : (pseudoIsIcon(ps, r) ? 'icon' : ''); };
  CZ.hide = (ids, mode) => {
    for (const id of ids) {
      const c = CZ.cands[id]; if (!c) continue; const el = c.el;
      const kept = n => { for (const x of c.keep) if (x.contains(n)) return x; return null; };
      const nodes = [el, ...el.querySelectorAll('*')].filter(n => !(n.closest('svg') && n.tagName !== 'svg'));
      /* the words go by their fill alone (-webkit-text-fill-color), so nothing drawn in currentColor - an icon, a rim,
         a switch's knob - changes; what is kept (a corner badge, a character) gets its own fill back, read first */
      const before = new Map(nodes.map(n => { const cs = getComputedStyle(n); return [n, { fill: cs.webkitTextFillColor, shadow: cs.textShadow }]; }));
      for (const n of nodes) {
        const k = kept(n);
        if (k) { if (k === n) { const b = before.get(n); set(n, '-webkit-text-fill-color', b.fill); set(n, 'text-shadow', b.shadow); if (mode === 'a') set(n, 'visibility', 'visible'); } continue; }
        if (n.tagName === 'svg') { if (mode === 'a') set(n, 'visibility', 'hidden'); continue; }
        set(n, '-webkit-text-fill-color', 'transparent'); set(n, 'text-shadow', 'none'); set(n, 'text-decoration-color', 'transparent');
        if (mode === 'a' && n !== el && !c.shapeKids.has(n) && ![...c.keep].some(x => n.contains(x))) set(n, 'visibility', 'hidden');
        if (mode === 'a' && c.shapeKids.has(n)) set(n, 'visibility', 'visible');
      }
      if (mode === 'a') for (const n of [el, ...c.shapeKids]) for (const [p, a] of [['::before', 'b'], ['::after', 'a']]) {
        if (pseudoKind(n, p)) { save(n); n.setAttribute('data-czp-' + a, 'all'); }
      }
    }
  };
  CZ.restore = () => {
    for (const [n, s] of CZ.saved) { if (s === null) n.removeAttribute('style'); else n.setAttribute('style', s); n.removeAttribute('data-czp-b'); n.removeAttribute('data-czp-a'); }
    CZ.saved.clear();
  };
  CZ.changed = ids => ids.filter(id => { const c = CZ.cands[id]; return c && lookOf(c.el) !== c.look; });
  CZ.done = ids => { for (const id of ids) { const c = CZ.cands[id]; if (c) c.el.dataset.czdone = '1'; } };
  const st = document.createElement('style'); st.id = 'cz-style';
  st.textContent = '[data-czp-b]::before,[data-czp-a]::after{visibility:hidden!important}';
  (document.head || document.documentElement).appendChild(st);
  /* a still page: no rAF-driven drawing while a screen is measured */
  const raf = window.requestAnimationFrame.bind(window); let q = [], fid = 1e9;
  window.requestAnimationFrame = cb => { if (CZ.frozen) { q.push(cb); return ++fid; } return raf(cb); };
  CZ.freeze = () => { CZ.frozen = true; try { CZ.held = document.getAnimations().filter(a => a.playState === 'running'); CZ.held.forEach(a => a.pause()); } catch (e) { CZ.held = []; } };
  CZ.thaw = () => { CZ.frozen = false; (CZ.held || []).forEach(a => { try { a.play(); } catch (e) {} }); CZ.held = []; const k = q; q = []; k.forEach(cb => raf(cb)); };
})();
