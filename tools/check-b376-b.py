#!/usr/bin/env python3
"""Build 376 (b): "The auto pausing thing mostly works but when I swipe to view the app it's still on the test question." Swiping up from the
bottom edge to the app switcher, iOS takes the touch away from the page (touchcancel) before the app goes; a running test pauses then, while
the pause screen can still be drawn into the picture iOS keeps. A touch that starts higher up and is cancelled does not pause it.
  python3 tools/check-b376-b.py   (--against: copy the old index.html and version.json over first)
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("st", os.path.join(HERE, "check-savetest.py"))
st = importlib.util.module_from_spec(spec); sys.argv_saved = list(sys.argv)
spec.loader.exec_module(st)
from playwright.sync_api import sync_playwright
TOUCH = """(y, type) => { const ev = new Event(type, { bubbles: true }); Object.defineProperty(ev, 'touches', { value: type === 'touchstart' ? [{ clientY: y, clientX: 200 }] : [] }); document.dispatchEvent(ev); }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=st.CHROME)
    ctx, pg, errors = st.booted(br, 440, 956)
    st.ev(pg, "await start('drill'); await answer(false); await next();")
    pg.evaluate("(a)=>(" + TOUCH + ")(a[0], a[1])", [500, "touchstart"]); pg.evaluate("(a)=>(" + TOUCH + ")(a[0], a[1])", [500, "touchcancel"])
    mid = st.ev(pg, "out.paused = paused;")
    st.check("a touch from the middle of the screen that is cancelled does not pause the test", mid.get("paused") is False, mid)
    h = pg.evaluate("()=>innerHeight")
    pg.evaluate("(a)=>(" + TOUCH + ")(a[0], a[1])", [h - 6, "touchstart"]); pg.evaluate("(a)=>(" + TOUCH + ")(a[0], a[1])", [h - 6, "touchcancel"])
    pg.wait_for_timeout(100)
    r = st.ev(pg, "out.paused = paused; out.menu = !!document.querySelector('.pausepanel'); out.vis = document.visibilityState;")
    st.check("a touch from the bottom edge that iOS takes away pauses the test at once (%s)" % (r,), r.get("paused") is True and r.get("menu") is True and r.get("vis") == "visible", r)
    br.close()
st.SERVER.shutdown()
print("ALL PASS" if not st.FAILURES else "FAILED: " + ", ".join(st.FAILURES))
sys.exit(1 if st.FAILURES else 0)
