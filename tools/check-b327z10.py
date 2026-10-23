#!/usr/bin/env python3
"""Build 327z10: the chat sheet slides down when swiped away, and smoothly.

Madison: "The chat when swiping down, it just disappears, it doesn't do the
animation that it goes downwards, and it's laggy."

Real touch input (CDP Input.dispatchTouchEvent), installed, on an iPhone 17
Pro Max (440x956 @3), the modern dark layout (the default):

  python3 tools/check-b327z10.py
  python3 tools/check-b327z10.py --against /path/to/old/index.html

  A. While a finger pulls the sheet (past the flat-fill point) and through
     the slide out, the sheet carries no backdrop blur - read off the
     computed style every frame.
  B. Let go past the line, the sheet travels from where the finger let go to
     off the bottom over at least 120ms, and at a quarter of that time it is no more
     than 58% of the way (the old .26s ease-out was about two thirds there).
  C. Closed, it rests off the bottom; opened again it comes back to rest at
     the same place it opened before. A short pull springs back and stays
     open.
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("z5b", os.path.join(HERE, "check-b327z5-b.py"))
z5b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(z5b)   # check-behaviour reads --against itself
cb = z5b.cb
check = cb.check
from playwright.sync_api import sync_playwright

TRACE = """() => { const p = document.querySelector('.chatdock-panel'); window.__tr = []; window.__stop = false;
  const L = () => { const cs = getComputedStyle(p);
    __tr.push({ t: performance.now(), top: p.getBoundingClientRect().top, bf: cs.backdropFilter, wbf: cs.webkitBackdropFilter || '',
                flat: p.classList.contains('is-flat'), open: chatDockOpen, rel: !!window.__released });
    if(__tr.length < 400 && !window.__stop) requestAnimationFrame(L); };
  requestAnimationFrame(L); }"""

READ = """() => { const p = document.querySelector('.chatdock-panel'); const r = p.getBoundingClientRect();
  return { top: r.top, h: r.height, open: chatDockOpen, inline: p.style.transform, vh: innerHeight }; }"""


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        label, w, h, dpr = z5b.PHONE
        ctx, pg = z5b.boot(br, w, h, dpr)
        lay = pg.evaluate("() => document.documentElement.dataset.layout + '/' + document.documentElement.dataset.theme")
        check("%s: the modern dark layout is on (%s)" % (label, lay), lay == "modern/dark", lay)
        o = pg.evaluate(z5b.OPEN_CHAT)
        cdp = ctx.new_cdp_session(pg)
        pg.evaluate("() => { document.querySelector('.chatdock-panel .vroom-chat-list').scrollTop = 0; }")
        time.sleep(0.3)
        rest = pg.evaluate(READ)
        CD = max(200, int(rest["h"] * 0.5))
        pg.evaluate(TRACE)
        z5b.drag_to(cdp, o["lx"], max(40, o["ly"] - CD // 3), 0, CD, steps=16)
        time.sleep(0.08)
        pg.evaluate("() => { window.__released = true; }")
        z5b.tend(cdp)
        time.sleep(0.9)
        pg.evaluate("() => { window.__stop = true; }")
        tr = pg.evaluate("() => __tr")
        aft = pg.evaluate(READ)

        moving = [f for f in tr if f["flat"] or (f["rel"] and f["top"] > rest["top"] + 2 and f["top"] < aft["top"] - 1)]
        blurred = [f for f in moving if (f["bf"] not in ("none", "")) or (f["wbf"] not in ("none", ""))]
        check("%s: A. no backdrop blur on any frame while it is pulled or slides out (%d of %d frames blurred)"
              % (label, len(blurred), len(moving)), moving and not blurred, blurred[:3])

        check("%s: and let go past the line, it closes" % label, aft["open"] is False, aft)
        after = [f for f in tr if f["rel"]]
        start = after[0]["top"] if after else rest["top"]
        end = aft["top"]
        way = end - start
        tops = [start] + [f["top"] for f in after]
        moved = [f for f in after if f["top"] > start + 0.5]
        t0 = moved[0]["t"] - 16.7 if moved else 0
        done = next((f["t"] for f in moved if f["top"] >= end - 1), t0)
        dur = done - t0
        q = t0 + dur / 4
        # how far it is at a quarter of its slide, interpolated between frames
        prev = (t0, start)
        at_q = end
        for f in moved:
            if f["t"] >= q:
                a, b = prev, (f["t"], f["top"])
                at_q = a[1] + (b[1] - a[1]) * ((q - a[0]) / max(0.01, b[0] - a[0]))
                break
            prev = (f["t"], f["top"])
        frac = (at_q - start) / max(1, way)
        check("%s: B. it slides from where the finger let go (%.0f) to off the bottom (%.0f) over %.0fms, %.0f%% of the way at a quarter of that (an ease-out that leaps is over 58%%)"
              % (label, start, end, dur, 100 * frac),
              way > 80 and end >= aft["vh"] - 1 and dur >= 120 and frac <= 0.58,
              [round(f["top"]) for f in moved])
        check("%s: C. closed, nothing inline is left on it" % label, aft["inline"] == "", aft)

        # reopen: back where it rested
        pg.evaluate("() => { openChatDock(); }")
        time.sleep(0.6)
        re = pg.evaluate(READ)
        check("%s: C. opened again, it rests where it did (%.0f, was %.0f)" % (label, re["top"], rest["top"]),
              re["open"] and abs(re["top"] - rest["top"]) < 2, [re, rest])

        # a short pull springs back
        pg.evaluate("() => { document.querySelector('.chatdock-panel .vroom-chat-list').scrollTop = 0; }")
        time.sleep(0.3)
        z5b.drag_to(cdp, o["lx"], o["ly"], 0, 60, steps=8, wait=0.05)
        time.sleep(0.3)
        z5b.tend(cdp)
        time.sleep(0.7)
        sp = pg.evaluate(READ)
        check("%s: C. a short slow pull springs back and stays open (%.0f)" % (label, sp["top"]),
              sp["open"] and abs(sp["top"] - rest["top"]) < 2 and sp["inline"] == "", sp)
        ctx.close()
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
