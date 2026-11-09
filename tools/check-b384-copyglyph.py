"""Build 384 r8: the copy control is just the glyph.
Madison (a phone screenshot of the save-code card, the copy button circled): "Not centered, and why is it within a button,
typically I just see it the copy button thing and people know to click it?"
On an iPhone 17 Pro Max, in each place the control lives (the save-your-code card, Settings > Sync's code, Manage friends' code):
(1) it is the glyph alone - no fill, no shadow, no rim, no outline; (2) its tap area is still at least 44 x 44;
(3) the glyph is centred in that area (0.5px); (4) the control is centred on the code beside it (1px - the card's code box,
the Sync well, the friend code's row); (5) opening the save-code card does not focus it (a focused button drew a white ring
round it on a phone); (6) no page errors.
Run:  python3 tools/check-b384-copyglyph.py   (--against OLD/index.html must FAIL)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cbx", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec)
argv = sys.argv[:]; spec.loader.exec_module(cb); sys.argv = argv
from playwright.sync_api import sync_playwright
fails = []
def ck(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -> %s" % (detail,)))
    if not ok: fails.append(name)
M = """(sel)=>{ const b=[...document.querySelectorAll('.friend-copy-btn')].find(e=>e.offsetParent); if(!b) return null; const r=b.getBoundingClientRect();
  const s=b.querySelector('svg').getBoundingClientRect(); const cs=getComputedStyle(b);
  const t=document.querySelector(sel); const q=t ? t.getBoundingClientRect() : null;
  return { w:r.width, h:r.height, gx:s.x+s.width/2-(r.x+r.width/2), gy:s.y+s.height/2-(r.y+r.height/2),
    bg:cs.backgroundColor, img:cs.backgroundImage, shadow:cs.boxShadow, border:parseFloat(cs.borderTopWidth)||0, outline:cs.outlineStyle,
    focused:document.activeElement===b, dy: q ? (r.y+r.height/2)-(q.y+q.height/2) : null }; }"""
PLACES = [
  ("the save-code card", "()=>{ try{ syncCode='K7Q2M9XP'; }catch(e){} showSaveCodeCard({mode:'new'}); }", ".savecode-value"),
  ("Settings > Sync", "()=>{ document.getElementById('savecode-card')?.remove(); syncCode='K7Q2M9XP'; showAppearance({page:'sync'}); }", ".sync-code-well"),
  ("Manage friends", "()=>{ showFriends(); }", ".friend-mycode"),
]
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = cb.booted(br, 440, 956, dpr=2)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    for name, go, sel in PLACES:
        pg.evaluate(go); pg.wait_for_timeout(1300)
        m = pg.evaluate(M, sel)
        if not m:
            ck("%s: the copy control is there" % name, False, None); continue
        plain = m["bg"] in ("rgba(0, 0, 0, 0)", "transparent") and m["img"] == "none" and m["shadow"] == "none" and m["border"] == 0
        ck("(1) %s: the glyph alone - no fill, shadow or rim (%s / %s)" % (name, m["bg"], m["shadow"][:40]), plain, m)
        ck("(2) %s: a 44px tap area (%.1f x %.1f)" % (name, m["w"], m["h"]), m["w"] >= 44 and m["h"] >= 44, m)
        ck("(3) %s: the glyph centred in it (%.2f, %.2f)" % (name, m["gx"], m["gy"]), abs(m["gx"]) <= .5 and abs(m["gy"]) <= .5, m)
        ck("(4) %s: centred on the code beside it (%s)" % (name, m["dy"] if m["dy"] is None else round(m["dy"], 2)), m["dy"] is not None and abs(m["dy"]) <= 1, m)
        if name == "the save-code card":
            ck("(5) opening the card does not focus the copy control (no ring)", not m["focused"] and m["outline"] in ("none", ""), m)
    ck("(6) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILURES (%d)" % len(fails))
sys.exit(1 if fails else 0)
