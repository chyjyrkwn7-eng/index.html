#!/usr/bin/env python3
"""Build 384 review: no visible patch, line or diamond where a pointer meets its bubble.

Madison: "I can literally see where the patch is ... Also please ensure there aren't any lines or visible patches like this on
anything." The pointers on the app's bubbles (Nova's speech bubble, the under-note, the "No hundo" reason, the slider's top note)
are painted twice where they overlap their body; if the two fills are not the same opaque colour the overlap shows as a diamond
or a box. This renders each at 3x and 2x and measures, in the body just inside the pointer's base, the largest per-channel
difference from the body's own colour (0-1 is invisible: it is rounding).
  python3 tools/check-b384-seams.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
CASES = [("under-note", "<div class='under-note show' style='position:fixed;left:60px;top:300px;width:300px;--arrow-x:150px;padding:14px;transition:none'>A note that says something</div>", 150),
         ("hundo-why", "<div class='hundo-why' style='position:fixed;left:60px;top:300px;width:300px;--tip-x:150px;padding:14px;display:block;animation:none'>Why there is no hundo here</div>", 150),
         ("slider-topnote", "<div class='slider-topnote' style='position:fixed;left:60px;top:300px;--tip-x:60px;animation:none'><div class='slider-topnote-title'>A title</div><div class='slider-topnote-sub'>and a line under it</div></div>", 60)]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for dpr in (3, 2):
        ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=dpr)
        pg.evaluate("document.querySelectorAll('#splashscreen').forEach(n=>n.remove())")
        for name, html, tip in CASES:
            pg.evaluate("(h)=>{ const d=document.createElement('div'); d.id='__t'; d.style.cssText='position:fixed;inset:0;z-index:99999;background:#0b0d12'; d.innerHTML=h; document.body.appendChild(d); }", html)
            pg.wait_for_timeout(450)
            r = pg.evaluate("()=>{ const b=document.querySelector('#__t > *').getBoundingClientRect(); return [b.left,b.top,b.width,b.height]; }")
            a = np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert("RGB")).astype(int)
            x, y, w, h = r; s = dpr
            tx = x + tip
            # the body just under the pointer's base: 3..9px below the top border, 12px either side of the tip, clear of text
            reg = a[int((y + 3) * s):int((y + 8) * s), int((tx - 12) * s):int((tx + 12) * s)]
            ref = a[int((y + 3) * s):int((y + 8) * s), int((x + w - 24) * s):int((x + w - 12) * s)] if w > 100 else reg
            body = np.median(ref.reshape(-1, 3), axis=0)
            d = int(np.abs(reg - body).max())
            chk("%s at %dx: the body under its pointer is the body's own colour (worst channel difference %d, wanted 1 or less)" % (name, dpr, d), d <= 1, d)
            pg.evaluate("document.getElementById('__t').remove()")
        ctx.close()
    br.close()
# the race line's markers are PERFECT circles ("Am I crazy or is this not a perfect circle?"): a 25.6px box turned by translate(-50%)
# landed on fractional pixels and the ring rendered 77 device pixels tall by 74 wide
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for dpr in (3, 2):
        ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=dpr)
        pg.evaluate("""()=>{ document.querySelectorAll('#splashscreen').forEach(n=>n.remove());
          const st=document.getElementById('stage'); const rb=document.getElementById('vroomracebar'); st.replaceChildren(); st.appendChild(rb); rb.hidden=false; rb.style.marginTop='3rem';
          const m=document.getElementById('vroomracemarkers'); [[0,'#ff4d4d'],[37,'#4dc3ff'],[100,'#ffd24d']].forEach(([p,c])=>{ const d=document.createElement('div'); d.className='vroom-race-marker'; d.style.left=p+'%'; d.style.borderColor=c; d.style.setProperty('--stack-y','0rem'); d.style.background='#222'; m.appendChild(d); }); }""")
        pg.wait_for_timeout(700)
        a = np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert("RGB")).astype(int)
        ms = pg.evaluate("()=>[...document.querySelectorAll('.vroom-race-marker')].map(m=>{const r=m.getBoundingClientRect(); return [r.left,r.top,r.width,r.height]})")
        worst = 0
        for (x, y, w, h), col in zip(ms, ((255, 77, 77), (77, 195, 255), (255, 210, 77))):
            reg = a[int((y - 3) * dpr):int((y + h + 3) * dpr), int((x - 3) * dpr):int((x + w + 3) * dpr)]
            m = (np.abs(reg - np.array(col)).sum(axis=2) < 90); ys, xs = np.nonzero(m)
            worst = max(worst, abs((xs.max() - xs.min()) - (ys.max() - ys.min())))
        chk("race markers are round at %dx (ring width and height differ by %d device px, wanted 1 or less)" % (dpr, worst), worst <= 1, worst)
        ctx.close()
    br.close()
cb.SERVER.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
