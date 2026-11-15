#!/usr/bin/env python3
"""Build 384 r8: the row tile in Delta's material, its glyphs one family on the middle, and one colour family per Settings card.

Madison, of Delta's purple tile: "Just look at how great this icon looks by the way"; of its grouped cards: "Do you see how their
grouped up stuff has the same color icons?"; of ours: "Our icons aren't centered, icons just need a lot of work".
Read off 3x screenshots (iPhone 17 Pro Max, dpr 3) of the Settings menu in BOTH classes, Profile and Stats (and the iPad Pro 11"
menu), every visible row tile:
(1) the fill is FLAT: the tile sampled near its top and near its bottom (clear of the glyph) within 6 levels on every channel;
(2) (384.110, re-read off two new screenshots: Delta's edge light is WHITE and sits on the top and the bottom - the top's outer
    device pixel ~.55-.6 white, the sides only ~.12 - not a coloured rim all round) the brightest pixel in the tile's outer 3
    device pixels at the middle of its TOP edge is brighter than the fill (HSL lightness, +.08) and brighter than the same read
    half way down its left edge (+.04): the light is along the top, not round the sides;
(3) the glyph's ink (the white drawing, read off the pixels inside the rim) spans 50-68% of the tile on its longer side, and the
    median glyph 57-66% (384.110: Delta's median is 61.7%, from its app grid's 51% to its gamepad's 80%; SF symbols of one size are
    not one box);
(4) ...and its ink box is centred on the tile within .5px both ways;
(5) every glyph part is one stroke: the effective stroke width (vector-effect aside, the stroke times its scale on screen) of
    every part of every glyph is within 15% of the others, and a glyph with no stroke counts as 0;
(6) no glyph is a filled silhouette (the set is outline): a part that paints a fill is a small detail - Delta Sync's solid
    arrowheads - its box under 22% of the tile's side (384.110);
(7) the menu's cards, read off the page (each .settings-card with tiles, in order): inside a card every coloured tile's hue is
    within 75 degrees of the others (384.110: Delta's Controls card is Controllers, Skins, Touch - purple to red, 72 degrees, one
    step - and General takes those three by position); two neighbouring cards are 40+ degrees apart or one is grey; the utility card - the one
    holding the Advanced settings row (.adv-toggle) - is grey (chroma under 16);
(8) no page errors.
  python3 tools/check-b384-tilematerial.py [--against OLD/index.html]   (must FAIL on cd34de2)"""
import io, os, sys, colorsys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
S = 3
IFC_SEED = cb.USED_ACCOUNT[:-1] + ',"publicId":"xph5b57jbp5a","novaMet":99}'
IFC_INIT = "try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.greet.ifc','done');}catch(e){}"
GEOM = """()=>{ const vis=e=>{ const b=e.getBoundingClientRect(); return b.width>0 && b.height>0 && b.top>=0 && b.bottom<=innerHeight; };
  const cards=[...document.querySelectorAll('#stage .screen-settings .settings-card')];
  return [...document.querySelectorAll('#stage .settings-row-icon')].filter(vis).map(t=>{
    const b=t.getBoundingClientRect(), svg=t.querySelector('svg');
    const parts=svg ? [...svg.querySelectorAll('path, circle, rect, line, polyline, polygon, ellipse')] : [];
    const strokes=parts.map(p=>{ const cs=getComputedStyle(p); if(cs.stroke==='none' || !(parseFloat(cs.strokeWidth)>0)) return 0;
      const sw=parseFloat(cs.strokeWidth); if(cs.vectorEffect==='non-scaling-stroke') return sw; const m=p.getScreenCTM(); return sw*Math.sqrt(Math.abs(m.a*m.d-m.b*m.c)); });
    const filled=parts.filter(p=>{ const f=getComputedStyle(p).fill; if(!(f && f!=='none' && !/rgba\\([^)]*,\\s*0\\)$/.test(f))) return false;
      const bb=p.getBBox(), m=p.getScreenCTM(), sc=Math.sqrt(Math.abs(m.a*m.d-m.b*m.c)); return Math.max(bb.width, bb.height)*sc > .22*b.width; }).length;
    const card=t.closest('.screen-settings .settings-card');
    return { k:t.dataset.tile, b:[b.left,b.top,b.width], strokes, filled, nparts: parts.length,
             card: card ? cards.indexOf(card) : -1, util: !!(card && card.querySelector('.adv-toggle')) }; }); }"""
def hls(c): return colorsys.rgb_to_hls(*(np.array(c[:3]) / 255.0))
def hdist(a, b): return min(abs(a - b), 360 - abs(a - b))
def measure(pg, tag):
    tiles = pg.evaluate(GEOM)
    im = np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert("RGB")).astype(int)
    out = []
    for t in tiles:
        x, y, w = t["b"]
        X0, Y0, W = int(round(x * S)), int(round(y * S)), int(round(w * S))
        reg = im[Y0:Y0 + W, X0:X0 + W]
        if reg.shape[0] < W or reg.shape[1] < W: continue
        top, bot = reg[int(W * .16), int(W * .16)], reg[int(W * .84), int(W * .16)]
        edge = reg[W // 2 - 1:W // 2 + 2, 0:3].reshape(-1, 3)
        rim = edge[np.argmax(edge.sum(axis=1))]
        tedge = reg[0:3, W // 2 - 1:W // 2 + 2].reshape(-1, 3)
        trim = tedge[np.argmax(tedge.sum(axis=1))]
        inner = reg[9:W - 9, 9:W - 9]
        fl = top.mean(); m = (inner.mean(axis=2) - fl) > .5 * (255 - fl)
        ys, xs = np.nonzero(m)
        if len(xs):
            x0, x1, y0, y1 = xs.min() + 9, xs.max() + 10, ys.min() + 9, ys.max() + 10
            dx, dy = ((x0 + x1) / 2 - W / 2) / S, ((y0 + y1) / 2 - W / 2) / S
            ext = max(x1 - x0, y1 - y0) / W
        else: dx = dy = ext = None
        t.update({"tag": tag, "top": top.tolist(), "bot": bot.tolist(), "rim": rim.tolist(), "trim": trim.tolist(), "dx": dx, "dy": dy, "ext": ext})
        out.append(t)
    return out
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    allt, menus, errs = [], [], []
    for cls, w, h, screens in (("academy", 440, 956, ["showAppearance()", "showProfile('profile')", "showProfile('stats')"]),
                               ("ifc", 440, 956, ["showAppearance()", "showProfile('profile')", "showProfile('stats')"]),
                               ("academy", 834, 1194, ["showAppearance()"])):
        ctx, pg = cb.booted(br, w, h, seed=(IFC_SEED if cls == "ifc" else cb.USED_ACCOUNT), init=(IFC_INIT if cls == "ifc" else None), dpr=S)
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} }")
        for s in screens:
            pg.evaluate("()=>{ %s; window.scrollTo(0,0); }" % s); pg.wait_for_timeout(1300)
            pg.evaluate("()=>document.querySelectorAll('.rs-spot,#tour-overlay,#tour-tooltip,#tour-line,#tour-line-dot').forEach(n=>n.remove())")
            got, seen = [], set()
            # walk down the page so every tile is measured on screen, once
            for step in range(6):
                for t in measure(pg, "%s %dx%d %s" % (cls, w, h, s)):
                    key = (t["k"], t["card"])
                    if key in seen: continue
                    seen.add(key); got.append(t)
                more = pg.evaluate("()=>{ const y=window.scrollY; window.scrollTo({top:y+innerHeight*.6, behavior:'instant'}); return window.scrollY>y; }")
                if not more: break
                pg.wait_for_timeout(350)
            allt += got
            if s == "showAppearance()": menus.append((cls, w, got))
        ctx.close()
    br.close()
cb.SERVER.shutdown()
bad = {i: [] for i in range(1, 8)}
for t in allt:
    nm = "%s / %s" % (t["tag"], t["k"])
    if max(abs(a - b) for a, b in zip(t["top"], t["bot"])) > 6: bad[1].append((nm, t["top"], t["bot"]))
    rf, rr, rt = hls(t["top"]), hls(t["rim"]), hls(t["trim"])
    if not (rt[1] > rf[1] + .08 and rt[1] > rr[1] + .04): bad[2].append((nm, "fill", t["top"], "top edge", t["trim"], "side", t["rim"]))
    if t["ext"] is None or not (.50 <= t["ext"] <= .68): bad[3].append((nm, t["ext"] and round(t["ext"], 3)))
    if t["dx"] is None or abs(t["dx"]) > .5 or abs(t["dy"]) > .5: bad[4].append((nm, t["dx"], t["dy"]))
    if t["filled"]: bad[6].append((nm, "%d filled part(s)" % t["filled"]))
sw = [v for t in allt for v in (t["strokes"] or [0])]
spread = (round(min(sw), 3), round(max(sw), 3)) if sw else None
if not (sw and min(sw) > 0 and all(abs(v - np.median(sw)) <= .15 * np.median(sw) for v in sw)):
    bad[5].append(("stroke widths (min, median, max)", spread and (spread[0], round(float(np.median(sw)), 3), spread[1]),
                   sorted(set((t["k"], round(v, 2)) for t in allt for v in (t["strokes"] or [0]) if abs(v - np.median(sw)) > .15 * np.median(sw)))[:8]))
for cls, w, tiles in menus:
    cards = {}
    for t in tiles: cards.setdefault(t["card"], []).append(t)
    order = sorted(c for c in cards if c >= 0)
    fam = {}
    for c in order:
        cols = [t["top"] for t in cards[c]]
        grey = [max(cc) - min(cc) < 16 for cc in cols]
        hues = [hls(cc)[0] * 360 for cc, g in zip(cols, grey) if not g]
        if hues:
            span = max(hdist(a, b) for a in hues for b in hues)
            if span > 75: bad[7].append((cls, w, "card %d spans %d degrees" % (c, span), [t["k"] for t in cards[c]], [round(x) for x in hues]))
        fam[c] = None if all(grey) else (hues[0] if hues else None)
        if any(t["util"] for t in cards[c]) and not all(grey): bad[7].append((cls, w, "the utility card is not grey", [(t["k"], t["top"]) for t in cards[c]]))
    for a, b in zip(order, order[1:]):
        if fam[a] is not None and fam[b] is not None and hdist(fam[a], fam[b]) < 40:
            bad[7].append((cls, w, "cards %d and %d one family" % (a, b), round(fam[a]), round(fam[b])))
    if not any(t["util"] for t in tiles): bad[7].append((cls, w, "no utility card found"))
print("tiles measured: %d (%s)" % (len(allt), sorted(set(t["k"] for t in allt))))
print("ink extents:", sorted(set(round(t["ext"], 3) for t in allt if t["ext"])), " stroke widths:", spread)
chk("(1) every tile's fill is flat (top and bottom within 6 levels)", allt and not bad[1], bad[1][:6])
chk("(2) every tile's edge is lit along the top: brighter than its fill and than its sides (384.110)", allt and not bad[2], bad[2][:6])
exts = [t["ext"] for t in allt if t["ext"]]
med = float(np.median(exts)) if exts else 0
chk("(3) every glyph's ink spans 50-68%% of its tile, the median 57-66%% (%.3f)" % med, allt and not bad[3] and .57 <= med <= .66, bad[3][:8])
chk("(4) every glyph's ink is centred on its tile within .5px", allt and not bad[4], bad[4][:8])
chk("(5) one stroke weight: every glyph part's stroke within 15% of the rest, none missing", allt and not bad[5], bad[5][:4])
chk("(6) no filled glyph (the set is outline; a solid arrowhead is a detail under 22% of the tile)", allt and not bad[6], bad[6][:6])
chk("(7) Settings menu: one colour family per card, neighbours differ, the utility card grey", menus and not bad[7], bad[7][:6])
chk("(8) no page errors", not errs, errs[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
