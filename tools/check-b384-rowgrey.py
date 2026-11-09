"""Build 384 r9: a row tile outside the Settings menu is Settings' grey. Madison, Stats' Test history tile: "Why does this icon not look
like the others?" - it was a darker grey than the menu's grey tiles (Share & Install, Check for update, Advanced).
On an iPhone 17 Pro Max: the Test history tile (Stats) and Customize's (Profile) have the same fill and rim as Settings' Share & Install
tile; no page errors.
Run:  python3 tools/check-b384-rowgrey.py   (--against OLD/index.html must FAIL)"""
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
TILE = """(label)=>{ const t=[...document.querySelectorAll('#stage *')].find(e=>e.childElementCount===0 && e.textContent.trim()===label); if(!t) return null;
  const row=t.closest('button, a, [role=button], .setrow, .row') || t.parentElement; const tile=row.querySelector('[style*="--tile"]'); if(!tile) return null;
  const c=getComputedStyle(tile); return { fill: c.getPropertyValue('--tile').trim().toUpperCase(), rim: c.getPropertyValue('--tile-rim').trim().toUpperCase(), bg: c.backgroundColor }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(1200)
    share = pg.evaluate(TILE, "Share & Install")
    pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1200)
    hist = pg.evaluate(TILE, "Test history")
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1200)
    cust = pg.evaluate(TILE, "Customize")
    for lab, t in (("Test history", hist), ("Customize", cust)):
        chk("%s's tile is Settings' grey (%s / rim %s; Share & Install %s / %s)" % (lab, t and t["fill"], t and t["rim"], share and share["fill"], share and share["rim"]),
            t and share and t["fill"] == share["fill"] and t["rim"] == share["rim"], [t, share])
    chk("no page errors", not errs, errs[:2])
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
