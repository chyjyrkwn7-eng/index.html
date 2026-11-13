#!/usr/bin/env python3
"""Build 384.110: Settings in Delta's look on the glass - the fourth round, measured off two new screenshots of Delta's Settings.

Madison: "I can't really put my finger on it but Delta still looks so much better than ours ... evaluate this extremely closely, the
exact look and feel of theirs and make ours better." Delta's numbers (2.695px/pt; docs/notes-archive.md 384.110 has the table) are
the targets. Everything is read off the page in POINTS ON THE GLASS (CSS px x the zoom an element carries x screen/layout width), on an
installed iPhone 17 Pro Max at 100% (440 CSS px on 440pt) and at his ~85% page zoom (518 CSS px on 440pt):
 (1) cards: corners 25.5-26.5pt, 19.5-20.5pt in from the screen's edges, a neutral grey fill (Delta's #2C2C2E: each channel
     within 4, chroma under 4);
 (2) rows: pitch 50.5-51.5pt, tile 27.5-28.5pt, the tile 17-18.3pt in from the card's edge, the words 13.5-14.6pt after the tile,
     the chevron's ink 21.6-23pt in from the card's right edge, 5.9-6.8 x 10.3-11.3pt, a neutral grey at 25-40%;
 (3) type: row words 15.8-16.3pt at 400, values 15.8-16.3pt in a neutral grey, section names 15.8-16.3pt at 600 in a neutral grey,
     footnotes 11.8-12.3pt on a 15.5-16.6pt line, the large title 32.5-33.6pt at 700, a page's title 16.7-17.3pt at 600; the font
     stack opens with the system face (-apple-system / system-ui);
 (4) the tile's material: a flat fill (::after, one colour), a keyline OUTSIDE the tile (::before larger than the tile and darker
     than the card), a lit edge brighter at the top and the bottom than down the sides (the rim layer's gradient), a continuous
     corner (the mask is drawn with curves); every glyph part one stroke of 1.18-1.36pt on the glass, the glyph's ink centred on
     the tile within .6pt, and the median glyph's longer side 57-66% of the tile (Delta's: 61.7%);
 (5) the hairline between two rows starts at the words (within 1pt), ends 19.3-20.7pt short of the card's right edge, and is at
     most .8pt thick, white 8-16%;
 (6) the header: at rest no bar shows; scrolled past the large title a bar does - its top at the inset (never within 4px of the
     top on a notched phone: the status bar's strip stays the one thing WebKit samples there), no background-colour of its own, its
     foot 7-11pt under the chat button's, the large title's words centred on the screen (1pt) and on the chat button's middle
     (1.5pt), a hairline at its foot; on a page that scrolls (Contributors) the back button stays where it rests and the bar shows
     behind it;
 (7) a status pill (settingsPill): 19.5-20.6pt tall, a capsule, white bold 10.8-11.3pt words, the green tone Delta's #68CE68;
 (8) no page errors.
(1)-(5) and (7) are read at both zooms; (6) at both.
  python3 tools/check-b384-settingslook.py [--against OLD/index.html]   (must FAIL on 384.95)"""
import os, re, sys, json, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_toprow_lib as L
from playwright.sync_api import sync_playwright
SRC = os.path.join(os.path.dirname(HERE), "index.html")
if "--against" in sys.argv: SRC = sys.argv[sys.argv.index("--against") + 1]
RAW = open(SRC, encoding="utf-8").read()
ok = True
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:600]), flush=True)
def go(pg, call, wait=1500):
    pg.evaluate(call); pg.wait_for_timeout(wait)
    pg.evaluate("()=>{ document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n=>n.remove()); const de=document.documentElement; de.style.scrollBehavior='auto'; scrollTo(0,0); }")
    pg.wait_for_timeout(500)
COMMON = r"""
  const k = screen.width / innerWidth, cs = (e, p) => getComputedStyle(e, p || null);
  const zoomOf = e => { let z = 1; for(let n = e; n && n.nodeType === 1; n = n.parentElement){ const v = parseFloat(cs(n).zoom); if(v && v !== 1) z *= v; } return z; };
  const pt = v => v * k;
  const rgb = s => { const m = (s || '').match(/[\d.]+/g); if(!m) return null; const v = m.slice(0, 4).map(Number); if(/^color\(/.test(s)) return [v[0]*255, v[1]*255, v[2]*255, v.length > 3 ? v[3] : 1]; return [v[0], v[1], v[2], v.length > 3 ? v[3] : 1]; };
  const fpt = e => parseFloat(cs(e).fontSize) * zoomOf(e) * k;
"""
MENU = r"""()=>{ """ + COMMON + r"""
  const out = { cards: [], rows: [], tiles: [], hair: [], errs: [] };
  const st = document.getElementById('stage');
  const cards = [...st.querySelectorAll('.screen-settings .settings-card.settings-menu-card')].filter(c => c.getClientRects().length);
  for(const c of cards){ const r = c.getBoundingClientRect(); out.cards.push({ radius: parseFloat(cs(c).borderTopLeftRadius) * zoomOf(c) * k, fill: rgb(cs(c).backgroundColor), img: cs(c).backgroundImage, left: pt(r.left), right: pt(innerWidth - r.right) }); }
  const rows = [...st.querySelectorAll('.screen-settings .settings-menu-card > .settings-row')].filter(e => e.getClientRects().length && e.querySelector('.settings-row-icon'));
  for(let i = 0; i < rows.length; i++){
    const r = rows[i], rr = r.getBoundingClientRect(), card = r.closest('.settings-card').getBoundingClientRect();
    const t = r.querySelector('.settings-row-icon'), tr = t.getBoundingClientRect();
    const lab = r.querySelector('.settings-row-label'), g = document.createRange(); g.selectNodeContents(lab); const lr = g.getClientRects()[0];
    const chev = r.querySelector('.settings-row-chev svg'); let ch = null;
    if(chev){ const p = chev.querySelector('path'), b = p.getBBox(), m = p.getScreenCTM(), sw = parseFloat(cs(p).strokeWidth) * Math.hypot(m.a, m.b);
      const x0 = m.a * b.x + m.e - sw / 2, x1 = m.a * (b.x + b.width) + m.e + sw / 2, y0 = m.d * b.y + m.f - sw / 2, y1 = m.d * (b.y + b.height) + m.f + sw / 2;
      ch = { w: pt(x1 - x0), h: pt(y1 - y0), right: pt(card.right - x1), color: rgb(cs(chev).color), op: parseFloat(cs(r.querySelector('.settings-row-chev')).opacity) }; }
    const v = r.querySelector('.settings-row-value');
    out.rows.push({ top: pt(rr.top), h: pt(rr.height), tile: pt(tr.width), tileIn: pt(tr.left - card.left), wordsAfter: pt(lr.left - tr.right), label: fpt(lab), weight: cs(lab).fontWeight,
      family: cs(lab).fontFamily, value: v ? { size: fpt(v), color: rgb(cs(v).color) } : null, ch, sub: !!r.querySelector('.settings-row-sub') });
    if(i > 0 && r.previousElementSibling === rows[i - 1]){ const b = cs(r, '::before'), z = zoomOf(r);
      out.hair.push({ left: pt(rr.left + parseFloat(b.left) * z), wordsLeft: pt(lr.left), right: pt(card.right - (rr.right - parseFloat(b.right) * z)), h: parseFloat(b.height) * z * k, color: rgb(b.backgroundColor) }); }
  }
  for(const t of [...st.querySelectorAll('.settings-row-icon')].filter(e => e.getClientRects().length)){
    const tr = t.getBoundingClientRect(), be = cs(t, '::before'), af = cs(t, '::after'), z = zoomOf(t);
    const svgs = [...t.querySelectorAll(':scope > svg')], gl = svgs[0], rim = svgs[1];
    const parts = gl ? [...gl.querySelectorAll('path, circle, rect, line, polyline, polygon, ellipse')] : [];
    const strokes = parts.map(p => { const c = cs(p); if(c.stroke === 'none' || !(parseFloat(c.strokeWidth) > 0)) return 0; const m = p.getScreenCTM(); return parseFloat(c.strokeWidth) * Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) * k; });
    let ink = null;
    if(gl){ let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for(const p of parts){ if(p.closest('clipPath, defs')) continue; const b = p.getBBox(), m = p.getScreenCTM(), sw = parseFloat(cs(p).strokeWidth) * Math.hypot(m.a, m.b) / 2;
        const xs = [m.a * b.x + m.c * b.y + m.e, m.a * (b.x + b.width) + m.c * (b.y + b.height) + m.e], ys = [m.b * b.x + m.d * b.y + m.f, m.b * (b.x + b.width) + m.d * (b.y + b.height) + m.f];
        x0 = Math.min(x0, ...xs) ; x1 = Math.max(x1, ...xs); y0 = Math.min(y0, ...ys); y1 = Math.max(y1, ...ys); x0 -= 0; }
      const sw = strokes.length ? Math.max(...strokes) / k / 2 : 0; x0 -= sw; y0 -= sw; x1 += sw; y1 += sw;
      ink = { long: Math.max(x1 - x0, y1 - y0) / tr.width, dx: pt((x0 + x1) / 2 - (tr.left + tr.width / 2)), dy: pt((y0 + y1) / 2 - (tr.top + tr.height / 2)) }; }
    let rimGrad = null;
    if(rim){ const lg = [...rim.querySelectorAll('linearGradient')].map(g => [...g.querySelectorAll('stop')].map(s => [parseFloat(s.getAttribute('offset')), parseFloat(s.getAttribute('stop-opacity') || '1')]));
      rimGrad = lg; }
    const mask = (af.webkitMaskImage && af.webkitMaskImage !== 'none') ? af.webkitMaskImage : af.maskImage;
    out.tiles.push({ kind: t.dataset.tile, w: pt(tr.width), beforeInset: parseFloat(be.top) * z * k, beforeBg: be.backgroundImage + ' ' + be.backgroundColor, afterBg: rgb(af.backgroundColor), afterImg: af.backgroundImage,
      mask: (mask || '').slice(0, 400), strokes, ink, rimGrad, nsvg: svgs.length });
  }
  const heads = [...st.querySelectorAll('.screen-settings .slab.motion-summary')].filter(e => e.getClientRects().length);
  out.heads = heads.map(h => ({ size: fpt(h), weight: cs(h).fontWeight, color: rgb(cs(h).color) }));
  const c = document.getElementById('count'); out.title = { size: fpt(c), weight: cs(c).fontWeight, family: cs(c).fontFamily, text: c.textContent.trim() };
  out.card = rgb(cs(cards[0]).backgroundColor);
  return out; }"""
BAR = r"""(phase)=>{ """ + COMMON + r"""
  const b = document.getElementById('settings-bar'), chat = document.getElementById('chatdock-btn'), cr = chat ? chat.getBoundingClientRect() : null;
  if(!b) return { exists: false };
  const s = cs(b), r = b.getBoundingClientRect(), t = b.querySelector('.settings-bar-title'), tr = t ? t.getBoundingClientRect() : null, a = cs(b, '::after');
  return { exists: true, on: s.visibility === 'visible' && parseFloat(s.opacity) > .95, top: r.top, bottom: r.bottom, bg: s.backgroundColor, img: s.backgroundImage, sat: parseFloat(cs(document.documentElement).getPropertyValue('--sat')) || 0,
    chatBottom: cr ? cr.bottom : null, chatMid: cr ? cr.top + cr.height / 2 : null, title: t ? t.textContent : '', titleSize: t ? fpt(t) : 0, titleWeight: t ? cs(t).fontWeight : '',
    titleMid: tr ? tr.left + tr.width / 2 : null, titleMidY: tr ? tr.top + tr.height / 2 : null, W: innerWidth, k, hair: parseFloat(a.height) > 0 && a.content !== 'none', pe: s.pointerEvents };
}"""
PAGE = r"""()=>{ """ + COMMON + r"""
  const st = document.getElementById('stage'), out = {};
  const nt = st.querySelector('.settings-nav-title'); out.nav = nt ? { size: fpt(nt), weight: cs(nt).fontWeight } : null;
  const fn = st.querySelector('.settings-footnote'); out.foot = fn ? { size: fpt(fn), line: parseFloat(cs(fn).lineHeight) * zoomOf(fn) * k, color: rgb(cs(fn).color) } : null;
  return out; }"""
def gray(c, tol=4): return c and max(c[:3]) - min(c[:3]) <= tol
def open_page(br, raw, devkey):
    """b384_toprow_lib.open_page with a patient load (the gates share a busy machine)"""
    name, w, h, ins, installed, ua, notched = L.DEVICES[devkey]
    scr = {"width": 440, "height": 956} if devkey == "zoom85" else {"width": w, "height": h}
    ctx = br.new_context(viewport={"width": w, "height": h}, screen=scr, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    if installed: ctx.add_init_script(L.g["STANDALONE"])
    ctx.add_init_script(L.g["FAKE_FIREBASE"].replace("__ROWS__", L.g["rows_json"]()))
    ctx.add_init_script(L.INIT % (json.dumps(json.dumps(L.seed())), ""))
    pg = ctx.new_page(); body = L.body_for(raw, ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    mm = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = mm.group(1) if mm else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(L.url(), timeout=150000); pg.wait_for_timeout(3500); pg.evaluate(L.QUIET); pg.wait_for_timeout(300)
    return ctx, pg, errs
def run(pw, dev):
    br = pw.chromium.launch(executable_path=L.CHROME)
    ctx, pg, errs = open_page(br, RAW, dev)
    tag = "[%s] " % ("100%" if dev == "promax" else "85%")
    go(pg, "()=>showAppearance()")
    m = pg.evaluate(MENU)
    cards = m["cards"]
    chk(tag + "(1) the menu's cards: corners 25.5-26.5pt (%s)" % [round(c["radius"], 1) for c in cards], cards and all(25.5 <= c["radius"] <= 26.5 for c in cards), cards[:2])
    chk(tag + "(1) ...20pt in from the screen's edges, as Delta's (%s)" % [(round(c["left"], 1), round(c["right"], 1)) for c in cards[:1]], cards and all(19.5 <= c["left"] <= 20.5 and 19.5 <= c["right"] <= 20.5 for c in cards), cards[:1])
    f = m["card"]
    chk(tag + "(1) ...and a neutral grey fill, Delta's #2C2C2E (%s, image %s)" % (f and [round(v) for v in f[:3]], cards and cards[0]["img"][:30]),
        f and all(abs(f[i] - (44, 44, 46)[i]) <= 4 for i in range(3)) and max(f[:3]) - min(f[:3]) <= 4 and all(c["img"] == "none" for c in cards), cards[:1])
    rows = m["rows"]
    one = [r for r in rows if not r["sub"]]
    pitches = [round(r["h"], 2) for r in one]
    chk(tag + "(2) rows: one-line rows 50.5-51.5pt (%s)" % pitches[:6], one and all(50.5 <= p <= 51.5 for p in pitches), pitches)
    chk(tag + "(2) tiles 27.5-28.5pt, 17-18.3pt in from the card's edge, words 13.5-14.6pt after (%s / %s / %s)" % (sorted({round(r["tile"], 1) for r in rows}), sorted({round(r["tileIn"], 1) for r in rows}), sorted({round(r["wordsAfter"], 1) for r in rows})),
        rows and all(27.5 <= r["tile"] <= 28.5 and 17 <= r["tileIn"] <= 18.3 and 13.5 <= r["wordsAfter"] <= 14.6 for r in rows), rows[:2])
    chs = [r["ch"] for r in rows if r["ch"]]
    chk(tag + "(2) the chevron's ink 21.6-23pt in from the card's right edge, 5.9-6.8 x 10.3-11.3pt, neutral grey at 25-40%% (%s)" % [(round(c["right"], 1), round(c["w"], 1), round(c["h"], 1)) for c in chs[:2]],
        chs and all(21.6 <= c["right"] <= 23 and 5.9 <= c["w"] <= 6.8 and 10.3 <= c["h"] <= 11.3 and gray(c["color"], 12) and .25 <= c["color"][3] * c["op"] <= .4 for c in chs), chs[:2])
    chk(tag + "(3) row words 15.8-16.3pt at 400 (%s)" % sorted({(round(r["label"], 2), r["weight"]) for r in rows}), rows and all(15.8 <= r["label"] <= 16.3 and r["weight"] == "400" for r in rows))
    vals = [r["value"] for r in rows if r["value"]]
    chk(tag + "(3) values 15.8-16.3pt in a neutral grey (%s)" % [(round(v["size"], 2), [round(x) for x in v["color"][:3]]) for v in vals[:2]],
        vals and all(15.8 <= v["size"] <= 16.3 and gray(v["color"], 12) for v in vals), vals[:2])
    hs = m["heads"]
    chk(tag + "(3) section names 15.8-16.3pt at 600 in a neutral grey (%s)" % sorted({(round(h["size"], 2), h["weight"]) for h in hs}),
        hs and all(15.8 <= h["size"] <= 16.3 and h["weight"] == "600" and gray(h["color"], 12) for h in hs), hs[:2])
    t = m["title"]
    chk(tag + "(3) the large title 32.5-33.6pt at 700 (%.2f, %s)" % (t["size"], t["weight"]), 32.5 <= t["size"] <= 33.6 and t["weight"] == "700", t)
    fam = rows[0]["family"] if rows else ""
    chk(tag + "(3) the font stack opens with the system face (%s)" % fam[:40], re.match(r"\s*(-apple-system|system-ui)", fam or "") and re.match(r"\s*(-apple-system|system-ui)", t["family"] or ""), [fam, t["family"]])
    tiles = [x for x in m["tiles"] if x["w"] > 20]
    flat = all(x["afterBg"] and x["afterBg"][3] > .99 and x["afterImg"] == "none" for x in tiles)
    keyline = all(x["beforeInset"] < -.25 and x["beforeInset"] > -.8 and ("rgba(0, 0, 0" in x["beforeBg"] or "rgb(0, 0, 0" in x["beforeBg"]) for x in tiles)
    chk(tag + "(4) every tile: a flat fill, a dark keyline .25-.8pt outside it (%s)" % sorted({round(x["beforeInset"], 2) for x in tiles}), tiles and flat and keyline, tiles[:1])
    def lit(g):
        if not g: return False
        best = False
        for stops in g:
            if len(stops) < 3: continue
            ends = [o for off, o in stops if off <= .02 or off >= .98]; mids = [o for off, o in stops if .3 <= off <= .7]
            if ends and min(ends) >= .4 and (not mids or max(mids) <= .2): best = True
        return best
    chk(tag + "(4) every tile has its lit edge: bright (.4+) at the top and the bottom, faint (.2-) down the sides", tiles and all(x["nsvg"] >= 2 and lit(x["rimGrad"]) for x in tiles), [x["rimGrad"] for x in tiles[:1]])
    chk(tag + "(4) every tile's corner is a continuous curve (the mask is drawn with curves, not a polygon)", tiles and all(re.search(r"path d=.?M[^']*C", x["mask"]) for x in tiles), [x["mask"][:120] for x in tiles[:1]])
    strokes = [s for x in tiles for s in x["strokes"]]
    chk(tag + "(4) every glyph part one stroke of 1.18-1.36pt on the glass (%s)" % (strokes and [round(min(strokes), 3), round(max(strokes), 3)]), strokes and all(1.18 <= s <= 1.36 for s in strokes), sorted(set(round(s, 3) for s in strokes))[:6])
    inks = [x["ink"] for x in tiles if x["ink"]]
    med = statistics.median([i["long"] for i in inks]) if inks else 0
    off = [round(max(abs(i["dx"]), abs(i["dy"])), 2) for i in inks]
    chk(tag + "(4) glyphs centred within .6pt (%s) and the median one's longer side 57-66%% of the tile (%.3f)" % (max(off) if off else None, med), inks and max(off) <= .6 and .57 <= med <= .66, [(x["kind"], x["ink"]) for x in tiles][:4])
    hl = m["hair"]
    chk(tag + "(5) hairlines from the words (1pt), 19.3-20.7pt short of the card's right edge, at most .8pt, white 8-16%% (%s)" % [(round(h["left"] - h["wordsLeft"], 1), round(h["right"], 1), round(h["h"], 2)) for h in hl[:2]],
        hl and all(abs(h["left"] - h["wordsLeft"]) <= 1 and 19.3 <= h["right"] <= 20.7 and h["h"] <= .8 and h["color"] and min(h["color"][:3]) > 240 and .08 <= h["color"][3] <= .16 for h in hl), hl[:2])
    b0 = pg.evaluate(BAR, "rest")
    chk(tag + "(6) at rest no bar shows", (not b0.get("exists")) or not b0["on"], b0)
    # scroll past the large title
    pg.evaluate("()=>{ const c=document.getElementById('count'); const de=document.documentElement; de.style.scrollBehavior='auto'; scrollTo(0, Math.ceil(c.getBoundingClientRect().bottom + scrollY) + 30); }")
    pg.wait_for_timeout(900)
    b1 = pg.evaluate(BAR, "scrolled")
    good = b1.get("exists") and b1["on"]
    chk(tag + "(6) scrolled past the large title, the bar shows", good, b1)
    if good:
        K = b1["k"]
        chk(tag + "(6) the bar starts at the inset (%.1f; inset %.1f), never within 4px of the top on a notched phone, with no background-colour of its own (%s) and no touch (%s)" % (b1["top"], b1["sat"], b1["bg"], b1["pe"]),
            abs(b1["top"] - b1["sat"]) <= .6 and b1["top"] > 4 and re.search(r"rgba\(0, 0, 0, 0\)|transparent", b1["bg"]) and b1["img"] != "none" and b1["pe"] == "none", b1)
        chk(tag + "(6) its foot 7-11pt under the chat button's (%.1f), a hairline there (%s)" % ((b1["bottom"] - b1["chatBottom"]) * K, b1["hair"]), 7 <= (b1["bottom"] - b1["chatBottom"]) * K <= 11 and b1["hair"], b1)
        chk(tag + "(6) the inline title is the large title's words (%r), 16.7-17.3pt at 600 (%.2f), centred on the screen (%.2fpt) and on the chat button's middle (%.2fpt)" % (b1["title"], b1["titleSize"], (b1["titleMid"] - b1["W"] / 2) * K, (b1["titleMidY"] - b1["chatMid"]) * K),
            b1["title"] == t["text"] and 16.7 <= b1["titleSize"] <= 17.3 and b1["titleWeight"] == "600" and abs(b1["titleMid"] - b1["W"] / 2) * K <= 1 and abs(b1["titleMidY"] - b1["chatMid"]) * K <= 1.5, b1)
    go(pg, "()=>showCredits()")
    back0 = pg.evaluate("()=>{ const b=document.querySelector('#stage .settings-nav-back'); const r=b.getBoundingClientRect(); return [r.left, r.top]; }")
    pg.evaluate("()=>{ const de=document.documentElement; de.style.scrollBehavior='auto'; scrollTo(0, 320); }"); pg.wait_for_timeout(900)
    back1 = pg.evaluate("()=>{ const b=document.querySelector('#stage .settings-nav-back'); const r=b.getBoundingClientRect(); const n=b.parentElement, bar=document.getElementById('settings-bar'); return [r.left, r.top, scrollY, +getComputedStyle(n).zIndex || 0, bar ? (+getComputedStyle(bar).zIndex || 0) : 1e9]; }")
    b2 = pg.evaluate(BAR, "page")
    chk(tag + "(6) a page that scrolls (Contributors, scrolled %dpx): its back button stays where it rests (%s -> %s) and the bar shows behind it" % (back1[2], [round(v, 1) for v in back0], [round(v, 1) for v in back1[:2]]),
        back1[2] > 100 and abs(back1[0] - back0[0]) <= .5 and abs(back1[1] - back0[1]) <= .5 and b2.get("exists") and b2["on"] and back1[3] > back1[4], [back0, back1, b2])
    go(pg, "()=>showAdvancedSettings()")
    p = pg.evaluate(PAGE)
    chk(tag + "(3) a page's title 16.7-17.3pt at 600 (%s)" % (p["nav"],), p["nav"] and 16.7 <= p["nav"]["size"] <= 17.3 and p["nav"]["weight"] == "600", p)
    chk(tag + "(3) footnotes 11.8-12.3pt on a 15.5-16.6pt line, neutral grey (%s)" % ((p["foot"] and (round(p["foot"]["size"], 2), round(p["foot"]["line"], 2))),),
        p["foot"] and 11.8 <= p["foot"]["size"] <= 12.3 and 15.5 <= p["foot"]["line"] <= 16.6 and gray(p["foot"]["color"], 12), p)
    pill = pg.evaluate("""()=>{ if(typeof settingsPill !== 'function') return null; const host=document.querySelector('#stage .settings-card') || document.body;
      const p=settingsPill('Up-to-date', 'green'); host.appendChild(p); const r=p.getBoundingClientRect(), s=getComputedStyle(p), k=screen.width/innerWidth;
      let z=1; for(let n=p; n && n.nodeType===1; n=n.parentElement){ const v=parseFloat(getComputedStyle(n).zoom); if(v && v!==1) z*=v; }
      const out={ h:r.height*k, w:r.width*k, radius:parseFloat(s.borderTopLeftRadius)*z*k, size:parseFloat(s.fontSize)*z*k, weight:s.fontWeight, color:s.color, bg:s.backgroundColor }; p.remove(); return out; }""")
    chk(tag + "(7) a status pill: 19.5-20.6pt tall, a capsule, white bold 10.8-11.3pt words, green #68CE68 (%s)" % (pill,),
        pill and 19.5 <= pill["h"] <= 20.6 and pill["radius"] >= pill["h"] / 2 - .5 and 10.8 <= pill["size"] <= 11.3 and int(pill["weight"]) >= 700 and pill["color"] == "rgb(255, 255, 255)" and pill["bg"] == "rgb(104, 206, 104)", pill)
    chk(tag + "(8) no page errors", not errs, errs)
    ctx.close(); br.close()
with sync_playwright() as pw:
    for dev in ("promax", "zoom85"):
        run(pw, dev)
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
