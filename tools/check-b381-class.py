"""Build 381: on an iPhone the class button opens its list again.
Madison: "the class button, when I click it, it doesn't open the drop down, it just takes me to the class
sign up thing, so right now I can't even switch classes". Since 380 the closed list sits inside the button,
and an iPhone's haptic switch in the hidden "+" took the tap. Real touch events, an iPhone's user agent.
Run:  python3 tools/check-b381-class.py   (--against: copy the old index.html over first)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0381');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0381c"; d["firstName"] = "Casey"; d["novaMet"] = 99
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
def tap(cdp, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(0.08)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
def page(br, w, h, ins, installed):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=3, has_touch=True, is_mobile=True, user_agent=UA)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    # the class button is the owner's (classSwitchAllowed); enrolled in Fire Code too, so the list has a class and the "+"
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; store.publicId=window.NOVA_CLASS_OWNER; localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); showHome(); }")
    pg.wait_for_timeout(3000)
    return ctx, pg, ctx.new_cdp_session(pg)
CENTRE = "(sel)=>{ const b=document.querySelector(sel); if(!b) return null; const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"
STATE = "()=>({open: !!document.querySelector('.class-bubble-wrap.is-open'), catalog: !!document.querySelector('#stage .class-catalog, #stage .class-enroll'), switching: document.documentElement.classList.contains('class-switching')})"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for label, (w, h, ins), installed in (("installed, phone", (440, 956, (62, 0, 34, 0)), True), ("Safari tab, phone", (440, 956, (62, 0, 34, 0)), False),
                                          ("installed, Pro Max at 85%", (518, 1125, (73, 0, 40, 0)), True)):
        ctx, pg, cdp = page(br, w, h, ins, installed)
        c = pg.evaluate(CENTRE, ".class-bubble")
        if not c:
            chk("%s: the class button is on Home" % label, False); ctx.close(); continue
        tap(cdp, *c); pg.wait_for_timeout(1000)
        s = pg.evaluate(STATE)
        chk("%s: a finger on the class button opens its list (%s)" % (label, s), s["open"] and not s["catalog"], s)
        if s["open"]:
            pg.wait_for_timeout(500)
            ci = pg.evaluate(CENTRE, ".class-stack-item.is-ifc .csi-bubble")
            tap(cdp, *ci); pg.wait_for_timeout(150)   # switchClass reloads 380ms after the tap: read before it
            try: s2 = pg.evaluate("()=>({switching: document.documentElement.classList.contains('class-switching'), to: localStorage.getItem('class26e.activeclass')})")
            except Exception as e: s2 = {"switching": False, "to": None, "err": str(e)[:80]}
            chk("%s: and Fire Code in it switches class (%s)" % (label, s2), s2["switching"] and s2["to"] == "ifc", s2)
        ctx.close()
    # the "+" still opens the class list
    ctx, pg, cdp = page(br, 440, 956, (62, 0, 34, 0), True)
    tap(cdp, *pg.evaluate(CENTRE, ".class-bubble")); pg.wait_for_timeout(1200)
    tap(cdp, *pg.evaluate(CENTRE, ".class-stack-item.is-add .csi-bubble")); pg.wait_for_timeout(1200)
    s = pg.evaluate(STATE)
    chk("the list's \"+\" opens the class list (%s)" % (s,), s["catalog"], s)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
