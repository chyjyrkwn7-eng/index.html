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
  (P5) character section headings are centred;
  (P6) exactly one tile is marked as on, with a tick you can see; every locked tile has its padlock;
  (P7) scrolled to the end, the last tile clears the tab bar; no horizontal scroll; a tile is a tap target (44px);
  (P8) a laptop's tiles are not tiny (a character's picture at least 72px on a tablet or laptop);
 BEHAVIOUR unchanged (phone, academy): tapping a character wears it, tapping a locked one opens its card, a hold opens the card.
Run:  python3 tools/check-b384-custom.py [--quick] [--class academy|ifc] [--against OLD/index.html]   (the old build must FAIL)"""
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
ok = True; nfail = 0
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
        if kind == "character":
            chk("%s (P5) the section headings are centred (%s)" % (t, r["headTitles"]), len(r["headTitles"]) >= 2 and all(near(v, 0, 2) for v in r["headTitles"]), r["headTitles"])
        chk("%s (P6) exactly one is on and it shows its tick (%d, %d); every locked tile has its padlock (%d of %d)" % (t, r["on"], r["ticks"], r["locks"], r["locked"]),
            r["on"] == 1 and r["ticks"] == 1 and r["locked"] == r["locks"], [r["on"], r["ticks"], r["locked"], r["locks"]])
        chk("%s (P7) the end clears the tab bar (%spx), no horizontal scroll, tiles are 44px targets (%s)" % (t, r["endClear"], r["picMin"]),
            r["endClear"] >= -0.5 and r["hscroll"] <= 0 and r["hscroll2"] <= 0 and r["picMin"] >= 44, [r["endClear"], r["hscroll"], r["hscroll2"], r["picMin"]])
        if kind == "character" and W >= 700:
            chk("%s (P8) the characters are not tiny on a big screen (%spx)" % (t, r["picMin"]), r["picMin"] >= 72, r["picMin"])
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
    chk("%s no page errors" % tag, not errs, errs[:2]); ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    for cls in CLS:
        for dev in DEVICES: run_device(br, dev, cls)
        behaviour(br, cls)
    br.close()
print("\nALL PASS" if ok else "\n%d FAILURES" % nfail)
sys.exit(0 if ok else 1)
