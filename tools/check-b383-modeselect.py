"""Build 383: "Choose your mode" in the iOS look - the last pushed screen still on the Back pill.
Madison, looking at 382's screenshots, was offered it: "Do the one thing you noticed."
Asserts shape, read off the page: the round 44px back button and the centred title in the same bar the
units screen uses, at the same height; no corner title; the question under it in the body's face;
the cards' titles in the body's face (not the serif); Back goes Home; the tour's targets are there.
Run:  python3 tools/check-b383-modeselect.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    def _patched(ins, _o=OLD):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    g["patched"] = _patched
    import re as _re
    OLD_BUILD = _re.search(r'const APP_BUILD = "([^"]+)"', OLD).group(1)
else:
    OLD_BUILD = None
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0383');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0383"; d["novaMet"] = 99
d.setdefault("novaHeard", {})["@recap"] = 99991231
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
NAV = """()=>{ const n=document.querySelector('#stage .settings-nav'); if(!n) return null; const h=n.querySelector('h1'), b=n.querySelector('.back-link, .settings-nav-back');
  const nr=n.getBoundingClientRect(), hr=h&&h.getBoundingClientRect(), br=b&&b.getBoundingClientRect();
  return {top:Math.round(nr.top), titleMid:hr?Math.round(hr.left+hr.width/2-(nr.left+nr.width/2)):null, back:br?[Math.round(br.width),Math.round(br.height), getComputedStyle(b).borderRadius]:null}; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for (w, h, dev) in [(440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11"), (375, 667, "SE")]:
        ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True)
        ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
        pg = ctx.new_page(); body = g["patched"]((59, 0, 34, 0)); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        if OLD_BUILD:   # the old page against the new version.json would take the update and reload
            pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
                     body=json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""})))
        pg.add_init_script(INIT % json.dumps(json.dumps(d)))
        pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
        pg.evaluate("()=>{ homeUnlocksOwed=()=>false; cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(900)
        units = pg.evaluate(NAV)
        pg.evaluate("()=>{ showModeSelect(); }"); pg.wait_for_timeout(900)
        m = pg.evaluate(NAV)
        chk("%s: a nav bar with a round back button, 44px+ (%s)" % (dev, m), m and m["back"] and m["back"][0] >= 44 and m["back"][1] >= 44
            and m["back"][0] == m["back"][1] and m["back"][2].startswith(("50%", "9999", str(m["back"][0] // 2))), m)
        chk("%s: its title is centred on the bar" % dev, m and m["titleMid"] is not None and abs(m["titleMid"]) <= 2, m)
        chk("%s: the bar sits where the units screen's does (%s vs %s)" % (dev, m and m["top"], units and units["top"]),
            m and units and m["top"] == units["top"], [m, units])
        r = pg.evaluate("""()=>{ const c=document.getElementById('count'); const cr=c.getBoundingClientRect();
            const body=getComputedStyle(document.body).fontFamily, t=document.querySelector('.panel.modeselect .modecardtitle');
            const q=[...document.querySelectorAll('.panel.modeselect > p')].find(p=>p.textContent.trim().length>3);
            return {corner: cr.height>1 && cr.width>1 && getComputedStyle(c).fontSize!=='0px' && c.textContent.trim().length>0,
              cardFace: t && getComputedStyle(t).fontFamily, qFace: q && getComputedStyle(q).fontFamily, body,
              cards: document.querySelectorAll('.modecard[data-mode]').length }; }""")
        chk("%s: no corner title above the bar" % dev, not r["corner"], r)
        chk("%s: the question under the bar and the cards' titles are in the body's face" % dev,
            r["cardFace"] == r["body"] and r["qFace"] == r["body"], r)
        chk("%s: the four mode cards are there for the tour (%d)" % (dev, r["cards"]), r["cards"] == 4, r)
        pg.evaluate("()=>(document.querySelector('#stage .settings-nav .back-link, #stage .settings-nav .settings-nav-back') || document.querySelector('#stage .panel.modeselect .back-link'))?.click()"); pg.wait_for_timeout(900)
        chk("%s: Back goes Home" % dev, pg.evaluate("()=>!!document.querySelector('#stage .screen-home-actual')"))
        chk("%s: no page errors" % dev, not errs, errs[:2])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
