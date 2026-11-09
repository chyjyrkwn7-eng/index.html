#!/usr/bin/env python3
"""Build 384 final check: the word "Search" sits on its field's middle.

Madison, circling the unit screen's field beside Select all: "The word search in the search bar is slightly lowered". Measured
2.0px (CSS) low: build 328 dropped every search field's words 2px for lowercase placeholders ("search names"); since 382 every
field just says "Search" - a capital and ascenders, whose ink a centred line box already centres. check-centering measures a
control's text, and a placeholder is not one, which is how this got past it.
In a browser (the iPhone/iPad rule, measured on a phone, is check-b382's), on an iPhone 17 Pro Max at its 3x:
(1) the unit screen's field (Police Academy and Fire Code): the placeholder's ink centre is within 1px of the field's middle;
(2) and level with Select all's words beside it (within 1px);
(3) the Leaderboard's field: the same, within 1px;
(4) the fields kept their height (44px on the unit screen);
(5) no page errors.
  python3 tools/check-b384-searchink.py [--against OLD/index.html]   (must FAIL on the build before)"""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b381-class.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b381-class.py"), "__name__": "b384si"}
exec(src, G)
g = G["g"]
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = g["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = _old
from playwright.sync_api import sync_playwright
from PIL import Image
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
BOX = """(sel)=>{ const i=document.querySelector(sel); if(!i) return null; i.scrollIntoView({block:'center', behavior:'instant'});
  const w=i.closest('.searchwrap, .rank-search-wrap') || i.parentElement; const ic=w.querySelector('.searchicon, svg');
  const r=i.getBoundingClientRect(), c=ic ? ic.getBoundingClientRect() : null; const cs=getComputedStyle(i);
  const b=document.querySelector('#stage .selall-btn'); const br=b && b.offsetHeight ? b.getBoundingClientRect() : null;
  return { x:r.left, y:r.top, w:r.width, h:r.height, textLeft: c ? c.right + 4 : r.left + parseFloat(cs.paddingLeft) - 2, pr: parseFloat(cs.paddingRight),
           btn: br ? [br.left, br.top, br.width, br.height] : null, empty: !i.value }; }"""
def ink_mid(im, s, x0, y0, x1, y1):
    """the vertical middle (CSS px from y0) of the pixels clearly brighter than the field's own fill"""
    c = im.crop((int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s))).convert("L"); w, h = c.size; px = c.load()
    vals = sorted(px[x, y] for x in range(0, w, 3) for y in range(0, h, 3)); bg = vals[len(vals) // 2]
    rows = [y for y in range(h) if any(px[x, y] > bg + 45 for x in range(w))]
    return (((rows[0] + rows[-1]) / 2) / s, (y1 - y0) / 2) if rows else (None, None)
def measure(pg, sel):
    b = pg.evaluate(BOX, sel)
    if not b or not b["empty"]: return None
    pg.wait_for_timeout(250)
    im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB"); s = im.width / pg.viewport_size["width"]
    m, half = ink_mid(im, s, b["textLeft"], b["y"] + 3, b["x"] + b["w"] - max(8, b["pr"] * .5), b["y"] + b["h"] - 3)
    out = {"field_h": round(b["h"], 1), "off": None if m is None else round(m - half, 2)}
    if b["btn"]:
        bx, by, bw, bh = b["btn"]
        bm, bhalf = ink_mid(im, s, bx + bw * .34, by + 3, bx + bw - 8, by + bh - 3)
        out["btn_off"] = None if bm is None else round((by + 3 + bm) - (b["y"] + 3 + m), 2) if m is not None else None
    return out
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    for cls in ("academy", "ifc"):
        ctx, pg, cdp = G["page"](br, 440, 956, (62, 0, 34, 0), False)
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        if cls == "ifc":
            pg.evaluate("()=>{ try{ localStorage.setItem('class26e.activeclass','ifc'); }catch(e){} location.reload(); }"); pg.wait_for_timeout(5000)
            pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} }")
        pg.evaluate("()=>{ document.querySelectorAll('.rs-spot,.unlock-card,#tour-overlay,#tour-tooltip,.daily-alert').forEach(n=>n.remove()); cfg.mode='drill'; cfg.units=[]; showSetup(); }")
        pg.wait_for_timeout(1600)
        u = measure(pg, "#stage .setup-tools input.searchbox")
        chk("(1) %s unit screen: \"Search\" on the field's middle (%s px off)" % (cls, u and u["off"]), u and u["off"] is not None and abs(u["off"]) <= 1, u)
        chk("(2) %s unit screen: level with Select all's words (%s px)" % (cls, u and u.get("btn_off")), u and u.get("btn_off") is not None and abs(u["btn_off"]) <= 1, u)
        chk("(4) %s unit screen: the field is still 44px (%s)" % (cls, u and u["field_h"]), u and abs(u["field_h"] - 44) < .6, u)
        if cls == "academy":
            pg.evaluate("()=>{ showRankings(); }"); pg.wait_for_timeout(2500)
            pg.evaluate("()=>{ document.querySelectorAll('.rs-spot,.unlock-card,#tour-overlay,#tour-tooltip,.daily-alert,.toast').forEach(n=>n.remove()); }")
            l = measure(pg, "#stage input.searchbox")
            chk("(3) the Leaderboard's field: \"Search\" on its middle (%s px off)" % (l and l["off"]), l and l["off"] is not None and abs(l["off"]) <= 1, l)
        ctx.close()
    chk("(5) no page errors", not errs, errs[:3])
    br.close()
G["srv"].shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
