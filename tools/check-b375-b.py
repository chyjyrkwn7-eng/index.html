#!/usr/bin/env python3
"""Build 375 (b): "When leaving the app mid test and coming back, it does automatically pause but the timing is off, you come back and
the test is there for a few seconds and then it pauses." A running test pauses as soon as the window loses focus - while the page is
still showing and can draw its pause screen, which is then the picture iOS keeps of the app - not only once the page is hidden.
  python3 tools/check-b375-b.py   (--against: copy the old index.html and version.json over first)
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("st", os.path.join(HERE, "check-savetest.py"))
st = importlib.util.module_from_spec(spec); sys.argv_saved = list(sys.argv)
spec.loader.exec_module(st)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=st.CHROME)
    ctx, pg, errors = st.booted(br, 440, 956)
    st.ev(pg, "await start('drill'); await answer(false); await next();")
    before = st.ev(pg, "out.paused = paused; out.vis = document.visibilityState;")
    r = st.ev(pg, """const real = document.hasFocus; document.hasFocus = () => false; window.dispatchEvent(new Event('blur'));
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
      out.paused = paused; out.menu = !!document.querySelector('.pausepanel'); out.vis = document.visibilityState; document.hasFocus = real;""")
    st.check("losing focus mid-test pauses it while the page is still visible (%s)" % (r,), before.get("paused") is False and r.get("paused") is True and r.get("menu") is True and r.get("vis") == "visible", (before, r))
    br.close()
st.SERVER.shutdown()
print("ALL PASS" if not st.FAILURES else "FAILED: " + ", ".join(st.FAILURES))
sys.exit(1 if st.FAILURES else 0)
