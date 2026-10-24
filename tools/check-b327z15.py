#!/usr/bin/env python3
"""Build 327z15: the tab bar under fast tapping - every sequence lands.

Madison: "When clicking the button tabs fast sometimes it lags, the bubble
pill lags and the screen lags ... Check all possible sequences and
combinations and make it run so smooth."

Real touches on an iPhone 17 Pro Max (440x956 @3), installed:

  python3 tools/check-b327z15.py
  python3 tools/check-b327z15.py --against /path/to/old/index.html

  F. Every ordered pair and triple of the four tabs (same tab twice too),
     tapped 60, 150 and 300ms apart from Home: when it settles the screen
     up is the LAST tab tapped (read off the highlight, which syncActive
     takes from the screen itself), exactly one tab is lit, the grey
     platter sits under it, the lens is down - and nothing is built that
     need not be: taps closer than the glide build only the last tab,
     and a tab whose screen is already up is never built again (a second
     tap on it scrolls to the top).
  G. The same, with the phone at a quarter speed (a build is then a long
     task the taps land in), for the sequences that went wrong:
     Profile-Home, Home-Profile-Home, Leaderboard-Profile-Calendar-Home.
"""
import importlib.util
import itertools
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("z5b", os.path.join(HERE, "check-b327z5-b.py"))
z5b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(z5b)
cb = z5b.cb
check = cb.check
from playwright.sync_api import sync_playwright

ONLY = os.environ.get("B327Z15_ONLY", "FG")
TABS = ["home", "profile", "rewards", "calendar"]

STATE = """() => { const bar = document.getElementById('bottomtabs'), sl = document.getElementById('bottomtabs-slider');
  const lit = [...bar.querySelectorAll('.bottomtab.active')];
  let off = null;
  if(lit.length === 1){ const a = lit[0].getBoundingClientRect(), b = sl.getBoundingClientRect();
    off = Math.abs((a.left + a.width / 2) - (b.left + b.width / 2)); }
  const home = !!document.querySelector('#stage .screen-home-actual');
  return { lit: lit.map(b => b.dataset.dest), off, lensUp: bar.classList.contains('lens-up'), builds: bar._navBuilds || 0, home,
           pend: !!bar._navPend }; }"""


def tap(cdp, pt, hold=0.05):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [pt]})
    time.sleep(hold)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def run(pg, cdp, pts, seq, gap):
    """From Home, tap seq with gap ms between presses; return (state, builds)."""
    pg.evaluate("() => { if(!document.querySelector('#stage .screen-home-actual')) showHome(); }")
    pg.wait_for_timeout(700)
    b0 = pg.evaluate(STATE)["builds"]
    for i, d in enumerate(seq):
        t0 = time.time()
        tap(cdp, pts[d])
        if i < len(seq) - 1:
            left = gap / 1000 - (time.time() - t0)
            if left > 0: time.sleep(left)
    pg.wait_for_timeout(1300)
    st = pg.evaluate(STATE)
    return st, st["builds"] - b0


def expect_builds(seq, gap):
    """Taps closer than the glide (290ms) build only the last tab, once,
    and none if it is the screen that was already up (Home, where every
    run starts). Further apart, each tap may build its own tab - but a
    tab whose screen is already up is never built again."""
    if gap < 290:
        return 0 if seq[-1] == "home" else 1
    n, cur = 0, "home"
    for d in seq:
        if d != cur: n += 1
        cur = d
    return n


def sweep(pg, cdp, label, seqs, gaps):
    pts = {d: pg.evaluate("d => { const r = document.querySelector('.bottomtab[data-dest=\"' + d + '\"]').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }", d) for d in TABS}
    bad = []
    for gap in gaps:
        for seq in seqs:
            st, nb = run(pg, cdp, pts, seq, gap)
            ok = (st["lit"] == [seq[-1]] and st["off"] is not None and st["off"] < 3 and not st["lensUp"]
                  and not st["pend"] and nb <= expect_builds(seq, gap) and (st["home"] == (seq[-1] == "home")))
            if not ok:
                bad.append((gap, "-".join(seq), st, nb))
    n = len(seqs) * len(gaps)
    check("%s: %d of %d sequences land on the last tab, lit once, platter under it, lens down, nothing extra built"
          % (label, n - len(bad), n), not bad, bad[:6])


def section_f(br):
    print("\nF. every pair and triple, full speed")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    seqs = [list(p) for p in itertools.product(TABS, repeat=2) if p[0] != "home" or p[1] != "home"]
    seqs += [list(p) for p in itertools.product(TABS, repeat=3) if p[0] != p[1] and p[1] != p[2]]
    sweep(pg, cdp, label, seqs, (60, 150, 300))
    ctx.close()


def section_g(br):
    print("\nG. the reported runs, at a quarter speed")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    # warm every screen once, then throttle
    for d in ("profile", "rewards", "calendar", "home"):
        pg.evaluate("d => document.querySelector('.bottomtab[data-dest=\"' + d + '\"]')._navigate()", d)
        pg.wait_for_timeout(900)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    seqs = [["profile", "home"], ["home", "profile", "home"], ["profile", "home", "profile", "home"],
            ["rewards", "profile", "calendar", "home"], ["calendar", "rewards"], ["profile", "calendar", "profile"]]
    sweep(pg, cdp, label + " at 4x CPU", seqs, (120, 250, 400))
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("F", section_f), ("G", section_g)):
            if k in ONLY:
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
