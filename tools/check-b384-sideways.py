#!/usr/bin/env python3
"""384.150: EVERY ROW THAT SLIDES SIDEWAYS SAYS SO. Madison (Unlocks, the filter chips): "You should be able to slide back and forth
across this filter to select them, but you can't." body is touch-action:pan-y (the app keeps the sideways axis for its own swipes) and
iOS carries that down to a sideways scroller unless the scroller gives the axis back itself (touch-action:pan-x pan-y, as the
Calendar's countdown track has since 327z15). Chromium scrolls them regardless, so this reads the declaration: on the Unlocks screen,
Profile and the Calendar (both classes), every element that scrolls sideways (overflow-x auto/scroll and wider than its box) declares
pan-x, and so does every element between a finger on it and it.
  python3 tools/check-b384-sideways.py [--against FILE]   (384.149 FAILS on the Unlocks chips)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
argv = sys.argv[:]; sys.argv = [G]
h = {"__file__": G, "__name__": "gate4"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = argv
from playwright.sync_api import sync_playwright
src = argv[argv.index("--against") + 1] if "--against" in argv else os.path.join(h["ROOT"], "index.html")
text = open(src, encoding="utf-8").read()
fx = h["fixtures"]()
READ = r"""async (go) => { const W = ms => new Promise(r => setTimeout(r, ms)); eval(go); await W(1600);
  const out = []; document.querySelectorAll('#stage *').forEach(n => { const cs = getComputedStyle(n);
    if(!/auto|scroll/.test(cs.overflowX) || n.scrollWidth <= n.clientWidth + 2 || !n.getClientRects().length) return;
    const bad = [];
    const leaf = n.querySelector('*:not(:has(*))') || n;
    for(let e = leaf; e && e !== n.parentElement; e = e.parentElement){ const ta = getComputedStyle(e).touchAction; if(!(ta === 'auto' && e !== n) && !/pan-x|manipulation|^auto$/.test(ta)) bad.push((e.className || e.tagName).toString().slice(0, 30) + ':' + ta); }
    const own = cs.touchAction;
    out.push({ cls: (n.className || n.tagName).toString().slice(0, 40), own, ok: /pan-x|manipulation/.test(own) && !bad.length, bad }); });
  return out; }"""
fails = 0
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    for cls in ("academy", "ifc"):
        ctx, pg, errs = h["page"](br, text, fx["rich_" + cls][0], fx["rich_" + cls][1])
        pg.wait_for_timeout(1500); h["quiet"](pg)
        for name, go in (("Unlocks", "showUnlockTracks()"), ("Profile", "showProfile()"), ("Calendar", "showCalendarTab ? showCalendarTab() : null")):
            try: rows = pg.evaluate(READ, go)
            except Exception as e: rows = [{"cls": "error", "ok": False, "bad": [str(e)[:120]]}]
            bad = [r for r in rows if not r["ok"]]
            ok = not bad and (name != "Unlocks" or any("ulk-chips" in r["cls"] for r in rows))
            fails += 0 if ok else 1
            print(("PASS" if ok else "FAIL"), "[%s] %s: every sideways scroller gives the sideways axis back (%s)" % (cls, name, [(r["cls"], r["own"]) for r in rows]), "" if ok else bad, flush=True)
        ctx.close()
    br.close()
print("ALL PASS" if not fails else "FAILURES: %d" % fails); sys.exit(1 if fails else 0)
