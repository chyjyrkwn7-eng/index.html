#!/usr/bin/env python3
"""Build 384 r16: the two class cards are one size everywhere, and the coin on each is a clean round disc.

Madison, on the sign-up "Select your classes" step: "Both of the boxes should still be the same size on the SE (smaller
devices)" and "the bottom of their circles look bad ... maybe the top too". On the stacked short-phone layout Police Academy was
83px tall and Fire Code 133px; the coin (.cc-emblem) had its fill gradient painted under its own 1px border (the gradient tiles
by default, so the border strips at the top and bottom showed the other end of the tile: a flat bright cut along the bottom
and a dark one along the top), an inset dark crescent at the bottom and a hairline at the top, a 16px halo the card cut off at
the top on a short phone, and behind it a glow ellipse hung off the card's corner whose gradient was still coloured where its
rounded box ended (a hard-edged lit disc).

  A  the two cards are the same height (within 1px) on the sign-up step - short phones stacked (375x667 installed, 375x548 in a
     browser tab, 320x568, SE on its side), a 13 mini, a Pro Max, an iPad Pro 11" both ways, laptops - unpicked, with each
     picked, and with both picked, and neither card's height changes with a pick (Select -> Selected); on the Classes screen
     (Settings / the class button's Add a class) at four widths, with none, one and both enrolled.
  B  the coin. Until 384.108 it was a flat grey disc and this leg measured its rim: rendered at device pixel ratio 3, the rim's brightness
     in 36 sectors against the ground outside and inside it (tolerances 3 / 6 / 3 on the spreads and the top/bottom means). Since 384.108
     (classmarks, at the owner's request: "ensure the two classes are updated (the logos and circles) to match what the Home Screen has now",
     and he approved the look) the coin is the class button's LIT RING, which is not an even rim by design, so that measurement is replaced
     by classmarks' own ring check: the coin is the button's ring - the same --cb-ring colour, the ring's four stops at the same share of the
     coin's radius (within 2 points), the same pool and rim colours, and the button's two glows in the same colours with their blur the same
     share of the coin's size (within 25%) - read against a probe of Home's button (54px, .class-bubble.is-<class>) on the same page. The mark
     is still centred in the coin (within .6px).
     REVISED for classglass (the owner circled option B, the liquid glass: "Ensure that's updated app wide"): the coin is now the
     button's LIQUID GLASS, so the ring check (--cb-ring, four stops) is replaced by the same glass check classmarks makes
     (tools/b384_classglass_lib.py: the five layers and their colours, a transparent rim over the border-box gradient at the
     button's width as a share of the size, the light behind the mark, the class-coloured shadow), against the same probe.
  C  nothing is cut: the coin plus its halo (its own computed box-shadow blur) and the glow box both sit inside the card and
     inside every ancestor that clips.

    python3 tools/check-b384-classcards.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import io, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.join(HERE, "check-positions.py")
g = {"__file__": CP, "__name__": "cp"}
exec(io.open(CP, encoding="utf-8").read().rsplit("\nmain()", 1)[0], g)
from playwright.sync_api import sync_playwright
from PIL import Image
sys.path.insert(0, HERE); import b384_classglass_lib as L

AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
SRC = io.open(AGAINST or os.path.join(g["ROOT"], "index.html"), encoding="utf-8").read()
def patched(ins):
    t, r, b, l = ins
    v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], SRC)

# (name, w, h, installed, insets)
SIGNUP = [
    ("SE 2nd/3rd gen installed", 375, 667, True, (20, 0, 0, 0)),
    ("SE 2nd/3rd gen in Safari", 375, 548, False, (0, 0, 0, 0)),
    ("SE 1st gen", 320, 568, True, (20, 0, 0, 0)),
    ("SE on its side", 667, 375, True, (0, 0, 0, 0)),
    ("13 mini", 375, 812, True, (50, 0, 34, 0)),
    ("14/15/16", 393, 852, True, (59, 0, 34, 0)),
    ("Pro Max", 440, 956, True, (62, 0, 34, 0)),
    ("iPad Pro 11 portrait", 834, 1194, True, (24, 0, 20, 0)),
    ("iPad Pro 11 landscape", 1194, 834, True, (24, 0, 20, 0)),
    ("Dell Latitude browser", 1366, 638, False, (0, 0, 0, 0)),
    ("MacBook Air browser", 1440, 770, False, (0, 0, 0, 0)),
]
CATALOG = [("SE", 375, 667), ("Pro Max", 440, 956), ("iPad Pro 11", 834, 1194), ("laptop", 1440, 770)]
COIN_VIEWS = [("SE", 375, 667, True, (20, 0, 0, 0)), ("Pro Max", 440, 956, True, (62, 0, 34, 0)), ("iPad Pro 11", 834, 1194, True, (24, 0, 20, 0))]
TOL_IN, TOL_OUT, TOL_SECTOR = 3.0, 6.0, 3.0

ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:300]), flush=True)

HEIGHTS = """()=>[...document.querySelectorAll('#stage .class-card:not(.is-soon)')].map(c => { const b = c.getBoundingClientRect(); return { h: b.height, w: b.width, chip: (c.querySelector('.cc-status')||{}).textContent }; })"""

# ---- ring measurement (the coin alone) ----
def lum(p): return .2126 * p[0] + .7152 * p[1] + .0722 * p[2]
def sample(px, W, H, cx, cy, r, th, k=3):
    x = (cx + r * math.cos(th)) * k - .5; y = (cy + r * math.sin(th)) * k - .5
    x = min(max(x, 0), W - 1.001); y = min(max(y, 0), H - 1.001)
    x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0
    return sum(w * lum(px[x0 + dx, y0 + dy]) for dx, dy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)))
def profile(im, cx, cy, R):
    px = im.load(); outc = []; inc = []
    for s in range(36):
        peak = []; inn = []; out = []
        for ai in range(10):
            th = math.radians(s * 10 + ai + .5)
            P = [(d, sample(px, im.width, im.height, cx, cy, R + d / 6.0, th)) for d in range(-18, 19)]
            peak.append(max(v for d, v in P if -6 <= d <= 3))
            inn.append(sum(v for d, v in P if -18 <= d <= -11) / 8.0)
            out.append(sum(v for d, v in P if 9 <= d <= 15) / 7.0)
        pk = sum(peak) / 10; outc.append(pk - sum(out) / 10); inc.append(pk - sum(inn) / 10)
    return outc, inc
RINGS = ("""()=>{ const one = ONE_JS;
  return [...document.querySelectorAll('#stage .class-card:not(.is-soon)')].map(card => { const key = ['academy', 'ifc'].find(k => card.classList.contains('is-' + k)) || window.NOVA_CLASS;
    return { key, el: one(card.querySelector('.cc-emblem')), ref: (PROBE_JS)(key) }; }); }""").replace("ONE_JS", L.ONE_JS).replace("PROBE_JS", L.PROBE_JS)
def sector_mean(a, lo, hi): v = [a[i % 36] for i in range(lo, hi)]; return sum(v) / len(v)

GEOM = """()=>[...document.querySelectorAll('#stage .class-card:not(.is-soon)')].map(card => {
  const R = e => e.getBoundingClientRect(), cr = R(card), coin = card.querySelector('.cc-emblem'), glow = card.querySelector('.cc-glow'), svg = coin.querySelector('svg');
  const sh = getComputedStyle(coin).boxShadow.split(/,(?![^(]*\))/).filter(x => !/inset/.test(x));
  const reach = Math.max(0, ...sh.map(x => { const m = x.match(/(-?[\d.]+)px (-?[\d.]+)px (-?[\d.]+)px(?: (-?[\d.]+)px)?/); return m ? Math.abs(+m[3]) + Math.max(0, +(m[4] || 0)) : 0; }));   // the halo's reach (blur radius + spread)
  const c = R(coin), gl = R(glow), sv = R(svg);
  const boxes = [{ n: 'card', r: cr }]; for(let e = card.parentElement; e && e !== document.body; e = e.parentElement){
    const o = getComputedStyle(e); if(o.overflow !== 'visible' || o.overflowX !== 'visible' || o.overflowY !== 'visible'){ const r = R(e); boxes.push({ n: e.className || e.tagName, r: { left: r.left, top: r.top, right: r.right, bottom: r.bottom } }); } }
  const worst = (box, r) => Math.min(r.left - box.left, r.top - box.top, box.right - r.right, box.bottom - r.bottom);
  let coinRoom = 1e9, glowRoom = 1e9;
  boxes.forEach(b => { coinRoom = Math.min(coinRoom, worst(b.r, { left: c.left - reach, top: c.top - reach, right: c.right + reach, bottom: c.bottom + reach }));
                        glowRoom = Math.min(glowRoom, worst(b.r, gl)); });
  return { reach, coinRoom, glowRoom, glowBox: [Math.round(gl.width), Math.round(gl.height)], card: [Math.round(cr.width), Math.round(cr.height)],
           dx: (sv.left + sv.width / 2) - (c.left + c.width / 2), dy: (sv.top + sv.height / 2) - (c.top + c.height / 2),
           rect: [c.left, c.top, c.width, c.height] }; })"""

def context(br, w, h, installed, ins, account, dpr=1):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True)
    ctx.add_init_script(g["SEED"])
    if installed: ctx.add_init_script(g["STANDALONE"])
    pg = ctx.new_page(); body = patched(ins); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json", lambda r, q: r.abort())
    return ctx, pg, errs
def open_step(pg, url, kind):
    pg.goto(url); pg.wait_for_timeout(2300)
    pg.evaluate("document.getElementById('splashscreen')?.remove(); document.querySelectorAll('.gs-page').forEach(n=>n.remove())")
    if kind == "signup":
        g["run"](pg, "showClassSelection")
    else:
        pg.evaluate("()=>{ homeUnlocksOwed=()=>false; document.querySelectorAll('.unlock-card,.rs-spot').forEach(n=>n.remove()); }")
        pg.evaluate("showClassCatalog(); scrollTo(0,0);")
    pg.wait_for_timeout(1500)

srv, url = g["serve"]()
errs_all = []
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=g["CHROME"])
        # ---- A: equal heights, sign-up ----
        for name, w, h, installed, ins in SIGNUP:
            ctx, pg, errs = context(br, w, h, installed, ins, True)
            open_step(pg, url, "signup")
            states = {}
            states["none picked"] = pg.evaluate(HEIGHTS)
            for label, idx in (("Police Academy picked", [0]), ("Fire Code picked", [1]), ("both picked", [0, 1])):
                pg.evaluate("()=>{ document.querySelectorAll('#stage .class-card.is-picked').forEach(c => c.click()); }")
                pg.wait_for_timeout(250)
                pg.evaluate("(idx)=>{ const cs = [...document.querySelectorAll('#stage .class-card:not(.is-soon)')]; idx.forEach(i => cs[i].click()); }", idx)
                pg.wait_for_timeout(450)
                states[label] = pg.evaluate(HEIGHTS)
            tag = f"{name} {w}x{h}"
            base = states["none picked"]
            worst = max(abs(s[0]["h"] - s[1]["h"]) for s in states.values())
            drift = max(abs(s[i]["h"] - base[i]["h"]) for s in states.values() for i in (0, 1))
            chk(f"A {tag}: the two class cards are one height in every state (heights {[round(c['h'], 1) for c in base]}, widest gap {worst:.2f}px)", worst <= 1.0, states)
            chk(f"A {tag}: a pick (Select -> Selected) changes neither card's size (most {drift:.2f}px)", drift <= 1.0, states)
            errs_all += errs; ctx.close()
        # ---- A: equal heights, the Classes screen ----
        for name, w, h in CATALOG:
            ctx, pg, errs = context(br, w, h, True, (20, 0, 0, 0), True)
            open_step(pg, url, "catalog")
            res = {}
            for label, mine in (("none enrolled", "[]"), ("Police Academy enrolled", "['academy']"), ("both enrolled", "['academy','ifc']")):
                pg.evaluate(f"()=>{{ enrolledClasses = () => {mine}; showClassCatalog(); scrollTo(0,0); }}"); pg.wait_for_timeout(1300)
                res[label] = pg.evaluate(HEIGHTS)
            worst = max(abs(s[0]["h"] - s[1]["h"]) for s in res.values())
            chk(f"A Classes screen {name} {w}x{h}: the two cards are one height with none, one and both enrolled (widest gap {worst:.2f}px)", worst <= 1.0, res)
            errs_all += errs; ctx.close()
        # ---- B and C: the coin ----
        for kind in ("signup", "catalog"):
            for name, w, h, installed, ins in COIN_VIEWS:
                if kind == "catalog" and name == "SE": continue
                ctx, pg, errs = context(br, w, h, installed, ins, True, dpr=3)
                open_step(pg, url, kind)
                geo = pg.evaluate(GEOM)
                tag = f"{kind} {name} {w}x{h}"
                for i, d in enumerate(geo):
                    chk(f"C {tag} card {i + 1}: coin + its {d['reach']:.0f}px halo is inside the card and every clipping ancestor (room {d['coinRoom']:.1f}px); the glow box {d['glowBox']} stays inside the card {d['card']} (room {d['glowRoom']:.1f}px)",
                        d["coinRoom"] >= -.01 and d["glowRoom"] >= -.51, d)
                    chk(f"B {tag} card {i + 1}: the mark is centred in the coin (off by {d['dx']:.2f}, {d['dy']:.2f}px)", abs(d["dx"]) <= .6 and abs(d["dy"]) <= .6, d)
                for i, d in enumerate(pg.evaluate(RINGS)):
                    e, ref = d["el"], d["ref"]
                    if not e or not e["vis"]:
                        chk(f"B {tag} card {i + 1}: the coin is drawn", False, d); continue
                    ok_g, summary, info = L.glass(e, ref)
                    chk(f"B {tag} card {i + 1} ({d['key']}): the coin is Home's liquid glass at {e['w']}px ({summary})", ok_g, info)
                errs_all += errs; ctx.close()
        br.close()
finally:
    srv.shutdown()
chk("no page errors", not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
