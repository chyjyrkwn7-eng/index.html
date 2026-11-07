#!/usr/bin/env python3
"""Build 384 round 5: the digits in the question clock sit in the middle of their pill (the race's and Tug's / Battle's).

Madison, twice: "It's not centered". A mono face with line-height 1 puts its digits high in the line box, so equal padding left them
about a pixel and a half nearer the top. This renders each clock at 3x and 2x and measures the space above and below the ink.
  python3 tools/check-b384-clocks.py [--against OLD/index.html]   (must FAIL on the build before)"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
MOUNT = {
 "tug": """()=>{ const c=document.createElement('span'); c.className='tug-clock'; c.id='__c'; c.textContent='17.9s'; c.style.margin='6rem 0 0 2rem'; c.style.display='inline-block'; document.getElementById('stage').appendChild(c); }""",
 "race": """()=>{ const c=document.createElement('span'); c.className='race-qclock'; c.id='__c'; c.style.margin='6rem 0 0 2rem'; const n=document.createElement('span'); n.className='race-qclock-num'; n.textContent='17.9'; const u=document.createElement('span'); u.className='race-qclock-unit'; u.textContent='s'; c.append(n,u); document.getElementById('stage').appendChild(c); }""",
}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for dpr in (3, 2):
        for name, js in MOUNT.items():
            ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=dpr)
            pg.evaluate("()=>{ document.querySelectorAll('#splashscreen').forEach(n=>n.remove()); document.getElementById('stage').replaceChildren(); }")
            pg.evaluate(js); pg.wait_for_timeout(500)
            x, y, w, h = pg.evaluate("()=>{const b=document.getElementById('__c').getBoundingClientRect(); return [b.left,b.top,b.width,b.height]}")
            a = np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert("RGB")).astype(int); s = dpr
            inner = a[int((y + 4) * s):int((y + h - 4) * s), int((x + 8) * s):int((x + w - 8) * s)]
            bg = np.median(inner.reshape(-1, 3), axis=0)
            ys, xs = np.where(np.abs(inner - bg).sum(axis=2) > 120)
            above = (ys.min() / s) + 4; below = h - ((ys.max() / s) + 4)
            chk("%s clock at %dx: space above the digits %.2fpx, below %.2fpx (within 0.75 of each other)" % (name, dpr, above, below), abs(above - below) <= 0.75, (above, below))
            ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
