"""Build 384, round 3: the 100% grade card is the SAME COMPONENT as the Pass / Fail grade card, through every part of it, in every effect.
Madison: "Do the hundo effects go with the failed and pass thing now? Like even the number 100 and the bar?"
Real 100% runs (a drill through summarize(), the recorder's own clock so a still is a chosen moment), Fire Code and the academy, every rung
(confetti + the four effects), phone 440x956 and tablet 834x1194, read at the MIDDLE of the effect and SETTLED, next to a real Pass card:
 (G1) same component: the kicker, the big number, its raised %, the fraction, the sub line and the unit name have the Pass card's face, size,
      weight and spacing; the card has the Pass card's radius and padding and the XP card's colour, no border, no shadow; the unit bar's track
      and fill have the Pass bar's height and radius, and the fill carries no shadow or border;
 (G2) the colour is ONE RAMP: the 100's gradient is the effect's three stops (g1, g2, g3 - gold for Confetti) and the unit bar's fill is the SAME
      three stops in the same order (it was g2 > g1, the number's ramp turned round and without its third colour); the number's glow is the
      effect's colour; the light layer on the card is the effect's colour;
 (G3) no frame, ever: sampled every quarter second through the whole effect (phone), nothing painted over the card draws a ring - no border, no
      inset hairline - the colour is light (a soft inner glow) and never an edge. (The Thermal Camera's own display frame is the effect's idea, a
      camera window, and is the one named exception.);
 (G4) the other places an effect shows (Customize's tiles, the unlock pop-up's box, the effect's detail card and its miniature): the number is the
      same ramp, and the miniature's bar is that ramp too, with no border or shadow on any of them.
Run:  python3 tools/check-b384-gradecard.py [--quick]   (--against OLD/index.html must FAIL)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
QUICK = "--quick" in sys.argv
if QUICK: sys.argv.remove("--quick")
import lib_realrun as L
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def stops(img):
    """[(r,g,b)] of every colour stop in a computed gradient"""
    out = []
    for m in re.finditer(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)|color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)", img or ""):
        if m.group(1) is not None: out.append(tuple(round(float(m.group(i))) for i in (1, 2, 3)))
        else: out.append(tuple(round(float(m.group(i)) * 255) for i in (4, 5, 6)))
    return out
def hexrgb(h):
    h = (h or "").strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else None
near = lambda a, b, t=3: a and b and max(abs(x - y) for x, y in zip(a, b)) <= t
GOLD = [hexrgb(c) for c in ("#FFEBC2", "#F6D58E", "#E3AC4C")]
FACE = ("fontFamily", "fontSize", "fontWeight", "letterSpacing", "lineHeight")
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
RING = r"""() => {
  const g = document.querySelector('.rs-grade'); if(!g) return [];
  const gr = g.getBoundingClientRect(), out = [], seen = new Set();
  const eff = el => { let o = 1, e = el; while(e && e !== document.body){ o *= +getComputedStyle(e).opacity; e = e.parentElement; } return o; };
  [...document.querySelectorAll('.hfx-layer, .hfx-ufo-top, .rs-grade')].forEach(root => root.querySelectorAll('*').forEach(e => {
    if(seen.has(e) || e.classList.contains('hfx-tint')) return; seen.add(e);
    const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if(r.width < 40 || r.height < 20) return;
    const bord = parseFloat(cs.borderTopWidth) > 0 && !/, 0\)$|transparent/.test(cs.borderTopColor);
    /* an inset shadow with a spread is a hairline: "0px 0px 0px 1.5px inset" */
    const hair = /(?:rgba?\([^)]*\)|color\([^)]*\))\s+0px\s+0px\s+0px\s+[\d.]*[1-9][\d.]*px\s+inset|inset\s+0px\s+0px\s+0px\s+[\d.]*[1-9][\d.]*px/.test(cs.boxShadow || '');
    if(!bord && !hair) return;
    const ov = Math.max(0, Math.min(r.right, gr.right) - Math.max(r.left, gr.left)) * Math.max(0, Math.min(r.bottom, gr.bottom) - Math.max(r.top, gr.top));
    /* a FRAME is as big as the card (a burst's expanding ring is round and is not one) */
    if(Math.abs(r.width - gr.width) > .1 * gr.width || Math.abs(r.height - gr.height) > .15 * gr.height || ov < .5 * gr.width * gr.height || eff(e) < .08) return;
    out.push((e.className || '').toString().slice(0, 40) + ' ' + (bord ? cs.borderTopWidth + ' ' + cs.borderTopColor : cs.boxShadow.slice(0, 60)));
  }));
  return out;
}"""
def face_same(g, p, tag):
    bad = []
    for part in ("kicker", "pct", "sign", "frac", "sub", "uname"):
        a, b = g.get(part), p.get(part)
        if not a or not b: bad.append(part + " missing"); continue
        for k in FACE:
            if a[k] != b[k]: bad.append("%s.%s %s vs %s" % (part, k, a[k], b[k]))
    c, d, x = g["card"], p["card"], g["xp"]
    for k in ("borderRadius", "paddingTop", "paddingLeft", "width"):
        if k == "width":
            # (384 r6) the LAYOUT widths: in the middle of the effect the XP card has not landed yet (the 100% plays on the
            # centred grade before it), so its box is still at the landing's 1.04 scale
            if abs(c["ow"] - x["ow"]) > .6: bad.append("card width %s vs XP %s" % (c["ow"], x["ow"]))
        elif c[k] != d[k]: bad.append("card.%s %s vs %s" % (k, c[k], d[k]))
    if c["backgroundColor"] != x["backgroundColor"] or c["backgroundImage"] != "none": bad.append("card colour %s / %s vs XP %s" % (c["backgroundColor"], c["backgroundImage"][:40], x["backgroundColor"]))
    if c["borderTopWidth"] != x["borderTopWidth"] or c["borderTopColor"] != x["borderTopColor"] or c["boxShadow"] != "none": bad.append("card edge %s %s %s" % (c["borderTopWidth"], c["borderTopColor"], c["boxShadow"][:40]))
    for part in ("track", "fill"):
        a, b = g[part], p[part]
        if a["h"] != b["h"] or a["borderRadius"] != b["borderRadius"]: bad.append("%s %sx%s r%s vs %sx%s r%s" % (part, a["w"], a["h"], a["borderRadius"], b["w"], b["h"], b["borderRadius"]))
    if g["track"]["backgroundColor"] != p["track"]["backgroundColor"]: bad.append("track colour")
    if g["fill"]["boxShadow"] != "none" or g["fill"]["borderTopWidth"] != "0px": bad.append("fill shadow/border %s %s" % (g["fill"]["boxShadow"][:40], g["fill"]["borderTopWidth"]))
    return bad
def ramp_of(g, fx):
    v = g["vars"]
    return GOLD if fx == "confetti" else [hexrgb(v["--hfx-g1"]), hexrgb(v["--hfx-g2"]), hexrgb(v["--hfx-g3"]) or hexrgb(v["--hfx-g1"])]
def ramp_check(g, fx):
    """(384 r9) Confetti: its gold ramp. Every other effect: ONE HUE - the number's three stops and the bar's are the same ramp,
    light to deep in the effect's own colour (--hfx-b), its middle that colour; the glow its colour; and NO light layer on the box
    (Madison: the box "doesn't change color" on the default, "follow suite with the default way")."""
    import colorsys
    num = stops(g["pct"]["backgroundImage"]); bar = stops(g["fill"]["backgroundImage"])
    glow = stops(g["pct"]["filter"]); b = hexrgb(g["vars"]["--hfx-b"]) if fx != "confetti" else hexrgb("#F6D58E")
    bad = []
    if fx == "confetti":
        if len(num) != 3 or not all(near(a, w) for a, w in zip(num, GOLD)): bad.append("number stops %s want %s" % (num, GOLD))
        if len(bar) != 3 or not all(near(a, w) for a, w in zip(bar, GOLD)): bad.append("bar stops %s want %s" % (bar, GOLD))
        return bad
    hls = lambda c: colorsys.rgb_to_hls(*[v / 255 for v in c])
    hd = lambda a, c: min(abs(hls(a)[0] - hls(c)[0]), 1 - abs(hls(a)[0] - hls(c)[0])) * 360
    if len(num) != 3 or len(bar) != 3 or not all(near(x, y) for x, y in zip(num, bar)): bad.append("number %s and bar %s are not one ramp" % (num, bar))
    elif not near(num[1], b, 6): bad.append("middle stop %s is not the effect's colour %s" % (num[1], b))
    elif not all(hd(c, b) <= 12 for c in num): bad.append("stops %s leave the effect's hue %s" % (num, b))
    elif not (hls(num[0])[1] > hls(num[1])[1] > hls(num[2])[1]): bad.append("stops %s not light to deep" % (num,))
    if not (glow and near(glow[0], b, 3)): bad.append("number glow %s want %s" % (glow, b))
    if g.get("tint"): bad.append("a light layer on the box: %s" % (stops(g["tint"]["backgroundImage"])[:2],))
    return bad

DEVS = [("phone", 440, 956)] + ([] if QUICK else [("tablet", 834, 1194)])
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.cb.CHROME)
    for cls in ("ifc", "academy"):
        for dev, W, H in DEVS:
            ctx, pg, errs = L.open_run(br, cls, W, H, "confetti", 1, "drill", False, dpr=1)
            L.advance(pg, 14); plain = pg.evaluate(L.READ_GRADE); ctx.close()
            chk("%s %s: the Pass card to compare with is a real one" % (cls, dev), plain and "is-pass" in plain["cls"], plain and plain["cls"])
            for fx in IDS:
                ctx, pg, errs = L.open_run(br, cls, W, H, fx, dpr=1)
                L.wait_fx(pg)
                tot = pg.evaluate("(f) => (HUNDO_FX_TOTAL[f] || 3000) / 1000", fx)
                rings = {}
                if dev == "phone":
                    t = 0.0
                    while t < tot * .45:
                        for r in pg.evaluate(RING): rings.setdefault(r.split(" ")[0] + r[len(r.split(" ")[0]):], t)
                        L.advance(pg, .25); t += .25
                    mid = pg.evaluate(L.READ_GRADE)
                    while t < tot + 1.7:
                        for r in pg.evaluate(RING): rings.setdefault(r, t)
                        L.advance(pg, .25); t += .25
                else:
                    L.advance(pg, tot * .45); mid = pg.evaluate(L.READ_GRADE); L.advance(pg, tot * .55 + 1.7)
                done = pg.evaluate(L.READ_GRADE)
                tag = "%s %s %s" % (cls, dev, fx)
                for when, g in (("mid", mid), ("settled", done)):
                    chk("(G1) %s %s: the same component as the Pass card - face, size, weight, spacing, radius, padding, the XP card's colour, no border or shadow, the same bar" % (tag, when),
                        g and "is-perfect" in g["cls"] and not face_same(g, plain, tag), g and face_same(g, plain, tag))
                    chk("(G2) %s %s: the number and the bar are one ramp in the effect's own hue (r9), the glow its colour, no light layer on the box" % (tag, when),
                        g and not ramp_check(g, fx), g and ramp_check(g, fx))
                if dev == "phone":
                    named = {k: v for k, v in rings.items() if not (cls == "ifc" and fx == "bubbles")}
                    chk("(G3) %s: no ring painted over the card at any quarter second of the effect (%s)" % (tag, "the Thermal Camera's display frame is its own idea" if cls == "ifc" and fx == "bubbles" else "colour is light, not an edge"), not named, named)
                if errs: chk("%s: no page errors" % tag, False, errs)
                ctx.close()
    # (G4) the other places
    PROBE4 = r"""() => {
      const rd = e => { const cs = getComputedStyle(e); return { img: cs.backgroundImage, bw: cs.borderTopWidth, bc: cs.borderTopColor, sh: cs.boxShadow, bg: cs.backgroundColor, ff: cs.fontFamily }; };
      const vars = e => { const o = {}; for(let n = e; n && n !== document.body; n = n.parentElement){ ['--hfx-g1','--hfx-g2','--hfx-g3','--hfx-b'].forEach(k => { if(!o[k]){ const v = n.style.getPropertyValue(k).trim(); if(v) o[k] = v; } }); } return o; };
      const out = { stages: [], mock: null };
      document.querySelectorAll('.hfx-stage').forEach(st => { const p = st.querySelector('.hfx-stage-pct'); if(!p) return; out.stages.push({ spot: !!st.closest('.rs-spot'), fx: (st.className.match(/hfx-stage-(\w+)/) || [])[1], tinted: st.classList.contains('hfx-tinted'), stage: rd(st), num: rd(p), vars: vars(st) }); });
      const m = document.querySelector('.hfx-mock');
      if(m){ const g = m.querySelector('.rs-grade'), f = m.querySelector('.unit-breakdown-fill'); out.mock = { fx: m.dataset.fx, card: rd(g), num: rd(m.querySelector('.rs-pct')), bar: f ? rd(f) : null, vars: vars(g) }; }
      return out;
    }"""
    for cls in ("ifc", "academy"):
        ctx, pg, errs = L.open_run(br, cls, 440, 956, "confetti", run=False, dpr=1)
        pg.evaluate("() => { store.lifetime.perfectTests = 600; saveStore(); document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove()); showCustomize('fx'); }")
        L.advance(pg, 1.2)
        r = pg.evaluate(PROBE4)
        tiles = [s for s in r["stages"] if s["tinted"]]
        bad = []
        for s in tiles:
            want = GOLD if s["fx"] == "confetti" else [hexrgb(s["vars"].get("--hfx-g1")), hexrgb(s["vars"].get("--hfx-g2")), hexrgb(s["vars"].get("--hfx-g3")) or hexrgb(s["vars"].get("--hfx-g1"))]
            num = stops(s["num"]["img"])
            if len(num) != 3 or not all(near(a, w) for a, w in zip(num, want)): bad.append((s["fx"], "number", num, want))
            if s["stage"]["bw"] not in ("0px",) and not re.search(r"0\)$", s["stage"]["bc"]): bad.append((s["fx"], "border", s["stage"]["bw"], s["stage"]["bc"]))
            if s["stage"]["sh"] != "none": bad.append((s["fx"], "shadow", s["stage"]["sh"][:50]))
        chk("(G4) %s Customize: %d effect tiles, each number in its effect's ramp, no border, no shadow" % (cls, len(tiles)), len(tiles) >= 3 and not bad, bad)
        for fx in ("fireworks", "ufo"):
            pg.evaluate("(fx) => { document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove()); playUnlockSpotlight(hundoFxUnlockItem(fx), 1, 1, () => {}); }", fx)
            L.advance(pg, 1.2)
            sp = [x for x in pg.evaluate(PROBE4)["stages"] if x["spot"] and x["tinted"]]
            bad = []
            for x in sp:
                want = [hexrgb(x["vars"].get("--hfx-g1")), hexrgb(x["vars"].get("--hfx-g2")), hexrgb(x["vars"].get("--hfx-g3")) or hexrgb(x["vars"].get("--hfx-g1"))]
                num = stops(x["num"]["img"])
                if len(num) != 3 or not all(near(a, w) for a, w in zip(num, want)): bad.append(("number", num, want))
                if x["stage"]["sh"] != "none" or not (x["stage"]["bw"] == "0px" or re.search(r"0\)$", x["stage"]["bc"])): bad.append(("edge", x["stage"]["bw"], x["stage"]["bc"], x["stage"]["sh"][:50]))
            chk("(G4) %s %s unlock pop-up: its box's number is the effect's ramp, no border, no shadow" % (cls, fx), len(sp) == 1 and not bad, [len(sp), bad])
            pg.evaluate("() => document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove())")
        for fx in ("fireworks", "ufo"):
            pg.evaluate("(fx) => { document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove()); showUnlockDetail(hundoFxDetail(fx)); }", fx)
            L.advance(pg, .12)
            r = pg.evaluate(PROBE4); m = r["mock"]
            if not m: chk("(G4) %s %s miniature exists" % (cls, fx), False, r); continue
            num, bar = stops(m["num"]["img"]), stops(m["bar"]["img"]) if m["bar"] else []
            # (384 r9) the miniature of the results card is the results card: its ramp is the one-hue one (hfxOneHueRamp), so the
            # stops it must match are the ones it actually carries - the number's and the bar's are compared with each other
            want = num
            chk("(G4) %s %s miniature: its number and its bar are one ramp, no border or shadow on the card or the bar" % (cls, fx),
                len(num) == 3 and len(bar) == 3 and all(near(a, w) for a, w in zip(num, want)) and all(near(a, w) for a, w in zip(bar, want)) and m["bar"]["sh"] in ("none",) and m["card"]["sh"] == "none" and m["card"]["bw"] in ("0px", "1px") and re.search(r"0\)$|transparent", m["card"]["bc"]) is not None,
                [num, bar, want, m["bar"] and m["bar"]["sh"][:50], m["card"]["sh"][:50], m["card"]["bc"]])
        ctx.close()
    br.close()
L.cb.SERVER.shutdown()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
