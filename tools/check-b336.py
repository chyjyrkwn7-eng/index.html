"""Build 336: a badge lifted out of the case is sharp from its first frame (the big face is drawn when the finger goes down).
Run:  python3 tools/check-b336.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, page = g["page_for"](br, "promax")
    for _ in range(3):
        page.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); page.wait_for_timeout(500)
    page.evaluate("()=>{ showProfile('badges'); }"); page.wait_for_timeout(2500)
    page.evaluate("""()=>{ const t = document.querySelector('.ncase-cell.is-earned'); window.__log = [];
      const obs = () => { const im = document.querySelector('.binspect-art.is-current'), f = document.querySelector('.binspect-float');
        if(im && f) window.__log.push({ nat: im.naturalWidth, shown: f.getBoundingClientRect().width }); window.__raf = requestAnimationFrame(obs); };
      window.__raf = requestAnimationFrame(obs);
      t.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true })); setTimeout(() => t.click(), 90); }""")
    page.wait_for_timeout(2200)
    log = page.evaluate("()=>window.__log")
    dpr = 2
    # sharp: the picture always has at least the pixels it is shown at (a 5% allowance)
    soft = [l for l in log if l["nat"] < l["shown"] * dpr * 0.95]
    g["chk"]("the badge opened (frames seen during the lift)", len(log) > 20, len(log))
    g["chk"]("in every frame of the lift the badge's picture has at least the pixels it is drawn at", not soft, soft[:3])
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
