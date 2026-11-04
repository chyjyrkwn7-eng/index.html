"""Build 384: the lit "100%" lies exactly on the real one - never a ghost beside it.
Madison saw the 100% look doubled in the hundo tiles: the light laid over the number (hfxLitText) was a copy in the font's
default figures, while the grade is set in tabular lining figures - 2.5px narrower - and placed on whole pixels while the
centred number sits on a fraction.
Read off the page (iPhone 17 Pro Max and iPad Pro 11"), every academy effect that lights the number, in its live tile
(buildHundoFxStage, as Customize and Settings show it):
(1) the copy's digits are set the way the number's are (font-variant-numeric the same);
(2) the copy's run of glyphs lies on the real one: left, top and width each within 0.25px;
(3) at least three effects light the number on each device (so the check measured something), and no page errors.
Run:  python3 tools/check-b384-litnum.py   (--against: copy the old index.html over first, as check-b382-board)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
_s = open(HERE + "/check-b382-board.py").read()
G = {"__file__": HERE + "/check-b382-board.py", "__name__": "b384lit"}
exec(_s[:_s.index("\nwith sync_playwright() as pw:")], G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
PROBE = """async (id)=>{ document.querySelectorAll('.hfx-stage-host').forEach(e=>e.remove());
  const host=document.createElement('div'); host.className='hfx-stage-host'; host.style.cssText='position:fixed;left:23.3px;top:120.6px;width:221px;height:221px;z-index:99999';
  host.appendChild(buildHundoFxStage(id,{live:true,delay:0})); document.body.appendChild(host);
  const t0=performance.now(); let out=null;
  while(performance.now()-t0<9000){ await new Promise(r=>setTimeout(r,50));
    const lit=host.querySelector('.hfx-lit-in'), real=host.querySelector('.hfx-stage-pct, .rs-pct');
    if(lit && real){ const a=document.createRange(); a.selectNodeContents(real); const A=a.getBoundingClientRect();
      const b=document.createRange(); b.selectNodeContents(lit); const B=b.getBoundingClientRect();
      out={ dx:B.left-A.left, dy:B.top-A.top, dw:B.width-A.width, fvReal:getComputedStyle(real).fontVariantNumeric, fvLit:getComputedStyle(lit).fontVariantNumeric }; break; } }
  host.remove(); return out; }"""
IDS = "()=>HUNDO_FX.map(f => f.id)"
errs = []
with sync_playwright() as pw:
    for dev in ("promax", "ipad"):
        G["g"]["DEV"].setdefault("ipad", (834, 1194, (24, 0, 20, 0), True))
        br, ctx, pg = G["load"](pw, dev)
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        ids = pg.evaluate(IDS) or ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
        res = {i: pg.evaluate(PROBE, i) for i in ids}
        br.close()
        lit = {k: v for k, v in res.items() if v}
        chk("(1) %s: the copy's digits set as the number's (%s)" % (dev, {k: v["fvLit"] for k, v in lit.items()}),
            lit and all(v["fvLit"] == v["fvReal"] for v in lit.values()), lit)
        off = {k: [round(v["dx"], 2), round(v["dy"], 2), round(v["dw"], 2)] for k, v in lit.items()}
        chk("(2) %s: the copy lies on the number - left, top, width within 0.25px (%s)" % (dev, off),
            lit and all(max(abs(x) for x in o) <= .25 for o in off.values()), off)
        chk("(3) %s: %d effects light the number (%s)" % (dev, len(lit), sorted(lit)), len(lit) >= 3, res)
chk("(3) no page errors", not errs, errs[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
