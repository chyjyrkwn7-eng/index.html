"""Build 361: the tab speed test also runs the effect-off variants ([g:base] ... [g:bare]), one line each with the four tabs'
l (tap to screen), p (tap to the second frame after it), w (worst frame) and s (slow frames), so the phone itself says which
kind of drawing costs most. Nothing else changes.
Run:  python3 tools/check-b361.py   (add --against old.html to run on another build)"""
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
    pg.wait_for_timeout(2000)
    text = pg.evaluate("async()=>{ const x=await runLagTest(()=>{}); return x.text; }")
    parts = [p for p in text.split(" | ") if p.startswith("[g:")]
    names = [p[3:p.index("]")] for p in parts]
    chk("the speed test reports the effect-off variants (%s)" % (names,), "base" in names and "bare" in names and len(names) >= 5, text)
    import re
    ok = len(parts) >= 5 and all(len(re.findall(r"[rpch] l\d+/p\d+/w\d+/s\d+", p)) == 4 for p in parts)
    chk("each variant line carries all four tabs' l/p/w/s", ok, parts[:2])
    chk("the usual lines are still there ([steady] [fast] [spam] [v:base])", all(k in text for k in ("[steady]", "[fast]", "[spam]", "[v:base]")), text[:200])
    br.close()
sys.exit(0 if g["ok"] else 1)
