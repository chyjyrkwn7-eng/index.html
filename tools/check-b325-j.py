#!/usr/bin/env python3
"""Build 325 (J): the tab bar's lens is DRAWN when you hold the tab it last
landed on.

Found by the review-pack recorder on 618ee2b and reproduced in plain real
time: tap a tab, wait, then press and hold that SAME tab without moving.
The bar swelled, the grey platter went and the label was magnified, but no
lens was drawn for the whole hold - while the page's own state said it was
up and opaque (.tab-lens.is-up, glass 1, grey 0, platter 0). Holding a
different tab worked, a first-ever hold worked, and a drag showed the lens
the moment the finger moved.

The cause was paint, not state: the lens was visibility:hidden at rest, and
its two clipped halves (.tab-lens-clip - a layer each, masked, plus-lighter)
were not repainted when that inherited visibility flipped back, unless their
own transform changed. They sit on the lens's centre line, so every press
moved them except a press on the tab the last lens settled on. So this gate
reads PIXELS, never the DOM (the DOM said it was fine all along): on the
frame-exact clock (check-b325-f's Frames: the page clock faked and every
animation seeked to it, a 60th of a second a step), the bar is screenshotted
through the hold and the lens's top rim - its catch-light, standing proud of
the bar - must be there in every sampled frame, on the iPhone 17 Pro Max
(3x) and the iPad Pro 11" (2x), installed.

  Home -> tap Profile -> ~3s -> hold Profile: drawn in every sampled frame,
  and it settles back into the grey platter on Profile on release - on
  each device, installed and in a browser, from a fresh launch. Installed,
  the same page then holds Leaderboard, lets go, and holds it again: drawn
  in every frame both times (the controls; the old build drew those).

Every check FAILS on 618ee2b and passes here:
  python3 tools/check-b325-j.py
  python3 tools/check-b325-j.py --against /tmp/claude-0/w325final/index.html
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cf", os.path.join(HERE, "check-b325-f.py"))
cf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cf)
cb = cf.cb
from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

check, booted, USED_ACCOUNT, CHROME = cb.check, cb.booted, cb.USED_ACCOUNT, cb.CHROME

STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){},
       addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""

CENTRE = "(id) => { const r = document.getElementById(id).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }"
BAND = 200      # css px of the bottom of the screen captured each frame
RIM_MIN = 40    # levels the rim must stand over the page just above it


def rim(pg, w, h):
    """The lens's top edge, in pixels: the median over the middle 40% of its
    width of the brightest of the rows 0.5-1.5px inside its top, less the
    row 4px above it (the page). ~125-155 where the lens is drawn; ~0 where
    it is not."""
    s = pg.evaluate(cf.SAMPLE)
    top = h - BAND
    im = Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": top, "width": w, "height": BAND}))).convert("L")
    k = im.size[0] / float(w)
    if not s["w"]:
        return s, -999
    l, r = s["cx"] - s["w"] / 2, s["cx"] + s["w"] / 2
    xs = range(int((l + (r - l) * .3) * k), int((l + (r - l) * .7) * k), 2)

    def row(y):
        yy = int((y - top) * k)
        if yy < 0 or yy >= im.size[1]:
            return 0
        v = sorted(im.getpixel((x, yy)) for x in xs)
        return v[len(v) // 2]
    return s, max(row(s["t"] + .5), row(s["t"] + 1), row(s["t"] + 1.5)) - row(s["t"] - 4)


def hold_frames(pg, F, w, h, n=64):
    """step n frames with the finger down; the rim every 4th frame once the
    lift is over (frame 16, ~270ms, on)"""
    out = []
    for i in range(n):
        F.step()
        if i >= 16 and i % 4 == 0:
            s, v = rim(pg, w, h)
            out.append((i, round(v), cf.shown(s)))
    return out


def _hold(pg, cdp, F, w, h, tab, n):
    cf.touch(cdp, "touchStart", *pg.evaluate(CENTRE, tab))
    fr = hold_frames(pg, F, w, h, n)
    cf.touch(cdp, "touchEnd"); F.step(60)
    return fr


def _drawn(fr, n):
    return len(fr) >= n and all(v >= RIM_MIN and up for _, v, up in fr)


def _settled(pg, tab):
    g = pg.evaluate(cf.GEO)
    lit = [t["id"] for t in g["tabs"] if t["active"]]
    pt = next(t for t in g["tabs"] if t["id"] == tab)
    land = pg.evaluate(cf.SAMPLE)
    return (lit == [tab] and not cf.shown(land) and g["op"] > .95
            and abs((g["p"]["l"] + g["p"]["r"]) / 2 - pt["c"]) <= 1 and .08 <= g["fillWhite"] <= .16), lit


def check_same_tab(br):
    print("\nJ. holding the tab the last lens landed on draws the lens, every frame (pixels, not the DOM)")
    for label, w, h, dpr in [("iPhone 17 Pro Max", 440, 956, 3), ("iPad Pro 11\"", 834, 1194, 2)]:
        for mode in ("installed", "in a browser"):
            # a fresh page each time: whether the old build showed the lens
            # depended on what had been painted before, and the reported
            # sequence is from a fresh launch
            ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True, dpr=dpr, init=STANDALONE if mode == "installed" else None)
            pg.evaluate(cf.CLEAN); pg.evaluate("() => { theme.reduceMotion = false; applyTheme(); showHome(); }")
            pg.wait_for_timeout(1100); pg.evaluate(cf.CLEAN)
            cdp = ctx.new_cdp_session(pg)
            F = cf.Frames(ctx, pg)
            # Home -> tap Profile -> ~3s -> hold Profile
            cf.touch(cdp, "touchStart", *pg.evaluate(CENTRE, "bottomtab-profile")); F.step(6); cf.touch(cdp, "touchEnd"); F.step(180)
            pg.evaluate(cf.CLEAN)
            fr = _hold(pg, cdp, F, w, h, "bottomtab-profile", 64)
            ok, lit = _settled(pg, "bottomtab-profile")
            detail = {"rim by frame": [(i, v) for i, v, _ in fr], "page says up": all(up for _, _, up in fr), "settled on Profile": ok, "lit": lit}
            if mode == "installed":
                # and nothing else changed: a hold on another tab, and then a
                # second hold on that tab once the first has landed there
                F.step(120); pg.evaluate(cf.CLEAN)
                fo = _hold(pg, cdp, F, w, h, "bottomtab-rewards", 40)
                F.step(180); pg.evaluate(cf.CLEAN)
                fa = _hold(pg, cdp, F, w, h, "bottomtab-rewards", 40)
                ok2, lit2 = _settled(pg, "bottomtab-rewards")
                detail.update({"hold Leaderboard": [v for _, v, _ in fo], "hold it again": [v for _, v, _ in fa], "settled on Leaderboard": ok2})
                check("%s, installed: tap Profile, ~3s, hold Profile: the lens is drawn in every sampled frame of the hold (its rim %d+ levels over the page), and on release it settles into the grey platter on Profile; a hold on Leaderboard, and a second one there once it has landed, draw it too" % (label, RIM_MIN),
                      _drawn(fr, 10) and ok and _drawn(fo, 5) and _drawn(fa, 5) and ok2, detail)
            else:
                check("%s, in a browser: tap Profile, ~3s, hold Profile: the lens is drawn in every sampled frame of the hold, and settles into the grey platter on release" % label,
                      _drawn(fr, 10) and ok, detail)
            ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        try:
            check_same_tab(br)
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
