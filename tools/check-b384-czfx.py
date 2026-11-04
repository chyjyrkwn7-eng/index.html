"""Build 384: Customize's Your look - the Hundo effect row plays, like the rows beside it.
Madison (a screenshot of Customize): "The Hundo effect box here, it doesn't animate but everything else does, fix that."
Read off the page, iPhone 17 Pro Max (440x956), the academy and Fire Code, the effect worn being Fireworks (the Extinguisher in Fire Code):
(1) in 6s on Customize, the Hundo effect row's box runs animations (the effect playing in it) at some moment, and none of them
    after the screen has gone;
(2) the effects page (Customize's Hundo effect grid) still shows every tile still - no animation in a tile (build 314: "all those
    effects and animations seems like a lot, don't do the effects there");
(3) with Reduce motion the row shows the effect's still and runs nothing;
(4) no page errors.
Run:  python3 tools/check-b384-czfx.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384cz"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
RUN = "()=>{ const a=document.querySelector('#stage .cz-row-fx .cz-pick'); return a ? a.getAnimations({subtree:true}).filter(x=>x.playState==='running').length : -1; }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    for cls in ("academy", "ifc"):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"] if cls == "ifc" else G["academy"], **({} if cls == "ifc" else {"active": "academy"})))
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); hundoFxEarned=()=>true; store.hundoFx='fireworks'; showCustomize(); window.scrollTo(0,0); }")
        seen = []
        for _ in range(30): seen.append(pg.evaluate(RUN)); pg.wait_for_timeout(200)
        pg.evaluate("()=>{ window.__czA = document.querySelector('#stage .cz-row-fx .cz-pick'); showHome(); }"); pg.wait_for_timeout(1500)
        after = pg.evaluate("()=>window.__czA ? window.__czA.getAnimations({subtree:true}).filter(x=>x.playState==='running').length : 0")
        name = pg.evaluate("()=>{ const d=hundoFxDef('fireworks'); return d && d.name; }")
        chk("(1) %s: the Hundo effect row plays (%s): animations running at its busiest %d, after leaving %d" % (cls, name, max(seen), after), max(seen) >= 3 and after == 0, seen)
        pg.evaluate("()=>{ showCustomize('fx'); window.scrollTo(0,0); }"); pg.wait_for_timeout(2500)
        grid = pg.evaluate("""()=>{ const t=[...document.querySelectorAll('#stage .hfx-stage')].filter(s=>!s.closest('.cz-row-fx'));
          return { tiles: t.length, running: t.reduce((n,s)=>n+s.getAnimations({subtree:true}).filter(x=>x.playState==='running').length, 0) }; }""")
        chk("(2) %s: the effects page's %d tiles stay still (%d running)" % (cls, grid["tiles"], grid["running"]), grid["tiles"] >= 4 and grid["running"] == 0, grid)
        pg.evaluate("()=>{ theme.reduceMotion = true; showCustomize(); window.scrollTo(0,0); }")
        rm = []
        for _ in range(12): rm.append(pg.evaluate(RUN)); pg.wait_for_timeout(250)
        still = pg.evaluate("()=>!!document.querySelector('#stage .cz-row-fx .hfx-stage.is-still, #stage .cz-row-fx .hfx-stage.is-poster')")
        chk("(3) %s: Reduce motion - the row shows a still and runs nothing (%s)" % (cls, max(rm)), still and max(rm) == 0, [still, rm])
        errs_all += errs; ctx.close()
    chk("(4) no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
