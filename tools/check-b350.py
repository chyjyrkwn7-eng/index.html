"""Build 350: the tab speed test runs five passes (base, still, flat, nofx, nosvg) and leaves no style behind.
Run:  python3 tools/check-b350.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    r = pg.evaluate("async ()=>await runLagTest()")
    t = (r or {}).get("text", "")
    for v in ("base", "still", "flat", "nofx", "nosvg"):
        chk("the speed test has a [%s] pass for the Leaderboard" % v, ("[" + v + "]rewards") in t, t[:200])
    left = pg.evaluate("()=>!!document.getElementById('lagtest-variant')")
    chk("it leaves no variant style on the page", left is False, left)
    chk("the report fits in the 1700 characters the bug report keeps (%d)" % len(t), len(t) <= 1650, len(t))
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
