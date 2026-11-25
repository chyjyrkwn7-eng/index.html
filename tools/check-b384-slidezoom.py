#!/usr/bin/env python3
"""384.153 (slidezoom): EVERY SLIDER'S KNOB RUNS FROM THE LINE'S START TO ITS END, AT ANY PAGE ZOOM.

Madison (a screen recording of Sound & Haptics on his iPhone, 384.152): "It should kinda end at line you see there? It's covering
the percent? ... 100 percent is at the end of that bar". On his phone the knob at 100% ran ~43pt past the line's end, over the
"100%" label, and sat too far right all the way along (1.18x the travel: his page is laid out at 85%). 384.152 placed the knob
with --nsl-w, a width read from script, and the press read it from getBoundingClientRect (the zoomed space) while the transform is
in CSS px - so any page zoom moved the knob off the line (Chromium under CSS zoom: 40px short at 100%; WebKit: past the end).

For each slider (Settings > Sound: Volume; the start sheet: How many, Minutes; the Virtual Room: How many), on an installed
iPhone 17 Pro Max (440x956, 2x), with the page at zoom 1, 0.85 and 1.15 (html { zoom }), read off getBoundingClientRect:
 (1) END    dragged past the end and let go: the input is at its max and the knob's right edge is on the line's end (+-1.5px),
            so nothing past the line (the value label) is covered;
 (2) START  dragged past the start and let go: the input is at its min and the knob's left edge is on the line's start (+-1.5px);
 (3) MIDDLE set to the middle of its range: the fill ends under the knob's middle (+-1.5px);
 (4) no page errors.
Run:  TMPDIR=/dev/shm python3 tools/check-b384-slidezoom.py [--only volume,howmany,minutes,vroom] [--against OLD/index.html]
Must FAIL (1) at 0.85 and 1.15 on 384.152."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "check-b384-sliders.py")
src = open(SRC, encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
# the page asks version.json for a newer build and reloads into it: answer with the served page's own build
src = src.replace('    pg.route("**/index.html"',
    '    _bld = (re.search(r\'const APP_BUILD = "([^"]+)"\', b) or [None, ""])[1]\n'
    '    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=\'{"build":"%s","force":true}\' % _bld))\n'
    '    pg.route("**/index.html"', 1)
G = {"__file__": SRC, "__name__": "slidezoom", "re": re}
exec(src, G)
from playwright.sync_api import sync_playwright

ZOOMS = (1, 0.85, 1.15)
TOL = 1.5
ok = True; fails = 0
def chk(name, cond, info=""):
    global ok, fails
    ok = ok and bool(cond); fails += 0 if cond else 1
    print(("PASS " if cond else "FAIL ") + name + ("  " + str(info)[:300] if info else ""), flush=True)

GEO = """(sel)=>{ const s = document.querySelector(sel); if(!s) return null; const host = s.closest('.nsl'); if(!host) return null;
  const R = e => { const q = e.getBoundingClientRect(); return [q.left, q.right, q.top, q.bottom]; };
  const t = R(host.querySelector('.nsl-track')), f = R(host.querySelector('.nsl-fill')), k = R(host.querySelector('.nsl-thumb'));
  return { track: t, fillEnd: Math.min(f[1], t[1]), knob: k, y: (t[2] + t[3]) / 2, v: +s.value, mn: +s.min, mx: +s.max,
           pressed: host.classList.contains('is-pressed') }; }"""
SETMID = """(sel)=>{ const s = document.querySelector(sel); const mn = +s.min, mx = +s.max, st = Number(s.step) || 1;
  s.value = String(mn + Math.round((mx - mn) / 2 / st) * st); s.dispatchEvent(new Event('input', { bubbles: true }));
  if(s._nsl) s._nsl.paint(); return +s.value; }"""

def drag(pg, sel, to_end):
    g0 = pg.evaluate(GEO, sel)
    x0 = (g0["knob"][0] + g0["knob"][1]) / 2; y = g0["y"]
    x1 = g0["track"][1] + 60 if to_end else g0["track"][0] - 60
    pg.mouse.move(x0, y); pg.mouse.down(); pg.wait_for_timeout(120)
    for i in range(1, 13):
        pg.mouse.move(x0 + (x1 - x0) * i / 12, y); pg.wait_for_timeout(24)
    pg.wait_for_timeout(120); pg.mouse.up(); pg.wait_for_timeout(900)
    return pg.evaluate(GEO, sel)

def run_one(br, key):
    for z in ZOOMS:
        ctx, pg, cdp, errs = G["open_page"](br)
        r = pg.evaluate(G["OPENERS"][key].replace("${COMMON}", G["COMMON"]))
        sel = G["SEL"][key]
        if r != "ok":
            chk("%s @%g opens" % (key, z), False, r); ctx.close(); continue
        pg.evaluate("(z)=>{ document.documentElement.style.zoom = String(z); }", z); pg.wait_for_timeout(700)
        pg.evaluate("(sel)=>{ const s = document.querySelector(sel); s.closest('.nsl').scrollIntoView({ block: 'center' }); }", sel); pg.wait_for_timeout(400)
        e = drag(pg, sel, True)
        chk("%s @%g (1) END: at %g of max %g, the knob's right edge %.1f on the line's end %.1f" % (key, z, e["v"], e["mx"], e["knob"][1], e["track"][1]),
            e["v"] == e["mx"] and abs(e["knob"][1] - e["track"][1]) <= TOL and not e["pressed"])
        s = drag(pg, sel, False)
        chk("%s @%g (2) START: at %g of min %g, the knob's left edge %.1f on the line's start %.1f" % (key, z, s["v"], s["mn"], s["knob"][0], s["track"][0]),
            s["v"] == s["mn"] and abs(s["knob"][0] - s["track"][0]) <= TOL and not s["pressed"])
        pg.evaluate(SETMID, sel); pg.wait_for_timeout(900)
        m = pg.evaluate(GEO, sel); mid = (m["knob"][0] + m["knob"][1]) / 2
        chk("%s @%g (3) MIDDLE: at %g the fill ends at %.1f, the knob's middle %.1f" % (key, z, m["v"], m["fillEnd"], mid),
            abs(m["fillEnd"] - mid) <= TOL)
        chk("%s @%g (4) no page errors" % (key, z), not errs, errs[:2])
        ctx.close()

with sync_playwright() as pw:
    srv, G["URL"] = G["g"]["serve"]()
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    for key in G["OPENERS"]:
        if G["ONLY"] and key not in G["ONLY"]: continue
        run_one(br, key)
    br.close()
print("\nALL PASS" if ok else "\n%d FAILED" % fails)
sys.exit(0 if ok else 1)
