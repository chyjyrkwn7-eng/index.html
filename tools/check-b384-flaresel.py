"""Build 384 r17: tapping the Home flares fast on a laptop selects nothing.
Madison: "when tapping the flares on the Home Screen very fast on a laptop, it changes color, it's almost as if it highlights it? It highlights
words on the screen if I try to so that should maybe be fixed". A run of quick clicks is a double/triple click and selects.
On a laptop (1440x900, mouse), on Home, in both classes' themes: double- and triple-clicking a flare, the sphere and the space between flares
leaves the page with no selection (window.getSelection() empty) and the flare/sphere computes user-select:none.
Run:  python3 tools/check-b384-flaresel.py   (--against OLD/index.html must FAIL)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for lab, W, H in (("laptop 1440x900", 1440, 900), ("laptop 1280x720", 1280, 720)):
        ctx, pg = cb.booted(br, W, H, seed=cb.USED_ACCOUNT)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>{ document.getElementById('tour-overlay')?.remove(); document.getElementById('tour-tooltip')?.remove(); showHome(); }"); pg.wait_for_timeout(1500)
        pg.evaluate("()=>{ document.querySelectorAll('.unlock-card,.rs-spot,.update-banner,.daily-alert').forEach(n=>n.remove()); }")
        boxes = pg.evaluate("""()=>{ const out=[]; document.querySelectorAll('.cosmic-icon-badge, .cosmic-flare-dot, .cosmic-badge-tappable').forEach((b,i)=>{ const r=b.getBoundingClientRect(); if(r.width>5&&r.height>5) out.push({k:'flare'+i,x:r.left+r.width/2,y:r.top+r.height/2}); });
          const h=document.querySelector('.cosmic-hero-wrap'); if(h){ const r=h.getBoundingClientRect(); out.push({k:'sphere',x:r.left+r.width/2,y:r.top+r.height/2}); } return out; }""")
        chk("%s: the flares and the sphere are on Home (%d targets)" % (lab, len(boxes)), len(boxes) >= 3, boxes)
        us = pg.evaluate("()=>{ const b=document.querySelector('.cosmic-icon-badge, .cosmic-flare-dot, .cosmic-badge-tappable'); const h=document.querySelector('.cosmic-hero-wrap'); return [getComputedStyle(b).userSelect, getComputedStyle(h).userSelect]; }")
        chk("%s: a flare and the planet system compute user-select none (%s)" % (lab, us), us == ["none", "none"], us)
        bad = []
        for t in boxes[:5] + boxes[-1:]:
            for n in (2, 3):
                pg.evaluate("()=>getSelection().removeAllRanges()")
                pg.mouse.click(t["x"], t["y"], click_count=n, delay=20); pg.wait_for_timeout(120)
                sel = pg.evaluate("()=>({t:String(getSelection()).trim(), n:getSelection().rangeCount && !getSelection().isCollapsed})")
                if sel["t"] or sel["n"]: bad.append((t["k"], n, sel["t"][:40]))
        chk("%s: double and triple clicks on every flare and the sphere select nothing (%s)" % (lab, bad[:3]), not bad, bad)
        chk("%s: no page errors" % lab, not errs, errs)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
