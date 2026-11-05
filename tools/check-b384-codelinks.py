#!/usr/bin/env python3
"""Build 384 final check: the code card's Enlarge and Show the whole page pills have their mark and words on the pill's middle.

Madison, circling Enlarge on a code card: "Am I crazy or is this still centered properly?" Measured at 3x: Enlarge's ink sat 1.00px
and Show the whole page's 2.25px right of the pill's middle. The icon-and-words group was centred; each mark's 24-unit box was
wider than its drawing (the page mark 12 of 24, a unit right of middle), so the empty left of the box pushed the ink right.
check-centering never opens a code card, which is how this got past it.
In a Fire Code drill on an iPhone 17 Pro Max at its 3x, a county question answered and its code shown:
(1) each pill's ink (mark and words) is on the pill's middle across, within .5px;
(2) and up and down, within .5px;
(3) the mark-to-words gap is the same on both pills (within .5px), so the two read as one design;
(4) no page errors.
  PDFJS_DIR=<pdfjs-dist 5.4.149> python3 tools/check-b384-codelinks.py [--against OLD/index.html]   (must FAIL there)"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-test.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b382-test.py"), "__name__": "b384cl"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    label, w, h, ins, ua = G["SIZES"][0]
    ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    G["start"](pg, "short", 4); G["answer_right"](pg, cdp); G["open_code"](pg, cdp); pg.wait_for_timeout(1500)
    dpr = pg.evaluate("devicePixelRatio")
    gaps = []
    for k in (1, 2):
        sel = ".qpanel .ifc-links .ifc-link:nth-child(%d)" % k
        pg.evaluate("(s)=>document.querySelector(s).scrollIntoView({block:'center',behavior:'instant'})", sel); pg.wait_for_timeout(300)
        r = pg.evaluate("(s)=>{ const b=document.querySelector(s); const r=b.getBoundingClientRect(); return [r.left, r.top, r.width, r.height, b.textContent.trim()]; }", sel)
        im = np.array(Image.open(io.BytesIO(pg.screenshot(clip={"x": r[0], "y": r[1], "width": r[2], "height": r[3]}))).convert("RGB")).astype(int)
        ink = (im[..., 0] > 150) & (im[..., 0] - im[..., 2] > 60)
        ys, xs = np.nonzero(ink); Wp, Hp = ink.shape[1], ink.shape[0]
        dx = ((xs.min() + xs.max()) / 2 - (Wp - 1) / 2) / dpr; dy = ((ys.min() + ys.max()) / 2 - (Hp - 1) / 2) / dpr
        cols = np.nonzero(ink.any(0))[0]; runs = np.split(cols, np.nonzero(np.diff(cols) > 1)[0] + 1)
        gap = (runs[1][0] - runs[0][-1] - 1) / dpr if len(runs) > 1 else None   # the first blank run: between the mark and the words
        gaps.append(gap)
        chk("(1) %s: its ink is on the pill's middle across (%+.2fpx)" % (r[4], dx), abs(dx) <= .5, dx)
        chk("(2) %s: and up and down (%+.2fpx)" % (r[4], dy), abs(dy) <= .5, dy)
    chk("(3) the mark-to-words gap is the same on both pills (%s)" % gaps, None not in gaps and abs(gaps[0] - gaps[1]) <= .5, gaps)
    chk("(4) no page errors", not errs, errs[:3])
    br.close()
G["srv"].shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
