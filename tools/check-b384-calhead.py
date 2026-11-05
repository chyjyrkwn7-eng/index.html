#!/usr/bin/env python3
"""Build 384 full check: on a laptop (and an iPad on its side) the Calendar's "Class 26E · police academy" line is under the
page's name, not through it.

From 64rem wide in landscape the page's name sits in the top-left corner (THE PAGE'S NAME IN THE TOP-LEFT CORNER) and the
Calendar spreads to a wide two-column grid whose first line - whose calendar it is - started at the same height, close
enough to the left edge to run under the name. Measured on four landscape sizes and the two portrait ones that must not move.

  python3 tools/check-b384-calhead.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300])
seed = dict(rc["SEED"]); seed["seenClassTip"] = True
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for w, h in ((1512, 852), (1366, 638), (1194, 834), (1920, 1080), (834, 1194), (440, 956)):
        ctx = br.new_context(viewport={"width": w, "height": h}); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','99');localStorage.setItem('class26e.drill.v1',%s)}catch(e){}" % json.dumps(json.dumps(seed)))
        if BODY is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2500)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); homeUnlocksOwed=()=>false; document.querySelectorAll('.unlock-card,.rs-spot').forEach(n=>n.remove()); (typeof showCalendarTab==='function'?showCalendarTab:showCalendar)(); }")
        pg.wait_for_timeout(1500)
        r = pg.evaluate("""()=>{ const R=e=>{ if(!e) return null; const b=e.getBoundingClientRect(); return [b.left,b.top,b.right,b.bottom]; };
          return { head: R(document.querySelector('.screen-calendar-tab > .cal-classhead')), title: R(document.getElementById('count')) }; }""")
        a, b = r["head"], r["title"]
        apart = a and b and (a[1] >= b[3] + 4 or a[0] >= b[2] + 4 or a[3] <= b[1] - 4)
        chk("%dx%d: the class line is clear of the page's name (line %s, name %s)" % (w, h, a and [round(x) for x in a], b and [round(x) for x in b]), apart, r)
        if errs: chk("%dx%d: no page errors" % (w, h), False, errs)
        ctx.close()
    br.close()
srv.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
