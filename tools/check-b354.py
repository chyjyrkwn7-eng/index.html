"""Build 354: the tab speed test runs [steady], [fast] and [spam] taps and reports, after the last tap, whether the right
screen is up, the right tab is lit and the platter is on it.   Run:  python3 tools/check-b354.py"""
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
    chk("the report has a [steady] run for each tab", "[steady]rewards" in t and "[steady]calendar" in t, t[:200])
    chk("and a [fast] run and a [spam] run", "[fast] taps" in t and "[spam] taps" in t, t[-300:])
    chk("the spam run made all of its taps (30)", "[spam] taps30" in t, t[-300:])
    for run in ("steady", "fast", "spam"):
        i = t.find("[" + run + "] screen") if run == "steady" else t.find("[" + run + "] taps")
        seg = t[i:i + 170] if i >= 0 else ""
        chk("after the %s run the right screen is up, the right tab lit and the platter on it" % run, "screenok" in seg and "litok" in seg and "WRONG" not in seg and "platter0" in seg.replace("platter0.", "platter0"), seg)
    chk("the report fits in the 1700 characters the bug report keeps (%d)" % len(t), len(t) <= 1650, len(t))
    chk("it leaves no style behind", pg.evaluate("()=>!document.getElementById('lagtest-variant')") is True)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
