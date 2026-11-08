#!/usr/bin/env python3
"""Build 384 round 4 - Customize: the four entry cards and every page behind them, centred, on every size, in both classes.
Madison: "when you go to profile and hit customize. Should those 4 options be nicer? Something more when you select which study
modes but not exactly the same? And centered? And then when you click on one could we make sure all the customize options they
are presented nicely, centered well and stuff like that? Ensure it looks good on all device sizes?"
Everything is read off the page (rects, computed styles), never a label or a typed number. Per device and per class:
 ENTRY (showCustomize())
  (E1) four cards (data-page character, banner, theme, fx), each a real tap target (44px both ways), none past the viewport;
  (E2) the cards of one row are one height (and the two rows are too: the grid stretches them);
  (E3) the group is centred in the viewport: its left gap equals its right gap;
  (E4) in each card the picture, the name and the count are centred across the card (centre within 1.5px of the card's);
  (E5) the contents are centred up-down in the card (the gap above the picture equals the gap under the count, within 2px);
  (E6) no horizontal page scroll; with the page scrolled to its end the last card clears the tab bar;
  (E7) on a phone tall enough (>= 800px) all four are on the first screen without scrolling;
 PAGES (showCustomize('character' | 'banner' | 'theme' | 'fx'))
  (P1) the header is centred: the count, the page's line and the hold hint (centre within 1.5px of the column's), and the hint
       is the SAME words on all four pages;
  (P2) every grid's rows are centred as a whole - each row's left slack equals its right slack, so the last, shorter row is in
       the middle - and its tiles are one width, the gaps in a row equal;
  (P3) tile centres line up column for column across the full rows;
  (P4) every row of banner/effect tiles is one height; nothing in a tile (its name, its requirement) is wider than the tile and
       each is centred under its picture;
  (P5) [384 r6, replaces "headings centred"] ONE BOX PER GROUP: every tile sits inside a group card (.cz-group), each card
       holds one header and one grid (384 r7: Theme and Hundo effect are ONE card now, the others two or more); the cards are one width and centred in the viewport; a card is the entry cards' own
       surface (background colour, radius, no shadow - read off the entry page); its header has the name at the left and
       "N of M" at the right, M the card's tiles and N the ones that are yours (counted off the tiles); one tile size across
       every card of a page;
  (P6) exactly one tile is on, and THE ONE MARK: exactly one visible selection mark (.pick-mark) on the page, inside the
       tile that is on, none anywhere else; every locked tile has its padlock;
  (P6b) [384 r6] no ring, no lit box, no glow on the tile that is on: its tile, picture and cell carry no box-shadow,
       filter, growth or light pool, its frame is an unselected tile's, and its name is set like any other held one's;
  (P6c) [384 r6] the mark is round and solid (one colour, no gradient), at least 18px, its tick centred in it (within
       .75px), the tick's path 30-60% of it (geometry, without its stroke), and it sits where a locked tile's padlock sits (centre to centre within 2px of the
       picture's same point);
  (P7) scrolled to the end, the last tile clears the tab bar; no horizontal scroll; a tile is a tap target (44px);
  (P8) a laptop's tiles are not tiny (a character's picture at least 72px on a tablet or laptop);
  (P9) [384 r7, BALANCED ROWS] in every card: maxCols is read off the card (its content width, a tile's width and the grid's
       gap: the most that fit across); the rows are the fewest that hold the tiles (ceil(n / maxCols)), no two rows differ by
       more than one tile, a row is never longer than the one above it, and a card of 3 or more never ends on a single tile
       unless only two fit across (two across cannot make anything else without shrinking the tiles);
  (P10) [384 r7] every row of every card is centred in the card's content box (left slack = right slack within 1.5px);
  (P11) [384 r7] the tile size is the previous build's (6057892), per class, device and page, within .5px: pinned in
       check-b384-custom.tiles.json (`--dump-tiles --against OLD` writes it). It is the reference, so it PASSES on the old
       build by construction; it fails on a copy with a tile size tampered;
  (P12) [384 r7] Theme, Banner and Hundo effect have no single-tile card, and on Theme the default (the swatch no rank hands
       over) is in the same card as every rank colour;
 ROTATION [384 r7] (phone, each class): the character page turned on its side and back keeps (P9) at each step;
 BEHAVIOUR unchanged (phone, academy): tapping a character wears it, tapping a locked one opens its card, a hold opens the card;
  [384 r6] after a tap the one mark is on the new pick only (characters, and a banner and a theme);
 SIGN-UP (Pro Max, each class): the sign-up character screen's pick shows the same mark (one, solid, centred) and no glow,
  growth or ring.
Run:  python3 tools/check-b384-custom.py [--quick] [--only DEVICE] [--class academy|ifc] [--against OLD/index.html]   (the old build must FAIL)
      python3 tools/check-b384-custom.py --dump-tiles --against OLD/index.html   (re-pins (P11)'s tile sizes from OLD)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_custom_lib as L
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
AG = args[args.index("--against") + 1] if "--against" in args else None
CLS = [args[args.index("--class") + 1]] if "--class" in args else ["academy", "ifc"]
QUICK = "--quick" in args
DEVICES = [("iPhone SE 1st", 320, 568, (20, 0, 0, 0)), ("iPhone SE", 375, 667, (20, 0, 0, 0)), ("iPhone 14", 393, 852, (59, 0, 34, 0)),
           ("iPhone 17 Pro Max", 440, 956, (62, 0, 34, 0)), ("iPad mini", 744, 1133, (24, 0, 20, 0)), ("iPad Pro 11", 834, 1194, (24, 0, 20, 0)),
           ("iPad Pro 12.9", 1024, 1366, (24, 0, 20, 0)), ("laptop 1512x852", 1512, 852, (0, 0, 0, 0)), ("laptop 1366x638", 1366, 638, (0, 0, 0, 0)),
           ("phone landscape", 874, 402, (0, 62, 21, 62))]
if QUICK: DEVICES = [d for d in DEVICES if d[0] in ("iPhone SE", "iPhone 17 Pro Max", "iPad Pro 11", "laptop 1512x852")]
if "--only" in args: DEVICES = [d for d in DEVICES if args[args.index("--only") + 1].lower() in d[0].lower()]
ok = True; nfail = 0
SURF = {}
DUMP = "--dump-tiles" in args
TILES_JSON = os.path.join(HERE, "check-b384-custom.tiles.json")
TILES = json.load(open(TILES_JSON)) if os.path.exists(TILES_JSON) and not DUMP else {}
DUMPED = {}
def chk(name, cond, info=""):
    global ok, nfail
    ok = ok and bool(cond)
    if not cond: nfail += 1
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

LIB = r"""() => {
  const R = e => { const r = e.getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height, cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2 }; };
  const shown = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const tabTop = () => { const t = document.getElementById('bottomtabs'); if(!t || t.hidden) return innerHeight; const r = t.getBoundingClientRect(); return r.height > 0 && getComputedStyle(t).display !== 'none' ? r.top : innerHeight; };
  const rows = (els, tol) => { const out = []; els.slice().sort((a, b) => R(a).t - R(b).t || R(a).l - R(b).l).forEach(e => { const t = R(e).t; let g = out.find(x => Math.abs(x.t - t) <= (tol || 6)); if(!g){ g = { t, els: [] }; out.push(g); } g.els.push(e); }); out.forEach(g => g.els.sort((a, b) => R(a).l - R(b).l)); return out; };
  const toEnd = async () => { window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' }); await new Promise(r => setTimeout(r, 500)); };
  const toTop = async () => { window.scrollTo({ top: 0, behavior: 'instant' }); await new Promise(r => setTimeout(r, 300)); };
  window.__cz = { R, shown, tabTop, rows, toEnd, toTop };
}"""

ENTRY = r"""async () => {
  const { R, tabTop, rows, toEnd, toTop } = window.__cz;
  const out = { errs: [] };
  const cards = [...document.querySelectorAll('.screen-customize .cz-row')];
  out.pages = cards.map(c => c.dataset.page);
  out.hscroll = document.documentElement.scrollWidth - innerWidth;
  const rs = cards.map(R);
  out.small = rs.filter(r => r.w < 44 || r.h < 44).length;
  out.past = rs.filter(r => r.l < -0.5 || r.r > innerWidth + 0.5).length;
  const rw = rows(cards, 8);
  out.rowHeights = rw.map(g => g.els.map(e => Math.round(R(e).h * 10) / 10));
  out.allH = rs.map(r => Math.round(r.h * 10) / 10);
  const L0 = Math.min(...rs.map(r => r.l)), R0 = Math.max(...rs.map(r => r.r));
  out.gaps = [Math.round(L0 * 10) / 10, Math.round((innerWidth - R0) * 10) / 10];
  out.ncols = rw.length ? rw[0].els.length : 0;
  // each card: the picture, the name and the count are centred across it, and the contents centred up-down
  out.cards = cards.map(c => { const cr = R(c), pick = c.querySelector('.cz-pick'), lab = c.querySelector('.cz-label'), val = c.querySelector('.cz-value'), go = c.querySelector('.cz-go') || c.querySelector('.cz-count');
    const art = c.querySelector('.cz-art'), meta = c.querySelector('.cz-meta');
    const pr = pick && R(pick), lr = lab && R(lab), vr = val && R(val), gr = go && R(go);
    const top = art ? R(art).t + (parseFloat(getComputedStyle(art).height) - (pr ? pr.h : 0)) / 2 : null;
    return { page: c.dataset.page, d: { pick: pr && Math.round((pr.cx - cr.cx) * 10) / 10, lab: lr && Math.round((lr.cx - cr.cx) * 10) / 10, val: vr && Math.round((vr.cx - cr.cx) * 10) / 10, go: gr && Math.round((gr.cx - cr.cx) * 10) / 10 },
      up: art && gr ? [Math.round((R(art).t - cr.t) * 10) / 10, Math.round((cr.b - gr.b) * 10) / 10] : null,
      pickUp: pr && art ? Math.round((pr.cy - R(art).cy) * 10) / 10 : null }; });
  out.first = rs.length ? { allAbove: rs.every(r => r.b <= Math.min(tabTop(), innerHeight) + 0.5), vh: innerHeight } : null;
  await toEnd();
  const rs2 = cards.map(R);
  out.endClear = Math.min(tabTop() - Math.max(...rs2.map(r => r.b)), 9999);
  out.hscroll2 = document.documentElement.scrollWidth - innerWidth;
  await toTop();
  return out; }"""

PAGE = r"""async (kind) => {
  const { R, shown, tabTop, rows, toEnd, toTop } = window.__cz;
  const out = { kind, errs: [] };
  const P = document.querySelector('.screen-customize');
  const col = R(P.querySelector('.ios-nav, .settings-nav') || P);
  const vcx = innerWidth / 2;
  out.hscroll = document.documentElement.scrollWidth - innerWidth;
  // the header
  const count = P.querySelector('.cz-bar-count'), note = P.querySelector('.cz-page-note'), hint = P.querySelector('.cz-page-hint');
  const ctr = e => { if(!e) return null; const r = document.createRange(); r.selectNodeContents(e); const b = r.getBoundingClientRect(); return Math.round(((b.left + b.right) / 2 - vcx) * 10) / 10; };
  out.head = { count: ctr(count), note: ctr(note), hint: ctr(hint) };
  out.hint = hint ? hint.textContent : null;
  // the grids
  const SEL = { character: ['.avatarchar-grid.avatarchar-grid-appearance', '.avatarchar-cell'], banner: ['.banner-grid', '.banner-opt'], theme: ['.swatches', '.swatch-cell'], fx: ['.hfx-grid', '.hfx-opt'] }[kind];
  out.grids = [...P.querySelectorAll(SEL[0])].filter(shown).map(g => { const gr = R(g); const tiles = [...g.querySelectorAll(':scope > ' + SEL[1])].filter(shown); const tr = tiles.map(R);
    const rw = rows(tiles, 6);
    const rowInfo = rw.map(x => { const rr = x.els.map(R); const sl = rr[0].l - gr.l, sr = gr.r - rr[rr.length - 1].r;
      const gaps = rr.slice(1).map((r, i) => r.l - rr[i].r);
      return { n: rr.length, slack: [Math.round(sl * 10) / 10, Math.round(sr * 10) / 10], gaps: gaps.map(v => Math.round(v * 10) / 10), cx: rr.map(r => Math.round(r.cx * 10) / 10), hs: rr.map(r => Math.round(r.h * 10) / 10) }; });
    const ws = tr.map(r => Math.round(r.w * 10) / 10);
    return { n: tiles.length, w: Math.round(gr.w), tw: [Math.min(...ws), Math.max(...ws)], rows: rowInfo, min: Math.min(...tr.map(r => Math.min(r.w, r.h))) }; });
  // words in tiles: inside the tile, centred under the picture
  const words = [];
  P.querySelectorAll(SEL[1]).forEach(t => { if(!shown(t)) return; const tr = R(t);
    t.querySelectorAll('.avatarchar-name, .swatch-name, .banner-opt-name, .banner-opt-need, .hfx-opt-name, .hfx-opt-need').forEach(w => { if(!shown(w)) return;
      const rg = document.createRange(); rg.selectNodeContents(w); const b = rg.getBoundingClientRect();
      const inside = b.left >= tr.l - 1 && b.right <= tr.r + 1;
      const wide = w.scrollWidth > w.clientWidth + 1;
      const pic = t.querySelector('.avatarchar-option, .swatch, .banner-opt-art, .hfx-opt-art'); const pc = pic ? R(pic).cx : tr.cx;
      words.push({ txt: (w.textContent || '').slice(0, 18), inside, wide, off: Math.round(((b.left + b.right) / 2 - pc) * 10) / 10 }); }); });
  out.wordsBad = words.filter(w => !w.inside || w.wide).slice(0, 4);
  out.wordsOff = words.filter(w => Math.abs(w.off) > 2).slice(0, 4);
  out.nwords = words.length;
  // character section headings
  out.heads = [...P.querySelectorAll('.avatarchar-group-title')].filter(shown).map(h => ctr(h.firstChild && h.firstChild.nodeType === 3 ? h : h));
  out.headTitles = [...P.querySelectorAll('.avatarchar-group-title')].filter(shown).map(h => { const r = document.createRange(); r.selectNodeContents(h.childNodes[0]); const b = r.getBoundingClientRect(); return Math.round(((b.left + b.right) / 2 - vcx) * 10) / 10; });
  // marks: the one on, its tick; locks
  const tiles = [...P.querySelectorAll(SEL[1])];
  const on = kind === 'character' ? [...P.querySelectorAll('.avatarchar-option.selected')] : kind === 'theme' ? [...P.querySelectorAll('.swatch.on')] : [...P.querySelectorAll('.banner-opt.selected, .hfx-opt.selected')];
  const tick = e => { if(kind === 'character'){ const c = e.querySelector('.avatarchar-check'); return !!c && +getComputedStyle(c).opacity > .9; } const a = getComputedStyle(e, '::after'); return a.content !== 'none' && a.content !== 'normal' && parseFloat(a.width) > 8; };
  out.on = on.length; out.ticks = on.filter(tick).length;
  const locked = kind === 'character' ? [...P.querySelectorAll('.avatarchar-option.locked')] : kind === 'theme' ? [...P.querySelectorAll('.swatch.locked')] : [...P.querySelectorAll('.banner-opt.locked:not(.is-secret), .hfx-opt.locked')];
  const lockSel = { character: '.avatarchar-lockmark', theme: '.swatch-lockmark', banner: '.banner-opt-lock', fx: '.hfx-opt-lock' }[kind];
  out.locked = locked.length; out.locks = locked.filter(e => e.querySelector(lockSel) && shown(e.querySelector(lockSel))).length;
  // (384 r6) the boxes
  const isLk = t => kind === 'character' ? !!t.querySelector('.avatarchar-option.locked') : kind === 'theme' ? !!t.querySelector('.swatch.locked') : t.classList.contains('locked');
  out.groups = [...P.querySelectorAll('.cz-group')].filter(shown).map(g => { const r = R(g), s = getComputedStyle(g);
    const head = g.querySelector(':scope > .cz-group-head'), tl = [...g.querySelectorAll(SEL[1])].filter(shown);
    const cnt = head && head.querySelector('.cz-group-count'), nm = head && head.querySelector('.cz-group-name');
    return { l: Math.round(r.l * 10) / 10, r: Math.round(r.r * 10) / 10, w: Math.round(r.w * 10) / 10, bg: s.backgroundColor, img: s.backgroundImage, rad: s.borderTopLeftRadius, shadow: s.boxShadow,
      heads: g.querySelectorAll(':scope > .cz-group-head').length, grids: g.querySelectorAll(':scope > ' + SEL[0]).length, n: tl.length, held: tl.filter(t => !isLk(t)).length,
      nums: cnt ? (cnt.textContent.match(/\d+/g) || []).map(Number) : [],
      nameL: nm ? Math.round((R(nm).l - r.l) * 10) / 10 : null, cntR: cnt ? Math.round((r.r - R(cnt).r) * 10) / 10 : null, between: nm && cnt ? Math.round((R(cnt).l - R(nm).r) * 10) / 10 : null }; });
  // (384 r7) balanced rows: per card, maxCols off the card, the row lengths, each row's slack against the card's content box
  out.bal = [...P.querySelectorAll('.cz-group')].filter(shown).map(g => { const cs = getComputedStyle(g), r = R(g);
    const cl = r.l + parseFloat(cs.paddingLeft), cr = r.r - parseFloat(cs.paddingRight), cw = cr - cl;
    const grid = g.querySelector(':scope > ' + SEL[0]); const tl = [...g.querySelectorAll(SEL[1])].filter(shown);
    const tw = tl.length ? R(tl[0]).w : 0; const gx = grid ? parseFloat(getComputedStyle(grid).columnGap) || 0 : 0;
    const rw = rows(tl, 6);
    return { n: tl.length, maxCols: tw ? Math.max(1, Math.floor((cw + gx + 0.5) / (tw + gx))) : 0, lens: rw.map(x => x.els.length),
      slack: rw.map(x => { const a = R(x.els[0]), b = R(x.els[x.els.length - 1]); return Math.round(((a.l - cl) - (cr - b.r)) * 10) / 10; }),
      isDefault: kind === 'theme' ? tl.map(t => { const sw = t.querySelector('[data-swatch]'); return !!sw && !(typeof TIER_UNLOCKS === 'object' && TIER_UNLOCKS[sw.dataset.swatch]); }) : [],
      isRank: kind === 'theme' ? tl.map(t => { const sw = t.querySelector('[data-swatch]'); return !!sw && typeof TIER_UNLOCKS === 'object' && !!TIER_UNLOCKS[sw.dataset.swatch]; }) : [] }; });
  out.loose = [...P.querySelectorAll(SEL[1])].filter(shown).filter(t => !t.closest('.cz-group')).length;
  const allW = [...P.querySelectorAll(SEL[1])].filter(shown).map(t => Math.round(R(t).w * 10) / 10);
  out.tileW = allW.length ? [Math.min(...allW), Math.max(...allW)] : [0, 0];
  // (384 r6) the one mark
  const vis = m => shown(m) && +getComputedStyle(m).opacity > .9;
  const marks = [...P.querySelectorAll('.pick-mark')].filter(vis);
  out.marks = marks.length;
  const selT = on[0] || null;
  out.markInSel = marks.length === 1 && !!selT && selT.contains(marks[0]);
  const PIC = { character: '.avatarchar-option', theme: '.swatch', banner: '.banner-opt-art', fx: '.hfx-opt-art' }[kind];
  const rel = (c, pic) => { const a = R(c), b = R(pic); return kind === 'banner' || kind === 'fx' ? [b.r - a.cx, a.cy - b.t] : [a.cx - b.l, a.cy - b.t]; };
  if(marks[0]){ const m = marks[0], mr = R(m), cs = getComputedStyle(m), path = m.querySelector('path'), pr = path ? R(path) : null;
    const pic = m.closest(PIC);
    const lt = [...P.querySelectorAll(lockSel)].find(e => shown(e) && e.closest(PIC) && !e.closest('.is-secret'));
    const mrel = pic ? rel(m, pic) : null, lrel = lt ? rel(lt, lt.closest(PIC)) : null;
    out.mark = { w: Math.round(mr.w * 10) / 10, h: Math.round(mr.h * 10) / 10, round: parseFloat(cs.borderTopLeftRadius) >= mr.w / 2 - .5 || cs.borderTopLeftRadius === '50%', bg: cs.backgroundColor, img: cs.backgroundImage,
      dx: pr ? Math.round((pr.cx - mr.cx) * 100) / 100 : null, dy: pr ? Math.round((pr.cy - mr.cy) * 100) / 100 : null, glyph: pr ? Math.round(Math.max(pr.w, pr.h) / mr.w * 100) / 100 : null,
      place: mrel && lrel ? [Math.round((mrel[0] - lrel[0]) * 10) / 10, Math.round((mrel[1] - lrel[1]) * 10) / 10] : null }; }
  // (384 r6) no ring, no lit box, no glow on the one that is on: compared with a held tile that is not on (or with nothing)
  if(selT){
    const CELL = kind === 'character' ? '.avatarchar-cell' : kind === 'theme' ? '.swatch-cell' : SEL[1];
    const cellOf = e => e.closest(CELL);
    const other = [...P.querySelectorAll(CELL)].filter(shown).find(c => !c.contains(selT) && c !== selT && !isLk(c));
    const look = cell => { if(!cell) return null; const pic = cell.matches(PIC) ? cell : cell.querySelector(PIC); const tile = kind === 'character' ? cell.querySelector('.avatarchar-option') : kind === 'theme' ? cell.querySelector('.swatch') : cell;
      const ps = getComputedStyle(pic), ts = getComputedStyle(tile), cs = getComputedStyle(cell), b4 = getComputedStyle(tile, '::before'), af = getComputedStyle(tile, '::after');
      const nm = cell.querySelector('.avatarchar-name, .swatch-name, .banner-opt-name, .hfx-opt-name'); const ns = nm ? getComputedStyle(nm) : null;
      const tf = ts.transform === 'none' ? 1 : (new DOMMatrix(ts.transform)).a;
      return { tileShadow: ts.boxShadow, picShadow: ps.boxShadow, cellShadow: cs.boxShadow, filter: ts.filter, scale: Math.round(tf * 1000) / 1000,
        pool: kind === 'character' ? +b4.opacity : 0, ring: kind === 'character' ? +af.opacity : 0,
        cellBg: cs.backgroundColor + ' ' + cs.backgroundImage, cellBorder: cs.borderTopWidth + ' ' + cs.borderTopColor, picBorder: ps.borderTopWidth + ' ' + ps.borderTopColor,
        name: ns ? [ns.color, ns.fontWeight, +ns.opacity].join(' ') : null }; };
    out.selLook = look(cellOf(selT));
    out.otherLook = look(other || null);
  }
  // a picture's size (the character's coin)
  const pics = [...P.querySelectorAll(kind === 'character' ? '.avatarchar-option' : kind === 'theme' ? '.swatch' : '.banner-opt-art, .hfx-opt-art')].filter(shown).map(R);
  out.picMin = pics.length ? Math.round(Math.min(...pics.map(r => Math.min(r.w, r.h)))) : 0;
  // the end of the page against the tab bar
  await toEnd();
  const tl = [...P.querySelectorAll(SEL[1])].filter(shown).map(R);
  out.endClear = Math.round(Math.min(tabTop() - Math.max(...tl.map(r => r.b)), 9999));
  out.hscroll2 = document.documentElement.scrollWidth - innerWidth;
  await toTop();
  return out; }"""

def near(a, b, tol): return a is not None and b is not None and abs(a - b) <= tol

def balance_faults(bal):
    """(P9) the shape of each card's rows: fewest rows, lengths within one, never longer than the row above, no lone last
    tile in a card of 3+ unless only two fit across"""
    out = []
    for b in bal:
        L_, n, m = b["lens"], b["n"], b["maxCols"]
        if not L_ or not m: out.append(("no rows", b)); continue
        if len(L_) != -(-n // m): out.append(("rows %d, want ceil(%d/%d)" % (len(L_), n, m), L_))
        if max(L_) - min(L_) > 1: out.append(("lengths differ by more than one", L_))
        if any(L_[i + 1] > L_[i] for i in range(len(L_) - 1)): out.append(("a row longer than the one above", L_))
        if n >= 3 and len(L_) > 1 and L_[-1] == 1 and m > 2: out.append(("a lone last tile", L_, "max", m))
        if max(L_) > m: out.append(("a row wider than fits", L_, m))
    return out

ROWS = r"""() => { const { R, shown, rows } = window.__cz; return [...document.querySelectorAll('.screen-customize .cz-group')].filter(shown).map(g => {
  const cs = getComputedStyle(g), r = R(g), cw = r.w - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const grid = g.querySelector(':scope > .avatarchar-grid'), tl = [...g.querySelectorAll('.avatarchar-cell')].filter(shown);
  const tw = tl.length ? R(tl[0]).w : 0, gx = grid ? parseFloat(getComputedStyle(grid).columnGap) || 0 : 0;
  return { n: tl.length, maxCols: tw ? Math.max(1, Math.floor((cw + gx + 0.5) / (tw + gx))) : 0, lens: rows(tl, 6).map(x => x.els.length) }; }); }"""

def rotation(br, cls):
    ctx, pg, errs = L.open_page(br, cls, 440, 956, (62, 0, 34, 0), body=L.body_for(AG, (62, 0, 34, 0)) if AG else None)
    pg.evaluate(LIB)
    tag = "[%s rotation]" % cls
    pg.evaluate("()=>showCustomize('character')"); pg.wait_for_timeout(2300)
    for W, H in ((440, 956), (956, 440), (440, 956)):
        pg.set_viewport_size({"width": W, "height": H}); pg.wait_for_timeout(700)
        b = pg.evaluate(ROWS); bad = balance_faults(b)
        chk("%s (P9) %dx%d: balanced rows after the turn (%s)" % (tag, W, H, "; ".join("%d max%d %s" % (x["n"], x["maxCols"], "+".join(map(str, x["lens"]))) for x in b)), b and not bad, bad[:3])
    chk("%s no page errors" % tag, not errs, errs[:2]); ctx.close()

def run_device(br, dev, cls):
    name, W, H, ins = dev
    body = L.body_for(AG, ins) if AG else None
    ctx, pg, errs = L.open_page(br, cls, W, H, ins, body=body, dpr=1)
    pg.evaluate(LIB)
    tag = "[%s %s %dx%d]" % (cls, name, W, H)
    got = pg.evaluate("() => window.NOVA_CLASS")
    chk("%s the page is in its class (%s)" % (tag, got), got == ("ifc" if cls == "ifc" else "academy"), got)
    pg.evaluate("()=>showCustomize()"); pg.wait_for_timeout(1800)
    e = pg.evaluate(ENTRY)
    SURF[cls] = pg.evaluate("()=>{ const c=document.querySelector('.screen-customize .cz-row'); if(!c) return null; const s=getComputedStyle(c); return { bg: s.backgroundColor, rad: s.borderTopLeftRadius, img: s.backgroundImage }; }")
    chk("%s (E1) four cards, each a 44px tap target, none past the viewport (%s)" % (tag, e["pages"]),
        e["pages"] == ["character", "banner", "theme", "fx"] and e["small"] == 0 and e["past"] == 0, [e["pages"], e["small"], e["past"]])
    chk("%s (E2) the cards are one height (%s)" % (tag, e["allH"]), max(e["allH"]) - min(e["allH"]) <= 1.01 if e["allH"] else False, e["allH"])
    chk("%s (E3) the group is centred in the viewport (gaps %s)" % (tag, e["gaps"]), near(e["gaps"][0], e["gaps"][1], 1.5), e["gaps"])
    bad = [c for c in e["cards"] if not all(near(c["d"][k], 0, 1.5) for k in ("pick", "lab", "val", "go") if c["d"][k] is not None)]
    chk("%s (E4) each card's picture, name and count are centred across it" % tag, e["cards"] and not bad, bad[:2])
    bad = [c for c in e["cards"] if not c["up"] or abs(c["up"][0] - c["up"][1]) > 2.5 or c["up"][0] < 4 or not near(c["pickUp"], 0, 1.5)]
    chk("%s (E5) each card's contents are centred up-down (gap over the picture box / under the count %s, the picture in its box)" % (tag, [c["up"] for c in e["cards"]]), e["cards"] and not bad, bad[:2])
    chk("%s (E6) no horizontal scroll, and the last card clears the tab bar when scrolled to the end (%spx)" % (tag, e["endClear"]),
        e["hscroll"] <= 0 and e["hscroll2"] <= 0 and e["endClear"] >= -0.5, [e["hscroll"], e["hscroll2"], e["endClear"]])
    if W < 700 and H >= 800 and H > W:
        chk("%s (E7) all four cards are on the first screen" % tag, e["first"]["allAbove"], e["first"])
    # the pages
    hints = []
    for kind in ("character", "banner", "theme", "fx"):
        pg.evaluate("(k)=>showCustomize(k)", kind); pg.wait_for_timeout(2300)
        r = pg.evaluate(PAGE, kind); hints.append(r["hint"])
        t = "%s [%s]" % (tag, kind)
        chk("%s (P1) the count, the line and the hint are centred (%s)" % (t, r["head"]), r["head"]["count"] is not None and all(near(v, 0, 1.5) for v in r["head"].values() if v is not None) and r["head"]["hint"] is not None, r["head"])
        okrows = bool(r["grids"]) and all(g["rows"] for g in r["grids"])
        slack = [(g["w"], ro["slack"]) for g in r["grids"] for ro in g["rows"] if not near(ro["slack"][0], ro["slack"][1], 1.5)]
        chk("%s (P2) every row of every grid is centred as a whole, the last short row too (%d rows)" % (t, sum(len(g["rows"]) for g in r["grids"])), okrows and not slack, slack[:3])
        badw = [g["tw"] for g in r["grids"] if g["tw"][1] - g["tw"][0] > 1.01]
        badg = [ro["gaps"] for g in r["grids"] for ro in g["rows"] if ro["gaps"] and max(ro["gaps"]) - min(ro["gaps"]) > 1.01]
        chk("%s (P2) one tile width, equal gaps in a row" % t, not badw and not badg, [badw[:2], badg[:2]])
        miscol = []
        for g in r["grids"]:
            full = [ro for ro in g["rows"] if ro["n"] == max(x["n"] for x in g["rows"])]
            for ro in full[1:]:
                if any(abs(a - b) > 1.5 for a, b in zip(ro["cx"], full[0]["cx"])): miscol.append(ro["cx"][:3])
        chk("%s (P3) tile centres line up column for column" % t, not miscol, miscol[:2])
        if kind in ("banner", "fx"):
            hs = [ro["hs"] for g in r["grids"] for ro in g["rows"] if max(ro["hs"]) - min(ro["hs"]) > 1.01]
            chk("%s (P4) a row's tiles are one height" % t, not hs, hs[:2])
        chk("%s (P4) no word is wider than its tile (%d words)" % (t, r["nwords"]), r["nwords"] > 0 and not r["wordsBad"], r["wordsBad"])
        chk("%s (P4) each word is centred under its picture" % t, not r["wordsOff"], r["wordsOff"])
        gs = r["groups"]
        chk("%s (P5) every tile sits in a group card, one header and one grid per card (%d cards, %d loose tiles)" % (t, len(gs), r["loose"]),
            len(gs) >= (2 if kind in ("character", "banner") else 1) and r["loose"] == 0 and all(g["heads"] == 1 and g["grids"] == 1 and g["n"] > 0 for g in gs), [r["loose"], [(g["heads"], g["grids"], g["n"]) for g in gs]])
        if gs:
            ws = [g["w"] for g in gs]; cen = [round(g["l"] - (W - g["r"]), 1) for g in gs]
            chk("%s (P5) the cards are one width and centred (%s, left-right %s)" % (t, sorted(set(ws)), sorted(set(cen))), max(ws) - min(ws) <= 1.01 and all(abs(c) <= 1.5 for c in cen), [ws, cen])
            sk = SURF.get(cls)
            same = [g for g in gs if sk and g["bg"] == sk["bg"] and g["rad"] == sk["rad"] and g["shadow"] in ("none", "") and g["img"] == sk["img"]]
            chk("%s (P5) a card is the entry cards' surface: colour, radius, no shadow (%s)" % (t, (gs[0]["bg"], gs[0]["rad"], gs[0]["shadow"])), sk and len(same) == len(gs), [sk, [(g["bg"], g["rad"], g["shadow"], g["img"][:40]) for g in gs if g not in same][:2]])
            badh = [(g["nameL"], g["cntR"], g["between"]) for g in gs if g["nameL"] is None or g["cntR"] is None or abs(g["nameL"] - g["cntR"]) > 1.5 or g["nameL"] > 32 or g["between"] < 4]
            chk("%s (P5) each header: the name at the left, the count at the right, the same inset from each side (%s)" % (t, [(g["nameL"], g["cntR"]) for g in gs][:2]), not badh, badh[:2])
            badn = [(g["nums"], g["held"], g["n"]) for g in gs if g["nums"] != [g["held"], g["n"]]]
            chk("%s (P5) each count is N of M off the card's own tiles (%s)" % (t, [g["nums"] for g in gs]), not badn, badn[:3])
        chk("%s (P5) one tile size across every card (%s)" % (t, r["tileW"]), r["tileW"][1] - r["tileW"][0] <= 1.01, r["tileW"])
        chk("%s (P6) exactly one is on, and exactly one mark on the page, inside it (%d on, %d marks, inside %s); every locked tile has its padlock (%d of %d)" % (t, r["on"], r["marks"], r["markInSel"], r["locks"], r["locked"]),
            r["on"] == 1 and r["marks"] == 1 and r["markInSel"] and r["locked"] == r["locks"], [r["on"], r["marks"], r["markInSel"], r["locked"], r["locks"]])
        sl, ol = r.get("selLook"), r.get("otherLook")
        lit = []
        if sl:
            for k in ("tileShadow", "picShadow", "cellShadow"):
                if sl[k] not in ("none", ""): lit.append((k, sl[k][:60]))
            if sl["filter"] not in ("none", ""): lit.append(("filter", sl["filter"][:60]))
            if abs(sl["scale"] - 1) > .001: lit.append(("scale", sl["scale"]))
            if sl["pool"] > .01: lit.append(("light pool", sl["pool"]))
            if sl["ring"] > .01: lit.append(("ring", sl["ring"]))
            if ol:
                for k in ("cellBg", "cellBorder", "picBorder", "name"):
                    if sl[k] != ol[k]: lit.append((k, sl[k], ol[k]))
        chk("%s (P6b) no ring, no lit box, no glow on the one that is on (its frame and name an unselected one's)" % t, sl is not None and not lit, lit[:4])
        mk = r.get("mark")
        okm = bool(mk) and mk["round"] and mk["w"] >= 18 and abs(mk["w"] - mk["h"]) <= .5 and mk["img"] == "none" and mk["bg"].startswith("rgb(") \
            and mk["dx"] is not None and abs(mk["dx"]) <= .75 and abs(mk["dy"]) <= .75 and .3 <= mk["glyph"] <= .6
        chk("%s (P6c) the mark is round and solid, its tick centred (%s)" % (t, mk and (mk["w"], mk["bg"], mk["dx"], mk["dy"], mk["glyph"])), okm, mk)
        if r["locked"]:
            chk("%s (P6c) the mark sits where a locked tile's padlock sits (%s)" % (t, mk and mk["place"]), bool(mk) and mk["place"] is not None and all(abs(v) <= 2 for v in mk["place"]), mk and mk["place"])
        chk("%s (P7) the end clears the tab bar (%spx), no horizontal scroll, tiles are 44px targets (%s)" % (t, r["endClear"], r["picMin"]),
            r["endClear"] >= -0.5 and r["hscroll"] <= 0 and r["hscroll2"] <= 0 and r["picMin"] >= 44, [r["endClear"], r["hscroll"], r["hscroll2"], r["picMin"]])
        if kind == "character" and W >= 700:
            chk("%s (P8) the characters are not tiny on a big screen (%spx)" % (t, r["picMin"]), r["picMin"] >= 72, r["picMin"])
        bad = balance_faults(r["bal"])
        chk("%s (P9) balanced rows in every card (%s)" % (t, "; ".join("%d max%d %s" % (b["n"], b["maxCols"], "+".join(map(str, b["lens"]))) for b in r["bal"])), r["bal"] and not bad, bad[:3])
        offc = [(b["lens"], b["slack"]) for b in r["bal"] if any(abs(v) > 1.5 for v in b["slack"])]
        chk("%s (P10) every row is centred in its card" % t, r["bal"] and not offc, offc[:2])
        key = "%s|%dx%d|%s" % (cls, W, H, kind)
        if DUMP: DUMPED[key] = r["tileW"][0]
        elif key in TILES:
            chk("%s (P11) the tile size is the previous build's (%s, was %s)" % (t, r["tileW"], TILES[key]), abs(r["tileW"][0] - TILES[key]) <= .5 and abs(r["tileW"][1] - TILES[key]) <= .5, [r["tileW"], TILES[key]])
        else:
            chk("%s (P11) a pinned tile size exists for this device (run --dump-tiles)" % t, False, key)
        if kind in ("theme", "banner", "fx"):
            ones = [b["n"] for b in r["bal"] if b["n"] < 2]
            okd = True
            if kind == "theme":
                home = [i for i, b in enumerate(r["bal"]) if any(b["isDefault"])]
                ranks = [i for i, b in enumerate(r["bal"]) if any(b["isRank"])]
                okd = len(home) == 1 and ranks == home and sum(sum(b["isRank"]) for b in r["bal"]) >= 2
            chk("%s (P12) no single-tile card%s (%s)" % (t, ", the default in the rank colours' card" if kind == "theme" else "", [b["n"] for b in r["bal"]]), not ones and okd, [ones, okd])
    chk("%s (P1) the hold hint is the same words on all four pages (%s)" % (tag, hints[0]), all(hints) and len(set(hints)) == 1, hints)
    chk("%s no page errors" % tag, not errs, errs[:2])
    ctx.close()

def behaviour(br, cls):
    ctx, pg, errs = L.open_page(br, cls, 440, 956, (62, 0, 34, 0), body=L.body_for(AG, (62, 0, 34, 0)) if AG else None)
    tag = "[%s behaviour]" % cls
    pg.evaluate("()=>showCustomize('character')"); pg.wait_for_timeout(2500)
    before = pg.evaluate("()=>store.avatarChar")
    pick = pg.evaluate("""()=>{ const o=[...document.querySelectorAll('.avatarchar-option:not(.locked):not(.selected)')][0]; if(!o) return null; o.scrollIntoView({block:'center'}); return o.getAttribute('aria-label'); }""")
    pg.wait_for_timeout(400)
    pg.locator('.avatarchar-option:not(.locked):not(.selected)').first.click(); pg.wait_for_timeout(700)
    after = pg.evaluate("()=>store.avatarChar")
    chk("%s tapping a held character wears it (%s -> %s)" % (tag, before, after), pick and after != before, [before, after])
    MK = """()=>{ const vis=[...document.querySelectorAll('.screen-customize .pick-mark')].filter(m=>+getComputedStyle(m).opacity>.9); const on=document.querySelector('.screen-customize :is(.avatarchar-option.selected, .swatch.on, .banner-opt.selected, .hfx-opt.selected)'); return [vis.length, !!on && vis.length===1 && on.contains(vis[0])]; }"""
    pg.wait_for_timeout(400)
    m = pg.evaluate(MK)
    chk("%s (384 r6) after the tap the one mark is on the new character only (%s)" % (tag, m), m == [1, True], m)
    pg.evaluate("()=>document.querySelector('.avatarchar-option.locked').scrollIntoView({block:'center'})"); pg.wait_for_timeout(400)
    pg.locator('.avatarchar-option.locked').first.click(); pg.wait_for_timeout(700)
    chk("%s tapping a locked one opens its card, and nothing is worn" % tag, pg.evaluate("()=>!!document.querySelector('.unlock-card') && store.avatarChar") == after, pg.evaluate("()=>store.avatarChar"))
    pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(e=>e.remove())")
    box = pg.locator('.avatarchar-option:not(.locked):not(.selected)').first.bounding_box()
    pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2); pg.mouse.down(); pg.wait_for_timeout(1300); pg.mouse.up(); pg.wait_for_timeout(500)
    chk("%s a hold opens the card (and does not wear it)" % tag, pg.evaluate("()=>!!document.querySelector('.unlock-card') && store.avatarChar") == after, pg.evaluate("()=>[!!document.querySelector('.unlock-card'), store.avatarChar]"))
    pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(e=>e.remove())")
    pg.evaluate("()=>showCustomize()"); pg.wait_for_timeout(1500)
    pg.locator('.cz-row[data-page=banner]').click(); pg.wait_for_timeout(1500)
    chk("%s a card opens its page" % tag, pg.evaluate("()=>!!document.querySelector('.screen-customize.cz-page-banner')"))
    pg.wait_for_timeout(800)
    # a banner and a theme: tap another held one (forced held where the account has none) and the mark follows
    for kind, sel in (("banner", ".banner-opt:not(.locked):not(.selected)"), ("theme", ".swatch:not(.locked):not(.on)")):
        if kind == "theme":
            pg.evaluate("()=>{ window.isLockedAccent=()=>false; showCustomize('theme'); }"); pg.wait_for_timeout(1500)
        else:
            pg.evaluate("()=>{ window.bannerEarned=()=>true; showCustomize('banner'); }"); pg.wait_for_timeout(1800)
        loc = pg.locator(".screen-customize " + sel).nth(1)
        loc.scroll_into_view_if_needed(); pg.wait_for_timeout(300); loc.click(); pg.wait_for_timeout(700)
        m = pg.evaluate(MK)
        chk("%s (384 r6) tapping another %s moves the one mark to it (%s)" % (tag, kind, m), m == [1, True], m)
    chk("%s no page errors" % tag, not errs, errs[:2]); ctx.close()

def signup(br, cls):
    ctx, pg, errs = L.open_page(br, cls, 440, 956, (62, 0, 34, 0), body=L.body_for(AG, (62, 0, 34, 0)) if AG else None)
    tag = "[%s sign-up]" % cls
    pg.evaluate("()=>{ showWelcome(); }"); pg.wait_for_timeout(500)
    pg.evaluate("()=>{ showWelcomeCharacterPrompt(); }"); pg.wait_for_timeout(1500)
    pg.locator(".charselect-panel .avatarchar-option:not(.locked)").nth(1).click(); pg.wait_for_timeout(900)
    r = pg.evaluate("""()=>{ const P=document.querySelector('.charselect-panel'); if(!P) return null;
      const vis=[...P.querySelectorAll('.pick-mark, .avatarchar-check')].filter(m=>+getComputedStyle(m).opacity>.9);
      const o=P.querySelector('.avatarchar-option.selected'); if(!o) return {marks:vis.length};
      const s=getComputedStyle(o), tf=s.transform==='none'?1:(new DOMMatrix(s.transform)).a, m=vis[0];
      const mr=m&&m.getBoundingClientRect(), pr=m&&m.querySelector('path')&&m.querySelector('path').getBoundingClientRect(), ms=m&&getComputedStyle(m);
      return {marks:vis.length, inside:!!m&&o.contains(m), cls:m?m.className:'', scale:Math.round(tf*1000)/1000, filter:s.filter, pool:+getComputedStyle(o,'::before').opacity, ring:+getComputedStyle(o,'::after').opacity,
        w:mr?Math.round(mr.width*10)/10:0, solid:ms?ms.backgroundImage==='none':false, dx:pr?Math.round(((pr.left+pr.right)/2-(mr.left+mr.right)/2)*100)/100:null, dy:pr?Math.round(((pr.top+pr.bottom)/2-(mr.top+mr.bottom)/2)*100)/100:null}; }""")
    chk("%s the pick shows the one mark (the Customize component), solid, its tick centred (%s)" % (tag, r),
        bool(r) and r["marks"] == 1 and r.get("inside") and "pick-mark" in r.get("cls", "") and r["w"] >= 18 and r["solid"] and r["dx"] is not None and abs(r["dx"]) <= .75 and abs(r["dy"]) <= .75, r)
    chk("%s no glow, growth or ring on the pick (%s)" % (tag, r and (r.get("scale"), r.get("filter"), r.get("pool"), r.get("ring"))),
        bool(r) and r.get("scale") == 1 and r.get("filter") in ("none", "") and r.get("pool", 1) < .01 and r.get("ring", 1) < .01, r)
    chk("%s no page errors" % tag, not errs, errs[:2]); ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    for cls in CLS:
        for dev in DEVICES: run_device(br, dev, cls)
        if DUMP: continue
        behaviour(br, cls)
        rotation(br, cls)
        signup(br, cls)
    br.close()
if DUMP:
    json.dump(DUMPED, open(TILES_JSON, "w"), indent=1, sort_keys=True); print("wrote", TILES_JSON, len(DUMPED)); sys.exit(0)
print("\nALL PASS" if ok else "\n%d FAILURES" % nfail)
sys.exit(0 if ok else 1)
