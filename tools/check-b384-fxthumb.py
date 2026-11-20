#!/usr/bin/env python3
"""Build 384.136: every small picture of a hundo effect is the effect itself.

Madison circled Customize's Next up tile on Profile: "The example of the hundo effect here is bad, fix those." It was a coloured
square with "100" in it (unlockItemThumb), on Customize's row, every track row and the unlocks browser. Now each is the effect's
own still (buildHundoFxStill), in both classes' art. Checked: for every effect, in the academy's art and Fire Code's, the thumbnail
holds an SVG that draws something (a sized box, more than a few shapes) and no text; and Profile's Customize row, with an effect
next, shows that picture.

  python3 tools/check-b384-fxthumb.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
seed = dict(rc["SEED"]); seed["seenClassTip"] = True
srv, port = rc["serve"]()
def page(br, w, h, account):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    init = "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.intro.seen','99');" % json.dumps(json.dumps(seed)) if account else "localStorage.setItem('class26e.getstarted','1');"
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.a2hs','1');localStorage.setItem('class26e.frame.ok','go-live-1');%s}catch(e){}" % init)
    pg.route("**/version.json", lambda r, q: r.abort())
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2600)
    return ctx, pg, errs

THUMBS = """(ifc)=>{ IFC_ART_ON = !!ifc; return HUNDO_FX.map(f => { const t = unlockItemThumb({ k: 'fx', id: f.id, held: true });
  document.body.appendChild(t); t.style.width = t.style.height = '52px'; const s = t.querySelector('svg'); const b = s ? s.getBoundingClientRect() : null;
  const r = { id: f.id, svg: !!s, w: b ? b.width : 0, shapes: s ? s.querySelectorAll('path,circle,ellipse,rect,polygon,line,g').length : 0,
    text: [...t.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('') }; t.remove(); return r; }); }"""
with sync_playwright() as p:
    br = p.chromium.launch(); errs_all = []
    ctx, pg, errs = page(br, 440, 956, True)
    for ifc in (False, True):
        for r in pg.evaluate(THUMBS, ifc):
            chk("%s %s: the thumbnail is the effect's picture (svg %s, %dpx, %d shapes, text '%s')" % ("Fire Code" if ifc else "academy", r["id"], r["svg"], r["w"], r["shapes"], r["text"]),
                r["svg"] and r["w"] >= 40 and r["shapes"] >= 3 and not r["text"], r)
    pg.evaluate("()=>{ IFC_ART_ON = window.NOVA_CLASS === 'ifc'; }")
    ctx.close(); errs_all += errs
    # Profile's Customize row with an effect next
    ctx, pg, errs = page(br, 440, 956, True)
    pg.evaluate("()=>{ showProfile(); }"); pg.wait_for_timeout(2500)
    m = pg.evaluate("""()=>{ const b = document.querySelector('#stage .profile-customize-btn'); if(!b) return null;
      const nx = unlockNextUp(null, 1)[0]; const t = b.querySelector('.trk-thumb'); const s = t && t.querySelector('svg');
      return { next: nx ? nx.item.k + ':' + nx.item.id : '', fx: !!(t && t.classList.contains('trk-thumb-fx')), svg: !!s,
        text: t ? [...t.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('') : null }; }""")
    if m and m["next"].startswith("fx:"):
        chk("Profile: Customize's tile for the next unlock (%s) is the effect's picture" % m["next"], m["fx"] and m["svg"] and not m["text"], m)
    else:
        chk("Profile: the fixture's next unlock is an effect (so the row is measured)", False, m)
    errs_all += errs; ctx.close()
    chk("no page errors", not errs_all, errs_all[:3])
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
