"""Build 384, round 9: every hundo effect leaves the grade box the way the default (Confetti) does.
Madison, on Extinguisher beside Confetti: "The default Hundo effect is perfect. The others, the grade box still has some of the
old interface in it, and the borders is messed up? Notice how when the grade box for the default one is done the box doesn't
change color but the others do? Yeah they should be like that, so follow suite with the default way."
On a REAL results screen (a full-chapter / full-unit drill at 100%, summarize() and the results reveal), in both classes, for every effect:
 (1) while it plays and after it ends, the grade card is never tinted (no .hfx-tinted, no .hfx-tint layer on it);
 (2) after it ends the card reads exactly as Confetti's does: background, border, shadow, the 100%'s fill and the unit bar's;
 (3) while it plays, the effect's layer in the box covers the card's whole border box - its 1px border included, so no ring of
     plain card shows round whatever the effect lays in the box.
Run:  python3 tools/check-b384-hfxdefault.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lib_realrun as R
from playwright.sync_api import sync_playwright
cb = R.cb
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1]).read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
READ = r"""() => { const g = document.querySelector('.rs-grade'); if(!g) return null; const cs = getComputedStyle(g), r = g.getBoundingClientRect();
  const f = g.querySelector('.unit-breakdown-fill'), p = g.querySelector('.rs-pct'), bx = g.querySelector(':scope > .hfx-box');
  const br = bx && bx.getBoundingClientRect();
  return { tinted: g.classList.contains('hfx-tinted') || !!g.querySelector(':scope > .hfx-tint'),
    look: [cs.backgroundColor, cs.backgroundImage, cs.borderTopWidth + ' ' + cs.borderTopColor, cs.boxShadow,
           f ? getComputedStyle(f).backgroundImage : '', p ? getComputedStyle(p).backgroundImage + ' ' + getComputedStyle(p).color : ''],
    box: br ? [br.left - r.left, br.top - r.top, r.right - br.right, r.bottom - br.bottom].map(v => Math.round(v * 10) / 10) : null }; }"""
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for cls in ("ifc", "academy"):
        ref = None
        for fx in IDS:
            ctx, pg, errs = R.open_run(br, cls, 440, 956, fx, dpr=1)
            R.wait_fx(pg); R.advance(pg, 2.0)
            mid = pg.evaluate(READ)
            R.advance(pg, 14)
            end = pg.evaluate(READ)
            ctx.close()
            tag = "%s %s" % (cls, fx)
            if not mid or not end:
                chk(tag + ": a results screen with a grade card", False, (mid, end)); continue
            if fx == "confetti":
                ref = end["look"]
                chk(tag + ": (1) the default's box is not tinted", not mid["tinted"] and not end["tinted"], (mid["tinted"], end["tinted"]))
                continue
            chk(tag + ": (1) the box is never tinted, while it plays or after", not mid["tinted"] and not end["tinted"], (mid["tinted"], end["tinted"]))
            chk(tag + ": (2) after it ends the box reads exactly as the default's", ref is not None and end["look"] == ref, json.dumps([end["look"], ref]))
            b = mid["box"]
            chk(tag + ": (3) the effect's layer covers the card's border box (offsets %s)" % b, b is None or all(v <= 0.05 for v in b), b)
            if errs: chk(tag + ": no page errors", False, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
