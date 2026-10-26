#!/usr/bin/env python3
"""Build 328: two things Madison hit.

  1. "If I'm mid test, and I go to another app and come back, make it so that the app
     automatically pauses. So when I come back I'm in the test's pause menu."
     A running Drill / Mock is paused the moment the page is hidden, and its pause screen is
     what is there on the way back. The Virtual Room, flash cards and results are left alone.
  2. "Going through the review phase of missed questions during a test. Just by tapping the
     screen while it loaded it backed me out to the main menu." On the results, a tap meant for
     the screen (it speeds up the card) must not press a button that rises under the finger.

Written against the build before (it fails there):
  python3 tools/check-b328-fixes.py
  python3 tools/check-b328-fixes.py --against /path/to/old-index.html
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("st", os.path.join(HERE, "check-savetest.py"))
st = importlib.util.module_from_spec(spec); sys.argv_saved = list(sys.argv)
spec.loader.exec_module(st)
from playwright.sync_api import sync_playwright

def hide(pg):
    pg.evaluate("""()=>{ Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});
      Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); document.dispatchEvent(new Event('visibilitychange')); }""")
def show(pg):
    pg.evaluate("""()=>{ Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'});
      Object.defineProperty(document,'hidden',{configurable:true,get:()=>false}); document.dispatchEvent(new Event('visibilitychange')); }""")

def auto_pause(br):
    print("\n1. leaving the app mid-test pauses it; coming back shows the pause menu")
    ctx, pg, errors = st.booted(br, 440, 956)
    st.ev(pg, "await start('drill'); await answer(false); await next();")
    before = st.ev(pg, "out.paused = paused; out.q = !!document.querySelector('.qpanel .choice'); out.pos = pos;")
    hide(pg); pg.wait_for_timeout(500); show(pg); pg.wait_for_timeout(700)
    r = st.ev(pg, """out.paused = paused; out.menu = !!document.querySelector('.pausepanel'); out.qShown = !!document.querySelector('.qpanel .choice');
      out.pos = pos; out.saved = !!(readRunSession() || {}).paused || !!readRunSession();""")
    st.check("a running test is paused when the page is hidden", before.get("paused") is False and r.get("paused") is True, (before, r))
    st.check("the pause menu is what is on screen on the way back, the question hidden", r.get("menu") is True and r.get("qShown") is False, r)
    st.check("it is still the same question", r.get("pos") == before.get("pos"), (before, r))
    # resume carries on
    st.ev(pg, "document.getElementById('resumebtn')?.click(); await wait(700);")
    r2 = st.ev(pg, "out.paused = paused; out.q = !!document.querySelector('.qpanel .choice');")
    st.check("Resume puts the question back", r2.get("paused") is False and r2.get("q") is True, r2)
    # results screen is left alone
    ctx.close()
    ctx, pg, errors = st.booted(br, 440, 956)
    st.ev(pg, "await start('drill'); document.getElementById('hint'); ")
    ctx.close()

def tap_guard(br):
    print("\n2. a tap on the results does not press the button that rises under it")
    ctx, pg, errors = st.booted(br, 440, 956)
    st.ev(pg, """await start('drill'); const n = order.length;
      for(let k = 0; k < n; k++){ await answer(true); if(k < n - 1) await next(); } """)
    pg.wait_for_timeout(300)
    # finish the run and get to the results
    st.ev(pg, "advance(); await wait(1200);")
    pg.wait_for_selector(".actions-results, .rs-final, #stage .panel", timeout=20000)
    # tap the panel (speeds the reveal) then click Main menu at once: it must not leave
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      for(let i = 0; i < 60 && !document.querySelector('.rs-final button'); i++) await wait(250);
      const panel = document.querySelector('#stage .panel'); if(!panel) return { err: 'no panel' };
      panel.click();                                   // a tap meant for the screen
      const home = [...document.querySelectorAll('.rs-final button')].find(b => /main menu/i.test(b.textContent));
      if(!home) return { err: 'no main menu button', btns: [...document.querySelectorAll('.rs-final button')].map(b => b.textContent) };
      home.click();                                    // the click that lands on it a moment later
      await wait(150);
      const stillResults = !!document.querySelector('.rs-final') && !document.querySelector('.panel.home.screen-home-actual');
      await wait(900);
      home.click(); await wait(600);
      return { stillResults, leftLater: !!document.querySelector('.panel.home.screen-home-actual') }; }""")
    st.check("a click on Main menu right after a tap on the screen does nothing", r.get("stillResults") is True, r)
    st.check("a deliberate click a moment later still works", r.get("leftLater") is True, r)
    st.check("no page errors", not errors, errors[:3])
    ctx.close()

if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=st.CHROME)
        for fn in (auto_pause, tap_guard):
            try: fn(br)
            except Exception as e: st.check("%s ran to the end" % fn.__name__, False, str(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not st.FAILURES else "%d FAILED" % len(st.FAILURES)))
    sys.exit(1 if st.FAILURES else 0)
