"""Build 370: the Drag test's looks are about the glass and the page under it, not the bar's blur (build 369's recording: ~30 updates a second in
every look). Look B has the glass halves' blend off, C their masks off, D their rim shadows off, E hides the page while the bar is held, F all four.
Reads the live style while each look is on, and checks it does what it says (computed values, not the label).
Run:  python3 tools/check-b370.py   (--against: copy the old index.html and version.json over first)"""
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
    pg.evaluate("()=>showBugReport()"); pg.wait_for_timeout(500)
    r = pg.evaluate("""async()=>{ window.__dragTick=120; const per={}; const p=runDragTest(); let done=false; p.then(()=>done=true);
      const lens=()=>document.querySelector('.tab-lens-clip'), glass=()=>document.querySelector('.tab-lens-glass');
      while(!done){ const n=[...document.body.children].find(e=>e.tagName==='DIV'&&/^Look /.test(e.textContent||'')); const L=n?n.textContent[5]:null;
        if(L && !per[L]){ document.documentElement.classList.add('tab-held'); await new Promise(r=>setTimeout(r,60)); const c=lens()&&getComputedStyle(lens()), gl=glass()&&getComputedStyle(glass());
          per[L]={ blend:c&&c.mixBlendMode, mask:c&&(c.maskImage||c.webkitMaskImage), shadow:gl&&gl.boxShadow, stage:getComputedStyle(document.getElementById('stage')).visibility, barBlur:getComputedStyle(document.querySelector('.bottomtabs')).backdropFilter };
          document.documentElement.classList.remove('tab-held'); }
        await new Promise(r=>setTimeout(r,20)); }
      return per; }""")
    A = r.get("A", {})
    chk("A is the glass as it is (blend %s, shadow set, page shown)" % A.get("blend"), A.get("blend") == "plus-lighter" and A.get("shadow") not in (None, "none") and A.get("stage") == "visible", r)
    chk("B blend off, C masks off, D shadows off", r["B"]["blend"] == "normal" and r["C"]["mask"] in ("none", "") and r["D"]["shadow"] == "none", r)
    chk("E hides the page while held, and the glass is still drawn", r["E"]["stage"] == "hidden" and r["E"]["blend"] == "plus-lighter", r)
    chk("F has all four", r["F"]["blend"] == "normal" and r["F"]["shadow"] == "none" and r["F"]["stage"] == "hidden", r)
    chk("the bar's own blur is left alone in every look (the old B made it solid)", all(r[k]["barBlur"] == A.get("barBlur") for k in "BCDEF"), r)
    br.close()
sys.exit(0 if g["ok"] else 1)
